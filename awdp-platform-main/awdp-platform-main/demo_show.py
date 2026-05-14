"""
AWDP Big Screen Demo Script — Send attack/fix events to asteroid-backend
"""
import requests
import time
import random
import sys

BASE_URL = "http://127.0.0.1:19999"
TOKEN = "AqEbNfDaq3akgfsgDDQBFfeOSytLaoZy"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

TEAMS = list(range(2, 12))  # team IDs 2-11
CHALLENGES = [1, 2]  # SQL Injection=1, SSRF=2

API_ATTACK = f"{BASE_URL}/attack"
API_FIX = f"{BASE_URL}/fix"
API_RANK = f"{BASE_URL}/rank"
API_STATUS = f"{BASE_URL}/status"
API_ROUND = f"{BASE_URL}/round"

def attack(team_id, challenge_id):
    try:
        r = requests.post(API_ATTACK, json={"From": team_id, "To": challenge_id}, headers=HEADERS, timeout=2)
        return r.ok
    except:
        return False

def fix(team_id, challenge_id):
    try:
        r = requests.post(API_FIX, json={"Team": team_id, "Challenge": challenge_id}, headers=HEADERS, timeout=2)
        return r.ok
    except:
        return False

def send_rank(scores=None):
    if scores is None:
        scores = {}
    team_list = []
    names = {
        2:"Alpha",3:"Beta",4:"Gamma",5:"Delta",
        6:"Epsilon",7:"Zeta",8:"Eta",9:"Theta",
        10:"Iota",11:"Kappa"
    }
    for i, tid in enumerate(TEAMS):
        s = scores.get(tid, 5000 - i * 300)
        team_list.append({
            "Id": tid, "Name": names[tid],
            "Rank": i+1, "Score": s,
            "AttackScore": int(s*0.6), "DefenseScore": int(s*0.4),
            "Image": ""
        })
    try:
        requests.post(API_RANK, json={"Team": team_list}, headers=HEADERS, timeout=2)
    except:
        pass

def wave_all_attack(challenge_id, label=""):
    """All teams simultaneously attack one challenge."""
    print(f"  [attack] All teams -> {label or f'Challenge {challenge_id}'}")
    for tid in TEAMS:
        attack(tid, challenge_id)
    time.sleep(0.3)

def wave_barrage(count=3):
    """Random attacks with all teams against both challenges."""
    for _ in range(count):
        for tid in TEAMS:
            cid = random.choice(CHALLENGES)
            attack(tid, cid)
        time.sleep(0.15)

def wave_fix(count_teams=5):
    """Fix events — challenge fires back, shields pop up."""
    print(f"  [fix] {count_teams} teams fixing challenges")
    for tid in TEAMS[:count_teams]:
        cid = random.choice(CHALLENGES)
        fix(tid, cid)
        time.sleep(0.3)

def dramatic_pause(seconds):
    print(f"  ...waiting {seconds}s ...")
    time.sleep(seconds)

print("=" * 50)
print("AWDP Big Screen Demo Script")
print("=" * 50)

# Phase 0: Init rank
print("\n[Phase 0] Initializing rank...")
send_rank()
time.sleep(0.5)

# Phase 1: Barrage on SQL Injection
print("\n[Phase 1] All teams barrage SQL Injection!")
wave_all_attack(1, "SQL Injection")
time.sleep(0.5)
wave_all_attack(1, "SQL Injection")
dramatic_pause(2)

# Phase 2: Switch to SSRF
print("\n[Phase 2] All teams switch to SSRF!")
wave_all_attack(2, "SSRF")
time.sleep(0.3)
wave_all_attack(2, "SSRF")
time.sleep(0.3)
wave_all_attack(2, "SSRF")
dramatic_pause(2)

# Phase 3: Coordinated barrage (alternating)
print("\n[Phase 3] Alternating barrage!")
for i in range(4):
    cid = 1 if i % 2 == 0 else 2
    label = "SQL Injection" if i % 2 == 0 else "SSRF"
    print(f"  Wave {i+1}: {label}")
    for tid in TEAMS:
        attack(tid, cid)
    time.sleep(0.4)
dramatic_pause(1.5)

# Phase 4: Massive all-out barrage
print("\n[Phase 4] All-out barrage!")
wave_barrage(6)
dramatic_pause(1.5)

# Phase 5: Fix defense (counter-attack visuals + shields)
print("\n[Phase 5] Counter-attack — shields up!")
wave_fix(10)
dramatic_pause(3)

# Phase 6: Final barrage
print("\n[Phase 6] Final wave — all fire!")
for i in range(5):
    for tid in TEAMS:
        attack(tid, random.choice(CHALLENGES))
    time.sleep(0.2)
dramatic_pause(2)

# Phase 7: More attacks (keep visual going)
print("\n[Phase 7] Sustained attack...")
for i in range(8):
    tid = random.choice(TEAMS)
    cid = random.choice(CHALLENGES)
    attack(tid, cid)
    time.sleep(0.1)

print("\n" + "=" * 50)
print("Demo complete! You can continue sending attacks manually:")
print('  curl -H "Authorization: AqEbNfDaq3akgfsgDDQBFfeOSytLaoZy"')
print('    -X POST -H "Content-Type: application/json"')
print('    -d \'{"From": 2, "To": 1}\'')
print(f'    {API_ATTACK}')
print("=" * 50)
