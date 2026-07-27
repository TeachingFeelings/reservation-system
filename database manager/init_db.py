import sqlite3

conn = sqlite3.connect("reservation.db")

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS reservations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument TEXT,
    user TEXT,
    start_hour INTEGER,
    end_hour INTEGER
)
""")

conn.commit()
conn.close()

print("Database created")