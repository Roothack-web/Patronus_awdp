#!/usr/bin/env python
"""AWDP 完整比赛流程测试 - v2"""
import json
import time
import os
import sys

os.environ['FLASK_APP'] = 'run.py'
sys.path.insert(0, '/opt/awdp')

# Phase 0: Prepare test data via SQLAlchemy
from run import app, db
from app.models import Team, Challenge, Contest, ContestRound, Container, Submission, Defense, ScoreLog
from datetime import datetime, timedelta

with app.app_context():
    print("=" * 60)
    print("Phase 0: 准备测试数据")
    print("=" * 60)

    # Check Docker is available
    import subprocess
    try:
        r = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=3)
        docker_ok = r.returncode == 0
    except:
        docker_ok = False
    print(f"  Docker 可用: {docker_ok}")

    # Create a new contest
    now = datetime.utcnow()
    contest = Contest(
        name='Test Contest',
        description='测试比赛流程',
        status='running',
        start_at=now,
        end_at=now + timedelta(hours=2),
        freeze_before_end=30
    )
    db.session.add(contest)
    db.session.commit()
    print(f"  [OK] 比赛已创建: ID={contest.id}")

    # Create rounds
    for i in range(1, 4):
        r = ContestRound(
            contest_id=contest.id, round_number=i,
            name=f'Round {i}', status='active',
            start_at=now + timedelta(minutes=(i-1)*40),
            end_at=now + timedelta(minutes=i*40)
        )
        db.session.add(r)
    db.session.commit()
    print(f"  [OK] 3个轮次已创建")

    # List challenges
    challenges = Challenge.query.filter_by(enabled=True).all()
    print(f"  [OK] 可用题目: {[f'#{c.id} {c.title}' for c in challenges]}")

# Phase 1-15: Use subprocess curl
import subprocess as sp

BASE = 'http://127.0.0.1:5000'
CJAR = '/tmp/test_cjar.txt'
sp.run(f'rm -f {CJAR}', shell=True)

def req(method, path, data=None, form=False):
    cmd = ['curl', '-s', f'-c{CJAR}', f'-b{CJAR}', '-X', method, f'{BASE}{path}']
    if data:
        if form:
            cmd.extend(['-F', data])
        else:
            cmd.extend(['-H', 'Content-Type: application/json', '-d', json.dumps(data)])
    r = sp.run(cmd, capture_output=True, text=True, timeout=15)
    try:
        return json.loads(r.stdout)
    except:
        return {'_raw': r.stdout[:200], '_http_err': True}

def ok(r):
    return r.get('ok') is True

print("\n" + "=" * 60)
print("Phase 1: 管理员登录")
print("=" * 60)
sp.run(f'rm -f {CJAR}', shell=True)  # Start fresh
r = req('POST', '/api/auth/login', {'username': 'admin', 'password': 'admin'})
assert ok(r), f"FAIL: {r}"
print(f"  [OK] 登录成功, 队伍: {r['data']['team']['name']}")

print("\n" + "=" * 60)
print("Phase 2: 查看题目列表")
print("=" * 60)
r = req('GET', '/api/challenges')
assert ok(r), f"FAIL: {r}"
challenges_data = r['data']
if isinstance(challenges_data, list):
    print(f"  [OK] 共 {len(challenges_data)} 个题目")
    for c in challenges_data:
        print(f"    #{c['id']} {c['title']} [{c['category']}] 分:{c.get('dynamic_score', '?')}")
else:
    print(f"  [OK] 响应: {json.dumps(challenges_data, ensure_ascii=False)[:300]}")

print("\n" + "=" * 60)
print("Phase 3: 查看比赛列表")
print("=" * 60)
r = req('GET', '/api/contests')
assert ok(r), f"FAIL: {r}"
contests_data = r['data']
if isinstance(contests_data, list):
    print(f"  [OK] 共 {len(contests_data)} 个比赛")
    for c in contests_data:
        print(f"    #{c['id']} {c['name']} - {c['status']}")
else:
    print(f"  [OK] {json.dumps(contests_data, ensure_ascii=False)[:200]}")

print("\n" + "=" * 60)
print("Phase 4: 退出并注册新队伍")
print("=" * 60)
sp.run(f'rm -f {CJAR}', shell=True)  # Clear any existing session
r = req('POST', '/api/auth/register', {'name': 'TestTeamA', 'password': 'test123'})
if ok(r):
    print(f"  [OK] 队伍: {r['data']['team']['name']} ID:{r['data']['team']['id']}")
else:
    print(f"  [INFO] 可能已存在: {r.get('error', '')}")
    r = req('POST', '/api/auth/login', {'username': 'TestTeamA', 'password': 'test123'})
    if ok(r):
        print(f"  [OK] 已登录 TestTeamA")

print("\n" + "=" * 60)
print("Phase 5: 退出管理员，登录 TestTeamA")
print("=" * 60)
sp.run(f'rm -f {CJAR}', shell=True)
r = req('POST', '/api/auth/login', {'username': 'TestTeamA', 'password': 'test123'})
assert ok(r), f"登录 TestTeamA FAIL: {r}"
print(f"  [OK] 登录成功, 分数: {r['data']['team']['score']}")

print("\n" + "=" * 60)
print("Phase 6: 查看题目详情 #1")
print("=" * 60)
r = req('GET', '/api/challenges/1')
if ok(r):
    c = r['data']['challenge']
    print(f"  [OK] {c['title']} - 分值:{c.get('dynamic_score','?')} 解题:{c.get('solve_count',0)}")
else:
    print(f"  FAIL: {r}")

print("\n" + "=" * 60)
print("Phase 7: 启动容器")
print("=" * 60)
if docker_ok:
    r = req('POST', '/api/containers/1/start')
    if ok(r):
        print(f"  [OK] 容器启动请求已发送")
    else:
        print(f"  [WARN] {r.get('error', json.dumps(r, ensure_ascii=False)[:300])}")
    time.sleep(3)
else:
    print("  [SKIP] Docker 不可用")

print("\n" + "=" * 60)
print("Phase 8: 查看容器状态")
print("=" * 60)
r = req('GET', '/api/challenges/1')
if ok(r):
    container = r['data'].get('container')
    if container:
        print(f"  [OK] 状态:{container.get('status')} 地址:{container.get('public_host')}:{container.get('public_port')}")
    else:
        print(f"  [INFO] 无容器信息")
    print(f"  已正确提交: {r['data'].get('already_correct')}")
else:
    print(f"  FAIL: {r}")

print("\n" + "=" * 60)
print("Phase 9: 提交正确 Flag")
print("=" * 60)
if docker_ok:
    with app.app_context():
        team = Team.query.filter_by(name='TestTeamA').first()
        container = Container.query.filter_by(challenge_id=1, team_id=team.id).first()
        if container and container.current_flag:
            flag = container.current_flag
            print(f"  [INFO] Flag: {flag}")
            r = req('POST', f'/api/challenges/1/flag', {'flag': flag})
            if ok(r):
                print(f"  [OK] Flag 提交正确! 得分: {r.get('score_earned', '?')}")
            else:
                print(f"  [WARN] 提交结果: {r.get('error', json.dumps(r, ensure_ascii=False)[:300])}")
        else:
            print(f"  [WARN] 无容器或Flag, container={container}")
else:
    print("  [SKIP] Docker 不可用")

print("\n" + "=" * 60)
print("Phase 10: 提交错误 Flag")
print("=" * 60)
r = req('POST', '/api/challenges/1/flag', {'flag': 'flag{this_is_wrong_flag_12345}'})
if not ok(r):
    print(f"  [OK] 错误 Flag 被正确拒绝: {r.get('error', '')}")
else:
    print(f"  [WARN] 错误 Flag 被接受了? {r}")

print("\n" + "=" * 60)
print("Phase 11: 下载源码")
print("=" * 60)
result = sp.run(['curl', '-s', '-b', CJAR, '-o', '/tmp/dl_source.tar.gz', '-w', '%{http_code}',
                 f'{BASE}/api/challenges/1/source'], capture_output=True, text=True, timeout=15)
code = result.stdout.strip()
size = os.path.getsize('/tmp/dl_source.tar.gz') if os.path.exists('/tmp/dl_source.tar.gz') else 0
print(f"  [OK] HTTP:{code} 大小:{size} bytes" if code == '200' else f"  [WARN] HTTP:{code}")

print("\n" + "=" * 60)
print("Phase 12: 上传防御补丁")
print("=" * 60)
# Create a test patch
sp.run('cd /tmp && rm -rf patch && mkdir patch && echo "test content" > patch/test.txt && tar czf dpatch.tar.gz patch/', shell=True, timeout=5)
result = sp.run(
    ['curl', '-s', '-b', CJAR, '-X', 'POST', '-F', 'file=@/tmp/dpatch.tar.gz',
     f'{BASE}/api/defenses/1/upload'],
    capture_output=True, text=True, timeout=15
)
r = json.loads(result.stdout) if result.stdout else {}
print(f"  [OK] 上传结果: {r.get('ok')}" if ok(r) else f"  [WARN] {r.get('error', json.dumps(r, ensure_ascii=False)[:300])}")

print("\n" + "=" * 60)
print("Phase 13: 查看排行榜")
print("=" * 60)
sp.run(f'rm -f {CJAR}', shell=True)
r = req('POST', '/api/auth/login', {'username': 'admin', 'password': 'admin'})
r = req('GET', '/api/leaderboard')
if ok(r):
    lb = r['data']
    if isinstance(lb, list):
        print(f"  [OK] 共 {len(lb)} 支队伍")
        for e in lb[:10]:
            print(f"    #{e.get('rank','?')} {e.get('team_name','?')} 攻击:{e.get('attack_score',0)} 防御:{e.get('defense_score',0)} 总分:{e.get('score',0)}")

print("\n" + "=" * 60)
print("Phase 14: 停止并重置容器")
print("=" * 60)
if docker_ok:
    sp.run(f'rm -f {CJAR}', shell=True)
    r = req('POST', '/api/auth/login', {'username': 'TestTeamA', 'password': 'test123'})
    r = req('POST', '/api/containers/1/stop')
    print(f"  [OK] 停止: {r.get('ok')}")
    time.sleep(1)
    r = req('POST', '/api/containers/1/reset')
    print(f"  [OK] 重置: {r.get('ok')}")
else:
    print("  [SKIP]")

print("\n" + "=" * 60)
print("Phase 15: 查看提交/防御记录")
print("=" * 60)
r = req('GET', '/api/challenges/1')
if ok(r):
    subs = r['data'].get('submissions', [])
    defs = r['data'].get('defenses', [])
    print(f"  [OK] 提交记录: {len(subs)} 条")
    for s in subs[:5]:
        print(f"    正确={s.get('is_correct')} 得分={s.get('score_earned')} 队伍={s.get('team_name')}")
    print(f"  [OK] 防御记录: {len(defs)} 条")
    for d in defs[:5]:
        print(f"    状态={d.get('status')} 尝试={d.get('attempt_number')} 队伍={d.get('team_name')}")

print("\n" + "=" * 60)
print("Phase 16: 查看比赛详情")
print("=" * 60)
r = req('GET', '/api/contests/2')
if ok(r):
    print(f"  [OK] 比赛: {json.dumps(r['data'], ensure_ascii=False)[:500]}")
else:
    print(f"  [INFO] {r.get('error', '')}")

print("\n" + "=" * 60)
print("全部测试完成！")
print("=" * 60)
