from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, current_app, jsonify, send_from_directory
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models import Challenge, Submission, Team, Contest, ContestRound, Defense, Container, ScoreLog, FlagHistory
from app.scoring import compute_break_score, award_break_score, award_defense_score, compute_defense_score
from app.forms import ChallengeForm, SubmitFlagForm, DefenseUploadForm, ContainerActionForm
from app import db
from sqlalchemy import func
import tarfile
import io
from app.asteroid_client import send_rank, send_status
from app.docker_manager import (
    create_challenge_container, stop_container as docker_stop,
    remove_container as docker_remove, refresh_flag_in_container,
    get_container_status, check_container_health
)
from app.utils import generate_flag, flag_expiry_delta
import os
import hashlib
import subprocess
import sys
import random
from werkzeug.utils import secure_filename
from config import basedir, Config
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__, template_folder='../templates')


def team_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录')
            return redirect(url_for('auth.login'))
        if not hasattr(current_user, 'name'):
            flash('需要队伍账号')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def contest_not_ended(challenge):
    """Check if challenge's contest has ended. Returns True if blocked."""
    if challenge.contest and (challenge.contest.status == 'finished'
                              or (challenge.contest.end_at and datetime.utcnow() > challenge.contest.end_at)):
        return True
    return False


def detect_flag_cheat(challenge_id, submitted_flag, team):
    """Check if a submitted flag belongs to another team's container.
    Returns the offending Container if found, None otherwise."""
    other = Container.query.filter(
        Container.challenge_id == challenge_id,
        Container.team_id != team.id,
        Container.status == 'running',
        Container.current_flag == submitted_flag
    ).first()
    return other


def penalize_cheat(team, challenge, submitted_flag, victim_container=None):
    """Reset a team's password to a random hash for cheating."""
    import secrets
    new_hash = secrets.token_hex(32)
    team.password_hash = generate_password_hash(new_hash)
    victim_name = victim_container.team.name if victim_container and victim_container.team else '未知'
    reason = f'作弊: 队伍[{team.name}]提交了队伍[{victim_name}]的Flag — {challenge.title}'
    log = ScoreLog(
        team_id=team.id, challenge_id=challenge.id,
        score_type='penalty', score_delta=0,
        score_before=team.score or 0, score_after=team.score or 0,
        reason=reason
    )
    db.session.add(log)
    db.session.commit()
    return new_hash


def get_active_round(contest_id):
    """Get the currently active round for a contest."""
    now = datetime.utcnow()
    r = ContestRound.query.filter(
        ContestRound.contest_id == contest_id,
        ContestRound.start_at <= now,
        ContestRound.end_at >= now,
        ContestRound.status == 'running'
    ).first()
    return r


# ─── Health Check ───────────────────────────────────────────

@bp.route('/_health')
def health():
    from flask import jsonify
    try:
        db.session.execute(db.text('SELECT 1'))
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify({'status': 'ok' if db_ok else 'degraded', 'db': db_ok})


# ─── Public Routes ───────────────────────────────────────────

@bp.route('/')
def index():
    dist_dir = os.path.join(basedir, 'frontend', 'dist')
    index_path = os.path.join(dist_dir, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(dist_dir, 'index.html')
    contests = Contest.query.order_by(Contest.start_at.desc()).all()
    return render_template('index.html', contests=contests)


@bp.route('/dashboard')
@login_required
def dashboard():
    if not hasattr(current_user, 'name'):
        return redirect(url_for('main.index'))
    team = current_user
    containers = Container.query.filter_by(team_id=team.id).all()
    active_containers = sum(1 for c in containers if c.status == 'running')
    submission_count = Submission.query.filter_by(team_id=team.id).count()
    defense_count = Defense.query.filter_by(team_id=team.id).count()

    # Get recent score logs
    score_logs = ScoreLog.query.filter_by(team_id=team.id).order_by(
        ScoreLog.created_at.desc()).limit(20).all()

    # Check for defense status changes (notifications)
    recent_defenses = Defense.query.filter_by(team_id=team.id).order_by(
        Defense.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           team=team,
                           containers=containers,
                           active_containers=active_containers,
                           submission_count=submission_count,
                           defense_count=defense_count,
                           score_logs=score_logs,
                           recent_defenses=recent_defenses)


# ─── Challenge Routes ───────────────────────────────────────

@bp.route('/challenges')
def challenges():
    contests = Contest.query.order_by(Contest.start_at.asc().nullsfirst()).all()
    # Only show unaffiliated challenges to admins
    uncat = []
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        uncat = Challenge.query.filter_by(contest_id=None, enabled=True).all()
    now = datetime.now()

    # Get container status for each team challenge if logged in
    team_containers = {}
    if current_user.is_authenticated and hasattr(current_user, 'name'):
        for c in Container.query.filter_by(team_id=current_user.id).all():
            team_containers[c.challenge_id] = c

    return render_template('challenges.html', contests=contests, uncat=uncat, now=now,
                           team_containers=team_containers)


@bp.route('/challenge/<int:challenge_id>', methods=['GET', 'POST'])
def challenge_detail(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    form = SubmitFlagForm()

    team_container = None
    already_correct = False
    team = getattr(current_user, 'name', None) and current_user

    if team:
        team_container = Container.query.filter_by(
            challenge_id=c.id, team_id=team.id).first()
        prev = Submission.query.filter_by(
            team_id=team.id, challenge_id=c.id, is_correct=True).first()
        already_correct = bool(prev)

    # Flag submission
    if form.validate_on_submit():
        if not team:
            flash('请先登录后提交')
            return redirect(url_for('auth.login'))

        # Rate limit: 1 submission per 3 seconds
        recent = Submission.query.filter_by(
            team_id=team.id, challenge_id=c.id
        ).order_by(Submission.submitted_at.desc()).first()
        if recent and (datetime.utcnow() - recent.submitted_at).total_seconds() < 3:
            flash('提交过于频繁，请稍后再试')
            return redirect(url_for('main.challenge_detail', challenge_id=c.id))

        submitted = form.flag.data.strip()
        correct = False
        score_earned = 0

        # Block flag submission after contest ends
        if contest_not_ended(c):
            flash('比赛已结束，无法提交 Flag')
            return redirect(url_for('main.challenge_detail', challenge_id=c.id))

        # Must have a running container with a valid flag
        if not team_container or team_container.status != 'running':
            flash('请先启动容器获取 Flag')
            return redirect(url_for('main.challenge_detail', challenge_id=c.id))

        if submitted == team_container.current_flag:
            correct = True
        else:
            # Anti-cheat: check if flag belongs to another team's container
            cheat = detect_flag_cheat(c.id, submitted, team)
            if cheat:
                penalize_cheat(team, c, submitted, victim_container=cheat)
                sub = Submission(team_id=team.id, challenge_id=c.id,
                                 container_id=cheat.id,
                                 flag_submitted=submitted, is_correct=False)
                db.session.add(sub)
                db.session.commit()
                flash('Flag 不正确')
                return redirect(url_for('main.challenge_detail', challenge_id=c.id))

            expired = FlagHistory.query.filter_by(
                container_id=team_container.id, flag=submitted).first()
            if expired:
                flash('Flag 已过期，请重新获取')
                return redirect(url_for('main.challenge_detail', challenge_id=c.id))

        if not correct:
            sub = Submission(team_id=team.id, challenge_id=c.id,
                             flag_submitted=submitted, is_correct=False)
            db.session.add(sub)
            db.session.commit()
            flash('Flag 不正确')
            return redirect(url_for('main.challenge_detail', challenge_id=c.id))

        # Correct submission
        prev_correct = Submission.query.filter_by(
            team_id=team.id, challenge_id=c.id, is_correct=True).first()
        if prev_correct:
            flash('你已正确提交过此题')
            return redirect(url_for('main.challenge_detail', challenge_id=c.id))

        score_earned, solve_rank = compute_break_score(c, team)
        sub = Submission(team_id=team.id, challenge_id=c.id,
                         container_id=team_container.id if team_container else None,
                         flag_submitted=submitted, is_correct=True,
                         score_earned=score_earned,
                         ip_address=request.remote_addr)
        db.session.add(sub)
        award_break_score(team, c, score_earned,
                          f'Break: {c.title} (第{solve_rank}个解出)')
        db.session.commit()
        # Notify visualization
        from app.models import Team as TeamModel
        send_rank(TeamModel.query.all())
        flash(f'提交正确！第 {solve_rank} 个解出，得分 +{score_earned}')
        return redirect(url_for('main.challenge_detail', challenge_id=c.id))

    # Gather data for template
    active_round = None
    if c.contest_id:
        active_round = get_active_round(c.contest_id)

    submissions = Submission.query.filter_by(challenge_id=c.id).order_by(
        Submission.submitted_at.desc()).limit(50).all()
    defenses = Defense.query.filter_by(challenge_id=c.id).order_by(
        Defense.created_at.desc()).all()

    # Count solvers for score display
    solve_count = db.session.query(func.count(func.distinct(Submission.team_id))).filter(
        Submission.challenge_id == c.id,
        Submission.is_correct == True
    ).scalar() or 0

    # Compute dynamic score
    if solve_count:
        dynamic_score = max(
            (c.initial_score or c.points) - (solve_count - 1) * (c.score_decay or 50),
            c.min_score or 100
        )
    else:
        dynamic_score = c.initial_score or c.points

    # First / second / third blood
    blood_submissions = Submission.query.filter_by(
        challenge_id=c.id, is_correct=True
    ).order_by(Submission.submitted_at.asc()).limit(3).all()
    bloods = []
    for i, s in enumerate(blood_submissions):
        t = Team.query.get(s.team_id)
        bloods.append({
            'rank': i + 1,
            'team_name': t.name if t else '?',
            'time': s.submitted_at,
        })

    contest_ended = contest_not_ended(c) if c.contest else False

    # Per-team fix status
    already_fixed = False
    if team:
        already_fixed = bool(Defense.query.filter_by(
            team_id=team.id, challenge_id=c.id, status='success').first())

    return render_template('challenge_detail.html', challenge=c, form=form,
                           already_correct=already_correct,
                           already_fixed=already_fixed,
                           container=team_container,
                           active_round=active_round,
                           submissions=submissions, defenses=defenses,
                           solve_count=solve_count,
                           dynamic_score=dynamic_score,
                           bloods=bloods,
                           team=team,
                           contest_ended=contest_ended)


@bp.route('/challenge/<int:challenge_id>/source')
def download_source(challenge_id):
    """Download challenge source code as tar.gz for Fix patch creation."""
    c = Challenge.query.get_or_404(challenge_id)

    img = c.docker_image or ''
    base = img.split(':')[0]
    dir_name = base.replace('awdp-', '', 1) if base.startswith('awdp-') else base
    dir_name = dir_name.replace('-', '_')
    source_dir = os.path.join(basedir, 'challenges', dir_name)

    if not os.path.isdir(source_dir):
        flash('源码目录不存在')
        return redirect(url_for('main.challenge_detail', challenge_id=c.id))

    exclude = {'exploit.sh', 'exp.py', 'exploit.py'}

    def generate():
        cmd = ['tar', 'czf', '-']
        for e in exclude:
            cmd.extend(['--exclude', e])
        cmd.extend(['-C', source_dir, '.'])
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                break
            yield chunk
        proc.wait()

    filename = f"{dir_name}-source.tar.gz"
    return Response(generate(), mimetype='application/gzip',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})


# ─── Container Management (Real Docker) ────────────────────

def _docker_available():
    try:
        from app.docker_manager import get_client
        get_client().ping()
        return True
    except Exception:
        return False


def _start_container_simulated(challenge, team, existing):
    """Fallback: simulated container (DB only)."""
    flag = generate_flag()
    host = current_app.config.get('PUBLIC_HOST', '127.0.0.1')
    port = random.randint(31000, 39999)
    if existing:
        existing.status = 'running'
        existing.public_host = host
        existing.public_port = port
        existing.current_flag = flag
        existing.flag_version += 1
        existing.flag_expires_at = datetime.utcnow() + flag_expiry_delta()
        existing.started_at = datetime.utcnow()
        existing.stopped_at = None
    else:
        container = Container(
            challenge_id=challenge.id, team_id=team.id,
            container_name=f"awdp-{challenge.id}-{team.id}",
            public_host=host,
            public_port=port,
            status='running', current_flag=flag, flag_version=1,
            flag_expires_at=datetime.utcnow() + flag_expiry_delta(),
            max_resets=challenge.max_resets or 10,
            started_at=datetime.utcnow(),
        )
        db.session.add(container)
    db.session.commit()
    return flag


@bp.route('/challenge/<int:challenge_id>/container/start', methods=['POST'])
@login_required
@team_required
def start_container(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    team = current_user

    # Check contest end
    if contest_not_ended(c):
        flash('比赛已结束，无法操作容器')
        return redirect(url_for('main.challenge_detail', challenge_id=c.id))

    existing = Container.query.filter_by(
        challenge_id=c.id, team_id=team.id).first()

    if existing and existing.status == 'running':
        if existing.docker_container_id:
            d_status = get_container_status(existing.docker_container_id)
            if d_status == 'running':
                flash('容器已在运行中')
                return redirect(url_for('main.challenge_detail', challenge_id=c.id))
        existing.status = 'stopped'
        db.session.commit()

    if not _docker_available():
        _start_container_simulated(c, team, existing)
        flash('Docker 不可用，使用模拟模式启动')
        return redirect(url_for('main.challenge_detail', challenge_id=c.id))

    try:
        if existing and existing.docker_container_id:
            docker_remove(existing.docker_container_id)

        result = create_challenge_container(c, team.id, host=current_app.config.get('PUBLIC_HOST', '127.0.0.1'))
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
        flash(f'容器已创建并启动 → {result["host"]}:{result["port"]}')
    except RuntimeError as e:
        _start_container_simulated(c, team, existing)
        flash(f'Docker 创建失败，已回退模拟模式: {e}')

    return redirect(url_for('main.challenge_detail', challenge_id=c.id))


@bp.route('/challenge/<int:challenge_id>/container/stop', methods=['POST'])
@login_required
@team_required
def stop_container(challenge_id):
    team = current_user
    c = Challenge.query.get(challenge_id)
    if c and contest_not_ended(c):
        flash('比赛已结束，无法操作容器')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))
    container = Container.query.filter_by(
        challenge_id=challenge_id, team_id=team.id).first()
    if not container or container.status != 'running':
        flash('没有运行中的容器')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))

    if container.docker_container_id:
        try:
            docker_stop(container.docker_container_id)
        except RuntimeError as e:
            flash(f'停止 Docker 容器失败: {e}')
            return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))

    container.status = 'stopped'
    container.stopped_at = datetime.utcnow()
    db.session.commit()
    send_status(team.id, 'offline')
    flash('容器已停止')
    return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))


@bp.route('/challenge/<int:challenge_id>/container/reset', methods=['POST'])
@login_required
@team_required
def reset_container(challenge_id):
    team = current_user
    container = Container.query.filter_by(
        challenge_id=challenge_id, team_id=team.id).first()
    if not container:
        flash('请先创建容器')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))
    if container.reset_count >= container.max_resets:
        flash(f'容器重置次数已达上限 ({container.max_resets})')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))

    c = Challenge.query.get(challenge_id)
    if c and contest_not_ended(c):
        flash('比赛已结束，无法操作容器')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))

    container.reset_count += 1

    if container.docker_container_id:
        try:
            docker_remove(container.docker_container_id)
        except RuntimeError:
            logger.warning('Failed to remove old container for reset (challenge %s)', c.id)

    if _docker_available():
        try:
            result = create_challenge_container(c, team.id, host=current_app.config.get('PUBLIC_HOST', '127.0.0.1'))
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
    flash(f'容器已重置 (剩余 {container.max_resets - container.reset_count} 次)')
    return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))


@bp.route('/challenge/<int:challenge_id>/container/refresh-flag', methods=['POST'])
@login_required
@team_required
def refresh_flag(challenge_id):
    team = current_user
    c = Challenge.query.get(challenge_id)
    if c and contest_not_ended(c):
        flash('比赛已结束，无法刷新 Flag')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))
    container = Container.query.filter_by(
        challenge_id=challenge_id, team_id=team.id).first()
    if not container or container.status != 'running':
        flash('没有运行中的容器')
        return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))

    old = FlagHistory(container_id=container.id, flag=container.current_flag,
                      version=container.flag_version, expires_at=datetime.utcnow())
    db.session.add(old)

    new_flag = generate_flag()
    container.current_flag = new_flag
    container.flag_version += 1
    container.flag_expires_at = datetime.utcnow() + flag_expiry_delta()

    if container.docker_container_id:
        try:
            refresh_flag_in_container(container.docker_container_id, new_flag)
        except Exception:
            logger.warning('Failed to refresh flag in container %s', container.docker_container_id)

    db.session.commit()
    flash('Flag 已刷新')
    return redirect(url_for('main.challenge_detail', challenge_id=challenge_id))


# ─── Defense Routes ─────────────────────────────────────────

@bp.route('/defend/<int:challenge_id>/upload', methods=['GET', 'POST'])
@login_required
@team_required
def defend_upload(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    if contest_not_ended(c):
        flash('比赛已结束，无法上传防护包')
        return redirect(url_for('main.challenge_detail', challenge_id=c.id))
    form = DefenseUploadForm()

    team = current_user

    # Check if current team already fixed this challenge
    already_fixed = Defense.query.filter_by(
        team_id=team.id, challenge_id=c.id, status='success').first()
    if already_fixed:
        flash('你已成功修复本题，无需再次提交')
        return redirect(url_for('main.challenge_detail', challenge_id=c.id))

    # Check attempt limit
    attempt_count = Defense.query.filter_by(
        team_id=team.id, challenge_id=c.id).count()
    max_attempts = current_app.config.get('DEFENSE_MAX_ATTEMPTS', 10)

    if form.validate_on_submit():
        if attempt_count >= max_attempts:
            flash(f'本题防御提交次数已达上限 ({max_attempts} 次)')
            return redirect(url_for('main.defend_upload', challenge_id=c.id))

        f = form.package.data
        fname = secure_filename(f.filename)
        upload_dir = os.path.join(basedir, 'instance', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, f"{team.id}_{c.id}_{int(datetime.utcnow().timestamp())}_{fname}")
        f.save(save_path)

        # Compute file hash
        file_hash = ''
        try:
            with open(save_path, 'rb') as fp:
                file_hash = hashlib.sha256(fp.read()).hexdigest()
        except Exception:
            logger.warning('Failed to compute file hash')

        file_size = os.path.getsize(save_path)

        # Validate tar.gz content
        import tarfile
        try:
            if tarfile.is_tarfile(save_path):
                with tarfile.open(save_path, 'r:*') as tar:
                    members = [m.name for m in tar.getmembers()]
                    basenames = [os.path.basename(m) for m in members]
                    if 'update.sh' not in basenames:
                        os.remove(save_path)
                        flash('补丁包必须包含 update.sh')
                        return redirect(url_for('main.defend_upload', challenge_id=c.id))
                    # Verify update.sh references the web root
                    try:
                        upd_member = None
                        for m in tar.getmembers():
                            if os.path.basename(m.name) == 'update.sh':
                                upd_member = m
                                break
                        if upd_member:
                            fobj = tar.extractfile(upd_member)
                            if fobj:
                                content = fobj.read().decode(errors='ignore')
                                if '/var/www/html' not in content:
                                    os.remove(save_path)
                                    flash('update.sh 必须引用 /var/www/html 路径')
                                    return redirect(url_for('main.defend_upload', challenge_id=c.id))
                    except Exception:
                        logger.warning('Failed to inspect update.sh content')
            else:
                os.remove(save_path)
                flash('上传文件不是有效的 tar.gz 包')
                return redirect(url_for('main.defend_upload', challenge_id=c.id))
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            flash(f'包检查失败: {str(e)}')
            return redirect(url_for('main.defend_upload', challenge_id=c.id))

        d = Defense(team_id=team.id, challenge_id=c.id,
                    filename=fname, file_path=save_path,
                    file_hash=file_hash, file_size=file_size,
                    attempt_number=attempt_count + 1,
                    status='uploaded')
        db.session.add(d)
        db.session.commit()

        # Launch evaluation as detached subprocess
        try:
            python = sys.executable or 'python3'
            script = os.path.join(basedir, 'evaluate_defense.py')
            subprocess.Popen([python, script, str(d.id)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            flash(f'防护包已上传 (第{attempt_count+1}/{max_attempts}次)，评估已启动')
        except Exception:
            flash(f'防护包已上传，等待管理员手动评估')

        return redirect(url_for('main.challenge_detail', challenge_id=c.id))

    return render_template('defend_upload.html', form=form, challenge=c,
                           attempt_count=attempt_count, max_attempts=max_attempts)


@bp.route('/defense/<int:def_id>/result')
def defense_result(def_id):
    d = Defense.query.get_or_404(def_id)
    return render_template('defense_result_fragment.html', defense=d)


@bp.route('/defense/<int:def_id>/download')
def defense_download(def_id):
    d = Defense.query.get_or_404(def_id)
    content = d.result or ''
    filename = f"defense_{def_id}_result.txt"
    return Response(content, mimetype='text/plain', headers={
        'Content-Disposition': f'attachment; filename={filename}'
    })


# ─── Leaderboard ────────────────────────────────────────────

@bp.route('/leaderboard')
def leaderboard():
    contest_id = request.args.get('contest_id', type=int)
    contests = Contest.query.order_by(Contest.name).all()

    # Check if scoreboard is frozen
    frozen = False
    freeze_until = None
    now = datetime.utcnow()
    if contest_id:
        contest = Contest.query.get(contest_id)
    else:
        contest = Contest.query.filter_by(status='running').first()
    if contest and contest.status == 'running' and contest.freeze_before_end and contest.end_at:
        freeze_start = contest.end_at - timedelta(minutes=contest.freeze_before_end)
        if freeze_start <= now < contest.end_at:
            frozen = True
            freeze_until = contest.end_at

    if contest_id:
        teams = Team.query.all()
        rows = []
        for t in teams:
            # Count solved challenges for this contest
            contest_challenges = Challenge.query.filter_by(contest_id=contest_id).all()
            ch_ids = [ch.id for ch in contest_challenges]
            if ch_ids:
                solved = db.session.query(func.count(func.distinct(Submission.challenge_id))).filter(
                    Submission.team_id == t.id,
                    Submission.challenge_id.in_(ch_ids),
                    Submission.is_correct == True
                ).scalar() or 0
            else:
                solved = 0
            rows.append((t.name, t.attack_score or 0, t.defense_score or 0,
                         t.score or 0, solved))
        rows.sort(key=lambda x: -x[3])
        return render_template('leaderboard.html', rows=rows, contest_id=contest_id,
                               contests=contests, is_contest=True, frozen=frozen,
                               freeze_until=freeze_until)

    # Global leaderboard
    teams = Team.query.all()
    rows = []
    for t in teams:
        solved = db.session.query(func.count(func.distinct(Submission.challenge_id))).filter(
            Submission.team_id == t.id,
            Submission.is_correct == True
        ).scalar() or 0
        rows.append((t.name, t.attack_score or 0, t.defense_score or 0,
                     t.score or 0, solved))
    rows.sort(key=lambda x: -x[3])
    return render_template('leaderboard.html', rows=rows, contests=contests,
                           is_contest=False, frozen=frozen, freeze_until=freeze_until)


# ─── Contest Detail ─────────────────────────────────────────

@bp.route('/contest/<int:contest_id>')
def contest_detail(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    rounds = contest.rounds.order_by(ContestRound.round_number).all()
    challenges = contest.challenges.filter_by(enabled=True).all()

    team_containers = {}
    if current_user.is_authenticated and hasattr(current_user, 'name'):
        for c in Container.query.filter_by(team_id=current_user.id).all():
            team_containers[c.challenge_id] = c

    return render_template('contest_detail.html', contest=contest, rounds=rounds,
                           challenges=challenges, team_containers=team_containers)


# ─── Viz API ────────────────────────────────────────────────

@bp.route('/api/viz_data')
def viz_data():
    """JSON endpoint for the visualization page to fetch initial data."""
    teams = []
    for t in Team.query.filter_by(is_admin=False).order_by(Team.id).all():
        teams.append({
            'id': t.id, 'name': t.name, 'score': t.score or 0,
            'attack_score': t.attack_score or 0, 'defense_score': t.defense_score or 0,
        })
    challenges = []
    for c in Challenge.query.filter_by(enabled=True).order_by(Challenge.id).all():
        challenges.append({
            'id': c.id, 'title': c.title, 'category': c.category,
        })
    return jsonify({'teams': teams, 'challenges': challenges})


# ─── SPA Catch-all ──────────────────────────────────────────

@bp.route('/<path:path>', methods=['GET'])
def serve_spa(path):
    """Serve Vue SPA for client-side routing."""
    if path.startswith('api/') or path.startswith('auth/'):
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    dist_dir = os.path.join(basedir, 'frontend', 'dist')
    file_path = os.path.join(dist_dir, path)
    if os.path.isfile(file_path):
        return send_from_directory(dist_dir, path)
    index_path = os.path.join(dist_dir, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(dist_dir, 'index.html')
    return render_template('index.html')
