import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("ALTER TABLE reservations ADD COLUMN room TEXT")

conn.commit()
conn.close()

print("done")