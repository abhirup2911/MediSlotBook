from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta

app = Flask(__name__)
bookings = []
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
DEFAULT_TOTAL_SLOTS_PER_TEST = 10
DEFAULT_SLOTS_PER_TIME_SLOT = 3

# ---------------------------
# In-memory booking stores
# ---------------------------
beds_calendar = {}
test_slots = {}
bookings = []

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
        # Clear any leftover pending booking
        session.pop("pending_booking", None)

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
    tests_dict = {}
    for t in tests:
        total_booked = test_slots.get(name, {}).get(t, {}).get("total", 0)
        available = max(0, DEFAULT_TOTAL_SLOTS_PER_TEST - total_booked)
        tests_dict[t] = available

    lab_bookings = [
        b for b in bookings
        if b["type"] == "test" and b["lab"] == name
    ]

    return render_template(
        "lab_detail.html",
        name=name,
        tests=tests_dict,
        lab_bookings=lab_bookings
    )

@app.route("/book_test/<lab>/<test>", methods=["GET", "POST"])
def test_booking_view(lab, test):
    # Predefined time slots
    time_slots = [
        "6:00AM - 7:00AM",
        "7:00AM - 8:00AM",
        "8:00AM - 9:00AM",
        "9:00AM - 10:00AM",
        "5:00PM - 6:00PM",
        "6:00PM - 7:00PM",
        "7:00PM - 8:00PM"
    ]

    # Compute available time slots based on current bookings
    available_times = []
    for ts in time_slots:
        booked_count = test_slots.get(lab, {}).get(test, {}).get(ts, 0)
        if booked_count < DEFAULT_SLOTS_PER_TIME_SLOT:
            available_times.append(ts)

    if request.method == "POST":
        slots = request.form.get("slots")
        date = request.form.get("date")
        time_slot = request.form.get("time")

        if not slots or not date or not time_slot:
            flash("Please fill in all fields before booking.")
            return redirect(url_for("test_booking_view", lab=lab, test=test))

        # Save as pending booking in session
        session["pending_booking"] = {
            "type": "test",
            "lab": lab,
            "test": test,
            "slots": int(slots),
            "date": date,
            "time_slot": time_slot
        }

        # Redirect to confirm page
        return redirect(url_for("confirm_booking"))

    return render_template(
        "test_booking.html",
        lab=lab,
        test=test,
        available_times=available_times
    )


# ---------------------------
# Confirm and Payment
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
# Institution Login & Dashboard
# ---------------------------

institution_credentials = {
    # Hospitals
    "IPGMER & SSKM Hospital": "ipgmer123",
    "Chittaranjan National Cancer Institute": "cnci123",
    "Saroj Gupta Cancer Centre & Research Institute": "saroj123",
    "Belle Vue Clinic": "belle123",
    "AMRI Hospitals": "amri123",
    "Apollo Gleneagles Hospital": "apollo123",
    "Medica Superspecialty Hospital": "medica123",
    "Fortis Hospital, Anandapur": "fortis123",
    "Rabindranath Tagore International Institute of Cardiac Sciences": "rtiics123",
    "Ruby General Hospital": "ruby123",

    # Labs
    "Dr Lal PathLabs": "lal123",
    "Metropolis Healthcare": "metro123",
    "SRL Diagnostics": "srl123",
    "Apollo Diagnostics": "apolloDiag123",
    "Thyrocare": "thyro123",
    "Vijaya Diagnostic Centre": "vijaya123",
    "Pathkind Labs": "pathkind123",
    "Oncquest Laboratories": "oncquest123",
    "Medall Diagnostics": "medall123",
    "Quest Diagnostics India": "quest123",
    "Healthians": "health123"
}

@app.route("/institution_login", methods=["GET", "POST"])
def institution_login():
    if request.method == "POST":
        name = request.form.get("institution_name")
        password = request.form.get("password")
        if name in institution_credentials and institution_credentials[name] == password:
            session["institution"] = name
            return redirect(url_for("institution_dashboard"))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template("institution_login.html", hospitals=hospitals, labs=labs)

@app.route("/institution_dashboard")
def institution_dashboard():
    if "institution" not in session:
        return redirect(url_for("institution_login"))
    institution_name = session["institution"]

    related_bookings = []
    for b in bookings:
        if b["type"] == "bed" and b["hospital"] == institution_name:
            related_bookings.append(b)
        elif b["type"] == "test" and b["lab"] == institution_name:
            related_bookings.append(b)

    return render_template("institution_dashboard.html",
                           institution=institution_name,
                           related_bookings=related_bookings)


@app.route("/institution_logout")
def institution_logout():
    session.pop("institution", None)
    flash("Logged out successfully.")
    return redirect(url_for("institution_login"))


# ---------------------------
# Debug Helper
# ---------------------------
@app.route("/_debug_bookings")
def debug_bookings():
    return {"bookings": bookings, "beds_calendar": beds_calendar, "test_slots": test_slots}


# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
