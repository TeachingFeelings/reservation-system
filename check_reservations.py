import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("""
SELECT
    id,
    instrument,
    user,
    start_minute,
    end_minute,
    color,
    date
FROM reservations
""")

for row in cur.fetchall():
    print(row)

conn.close()