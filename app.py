from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)
from werkzeug.security import check_password_hash
from database import get_connection, PLACEHOLDER
import calendar

app = Flask(__name__)

app.secret_key = "change-this-to-a-random-secret-key"


from datetime import date,datetime

@app.route("/")
def index():

    selected_date = request.args.get(
        "date",
        date.today().isoformat()
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT name
    FROM rooms
    ORDER BY id
    LIMIT 1
    """)

    default_room = cur.fetchone()[0]

    selected_room = request.args.get(
        "room",
        default_room
    )

    dt = datetime.strptime(
    selected_date,
    "%Y-%m-%d"
    )

    year = dt.year
    month = dt.month
    #---------------------
    # Generate date
    #---------------------
    cal = calendar.monthcalendar(
    year,
    month
    )

    #---------------------
    # Generate Japan holiday
    #---------------------
    import holidays
    jp_holidays = holidays.JP()
    holiday_dates = {}

    for week in cal:
     for day in week:
        if day == 0:
            continue

        d = date(year, month, day)

        if d in jp_holidays:
            holiday_dates[d.isoformat()] = jp_holidays[d]


    weekday = datetime.strptime(
    selected_date,
    "%Y-%m-%d"
    ).strftime("%a")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(f"""
       SELECT id, name
       FROM instruments
       WHERE room_id = (
           SELECT id
           FROM rooms
           WHERE name = {PLACEHOLDER}
       )
       ORDER BY name
       """,(selected_room,))

    instrument_list=[]

    for row in cur.fetchall():

        instrument_list.append({

        "id":row[0],

        "name":row[1]

        })

    cur.execute("""
       SELECT name
       FROM rooms
       ORDER BY id
       """)

    room_ids = [row[0] for row in cur.fetchall()]

    room_names = {
        "room1": "6S05_wet_Lab",
        "room2": "6S04_Cell_Culture",
        "room3": "6S03_Incubator",
        "room4": "ISSP_A463",
        "room5": "B1"
    }

    rooms = {
        room_id: room_names.get(room_id, room_id)
        for room_id in room_ids
    }

    print("ROOM DEBUG =", rooms)

    cur.execute("""
    SELECT id, name
    FROM users
    ORDER BY name
    """)

    users = []

    for row in cur.fetchall():
        users.append({
            "id": row[0],
            "name": row[1]
        })

     # 热力图统计
    cur.execute("""
        SELECT date, COUNT(*)
        FROM reservations
        GROUP BY date
    """)

    #---------------------
    # Set symbol %s or {PLACEHOLDER} for different database
    #---------------------

    counts = {}

    for d, c in cur.fetchall():

        print("DEBUG:", type(d), d, c)

        if hasattr(d, "isoformat"):
            key = d.isoformat()
        else:
            key = str(d)

        counts[key] = c

    cur.execute(f"""
    SELECT
        reservations.id,
        reservations.instrument_id,
        reservations.user_id,
        users.name,
        reservations.color,
        reservations.start_minute,
        reservations.end_minute,
        reservations.password,
        reservations.comment
    FROM reservations
    JOIN instruments
        ON reservations.instrument_id=instruments.id
    JOIN users
        ON reservations.user_id=users.id
    WHERE reservations.date={PLACEHOLDER}
    AND instruments.room_id=(
        SELECT id
        FROM rooms
        WHERE name={PLACEHOLDER}
    )
    ORDER BY reservations.start_minute
    """,(selected_date,selected_room))

    rows = cur.fetchall()

    print("selected_date =", selected_date)
    print("rows =", rows)


    conn.close()

    reservations = []

    for row in rows:

        reservations.append({

            "id": row[0],
            "instrument_id": row[1],
             "user_id":row[2],
            "user_name": row[3],
            "color":row[4],
            "start": row[5],
            "end": row[6],
            "password": row[7],
            "comment": row[8]

        })

    return render_template(
        "index.html",
        reservations=reservations,
        instrument_list=instrument_list,
        users=users,
        rooms=rooms,
        selected_room=selected_room,
        selected_date=selected_date,
        weekday=weekday,
        calendar_data=cal,
        current_year=year,
        current_month=month,
        reservation_counts=counts,
        holiday_dates=holiday_dates
    )


@app.route("/add_reservation", methods=["POST"])
def add_reservation():

    print("RAW:", request.data)
    print("TYPE:", type(request.data))
    print("JSON:", request.get_json())
    data = request.json

    start_minute = data["start"]
    end_minute = data["end"]

    if start_minute >= end_minute:
       return jsonify({
        "status": "invalid_time"
       })

    conn = get_connection()
    cur = conn.cursor()

    # 检查冲突
    cur.execute(f"""
        SELECT *
        FROM reservations
        WHERE instrument_id = {PLACEHOLDER}
        AND date = {PLACEHOLDER}
        AND start_minute < {PLACEHOLDER}
        AND end_minute > {PLACEHOLDER}
    """,
    (
        data["instrument_id"],
        data["date"],
        end_minute,
        start_minute
    ))

    conflict = cur.fetchone()

    if conflict:

        conn.close()

        return jsonify({
            "status": "conflict"
        })

    # 没有冲突，写入数据库
    cur.execute(f"""
        INSERT INTO reservations
        (
        instrument_id,
        user_id,
        start_minute,
        end_minute,
        date,
        password,
        comment,
        color
        )
        VALUES (    
        {PLACEHOLDER},
        {PLACEHOLDER},
        {PLACEHOLDER},
        {PLACEHOLDER},
        {PLACEHOLDER},
        {PLACEHOLDER},
        {PLACEHOLDER},
        {PLACEHOLDER})
    """,
    (
        data["instrument_id"],
        data["user_id"],
        start_minute,
        end_minute,
        data["date"],
        data["password"],
        data.get("comment",""),
        data["color"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok"
    })

@app.route("/update_reservation", methods=["POST"])
def update_reservation():

    data = request.get_json()

    print("UPDATE DATA =", data)

    room = data.get("room", "room1")

    if data["start"] >= data["end"]:
        return jsonify({
        "status": "invalid_time"
    })

    conn = get_connection()
    cur = conn.cursor()

    # 冲突检测（排除自己）

    cur.execute(f"""
        SELECT *
        FROM reservations
        WHERE instrument_id = {PLACEHOLDER}
        AND date = {PLACEHOLDER}
        AND id != {PLACEHOLDER}
        AND start_minute < {PLACEHOLDER}
        AND end_minute > {PLACEHOLDER}
    """,
    (
        data["instrument_id"],
        data["date"],
        data["id"],
        data["end"],
        data["start"]
    ))

    conflict = cur.fetchone()

    if conflict:

        conn.close()

        return jsonify({
            "status": "conflict"
        })

    cur.execute(f"""
        UPDATE reservations
        SET
            user_id = {PLACEHOLDER},
            start_minute = {PLACEHOLDER},
            end_minute = {PLACEHOLDER},
            color = {PLACEHOLDER},
            comment = {PLACEHOLDER}
        WHERE id = {PLACEHOLDER}
    """,
    (
        data["user_id"],
        data["start"],
        data["end"],
        data["color"],
        data.get("comment",""),
        data["id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok"
    })

@app.route("/delete_reservation", methods=["POST"])
def delete_reservation():

    data = request.get_json()

    conn = get_connection()
    cur = conn.cursor()

    # 读取该预约的密码
    cur.execute(f"""
        SELECT password
        FROM reservations
        WHERE id = {PLACEHOLDER}
    """,
    (data["id"],))

    row = cur.fetchone()

    if not row:
        conn.close()

        return jsonify({
            "status": "not_found"
        })

    saved_password = row[0]

    # 如果设置了密码
    if saved_password:

        if data.get("password", "") != saved_password:

            conn.close()

            return jsonify({
                "status": "wrong_password"
            })

    # 密码正确（或没有密码）
    cur.execute(f"""
        DELETE FROM reservations
        WHERE id = {PLACEHOLDER}
    """,
    (data["id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok"
    })

# Admin Login

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            f"""
            SELECT password_hash
            FROM admin_users
            WHERE username={PLACEHOLDER}
            """,
            (username,)
        )

        row = cur.fetchone()
        conn.close()

        if row:

            password_hash = row[0]

            if check_password_hash(password_hash, password):

                session["admin"] = username

                return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="Wrong username or password"
        )

    return render_template("admin_login.html")

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    member_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM rooms")
    room_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM instruments")
    instrument_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reservations")
    reservation_count = cur.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        member_count=member_count,
        room_count=room_count,
        instrument_count=instrument_count,
        reservation_count=reservation_count
    )


@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/")


@app.route("/admin/users")
def admin_users():

    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,name
        FROM users
        ORDER BY name
    """)

    rows = cur.fetchall()

    users = []

    for row in rows:
        users.append({
            "id": row["id"],
            "name": row["name"]
        })

    print("DEBUG USERS =", users)

    conn.close()

    return render_template(
        "admin_users.html",
        users=users
    )

@app.route(
"/admin/users/add",
methods=["POST"]
)
def add_user():

    if "admin" not in session:
        return redirect("/")

    name = request.form["name"].strip()

    conn = get_connection()
    cur = conn.cursor()

    # 检查是否已经存在
    cur.execute(
        f"""
        SELECT id
        FROM users
        WHERE name={PLACEHOLDER}
        """,
        (name,)
    )

    exists = cur.fetchone()

    if exists:
        conn.close()
        return "User already exists!"

    # 添加用户
    cur.execute(
        f"""
        INSERT INTO users(name)
        VALUES({PLACEHOLDER})
        """,
        (name,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/users")


@app.route(
"/admin/users/delete",
methods=["POST"]
)
def delete_user():

    if "admin" not in session:
        return redirect("/")

    conn=get_connection()

    cur=conn.cursor()

    cur.execute(
        f"""
        DELETE
        FROM users
        WHERE id={PLACEHOLDER}
        """,
        (request.form["id"],)
    )

    conn.commit()

    conn.close()

    return redirect("/admin/users")

@app.route("/admin/instruments")
def admin_instruments():

    if "admin" not in session:
        return redirect("/admin/login")


    conn = get_connection()
    cur = conn.cursor()


    cur.execute("""
        SELECT 
            instruments.id,
            instruments.name,
            rooms.name
        FROM instruments
        JOIN rooms
        ON instruments.room_id = rooms.id
        ORDER BY rooms.id, instruments.name
    """)

    instruments = cur.fetchall()

    room_names = {
        "room1": "6S05_wet_Lab",
        "room2": "6S04_Cell_Culture",
        "room3": "6S03_Incubator",
        "room4": "ISSP_A463",
        "room5": "B1"
    }


    rows = instruments

    instruments = []

    for row in rows:
        instruments.append({
            "id": row[0],
            "name": row[1],
            "room": room_names.get(row[2], row[2])
        })


    cur.execute("""
        SELECT id,name
        FROM rooms
        ORDER BY id
    """)

    room_rows = cur.fetchall()

    room_names = {
    "room1": "6S05_wet_Lab",
    "room2": "6S04_Cell_Culture",
    "room3": "6S03_Incubator",
    "room4": "ISSP_A463",
    "room5": "B1"
    }


    rooms = []

    for r in room_rows:

        rooms.append({
            "id": r[0],
            "name": room_names.get(
                r[1],
                r[1]
            )
        })


    conn.close()


    return render_template(
        "admin_instruments.html",
        instruments=instruments,
        rooms=rooms
    )

@app.route(
"/admin/instruments/add",
methods=["POST"]
)
def add_instrument():

    if "admin" not in session:
        return redirect("/admin/login")


    name=request.form["name"]
    room_id=request.form["room_id"]


    conn=get_connection()
    cur=conn.cursor()


    cur.execute(
        f"""
        INSERT INTO instruments
        (
        name,
        room_id
        )
        VALUES
        (
        {PLACEHOLDER},
        {PLACEHOLDER}
        )
        """,
        (
            name,
            room_id
        )
    )


    conn.commit()
    conn.close()


    return redirect("/admin/instruments")


@app.route(
"/admin/instruments/delete",
methods=["POST"]
)
def delete_instrument():


    if "admin" not in session:
        return redirect("/admin/login")


    instrument_id=request.form["id"]


    conn=get_connection()
    cur=conn.cursor()


    # 删除该仪器预约
    cur.execute(
        f"""
        DELETE FROM reservations
        WHERE instrument_id={PLACEHOLDER}
        """,
        (instrument_id,)
    )


    # 删除仪器
    cur.execute(
        f"""
        DELETE FROM instruments
        WHERE id={PLACEHOLDER}
        """,
        (instrument_id,)
    )


    conn.commit()
    conn.close()


    return redirect("/admin/instruments")


@app.route("/admin/rooms")
def admin_rooms():

    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name
        FROM rooms
        ORDER BY id
    """)

    rows = cur.fetchall()

    rooms = []

    for row in rows:

        rooms.append({
            "id": row["id"],
            "name": row["name"]
        })

    conn.close()

    return render_template(
        "admin_rooms.html",
        rooms=rooms
    )

@app.route(
"/admin/rooms/add",
methods=["POST"]
)
def add_room():

    if "admin" not in session:
        return redirect("/admin/login")

    name=request.form["name"].strip()

    conn=get_connection()
    cur=conn.cursor()

    cur.execute(
        f"""
        INSERT INTO rooms(name)
        VALUES({PLACEHOLDER})
        """,
        (name,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/rooms")

@app.route(
"/admin/rooms/delete",
methods=["POST"]
)
def delete_room():

    if "admin" not in session:
        return redirect("/admin/login")

    room_id=request.form["id"]

    conn=get_connection()
    cur=conn.cursor()

    cur.execute(
        f"""
        SELECT COUNT(*)
        FROM instruments
        WHERE room_id={PLACEHOLDER}
        """,
        (room_id,)
    )

    if cur.fetchone()[0] > 0:

        conn.close()

        return "Cannot delete a room that still contains instruments."

    cur.execute(
        f"""
        DELETE
        FROM rooms
        WHERE id={PLACEHOLDER}
        """,
        (room_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/rooms")

@app.route(
    "/admin/rooms/update",
    methods=["POST"]
)
def update_room():

    if "admin" not in session:
        return redirect("/admin/login")

    room_id = request.form["id"]
    room_name = request.form["name"].strip()

    conn = get_connection()
    cur = conn.cursor()

    # 防止名称重复
    cur.execute(
        f"""
        SELECT id
        FROM rooms
        WHERE name={PLACEHOLDER}
        AND id!={PLACEHOLDER}
        """,
        (
            room_name,
            room_id
        )
    )

    if cur.fetchone():

        conn.close()

        return "Room name already exists."

    cur.execute(
        f"""
        UPDATE rooms
        SET name={PLACEHOLDER}
        WHERE id={PLACEHOLDER}
        """,
        (
            room_name,
            room_id
        )
    )

    conn.commit()
    conn.close()

    return redirect("/admin/rooms")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )

