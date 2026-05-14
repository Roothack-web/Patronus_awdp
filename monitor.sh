#!/bin/bash
# Real-time monitoring for AWDP platform pentest
# Does NOT modify any application code

cd /opt/awdp || exit 1
source venv/bin/activate 2>/dev/null

INTERVAL=10

while true; do
    clear
    echo "============================================"
    echo "  AWDP 平台实时监控  $(date '+%H:%M:%S')"
    echo "============================================"

    # 1. Active containers
    echo ""
    echo "--- 活跃容器 ---"
    docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null

    # 2. Check for new teams (potential data exfiltration via long names)
    echo ""
    echo "--- 注册队伍 ---"
    python3 << 'PYEOF'
import sys
sys.path.insert(0, '/opt/awdp')
from app import create_app
from app.models import Team
app = create_app()
with app.app_context():
    teams = Team.query.order_by(Team.id).all()
    print(f'总计: {len(teams)} 支队伍')
    for t in teams:
        if len(t.name) > 30:
            print(f'  *** 可疑 *** id={t.id} 长度={len(t.name)} name={repr(t.name)}')
        elif t.id > 20:
            print(f'  新队伍 id={t.id} name={repr(t.name)}')
PYEOF

    # 3. Recent asteroid events
    echo ""
    echo "--- 大屏事件 ---"
    curl -s -X POST -H "Authorization: AqEbNfDaq3akgfsgDDQBFfeOSytLaoZy" \
      -H "Content-Type: application/json" \
      -d '{}' http://127.0.0.1:19999/api/rank 2>&1 | head -3

    # 4. Defense evaluation processes
    echo ""
    echo "--- 防御评估进程 ---"
    ps aux | grep evaluate_defense | grep -v grep | head -5

    # 5. Container events in last 5 minutes
    echo ""
    echo "--- 最近容器事件 ---"
    docker events --since 5m 2>/dev/null | tail -5 &

    sleep $INTERVAL
done
