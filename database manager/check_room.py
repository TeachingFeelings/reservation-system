import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("""
SELECT *
FROM room_instruments
""")

for row in cur.fetchall():
    print(row)

conn.close()