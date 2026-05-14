"""Deployment helper: SSH into the server and run commands."""
import paramiko
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

host = sys.argv[1]
cmd = sys.argv[2]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username='root', password='3339796Nyh')

stdin, stdout, stderr = ssh.exec_command(cmd)
exit_status = stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print(out)
if err:
    print('[STDERR]', err, file=sys.stderr)
sys.exit(exit_status)
