import sqlite3
conn = sqlite3.connect("/opt/awdp/awdp.db")
conn.execute("DELETE FROM container")
conn.commit()
conn.close()
print("All container records deleted")
