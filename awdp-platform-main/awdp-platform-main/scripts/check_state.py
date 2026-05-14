"""Check current database state on the server."""
import sqlite3
import sys

conn = sqlite3.connect('/opt/awdp/awdp.db')
conn.row_factory = sqlite3.Row

print("=== TEAMS ===")
for r in conn.execute("SELECT id, name, is_admin, score FROM team"):
    print(dict(r))

print("\n=== CHALLENGES ===")
for r in conn.execute("SELECT id, title, category, enabled, docker_image, docker_port, internal_port FROM challenge"):
    row = dict(r)
    print(row)

print("\n=== CONTESTS ===")
for r in conn.execute("SELECT id, name, status, start_at, end_at FROM contest"):
    print(dict(r))

print("\n=== CONTEST ROUNDS ===")
for r in conn.execute("SELECT id, contest_id, round_number, name, status FROM contest_round"):
    print(dict(r))

conn.close()
