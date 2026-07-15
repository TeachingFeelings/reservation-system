from flask import Flask, render_template, request, jsonify
from database import get_connection
import calendar

app = Flask(__name__)




from datetime import date,datetime

@app.route("/")
def index():

    selected_date = request.args.get(
        "date",
        date.today().isoformat()
    )

    selected_room = request.args.get("room", "room1")

    dt = datetime.strptime(
    selected_date,
    "%Y-%m-%d"
    )

    year = dt.year
    month = dt.month
    #---------------------
    # 先生成日历
    #---------------------
    cal = calendar.monthcalendar(
    year,
    month
    )

    #---------------------
    # 生成日本节假日
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

    cur.execute("""
       SELECT instrument
       FROM room_instruments
       WHERE room = %s
    """, (selected_room,))

    instrument_list = [r[0] for r in cur.fetchall()]

     # 热力图统计
    cur.execute("""
        SELECT date, COUNT(*)
        FROM reservations
        GROUP BY date
    """)

    counts = {}

    for d, c in cur.fetchall():
        print("DEBUG:", type(d), d, c)
        counts[d] = c

    cur.execute("""
        SELECT id,
        instrument,
        user,
        start_minute,
        end_minute,
        color,
        password,
        comment
        FROM reservations
        WHERE date = %s
        AND room = %s
    """, (selected_date,selected_room))

    rows = cur.fetchall()

    print("selected_date =", selected_date)
    print("rows =", rows)


    conn.close()

    reservations = []

    for row in rows:

        reservations.append({

            "id": row[0],
            "instrument": row[1],
            "user": row[2],
            "start": row[3],
            "end": row[4],
            "color": row[5],
            "password": row[6],
            "comment": row[7]

        })

    return render_template(
        "index.html",
        reservations=reservations,
        instrument_list=instrument_list,
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
    cur.execute("""
        SELECT *
        FROM reservations
        WHERE instrument = %s
        AND date = %s
        AND start_minute < %s
        AND end_minute > %s
    """,
    (
        data["instrument"],
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
    cur.execute("""
        INSERT INTO reservations
        (instrument,user,start_minute,end_minute,color,date,room,password,comment)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,
    (
        data["instrument"],
        data["user"],
        start_minute,
        end_minute,
        data["color"],
        data["date"],
        data["room"],
        data["password"],
        data.get("comment","")
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok"
    })

@app.route("/update_reservation", methods=["POST"])
def update_reservation():

    data = request.get_json()

    room = data.get("room", "room1")

    if data["start"] >= data["end"]:
        return jsonify({
        "status": "invalid_time"
    })

    conn = get_connection()
    cur = conn.cursor()

    # 冲突检测（排除自己）

    cur.execute("""
        SELECT *
        FROM reservations
        WHERE instrument = %s
        AND date = %s
        AND id != %s
        AND room = %s
        AND start_minute < %s
        AND end_minute > %s
    """,
    (
        data["instrument"],
        data["date"],
        data["id"],
        data["room"],
        data["end"],
        data["start"]
    ))

    conflict = cur.fetchone()

    if conflict:

        conn.close()

        return jsonify({
            "status": "conflict"
        })

    cur.execute("""
        UPDATE reservations
        SET
            user = %s,
            start_minute = %s,
            end_minute = %s,
            color = %s,
            comment = %s
        WHERE id = %s
    """,
    (
        data["user"],
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
    cur.execute("""
        SELECT password
        FROM reservations
        WHERE id = %s
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
    cur.execute("""
        DELETE FROM reservations
        WHERE id = %s
    """,
    (data["id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "status": "ok"
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )