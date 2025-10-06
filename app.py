from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# ---------------------------
# DATABASE INITIALIZATION
# ---------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hospital_name TEXT,
                    ward_name TEXT,
                    beds INTEGER,
                    from_date TEXT,
                    to_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS test_bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lab_name TEXT,
                    test_name TEXT,
                    slots INTEGER,
                    time_slot TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hospital_name TEXT,
                    ward_name TEXT,
                    available_beds INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------
# STATIC DATA
# ---------------------------
hospitals = [
    "Apollo Gleneagles Hospital",
    "AMRI Hospitals",
    "Fortis Hospital",
    "Peerless Hospital",
    "Narayana Superspeciality Hospital",
    "Columbia Asia Hospital",
    "ILS Hospital",
    "Belle Vue Clinic",
    "Medica Superspeciality Hospital",
    "Desun Hospital"
]

pathology_labs = [
    "Apollo Diagnostics",
    "Thyrocare",
    "Dr. Lal PathLabs",
    "Suburban Diagnostics",
    "Metropolis Healthcare",
    "SRL Diagnostics",
    "Redcliffe Labs",
    "Pathkind Labs",
    "Vijaya Diagnostic Centre",
    "Oncquest Laboratories"
]

time_slots = [
    "6:00 AM - 7:00 AM",
    "7:00 AM - 8:00 AM",
    "8:00 AM - 9:00 AM",
    "9:00 AM - 10:00 AM",
    "5:00 PM - 6:00 PM",
    "6:00 PM - 7:00 PM",
    "7:00 PM - 8:00 PM"
]

# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    if 'username' in session:
        return render_template('choice.html', user={'name': session['username']})
    else:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "guest" in request.form:
            return redirect(url_for("choice"))
        return redirect(url_for("choice"))
    return render_template("login.html")

@app.route("/choice")
def choice():
    return render_template("choice.html")

@app.route("/hospitals")
def hospitals_page():
    return render_template("hospitals.html", hospitals=hospitals)

@app.route("/hospital_detail/<name>")
def hospital_detail(name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Fetch wards for this hospital
    cursor.execute("SELECT ward_name, available_beds FROM wards WHERE hospital_name = ?", (name,))
    wards = cursor.fetchall()

    # Fetch all bookings for this hospital
    cursor.execute("""
        SELECT ward_name, beds, from_date, to_date
        FROM bookings
        WHERE hospital_name = ?
        ORDER BY from_date ASC
    """, (name,))
    bookings = cursor.fetchall()
    conn.close()

    return render_template("hospital_detail.html", hospital=name, wards=wards, bookings=bookings)

@app.route("/ward_booking/<hospital>/<ward>", methods=["GET", "POST"])
def ward_booking(hospital, ward):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT available_beds FROM wards WHERE hospital_name=? AND ward_name=?", (hospital, ward))
    result = cursor.fetchone()
    available_beds = result[0] if result else 10  # default

    if request.method == "POST":
        beds = int(request.form["beds"])
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]

        if beds > available_beds:
            return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds, error="Not enough beds available!")

        new_available = available_beds - beds
        cursor.execute("UPDATE wards SET available_beds=? WHERE hospital_name=? AND ward_name=?", (new_available, hospital, ward))
        cursor.execute("INSERT INTO bookings (hospital_name, ward_name, beds, from_date, to_date) VALUES (?, ?, ?, ?, ?)",
                       (hospital, ward, beds, from_date, to_date))
        conn.commit()
        conn.close()
        return render_template("confirmation.html", message=f"{beds} bed(s) booked in {ward} of {hospital} from {from_date} to {to_date}.")

    conn.close()
    return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds)

@app.route("/pathology")
def pathology():
    return render_template("pathology.html", labs=pathology_labs)

@app.route("/lab_detail/<name>")
def lab_detail(name):
    tests = ["Blood Test", "Blood Sugar Test", "Thyroid Test", "Vitamin D Test", "Cholesterol Test"]
    return render_template("lab_detail.html", lab=name, tests=tests)

@app.route("/test_booking/<lab>/<test>", methods=["GET", "POST"])
def test_booking(lab, test):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    max_slots = 10
    available_slots = {}

    # Calculate available slots for each time slot
    for slot in time_slots:
        cursor.execute("SELECT SUM(slots) FROM test_bookings WHERE lab_name=? AND test_name=? AND time_slot=?", (lab, test, slot))
        booked = cursor.fetchone()[0]
        booked = booked if booked else 0
        available_slots[slot] = max_slots - booked

    total_available = sum(available_slots.values())

    if request.method == "POST":
        slots = int(request.form["slots"])
        time_slot = request.form["time_slot"]

        if available_slots[time_slot] <= 0:
            conn.close()
            return render_template("test_booking.html", lab=lab, test=test, total_available=total_available,
                                   time_slots=time_slots, available_slots=available_slots,
                                   error="This slot time is already full. Please choose another time.")

        cursor.execute("INSERT INTO test_bookings (lab_name, test_name, slots, time_slot) VALUES (?, ?, ?, ?)",
                       (lab, test, slots, time_slot))
        conn.commit()
        conn.close()
        return render_template("confirmation.html", message=f"{slots} slot(s) booked for {test} at {lab} during {time_slot}.")

    conn.close()
    return render_template("test_booking.html", lab=lab, test=test, total_available=total_available,
                           time_slots=time_slots, available_slots=available_slots)

@app.route("/payment", methods=["GET", "POST"])
def payment():
    if request.method == "POST":
        return render_template("payment.html", success="Payment successful!")
    return render_template("payment.html")

@app.route("/confirmation")
def confirmation():
    return render_template("confirmation.html", message="Booking confirmed!")

if __name__ == "__main__":
    app.run(debug=True)
