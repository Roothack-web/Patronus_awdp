from flask import jsonify
from flask_login import current_user
from sqlalchemy import func
from datetime import datetime

from app.models import Contest, Challenge, Submission, Container, ContestRound
from app import db
from app.api import api_bp, team_required_api


@api_bp.route('/contests')
@team_required_api
def list_contests():
    contests = Contest.query.order_by(Contest.start_at.desc()).all()
    now = datetime.utcnow()
    data = []
    for c in contests:
        ch_count = Challenge.query.filter_by(contest_id=c.id, enabled=True).count()
        remaining = 0
        if c.status == 'running' and c.end_at:
            remaining = max(int((c.end_at - now).total_seconds()), 0)
        data.append({
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'status': c.status,
            'challenge_count': ch_count,
            'start_at': c.start_at.isoformat() if c.start_at else None,
            'end_at': c.end_at.isoformat() if c.end_at else None,
            'remaining_seconds': remaining,
        })
    return jsonify({'ok': True, 'data': data})


@api_bp.route('/contests/<int:contest_id>')
@team_required_api
def contest_detail(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    now = datetime.utcnow()
    challenges = Challenge.query.filter_by(
        contest_id=contest.id, enabled=True).order_by(Challenge.id).all()

    team = current_user if hasattr(current_user, 'name') else None
    solved_ids = set()
    team_containers = {}
    if team:
        for s in Submission.query.filter_by(team_id=team.id, is_correct=True).all():
            solved_ids.add(s.challenge_id)
        for ct in Container.query.filter_by(team_id=team.id).all():
            team_containers[ct.challenge_id] = ct

    ch_data = []
    for c in challenges:
        solve_count = db.session.query(func.count(func.distinct(Submission.team_id))).filter(
            Submission.challenge_id == c.id,
            Submission.is_correct == True
        ).scalar() or 0
        ch_data.append({
            'id': c.id,
            'title': c.title,
            'category': c.category,
            'description': c.description,
            'initial_score': c.initial_score or c.points,
            'solve_count': solve_count,
            'solved': c.id in solved_ids,
            'container_status': team_containers.get(c.id).status if team_containers.get(c.id) else None,
        })

    remaining = 0
    if contest.status == 'running' and contest.end_at:
        remaining = max(int((contest.end_at - now).total_seconds()), 0)

    # Rounds
    rounds = []
    for r in contest.rounds.order_by(ContestRound.round_number).all():
        rounds.append({
            'id': r.id,
            'name': r.name,
            'round_number': r.round_number,
            'status': r.status,
            'start_at': r.start_at.isoformat() if r.start_at else None,
            'end_at': r.end_at.isoformat() if r.end_at else None,
        })

    return jsonify({'ok': True, 'data': {
        'id': contest.id,
        'name': contest.name,
        'description': contest.description,
        'status': contest.status,
        'start_at': contest.start_at.isoformat() if contest.start_at else None,
        'end_at': contest.end_at.isoformat() if contest.end_at else None,
        'remaining_seconds': remaining,
        'challenges': ch_data,
        'rounds': rounds,
    }})
