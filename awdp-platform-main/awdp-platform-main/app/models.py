from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Team(UserMixin, db.Model):
    """Team is the primary player entity in AWDP."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    token = db.Column(db.String(256), unique=True)
    is_admin = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float, default=0.0)
    attack_score = db.Column(db.Float, default=0.0)
    defense_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('User', backref='team', lazy='dynamic')
    submissions = db.relationship('Submission', backref='team', lazy='dynamic')
    defenses = db.relationship('Defense', backref='team', lazy='dynamic')
    containers = db.relationship('Container', backref='team', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"team_{self.id}"


@login.user_loader
def load_user(id):
    if id and id.startswith('team_'):
        return Team.query.get(int(id[5:]))
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    """Team member (optional, for multi-member teams)."""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_leader = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(32), default='web')
    description = db.Column(db.Text)
    points = db.Column(db.Integer, default=500)
    # Docker config
    docker_image = db.Column(db.String(256), default='')
    docker_port = db.Column(db.Integer, default=80)
    internal_port = db.Column(db.Integer, default=80)
    # AWDP scoring config
    initial_score = db.Column(db.Integer, default=500)
    min_score = db.Column(db.Integer, default=100)
    score_decay = db.Column(db.Integer, default=50)
    # Fix / defense config
    exp_cmd = db.Column(db.String(500))
    fix_base_score = db.Column(db.Integer, default=300)
    max_resets = db.Column(db.Integer, default=10)
    # Status
    enabled = db.Column(db.Boolean, default=True)
    is_fixed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Contest
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=True)


class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    status = db.Column(db.String(32), default='pending')
    freeze_before_end = db.Column(db.Integer, default=30)  # minutes before end to freeze
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    challenges = db.relationship('Challenge', backref='contest', lazy='dynamic')
    rounds = db.relationship('ContestRound', backref='contest', lazy='dynamic')


class ContestRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False, default=1)
    name = db.Column(db.String(140), nullable=False)
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    status = db.Column(db.String(32), default='pending')
    multiplier = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Container(db.Model):
    """Docker container per team per challenge."""
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    docker_container_id = db.Column(db.String(256))
    container_name = db.Column(db.String(256))
    public_host = db.Column(db.String(256), default='127.0.0.1')
    public_port = db.Column(db.Integer)
    status = db.Column(db.String(32), default='stopped')
    current_flag = db.Column(db.String(256), default='')
    flag_version = db.Column(db.Integer, default=0)
    flag_expires_at = db.Column(db.DateTime)
    reset_count = db.Column(db.Integer, default=0)
    max_resets = db.Column(db.Integer, default=10)
    started_at = db.Column(db.DateTime)
    stopped_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    challenge = db.relationship('Challenge', backref=db.backref('containers', lazy='dynamic'))
    __table_args__ = (db.UniqueConstraint('challenge_id', 'team_id', name='_challenge_team_uc'),)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=True)
    flag_submitted = db.Column(db.String(500))
    is_correct = db.Column(db.Boolean, default=False)
    score_earned = db.Column(db.Float, default=0.0)
    ip_address = db.Column(db.String(64))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    challenge = db.relationship('Challenge', backref=db.backref('submissions', lazy='dynamic'))


class Defense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    filename = db.Column(db.String(260))
    file_path = db.Column(db.String(500))
    file_hash = db.Column(db.String(128))
    file_size = db.Column(db.Integer, default=0)
    attempt_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(32), default='uploaded')
    result = db.Column(db.Text)
    defense_score_earned = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    challenge = db.relationship('Challenge', backref=db.backref('defenses', lazy='dynamic'))


class ScoreLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=True)
    score_type = db.Column(db.String(32), nullable=False)
    score_delta = db.Column(db.Float, nullable=False)
    score_before = db.Column(db.Float, nullable=False)
    score_after = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CheckResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)
    check_type = db.Column(db.String(32), default='health')
    status = db.Column(db.String(32), default='up')
    response_time_ms = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)


class FlagHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey('container.id'), nullable=False)
    flag = db.Column(db.String(256), nullable=False)
    version = db.Column(db.Integer, default=1)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)


class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(128), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(512))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
