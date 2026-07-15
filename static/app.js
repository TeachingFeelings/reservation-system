let PIXELS_PER_MINUTE =
    parseFloat(
        getComputedStyle(
            document.documentElement
        ).getPropertyValue(
            "--hour-width"
        )
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
let movedReservation = false;
let mouseDownReservation = null;
let longPressTimer = null;
let longPressTriggered = false;


// =========================
// 时间转换
// =========================

function minuteToTime(minute) {

    const h = Math.floor(minute / 60);
    const m = minute % 60;

    return (
        String(h).padStart(2, "0")
        + ":"
        + String(m).padStart(2, "0")
    );
}

function timeToMinute(timeString) {

    const parts = timeString.split(":");

    return (
        parseInt(parts[0]) * 60
        + parseInt(parts[1])
    );
}


// =========================
// 创建预约
// =========================

document.querySelectorAll(".timeline").forEach(timeline => {

    // 开始拖动

    timeline.addEventListener("pointerdown", function (event) {

        const isTouch =
            event.pointerType === "touch";

        if (event.target !== timeline) {
            return;
        }

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
            previewBlock.style.background = "rgba(74,137,220,.5)";
            previewBlock.style.borderRadius = "4px";
            previewBlock.style.pointerEvents = "none";

            previewBlock.style.left =
                startMinute * PIXELS_PER_MINUTE + "px";

            previewBlock.style.width = "0px";

            timeline.appendChild(previewBlock);

        };

        if (isTouch) {

            longPressTriggered = false;

            longPressTimer =
                setTimeout(beginCreate, 800);   // ← 改这里控制长按时间

        }
        else {

            beginCreate();

        }

    });


    // 拖动预览

    timeline.addEventListener("pointermove", function (event) {

        if (
            event.pointerType === "touch"
            && !longPressTriggered
        ) {
            return;
        }

        if (!isDragging) {
            return;
        }

        if (timeline !== currentTimeline) {
            return;
        }


        const rect =
            timeline.getBoundingClientRect();

        let x =
            event.clientX - rect.left;

        let currentMinute =
            0 +
            Math.round(
                x / PIXELS_PER_MINUTE
            );

        currentMinute =
            Math.round(
                currentMinute / 10
            ) * 10;

        let leftMinute =
            Math.min(
                startMinute,
                currentMinute
            );

        let rightMinute =
            Math.max(
                startMinute,
                currentMinute
            );

        previewBlock.style.left =
            (
                (leftMinute - 0)
                * PIXELS_PER_MINUTE
            ) + "px";

        previewBlock.style.width =
            (
                (rightMinute - leftMinute)
                * PIXELS_PER_MINUTE
            ) + "px";

    });


    // 松开鼠标

    timeline.addEventListener("pointerup", function (event) {

        clearTimeout(longPressTimer);

        longPressTimer = null;

        if (
            event.pointerType === "touch"
            &&
            !longPressTriggered
        ) {
            return;
        }

        if (!isDragging) {
            return;
        }

        if (timeline !== currentTimeline) {
            return;
        }

        isDragging = false;

        const rect =
            timeline.getBoundingClientRect();

        let x =
            event.clientX - rect.left;

        let endMinute =
            0 +
            Math.round(
                x / PIXELS_PER_MINUTE
            );

        endMinute =
            Math.round(
                endMinute / 10
            ) * 10;

        endMinute =
            Math.max(
                0,
                Math.min(
                    1440,
                    endMinute
                )
            );

        let leftMinute =
            Math.min(
                startMinute,
                endMinute
            );

        let rightMinute =
            Math.max(
                startMinute,
                endMinute
            );

        // 至少拖动10分钟

        if ((rightMinute - leftMinute) < 10) {

            if (previewBlock) {
                previewBlock.remove();
            }

            return;
        }

        previewBlock.remove();

        pendingReservation = {

            instrument:
                timeline.dataset.instrument,

            start:
                leftMinute,

            end:
                rightMinute

        };

        document.getElementById(
            "start-time"
        ).value =
            minuteToTime(
                leftMinute
            );

        document.getElementById(
            "end-time"
        ).value =
            minuteToTime(
                rightMinute
            );

        document.getElementById(
            "modal-title"
        ).innerText =
            "New Reservation";

        document.getElementById(
            "reservation-modal"
        ).style.display =
            "flex";

    });


    // 鼠标离开

    timeline.addEventListener("pointerleave", function () {

        clearTimeout(longPressTimer);

        if (!isDragging) {
            return;
        }

        if (previewBlock) {
            previewBlock.remove();
        }

        isDragging = false;

    });

});

// =========================
// Modify
// =========================
document
    .querySelectorAll(".reservation")
    .forEach(reservation => {
       

        reservation.addEventListener(
            "pointerdown",
            function (event) {

                if (
                    event.target.classList.contains("resize-left")
                    || event.target.classList.contains("resize-right")
                ) {
                    return;
                }

                mouseDownReservation = reservation;

                dragStartX = event.clientX;

                originalStart =
                    parseInt(reservation.dataset.start);

                originalEnd =
                    parseInt(reservation.dataset.end);

                movedReservation = false;

                event.stopPropagation();
            }
        );

        reservation.addEventListener(
            "click",
            function (event) {

                if (movedReservation) {

                    movedReservation = false;

                    return;
                }


                event.stopPropagation();

                editingReservation = {

                    id:
                        reservation.dataset.id,

                    instrument:
                        reservation
                            .parentElement
                            .dataset
                            .instrument

                };

                document.getElementById(
                    "modal-title"
                ).innerText =
                    "Edit Reservation";

                document.getElementById(
                    "user-select"
                ).value =
                    reservation.dataset.user;

                document.getElementById(
                    "color-select"
                ).value =
                    reservation.dataset.color;

                document.getElementById(
                    "start-time"
                ).value =
                    minuteToTime(
                        parseInt(
                            reservation.dataset.start
                        )
                    );

                document.getElementById(
                    "end-time"
                ).value =
                    minuteToTime(
                        parseInt(
                            reservation.dataset.end
                        )
                    );

                document.getElementById(
                    "comment"
                ).value =
                    reservation.dataset.comment || "";

                document.getElementById(
                    "reservation-modal"
                ).style.display =
                    "flex";

            }

        );


    });


// =========================
// Cancel
// =========================

document
    .getElementById("cancel-btn")
    .addEventListener("click", () => {

        document
            .getElementById(
                "reservation-modal"
            )
            .style.display = "none";

    });


// =========================
// Save
// =========================

document
    .getElementById("save-btn")
    .addEventListener("click", () => {

        const user =
            document
                .getElementById(
                    "user-select"

                )
                .value;

        const color =
            document.getElementById(
                "color-select"
            ).value;

        const start =
            timeToMinute(
                document
                    .getElementById(
                        "start-time"
                    )
                    .value
            );

        const end =
            timeToMinute(
                document
                    .getElementById(
                        "end-time"
                    )
                    .value
            );

        const comment =
            document.getElementById(
                "comment"
            ).value;

        if (start >= end) {

            alert(
                "End time must be later than start time."
            );

            return;
        }

        const url =
            editingReservation
                ? "/update_reservation"
                : "/add_reservation";

        const payload = {

            instrument:
                editingReservation
                    ? editingReservation.instrument
                    : pendingReservation.instrument,

            user:
                user,

            start:
                start,

            end:
                end,

            color:
                color,

            password:
                document.getElementById(
                    "password"
                ).value,

            date: document.body.dataset.date,

            room: selectedRoom,

            comment:
                comment,
        };

        if (editingReservation) {

            payload.id =
                editingReservation.id;

        }

        fetch(url, {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                payload
            )

        })
            .then(response =>
                response.json()
            )
            .then(data => {

                if (
                    data.status === "invalid_time"
                ) {

                    alert(
                        "End time must be later than start time."
                    );

                    return;
                }

                if (
                    data.status === "conflict"
                ) {

                    alert(
                        "This time slot is already reserved."
                    );

                    return;
                }

                location.reload();

            });

    });

document
    .getElementById("delete-btn")
    .addEventListener("click", () => {

        if (!editingReservation) {
            return;
        }

        const password =
            prompt(
                "Enter password (leave blank if none)"
            );

        fetch(
            "/delete_reservation",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    id:
                        editingReservation.id,

                    password:
                        password
                })

            }
        )
            .then(response =>
                response.json()
            )
            .then(data => {

                if (
                    data.status ===
                    "wrong_password"
                ) {

                    alert(
                        "Incorrect password"
                    );

                    return;
                }

                location.reload();

            });

    });

// =========================
// Date Navigation
// =========================

document
    .getElementById("prev-day")
    .addEventListener("click", () => {

        let d =
            new Date(
                document.body.dataset.date
            );

        d.setDate(
            d.getDate() - 1
        );

        location.href =
            "/?date=" +
        localDateString(d)

    });


document
    .getElementById("next-day")
    .addEventListener("click", () => {

        let d =
            new Date(
                document.body.dataset.date
            );

        d.setDate(
            d.getDate() + 1
        );

        location.href =
            "/?date=" +
            localDateString(d)

    });


document
    .getElementById("today-btn")
    .addEventListener("click", () => {

        location.href =
            "/?date=" +
            localDateString()

    });

document
    .getElementById("prev-month")
    ?.addEventListener("click", () => {

        let d =
            new Date(
                document.body.dataset.date
            );

        d.setMonth(
            d.getMonth() - 1
        );

        const firstDay =
            d.getFullYear()
            + "-"
            + String(
                d.getMonth() + 1
            ).padStart(2, "0")
            + "-01";

        location.href =
            "/?date=" + firstDay;

    });


document
    .getElementById("next-month")
    ?.addEventListener("click", () => {

        let d =
            new Date(
                document.body.dataset.date
            );

        d.setMonth(
            d.getMonth() + 1
        );

        const firstDay =
            d.getFullYear()
            + "-"
            + String(
                d.getMonth() + 1
            ).padStart(2, "0")
            + "-01";

        location.href =
            "/?date=" + firstDay;

    });

let selectedRoom =
    document.body.dataset.room || "room1";

const roomSelect = document.getElementById("roomSelect");

if (roomSelect) {
    roomSelect.value = selectedRoom;

    roomSelect.addEventListener("change", (e) => {
        selectedRoom = e.target.value;

        const date = document.body.dataset.date;

        location.href =
            "/?date=" +
            localDateString(new Date(document.body.dataset.date)) +
            "&room=" +
            selectedRoom;
    });
}

document.addEventListener(
    "pointermove",
    function (event) {

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

        if (!draggingReservation) {
            return;
        }

        if (!mouseDownReservation) {
            return;
        }


        const deltaMinute =
            Math.round(
                deltaX / PIXELS_PER_MINUTE / 10
            ) * 10;

        let newStart =
            originalStart + deltaMinute;

        let newEnd =
            originalEnd + deltaMinute;

        const duration =
            originalEnd - originalStart;

        // 不允许早于00:00

        if (newStart < 0) {

            newStart = 0;

            newEnd = duration;
        }

        // 不允许晚于24:00

        if (newEnd > 1440) {

            newEnd = 1440;

            newStart = 1440 - duration;
        }


        draggingReservation.style.left =
            ((newStart - 0) * PIXELS_PER_MINUTE)
            + "px";

        draggingReservation.dataset.start =
            newStart;

        draggingReservation.dataset.end =
            newEnd;
    }
);

document.addEventListener(
    "pointerup",
    function () {

        if (!draggingReservation) {
            mouseDownReservation = null;
            return;
        }

        fetch(
            "/update_reservation",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    id:
                        draggingReservation.dataset.id,

                    instrument:
                        draggingReservation
                            .parentElement
                            .dataset
                            .instrument,

                    user:
                        draggingReservation
                            .dataset
                            .user,

                    color:
                        draggingReservation
                            .dataset
                            .color,

                    start:
                        parseInt(
                            draggingReservation
                                .dataset
                                .start
                        ),

                    end:
                        parseInt(
                            draggingReservation
                                .dataset
                                .end
                        ),

                    date:
                        document.body.dataset.date,

                    room:
                        document.body.dataset.room
                })
            }
        )
            .then(r => r.json())
            .then(data => {

                if (data.status === "conflict") {

                    alert("Time conflict");

                    location.reload();

                    return;
                }

                location.reload();
            });

        draggingReservation = null;
        mouseDownReservation = null;
    }
);

// =========================
// Current Time Line
// =========================

function updateNowLine() {

    console.log("updateNowLine called");

    const now =
        new Date();

    const minutes =
        now.getHours() * 60
        + now.getMinutes();

    document
        .querySelectorAll(".now-line")
        .forEach(line => line.remove());

    if (minutes < 0 || minutes > 1440) {
        return;
    }

    const left =
        (minutes - 0)
        * PIXELS_PER_MINUTE;

    document
        .querySelectorAll(".timeline")
        .forEach(timeline => {

            const line =
                document.createElement("div");

            line.className =
                "now-line";

            line.style.left =
                left + "px";

            timeline.appendChild(line);

        });
}


// =========================
// 禁用长按复制
// =========================
document.addEventListener(
    "contextmenu",
    e => e.preventDefault()
);


// =========================
// 根据屏幕宽度动态改变时间条
// =========================
function resizeScheduler() {

    const instrumentWidth = 280;

    const totalHours = 24;

    const availableWidth =
        window.innerWidth
        - instrumentWidth
        - 40;

    let hourWidth =
        availableWidth / totalHours;

    // 最大80px，最小30px
    hourWidth =
        Math.max(30,
            Math.min(80, hourWidth));

    document.documentElement
        .style.setProperty(
            "--hour-width",
            hourWidth + "px"
    );
    PIXELS_PER_MINUTE =
        hourWidth / 60;
}

resizeScheduler();

updateReservationPosition();

window.addEventListener(
    "resize",
    function () {

        resizeScheduler();

        updateReservationPosition();

        updateNowLine();

    }
);

// =========================
// 立即重新校准红线
// =========================
const today =
    new Date()
        .toLocaleDateString("sv-SE");

if (
    document.body.dataset.date
    === today
) {

    updateNowLine();

    setInterval(
        updateNowLine,
        60000
    );
}


// =========================
// 根据屏幕宽度动态改变预约条
// =========================
function updateReservationPosition() {

    document.querySelectorAll(".reservation").forEach(reservation => {

        const start =
            parseInt(reservation.dataset.start);

        const end =
            parseInt(reservation.dataset.end);

        reservation.style.left =
            (start * PIXELS_PER_MINUTE) + "px";

        reservation.style.width =
            ((end - start) * PIXELS_PER_MINUTE) + "px";

    });

}
// =========================
// 使用日本时间UTC+8
// =========================
function localDateString(date = new Date()) {

    const y = date.getFullYear();

    const m = String(
        date.getMonth() + 1
    ).padStart(2, "0");

    const d = String(
        date.getDate()
    ).padStart(2, "0");

    return `${y}-${m}-${d}`;
}