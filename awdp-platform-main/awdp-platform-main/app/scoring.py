from app.models import Submission, Team, ScoreLog, Challenge, ContestRound, Defense
from app import db
from datetime import datetime
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


def _notify_rank():
    """Fire-and-forget rank notification to Asteroid visualization."""
    try:
        from app.asteroid_client import send_rank
        all_teams = Team.query.all()
        send_rank(all_teams)
    except Exception:
        logger.debug('Rank notification failed (visualization optional)')


def _notify_break(team, challenge):
    """Notify visualization of a break event."""
    try:
        from app.asteroid_client import send_break
        send_break(team.id, challenge.id, challenge.title)
    except Exception:
        logger.debug('Break notification failed (visualization optional)')

def _notify_fix(team, challenge):
    """Notify visualization of a fix event."""
    try:
        from app.asteroid_client import send_fix
        send_fix(team.id, challenge.id, challenge.title)
    except Exception:
        logger.debug('Fix notification failed (visualization optional)')


# Rank bonus multiplier per solve rank (top 20)
RANK_BONUS = [
    0.05, 0.049, 0.048, 0.047, 0.046,
    0.045, 0.044, 0.043, 0.042, 0.041,
    0.04, 0.039, 0.038, 0.037, 0.036,
    0.035, 0.034, 0.033, 0.032, 0.031,
]


def compute_break_score(challenge, team):
    """
    Standard AWDP Break scoring:
    BreakScore = max(initial_score - (solve_count - 1) * score_decay, min_score)
    Plus rank bonus for top 20 solvers.

    Returns: (score_earned, solve_rank)
    """
    initial_score = challenge.initial_score or challenge.points or 500
    min_score = challenge.min_score or 100
    score_decay = challenge.score_decay or 50

    # Count prior distinct solvers (teams that already solved this challenge)
    prev_solvers = db.session.query(func.count(func.distinct(Submission.team_id))).filter(
        Submission.challenge_id == challenge.id,
        Submission.is_correct == True
    ).scalar() or 0

    solve_rank = prev_solvers + 1

    # Dynamic base score
    base = max(initial_score - (solve_rank - 1) * score_decay, min_score)

    # Rank bonus for top 20
    bonus = 0.0
    if 1 <= solve_rank <= len(RANK_BONUS):
        bonus = initial_score * RANK_BONUS[solve_rank - 1]

    total = base + bonus
    return round(total, 2), solve_rank


def compute_defense_score(challenge):
    """
    AWDP Defense scoring: fixed base score per successful fix.
    """
    return challenge.fix_base_score or 300


def award_break_score(team, challenge, score_earned, reason=''):
    """Award break score to a team and log it."""
    before = team.score or 0.0
    team.score = (team.score or 0.0) + score_earned
    team.attack_score = (team.attack_score or 0.0) + score_earned
    db.session.flush()

    log = ScoreLog(
        team_id=team.id, challenge_id=challenge.id,
        score_type='attack', score_delta=score_earned,
        score_before=before, score_after=team.score,
        reason=reason or f'Break: {challenge.title}'
    )
    db.session.add(log)
    _notify_rank()
    _notify_break(team, challenge)
    return score_earned


def award_defense_score(team, challenge, score_earned, defense_id=None, reason=''):
    """Award defense score to a team and log it."""
    before = team.score or 0.0
    team.score = (team.score or 0.0) + score_earned
    team.defense_score = (team.defense_score or 0.0) + score_earned
    db.session.flush()

    log = ScoreLog(
        team_id=team.id, challenge_id=challenge.id,
        score_type='defense', score_delta=score_earned,
        score_before=before, score_after=team.score,
        reason=reason or f'Fix: {challenge.title}'
    )
    db.session.add(log)
    _notify_rank()
    _notify_fix(team, challenge)
    return score_earned


def apply_penalty(team, challenge, penalty=50, reason=''):
    """Apply a penalty (e.g., for service downtime)."""
    before = team.score or 0.0
    penalty = -abs(penalty)
    team.score = max(0, (team.score or 0.0) + penalty)
    team.defense_score = max(0, (team.defense_score or 0.0) + penalty)
    db.session.flush()

    log = ScoreLog(
        team_id=team.id, challenge_id=challenge.id,
        score_type='penalty', score_delta=penalty,
        score_before=before, score_after=team.score,
        reason=reason or f'Penalty: {challenge.title}'
    )
    db.session.add(log)
    _notify_rank()
    return penalty
