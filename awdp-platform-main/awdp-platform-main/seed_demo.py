"""Seed demo data for AWDP platform big-screen demo."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models import Team, Challenge, Contest, ContestRound, Container
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    # Clean existing non-admin data
    ContestRound.query.delete()
    Contest.query.delete()
    Container.query.delete()
    Team.query.filter(Team.name != 'admin').delete()
    Challenge.query.delete()
    db.session.commit()

    # Create 10 teams (admin already exists)
    team_names = [
        "Alpha", "Beta", "Gamma", "Delta",
        "Epsilon", "Zeta", "Eta", "Theta",
        "Iota", "Kappa"
    ]
    teams = []
    for i, name in enumerate(team_names):
        t = Team(name=name)
        t.set_password("password")
        db.session.add(t)
        teams.append(t)
    db.session.commit()
    print(f"Created {len(teams)} teams (ID {teams[0].id} - {teams[-1].id})")

    # Create 2 challenges
    challenges = [
        Challenge(
            title="SQL Injection",
            points=500, initial_score=500, min_score=100,
            docker_image="awdp-sqli:latest",
            docker_port=0, internal_port=80,
            exp_cmd='python3 /opt/exp.py --target http://127.0.0.1',
        ),
        Challenge(
            title="SSRF",
            points=500, initial_score=500, min_score=100,
            docker_image="awdp-ssrf:latest",
            docker_port=0, internal_port=80,
            exp_cmd='python3 /opt/exp.py --target http://127.0.0.1',
        ),
    ]
    for c in challenges:
        db.session.add(c)
    db.session.commit()
    print(f"Created {len(challenges)} challenges")

    # Create a running contest
    now = datetime.utcnow()
    contest = Contest(
        name="AWDP Demo",
        status="running",
        start_at=now - timedelta(minutes=5),
        end_at=now + timedelta(hours=2),
    )
    db.session.add(contest)
    db.session.commit()

    # Create 4 rounds (15 min each)
    for r in range(4):
        round_start = now + timedelta(minutes=r * 15)
        round_end = now + timedelta(minutes=(r + 1) * 15)
        cr = ContestRound(
            contest_id=contest.id,
            round_number=r + 1,
            name=f"Round {r+1}",
            status="running" if r == 0 else "pending",
            start_at=round_start,
            end_at=round_end,
        )
        db.session.add(cr)
    db.session.commit()
    print(f"Created contest '{contest.name}' with rounds")

    print("\n=== Demo data ready ===")
    print(f"Teams: {len(teams)} (ID {teams[0].id} - {teams[-1].id})")
    print(f"Challenges: {len(challenges)}")
    print(f"Contest: {contest.name} (status={contest.status})")
