"""Copy systemd service files and install them on the server."""
import paramiko
import sys

host = sys.argv[1]
password = '3339796Nyh'

web_service = """[Unit]
Description=AWDP Platform Web (Gunicorn)
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/awdp
Environment=PATH=/opt/awdp/venv/bin:/usr/bin
Environment=PYTHONPATH=/opt/awdp
ExecStart=/opt/awdp/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 60 run:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

scheduler_service = """[Unit]
Description=AWDP Platform Scheduler
After=network.target awdp-web.service
Wants=awdp-web.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/awdp
Environment=PATH=/opt/awdp/venv/bin:/usr/bin
Environment=PYTHONPATH=/opt/awdp
ExecStart=/opt/awdp/venv/bin/python /opt/awdp/services/scheduler.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password=password)

sftp = ssh.open_sftp()

# Write service files directly to remote
with sftp.open('/etc/systemd/system/awdp-web.service', 'w') as f:
    f.write(web_service)
with sftp.open('/etc/systemd/system/awdp-scheduler.service', 'w') as f:
    f.write(scheduler_service)
sftp.close()

# Kill existing gunicorn, reload, enable, start
commands = """
pkill -f gunicorn 2>/dev/null || true
sleep 1
systemctl daemon-reload
systemctl enable awdp-web.service
systemctl enable awdp-scheduler.service
systemctl start awdp-web.service
sleep 3
echo "---STATUS---"
systemctl is-active awdp-web.service
echo "---CURL---"
curl -s -o /dev/null -w "HTTP:%{http_code}\\n" http://127.0.0.1:5000/
"""
stdin, stdout, stderr = ssh.exec_command(commands)
out = stdout.read().decode('utf-8', errors='replace')
sys.stdout.write(out)
err = stderr.read().decode('utf-8', errors='replace')
if err.strip():
    sys.stdout.write('STDERR: ' + err[:500])
ssh.close()
