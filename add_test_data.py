import sqlite3

conn = sqlite3.connect("reservation.db")

cur = conn.cursor()

cur.execute("""
INSERT INTO reservations
(instrument,user,start_hour,end_hour)
VALUES
('Flash','Li',11,14)
""")

conn.commit()
conn.close()

print("Done")