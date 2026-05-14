import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'awdp-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'awdp.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    WTF_CSRF_TIME_LIMIT = None  # No CSRF time limit for long uploads
    PUBLIC_HOST = os.environ.get('PUBLIC_HOST') or '127.0.0.1'

    # Container / Flag settings
    FLAG_EXPIRY_MINUTES = int(os.environ.get('FLAG_EXPIRY_MINUTES', 5))
    DOCKER_PORT_START = int(os.environ.get('DOCKER_PORT_START', 30000))
    DOCKER_PORT_END = int(os.environ.get('DOCKER_PORT_END', 40000))
    DOCKER_NETWORK_NAME = os.environ.get('DOCKER_NETWORK_NAME', 'awdp-network')
    DOCKER_MEM_LIMIT = os.environ.get('DOCKER_MEM_LIMIT', '512m')
    DOCKER_CPU_QUOTA = int(os.environ.get('DOCKER_CPU_QUOTA', 100000))

    # Defense settings
    DEFENSE_MAX_ATTEMPTS = int(os.environ.get('DEFENSE_MAX_ATTEMPTS', 10))

    # Scheduler
    SCHEDULER_CHECK_INTERVAL = int(os.environ.get('SCHEDULER_CHECK_INTERVAL', 60))
