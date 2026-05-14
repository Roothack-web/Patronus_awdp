from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from datetime import datetime
import os
import logging


db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'


@login.unauthorized_handler
def unauthorized():
    """Return JSON for API requests, redirect HTML for others."""
    from flask import request, jsonify
    if request.path.startswith('/api/'):
        return jsonify({'ok': False, 'error': '请先登录'}), 401
    return '请先登录', 302

def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'),
                static_url_path='/static')
    app.config.from_object(config_class)

    # Logging setup
    log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    # Silence noisy libs
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    db.init_app(app)
    login.init_app(app)

    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.admin import bp as admin_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp)

    # Context processor: pass active contests to all templates
    @app.context_processor
    def inject_global():
        from app.models import Contest
        now = datetime.utcnow()
        running = Contest.query.filter_by(status='running').first()
        ctx = {'active_contest': None}
        if running:
            remaining = int((running.end_at - now).total_seconds()) if running.end_at else 0
            ctx['active_contest'] = {
                'id': running.id,
                'name': running.name,
                'end_at': running.end_at.isoformat() if running.end_at else '',
                'remaining_seconds': max(remaining, 0),
            }
        return ctx

    return app
