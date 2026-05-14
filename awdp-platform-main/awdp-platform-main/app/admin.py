from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
import csv
import io
from flask_login import login_required, current_user
from app.models import Challenge, Submission, Team, Defense, Contest, ContestRound, Container, CheckResult, ScoreLog
from app.forms import ChallengeForm, ContestForm, ContestRoundForm
from app import db
from sqlalchemy import func
from datetime import datetime, timedelta
import os
import subprocess
import sys
from config import basedir
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, template_folder='../templates')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@bp.route('/')
@login_required
@admin_required
def index():
    from app.models import SystemConfig
    stats = {
        'teams': Team.query.count(),
        'challenges': Challenge.query.count(),
        'containers': Container.query.count(),
        'submissions': Submission.query.count(),
        'defenses': Defense.query.count(),
        'running_containers': Container.query.filter_by(status='running').count(),
    }
    recent_submissions = Submission.query.order_by(
        Submission.submitted_at.desc()).limit(10).all()

    # Scheduler status
    scheduler_cfg = SystemConfig.query.filter_by(key='scheduler_last_run').first()
    scheduler_last_run = scheduler_cfg.value if scheduler_cfg else None

    # Pending defenses count
    pending_defenses = Defense.query.filter(
        Defense.status.in_(['uploaded', 'queued', 'running'])).count()

    return render_template('admin_dashboard.html', stats=stats,
                           recent_submissions=recent_submissions,
                           scheduler_last_run=scheduler_last_run,
                           pending_defenses=pending_defenses)


# ─── Team Management ───────────────────────────────────────

@bp.route('/teams')
@login_required
@admin_required
def teams():
    items = Team.query.order_by(Team.created_at.desc()).all()
    return render_template('admin_teams.html', teams=items)


@bp.route('/teams/<int:team_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(team_id):
    team = Team.query.get_or_404(team_id)
    team.is_admin = not team.is_admin
    db.session.commit()
    flash(f'队伍 {team.name} 管理员状态已切换')
    return redirect(url_for('admin.teams'))


@bp.route('/teams/<int:team_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_team_password(team_id):
    team = Team.query.get_or_404(team_id)
    new_pass = request.form.get('new_password', '')
    if new_pass:
        team.set_password(new_pass)
        db.session.commit()
        flash(f'队伍 {team.name} 密码已重置')
    return redirect(url_for('admin.teams'))


# ─── Challenge Management ──────────────────────────────────

@bp.route('/challenges/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_challenge():
    form = ChallengeForm()
    form.contest_id.choices = [(0, '(无)')] + [
        (ct.id, ct.name) for ct in Contest.query.order_by(Contest.name).all()
    ]
    if form.validate_on_submit():
        c = Challenge(
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            points=form.initial_score.data or 500,
            initial_score=form.initial_score.data or 500,
            docker_image=form.docker_image.data or '',
            docker_port=form.docker_port.data or 0,
            internal_port=form.internal_port.data or 80,
            min_score=form.min_score.data or 100,
            score_decay=form.score_decay.data or 50,
            exp_cmd=form.exp_cmd.data or '',
            fix_base_score=form.fix_base_score.data or 300,
            max_resets=form.max_resets.data or 10,
            enabled=form.enabled.data if form.enabled.data is not None else True,
            is_fixed=form.is_fixed.data if form.is_fixed.data is not None else False,
        )
        cid = form.contest_id.data
        c.contest_id = cid if cid and cid != 0 else None
        db.session.add(c)
        db.session.commit()
        flash('题目已创建')
        return redirect(url_for('admin.challenges'))
    return render_template('add_challenge.html', form=form, edit_mode=False)


@bp.route('/challenges')
@login_required
@admin_required
def challenges():
    items = Challenge.query.order_by(Challenge.created_at.desc()).all()
    return render_template('admin_challenges.html', challenges=items)


@bp.route('/challenges/<int:challenge_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_challenge(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=c)
    form.contest_id.choices = [(0, '(无)')] + [
        (ct.id, ct.name) for ct in Contest.query.order_by(Contest.name).all()
    ]
    if form.validate_on_submit():
        c.title = form.title.data
        c.category = form.category.data
        c.description = form.description.data
        c.points = form.initial_score.data or 500
        c.initial_score = form.initial_score.data or 500
        c.docker_image = form.docker_image.data
        c.docker_port = form.docker_port.data or 0
        c.internal_port = form.internal_port.data or 80
        c.min_score = form.min_score.data or 100
        c.score_decay = form.score_decay.data or 50
        c.exp_cmd = form.exp_cmd.data
        c.fix_base_score = form.fix_base_score.data or 300
        c.max_resets = form.max_resets.data or 10
        c.enabled = form.enabled.data if form.enabled.data is not None else True
        c.is_fixed = form.is_fixed.data if form.is_fixed.data is not None else False
        cid = form.contest_id.data
        c.contest_id = cid if cid and cid != 0 else None
        db.session.commit()
        flash('题目已更新')
        return redirect(url_for('admin.challenges'))
    form.contest_id.data = c.contest_id or 0
    return render_template('add_challenge.html', form=form, edit_mode=True, challenge=c)


# ─── Submission Management ─────────────────────────────────

@bp.route('/submissions')
@login_required
@admin_required
def submissions():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = Submission.query.order_by(
        Submission.submitted_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items
    return render_template('admin_submissions.html', submissions=items, pagination=pagination)


# ─── Defense Management ────────────────────────────────────

@bp.route('/defenses')
@login_required
@admin_required
def defenses():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = Defense.query.order_by(
        Defense.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items
    return render_template('admin_defenses.html', defenses=items, pagination=pagination)


@bp.route('/defenses/pending')
@login_required
@admin_required
def defenses_pending():
    """View all pending/queued defenses."""
    items = Defense.query.filter(
        Defense.status.in_(['uploaded', 'queued', 'running'])
    ).order_by(Defense.created_at.asc()).all()
    return render_template('admin_defenses.html', defenses=items, pending_only=True)


@bp.route('/defenses/<int:def_id>/evaluate', methods=['POST'])
@login_required
@admin_required
def evaluate(def_id):
    d = Defense.query.get_or_404(def_id)
    if d.status in ('running', 'queued'):
        flash('该防护包正在评估或已排队')
        return redirect(url_for('admin.defenses'))
    d.status = 'queued'
    db.session.commit()

    script = os.path.join(basedir, 'evaluate_defense.py')
    try:
        with open(os.devnull, 'wb') as devnull:
            subprocess.Popen([sys.executable, script, str(d.id)],
                             stdout=devnull, stderr=devnull)
        flash('已开始后台评估')
    except Exception as e:
        d.status = 'error'
        d.result = f'启动评估失败: {e}'
        db.session.commit()
        flash(f'启动评估失败: {e}')
    return redirect(url_for('admin.defenses'))


# ─── Contest Management ────────────────────────────────────

@bp.route('/contests', methods=['GET', 'POST'])
@login_required
@admin_required
def contests():
    items = Contest.query.order_by(Contest.start_at.desc()).all()
    form = ContestForm()
    if form.validate_on_submit():
        c = Contest(name=form.name.data, description=form.description.data)
        try:
            if form.start_at.data:
                c.start_at = datetime.fromisoformat(form.start_at.data)
            if form.end_at.data:
                c.end_at = datetime.fromisoformat(form.end_at.data)
        except Exception:
            logger.warning('Invalid contest date format')
            flash('时间格式不正确，应为 ISO 格式')
            return render_template('admin_contests.html', contests=items, form=form)
        db.session.add(c)
        db.session.commit()
        flash('比赛已创建')
        return redirect(url_for('admin.contests'))
    return render_template('admin_contests.html', contests=items, form=form)


@bp.route('/contests/<int:contest_id>/start', methods=['POST'])
@login_required
@admin_required
def start_contest(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    contest.status = 'running'
    db.session.commit()
    flash('比赛已开始')
    return redirect(url_for('admin.contests'))


@bp.route('/contests/<int:contest_id>/end', methods=['POST'])
@login_required
@admin_required
def end_contest(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    contest.status = 'finished'
    db.session.commit()
    flash('比赛已结束')
    return redirect(url_for('admin.contests'))


@bp.route('/contests/<int:contest_id>/rounds', methods=['GET', 'POST'])
@login_required
@admin_required
def contest_rounds(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    form = ContestRoundForm()
    if form.validate_on_submit():
        try:
            # Auto-assign round number
            max_round = db.session.query(db.func.max(ContestRound.round_number)).filter(
                ContestRound.contest_id == contest.id).scalar() or 0
            r = ContestRound(contest_id=contest.id, name=form.name.data,
                             round_number=max_round + 1)
            if form.start_at.data:
                r.start_at = datetime.fromisoformat(form.start_at.data)
            if form.end_at.data:
                r.end_at = datetime.fromisoformat(form.end_at.data)
            if form.multiplier.data:
                r.multiplier = float(form.multiplier.data)
            r.status = 'pending'
        except Exception:
            logger.warning('Invalid round date format')
            flash('轮次数据格式不正确')
            return render_template('admin_rounds.html', contest=contest, form=form)
        db.session.add(r)
        db.session.commit()
        flash('轮次已添加')
        return redirect(url_for('admin.contest_rounds', contest_id=contest.id))
    rounds = contest.rounds.order_by(ContestRound.start_at.asc()).all()
    return render_template('admin_rounds.html', contest=contest, rounds=rounds, form=form)


@bp.route('/rounds/<int:round_id>/start', methods=['POST'])
@login_required
@admin_required
def start_round(round_id):
    r = ContestRound.query.get_or_404(round_id)
    r.status = 'running'
    db.session.commit()
    flash(f'轮次 {r.name} 已开始')
    return redirect(url_for('admin.contest_rounds', contest_id=r.contest_id))


@bp.route('/rounds/<int:round_id>/end', methods=['POST'])
@login_required
@admin_required
def end_round(round_id):
    r = ContestRound.query.get_or_404(round_id)
    r.status = 'finished'
    db.session.commit()
    flash(f'轮次 {r.name} 已结束')
    return redirect(url_for('admin.contest_rounds', contest_id=r.contest_id))


# ─── Container Management ──────────────────────────────────

@bp.route('/containers')
@login_required
@admin_required
def containers():
    items = Container.query.order_by(Container.created_at.desc()).all()
    # Enrich with real Docker status
    for c in items:
        if c.docker_container_id:
            try:
                from app.docker_manager import get_container_status
                d_status = get_container_status(c.docker_container_id)
                if d_status and d_status != c.status:
                    # Update DB to match real state
                    c.status = d_status
                    if d_status == 'running':
                        c.started_at = datetime.utcnow()
                    db.session.commit()
            except Exception:
                logger.warning('Failed to sync Docker status for container %s', c.id)
    return render_template('admin_containers.html', containers=items)


@bp.route('/containers/<int:container_id>/refresh-flag', methods=['POST'])
@login_required
@admin_required
def refresh_container_flag(container_id):
    container = Container.query.get_or_404(container_id)
    if container.status == 'running':
        from app.utils import generate_flag, flag_expiry_delta
        container.current_flag = generate_flag()
        container.flag_version += 1
        container.flag_expires_at = datetime.utcnow() + flag_expiry_delta()
        db.session.commit()
        flash('Flag 已刷新')
    return redirect(url_for('admin.containers'))


# ─── Score Logs ────────────────────────────────────────────

@bp.route('/export/scores.csv')
@login_required
@admin_required
def export_scores():
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['排名', '队伍', '攻击分', '防御分', '总分', '解题数'])
    teams = Team.query.order_by(Team.score.desc()).all()
    for i, t in enumerate(teams, 1):
        solved = db.session.query(func.count(func.distinct(Submission.challenge_id))).filter(
            Submission.team_id == t.id,
            Submission.is_correct == True
        ).scalar() or 0
        w.writerow([i, t.name, t.attack_score or 0, t.defense_score or 0,
                     t.score or 0, solved])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=scores.csv'})


@bp.route('/export/submissions.csv')
@login_required
@admin_required
def export_submissions():
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['ID', '队伍', '题目', 'Flag', '正确', '得分', '时间'])
    subs = Submission.query.order_by(Submission.submitted_at.desc()).limit(5000).all()
    for s in subs:
        team_name = s.team.name if s.team else '?'
        ch_title = s.challenge.title if s.challenge else '?'
        w.writerow([s.id, team_name, ch_title, s.flag_submitted,
                     '是' if s.is_correct else '否', s.score_earned, s.submitted_at])
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=submissions.csv'})


@bp.route('/scores')
@login_required
@admin_required
def scores():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    pagination = ScoreLog.query.order_by(
        ScoreLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    return render_template('admin_scores.html', logs=logs, pagination=pagination)
