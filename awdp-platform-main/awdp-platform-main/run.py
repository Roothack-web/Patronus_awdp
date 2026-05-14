import os
import sys
import shutil
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app import create_app, db
from app.models import Team, Challenge, User, Contest, ContestRound, Container, Submission, Defense, ScoreLog, CheckResult, FlagHistory, SystemConfig
from config import basedir

app = create_app()


def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Ensure default admin exists
        admin = Team.query.filter_by(name='admin').first()
        if admin is None:
            try:
                admin = Team(name='admin', is_admin=True)
                admin.set_password('admin')
                db.session.add(admin)
                db.session.commit()
                print('默认管理员已创建: admin / admin')
            except IntegrityError:
                db.session.rollback()
                existing = Team.query.filter_by(name='admin').first()
                if existing:
                    existing.is_admin = True
                    if not existing.password_hash:
                        existing.set_password('admin')
                    db.session.commit()
                    print('已有 admin 用户，已设置为管理员')
        else:
            changed = False
            if not admin.is_admin:
                admin.is_admin = True
                changed = True
            if not admin.password_hash:
                admin.set_password('admin')
                changed = True
            if changed:
                db.session.commit()
            print('数据库已初始化（管理员已存在）')

        # Create default configs if not exist
        defaults = {
            'penalty_per_down': '50',
            'check_interval': '60',
        }
        for key, value in defaults.items():
            existing = SystemConfig.query.filter_by(key=key).first()
            if not existing:
                db.session.add(SystemConfig(key=key, value=value))
        db.session.commit()

        print('数据库初始化完成')


def run_app():
    with app.app_context():
        from app.asteroid_client import write_team_txt
        try:
            teamdata_dir = os.environ.get('TEAMDATA_DIR', '')
            if teamdata_dir:
                write_team_txt(os.path.join(teamdata_dir, 'team.txt'))
        except Exception as e:
            print(f'[asteroid] team.txt 生成失败: {e}')
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)


def backup():
    """备份数据库和上传文件到 backup/ 目录。"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(basedir, 'backup', f'awdp-backup-{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)

    # 备份数据库
    db_path = os.path.join(basedir, 'instance', 'awdp.db')
    if os.path.exists(db_path):
        shutil.copy2(db_path, os.path.join(backup_dir, 'awdp.db'))
        print(f'数据库已备份: {db_path}')

    # 备份上传文件
    uploads_dir = os.path.join(basedir, 'instance', 'uploads')
    if os.path.exists(uploads_dir):
        dest = os.path.join(backup_dir, 'uploads')
        shutil.copytree(uploads_dir, dest)
        print(f'上传文件已备份: {uploads_dir}')

    print(f'备份完成: {backup_dir}')


def main(argv):
    if len(argv) >= 2 and argv[1] == 'init-db':
        init_db()
    elif len(argv) >= 2 and argv[1] == 'run':
        run_app()
    elif len(argv) >= 2 and argv[1] == 'backup':
        backup()
    else:
        print('用法:')
        print('  python run.py init-db    初始化数据库')
        print('  python run.py run        启动服务器')
        print('  python run.py backup     备份数据库和上传文件')


if __name__ == '__main__':
    main(sys.argv)
