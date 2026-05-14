from app import create_app, db
from app.models import User, Challenge, Defense
import os, tarfile, shutil

app = create_app()

def main():
    with app.app_context():
        user = User.query.filter_by(username='tester').first()
        if not user:
            user = User(username='tester', email='tester@example.com', is_admin=False)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()

        ch = Challenge.query.filter_by(title='Sample Docker Challenge').first()
        if not ch:
            exp_cmd = "bash -lc \"docker ps --format '{{.Names}}' | grep awdp_def_ | head -n1 | xargs -r -I{} docker logs {} | grep FLAG\""
            ch = Challenge(title='Sample Docker Challenge', description='Auto test Docker defense', flag='FLAG{test_flag_123}', points=100, exp_cmd=exp_cmd)
            db.session.add(ch)
            db.session.commit()

        uploads = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads, exist_ok=True)

        pkgdir = os.path.join(uploads, f'defpkg_{ch.id}')
        if os.path.exists(pkgdir):
            shutil.rmtree(pkgdir)
        os.makedirs(pkgdir)

        dockerfile = """FROM alpine:3.18
RUN echo 'FLAG{test_flag_123}' > /flag
CMD [\"sh\",\"-c\",\"cat /flag && sleep 300\"]
"""
        with open(os.path.join(pkgdir, 'Dockerfile'), 'w', newline='') as f:
            f.write(dockerfile)

        tarpath = os.path.join(uploads, 'def_sample.tar.gz')
        if os.path.exists(tarpath):
            os.remove(tarpath)
        with tarfile.open(tarpath, 'w:gz') as tar:
            tar.add(pkgdir, arcname='.')

        d = Defense(user_id=user.id, challenge_id=ch.id, filename=tarpath, status='uploaded')
        db.session.add(d)
        db.session.commit()
        print('created_defense_id', d.id)

if __name__ == '__main__':
    main()
