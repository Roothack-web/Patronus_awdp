"""
Docker Manager for AWDP platform.
Handles real Docker container lifecycle for team challenge instances.
"""
from app.utils import generate_flag

import docker
import random
import time
import socket
import tarfile
import io
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Docker client - initialized on first use
_client = None

# Port allocation range
PORT_START = 30000
PORT_END = 40000
NETWORK_NAME = 'awdp-network'


def get_client():
    global _client
    if _client is None:
        try:
            _client = docker.from_env()
            _client.ping()
        except Exception as e:
            raise RuntimeError(f'Cannot connect to Docker: {e}')
    return _client


def ensure_network():
    """Create the AWDP network if it doesn't exist."""
    client = get_client()
    try:
        client.networks.get(NETWORK_NAME)
    except docker.errors.NotFound:
        client.networks.create(NETWORK_NAME, driver='bridge', check_duplicate=True)


def find_free_port() -> int:
    """Find a free port on the host in the configured range."""
    for port in range(PORT_START, PORT_END + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            sock.close()
            continue
    raise RuntimeError('No free ports available')





def pull_image(image_name: str) -> bool:
    """Pull a Docker image. Returns True on success."""
    try:
        client = get_client()
        client.images.pull(image_name)
        return True
    except Exception as e:
        logger.error('Failed to pull image %s: %s', image_name, e)
        return False


def _inject_exp_script(challenge, container):
    """Inject exp.py from challenges/{dir}/ into container's /opt/ directory."""
    image_name = challenge.docker_image or ''
    dir_name = image_name.split(':')[0]  # strip tag
    if dir_name.startswith('awdp-'):
        dir_name = dir_name[5:]  # remove awdp- prefix
    dir_name = dir_name.replace('-', '_')  # docker_image uses hyphens, dir uses underscores
    from config import basedir
    exp_path = os.path.join(basedir, 'challenges', dir_name, 'exp.py')
    if not os.path.isfile(exp_path):
        return  # no exp.py, skip silently
    try:
        with open(exp_path, 'rb') as f:
            content = f.read()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w') as tar:
            info = tarfile.TarInfo(name='exp.py')
            info.size = len(content)
            info.mode = 0o755
            tar.addfile(info, io.BytesIO(content))
        buf.seek(0)
        container.put_archive('/opt', buf.read())
    except Exception as e:
        logger.warning('Failed to inject exp.py: %s', e)


def create_challenge_container(challenge, team_id: int, host: str = '127.0.0.1') -> dict:
    """
    Create a Docker container for a team's challenge instance.

    Args:
        challenge: Challenge model instance (has docker_image, docker_port, internal_port, etc.)
        team_id: Team ID

    Returns:
        dict with keys: container_id, container_name, host, port, flag
    """
    client = get_client()
    ensure_network()

    image_name = challenge.docker_image or 'alpine:latest'
    container_name = f"awdp-c{challenge.id}-t{team_id}-{random.randint(1000, 9999)}"
    flag = generate_flag()

    # Ensure image exists
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        if not pull_image(image_name):
            raise RuntimeError(f'Image {image_name} not found and pull failed')

    # Map ports: Docker auto-assigns a random host port (no race condition)
    internal_port = challenge.docker_port or challenge.internal_port or 80
    port_bindings = {f'{internal_port}/tcp': None} if internal_port else {}
    environment = {
        'FLAG': flag,
        'TEAM_ID': str(team_id),
        'CHALLENGE_ID': str(challenge.id),
    }

    try:
        container = client.containers.create(
            image=image_name,
            name=container_name,
            ports=port_bindings,
            environment=environment,
            network=NETWORK_NAME,
            detach=True,
            tty=True,
            stdin_open=True,
            mem_limit='512m',
            cpu_period=100000,
            cpu_quota=100000,  # 1 CPU
        )
        container.start()

        # Wait a moment for startup
        time.sleep(2)

        # Inject exp.py into /opt/ if it exists locally
        _inject_exp_script(challenge, container)

        # Refresh container info and get actual mapped port
        container.reload()
        port_key = f'{internal_port}/tcp'
        host_port = int(container.attrs['NetworkSettings']['Ports'][port_key][0]['HostPort'])

        return {
            'container_id': container.id,
            'container_name': container.name,
            'host': host,
            'port': host_port,
            'flag': flag,
            'status': container.status,
        }
    except docker.errors.APIError as e:
        raise RuntimeError(f'Docker API error: {e}')


def start_container(container_id: str) -> str:
    """Start a stopped container."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        container.start()
        time.sleep(1)
        container.reload()
        return container.status
    except docker.errors.NotFound:
        raise RuntimeError(f'Container {container_id} not found')
    except Exception as e:
        raise RuntimeError(f'Failed to start container: {e}')


def stop_container(container_id: str) -> str:
    """Stop a running container."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=10)
        container.reload()
        return container.status
    except docker.errors.NotFound:
        raise RuntimeError(f'Container {container_id} not found')
    except Exception as e:
        raise RuntimeError(f'Failed to stop container: {e}')


def remove_container(container_id: str):
    """Force remove a container."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except docker.errors.NotFound:
        logger.debug('Container %s already gone, skipping remove', container_id)
    except Exception as e:
        raise RuntimeError(f'Failed to remove container: {e}')


def restart_container(container_id: str) -> str:
    """Restart a container."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        container.restart(timeout=10)
        time.sleep(2)
        container.reload()
        return container.status
    except docker.errors.NotFound:
        raise RuntimeError(f'Container {container_id} not found')
    except Exception as e:
        raise RuntimeError(f'Failed to restart container: {e}')


def refresh_flag_in_container(container_id: str, new_flag: str) -> bool:
    """
    Update the FLAG environment variable in a running container.
    Since Docker doesn't support updating env vars on running containers,
    we inject the flag via a file and exec.
    """
    client = get_client()
    try:
        container = client.containers.get(container_id)
        if container.status != 'running':
            return False

        # Write flag to /flag file inside container
        # Also write to /home/ctf/flag and /tmp/flag for compatibility
        commands = [
            f'sh -c "echo {new_flag} > /flag"',
            f'sh -c "mkdir -p /home/ctf && echo {new_flag} > /home/ctf/flag"',
            f'sh -c "echo {new_flag} > /tmp/flag"',
        ]
        for cmd in commands:
            try:
                container.exec_run(cmd, user='root')
            except Exception:
                logger.debug('Failed to write flag to one of the paths')
        return True
    except Exception:
        return False


def check_container_health(container_id: str) -> dict:
    """
    Check if a container is healthy.
    Returns dict with status, response_time_ms, error.
    """
    client = get_client()
    try:
        container = client.containers.get(container_id)
        if container.status != 'running':
            return {'status': 'down', 'response_time_ms': 0, 'error': f'Container status: {container.status}'}

        # Check if container is responsive via exec
        start = datetime.utcnow()
        exit_code, output = container.exec_run('sh -c "echo ok"', user='root')
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)

        if exit_code == 0 and b'ok' in output:
            return {'status': 'up', 'response_time_ms': elapsed, 'error': ''}
        else:
            return {'status': 'down', 'response_time_ms': elapsed, 'error': f'exec failed: {output[:200]}'}
    except docker.errors.NotFound:
        return {'status': 'down', 'response_time_ms': 0, 'error': 'Container not found'}
    except Exception as e:
        return {'status': 'error', 'response_time_ms': 0, 'error': str(e)}


def get_container_logs(container_id: str, tail: int = 100) -> str:
    """Get container logs."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        logs = container.logs(tail=tail, timestamps=True)
        return logs.decode('utf-8', errors='replace')
    except Exception as e:
        return f'Error getting logs: {e}'


def get_container_status(container_id: str) -> Optional[str]:
    """Get container status string."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        return container.status
    except docker.errors.NotFound:
        return None
    except Exception:
        return None


def get_host_port(container_id: str, internal_port: int = 80) -> Optional[int]:
    """Get the host port mapped to a container's internal port."""
    client = get_client()
    try:
        container = client.containers.get(container_id)
        port_info = container.attrs['NetworkSettings']['Ports']
        key = f'{internal_port}/tcp'
        if key in port_info and port_info[key]:
            return int(port_info[key][0]['HostPort'])
        # Try to find any mapped port
        for p_key, p_val in port_info.items():
            if p_val:
                return int(p_val[0]['HostPort'])
        return None
    except Exception:
        return None


def cleanup_team_containers(team_name: str):
    """Remove all containers belonging to a team."""
    client = get_client()
    containers = client.containers.list(all=True, filters={'name': team_name})
    for c in containers:
        try:
            c.remove(force=True)
        except Exception:
            logger.warning('Failed to remove container %s during cleanup', c.name)


def list_awdp_containers():
    """List all AWDP-related containers on the host."""
    client = get_client()
    containers = client.containers.list(all=True)
    return [c for c in containers if c.name.startswith('awdp-')]
