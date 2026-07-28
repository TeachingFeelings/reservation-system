import sqlite3

PLACEHOLDER = "?"

def get_connection():
    conn = sqlite3.connect("reservation.db")
    conn.row_factory = sqlite3.Row
    return conn
