# init_db_v2.py

import sqlite3

conn = sqlite3.connect("reservation.db")

cur = conn.cursor()

cur.execute("""
DROP TABLE IF EXISTS reservations
""")

cur.execute("""
CREATE TABLE reservations(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    instrument TEXT,

    user TEXT,

    start_minute INTEGER,

    end_minute INTEGER

)
""")

conn.commit()
conn.close()

print("Database initialized")