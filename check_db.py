import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("""
SELECT *
FROM reservations
""")

for row in cur.fetchall():
    print(row)

conn.close()