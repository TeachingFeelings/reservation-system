import sqlite3

conn = sqlite3.connect("reservation.db")

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS admin_users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
""")

conn.commit()

print("admin_users created.")

conn.close()