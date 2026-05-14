from app import create_app, db
from app.models import User, Challenge, Defense
import os, tarfile, shutil

app = create_app()

def main():
    with app.app_context():
        user = User.query.filter_by(username='patcher').first()
        if not user:
            user = User(username='patcher', email='patcher@example.com', is_admin=False)
            user.set_password('patch')
            db.session.add(user)
            db.session.commit()

        ch = Challenge.query.filter_by(title='Patch Update Challenge').first()
        if not ch:
            # exp_cmd finds the awdp_def_* container and cats /flag inside it
            exp_cmd = "bash -lc \"docker ps --format '{{.Names}}' | grep awdp_def_ | head -n1 | xargs -r -I{} docker exec {} cat /flag\""
            ch = Challenge(title='Patch Update Challenge', description='Patch-style defense test', points=120, exp_cmd=exp_cmd)
            db.session.add(ch)
            db.session.commit()

        uploads = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads, exist_ok=True)

        pkgdir = os.path.join(uploads, f'patchpkg_{ch.id}')
        if os.path.exists(pkgdir):
            shutil.rmtree(pkgdir)
        os.makedirs(pkgdir)

        # write target_image file
        with open(os.path.join(pkgdir, 'target_image'), 'w', newline='') as f:
            f.write('alpine:3.18')

        # write update.sh that writes the flag to /flag
        update_sh = """#!/bin/sh
echo '""" + ch.flag + """' > /flag
chmod 644 /flag
"""
        with open(os.path.join(pkgdir, 'update.sh'), 'w', newline='') as f:
            f.write(update_sh)
        os.chmod(os.path.join(pkgdir, 'update.sh'), 0o755)

        tarpath = os.path.join(uploads, 'patch_sample.tar.gz')
        if os.path.exists(tarpath):
            os.remove(tarpath)
        with tarfile.open(tarpath, 'w:gz') as tar:
            tar.add(pkgdir, arcname='.')

        d = Defense(user_id=user.id, challenge_id=ch.id, filename=tarpath, status='uploaded')
        db.session.add(d)
        db.session.commit()
        print('created_patch_defense_id', d.id)

if __name__ == '__main__':
    main()
