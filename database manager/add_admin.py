from werkzeug.security import generate_password_hash
import sqlite3

conn = sqlite3.connect("reservation.db")

cur = conn.cursor()

cur.execute(
    """
    INSERT INTO admin_users(username,password_hash)
    VALUES(?,?)
    """,
    (
        "admin",
        generate_password_hash("123456")
    )
)

conn.commit()
conn.close()

print("Done")