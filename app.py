from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, math
from urllib.parse import quote_plus
from datetime import datetime, timedelta

# ✅ SMS TOOLS
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler

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

# ---------------------- ✅ TWILIO CONFIG (PASTE YOUR VALUES)
TWILIO_SID = "PASTE_SID"
TWILIO_AUTH = "PASTE_AUTH"
TWILIO_PHONE = "+1234567890"

client = Client(TWILIO_SID, TWILIO_AUTH)

# ---------------------- ✅ MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(15))  # ✅ MOBILE NUMBER
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

# ---------------------- ✅ ROUTES
@app.route("/")
def home():
    return render_template("base.html")

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
        hashed_pw = generate_password_hash(request.form["password"])
        user = User(
            username=request.form["username"],
            password=hashed_pw,
            phone=request.form["phone"]
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

@app.route("/add_pet", methods=["POST"])
def add_pet():
    if "user_id" not in session:
        return redirect(url_for("login"))

    pet = Pet(
        name=request.form["name"],
        species=request.form["species"],
        breed=request.form["breed"],
        age=request.form["age"],
        user_id=session["user_id"]
    )

    db.session.add(pet)
    db.session.commit()
    return redirect(url_for("dashboard"))

@app.route("/pet/<int:pet_id>")
def pet_profile(pet_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    pet = Pet.query.get_or_404(pet_id)
    vaccines = Vaccine.query.filter_by(pet_id=pet.id).all()

    return render_template(
        "pet_profile.html",
        pet=pet,
        vaccines=vaccines
    )

@app.route("/add_vaccine/<int:pet_id>", methods=["GET", "POST"])
def add_vaccine(pet_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    pet = Pet.query.get_or_404(pet_id)

    if request.method == "POST":
        new_vaccine = Vaccine(
            vaccine_name=request.form["vaccine_name"],
            last_given_date=datetime.strptime(request.form["last_given_date"], "%Y-%m-%d"),
            next_due_date=datetime.strptime(request.form["next_due_date"], "%Y-%m-%d"),
            pet_id=pet.id
        )

        db.session.add(new_vaccine)
        db.session.commit()

        flash("Vaccine added successfully!")
        return redirect(url_for("pet_profile", pet_id=pet.id))

    return render_template("add_vaccine.html", pet=pet)

# ---------------------- ✅ DOCTOR
@app.route("/doctor_finder")
def doctor_finder():
    return render_template("doctor_finder.html")

@app.route("/shop")
def shop():
    return render_template("shop.html")

@app.route("/clinics_within_20km")
def clinics_within_20km():
    user_lat = float(request.args.get("lat"))
    user_lon = float(request.args.get("lon"))

    count = 0
    for c in Clinic.query.all():
        if calculate_distance(user_lat, user_lon, c.latitude, c.longitude) <= 20:
            count += 1

    return {"clinics_within_20km": count}

# ---------------------- ✅ AUTO SMS REMINDER SYSTEM
def send_vaccine_reminders():
    today = datetime.today().date()
    reminder_day = today + timedelta(days=1)

    vaccines = Vaccine.query.filter_by(next_due_date=reminder_day).all()

    for vaccine in vaccines:
        pet = vaccine.pet
        owner = pet.owner

        message = f"""
Reminder!

Pet: {pet.name}
Vaccine: {vaccine.vaccine_name}
Due Date: {vaccine.next_due_date}
"""

        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=owner.phone
        )

scheduler = BackgroundScheduler()
scheduler.add_job(send_vaccine_reminders, 'interval', hours=24)
scheduler.start()

# ---------------------- ✅ RUN APP
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
