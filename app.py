from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"

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
DEFAULT_SLOTS_PER_TEST = 10

# ---------------------------
# In-memory booking stores (prototype)
# Beds stored per hospital->ward->date
# Test slots stored per lab->test->time_slot
# ---------------------------
beds_calendar = {}     # beds_calendar[hospital][ward][date_str] = booked_count
test_slots = {}        # test_slots[lab][test][time_slot] = booked_count
bookings = []          # list of confirmed bookings (records)

# initialize calendars
for h in hospitals:
    beds_calendar[h] = {}
    for w in wards:
        beds_calendar[h][w] = {}  # date_str -> booked_count

for l in labs:
    test_slots[l] = {}
    for t in tests:
        test_slots[l][t] = {}
        for ts in time_slots:
            test_slots[l][t][ts] = 0

# ---------------------------
# Helpers
# ---------------------------
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def parse_date(d):
    # expects YYYY-MM-DD
    return datetime.strptime(d, "%Y-%m-%d").date()

# ---------------------------
# Routes: home, login, choice
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # If a pending booking exists in session, we'll let user continue after login
    if request.method == "POST":
        if "guest" in request.form:
            session["user"] = {"name": "Guest"}
            return redirect(url_for("choice"))
        else:
            # Save minimal user info in session
            session["user"] = {
                "name": request.form.get("fullname") or request.form.get("name") or "User",
                "age": request.form.get("age"),
                "address": request.form.get("address"),
                "email": request.form.get("email"),
                "phone": request.form.get("phone")
            }
            # if pending booking exists, go to confirm page so they can pay
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

# main hospitals endpoint (keeps name matching many templates)
@app.route("/hospitals")
def hospitals_page():
    # your template file name is hospital.html (you changed it). Render it.
    return render_template("hospital.html", hospitals=hospitals)

# alias 'show_hospitals' used in some templates -> point to same view
app.add_url_rule('/hospitals', endpoint='show_hospitals', view_func=hospitals_page)

# hospital detail (wards). Template name you have: hospital_detail.html
@app.route("/hospital/<name>")
def hospital_detail(name):
    # prepare a dict mapping ward->available beds (current availability)
    # compute "available now" as DEFAULT - max booked on any date (conservative)
    wards_dict = {}
    for w in wards:
        # compute maximum booked across dates for that ward (if any)
        booked_values = beds_calendar.get(name, {}).get(w, {})
        max_booked = max(booked_values.values()) if booked_values else 0
        available = max(0, DEFAULT_BEDS_PER_WARD - max_booked)
        wards_dict[w] = available
    return render_template("hospital_detail.html", name=name, wards=wards_dict)

# booking form: templates expect endpoint name 'ward_booking', so register that name
@app.route("/hospital/<hospital>/ward/<ward>", methods=["GET", "POST"])
def ward_booking_view(hospital, ward):
    # GET -> show booking form (ward_booking.html expects available_beds)
    if request.method == "POST":
        # Accept beds and dates. Templates used "from_date"/"to_date" or "start_date"/"end_date" in messages; be flexible.
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
        # Save pending booking in session (will be finalized on payment)
        session["pending_booking"] = {
            "type": "bed",
            "hospital": hospital,
            "ward": ward,
            "beds": beds,
            "start_date": start_date_str,
            "end_date": end_date_str
        }
        return redirect(url_for("confirm_booking"))
    # GET: compute available beds today (conservative: minimum available across upcoming dates not shown — use default minus current max)
    booked_values = beds_calendar.get(hospital, {}).get(ward, {})
    max_booked = max(booked_values.values()) if booked_values else 0
    available_beds = max(0, DEFAULT_BEDS_PER_WARD - max_booked)
    return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds)

# also register alias endpoint 'ward_booking' so templates calling that name work
app.add_url_rule('/hospital/<hospital>/ward/<ward>', endpoint='ward_booking', view_func=ward_booking_view, methods=['GET','POST'])

# ---------------------------
# Labs: list, tests, book-test
# ---------------------------
@app.route("/labs")
def labs_page():
    # your file is labs.html
    return render_template("labs.html", labs=labs)

# alias expected by templates
app.add_url_rule('/labs', endpoint='show_labs', view_func=labs_page)

@app.route("/lab/<name>")
def lab_detail(name):
    # return tests dict mapping test -> remaining slots per time slot (we'll show default)
    tests_dict = {t: DEFAULT_SLOTS_PER_TEST for t in tests}
    return render_template("lab_detail.html", name=name, tests=tests_dict)

# booking form for tests: templates expect endpoint 'test_booking'
@app.route("/lab/<lab>/test/<test>", methods=["GET", "POST"])
def test_booking_view(lab, test):
    if request.method == "POST":
        slots = int(request.form.get("slots", 0))
        time_slot = request.form.get("time_slot")
        if time_slot not in time_slots:
            return render_template("test_booking.html", lab=lab, test=test, time_slots=time_slots,
                                   error="Invalid time slot selected.", available_slots=DEFAULT_SLOTS_PER_TEST)
        # store pending booking
        session["pending_booking"] = {
            "type": "test",
            "lab": lab,
            "test": test,
            "slots": slots,
            "time_slot": time_slot
        }
        return redirect(url_for("confirm_booking"))
    # GET: compute available slots for this lab/test/time_slot conservatively (show default)
    # templates expect available_slots variable (single number), so we show default minus max booked across slots (conservative)
    # But better UX would show per time slot; for now provide DEFAULT
    return render_template("test_booking.html", lab=lab, test=test, time_slots=time_slots, available_slots=DEFAULT_SLOTS_PER_TEST)

# alias endpoint 'test_booking' so url_for('test_booking', ...) used in templates resolves
app.add_url_rule('/lab/<lab>/test/<test>', endpoint='test_booking', view_func=test_booking_view, methods=['GET','POST'])

# ---------------------------
# Confirm Page (shows pending booking)
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
# Payment processing (finalize booking)
# ---------------------------
@app.route("/payment", methods=["POST"])
def payment():
    pending = session.get("pending_booking")
    user = session.get("user")
    if not pending:
        return render_template("payment.html", error="No pending booking to pay for.")
    # If user not logged in or Guest, show the login-first message
    if not user or user.get("name") == "Guest":
        return render_template("payment.html", error="Please Login first and then try again.")
    # finalize bed booking
    if pending["type"] == "bed":
        hospital = pending["hospital"]
        ward = pending["ward"]
        beds_requested = int(pending["beds"])
        start_date = parse_date(pending["start_date"])
        end_date = parse_date(pending["end_date"])
        # check availability on every date
        for single_date in daterange(start_date, end_date):
            date_str = single_date.isoformat()
            booked = beds_calendar.setdefault(hospital, {}).setdefault(ward, {}).get(date_str, 0)
            if booked + beds_requested > DEFAULT_BEDS_PER_WARD:
                msg = (f"Not enough beds available on {date_str}. "
                       f"{DEFAULT_BEDS_PER_WARD - booked} beds left that day.")
                return render_template("confirm_bed_booking.html",
                                       hospital=hospital, ward=ward,
                                       beds=beds_requested,
                                       from_date=pending["start_date"],
                                       to_date=pending["end_date"],
                                       error=msg)
        # reserve on all dates
        for single_date in daterange(start_date, end_date):
            date_str = single_date.isoformat()
            current = beds_calendar[hospital][ward].get(date_str, 0)
            beds_calendar[hospital][ward][date_str] = current + beds_requested
        # record booking and clear pending
        booking_record = {
            "type": "bed",
            "user": user,
            "hospital": hospital,
            "ward": ward,
            "beds": beds_requested,
            "from": pending["start_date"],
            "to": pending["end_date"]
        }
        bookings.append(booking_record)
        session.pop("pending_booking", None)
        return render_template("payment.html", success="Your bed(s) have been booked. Thank you for using MediSlotBook.")
    # finalize test booking
    elif pending["type"] == "test":
        lab = pending["lab"]
        test_name = pending["test"]
        slots_requested = int(pending["slots"])
        time_slot = pending["time_slot"]
        current = test_slots.setdefault(lab, {}).setdefault(test_name, {}).get(time_slot, 0)
        if current + slots_requested > DEFAULT_SLOTS_PER_TEST:
            msg = (f"Not enough slots available for {time_slot}. "
                   f"{DEFAULT_SLOTS_PER_TEST - current} slots left at that time.")
            return render_template("confirm_test_booking.html",
                                   lab=lab, test=test_name,
                                   slots=slots_requested,
                                   time_slot=time_slot,
                                   error=msg)
        # reserve
        test_slots[lab][test_name][time_slot] = current + slots_requested
        booking_record = {
            "type": "test",
            "user": user,
            "lab": lab,
            "test": test_name,
            "slots": slots_requested,
            "time_slot": time_slot
        }
        bookings.append(booking_record)
        session.pop("pending_booking", None)
        return render_template("payment.html", success="Your slot(s) have been booked. Thank you for using MediSlotBook.")
    else:
        return render_template("payment.html", error="Unknown booking type.")

# ---------------------------
# Debug helper (optional)
# ---------------------------
@app.route("/_debug_bookings")
def debug_bookings():
    return {"bookings": bookings, "beds_calendar": beds_calendar, "test_slots": test_slots}

if __name__ == "__main__":
    app.run(debug=True)
