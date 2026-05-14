"""
Defense evaluation script.
Evaluates uploaded defense patches against challenge containers.
Injects local challenges/<dir>/exp.py into /opt/exp.py, then runs ch.exp_cmd.
"""
import os
import sys
import subprocess
import time
import logging
from app import create_app, db
from app.models import Defense, Challenge, Team
from config import basedir
from app.scoring import award_defense_score, compute_defense_score
from datetime import datetime

logger = logging.getLogger(__name__)

app = create_app()


def run_cmd(cmd, cwd=None, timeout=60, check=False):
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
        return r.returncode, r.stdout.decode(errors='replace')
    except subprocess.TimeoutExpired:
        return -1, 'timeout'
    except Exception as e:
        return -1, str(e)


def evaluate(def_id):
    return _evaluate_impl(def_id)


def _evaluate_impl(def_id):
    with app.app_context():
        d = Defense.query.get(def_id)
        if not d:
            logger.warning('Defense not found')
            return 2
        if d.status == 'running':
            logger.warning('Already running')
            return 3
        d.status = 'running'
        db.session.commit()

        workdir = os.path.dirname(d.file_path) if d.file_path else os.path.dirname(d.filename)
        tag = f"awdp_def_{d.id}"
        build_dir = os.path.join(workdir, f"build_{d.id}")
        os.makedirs(build_dir, exist_ok=True)

        local_filename = d.file_path
        if not local_filename or not os.path.exists(local_filename):
            d.status = 'error'
            d.result = 'file not found'
            db.session.commit()
            return 4

        # Extract archive
        code, out = run_cmd(f"tar -xzf \"{local_filename}\" -C \"{build_dir}\"")
        if code != 0:
            d.status = 'error'
            d.result = f'extract failed: {out[:300]}'
            db.session.commit()
            return 4

        ch = Challenge.query.get(d.challenge_id)
        if not ch:
            d.status = 'error'
            d.result = 'challenge not found'
            db.session.commit()
            return 4

        container_started = False
        simulated = False

        # Determine if this is a Dockerfile build or patch package
        code, has_df = run_cmd(f"[ -f \"{build_dir}/Dockerfile\" ] && echo yes || echo no")
        is_dockerfile = has_df.strip() == 'yes'

        if not is_dockerfile:
            # Patch mode: extract and copy files, run update.sh
            img = ch.docker_image or 'alpine:latest'

            # Pull image if needed
            run_cmd(f"docker pull {img}", timeout=120)

            # Start container (runs its normal CMD, e.g. Apache + MySQL)
            code, out = run_cmd(
                f"docker run -d --name {tag}_ctr {img}",
                timeout=30)
            if code != 0:
                d.status = 'error'
                d.result = f'run base image failed: {out[:400]}'
                db.session.commit()
                return 6

            container_started = True

            # Wait for Apache to be ready (up to 30s)
            for _ in range(15):
                rc, _ = run_cmd(f"docker exec {tag}_ctr sh -c 'curl -s http://localhost/ >/dev/null 2>&1'", timeout=10, check=False)
                if rc == 0:
                    break
                time.sleep(2)

            # Copy patch files (tar pipe avoids Windows docker cp path issues)
            run_cmd(f"docker exec {tag}_ctr sh -c 'mkdir -p /tmp/defpatch'")
            run_cmd(f"tar -czf - -C \"{build_dir}\" . | docker exec -i {tag}_ctr tar -xzf - -C /tmp/defpatch", timeout=30)
            run_cmd(f"docker exec {tag}_ctr sh -c 'mkdir -p /home/ctf'")

            # Run update.sh
            ucode, uout = run_cmd(
                f"docker exec {tag}_ctr sh -c 'if [ -f /tmp/defpatch/update.sh ]; then chmod +x /tmp/defpatch/update.sh && cd /tmp/defpatch && ./update.sh; fi'",
                timeout=120)

            if uout:
                d.result = (d.result or '') + f'\n[update.sh]\n{uout[:1000]}'
                db.session.commit()

            if ucode != 0 or (uout and 'No such container' in uout):
                d.status = 'error'
                d.result = (d.result or '') + '\n[error] update.sh failed'
                db.session.commit()
                run_cmd(f"docker rm -f {tag}_ctr", check=False)
                return 5

            # Restart web services to apply the patch
            run_cmd(f"docker exec {tag}_ctr sh -c 'apachectl restart 2>/dev/null || apache2ctl restart 2>/dev/null || service apache2 restart 2>/dev/null || true'", timeout=15, check=False)
            time.sleep(1)
        else:
            # Docker build mode
            code, out = run_cmd(f"DOCKER_BUILDKIT=0 docker build -t {tag} \"{build_dir}\"", timeout=300)
            if code != 0:
                d.status = 'error'
                d.result = f'build failed: {out[:400]}'
                db.session.commit()
                return 6

            code, out = run_cmd(f"docker run -d --name {tag}_ctr {tag}")
            if code != 0:
                d.status = 'error'
                d.result = f'run failed: {out[:400]}'
                db.session.commit()
                return 6
            container_started = True

        time.sleep(3)

        # Run exploit to test defense (inside the container)
        # Use exp_cmd from challenge config, inject local exp.py first
        img_name = ch.docker_image.split(':')[0]  # e.g. "awdp-sqli"
        for pfx in ['awdp-', 'awdp_']:
            if img_name.startswith(pfx):
                img_name = img_name[len(pfx):]
                break
        img_name = img_name.replace('-', '_')  # docker_image uses hyphens, dir uses underscores
        exp_local = os.path.join(basedir, 'challenges', img_name, 'exp.py')
        exp_cmd = (ch.exp_cmd or '').strip()

        # If no exp_cmd configured, check for local exp.py as fallback
        if not exp_cmd and os.path.exists(exp_local):
            exp_cmd = 'python3 /opt/exp.py --target http://127.0.0.1'

        if not exp_cmd:
            if container_started:
                run_cmd(f"docker kill {tag}_ctr", check=False)
                run_cmd(f"docker rm -f {tag}_ctr", check=False)
            d.status = 'error'
            d.result = 'no exp_cmd configured and no exp.py found'
            db.session.commit()
            return 7

        # Inject local exp.py into container if it exists
        if os.path.exists(exp_local):
            run_cmd(f"docker exec {tag}_ctr sh -c 'mkdir -p /tmp/defpatch'")
            cp_code, cp_out = run_cmd(f"docker cp \"{exp_local}\" {tag}_ctr:/tmp/defpatch/exp.py", timeout=30)
            if cp_code != 0:
                d.result = (d.result or '') + f'\n[cp error] exp.py: {cp_out[:200]}'
                db.session.commit()
            run_cmd(f"docker exec {tag}_ctr cp /tmp/defpatch/exp.py /opt/exp.py", check=False)
            run_cmd(f"docker exec {tag}_ctr chmod +x /opt/exp.py", check=False)

        # Replace {PORT} placeholder with container's internal port
        port = ch.internal_port or ch.docker_port or 80
        cmd = exp_cmd.replace('{PORT}', str(port))

        code, out = run_cmd(
            f"docker exec {tag}_ctr sh -c '{cmd}'",
            timeout=120)

        if container_started:
            run_cmd(f"docker kill {tag}_ctr", check=False)
            run_cmd(f"docker rm -f {tag}_ctr", check=False)

        if code == 0:
            d.status = 'failed'
            d.result = (d.result or '') + f'\n[result] Attack succeeded (defense failed): {out[:400]}'
        else:
            d.status = 'success'
            d.result = (d.result or '') + f'\n[result] Attack failed (defense successful): {out[:400]}'

        d.image_name = tag
        db.session.commit()

        # Award defense points if successful
        if d.status == 'success':
            try:
                team = Team.query.get(d.team_id)
                if team:
                    score = compute_defense_score(ch)
                    award_defense_score(team, ch, score, defense_id=d.id)
                    d.defense_score_earned = score
                    # is_fixed is per-team now, checked via Defense.status='success'
                    db.session.commit()
                    logger.info('Awarded %s defense points to team %s', score, team.name)
            except Exception as e:
                d.result = (d.result or '') + f'\n[award error] {e}'
                db.session.commit()

        logger.info('Evaluation finished: %s', d.status)
        return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python evaluate_defense.py <defense_id>', file=sys.stderr)
        sys.exit(1)
    sys.exit(evaluate(int(sys.argv[1])))
