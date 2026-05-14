from app import create_app, db
from app.models import User, Challenge, Defense
import os, tarfile, shutil

app = create_app()

def make_tar(src_dir, tarpath):
    if os.path.exists(tarpath):
        os.remove(tarpath)
    with tarfile.open(tarpath, 'w:gz') as tar:
        tar.add(src_dir, arcname='.')


def main():
    with app.app_context():
        # create users
        attacker = User.query.filter_by(username='attacker').first()
        if not attacker:
            attacker = User(username='attacker', email='attacker@example.com', is_admin=False)
            attacker.set_password('attack')
            db.session.add(attacker)

        defender = User.query.filter_by(username='defender').first()
        if not defender:
            defender = User(username='defender', email='defender@example.com', is_admin=False)
            defender.set_password('defend')
            db.session.add(defender)

        db.session.commit()

        ch = Challenge.query.filter_by(title='StackOverflow Docker Challenge').first()
        if not ch:
            # exp_cmd: find the first awdp_test container and grep logs for FLAG
            exp_cmd = "bash -lc \"docker ps --format '{{.Names}}' | grep awdp_test_ | head -n1 | xargs -r -I{} docker logs {} | grep FLAG\""
            ch = Challenge(title='StackOverflow Docker Challenge', description='A toy stack overflow style Docker challenge', flag='FLAG{stack_of_test}', points=200, exp_cmd=exp_cmd)
            db.session.add(ch)
            db.session.commit()

        uploads = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads, exist_ok=True)

        # vulnerable package: prints flag on startup (simulates vulnerable service)
        vuln_dir = os.path.join(uploads, f'vuln_pkg_{ch.id}')
        if os.path.exists(vuln_dir):
            shutil.rmtree(vuln_dir)
        os.makedirs(vuln_dir)
        docker_vuln = r"""FROM alpine:3.18
RUN apk add --no-cache socat
COPY run.sh /run.sh
RUN chmod +x /run.sh
CMD ["/run.sh"]
"""
        run_sh = r"""#!/bin/sh
# Simple loop: simulate a service that logs a flag when receiving a special input
echo 'service started'
while true; do
  read line || break
  if [ "$line" = "EXPLOIT" ]; then
    echo 'FLAG{stack_of_test}'
  else
    echo "received: $line"
  fi
done
"""
        with open(os.path.join(vuln_dir, 'Dockerfile'), 'w', newline='') as f:
            f.write(docker_vuln)
        with open(os.path.join(vuln_dir, 'run.sh'), 'w', newline='') as f:
            f.write(run_sh)

        vuln_tar = os.path.join(uploads, 'vuln_stack.tar.gz')
        make_tar(vuln_dir, vuln_tar)

        # patched package: service does not expose flag
        patch_dir = os.path.join(uploads, f'patch_pkg_{ch.id}')
        if os.path.exists(patch_dir):
            shutil.rmtree(patch_dir)
        os.makedirs(patch_dir)
        docker_patch = r"""FROM alpine:3.18
RUN apk add --no-cache socat
COPY run.sh /run.sh
RUN chmod +x /run.sh
CMD ["/run.sh"]
"""
        run_sh_patch = r"""#!/bin/sh
echo 'service started patched'
while true; do
  read line || break
  # patched: never prints flag
  echo "received: $line"
done
"""
        with open(os.path.join(patch_dir, 'Dockerfile'), 'w', newline='') as f:
            f.write(docker_patch)
        with open(os.path.join(patch_dir, 'run.sh'), 'w', newline='') as f:
            f.write(run_sh_patch)

        patch_tar = os.path.join(uploads, 'patch_stack.tar.gz')
        make_tar(patch_dir, patch_tar)

        # create a Defense record for the patched package (as if defender uploaded it)
        d = Defense(user_id=defender.id, challenge_id=ch.id, filename=patch_tar, status='uploaded')
        db.session.add(d)
        db.session.commit()
        print('created_challenge_id', ch.id)
        print('vuln_tar', vuln_tar)
        print('patch_tar', patch_tar)
        print('created_defense_id', d.id)


if __name__ == '__main__':
    main()
