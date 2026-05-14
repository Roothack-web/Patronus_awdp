from flask import jsonify, request, Response
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
import io
import tarfile
import os

from app.models import Challenge, Submission, Team, Container, Defense, FlagHistory, ScoreLog
from app.scoring import compute_break_score, award_break_score
from app import db
from app.api import api_bp, team_required_api
from app.main import contest_not_ended, detect_flag_cheat, penalize_cheat, get_active_round
from config import basedir


@api_bp.route('/challenges')
@login_required
def list_challenges():
    if not hasattr(current_user, 'name'):
        return jsonify({'ok': False, 'error': '需要队伍账号'}), 403

    challenges = Challenge.query.filter_by(enabled=True).filter(
        Challenge.contest_id.isnot(None)).order_by(Challenge.id).all()
    team = current_user

    # Get all solves by this team
    solved_ids = set()
    for s in Submission.query.filter_by(team_id=team.id, is_correct=True).all():
        solved_ids.add(s.challenge_id)

    data = []
    for c in challenges:
        solve_count = db.session.query(func.count(func.distinct(Submission.team_id))).filter(
            Submission.challenge_id == c.id,
            Submission.is_correct == True
        ).scalar() or 0

        if solve_count:
            dynamic_score = max(
                (c.initial_score or c.points) - (solve_count - 1) * (c.score_decay or 50),
                c.min_score or 100
            )
        else:
            dynamic_score = c.initial_score or c.points

        data.append({
            'id': c.id,
            'title': c.title,
            'category': c.category,
            'description': c.description,
            'initial_score': c.initial_score or c.points,
            'dynamic_score': dynamic_score,
            'solve_count': solve_count,
            'solved': c.id in solved_ids,
            'is_fixed': c.is_fixed,
            'contest_id': c.contest_id,
            'docker_image': c.docker_image,
            'docker_port': c.docker_port,
        })

    return jsonify({'ok': True, 'data': data})


@api_bp.route('/challenges/<int:challenge_id>')
@login_required
def challenge_detail(challenge_id):
    if not hasattr(current_user, 'name'):
        return jsonify({'ok': False, 'error': '需要队伍账号'}), 403

    c = Challenge.query.get_or_404(challenge_id)
    team = current_user

    if not c.contest_id:
        return jsonify({'ok': False, 'error': '题目未关联比赛'}), 403

    team_container = Container.query.filter_by(
        challenge_id=c.id, team_id=team.id).first()
    prev = Submission.query.filter_by(
        team_id=team.id, challenge_id=c.id, is_correct=True).first()
    already_correct = bool(prev)

    # Per-team fix status
    already_fixed = bool(Defense.query.filter_by(
        team_id=team.id, challenge_id=c.id, status='success').first())

    # Count solvers
    solve_count = db.session.query(func.count(func.distinct(Submission.team_id))).filter(
        Submission.challenge_id == c.id,
        Submission.is_correct == True
    ).scalar() or 0

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
            'time': s.submitted_at.isoformat() if s.submitted_at else None,
        })

    # Recent submissions
    submissions = []
    for s in Submission.query.filter_by(challenge_id=c.id).order_by(
            Submission.submitted_at.desc()).limit(20).all():
        t = Team.query.get(s.team_id)
        submissions.append({
            'id': s.id,
            'team_name': t.name if t else '?',
            'is_correct': s.is_correct,
            'score_earned': s.score_earned,
            'submitted_at': s.submitted_at.isoformat() if s.submitted_at else None,
        })

    # Defenses
    defenses = []
    for d in Defense.query.filter_by(challenge_id=c.id).order_by(
            Defense.created_at.desc()).all():
        t = Team.query.get(d.team_id)
        defenses.append({
            'id': d.id,
            'team_name': t.name if t else '?',
            'status': d.status,
            'attempt_number': d.attempt_number,
            'created_at': d.created_at.isoformat() if d.created_at else None,
        })

    active_round = None
    if c.contest_id:
        r = get_active_round(c.contest_id)
        if r:
            active_round = {
                'id': r.id,
                'name': r.name,
                'round_number': r.round_number,
                'start_at': r.start_at.isoformat() if r.start_at else None,
                'end_at': r.end_at.isoformat() if r.end_at else None,
            }

    contest_ended = contest_not_ended(c) if c.contest else False

    container_data = None
    if team_container:
        container_data = {
            'id': team_container.id,
            'status': team_container.status,
            'public_host': team_container.public_host,
            'public_port': team_container.public_port,
            'flag_version': team_container.flag_version,
            'reset_count': team_container.reset_count,
            'max_resets': team_container.max_resets,
            'started_at': team_container.started_at.isoformat() if team_container.started_at else None,
        }

    return jsonify({'ok': True, 'data': {
        'challenge': {
            'id': c.id,
            'title': c.title,
            'category': c.category,
            'description': c.description,
            'initial_score': c.initial_score or c.points,
            'dynamic_score': dynamic_score,
            'solve_count': solve_count,
            'is_fixed': c.is_fixed,
            'contest_id': c.contest_id,
            'docker_image': c.docker_image,
            'docker_port': c.docker_port,
        },
        'container': container_data,
        'already_correct': already_correct,
        'already_fixed': already_fixed,
        'bloods': bloods,
        'submissions': submissions,
        'defenses': defenses,
        'active_round': active_round,
        'contest_ended': contest_ended,
    }})


@api_bp.route('/challenges/<int:challenge_id>/flag', methods=['POST'])
@login_required
@team_required_api
def submit_flag(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    team = current_user

    if not c.contest_id:
        return jsonify({'ok': False, 'error': '题目未关联比赛'}), 403
    if contest_not_ended(c):
        return jsonify({'ok': False, 'error': '比赛已结束，无法提交 Flag'}), 403

    data = request.get_json(silent=True) or {}
    submitted = data.get('flag', '').strip()
    if not submitted:
        return jsonify({'ok': False, 'error': 'Flag 不能为空'}), 400

    # Rate limit: 1 submission per 3 seconds
    recent = Submission.query.filter_by(
        team_id=team.id, challenge_id=c.id
    ).order_by(Submission.submitted_at.desc()).first()
    if recent and (datetime.utcnow() - recent.submitted_at).total_seconds() < 3:
        return jsonify({'ok': False, 'error': '提交过于频繁，请稍后再试'}), 429

    team_container = Container.query.filter_by(
        challenge_id=c.id, team_id=team.id).first()

    correct = False
    score_earned = 0
    solve_rank = 0

    if not team_container or team_container.status != 'running':
        return jsonify({'ok': False, 'error': '请先启动容器获取 Flag'}), 400
    if submitted == team_container.current_flag:
        correct = True
    else:
        cheat = detect_flag_cheat(c.id, submitted, team)
        if cheat:
            penalize_cheat(team, c, submitted, victim_container=cheat)
            sub = Submission(team_id=team.id, challenge_id=c.id,
                             container_id=cheat.id,
                             flag_submitted=submitted, is_correct=False)
            db.session.add(sub)
            db.session.commit()
            return jsonify({'ok': False, 'error': 'Flag 不正确'}), 400
        expired = FlagHistory.query.filter_by(
            container_id=team_container.id, flag=submitted).first()
        if expired:
            return jsonify({'ok': False, 'error': 'Flag 已过期，请重新获取'}), 400

    if not correct:
        sub = Submission(team_id=team.id, challenge_id=c.id,
                         flag_submitted=submitted, is_correct=False)
        db.session.add(sub)
        db.session.commit()
        return jsonify({'ok': False, 'error': 'Flag 不正确'}), 400

    # Check already solved
    prev_correct = Submission.query.filter_by(
        team_id=team.id, challenge_id=c.id, is_correct=True).first()
    if prev_correct:
        return jsonify({'ok': False, 'error': '你已正确提交过此题'}), 409

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

    from app.models import Team as TeamModel
    from app.asteroid_client import send_rank
    send_rank(TeamModel.query.all())

    return jsonify({'ok': True, 'data': {
        'score_earned': score_earned,
        'solve_rank': solve_rank,
        'message': f'提交正确！第 {solve_rank} 个解出，得分 +{score_earned}',
    }})


@api_bp.route('/challenges/<int:challenge_id>/source')
def download_source(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)

    img = c.docker_image or ''
    base = img.split(':')[0]
    dir_name = base.replace('awdp-', '', 1) if base.startswith('awdp-') else base
    dir_name = dir_name.replace('-', '_')
    source_dir = os.path.join(basedir, 'challenges', dir_name)

    if not os.path.isdir(source_dir):
        return jsonify({'ok': False, 'error': '源码目录不存在'}), 404

    exclude = {'exploit.sh', 'exp.py', 'exploit.py'}

    def generate():
        import subprocess as sp
        cmd = ['tar', 'czf', '-']
        for e in exclude:
            cmd.extend(['--exclude', e])
        cmd.extend(['-C', source_dir, '.'])
        proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL)
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk:
                break
            yield chunk
        proc.wait()

    filename = f"{dir_name}-source.tar.gz"
    return Response(generate(), mimetype='application/gzip',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})
