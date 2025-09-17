from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Dummy hospital and lab data
hospitals = {
    "Apollo Hospital": {"Maternity Ward": 10, "ICU": 5, "General Ward": 15},
    "Fortis Hospital": {"Pediatric Ward": 8, "ICU": 6, "General Ward": 12},
    "AIIMS": {"Emergency Ward": 7, "ICU": 10, "Maternity Ward": 9},
    "Rabindranath Tagore International Institute of Cardiac Sciences": {"Emergency Ward": 7, "ICU": 10, "Maternity Ward": 9},
    "Belle Vue Clinic": {"Maternity Ward": 10, "ICU": 5, "General Ward": 15},
    "Chittaranjan National Cancer Institute": {"Pediatric Ward": 8, "ICU": 6, "General Ward": 12},
    "Ruby General Hospital": {"Emergency Ward": 7, "ICU": 10, "Maternity Ward": 9} 
}

labs = {
    "Dr Lal Path Labs": {"Blood Test": 20, "Blood-Sugar Test": 15, "X-Ray": 10},
    "Thyrocare": {"Thyroid Test": 12, "MRI": 6, "Vitamin Test": 8},
    "SRL Diagnostics": {"Liver Function Test": 14, "Kidney Function Test": 10, "CT Scan": 5},
    "Apollo Diagnostics": {"Blood Test": 20, "Blood-Sugar Test": 15, "X-Ray": 10},
    "Redcliffe Labs": {"Liver Function Test": 14, "Kidney Function Test": 10, "CT Scan": 5}, 
    "Healthians": {"Blood Test": 20, "Blood-Sugar Test": 15, "X-Ray": 10},
    "Metropolis Healthcare": {"Liver Function Test": 14, "Kidney Function Test": 10, "CT Scan": 5}
}

time_slots = ["6:00AM - 7:00AM", "7:00AM - 8:00AM", "10:00AM - 11:00AM",
              "12:00PM - 1:00PM", "3:00PM - 4:00PM", "6:00PM - 7:00PM"]

# ---------- ROUTES ----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if "guest" in request.form:
            session["user"] = {"name": "Guest"}
            return redirect(url_for("choice"))
        else:
            session["user"] = {
                "name": request.form["fullname"],
                "age": request.form["age"],
                "address": request.form["address"],
                "email": request.form["email"],
                "phone": request.form["phone"]
            }
            return redirect(url_for("choice"))
    return render_template("login.html")

@app.route("/choice")
def choice():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("choice.html", user=session["user"])

# ---------- HOSPITALS ----------

@app.route("/hospitals")
def show_hospitals():
    return render_template("hospitals.html", hospitals=hospitals)

@app.route("/hospital/<name>")
def hospital_detail(name):
    return render_template("hospital_detail.html", name=name, wards=hospitals[name])

@app.route("/hospital/<hospital>/<ward>", methods=["GET", "POST"])
def ward_booking(hospital, ward):
    available_beds = hospitals[hospital][ward]
    if request.method == "POST":
        beds = request.form["beds"]
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        return render_template("confirm_bed_booking.html", hospital=hospital, ward=ward,
                               beds=beds, from_date=from_date, to_date=to_date)
    return render_template("ward_booking.html", hospital=hospital, ward=ward, available_beds=available_beds)

# ---------- LABS ----------

@app.route("/labs")
def show_labs():
    return render_template("labs.html", labs=labs)

@app.route("/lab/<name>")
def lab_detail(name):
    return render_template("lab_detail.html", name=name, tests=labs[name])

@app.route("/lab/<lab>/<test>", methods=["GET", "POST"])
def test_booking(lab, test):
    available_slots = labs[lab][test]
    if request.method == "POST":
        slots = request.form["slots"]
        time_slot = request.form["time_slot"]
        return render_template("confirm_test_booking.html", lab=lab, test=test,
                               slots=slots, time_slot=time_slot)
    return render_template("test_booking.html", lab=lab, test=test,
                           available_slots=available_slots, time_slots=time_slots)

# ---------- PAYMENT ----------

@app.route("/payment", methods=["POST"])
def payment():
    return render_template("payment.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
