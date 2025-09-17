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
    {"id": 1, "name": "IPGMER & SSKM Hospital"},
    {"id": 2, "name": "Chittaranjan National Cancer Institute"},
    {"id": 3, "name": "Saroj Gupta Cancer Centre & Research Institute"},
    {"id": 4, "name": "Belle Vue Clinic"},
    {"id": 5, "name": "AMRI Hospitals"},
    {"id": 6, "name": "Apollo Gleneagles Hospital"},
    {"id": 7, "name": "Medica Superspecialty Hospital"},
    {"id": 8, "name": "Fortis Hospital, Anandapur"},
    {"id": 9, "name": "Rabindranath Tagore International Institute of Cardiac Sciences"},
    {"id": 10, "name": "Ruby General Hospital"}
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

@app.route("/hospital/<int:hospital_id>")
def hospital_detail(hospital_id):
    hospital = next((h for h in hospitals if h["id"] == hospital_id), None)
    if hospital is None:
        return "Hospital not found", 404
    return render_template("wards.html", hospital=hospital["name"], wards=wards, hospital_id=hospital_id)

@app.route("/hospital/<int:hospital_id>/ward/<ward>", methods=["GET", "POST"])
def book_bed(hospital_id, ward):
    hospital = next((h for h in hospitals if h["id"] == hospital_id), None)
    if hospital is None:
        return "Hospital not found", 404
    if request.method == "POST":
        beds = request.form["beds"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        return render_template(
            "confirm_booking.html",
            hospital=hospital["name"],
            ward=ward,
            beds=beds,
            start_date=start_date,
            end_date=end_date
        )
    return render_template("book_bed.html", hospital=hospital["name"], ward=ward)

# ---------------- PATHOLOGY LABS ----------------
labs = [
    {"id": 1, "name": "Dr Lal PathLabs"},
    {"id": 2, "name": "Metropolis Healthcare"},
    {"id": 3, "name": "SRL Diagnostics"},
    {"id": 4, "name": "Apollo Diagnostics"},
    {"id": 5, "name": "Thyrocare"},
    {"id": 6, "name": "Vijaya Diagnostic Centre"},
    {"id": 7, "name": "Pathkind Labs"},
    {"id": 8, "name": "Oncquest Laboratories"},
    {"id": 9, "name": "Medall Diagnostics"},
    {"id": 10, "name": "Quest Diagnostics India"},
    {"id": 11, "name": "Healthians"}
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

@app.route("/lab/<int:lab_id>")
def lab_detail(lab_id):
    lab = next((l for l in labs if l["id"] == lab_id), None)
    if lab is None:
        return "Lab not found", 404
    return render_template("tests.html", lab=lab["name"], tests=tests, lab_id=lab_id)

@app.route("/lab/<int:lab_id>/test/<test>", methods=["GET", "POST"])
def book_test(lab_id, test):
    lab = next((l for l in labs if l["id"] == lab_id), None)
    if lab is None:
        return "Lab not found", 404
    if request.method == "POST":
        slots = request.form["slots"]
        time_slot = request.form["time_slot"]
        return render_template(
            "confirm_test_booking.html",
            lab=lab["name"],
            test=test,
            slots=slots,
            time_slot=time_slot
        )
    return render_template("book_test.html", lab=lab["name"], test=test, time_slots=time_slots)

# ---------------- PAYMENT ----------------
@app.route("/payment")
def payment():
    return render_template("payment.html")

if __name__ == "__main__":
    app.run(debug=True)
