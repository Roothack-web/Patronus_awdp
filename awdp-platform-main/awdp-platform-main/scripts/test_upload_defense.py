#!/usr/bin/env python3
import requests, re, os, sys, time

BASE = os.environ.get('AWDP_BASE', 'http://127.0.0.1:5000')

def get_csrf(session, url):
    r = session.get(url)
    m = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', r.text)
    if not m:
        return None
    return m.group(1)

def login(session, username, password):
    login_url = BASE + '/auth/login'
    token = get_csrf(session, login_url)
    data = {'username': username, 'password': password, 'remember_me': 'y'}
    if token:
        data['csrf_token'] = token
    r = session.post(login_url, data=data, allow_redirects=True)
    return r

def upload_package(session, challenge_id, path):
    url = f"{BASE}/defend/{challenge_id}/upload"
    token = get_csrf(session, url)
    files = {'package': open(path, 'rb')}
    data = {}
    if token:
        data['csrf_token'] = token
    r = session.post(url, files=files, data=data, allow_redirects=True)
    return r

def main():
    if len(sys.argv) < 4:
        print('usage: test_upload_defense.py <username> <password> <tarpath> [challenge_id]')
        return 1
    username = sys.argv[1]
    password = sys.argv[2]
    tarpath = sys.argv[3]
    challenge_id = int(sys.argv[4]) if len(sys.argv) > 4 else 5

    if not os.path.exists(tarpath):
        print('file not found', tarpath)
        return 2

    s = requests.Session()
    print('GET / ->', s.get(BASE).status_code)
    print('logging in as', username)
    r = login(s, username, password)
    print('post-login status', r.status_code)
    print('uploading', tarpath, 'to challenge', challenge_id)
    r2 = upload_package(s, challenge_id, tarpath)
    print('upload response status', r2.status_code)
    # print snippet
    print('response snippet:\n', r2.text[:800])
    return 0

if __name__ == '__main__':
    sys.exit(main())
