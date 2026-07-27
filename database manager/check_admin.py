import sqlite3

conn = sqlite3.connect("reservation.db")

cur = conn.cursor()

cur.execute("SELECT * FROM admin_users")

rows = cur.fetchall()

print(rows)

conn.close()