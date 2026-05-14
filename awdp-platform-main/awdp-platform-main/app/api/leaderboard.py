from flask import jsonify, request
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models import Team, Submission, Challenge, Contest
from app import db
from app.api import api_bp


@api_bp.route('/leaderboard')
@login_required
def leaderboard():
    contest_id = request.args.get('contest_id', type=int)

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
            freeze_until = contest.end_at.isoformat() if contest.end_at else None

    teams = Team.query.all()
    rows = []

    for t in teams:
        if contest_id:
            ch_ids = [ch.id for ch in Challenge.query.filter_by(contest_id=contest_id).all()]
            if ch_ids:
                solved = db.session.query(func.count(func.distinct(Submission.challenge_id))).filter(
                    Submission.team_id == t.id,
                    Submission.challenge_id.in_(ch_ids),
                    Submission.is_correct == True
                ).scalar() or 0
            else:
                solved = 0
        else:
            solved = db.session.query(func.count(func.distinct(Submission.challenge_id))).filter(
                Submission.team_id == t.id,
                Submission.is_correct == True
            ).scalar() or 0

        rows.append({
            'team_name': t.name,
            'attack_score': t.attack_score or 0,
            'defense_score': t.defense_score or 0,
            'score': t.score or 0,
            'solved': solved,
        })

    rows.sort(key=lambda x: -x['score'])

    # Add rank
    for i, r in enumerate(rows):
        r['rank'] = i + 1

    return jsonify({'ok': True, 'data': {
        'rows': rows,
        'frozen': frozen,
        'freeze_until': freeze_until,
    }})
