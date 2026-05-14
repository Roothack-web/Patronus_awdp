from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import os
import hashlib
import subprocess
import sys
import tarfile
from werkzeug.utils import secure_filename

from app.models import Challenge, Defense
from app import db
from app.api import api_bp, team_required_api
from app.main import contest_not_ended
from config import basedir
import logging

logger = logging.getLogger(__name__)


@api_bp.route('/defenses/<int:challenge_id>/upload', methods=['GET', 'POST'])
@login_required
@team_required_api
def defend_upload(challenge_id):
    c = Challenge.query.get_or_404(challenge_id)
    team = current_user

    if request.method == 'GET':
        attempt_count = Defense.query.filter_by(
            team_id=team.id, challenge_id=c.id).count()
        already_fixed = bool(Defense.query.filter_by(
            team_id=team.id, challenge_id=c.id, status='success').first())
        return jsonify({'ok': True, 'data': {
            'challenge_id': c.id,
            'challenge_title': c.title,
            'is_fixed': already_fixed,
            'attempt_count': attempt_count,
            'max_attempts': 10,
        }})

    # POST — file upload
    if contest_not_ended(c):
        return jsonify({'ok': False, 'error': '比赛已结束，无法上传防护包'}), 403

    already_fixed = Defense.query.filter_by(
        team_id=team.id, challenge_id=c.id, status='success').first()
    if already_fixed:
        return jsonify({'ok': False, 'error': '你已成功修复本题，无需再次提交'}), 400

    attempt_count = Defense.query.filter_by(
        team_id=team.id, challenge_id=c.id).count()
    max_attempts = current_app.config.get('DEFENSE_MAX_ATTEMPTS', 10)
    if attempt_count >= max_attempts:
        return jsonify({'ok': False, 'error': f'本题防御提交次数已达上限 ({max_attempts} 次)'}), 400

    if 'package' not in request.files:
        return jsonify({'ok': False, 'error': '请上传防护包文件'}), 400

    f = request.files['package']
    if not f.filename:
        return jsonify({'ok': False, 'error': '文件名为空'}), 400

    fname = secure_filename(f.filename)
    upload_dir = os.path.join(basedir, 'instance', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(
        upload_dir, f"{team.id}_{c.id}_{int(datetime.utcnow().timestamp())}_{fname}")
    f.save(save_path)

    # Compute file hash
    file_hash = ''
    try:
        with open(save_path, 'rb') as fp:
            file_hash = hashlib.sha256(fp.read()).hexdigest()
    except Exception:
        logger.warning('Failed to compute file hash')

    file_size = os.path.getsize(save_path)

    # Validate tar.gz content
    try:
        if tarfile.is_tarfile(save_path):
            with tarfile.open(save_path, 'r:*') as tar:
                members = [m.name for m in tar.getmembers()]
                basenames = [os.path.basename(m) for m in members]
                if 'update.sh' not in basenames:
                    os.remove(save_path)
                    return jsonify({'ok': False, 'error': '补丁包必须包含 update.sh'}), 400
                try:
                    upd_member = None
                    for m in tar.getmembers():
                        if os.path.basename(m.name) == 'update.sh':
                            upd_member = m
                            break
                    if upd_member:
                        fobj = tar.extractfile(upd_member)
                        if fobj:
                            content = fobj.read().decode(errors='ignore')
                            if '/var/www/html' not in content:
                                os.remove(save_path)
                                return jsonify({'ok': False, 'error': 'update.sh 必须引用 /var/www/html 路径'}), 400
                except Exception:
                    logger.warning('Failed to inspect update.sh content')
        else:
            os.remove(save_path)
            return jsonify({'ok': False, 'error': '上传文件不是有效的 tar.gz 包'}), 400
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        return jsonify({'ok': False, 'error': f'包检查失败: {str(e)}'}), 400

    d = Defense(team_id=team.id, challenge_id=c.id,
                filename=fname, file_path=save_path,
                file_hash=file_hash, file_size=file_size,
                attempt_number=attempt_count + 1,
                status='uploaded')
    db.session.add(d)
    db.session.commit()

    # Launch evaluation as detached subprocess
    eval_launched = False
    try:
        python = sys.executable or 'python3'
        script = os.path.join(basedir, 'evaluate_defense.py')
        subprocess.Popen([python, script, str(d.id)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        eval_launched = True
    except Exception:
        logger.error('Failed to launch evaluation subprocess')

    return jsonify({'ok': True, 'data': {
        'defense_id': d.id,
        'attempt_number': attempt_count + 1,
        'max_attempts': max_attempts,
        'status': 'uploaded',
        'evaluation_started': eval_launched,
        'message': f'防护包已上传 (第{attempt_count+1}/{max_attempts}次)，{"评估已启动" if eval_launched else "等待管理员手动评估"}',
    }}), 201
