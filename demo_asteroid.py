import os, time, random
os.environ['ASTEROID_URL'] = 'http://127.0.0.1:19999'
os.environ['ASTEROID_TOKEN_FILE'] = '/opt/awdp/asteroid_token.txt'
from app.asteroid_client import _post
from app import create_app
from app.models import Team

app = create_app()

def send_rank():
    with app.app_context():
        teams = Team.query.order_by(Team.id).all()
        sorted_teams = sorted(teams, key=lambda x: -(x.score or 0))
        team_list = [
            {'Id': t.id, 'Name': t.name, 'Rank': i+1,
             'Score': random.randint(500, 8000),
             'AttackScore': random.randint(200, 5000),
             'DefenseScore': random.randint(100, 3000),
             'Image': ''}
            for i, t in enumerate(sorted_teams)
        ]
        _post('/rank', {'Team': team_list})

def attack(frm, to):
    _post('/attack', {'From': frm, 'To': to})

def fix(team_id, ch):
    _post('/fix', {'Team': team_id, 'Challenge': ch})

def round_num(r):
    _post('/round', {'Round': r})

# Round 3 - initial attacks
round_num(3)
send_rank()
attack(6, 4)
attack(7, 4)
attack(8, 4)
time.sleep(2)

# Round 3 - more attacks + fixes
attack(9, 4)
attack(10, 4)
attack(11, 4)
fix(6, 4)
fix(7, 4)
send_rank()
time.sleep(2)

# Round 4
round_num(4)
attack(8, 4)
attack(9, 4)
attack(22, 4)
fix(8, 4)
send_rank()
time.sleep(2)

# Round 4 - more action
attack(10, 4)
attack(11, 4)
attack(12, 4)
fix(9, 4)
fix(10, 4)
send_rank()
time.sleep(2)

# Round 5 - finale
round_num(5)
attack(6, 4)
attack(7, 4)
attack(8, 4)
attack(9, 4)
attack(10, 4)
attack(11, 4)
fix(22, 4)
fix(11, 4)
send_rank()

print("Long demo done - 3 rounds, 15 attacks, 7 fixes")
