"""
Background services for AWDP platform:
- Docker container health checks with auto-restart for down containers
- Contest auto-start/end and round transitions

Run: python -m services.scheduler
"""
import time
import logging
from datetime import datetime

from app import create_app, db
from app.models import Container, Challenge, CheckResult, Team, SystemConfig, Contest, ContestRound
from app.docker_manager import restart_container, check_container_health
from app.asteroid_client import send_status, send_round
from config import Config

logger = logging.getLogger(__name__)
app = create_app()

CHECK_INTERVAL = Config.SCHEDULER_CHECK_INTERVAL


def manage_contests():
    """Auto-start/end contests and auto-transition rounds."""
    with app.app_context():
        now = datetime.utcnow()

        # Auto-start pending contests
        pending = Contest.query.filter_by(status='pending').all()
        for c in pending:
            if c.start_at and c.start_at <= now:
                c.status = 'running'
                logger.info('Contest "%s" auto-started', c.name)

        # Auto-end running contests
        running = Contest.query.filter_by(status='running').all()
        for c in running:
            if c.end_at and c.end_at <= now:
                c.status = 'finished'
                logger.info('Contest "%s" auto-ended', c.name)

        # Auto-transition rounds for running contests
        for c in running:
            rounds = ContestRound.query.filter_by(
                contest_id=c.id, status='pending'
            ).order_by(ContestRound.round_number).all()
            for r in rounds:
                if r.start_at and r.start_at <= now:
                    r.status = 'running'
                    send_round(r.round_number)
                    logger.info('Round "%s" auto-started', r.name)

            # End expired rounds
            active_rounds = ContestRound.query.filter_by(
                contest_id=c.id, status='running'
            ).all()
            for r in active_rounds:
                if r.end_at and r.end_at <= now:
                    r.status = 'finished'
                    logger.info('Round "%s" auto-ended', r.name)

        # Record scheduler heartbeat
        cfg = SystemConfig.query.filter_by(key='scheduler_last_run').first()
        if cfg:
            cfg.value = now.isoformat()
        else:
            db.session.add(SystemConfig(key='scheduler_last_run',
                                        value=now.isoformat()))
        db.session.commit()


def check_and_penalize(container):
    """Check container health using Docker API and auto-restart if down."""
    with app.app_context():
        try:
            c = Container.query.get(container.id)
            if not c or c.status != 'running':
                return

            if c.docker_container_id:
                # Real Docker health check
                health = check_container_health(c.docker_container_id)
                status = health['status']
                ms = health['response_time_ms']
                err = health['error']
            else:
                # Simulated: simple TCP port check
                import socket
                host = c.public_host or '127.0.0.1'
                port = c.public_port or 80
                start = datetime.utcnow()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                ms = int((datetime.utcnow() - start).total_seconds() * 1000)
                status = 'up' if result == 0 else 'down'
                err = '' if result == 0 else f'connect failed: {result}'

            check = CheckResult(
                container_id=c.id, check_type='health',
                status=status, response_time_ms=ms,
                error_message=err[:200] if err else ''
            )
            db.session.add(check)

            if status == 'down':
                ch = Challenge.query.get(c.challenge_id)
                team = Team.query.get(c.team_id)
                if ch and team:
                    send_status(team.id, 'offline')
                # Auto-restart the container
                try:
                    restart_container(c.docker_container_id)
                    logger.info('Auto-restarted container %s (team %s, challenge %s)',
                                c.docker_container_id, c.team_id, c.challenge_id)
                except Exception as e:
                    logger.warning('Failed to restart container %s: %s', c.docker_container_id, e)
            elif status == 'up':
                team = Team.query.get(c.team_id)
                if team:
                    send_status(team.id, 'online')
            db.session.commit()
        except Exception as e:
            try:
                check = CheckResult(
                    container_id=container.id, check_type='health',
                    status='error', error_message=str(e)[:200]
                )
                db.session.add(check)
                db.session.commit()
            except Exception:
                logger.debug('Failed to persist check result for container %s', container.id)


def check_cycle():
    """Run one cycle of health checks and contest management."""
    with app.app_context():
        # Auto contest/round management
        manage_contests()

        containers = Container.query.filter_by(status='running').all()

        for c in containers:
            check_and_penalize(c)


def run_scheduler():
    """Main scheduler loop."""
    logger.info('=== AWDP Background Services ===')
    logger.info('Health check interval: %ds', CHECK_INTERVAL)
    logger.info('===============================')

    while True:
        try:
            check_cycle()
        except Exception as e:
            logger.error('Check cycle error', exc_info=True)
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    run_scheduler()
