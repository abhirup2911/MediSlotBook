from flask import Flask, render_template

app = Flask(__name__)

# ---------------------------
# Root / Welcome + Choice page
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------------------
# Hospitals: list + detail
# ---------------------------
@app.route("/hospitals")
def hospitals():
    hospitals_list = [
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
    return render_template("hospitals.html", hospitals=hospitals_list)

@app.route("/hospital/<name>")
def hospital_detail(name):
    wards = [
        {"name": "Intensive Care Units (ICU)", "beds": 10},
        {"name": "Medical Wards", "beds": 10},
        {"name": "Surgical Wards", "beds": 10},
        {"name": "Maternity Wards", "beds": 10},
    ]
    return render_template("hospital_detail.html", hospital=name, wards=wards)

# ---------------------------
# Pathology Labs: list + detail
# ---------------------------
@app.route("/pathology")
def pathology():
    labs_list = [
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
        "Healthians",
    ]
    return render_template("pathology.html", labs=labs_list)

@app.route("/lab/<name>")
def lab_detail(name):
    tests = [
        "Complete Blood Count (CBC)",
        "Liver Function Tests (LFTs)",
        "Lipid Profile",
        "Blood-Sugar Test",
        "Urinalysis",
    ]
    return render_template("lab_detail.html", lab=name, tests=tests)

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
