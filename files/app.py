from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "your-secret-key"

# Database Config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///petcare.db"  # fallback for testing
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    pets = db.relationship('Pet', backref='owner', lazy='dynamic')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
class Pet(db.Model):
    __tablename__ = "pets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    species = db.Column(db.String(80))
    breed = db.Column(db.String(120))
    age = db.Column(db.String(40))
    image_filename = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
# Routes
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
        flash("Invalid login credentials.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # save user logic
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")

@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

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

@app.route("/doctor_finder")
def doctor_finder():
    return render_template("doctor_finder.html")

@app.route("/shop")
def shop():
    return render_template("shop.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
