from flask import Blueprint, jsonify
from functools import wraps
from flask_login import current_user

api_bp = Blueprint('api', __name__, url_prefix='/api')


def team_required_api(f):
    """JSON-error variant of team_required for API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'ok': False, 'error': '请先登录'}), 401
        if not hasattr(current_user, 'name'):
            return jsonify({'ok': False, 'error': '需要队伍账号'}), 403
        return f(*args, **kwargs)
    return decorated


from app.api import auth
from app.api import challenges
from app.api import containers
from app.api import defenses
from app.api import leaderboard
from app.api import contests
