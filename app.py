from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, math
from urllib.parse import quote_plus
from datetime import datetime, timedelta, date
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# ---------------------- ✅ APP CONFIG
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "your-secret-key"

# ---------------------- ✅ DATABASE CONFIG
db_password = quote_plus("admin@123")
db_user = "postgres"
db_host = "localhost"
db_port = "5432"
db_name = "smartpetdb"

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------------- ✅ FAST2SMS CONFIG
FAST2SMS_API_KEY = "PASTE_YOUR_FAST2SMS_API_KEY_HERE"

def send_sms(phone, message):
    try:
        requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            json={
                "route": "q",
                "message": message,
                "language": "english",
                "numbers": phone
            },
            headers={
                "authorization": FAST2SMS_API_KEY,
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        print("SMS Failed:", e)

# ---------------------- ✅ MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(15))
    pets = db.relationship("Pet", backref="owner", lazy=True)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    species = db.Column(db.String(100))
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    vaccines = db.relationship("Vaccine", backref="pet", lazy=True)

class Vaccine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(150), nullable=False)
    last_given_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey("pet.id"), nullable=False)

class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

# ---------------------- ✅ DISTANCE FUNCTION
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ---------------------- ✅ AUTH ROUTES
@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "user_id" in session else render_template("base.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Invalid login")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"]),
            phone=request.form.get("phone")
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created!")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("login"))

# ---------------------- ✅ DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# ---------------------- ✅ PET PAGE (ADD + VIEW)
@app.route("/pet", methods=["GET", "POST"])
def pet():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        pet = Pet(
            name=request.form["name"],
            species=request.form["species"],
            breed=request.form["breed"],
            age=int(request.form["age"]),
            user_id=user.id
        )
        db.session.add(pet)
        db.session.commit()
        flash("Pet added successfully!")
        return redirect(url_for("pet"))

    pets = Pet.query.filter_by(user_id=user.id).all()
    return render_template("pet.html", pets=pets)

# ---------------------- ✅ PET PROFILE
@app.route("/pet/<int:pet_id>")
def pet_profile(pet_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    pet = Pet.query.get_or_404(pet_id)
    vaccines = Vaccine.query.filter_by(pet_id=pet.id).all()
    today = date.today()

    return render_template("pet_profile.html", pet=pet, vaccines=vaccines, now=today)

# ---------------------- ✅ ADD VACCINE
@app.route("/add_vaccine/<int:pet_id>", methods=["GET", "POST"])
def add_vaccine(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    if request.method == "POST":
        vaccine = Vaccine(
            vaccine_name=request.form["vaccine_name"],
            last_given_date=datetime.strptime(request.form["last_given_date"], "%Y-%m-%d").date(),
            next_due_date=datetime.strptime(request.form["next_due_date"], "%Y-%m-%d").date(),
            pet_id=pet.id
        )
        db.session.add(vaccine)
        db.session.commit()
        flash("Vaccine added!")
        return redirect(url_for("pet_profile", pet_id=pet.id))

    return render_template("add_vaccine.html", pet=pet)

# ---------------------- ✅ EXTRA PAGES
@app.route("/shop")
def shop():
    return render_template("shop.html")

@app.route("/agripet")
def agripet():
    return render_template("Agripet.html")

@app.route("/health")
def health():
    return render_template("health.html")

@app.route("/doctor_finder")
def doctor_finder():
    return render_template("doctor_finder.html")

# ---------------------- ✅ CLINIC API
@app.route("/clinics_within_20km")
def clinics_within_20km():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Missing lat/lon"}), 400

    user_lat, user_lon = float(lat), float(lon)
    count = 0

    for c in Clinic.query.all():
        if c.latitude and c.longitude:
            if calculate_distance(user_lat, user_lon, c.latitude, c.longitude) <= 20:
                count += 1

    return jsonify({"clinics_within_20km": count})

# ---------------------- ✅ AUTO SMS REMINDER
def send_vaccine_reminders():
    reminder_day = date.today() + timedelta(days=1)
    vaccines = Vaccine.query.filter(Vaccine.next_due_date == reminder_day).all()

    for v in vaccines:
        if v.pet and v.pet.owner and v.pet.owner.phone:
            send_sms(
                v.pet.owner.phone,
                f"Reminder! Pet: {v.pet.name}, Vaccine: {v.vaccine_name}, Due: {v.next_due_date}"
            )

scheduler = BackgroundScheduler()
scheduler.add_job(send_vaccine_reminders, 'interval', hours=24, id="vaccine_job", replace_existing=True)
scheduler.start()

# ---------------------- ✅ RUN APP
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
