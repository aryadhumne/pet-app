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
db_password = quote_plus("root@123")
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
<<<<<<< HEAD

    # Username must be unique + required
    username = db.Column(db.String(100), unique=True, nullable=False)

    # Password required
    password = db.Column(db.String(200), nullable=False)

    # Phone optional (nullable allowed)
    phone = db.Column(db.String(15), nullable=True)

    # Relationship with pets
=======
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(15))
>>>>>>> b9b17d9ee7b2f43ee8e379ae657ae42cdf85896f
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
<<<<<<< HEAD
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("login"))  # redirect to login page

=======
    return redirect(url_for("dashboard")) if "user_id" in session else render_template("base.html")
>>>>>>> b9b17d9ee7b2f43ee8e379ae657ae42cdf85896f

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        flash("Invalid login")
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
<<<<<<< HEAD
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Example: save to DB
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect("/login")

=======
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"]),
            phone=request.form.get("phone")
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created!")
        return redirect(url_for("login"))
>>>>>>> b9b17d9ee7b2f43ee8e379ae657ae42cdf85896f
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

<<<<<<< HEAD
@app.route('/agrishop')
def agrishop():
    return render_template('agrishop.html')

@app.route("/agripets")
def agripets():
    return render_template("agripets.html")


@app.route("/cow_breeds")
def cow_breeds():
    cow_list = [
        {
            "name": "Sahiwal","image": "sahiwalcow.jpeg",
        },
        {
            "name": "Holstein Friesian", "image": "Holstein Friesiancow.jpeg",
        },
        {
            "name": "Jersey", "image": "jerseycow.jpg"
        },
        {
            "name": "Rathi","image": "Rathicow.jpeg"
        }
    ]
    
    return render_template("cow_breeds.html", cow_list=cow_list)

@app.route("/buffalo_breeds")
def buffalo_breeds():
    buffalo_list = [
        {"name": "Murrah", "image": "murrahbuffalo.jpg"},
        {"name": "Jaffarabadi", "image": "jaffarabadi.jpeg"},
        {"name": "Surti", "image": "Surti.jpeg"},
        {"name": "Mehsana", "image": "Mehsana.jpeg"}
    ]
    return render_template("buffalo_breeds.html", buffalo_list=buffalo_list)


@app.route("/ox_breeds")
def ox_breeds():
    ox_list = [
        {"name": "Kangayam", "image": "Kangayam.jpeg"},
        {"name": "Khillari", "image": "khillari.jpeg"},
        {"name": "Ongole", "image": "Ongole.jpeg"},
        {"name": "Malvi", "image": "Malvi.jpeg"}
    ]
    return render_template("ox_breeds.html", ox_list=ox_list)
@app.route("/camel_breeds")
def camel_breeds():
    camel_list = [
        {"name": "Bikaneri", "image": "Bikaneri.jpeg"},
        {"name": "Jaisalmeri", "image": "jaisalmeri.jpeg"},
        {"name": "Kachchi", "image": "Kachchi.jpeg"}
        
    ]
    return render_template("camel_breeds.html", camel_list=camel_list)

@app.route("/horse_breeds")
def horse_breeds():
    horse_list = [
        {"name": "Marwari", "image": "marwari.jpeg"},
        {"name": "Kathiawari", "image": "kathiawari.jpeg"},
        {"name": "Indian Thoroughbred", "image": "thoroughbred.jpeg"}
    ]
    return render_template("horse_breeds.html", horse_list=horse_list)

@app.route("/donkey_breeds")
def donkey_breeds():
    donkey_list = [
        {"name": "Indian Wild Donkey", "image": "donkey1.jpeg"},
        {"name": "Ghudkhur", "image": "ghudkhur1.jpg"}
    ]
    return render_template("donkey_breeds.html", donkey_list=donkey_list)


@app.route("/sheep_breeds")
def sheep_breeds():
    sheep_list = [
        {"name": "Deccani", "image": "deccani.jpeg"},
        {"name": "Nali", "image": "nali.jpeg"},
        {"name": "Chokla", "image": "chokla.jpeg"}
    ]
    return render_template("sheep_breeds.html", sheep_list=sheep_list)

@app.route("/pig_breeds")
def pig_breeds():
    pig_list = [
        {"name": "Ghoongroo", "image": "ghoongroo.jpeg"},
        {"name": "Hampshire", "image": "hampshire.jpeg"}
    ]
    return render_template("pig_breeds.html", pig_list=pig_list)
@app.route("/chicken_breeds")
def chicken_breeds():
    chicken_list = [
        {"name": "Giriraja", "image": "giriraja.jpeg"},
        {"name": "Kadaknath", "image": "k1.jpeg"},
        {"name": "Aseel", "image": "a2.jpeg"}
    ]
    return render_template("chicken_breeds.html", chicken_list=chicken_list)

@app.route("/rooster_breeds")
def rooster_breeds():
    rooster_list = [
        {"name": "Aseel Rooster", "image": "aseel_rooster.jpeg"},
       {"name":"Giriraja","image": "giriraja_rooster.jpeg"}
    ]
    return render_template("rooster_breeds.html", rooster_list=rooster_list)


      
agripets_data = {
    "Buffalo": {
        "Murrah": {
            "image": "murrahbuffalo.jpg",
            "origin": "Haryana – Rohtak, Hisar",
            "reproductive_age": "30–36 months",
            "lifespan": "15–20 years",
            "breeding_cycle": "Estrus: 21 days, Heat: 12–18 hrs",
            "gestation_period": "310–315 days",
            "info": "World’s highest milk-yielding buffalo breed.",
            "common_diseases": "Mastitis, FMD",
            "climate": "Hot–humid",
            "suitable_for": "Commercial dairy farms"
        },
        "Jaffarabadi": {
            "image": "jaffarabadi.jpeg",
            "origin": "Saurashtra (Gujarat)",
            "reproductive_age": "36–42 months",
            "lifespan": "18–22 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "310–320 days",
            "info": "Largest Indian buffalo breed with heavy body.",
            "common_diseases": "Trypanosomiasis",
            "climate": "Dry & semi-humid",
            "suitable_for": "Medium dairy farms"
        },
        "Surti": {
            "image": "surti.jpeg",
            "origin": "Surat & Baroda (Gujarat)",
            "reproductive_age": "30–36 months",
            "lifespan": "12–18 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "310–315 days",
            "info": "Small-sized buffalo with high fat milk.",
            "common_diseases": "FMD",
            "climate": "Hot–dry",
            "suitable_for": "Home dairy"
        },
        "Mehsana": {
            "image": "mehsana.jpeg",
            "origin": "Mehsana district (Gujarat)",
            "reproductive_age": "30–36 months",
            "lifespan": "15–20 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "310–315 days",
            "info": "Cross of Murrah × Surti with good milk.",
            "common_diseases": "Foot rot",
            "climate": "Hot & semi-humid",
            "suitable_for": "Medium-scale dairy farms"
        }
    },
    "Cow": {
        "Sahiwal": {
            "image": "Sahiwalcow.jpeg",
            "origin": "Punjab (India–Pakistan border)",
            "reproductive_age": "30–36 months",
            "lifespan": "15–20 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "280–285 days",
            "info": "Sahiwal cows are known for high milk fat and heat tolerance.",
            "common_diseases": "Tick fever",
            "climate": "Hot & humid",
            "suitable_for": "Commercial dairy farms"
        },
        "Holstein Friesian": {
            "image": "Holstein Friesiancow.jpeg",
            "origin": "Netherlands",
            "reproductive_age": "15–18 months",
            "lifespan": "10–12 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "280 days",
            "info": "World's highest milk-producing breed.",
            "common_diseases": "Mastitis",
            "climate": "Cool–moderate",
            "suitable_for": "Large dairy farms"
        },
        "Jersey": {
            "image": "Jerseycow.jpg",
            "origin": "Jersey Island (UK)",
            "reproductive_age": "15–18 months",
            "lifespan": "12–15 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "278–280 days",
            "info": "Jersey cows give high-fat milk, ideal for ghee and butter.",
            "common_diseases": "Milk fever",
            "climate": "Moderate climate",
            "suitable_for": "Small & medium dairy farms"
        },
        "Rathi": {
            "image": "Rathicow.jpeg",
            "origin": "Rajasthan",
            "reproductive_age": "30–36 months",
            "lifespan": "12–15 years",
            "breeding_cycle": "Estrus: 21 days",
            "gestation_period": "280–285 days",
            "info": "Rathi cows are hardy and drought-tolerant with good milk yield.",
            "common_diseases": "FMD",
            "climate": "Hot–dry regions",
            "suitable_for": "Desert & dry areas"
        }
    },
    "Ox": {
        "Kangayam": {
    "image": "Kangayam.jpeg",
    "origin": "Tamil Nadu – Kangayam region",
    "reproductive_age": "30–36 months",
    "lifespan": "15–18 years",
    "breeding_cycle": "Estrus: 21 days",
    "gestation_period": "280–285 days",
    "info": "Well-known draught ox breed, strong and hardy.",
    "common_diseases": "Foot rot, tick infestations",
    "climate": "Hot–dry",
    "suitable_for": "Ploughing, draught work"
},
 
 "Khillari": {
    "image": "khillari.jpeg",
    "origin": "Maharashtra & Karnataka, India",
    "reproductive_age": "3–4 years",
    "lifespan": "15–18 years",
    "breeding_cycle": "Estrus: 21 days",
    "gestation_period": "280–285 days",
    "info": "Khillari oxen are strong draught animals, known for plowing fields and pulling carts.",
    "common_diseases": "Foot-and-mouth disease, bloat",
    "climate": "Tropical to semi-arid regions",
    "suitable_for": "Agricultural work, heavy draft purposes"
},
"Ongole": {
    "image": "Ongole.jpeg",
    "origin": "Andhra Pradesh, India",
    "reproductive_age": "3–4 years",
    "lifespan": "15–20 years",
    "breeding_cycle": "Estrus: 21 days",
    "gestation_period": "280–285 days",
    "info": "Ongole oxen are large, strong draught animals, also used in crossbreeding for improving cattle breeds.",
    "common_diseases": "FMD (Foot-and-mouth disease), mastitis",
    "climate": "Tropical and semi-arid regions",
    "suitable_for": "Agricultural work, plowing, and heavy draft purposes"
},
"Malvi": {
    "image": "Malvi.jpeg",
    "origin": "Madhya Pradesh, India",
    "reproductive_age": "3–4 years",
    "lifespan": "15–18 years",
    "breeding_cycle": "Estrus: 21 days",
    "gestation_period": "280–285 days",
    "info": "Malvi oxen are hardy draught animals, well-suited for plowing and other agricultural activities in semi-arid regions.",
    "common_diseases": "Tick-borne diseases, bloat",
    "climate": "Tropical and semi-arid regions",
    "suitable_for": "Agricultural work, medium to heavy draft purposes"
}
},
    "Camel": {
    "Bikaneri": {
        "image": "Bikaneri.jpeg",
        "origin": "Bikaner, Rajasthan, India",
        "reproductive_age": "3–4 years",
        "lifespan": "40–50 years",
        "breeding_cycle": "Estrus: 21–24 days",
        "gestation_period": "12–13 months",
        "info": "Bikaneri camels are strong and hardy, mainly used for transport, milk, and agricultural work in desert regions.",
        "common_diseases": "Trypanosomiasis, tick infestations",
        "climate": "Arid desert regions",
        "suitable_for": "Transport, milk production, desert agriculture"
    },
    "Jaisalmeri": {
        "image": "Jaisalmeri.jpeg",
        "origin": "Jaisalmer, Rajasthan, India",
        "reproductive_age": "3–4 years",
        "lifespan": "40–50 years",
        "breeding_cycle": "Estrus: 21–24 days",
        "gestation_period": "12–13 months",
        "info": "Jaisalmeri camels are prized for their endurance, speed, and milk yield; often used in races and long desert journeys.",
        "common_diseases": "Tick-borne diseases, bloat",
        "climate": "Arid desert regions",
        "suitable_for": "Racing, transport, milk production"
    },
    "Kachchi": {
        "image": "Kachchi.jpeg",
        "origin": "Kutch region, Gujarat, India",
        "reproductive_age": "3–4 years",
        "lifespan": "40–50 years",
        "breeding_cycle": "Estrus: 21–24 days",
        "gestation_period": "12–13 months",
        "info": "Kachchi camels are strong draught animals, used for carrying loads, plowing, and milk production in harsh climates.",
        "common_diseases": "Tick infestations, respiratory infections",
        "climate": "Semi-arid to arid regions",
        "suitable_for": "Agriculture, transport, milk production"
    }
},

"Horse": {
    "Marwari": {
        "image": "marwari.jpeg",
        "origin": "Rajasthan, India",
        "reproductive_age": "3–4 years",
        "lifespan": "25–30 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "11 months",
        "info": "Marwari horses are known for their inward-curving ears, endurance, and agility. They are often used in ceremonial events and light cavalry.",
        "common_diseases": "Colic, laminitis",
        "climate": "Arid and semi-arid regions",
        "suitable_for": "Riding, ceremonial use, endurance riding"
    },
    "Kathiawari": {
        "image": "kathiawari.jpeg",
        "origin": "Gujarat, India",
        "reproductive_age": "3–4 years",
        "lifespan": "25–30 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "11 months",
        "info": "Kathiawari horses are hardy, drought-resistant, and used for riding and light draft work. They have a characteristic concave profile and strong legs.",
        "common_diseases": "Colic, equine influenza",
        "climate": "Semi-arid regions",
        "suitable_for": "Riding, light draft work, endurance"
    },
    "Indian Thoroughbred": {
        "image": "thoroughbred.jpeg",
        "origin": "Imported and bred in India",
        "reproductive_age": "3–4 years",
        "lifespan": "25–30 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "11 months",
        "info": "Indian Thoroughbreds are primarily bred for racing and competitive sports. They are fast, athletic, and have a sleek build.",
        "common_diseases": "Laminitis, respiratory infections",
        "climate": "Moderate climate",
        "suitable_for": "Racing, sports, show jumping"
    }
},

   "Donkey": {
    "Indian Wild Donkey": {
        "image": "donkey1.jpeg",
        "origin": "Rajasthan, Gujarat, India",
        "reproductive_age": "2–3 years",
        "lifespan": "20–25 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "11–12 months",
        "info": "Indian Wild Donkeys are hardy and drought-resistant. They are mainly used for light transport in desert and semi-arid regions.",
        "common_diseases": "Hoof infections, parasitic infestations",
        "climate": "Arid and semi-arid regions",
        "suitable_for": "Light transport, agricultural work"
    },
    "Ghudkhur": {
        "image": "ghudkhur1.jpg",
        "origin": "India (general domestic breed)",
        "reproductive_age": "2–3 years",
        "lifespan": "20–25 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "11–12 months",
        "info": "Ghudkhur donkeys are domesticated donkeys used for carrying loads, carts, and light agricultural tasks. They are known for endurance and adaptability.",
        "common_diseases": "Hoof problems, colic",
        "climate": "Tropical to semi-arid regions",
        "suitable_for": "Transport, farming, pack animal"
    }
},

   "Sheep": {
    "Deccani": {
        "image": "deccani.jpeg",
        "origin": "Deccan Plateau, India",
        "reproductive_age": "8–12 months",
        "lifespan": "10–12 years",
        "breeding_cycle": "Estrus: 17–20 days",
        "gestation_period": "145–150 days",
        "info": "Deccani sheep are hardy, drought-tolerant, and raised for meat, coarse wool, and milk in semi-arid regions.",
        "common_diseases": "Peste des petits ruminants (PPR), foot rot",
        "climate": "Semi-arid to arid regions",
        "suitable_for": "Meat, coarse wool, and milk production"
    },
    "Nali": {
        "image": "nali.jpeg",
        "origin": "Rajasthan, India",
        "reproductive_age": "8–12 months",
        "lifespan": "10–12 years",
        "breeding_cycle": "Estrus: 17–20 days",
        "gestation_period": "145–150 days",
        "info": "Nali sheep are primarily raised for high-quality mutton. They are medium-sized and well-adapted to arid regions.",
        "common_diseases": "PPR, sheep pox",
        "climate": "Arid and semi-arid regions",
        "suitable_for": "Meat production"
    },
    "Chokla": {
        "image": "chokla.jpeg",
        "origin": "Rajasthan, India",
        "reproductive_age": "8–12 months",
        "lifespan": "10–12 years",
        "breeding_cycle": "Estrus: 17–20 days",
        "gestation_period": "145–150 days",
        "info": "Chokla sheep are known for their fine carpet-quality wool. They are medium-sized and thrive in arid climates.",
        "common_diseases": "PPR, foot rot",
        "climate": "Arid and semi-arid regions",
        "suitable_for": "Wool and meat production"
    }
},

  "Pig": {
    "Ghoongroo": {
        "image": "ghoongroo.jpeg",
        "origin": "India (local breed, mainly North India)",
        "reproductive_age": "6–8 months",
        "lifespan": "10–12 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "114 days",
        "info": "Ghoongroo pigs are hardy, medium-sized, and raised for meat. They adapt well to local climates and small-scale farming.",
        "common_diseases": "Swine fever, parasites",
        "climate": "Tropical and subtropical regions",
        "suitable_for": "Meat production, small-scale farming"
    },
    "Hampshire": {
        "image": "hampshire.jpeg",
        "origin": "United States (bred in India)",
        "reproductive_age": "6–8 months",
        "lifespan": "10–12 years",
        "breeding_cycle": "Estrus: 21 days",
        "gestation_period": "114 days",
        "info": "Hampshire pigs are large, fast-growing, and known for lean meat. They are popular in commercial pig farming.",
        "common_diseases": "Swine fever, respiratory infections",
        "climate": "Moderate climates",
        "suitable_for": "Commercial meat production"
    }
},

    "Chicken": {
    "Giriraja": {
        "image": "giriraja.jpeg",
        "origin": "Karnataka, India",
        "reproductive_age": "5–6 months",
        "lifespan": "6–8 years",
        "breeding_cycle": "Egg-laying: daily",
        "gestation_period": "21 days (incubation period)",
        "info": "Giriraja chickens are dual-purpose, good for both meat and eggs. They are hardy and adapt well to free-range farming.",
        "common_diseases": "Newcastle disease, coccidiosis",
        "climate": "Tropical and subtropical regions",
        "suitable_for": "Egg production, meat, backyard farming"
    },
    "Kadaknath": {
        "image": "k1.jpeg",
        "origin": "Madhya Pradesh, India",
        "reproductive_age": "5–6 months",
        "lifespan": "6–8 years",
        "breeding_cycle": "Egg-laying: daily",
        "gestation_period": "21 days (incubation period)",
        "info": "Kadaknath chickens are famous for black meat, high protein content, and disease resistance. Suitable for both backyard and commercial farming.",
        "common_diseases": "Newcastle disease, parasites",
        "climate": "Tropical and subtropical regions",
        "suitable_for": "Meat, egg production, backyard farming"
    },
    "Aseel": {
        "image": "a2.jpeg",
        "origin": "India (crossbred variety)",
        "reproductive_age": "5–6 months",
        "lifespan": "6–8 years",
        "breeding_cycle": "Egg-laying: daily",
        "gestation_period": "21 days (incubation period)",
        "info": "Aseen chickens are hardy and fast-growing, primarily raised for meat and moderate egg production.",
        "common_diseases": "Newcastle disease, coccidiosis",
        "climate": "Tropical and subtropical regions",
        "suitable_for": "Meat and backyard egg production"
    }
},

   "Rooster": {
    "Aseel Rooster": {
        "image": "aseel_rooster.jpeg",
        "origin": "Punjab, India",
        "reproductive_age": "5–6 months",
        "lifespan": "6–8 years",
        "breeding_cycle": "Daily mating possible",
        "gestation_period": "21 days (incubation for eggs)",
        "info": "Aseel roosters are muscular, hardy, and known for their aggressive behavior. Often used for breeding and cockfighting in traditional settings.",
        "common_diseases": "Newcastle disease, parasites",
        "climate": "Tropical and subtropical regions",
        "suitable_for": "Breeding, backyard farming, cockfighting (traditional)"
    },

    "Giriraja": {
    "image": "giriraja_rooster.jpeg",
    "origin": "India (Developed in Karnataka, Andhra Pradesh, and Tamil Nadu)",
    "reproductive_age": "5–6 months",
    "lifespan": "5–7 years",
    "breeding_cycle": "Year-round under proper management",
    "gestation_period": "Not applicable (fertilizes eggs; incubation ~21 days for chicks)",
    "info": "Giriraja roosters are dual-purpose males used for breeding and meat. They are hardy, have strong mating ability, and are active foragers. Known for good fertility rates in backyard and semi-intensive systems.",
    "common_diseases": "Newcastle Disease, Fowl Pox, Marek's Disease (preventable with vaccination and hygiene)",
    "climate": "Tropical and subtropical climates; tolerates heat and humidity well",
    "suitable_for": "Backyard breeding, small-scale poultry farms, free-range and semi-intensive systems"
}

}

    
}




# ===== AGRI BREED DETAIL ROUTES =====

# Cow
@app.route("/agribreed_details/cow/<name>")
def cow_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Cow"].get(name)
    if not info:
        return f"Cow breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Buffalo
@app.route("/agribreed_details/buffalo/<name>")
def buffalo_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Buffalo"].get(name)
    if not info:
        return f"Buffalo breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Ox
@app.route("/agribreed_details/ox/<name>")
def ox_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Ox"].get(name)
    if not info:
        return f"Ox breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Camel
@app.route("/agribreed_details/camel/<name>")
def camel_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Camel"].get(name)
    if not info:
        return f"Camel breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Horse
@app.route("/agribreed_details/horse/<name>")
def horse_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Horse"].get(name)
    if not info:
        return f"Horse breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Donkey
@app.route("/agribreed_details/donkey/<name>")
def donkey_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Donkey"].get(name)
    if not info:
        return f"Donkey breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Sheep
@app.route("/agribreed_details/sheep/<name>")
def sheep_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Sheep"].get(name)
    if not info:
        return f"Sheep breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Pig
@app.route("/agribreed_details/pig/<name>")
def pig_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Pig"].get(name)
    if not info:
        return f"Pig breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Chicken
@app.route("/agribreed_details/chicken/<name>")
def chicken_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Chicken"].get(name)
    if not info:
        return f"Chicken breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)

# Rooster
@app.route("/agribreed_details/rooster/<name>")
def rooster_details(name):
    name = name.replace("-", " ")
    info = agripets_data["Rooster"].get(name)
    if not info:
        return f"Rooster breed '{name}' not found", 404
    return render_template("agribreed_details.html", info=info, breed_name=name)



=======
>>>>>>> b9b17d9ee7b2f43ee8e379ae657ae42cdf85896f
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

<<<<<<< HEAD




=======
>>>>>>> b9b17d9ee7b2f43ee8e379ae657ae42cdf85896f
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