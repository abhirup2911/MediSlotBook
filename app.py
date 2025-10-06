from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d %b %Y'):
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime(format)
    except Exception:
        return value
# ---------------------------
# Prototype data (initial)
# ---------------------------
hospitals = [
    "IPGMER & SSKM Hospital",
    "Chittaranjan National Cancer Institute",
    "Saroj Gupta Cancer Centre & Research Institute",
    "Belle Vue Clinic",
    "AMRI Hospitals",
    "Apollo Gleneagles Hospital",
    "Medica Superspecialty Hospital",
    "Fortis Hospital, Anandapur",
    "Rabindranath Tagore International Institute of Cardiac Sciences",
    "Ruby General Hospital"
]

wards = [
    "Intensive Care Units (ICU)",
    "Medical Wards",
    "Surgical Wards",
    "Maternity Wards"
]

labs = [
    "Dr Lal PathLabs",
    "Metropolis Healthcare",
    "SRL Diagnostics",
    "Apollo Diagnostics",
    "Thyrocare",
    "Vijaya Diagnostic Centre",
    "Pathkind Labs",
    "Oncquest Laboratories",
    "Medall Diagnostics",
    "Quest Diagnostics India",
    "Healthians"
]

tests = [
    "Complete Blood Count (CBC)",
    "Liver Function Tests (LFTs)",
    "Lipid Profile",
    "Blood-Sugar Test",
    "Urinalysis"
]

time_slots = [
    "6:00AM - 7:00AM",
    "7:00AM - 8:00AM",
    "8:00AM - 9:00AM",
    "9:00AM - 10:00AM",
    "5:00PM - 6:00PM",
    "6:00PM - 7:00PM",
    "7:00PM - 8:00PM"
]

# ---------------------------
# Capacity (prototype)
# ---------------------------
DEFAULT_BEDS_PER_WARD = 10
DEFAULT_TOTAL_SLOTS_PER_TEST = 10    # Total quota per test across all slots
DEFAULT_SLOTS_PER_TIME_SLOT = 3      # Max bookings per single time slot

# ---------------------------
# In-memory booking stores (prototype)
# ---------------------------
beds_calendar = {}
test_slots = {}   # test_slots[lab][test]["total"], test_slots[lab][test][time_slot]
bookings = []

# initialize calendars
for h in hospitals:
    beds_calendar[h] = {}
    for w in wards:
        beds_calendar[h][w] = {}

for l in labs:
    test_slots[l] = {}
    for t in tests:
        test_slots[l][t] = {"total": 0}
        for ts in time_slots:
            test_slots[l][t][ts] = 0

# ---------------------------
# Helpers
# ---------------------------
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def parse_date(d):
    return datetime.strptime(d, "%Y-%m-%d").date()

# ---------------------------
# Routes: home, login, choice
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "guest" in request.form:
            session["user"] = {"name": "Guest"}
            return redirect(url_for("choice"))
        else:
            session["user"] = {
                "name": request.form.get("fullname") or request.form.get("name") or "User",
                "age": request.form.get("age"),
                "address": request.form.get("address"),
                "email": request.form.get("email"),
                "phone": request.form.get("phone")
            }
            if session.get("pending_booking"):
                return redirect(url_for("confirm_booking"))
            return redirect(url_for("choice"))
    return render_template("login.html")

@app.route("/choice")
def choice():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("choice.html", user=session["user"])

# ---------------------------
# Hospitals: list, wards, book-bed
# ---------------------------
@app.route("/hospitals")
def hospitals_page():
    return render_template("hospital.html", hospitals=hospitals)

app.add_url_rule('/hospitals', endpoint='show_hospitals', view_func=hospitals_page)

@app.route("/hospital/<name>")
def hospital_detail(name):
    wards_dict = {}
    for w in wards:
        booked_values = beds_calendar.get(name, {}).get(w, {})
        max_booked = max(booked_values.values()) if booked_values else 0
        available = max(0, DEFAULT_BEDS_PER_WARD - max_booked)
        wards_dict[w] = available

    # --- New code: collect all bookings for this hospital ---
    hospital_bookings = [
        b for b in bookings
        if b["type"] == "bed" and b["hospital"] == name
    ]

    return render_template(
        "hospital_detail.html",
        name=name,
        wards=wards_dict,
        hospital_bookings=hospital_bookings
    )

@app.route("/hospital/<hospital>/ward/<ward>", methods=["GET", "POST"])
def ward_booking_view(hospital, ward):
    if request.method == "POST":
        beds = int(request.form.get("beds", 0))
        start_date_str = request.form.get("start_date") or request.form.get("from_date")
        end_date_str = request.form.get("end_date") or request.form.get("to_date")
        try:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            if end_date < start_date:
                return render_template("ward_booking.html", hospital=hospital, ward=ward,
                                       error="End date must be same or after start date.",
                                       available_beds=DEFAULT_BEDS_PER_WARD)
        except Exception:
            return render_template("ward_booking.html", hospital=hospital, ward=ward,
                                   error="Invalid date format. Use YYYY-MM-DD.",
                                   available_beds=DEFAULT_BEDS_PER_WARD)
        session["pending_booking"] = {
            "type": "bed",
            "hospital": hospital,
            "ward": ward,
            "beds": beds,
            "start_date": start_date_str,
            "end_date": end_date_str
        }
        return redirect(url_for("confirm_booking"))
    booked_values = beds_calendar.get(hospital, {}).get(ward, {})
    max_booked = max(booked_values.values()) if booked_values else 0
    available_beds = max(0, DEFAULT_BEDS_PER_WARD - max_booked)
    return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds)

app.add_url_rule('/hospital/<hospital>/ward/<ward>', endpoint='ward_booking', view_func=ward_booking_view, methods=['GET','POST'])

# ---------------------------
# Labs: list, tests, book-test
# ---------------------------
@app.route("/labs")
def labs_page():
    return render_template("labs.html", labs=labs)

app.add_url_rule('/labs', endpoint='show_labs', view_func=labs_page)

@app.route("/lab/<name>")
def lab_detail(name):
    # Build test availability dictionary (your original code)
    tests_dict = {}
    for t in tests:
        total_booked = test_slots.get(name, {}).get(t, {}).get("total", 0)
        available = max(0, DEFAULT_TOTAL_SLOTS_PER_TEST - total_booked)
        tests_dict[t] = available

    # --- NEW CODE: Collect all existing bookings for this lab ---
    lab_bookings = [
        b for b in bookings
        if b["type"] == "test" and b["lab"] == name
    ]

    # Pass everything to the template
    return render_template(
        "lab_detail.html",
        name=name,
        tests=tests_dict,
        lab_bookings=lab_bookings
    )
@app.route("/book_test/<lab>/<test>", methods=["GET", "POST"])
def test_booking_view(lab, test):
    if request.method == "POST":
        # Get form data
        slots = request.form.get("slots")
        date = request.form.get("date")
        time = request.form.get("time")

        # Validate form fields
        if not slots or not date or not time:
            flash("Please fill in all fields before booking.")
            return redirect(url_for("test_booking_view", lab=lab, test=test))

        # Convert slots to integer
        slots = int(slots)

        # --- Store the booking in global list ---
        bookings.append({
            "type": "test",
            "lab": lab,
            "test": test,
            "slots": slots,
            "date": date,
            "time": time
        })

        # --- Update total booked slots for that lab/test ---
        test_slots.setdefault(lab, {}).setdefault(test, {}).setdefault("total", 0)
        test_slots[lab][test]["total"] += slots

        flash(f"{test} booked successfully at {lab} for {date} at {time}!")
        return redirect(url_for("lab_detail", name=lab))

    # For GET request, show booking form
    return render_template("test_booking.html", lab=lab, test=test)
# ---------------------------
# Confirm Page
# ---------------------------
@app.route("/confirm_booking")
def confirm_booking():
    pending = session.get("pending_booking")
    if not pending:
        return redirect(url_for("choice"))
    if pending["type"] == "bed":
        return render_template("confirm_bed_booking.html",
                               hospital=pending["hospital"],
                               ward=pending["ward"],
                               beds=pending["beds"],
                               from_date=pending["start_date"],
                               to_date=pending["end_date"])
    else:
        return render_template("confirm_test_booking.html",
                               lab=pending["lab"],
                               test=pending["test"],
                               slots=pending["slots"],
                               time_slot=pending["time_slot"])

# ---------------------------
# Payment processing
# ---------------------------
@app.route("/payment", methods=["POST"])
def payment():
    pending = session.get("pending_booking")
    user = session.get("user")
    if not pending:
        return render_template("payment.html", error="No pending booking to pay for.")
    if not user or user.get("name") == "Guest":
        return render_template("payment.html", error="Please Login first and then try again.")

    if pending["type"] == "bed":
        hospital = pending["hospital"]
        ward = pending["ward"]
        beds_requested = int(pending["beds"])
        start_date = parse_date(pending["start_date"])
        end_date = parse_date(pending["end_date"])
        for single_date in daterange(start_date, end_date):
            date_str = single_date.isoformat()
            booked = beds_calendar.setdefault(hospital, {}).setdefault(ward, {}).get(date_str, 0)
            if booked + beds_requested > DEFAULT_BEDS_PER_WARD:
                msg = f"Not enough beds available on {date_str}. {DEFAULT_BEDS_PER_WARD - booked} beds left that day."
                return render_template("confirm_bed_booking.html",
                                       hospital=hospital, ward=ward,
                                       beds=beds_requested,
                                       from_date=pending["start_date"],
                                       to_date=pending["end_date"],
                                       error=msg)
        for single_date in daterange(start_date, end_date):
            date_str = single_date.isoformat()
            current = beds_calendar[hospital][ward].get(date_str, 0)
            beds_calendar[hospital][ward][date_str] = current + beds_requested
        bookings.append({
            "type": "bed", "user": user,
            "hospital": hospital, "ward": ward,
            "beds": beds_requested,
            "from": pending["start_date"], "to": pending["end_date"]
        })
        session.pop("pending_booking", None)
        return render_template("payment.html", success="Your bed(s) have been booked. Thank you for using MediSlotBook.")

    elif pending["type"] == "test":
        lab = pending["lab"]
        test_name = pending["test"]
        slots_requested = int(pending["slots"])
        time_slot = pending["time_slot"]

        total_booked = test_slots[lab][test_name]["total"]
        slot_booked = test_slots[lab][test_name][time_slot]

        if total_booked + slots_requested > DEFAULT_TOTAL_SLOTS_PER_TEST:
            msg = "No slots left for this test."
            return render_template("confirm_test_booking.html",
                                   lab=lab, test=test_name,
                                   slots=slots_requested,
                                   time_slot=time_slot,
                                   error=msg)

        if slot_booked + slots_requested > DEFAULT_SLOTS_PER_TIME_SLOT:
            msg = "All slots for this time is already full. Please choose another time."
            return render_template("confirm_test_booking.html",
                                   lab=lab, test=test_name,
                                   slots=slots_requested,
                                   time_slot=time_slot,
                                   error=msg)

        test_slots[lab][test_name]["total"] += slots_requested
        test_slots[lab][test_name][time_slot] += slots_requested
        bookings.append({
            "type": "test", "user": user,
            "lab": lab, "test": test_name,
            "slots": slots_requested,
            "time_slot": time_slot
        })
        session.pop("pending_booking", None)
        return render_template("payment.html", success="Your slot(s) have been booked. Thank you for using MediSlotBook.")

    else:
        return render_template("payment.html", error="Unknown booking type.")

# ---------------------------
# Debug helper
# ---------------------------
@app.route("/_debug_bookings")
def debug_bookings():
    return {"bookings": bookings, "beds_calendar": beds_calendar, "test_slots": test_slots}

if __name__ == "__main__":
    app.run(debug=True)
