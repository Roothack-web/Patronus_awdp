"""
Seed script: create demo contest with challenges for testing.
Run: python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.models import Team, Challenge, Contest, SystemConfig, Container
from datetime import datetime, timedelta

app = create_app()

def seed():
    with app.app_context():
        # Ensure admin
        admin = Team.query.filter_by(name='admin').first()
        if not admin:
            admin = Team(name='admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)

        # Create demo teams
        for name in ['RedTeam', 'BlueTeam', 'GreenTeam']:
            if not Team.query.filter_by(name=name).first():
                t = Team(name=name)
                t.set_password('test123')
                db.session.add(t)

        # Create demo contest
        contest = Contest.query.filter_by(name='AWDP 演示赛').first()
        if not contest:
            now = datetime.utcnow()
            contest = Contest(
                name='AWDP 演示赛',
                description='用于测试的演示比赛',
                start_at=now - timedelta(hours=1),
                end_at=now + timedelta(hours=3),
                status='running',
                freeze_before_end=30,
            )
            db.session.add(contest)
            db.session.flush()

        # Create demo challenges
        challenges = [
            dict(title='SQL Injection', category='web',
                 docker_image='awdp-sqli:latest', docker_port=0, internal_port=80,
                 description='A news site with SQL Injection\n\nFind admin password and login to get Flag',
                 points=500, initial_score=500,
                 min_score=100, score_decay=50,
                 exp_cmd='python3 /opt/exp.py --target http://127.0.0.1',
                 fix_base_score=300, max_resets=10, contest_id=contest.id),
            dict(title='SSRF', category='web',
                 docker_image='awdp-ssrf:latest', docker_port=0, internal_port=80,
                 description='SSRF proxy + ThinkPHP 5.0.23 RCE\n\nAccess internal service via SSRF to get Flag',
                 points=500, initial_score=500,
                 min_score=100, score_decay=50,
                 exp_cmd='python3 /opt/exp.py --target http://127.0.0.1',
                 fix_base_score=300, max_resets=10, contest_id=contest.id),
        ]
        for ch_data in challenges:
            title = ch_data['title']
            if not Challenge.query.filter_by(title=title).first():
                ch = Challenge(**ch_data)
                db.session.add(ch)

        db.session.commit()
        print('Seed data created successfully!')
        print('  Admin: admin / admin')
        print('  Teams: RedTeam, BlueTeam, GreenTeam (password: test123)')
        print('  Contest: AWDP 演示赛 (running, ends in ~3h)')
        print('  Challenges: SQL Injection, SSRF')

if __name__ == '__main__':
    seed()
