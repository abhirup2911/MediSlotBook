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
# - beds_calendar[hospital][ward][date_str] = booked_count
# - test_slots[lab][test][time_slot] = booked_count
# - bookings list keeps records for auditing (optional)
# ---------------------------
beds_calendar = {}     # nested dict
test_slots = {}        # nested dict
bookings = []          # list of confirmed bookings for record

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
# Helper functions
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
            # Guest should not be allowed to pay — they will be asked to login when trying to pay
            return redirect(url_for("choice"))
        else:
            # Save minimal user info in session for prototype
            session["user"] = {
                "name": request.form.get("fullname") or request.form.get("name") or "User",
                "age": request.form.get("age"),
                "address": request.form.get("address"),
                "email": request.form.get("email"),
                "phone": request.form.get("phone")
            }
            # After login, if there is a pending booking, redirect to confirm page
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
    return render_template("hospitals.html", hospitals=hospitals)

@app.route("/hospital/<name>")
def hospital_detail(name):
    # templates expect hospital name variable
    return render_template("wards.html", hospital=name, wards=wards)

@app.route("/hospital/<hospital>/ward/<ward>", methods=["GET", "POST"])
def book_bed(hospital, ward):
    # show booking form on GET
    if request.method == "POST":
        # collect requested booking info
        beds = int(request.form.get("beds"))
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")
        # validate date format
        try:
            start_date = parse_date(start_date_str)
            end_date = parse_date(end_date_str)
            if end_date < start_date:
                return render_template("book_bed.html", hospital=hospital, ward=ward,
                                       error="End date must be same or after start date.")
        except Exception:
            return render_template("book_bed.html", hospital=hospital, ward=ward,
                                   error="Invalid date format. Use YYYY-MM-DD.")
        # store pending booking in session (will be confirmed on payment)
        session["pending_booking"] = {
            "type": "bed",
            "hospital": hospital,
            "ward": ward,
            "beds": beds,
            "start_date": start_date_str,
            "end_date": end_date_str
        }
        return redirect(url_for("confirm_booking"))
    return render_template("book_bed.html", hospital=hospital, ward=ward)

# ---------------------------
# Labs: list, tests, book-test
# ---------------------------
@app.route("/labs")
def labs_page():
    return render_template("labs.html", labs=labs)

@app.route("/lab/<name>")
def lab_detail(name):
    return render_template("tests.html", lab=name, tests=tests)

@app.route("/lab/<lab>/test/<test>", methods=["GET", "POST"])
def book_test(lab, test):
    if request.method == "POST":
        slots = int(request.form.get("slots"))
        time_slot = request.form.get("time_slot")
        # basic validation
        if time_slot not in time_slots:
            return render_template("book_test.html", lab=lab, test=test, time_slots=time_slots,
                                   error="Invalid time slot selected.")
        # pending booking saved in session
        session["pending_booking"] = {
            "type": "test",
            "lab": lab,
            "test": test,
            "slots": slots,
            "time_slot": time_slot
        }
        return redirect(url_for("confirm_booking"))
    return render_template("book_test.html", lab=lab, test=test, time_slots=time_slots)

# ---------------------------
# Confirm Page (shows pending booking)
# ---------------------------
@app.route("/confirm_booking")
def confirm_booking():
    pending = session.get("pending_booking")
    if not pending:
        return redirect(url_for("choice"))  # nothing to confirm
    # Render the right template depending on booking type
    if pending["type"] == "bed":
        return render_template("confirm_booking.html",
                               hospital=pending["hospital"],
                               ward=pending["ward"],
                               beds=pending["beds"],
                               start_date=pending["start_date"],
                               end_date=pending["end_date"])
    else:
        # test booking
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
    # require logged-in (not Guest)
    if not user or user.get("name") == "Guest":
        # Ask to login first. Keep pending booking in session.
        # Redirect to login page so they can create account and then continue.
        return redirect(url_for("login"))
    # Process bed booking
    if pending["type"] == "bed":
        hospital = pending["hospital"]
        ward = pending["ward"]
        beds_requested = int(pending["beds"])
        start_date = parse_date(pending["start_date"])
        end_date = parse_date(pending["end_date"])
        # Check availability for all dates in range
        for single_date in daterange(start_date, end_date):
            date_str = single_date.isoformat()
            booked = beds_calendar.setdefault(hospital, {}).setdefault(ward, {}).get(date_str, 0)
            if booked + beds_requested > DEFAULT_BEDS_PER_WARD:
                # Not enough beds on this date
                msg = (f"Not enough beds available on {date_str}. "
                       f"{DEFAULT_BEDS_PER_WARD - booked} beds left that day.")
                return render_template("confirm_booking.html",
                                       hospital=hospital, ward=ward,
                                       beds=beds_requested,
                                       start_date=pending["start_date"],
                                       end_date=pending["end_date"],
                                       error=msg)
        # All dates ok — reserve them
        for single_date in daterange(start_date, end_date):
            date_str = single_date.isoformat()
            current = beds_calendar[hospital][ward].get(date_str, 0)
            beds_calendar[hospital][ward][date_str] = current + beds_requested
        # record booking
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
        # clear pending booking
        session.pop("pending_booking", None)
        # show success message on payment page
        return render_template("payment.html", success=f"Your bed(s) have been booked. Thank you for using MediSlotBook.")
    # Process test booking
    elif pending["type"] == "test":
        lab = pending["lab"]
        test_name = pending["test"]
        slots_requested = int(pending["slots"])
        time_slot = pending["time_slot"]
        # check availability for that lab/test/time_slot
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
        return render_template("payment.html", success=f"Your slot(s) have been booked. Thank you for using MediSlotBook.")
    else:
        return render_template("payment.html", error="Unknown booking type.")

# ---------------------------
# Optional: view bookings (for debugging)
# ---------------------------
@app.route("/_debug_bookings")
def debug_bookings():
    # return a simple text page (do NOT expose in production)
    return {"bookings": bookings, "beds_calendar": beds_calendar, "test_slots": test_slots}

if __name__ == "__main__":
    app.run(debug=True)
