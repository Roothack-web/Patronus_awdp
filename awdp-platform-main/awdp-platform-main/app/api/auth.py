from flask import jsonify, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Team
from app import db
from app.api import api_bp


@api_bp.route('/auth/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'ok': True, 'data': {'team': _team_to_dict(current_user)}})

    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'ok': False, 'error': '队伍名和密码不能为空'}), 400

    team = Team.query.filter_by(name=username).first()
    if team is None or not team.check_password(password):
        return jsonify({'ok': False, 'error': '队伍名或密码错误'}), 401

    login_user(team, remember=data.get('remember', False))
    return jsonify({'ok': True, 'data': {'team': _team_to_dict(team)}})


@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'ok': True})


@api_bp.route('/auth/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({'ok': True, 'data': {'team': _team_to_dict(current_user)}})

    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    password = data.get('password', '')

    if not name or not password:
        return jsonify({'ok': False, 'error': '队伍名和密码不能为空'}), 400
    if len(password) < 4:
        return jsonify({'ok': False, 'error': '密码长度至少 4 位'}), 400

    existing = Team.query.filter_by(name=name).first()
    if existing:
        return jsonify({'ok': False, 'error': '队伍名已存在'}), 409

    team = Team(name=name)
    team.set_password(password)
    db.session.add(team)
    db.session.commit()

    return jsonify({'ok': True, 'data': {'team': _team_to_dict(team)}}), 201


@api_bp.route('/auth/me')
@login_required
def me():
    if not hasattr(current_user, 'name'):
        return jsonify({'ok': False, 'error': '需要队伍账号'}), 403
    return jsonify({'ok': True, 'data': {'team': _team_to_dict(current_user)}})


def _team_to_dict(team):
    return {
        'id': team.id,
        'name': team.name,
        'score': team.score or 0,
        'attack_score': team.attack_score or 0,
        'defense_score': team.defense_score or 0,
        'is_admin': team.is_admin,
        'created_at': team.created_at.isoformat() if team.created_at else None,
    }
