"""
Asteroid visualization integration client.
Sends events to Asteroid_backend for real-time big-screen CTF visualization.

Asteroid_backend endpoints (auth via Authorization header with raw token):
  POST /attack  {"From": team_id, "To": team_id}
  POST /rank    {"Team": [{"Id": int, "Name": str, "Rank": int, "Score": int, "Image": str}]}
  POST /status  {"Id": team_id, "Status": "online"|"offline"}
  POST /round   {"Round": int}
  POST /clear   {"Id": team_id}
"""
import os
import threading
import logging

import requests

logger = logging.getLogger(__name__)

_ASTEROID_URL = None
_ASTEROID_TOKEN = None


def _get_config():
    global _ASTEROID_URL, _ASTEROID_TOKEN
    if _ASTEROID_URL is None:
        _ASTEROID_URL = os.environ.get('ASTEROID_URL', 'http://127.0.0.1:8080')
    if _ASTEROID_TOKEN is None:
        _ASTEROID_TOKEN = os.environ.get('ASTEROID_TOKEN', '')
        if not _ASTEROID_TOKEN:
            # Fallback: read from token file
            try:
                with open(os.environ.get('ASTEROID_TOKEN_FILE', 'asteroid_token.txt')) as f:
                    _ASTEROID_TOKEN = f.read().strip()
            except Exception:
                logger.debug('No Asteroid token file found')
    return _ASTEROID_URL, _ASTEROID_TOKEN


def _post(path, data):
    """Fire-and-forget POST to Asteroid_backend."""
    def _do():
        try:
            url, token = _get_config()
            headers = {}
            if token:
                headers['Authorization'] = token  # raw token, no "Bearer " prefix
            requests.post(f"{url}{path}", json=data, headers=headers, timeout=3)
        except Exception as e:
            logger.debug("Asteroid %s failed: %s", path, e)
    threading.Thread(target=_do, daemon=True).start()


def send_attack(attacker_team_id, victim_team_id):
    """Send attack event: attacker exploited victim's container."""
    _post('/attack', {"From": attacker_team_id, "To": victim_team_id})


def send_break(team_id, challenge_id, challenge_title=''):
    """Send break event: team successfully broke a challenge."""
    _post('/attack', {"From": team_id, "To": challenge_id})


def send_fix(team_id, challenge_id, challenge_title=''):
    """Send fix event: team successfully patched a challenge."""
    _post('/fix', {"Team": team_id, "Challenge": challenge_id})


def send_rank(teams):
    """Send full team ranking.

    teams: list of Team model objects (uses .id, .name, .score).
    Rank order is by score descending.
    """
    sorted_teams = sorted(teams, key=lambda x: -(x.score or 0))
    team_list = [
        {"Id": t.id, "Name": t.name, "Rank": i + 1,
         "Score": int(t.score or 0), "AttackScore": int(t.attack_score or 0),
         "DefenseScore": int(t.defense_score or 0), "Image": ""}
        for i, t in enumerate(sorted_teams)
    ]
    _post('/rank', {"Team": team_list})


def send_status(team_id, status):
    """Send container status: 'online' or 'offline'."""
    _post('/status', {"Id": team_id, "Status": status})


def send_round(round_number):
    """Send round change event."""
    _post('/round', {"Round": round_number})


def send_clear(team_id):
    """Clear attack records for a team."""
    _post('/clear', {"Id": team_id})


def write_challenge_txt(filepath, challenges=None):
    """Write challenge.txt for Asteroid_backend.

    Format: one "name,id" per line — the patched Asteroid_backend
    loadChallenges() reads the id for consistent challenge identification.
    If challenges is None, queries the database directly (requires app context).
    """
    if challenges is None:
        from app.models import Challenge
        challenges = Challenge.query.order_by(Challenge.id).all()
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w') as f:
        for c in challenges:
            f.write(f"{c.title},{c.id}\n")


def write_team_txt(filepath, teams=None):
    """Write team.txt for Asteroid_backend.

    Format: one "name,id" per line — the patched Asteroid_backend
    loadTeams() reads the id for consistent team identification.
    If teams is None, queries the database directly (requires app context).
    """
    if teams is None:
        from app.models import Team
        teams = Team.query.order_by(Team.id).all()
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(filepath, 'w') as f:
        for t in teams:
            f.write(f"{t.name},{t.id}\n")
