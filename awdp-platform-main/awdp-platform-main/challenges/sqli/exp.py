#!/usr/bin/env python3
"""SQLi exploit — tests boolean-based blind injection via ?id= param.

Returns 0 if attack succeeds (defense failed), non-zero if blocked (defense holds).
"""
import argparse
import urllib.request
import sys


def health_check(base):
    """Check service is up and article page loads normally."""
    ok = True
    try:
        body = urllib.request.urlopen(f'{base}/?id=1', timeout=10).read().decode()
        if len(body) > 100:
            print(f'[health] article page OK ({len(body)} bytes)')
        else:
            print(f'[health] WARNING: article page too short ({len(body)} bytes)')
            ok = False
    except Exception as e:
        print(f'[health] FAILED: article page ({e})')
        ok = False
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', default='http://127.0.0.1')
    args = parser.parse_args()

    base = args.target.rstrip('/')

    health_check(base)

    # id=0 should return nothing (article not found)
    try:
        body = urllib.request.urlopen(f'{base}/?id=0', timeout=10).read().decode()
    except Exception:
        print('[exp] connection failed')
        sys.exit(1)

    if '该文章不存在' not in body:
        print('[exp] id=0 unexpected response, aborting')
        sys.exit(1)

    # id=1 AND 1=2 — if injection works, this returns nothing
    try:
        body = urllib.request.urlopen(f'{base}/?id=1%20AND%201=2', timeout=10).read().decode()
    except Exception:
        print('[exp] connection failed')
        sys.exit(1)

    if '该文章不存在' in body:
        # Can distinguish 1=1 vs 1=2 → injection works → attack succeeds
        print('[exp] SQL injection works — attack succeeds')
        sys.exit(0)
    else:
        print('[exp] Injection blocked — defense holds')
        sys.exit(1)


if __name__ == '__main__':
    main()
