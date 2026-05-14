"""Add PHP intval bypass challenge to database."""
import sys
sys.path.insert(0, "/opt/awdp")
from run import app, db
from app.models import Challenge

with app.app_context():
    existing = Challenge.query.filter_by(title="PHP intval Bypass").first()
    if existing:
        print(f"Already exists: ID={existing.id}")
    else:
        c = Challenge(
            title="PHP intval Bypass",
            category="web",
            description="PHP type juggling and intval bypass challenge.\n\n"
                        "Bypass all filters to get the flag. Hint: intval() stops at newlines.",
            docker_image="awdp-php-num:latest",
            docker_port=80,
            internal_port=80,
            initial_score=300,
            min_score=50,
            score_decay=30,
            exp_cmd="exp.py",
            fix_base_score=200,
            max_resets=5,
            enabled=True,
            is_fixed=False,
        )
        db.session.add(c)
        db.session.commit()
        print(f"Created: ID={c.id}")

    for ch in Challenge.query.all():
        print(f"  #{ch.id} {ch.title}")
