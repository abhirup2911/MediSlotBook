from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- HOME + LOGIN ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "guest" in request.form:
            session["user"] = "Guest User"
            return redirect(url_for("choice"))
        else:
            full_name = request.form["full_name"]
            session["user"] = full_name
            return redirect(url_for("choice"))
    return render_template("login.html")

@app.route("/choice")
def choice():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("choice.html", user=session["user"])

# ---------------- HOSPITALS ----------------
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

@app.route("/hospitals")
def hospitals_page():
    return render_template("hospitals.html", hospitals=hospitals)

@app.route("/hospital/<name>")
def hospital_detail(name):
    return render_template("wards.html", hospital=name, wards=wards)

@app.route("/hospital/<hospital>/ward/<ward>", methods=["GET", "POST"])
def book_bed(hospital, ward):
    if request.method == "POST":
        beds = request.form["beds"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        return render_template(
            "confirm_booking.html",
            hospital=hospital,
            ward=ward,
            beds=beds,
            start_date=start_date,
            end_date=end_date
        )
    return render_template("book_bed.html", hospital=hospital, ward=ward)

# ---------------- PATHOLOGY LABS ----------------
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

@app.route("/labs")
def labs_page():
    return render_template("labs.html", labs=labs)

@app.route("/lab/<name>")
def lab_detail(name):
    return render_template("tests.html", lab=name, tests=tests)

@app.route("/lab/<lab>/test/<test>", methods=["GET", "POST"])
def book_test(lab, test):
    if request.method == "POST":
        slots = request.form["slots"]
        time_slot = request.form["time_slot"]
        return render_template(
            "confirm_test_booking.html",
            lab=lab,
            test=test,
            slots=slots,
            time_slot=time_slot
        )
    return render_template("book_test.html", lab=lab, test=test, time_slots=time_slots)

# ---------------- PAYMENT ----------------
@app.route("/payment")
def payment():
    return render_template("payment.html")

if __name__ == "__main__":
    app.run(debug=True)
