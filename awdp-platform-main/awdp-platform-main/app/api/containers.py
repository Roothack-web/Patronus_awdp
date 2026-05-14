from flask import jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime

from app.models import Challenge, Container, FlagHistory
from app import db
from app.api import api_bp, team_required_api
from app.main import contest_not_ended, _docker_available, _start_container_simulated
from app.utils import generate_flag, flag_expiry_delta
from app.docker_manager import (
    create_challenge_container, stop_container as docker_stop,
    remove_container as docker_remove, get_container_status,
)
from app.asteroid_client import send_status
import logging

logger = logging.getLogger(__name__)


@api_bp.route('/containers/<int:challenge_id>/start', methods=['POST'])
@login_required
@team_required_api
def start_container(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    team = current_user

    if contest_not_ended(c):
        return jsonify({'ok': False, 'error': '比赛已结束，无法操作容器'}), 403

    existing = Container.query.filter_by(
        challenge_id=c.id, team_id=team.id).first()

    if existing and existing.status == 'running':
        if existing.docker_container_id:
            d_status = get_container_status(existing.docker_container_id)
            if d_status == 'running':
                return jsonify({'ok': False, 'error': '容器已在运行中'}), 409
        existing.status = 'stopped'
        db.session.commit()

    if not _docker_available():
        _start_container_simulated(c, team, existing)
        return jsonify({'ok': True, 'data': {
            'message': 'Docker 不可用，使用模拟模式启动',
            'simulated': True,
        }})

    try:
        if existing and existing.docker_container_id:
            try:
                docker_remove(existing.docker_container_id)
            except RuntimeError:
                logger.warning('Remove stale container %s', existing.docker_container_id)

        result = create_challenge_container(
            c, team.id,
            host=current_app.config.get('PUBLIC_HOST', '127.0.0.1'))
        flag = result['flag']

        if existing:
            existing.docker_container_id = result['container_id']
            existing.container_name = result['container_name']
            existing.public_host = result['host']
            existing.public_port = result['port']
            existing.current_flag = flag
            existing.flag_version += 1
            existing.flag_expires_at = datetime.utcnow() + flag_expiry_delta()
            existing.status = 'running'
            existing.started_at = datetime.utcnow()
            existing.stopped_at = None
        else:
            container = Container(
                challenge_id=c.id, team_id=team.id,
                docker_container_id=result['container_id'],
                container_name=result['container_name'],
                public_host=result['host'],
                public_port=result['port'],
                status='running', current_flag=flag, flag_version=1,
                flag_expires_at=datetime.utcnow() + flag_expiry_delta(),
                max_resets=c.max_resets or 10,
                started_at=datetime.utcnow(),
            )
            db.session.add(container)
        db.session.commit()
        send_status(team.id, 'online')

        return jsonify({'ok': True, 'data': {
            'message': f'容器已创建并启动 → {result["host"]}:{result["port"]}',
            'host': result['host'],
            'port': result['port'],
        }})
    except RuntimeError as e:
        _start_container_simulated(c, team, existing)
        return jsonify({'ok': True, 'data': {
            'message': f'Docker 创建失败，已回退模拟模式: {e}',
            'simulated': True,
        }})


@api_bp.route('/containers/<int:challenge_id>/stop', methods=['POST'])
@login_required
@team_required_api
def stop_container(challenge_id):
    team = current_user
    c = Challenge.query.get(challenge_id)
    if c and contest_not_ended(c):
        return jsonify({'ok': False, 'error': '比赛已结束，无法操作容器'}), 403

    container = Container.query.filter_by(
        challenge_id=challenge_id, team_id=team.id).first()
    if not container or container.status != 'running':
        return jsonify({'ok': False, 'error': '没有运行中的容器'}), 400

    if container.docker_container_id:
        try:
            docker_stop(container.docker_container_id)
        except RuntimeError as e:
            logger.warning('Stop container %s: %s', container.docker_container_id, e)

    container.status = 'stopped'
    container.stopped_at = datetime.utcnow()
    db.session.commit()
    send_status(team.id, 'offline')

    return jsonify({'ok': True, 'data': {'message': '容器已停止'}})


@api_bp.route('/containers/<int:challenge_id>/reset', methods=['POST'])
@login_required
@team_required_api
def reset_container(challenge_id):
    team = current_user
    container = Container.query.filter_by(
        challenge_id=challenge_id, team_id=team.id).first()
    if not container:
        return jsonify({'ok': False, 'error': '请先创建容器'}), 400
    if container.reset_count >= container.max_resets:
        return jsonify({'ok': False, 'error': f'容器重置次数已达上限 ({container.max_resets})'}), 400

    c = Challenge.query.get(challenge_id)
    if c and contest_not_ended(c):
        return jsonify({'ok': False, 'error': '比赛已结束，无法操作容器'}), 403

    container.reset_count += 1

    if container.docker_container_id:
        try:
            docker_remove(container.docker_container_id)
        except RuntimeError:
            logger.warning('Failed to remove old container during reset')
        container.docker_container_id = None

    if _docker_available():
        try:
            result = create_challenge_container(
                c, team.id,
                host=current_app.config.get('PUBLIC_HOST', '127.0.0.1'))
            container.docker_container_id = result['container_id']
            container.container_name = result['container_name']
            container.public_host = result['host']
            container.public_port = result['port']
            new_flag = result['flag']
        except RuntimeError:
            new_flag = generate_flag()
    else:
        new_flag = generate_flag()

    container.current_flag = new_flag
    container.flag_version += 1
    container.flag_expires_at = datetime.utcnow() + flag_expiry_delta()
    container.status = 'running'
    container.started_at = datetime.utcnow()
    container.stopped_at = None
    db.session.commit()
    send_status(team.id, 'online')

    return jsonify({'ok': True, 'data': {
        'message': f'容器已重置 (剩余 {container.max_resets - container.reset_count} 次)',
        'reset_count': container.reset_count,
        'max_resets': container.max_resets,
    }})


@api_bp.route('/containers/<int:challenge_id>/refresh-flag', methods=['POST'])
@login_required
@team_required_api
def refresh_flag(challenge_id):
    team = current_user
    c = Challenge.query.get(challenge_id)
    if c and contest_not_ended(c):
        return jsonify({'ok': False, 'error': '比赛已结束，无法刷新 Flag'}), 403

    container = Container.query.filter_by(
        challenge_id=challenge_id, team_id=team.id).first()
    if not container or container.status != 'running':
        return jsonify({'ok': False, 'error': '没有运行中的容器'}), 400

    old = FlagHistory(container_id=container.id, flag=container.current_flag,
                      version=container.flag_version, expires_at=datetime.utcnow())
    db.session.add(old)

    new_flag = generate_flag()
    container.current_flag = new_flag
    container.flag_version += 1
    container.flag_expires_at = datetime.utcnow() + flag_expiry_delta()

    if container.docker_container_id:
        from app.docker_manager import refresh_flag_in_container
        try:
            refresh_flag_in_container(container.docker_container_id, new_flag)
        except Exception:
            logger.warning('Failed to refresh flag in container %s', container.docker_container_id)

    db.session.commit()
    return jsonify({'ok': True, 'data': {'message': 'Flag 已刷新', 'flag_version': container.flag_version}})
