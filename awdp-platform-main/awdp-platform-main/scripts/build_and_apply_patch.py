#!/usr/bin/env python3
"""
构建并运行题目容器，按需在容器内应用补丁并重启服务。

用法示例:
  python3 scripts/build_and_apply_patch.py \
      --build-dir uploads/pwn-ubuntu_22.04 \
      --tag pwn_local:latest \
      --name pwn_demo \
      --patch update_demo/pwn_demo/update.tar.gz

功能:
  - 在指定目录运行 `docker build -t <tag> <build-dir>`
  - 使用 `docker run -d -P` 启动容器，让 Docker 为暴露端口分配随机主机端口
  - 读取容器 9999/tcp 对应的主机端口，打印访问地址
  - 若提供 `--patch`，则把补丁复制到容器 `/tmp/patch.tar.gz`，解压并执行 `/tmp/patch/update.sh`
  - 在应用补丁后重启容器内的 xinetd 服务（使用 `/etc/init.d/xinetd restart`）
  - 输出容器日志（最近若干行）和命令执行结果

注意: 该脚本依赖宿主机上已安装并可访问的 `docker` 命令。
"""

import argparse
import subprocess
import sys
import os
import time


def run(cmd, capture=True, check=True):
    print(f"> {cmd}")
    try:
        if capture:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return out.decode(errors='ignore')
        else:
            ret = subprocess.call(cmd, shell=True)
            return ret
    except subprocess.CalledProcessError as e:
        print(e.output.decode(errors='ignore'))
        if check:
            raise
        return e.output.decode(errors='ignore')


def find_host_port(container_id, container_port):
    # docker port <container> <port>/tcp -> 0.0.0.0:32768
    out = run(f"docker port {container_id} {container_port}/tcp")
    if not out:
        return None
    # take last line
    line = out.strip().splitlines()[-1]
    if ':' in line:
        return line.split(':')[-1]
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build-dir', default='uploads/pwn-ubuntu_22.04')
    p.add_argument('--tag', default='pwn_local:latest')
    p.add_argument('--name', default=None)
    p.add_argument('--patch', default=None, help='补丁 tar.gz 路径（可选）')
    p.add_argument('--keep', action='store_true', help='保留已启动的容器（默认删除）')
    p.add_argument('--logs', type=int, default=200, help='显示的容器日志行数')
    args = p.parse_args()

    build_dir = args.build_dir
    tag = args.tag
    name = args.name

    if not os.path.isdir(build_dir):
        print('构建目录不存在:', build_dir)
        sys.exit(2)

    # 1) build
    print('构建镜像', tag, '来自', build_dir)
    run(f'docker build -t {tag} {build_dir}')

    # 2) run container with random published port(s)
    run_name = f'--name {name}' if name else ''
    cmd_run = f'docker run -d -P {run_name} {tag}'
    container_id = run(cmd_run).strip()
    print('容器启动 ID:', container_id)

    # wait a moment for docker to publish ports
    time.sleep(1)

    # 3) find published host port for container port 9999
    host_port = find_host_port(container_id, 9999)
    if host_port:
        print(f'容器 9999 -> 主机端口 {host_port}，访问地址: http://localhost:{host_port} （或替换为宿主机IP）')
    else:
        print('未找到容器 9999 的主机端口映射（容器可能未暴露该端口）')

    try:
        # 4) 如果提供补丁，复制并在容器内解压、执行 update.sh
        if args.patch:
            patch_path = args.patch
            if not os.path.exists(patch_path):
                print('补丁文件不存在:', patch_path)
                raise SystemExit(2)

            print('复制补丁到容器:/tmp/patch.tar.gz')
            run(f'docker cp {patch_path} {container_id}:/tmp/patch.tar.gz')

            print('在容器内解压补丁并执行 update.sh')
            run(f"docker exec {container_id} sh -c 'mkdir -p /tmp/patch && tar -xzf /tmp/patch.tar.gz -C /tmp/patch' ")

            # run update.sh from the patch directory so relative paths work
            run(f"docker exec {container_id} sh -c 'cd /tmp/patch && if [ -f update.sh ]; then chmod +x update.sh && ./update.sh; else echo \"/tmp/patch/update.sh not found\"; fi' ")

            print('重启容器内的 xinetd 服务')
            run(f"docker exec {container_id} sh -c '/etc/init.d/xinetd restart || service xinetd restart'", check=False)

        # 5) 显示容器日志
        print('\n==== 容器最近日志 ===')
        logs = run(f'docker logs --tail {args.logs} {container_id}', check=False)
        print(logs)

    finally:
        if not args.keep:
            print('注意：容器仍在运行。若需要我可停止并删除它（手动或再运行本脚本时使用 --keep）')


if __name__ == '__main__':
    main()
