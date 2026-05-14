"""Cleanup: delete all data except challenges (题目)"""
import sys
import os
os.environ['FLASK_APP'] = 'run.py'
sys.path.insert(0, '/opt/awdp')

from run import app, db
from app.models import (
    Team, User, Contest, ContestRound, Container,
    Submission, Defense, ScoreLog, CheckResult, FlagHistory
)

with app.app_context():
    print("清理测试数据...")

    # Delete in order to respect FK constraints
    print("  删除 FlagHistory...")
    FlagHistory.query.delete()

    print("  删除 CheckResult...")
    CheckResult.query.delete()

    print("  删除 Submission...")
    Submission.query.delete()

    print("  删除 Defense...")
    Defense.query.delete()

    print("  删除 ScoreLog...")
    ScoreLog.query.delete()

    print("  删除 Container...")
    Container.query.delete()

    print("  删除 User...")
    User.query.delete()

    print("  删除 ContestRound...")
    ContestRound.query.delete()

    print("  删除 Contest...")
    Contest.query.delete()

    # Delete all non-admin teams
    print("  删除队伍 (保留 admin)...")
    Team.query.filter(Team.name != 'admin').delete()

    db.session.commit()

    # Verify
    from app.models import Challenge
    challenges = Challenge.query.all()
    teams = Team.query.all()
    contests = Contest.query.all()
    containers = Container.query.all()
    submissions = Submission.query.all()
    defenses = Defense.query.all()

    print(f"\n清理完成！")
    print(f"  题目: {len(challenges)} 个 (保留)")
    print(f"  队伍: {len(teams)} 个 (仅 admin)")
    print(f"  比赛: {len(contests)} 个 (已清空)")
    print(f"  容器: {len(containers)} 个 (已清空)")
    print(f"  提交: {len(submissions)} 条 (已清空)")
    print(f"  防御: {len(defenses)} 条 (已清空)")
