import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("DELETE FROM reservations")

conn.commit()
conn.close()

print("Database cleared")