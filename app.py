from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from urllib.parse import quote_plus

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "your-secret-key"

# ----------------------
# Database Config
# ----------------------
db_password = quote_plus("admin@123")
db_user = "petuser"
db_host = "localhost"
db_port = "5432"
db_name = "smartpetdb"

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ----------------------
# Models
# ----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    pets = db.relationship("Pet", backref="owner", lazy=True)


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    species = db.Column(db.String(100))
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

# ----------------------
# Routes
# ----------------------
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
        user = User(username=request.form["username"], password=hashed_pw)
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


# ----------------------
# PET PROFILE ROUTE
# ----------------------
@app.route("/pet/<int:pet_id>")
def pet_profile(pet_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    pet = Pet.query.get_or_404(pet_id)

    # Breed information
    breed_info = {
        "Labrador": "Friendly and energetic. Needs exercise and proper grooming.",
        "German Shepherd": "Loyal, strong, and intelligent. Great for protection.",
        "Persian Cat": "Calm, gentle, and requires daily fur care.",
        "Siamese Cat": "Very vocal, social, and affectionate."
    }

    info = breed_info.get(
        pet.breed,
        "General Care: Provide regular food, grooming, health checkups, and affection."
    )

    return render_template("pet_profile.html", pet=pet, info=info)


@app.route("/doctor_finder")
def doctor_finder():
    return render_template("doctor_finder.html")


@app.route("/shop")
def shop():
    return render_template("shop.html")


# ----------------------
# Run App
# ----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
