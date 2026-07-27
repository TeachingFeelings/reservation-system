let PIXELS_PER_MINUTE =
    parseFloat(
        getComputedStyle(document.documentElement)
            .getPropertyValue("--hour-width")
    ) / 60;

let isDragging = false;
let startMinute = null;
let currentTimeline = null;
let previewBlock = null;

let pendingReservation = null;
let editingReservation = null;

let draggingReservation = null;
let dragStartX = 0;
let originalStart = 0;
let originalEnd = 0;
let dragNewStart = 0;
let dragNewEnd = 0;
let movedReservation = false;
let mouseDownReservation = null;

let longPressTimer = null;
let longPressTriggered = false;


// =========================
// Time
// =========================

function minuteToTime(minute) {

    const h = Math.floor(minute / 60);
    const m = minute % 60;

    return (
        String(h).padStart(2, "0") +
        ":" +
        String(m).padStart(2, "0")
    );
}

function timeToMinute(str) {

    const p = str.split(":");

    return parseInt(p[0]) * 60 + parseInt(p[1]);
}


// =========================
// Create Reservation
// =========================

document.querySelectorAll(".timeline").forEach(timeline => {

    timeline.addEventListener("pointerdown", function (event) {

        if (event.target !== timeline)
            return;

        const isTouch =
            event.pointerType === "touch";

        const beginCreate = () => {

            longPressTriggered = true;

            const rect =
                timeline.getBoundingClientRect();

            let x =
                event.clientX - rect.left;

            startMinute =
                Math.round(
                    x / PIXELS_PER_MINUTE
                );

            startMinute =
                Math.round(startMinute / 10) * 10;

            startMinute =
                Math.max(
                    0,
                    Math.min(1440, startMinute)
                );

            currentTimeline = timeline;
            isDragging = true;

            previewBlock =
                document.createElement("div");

            previewBlock.className = "preview";

            previewBlock.style.position = "absolute";
            previewBlock.style.top = "5px";
            previewBlock.style.height = "40px";
            previewBlock.style.left =
                startMinute * PIXELS_PER_MINUTE + "px";
            previewBlock.style.width = "0px";
            previewBlock.style.background =
                "rgba(74,137,220,.5)";
            previewBlock.style.borderRadius = "4px";
            previewBlock.style.pointerEvents = "none";

            timeline.appendChild(previewBlock);

        };

        if (isTouch) {

            longPressTriggered = false;

            longPressTimer =
                setTimeout(beginCreate, 800);

        }
        else {

            beginCreate();

        }

    });


    timeline.addEventListener("pointermove", function (event) {

        if (
            event.pointerType === "touch"
            &&
            !longPressTriggered
        )
            return;

        if (!isDragging)
            return;

        if (timeline !== currentTimeline)
            return;

        const rect =
            timeline.getBoundingClientRect();

        let x =
            event.clientX - rect.left;

        let currentMinute =
            Math.round(
                x / PIXELS_PER_MINUTE
            );

        currentMinute =
            Math.round(currentMinute / 10) * 10;

        let left =
            Math.min(startMinute, currentMinute);

        let right =
            Math.max(startMinute, currentMinute);

        previewBlock.style.left =
            left * PIXELS_PER_MINUTE + "px";

        previewBlock.style.width =
            (right - left) * PIXELS_PER_MINUTE + "px";

    });


    timeline.addEventListener("pointerup", function (event) {

        clearTimeout(longPressTimer);

        if (
            event.pointerType === "touch"
            &&
            !longPressTriggered
        )
            return;

        if (!isDragging)
            return;

        if (timeline !== currentTimeline)
            return;

        isDragging = false;

        const rect =
            timeline.getBoundingClientRect();

        let x =
            event.clientX - rect.left;

        let endMinute =
            Math.round(
                x / PIXELS_PER_MINUTE
            );

        endMinute =
            Math.round(endMinute / 10) * 10;

        endMinute =
            Math.max(
                0,
                Math.min(1440, endMinute)
            );

        let left =
            Math.min(startMinute, endMinute);

        let right =
            Math.max(startMinute, endMinute);

        if ((right - left) < 10) {

            previewBlock.remove();

            return;

        }

        previewBlock.remove();

        pendingReservation = {

            instrument_id:
                parseInt(
                    timeline.dataset.instrumentId
                ),

            start: left,

            end: right

        };

        document.getElementById("start-time").value =
            minuteToTime(left);

        document.getElementById("end-time").value =
            minuteToTime(right);

        document.getElementById("modal-title").innerText =
            "New Reservation";

        document.getElementById("reservation-modal").style.display =
            "flex";

    });


    timeline.addEventListener("pointerleave", function () {

        clearTimeout(longPressTimer);

        if (!isDragging)
            return;

        previewBlock.remove();

        isDragging = false;

    });

});

// =========================
// Modify Reservation
// =========================

document.querySelectorAll(".reservation").forEach(reservation => {

    reservation.addEventListener("pointerdown", function (event) {

        mouseDownReservation = reservation;

        dragStartX = event.clientX;

        originalStart =
            parseInt(reservation.dataset.start);

        originalEnd =
            parseInt(reservation.dataset.end);

        movedReservation = false;

        event.stopPropagation();

    });


    reservation.addEventListener("click", function (event) {

        if (movedReservation) {

            movedReservation = false;

            return;

        }

        event.stopPropagation();

        editingReservation = {

            id:
                parseInt(reservation.dataset.id),

            instrument_id:
                parseInt(
                    reservation.parentElement.dataset.instrumentId
                )

        };

        document.getElementById("modal-title").innerText =
            "Edit Reservation";

        document.getElementById("user-select").value =
            reservation.dataset.userId;

        document.getElementById("color-select").value =
            reservation.dataset.color;

        document.getElementById("start-time").value =
            minuteToTime(
                parseInt(reservation.dataset.start)
            );

        document.getElementById("end-time").value =
            minuteToTime(
                parseInt(reservation.dataset.end)
            );

        document.getElementById("comment").value =
            reservation.dataset.comment || "";

        document.getElementById("reservation-modal").style.display =
            "flex";

    });

});


// =========================
// Cancel
// =========================

document.getElementById("cancel-btn")
    .addEventListener("click", () => {

        if (editingReservation && movedReservation) {

            const r = document.querySelector(
                `.reservation[data-id="${editingReservation.id}"]`
            );

            r.style.left =
                originalStart * PIXELS_PER_MINUTE + "px";

            r.dataset.start = originalStart;
            r.dataset.end = originalEnd;

            r.style.width =
                (originalEnd - originalStart)
                * PIXELS_PER_MINUTE
                + "px";
        }

        movedReservation = false;
        editingReservation = null;

        document.getElementById("reservation-modal").style.display =
            "none";

    });


// =========================
// Save
// =========================

document.getElementById("save-btn")
    .addEventListener("click", () => {

        const user_id =
            parseInt(
                document.getElementById("user-select").value
            );

        const start =
            timeToMinute(
                document.getElementById("start-time").value
            );

        const end =
            timeToMinute(
                document.getElementById("end-time").value
            );

        const comment =
            document.getElementById("comment").value;

        if (start >= end) {

            alert("End time must be later than start time.");

            return;

        }

        const url =
            editingReservation
                ? "/update_reservation"
                : "/add_reservation";

        const payload = {

            instrument_id:
                editingReservation
                    ? editingReservation.instrument_id
                    : pendingReservation.instrument_id,

            user_id: user_id,

            start: start,

            end: end,

            color:
                document.getElementById("color-select").value,

            password:
                document.getElementById("password").value,

            date:
                document.body.dataset.date,

            room:
                selectedRoom,

            comment:
                comment

        };

        if (editingReservation) {

            payload.id =
                editingReservation.id;

        }

        fetch(url, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)

        })

            .then(r => r.json())

            .then(data => {

                console.log(data);


                if (data.status === "invalid_time") {

                    alert("End time must be later than start time.");

                    return;

                }

                if (data.status === "conflict") {

                    alert("This time slot is already reserved.");

                    const r = document.querySelector(
                        `.reservation[data-id="${editingReservation.id}"]`
                    );

                    r.style.left =
                        originalStart * PIXELS_PER_MINUTE + "px";

                    r.style.width =
                        (originalEnd - originalStart)
                        * PIXELS_PER_MINUTE + "px";

                    r.dataset.start = originalStart;
                    r.dataset.end = originalEnd;

                    movedReservation = false;

                    return;

                }

                location.reload();

            });

    });

// =========================
// Delete Reservation
// =========================

document.getElementById("delete-btn")
    .addEventListener("click", () => {

        if (!editingReservation)
            return;

        const password =
            prompt("Enter password (leave blank if none)");

        fetch("/delete_reservation", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                id: editingReservation.id,

                password: password

            })

        })

            .then(r => r.json())

            .then(data => {

                if (data.status === "wrong_password") {

                    alert("Incorrect password");

                    return;

                }

                location.reload();

            });

    });


// =========================
// Drag Reservation
// =========================

document.addEventListener("pointermove", function (event) {

    const deltaX =
        event.clientX - dragStartX;

    if (
        !draggingReservation &&
        Math.abs(deltaX) > 5
    ) {

        draggingReservation =
            mouseDownReservation;

        movedReservation = true;

    }

    if (!draggingReservation)
        return;

    const deltaMinute =
        Math.round(
            deltaX /
            PIXELS_PER_MINUTE /
            10
        ) * 10;

    let newStart =
        originalStart + deltaMinute;

    let newEnd =
        originalEnd + deltaMinute;

    const duration =
        originalEnd - originalStart;

    if (newStart < 0) {

        newStart = 0;

        newEnd = duration;

    }

    if (newEnd > 1440) {

        newEnd = 1440;

        newStart =
            1440 - duration;

    }

    draggingReservation.style.left =
        newStart * PIXELS_PER_MINUTE + "px";

    draggingReservation.style.width =
        (newEnd - newStart) * PIXELS_PER_MINUTE + "px";

    draggingReservation.dataset.start = newStart;
    draggingReservation.dataset.end = newEnd;

    dragNewStart = newStart;

    dragNewEnd = newEnd;

});


document.addEventListener("pointerup", function () {

    if (!draggingReservation) {

        mouseDownReservation = null;

        return;

    }

    editingReservation = {

        id:
            parseInt(
                draggingReservation.dataset.id
            ),

        instrument_id:
            parseInt(
                draggingReservation.parentElement.dataset.instrumentId
            )

    };

    document.getElementById("modal-title").innerText =
        "Modify this reservation?";

    document.getElementById("user-select").value =
        draggingReservation.dataset.userId;

    document.getElementById("color-select").value =
        draggingReservation.dataset.color;

    document.getElementById("start-time").value =
        minuteToTime(dragNewStart);

    document.getElementById("end-time").value =
        minuteToTime(dragNewEnd);

    document.getElementById("comment").value =
        draggingReservation.dataset.comment || "";

    document.getElementById("reservation-modal").style.display =
        "flex";

    draggingReservation = null;

    mouseDownReservation = null;

});


// =========================
// Date Navigation
// =========================

document.getElementById("prev-day")
    .addEventListener("click", () => {

        let d =
            new Date(document.body.dataset.date);

        d.setDate(
            d.getDate() - 1
        );

        location.href =
            "/?date=" +
            localDateString(d) +
            "&room=" +
            selectedRoom;

    });


document.getElementById("next-day")
    .addEventListener("click", () => {

        let d =
            new Date(document.body.dataset.date);

        d.setDate(
            d.getDate() + 1
        );

        location.href =
            "/?date=" +
            localDateString(d) +
            "&room=" +
            selectedRoom;

    });


document.getElementById("today-btn")
    .addEventListener("click", () => {

        location.href =
            "/?date=" +
            localDateString() +
            "&room=" +
            selectedRoom;

    });


document.getElementById("prev-month")
    ?.addEventListener("click", () => {

        let d =
            new Date(document.body.dataset.date);

        d.setMonth(
            d.getMonth() - 1
        );

        d.setDate(1);

        location.href =
            "/?date=" +
            localDateString(d) +
            "&room=" +
            selectedRoom;

    });


document.getElementById("next-month")
    ?.addEventListener("click", () => {

        let d =
            new Date(document.body.dataset.date);

        d.setMonth(
            d.getMonth() + 1
        );

        d.setDate(1);

        location.href =
            "/?date=" +
            localDateString(d) +
            "&room=" +
            selectedRoom;

    });


// =========================
// Room
// =========================

let selectedRoom =
    document.body.dataset.room || "room1";

const roomSelect =
    document.getElementById("roomSelect");

if (roomSelect) {

    roomSelect.value =
        selectedRoom;

    roomSelect.addEventListener("change", e => {

        selectedRoom =
            e.target.value;

        location.href =
            "/?date=" +
            document.body.dataset.date +
            "&room=" +
            selectedRoom;

    });

}


// =========================
// Current Time Line
// =========================

function updateNowLine() {

    const now = new Date();

    const minutes =
        now.getHours() * 60 +
        now.getMinutes();

    document
        .querySelectorAll(".now-line")
        .forEach(line => line.remove());

    if (minutes < 0 || minutes > 1440)
        return;

    const left =
        minutes * PIXELS_PER_MINUTE;

    document
        .querySelectorAll(".timeline")
        .forEach(timeline => {

            const line =
                document.createElement("div");

            line.className = "now-line";

            line.style.left =
                left + "px";

            timeline.appendChild(line);

        });

}


// =========================
// Disable Context Menu
// =========================

document.addEventListener(
    "contextmenu",
    e => e.preventDefault()
);


// =========================
// Responsive Timeline
// =========================

function resizeScheduler() {

    const instrumentWidth = 280;

    const totalHours = 24;

    const availableWidth =
        window.innerWidth -
        instrumentWidth -
        40;

    let hourWidth =
        availableWidth / totalHours;

    hourWidth =
        Math.max(
            30,
            Math.min(80, hourWidth)
        );

    document.documentElement.style.setProperty(
        "--hour-width",
        hourWidth + "px"
    );

    PIXELS_PER_MINUTE =
        hourWidth / 60;

}


function updateReservationPosition() {

    document
        .querySelectorAll(".reservation")
        .forEach(r => {

            const start =
                parseInt(r.dataset.start);

            const end =
                parseInt(r.dataset.end);

            r.style.left =
                start *
                PIXELS_PER_MINUTE +
                "px";

            r.style.width =
                (end - start) *
                PIXELS_PER_MINUTE +
                "px";

        });

}


resizeScheduler();

updateReservationPosition();


window.addEventListener(
    "resize",
    () => {

        resizeScheduler();

        updateReservationPosition();

        updateNowLine();

    }
);


// =========================
// Today Red Line
// =========================

const today =
    new Date()
        .toLocaleDateString("sv-SE");

if (document.body.dataset.date === today) {

    updateNowLine();

    setInterval(
        updateNowLine,
        60000
    );

}


// =========================
// Date Format
// =========================

function localDateString(
    date = new Date()
) {

    const y =
        date.getFullYear();

    const m =
        String(
            date.getMonth() + 1
        ).padStart(2, "0");

    const d =
        String(
            date.getDate()
        ).padStart(2, "0");

    return `${y}-${m}-${d}`;

}