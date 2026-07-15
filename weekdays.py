import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("""
ALTER TABLE reservations
ADD COLUMN weekday TEXT
""")

conn.commit()
conn.close()

print("done")