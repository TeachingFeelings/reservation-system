# add_color_column.py

import sqlite3

conn = sqlite3.connect("reservation.db")
cur = conn.cursor()

cur.execute("""
ALTER TABLE reservations
ADD COLUMN color TEXT
""")

conn.commit()
conn.close()

print("Done")