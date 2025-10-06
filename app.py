from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_to_a_secure_random_value"  # set a real secret key for production

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

# Root: Welcome page (index.html)
@app.route("/")
def index():
    # show the welcome splash
    return render_template("index.html")

# Login: create a simple session (guest or fullname)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # If user clicked "Login as Guest" button, form includes name "guest"
        if "guest" in request.form:
            session['username'] = "Guest"
        else:
            # create account — store just a display name in session for now
            fullname = request.form.get("fullname", "").strip()
            session['username'] = fullname if fullname else "User"
        return redirect(url_for("choice"))
    return render_template("login.html")

@app.route("/choice")
def choice():
    # show choice page — pass user object expected by choice.html
    user = {"name": session.get("username", "Guest")}
    return render_template("choice.html", user=user)

# Hospitals listing (renders the template file you provided: hospital.html)
@app.route("/hospitals")
def hospitals_page():
    # your template file is hospital.html (singular), so render that
    return render_template("hospital.html", hospitals=hospitals)

# Hospital detail page
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

# Ward booking
@app.route("/ward_booking/<hospital>/<ward>", methods=["GET", "POST"])
def ward_booking(hospital, ward):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT available_beds FROM wards WHERE hospital_name=? AND ward_name=?", (hospital, ward))
    result = cursor.fetchone()
    available_beds = result[0] if result else 10  # default

    if request.method == "POST":
        try:
            beds = int(request.form["beds"])
        except (ValueError, KeyError):
            conn.close()
            return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds, error="Invalid bed count.")

        from_date = request.form["from_date"]
        to_date = request.form["to_date"]

        if beds > available_beds:
            conn.close()
            return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds, error="Not enough beds available!")

        new_available = available_beds - beds
        cursor.execute("UPDATE wards SET available_beds=? WHERE hospital_name=? AND ward_name=?", (new_available, hospital, ward))
        cursor.execute("INSERT INTO bookings (hospital_name, ward_name, beds, from_date, to_date) VALUES (?, ?, ?, ?, ?)",
                       (hospital, ward, beds, from_date, to_date))
        conn.commit()
        conn.close()

        # Render confirmation with explicit details (template updated will handle message or details)
        return render_template("confirmation.html",
                               message=f"{beds} bed(s) booked in {ward} of {hospital} from {from_date} to {to_date}.",
                               hospital=hospital, ward=ward, beds=beds, from_date=from_date, to_date=to_date)

    conn.close()
    return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds)

# Pathology labs listing — create a labs_page route (choice.html refers to labs_page)
@app.route("/labs")
def labs_page():
    return render_template("labs.html", labs=pathology_labs)

# Lab detail — pass a dict of tests -> available slots for template that expects items()
@app.route("/lab_detail/<name>")
def lab_detail(name):
    tests_list = ["Blood Test", "Blood Sugar Test", "Thyroid Test", "Vitamin D Test", "Cholesterol Test"]
    # make a tests dict so templates that call tests.items() work
    tests = {t: 10 for t in tests_list}  # default 10 slots each
    return render_template("lab_detail.html", name=name, tests=tests)

# Test booking
@app.route("/test_booking/<lab>/<test>", methods=["GET", "POST"])
def test_booking(lab, test):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    max_slots = 10
    available_slots = {}

    # Calculate available slots for each time slot
    for slot in time_slots:
        cursor.execute("SELECT SUM(slots) FROM test_bookings WHERE lab_name=? AND test_name=? AND time_slot=?", (lab, test, slot))
        booked_row = cursor.fetchone()
        booked = booked_row[0] if booked_row and booked_row[0] is not None else 0
        available_slots[slot] = max_slots - booked

    total_available = sum(available_slots.values())

    if request.method == "POST":
        try:
            slots = int(request.form["slots"])
        except (ValueError, KeyError):
            conn.close()
            return render_template("test_booking.html", lab=lab, test=test, total_available=total_available,
                                   time_slots=time_slots, available_slots=available_slots,
                                   error="Invalid slot count.")
        time_slot = request.form["time_slot"]

        if available_slots.get(time_slot, 0) <= 0:
            conn.close()
            return render_template("test_booking.html", lab=lab, test=test, total_available=total_available,
                                   time_slots=time_slots, available_slots=available_slots,
                                   error="This slot time is already full. Please choose another time.")

        cursor.execute("INSERT INTO test_bookings (lab_name, test_name, slots, time_slot) VALUES (?, ?, ?, ?)",
                       (lab, test, slots, time_slot))
        conn.commit()
        conn.close()
        return render_template("confirmation.html", message=f"{slots} slot(s) booked for {test} at {lab} during {time_slot}.",
                               lab=lab, test=test, slots=slots, time_slot=time_slot)

    conn.close()
    return render_template("test_booking.html", lab=lab, test=test, total_available=total_available,
                           time_slots=time_slots, available_slots=available_slots)

# Payment
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if request.method == "POST":
        # In a real app you'd verify payment; here we just show success
        return render_template("payment.html", success="Payment successful!")
    # If payment.html expects labs or other context, pass minimal safe context
    return render_template("payment.html", labs=pathology_labs)

# Generic confirmation route (if used)
@app.route("/confirmation")
def confirmation():
    # This route can show a default confirmation message if no details passed
    return render_template("confirmation.html", message="Booking confirmed!")

if __name__ == "__main__":
    app.run(debug=True)
