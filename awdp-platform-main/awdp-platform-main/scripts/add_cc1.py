"""Add CC1 Deserialization challenge to database."""
import sys
sys.path.insert(0, "/opt/awdp")
from run import app, db
from app.models import Challenge

with app.app_context():
    existing = Challenge.query.filter_by(title="CC1 Deserialization").first()
    if existing:
        print(f"CC1 already exists: ID={existing.id}")
    else:
        c = Challenge(
            title="CC1 Deserialization",
            category="web",
            description="Java deserialization vulnerability with CommonsCollections1 gadget chain. "
                        "JDK 8u65 is used to enable the classic AnnotationInvocationHandler chain.\n\n"
                        "Locate the deserialization endpoint and craft a malicious serialized object to achieve RCE.",
            docker_image="awdp-cc1:latest",
            docker_port=8080,
            internal_port=8080,
            initial_score=500,
            min_score=100,
            score_decay=50,
            exp_cmd="exp.py",
            fix_base_score=300,
            max_resets=5,
            enabled=True,
            is_fixed=False,
        )
        db.session.add(c)
        db.session.commit()
        print(f"CC1 created: ID={c.id}")

    for ch in Challenge.query.all():
        print(f"  #{ch.id} {ch.title} [{ch.category}] enabled={ch.enabled}")
