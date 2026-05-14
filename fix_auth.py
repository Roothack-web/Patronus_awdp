with open("/opt/awdp/app/api/auth.py", "r") as f:
    lines = f.readlines()

# Find the line with db.session.commit() that belongs to register function
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if line.strip() == "db.session.commit()" and i > 45 and i < 60:
        # This is the commit in register(). Add asteroid sync after it.
        new_lines.append("    # Sync new team to asteroid big screen\n")
        new_lines.append("    try:\n")
        new_lines.append("        from app.asteroid_client import write_team_txt, send_rank, send_status\n")
        new_lines.append('        write_team_txt("/opt/awdp/deploy/asteroid-backend/team.txt")\n')
        new_lines.append("        send_rank(Team.query.order_by(Team.id).all())\n")
        new_lines.append('        send_status(team.id, "online")\n')
        new_lines.append("    except Exception:\n")
        new_lines.append("        pass\n")

with open("/opt/awdp/app/api/auth.py", "w") as f:
    f.writelines(new_lines)
print("Done")
