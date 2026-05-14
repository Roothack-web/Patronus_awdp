#!/usr/bin/env python3
"""AWDP Exploit Script — Defense Evaluation.

This script runs INSIDE the challenge container during defense evaluation
(via `docker exec`). It tests whether the vulnerability is still exploitable.

Exit codes:
    0 = Attack SUCCEEDS  → defense FAILS (vulnerability still open)
    1 = Attack FAILS     → defense SUCCEEDS (vulnerability patched)

The platform's evaluate_defense.py copies exp.py into /opt/exp.py of the
test container and runs `exp_cmd` from the challenge config (typically
`python3 /opt/exp.py --target http://127.0.0.1:{PORT}`).

The script should test for the VULNERABILITY, not just whether the
service is alive.
"""
import argparse
import urllib.request
import sys


def health_check(base):
    """Check service is up and basic functionality works.

    Modify this to verify your challenge's specific features:
    - Login page accessible
    - External network reachable
    - Database connection alive
    - API endpoints responding
    etc.
    """
    ok = True
    try:
        body = urllib.request.urlopen(base, timeout=10).read().decode()
        print(f'[health] main page OK ({len(body)} bytes)')
    except Exception as e:
        print(f'[health] FAILED: main page ({e})')
        ok = False

    # Example: check login page
    # try:
    #     resp = urllib.request.urlopen(f'{base}/login', timeout=10)
    #     if resp.status == 200:
    #         print('[health] login page OK')
    #     else:
    #         print(f'[health] WARNING: login returned {resp.status}')
    # except Exception as e:
    #     print(f'[health] login page check skipped ({e})')

    # Example: check external network access
    # try:
    #     resp = urllib.request.urlopen(f'{base}/proxy?url=http://example.com', timeout=10)
    #     print(f'[health] external access OK ({resp.status})')
    # except Exception as e:
    #     print(f'[health] external access check skipped ({e})')

    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', default='http://127.0.0.1')
    args = parser.parse_args()

    base = args.target.rstrip('/')

    health_check(base)

    # --- Test your vulnerability here ---
    # Example: SQL injection test
    # try:
    #     body = urllib.request.urlopen(
    #         f'{base}/?id=1%20AND%201=2', timeout=10).read().decode()
    # except Exception:
    #     print('[exp] connection failed')
    #     sys.exit(1)
    #
    # if 'error' in body:
    #     # Vulnerability still exploitable → attack succeeds
    #     sys.exit(0)
    # else:
    #     # Vulnerability patched → defense holds
    #     sys.exit(1)

    # Replace this with actual exploit logic
    sys.exit(0)


if __name__ == '__main__':
    main()
