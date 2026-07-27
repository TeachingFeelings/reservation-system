import sqlite3

# 旧数据库
old_db = sqlite3.connect("reservation.db")
old_cur = old_db.cursor()

# 新数据库
new_db = sqlite3.connect("reservation_v2.db")
new_cur = new_db.cursor()

print("Database opened successfully.")

# Rooms
new_cur.execute("""
CREATE TABLE rooms(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

# Instruments
new_cur.execute("""
CREATE TABLE instruments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY(room_id) REFERENCES rooms(id)
)
""")

# Users
new_cur.execute("""
CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#4A89DC'
)
""")

# Reservations
new_cur.execute("""
CREATE TABLE reservations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    instrument_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    start_minute INTEGER,
    end_minute INTEGER,

    date TEXT,

    password TEXT,
    comment TEXT,

    FOREIGN KEY(instrument_id)
        REFERENCES instruments(id),

    FOREIGN KEY(user_id)
        REFERENCES users(id)
)
""")

new_db.commit()

print("Tables created.")

# ===============================
# Migrate Rooms
# ===============================

old_cur.execute("""
SELECT DISTINCT room
FROM room_instruments
ORDER BY room
""")

rooms = old_cur.fetchall()

for room in rooms:

    new_cur.execute("""
        INSERT INTO rooms(name)
        VALUES(?)
    """, (room[0],))

new_db.commit()

print("Rooms migrated.")

print("\nRooms in new database:")

new_cur.execute("""
SELECT *
FROM rooms
""")

for row in new_cur.fetchall():
    print(row)

# ===============================
# Migrate Instruments
# ===============================

old_cur.execute("""
SELECT room, instrument
FROM room_instruments
ORDER BY room, instrument
""")

instrument_rows = old_cur.fetchall()

print(instrument_rows)

new_cur.execute("""
SELECT id, name
FROM rooms
""")

room_map = {}

for room_id, room_name in new_cur.fetchall():
    room_map[room_name] = room_id

print(room_map)

for room_name, instrument_name in instrument_rows:

    new_cur.execute("""
        INSERT INTO instruments(room_id, name)
        VALUES(?, ?)
    """,
    (
        room_map[room_name],
        instrument_name
    ))

new_db.commit()

print("Instruments migrated.")

print("\nInstruments:")

new_cur.execute("""
SELECT
    instruments.id,
    rooms.name,
    instruments.name
FROM instruments
JOIN rooms
ON instruments.room_id = rooms.id
ORDER BY rooms.name, instruments.name
""")

for row in new_cur.fetchall():
    print(row)


# ===============================
# Migrate Users
# ===============================

old_cur.execute("""
SELECT DISTINCT user, color
FROM reservations
ORDER BY user
""")

users = old_cur.fetchall()

for user_name, color in users:

    new_cur.execute("""
        INSERT INTO users(name, color)
        VALUES(?, ?)
    """,
    (
        user_name,
        color
    ))

new_db.commit()

print("Users migrated.")

print("\nUsers:")

new_cur.execute("""
SELECT *
FROM users
""")

for row in new_cur.fetchall():
    print(row)



# ===============================
# Instrument ID Map
# ===============================

new_cur.execute("""
SELECT id, name
FROM instruments
""")

instrument_map = {}

for instrument_id, name in new_cur.fetchall():
    instrument_map[name] = instrument_id


# ===============================
# User ID Map
# ===============================

new_cur.execute("""
SELECT id, name
FROM users
""")

user_map = {}

for user_id, name in new_cur.fetchall():
    user_map[name] = user_id


# ===============================
# Read Old Reservations
# ===============================

old_cur.execute("""
SELECT
    id,
    instrument,
    user,
    start_minute,
    end_minute,
    date,
    password,
    comment
FROM reservations
""")

old_reservations = old_cur.fetchall()

# ===============================
# Insert Reservations
# ===============================

for row in old_reservations:

    (
        old_id,
        instrument_name,
        user_name,
        start,
        end,
        date,
        password,
        comment
    ) = row

    new_cur.execute("""
        INSERT INTO reservations
        (
            instrument_id,
            user_id,
            start_minute,
            end_minute,
            date,
            password,
            comment
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (
        instrument_map[instrument_name],
        user_map[user_name],
        start,
        end,
        date,
        password,
        comment
    ))

new_db.commit()

print("Reservations migrated.")


print("\nReservations:")

new_cur.execute("""
SELECT
    reservations.id,
    users.name,
    instruments.name,
    reservations.start_minute,
    reservations.end_minute,
    reservations.date
FROM reservations
JOIN users
ON reservations.user_id = users.id
JOIN instruments
ON reservations.instrument_id = instruments.id
ORDER BY reservations.date
""")

for row in new_cur.fetchall():
    print(row)