import re
with open("/opt/awdp/app/asteroid_client.py", "r") as f:
    content = f.read()

old = """def _post(path, data):
    \"\"\"Fire-and-forget POST to Asteroid_backend.\"\"\"
    def _do():
        try:
            url, token = _get_config()
            headers = {}
            if token:
                headers['Authorization'] = token  # raw token, no "Bearer " prefix
            requests.post(f"{url}{path}", json=data, headers=headers, timeout=3)
        except Exception as e:
            logger.debug("Asteroid %s failed: %s", path, e)
    threading.Thread(target=_do, daemon=True).start()"""

new = """def _post(path, data):
    \"\"\"POST to Asteroid_backend synchronously.\"\"\"
    try:
        url, token = _get_config()
        headers = {}
        if token:
            headers['Authorization'] = token
        requests.post(f"{url}{path}", json=data, headers=headers, timeout=3)
    except Exception as e:
        logger.debug("Asteroid %s failed: %s", path, e)"""

if old in content:
    content = content.replace(old, new)
    with open("/opt/awdp/app/asteroid_client.py", "w") as f:
        f.write(content)
    print("OK - replaced")
else:
    print("NO MATCH")
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "def _post" in line:
            for j in range(i, min(i+15, len(lines))):
                print("L{}: {}".format(j+1, repr(lines[j])))
