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

@app.route('/upload_pet_image/<int:pet_id>', methods=['POST'])
def upload_pet_image(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    file = request.files['image']

    if file:
        filename = file.filename
        file.save(os.path.join('static/uploads', filename))
        pet.image = filename
        db.session.commit()

    return redirect(url_for('home'))

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

    photo = db.Column(db.String(200))   # ✅ ADD THIS

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

# ---------------------- ✅ STATIC PET BROWSING DATA
# ---------------------- ✅ PET BROWSING DATA (ALL PETS ADDED)
pets_data = {

# ✅ ================== DOG BREEDS ==================
"Dog": {

    "Husky": {
        "image": "husky.webp",
        "origin": "Siberia",
        "lifespan": "12–15 years",
        "temperament": "Energetic, Friendly, Intelligent",
        "info": "Huskies are strong working dogs used for pulling sleds in cold climates. They require heavy exercise and love outdoor activity.",
        "habitat": "Cold regions like Siberia and Alaska",
        "diet": "High-protein food, meat, fish, rice",
        "exercise": "Very high – daily running required",
        "grooming": "Heavy shedding – frequent brushing",
        "common_diseases": "Hip Dysplasia, Eye Disorders",
        "climate": "Cold climate only",
        "suitable_for": "Active owners, farmhouses"
    },

    "Labrador": {
        "image": "lab.jpeg",
        "origin": "Canada",
        "lifespan": "10–14 years",
        "temperament": "Friendly, Loyal, Intelligent",
        "info": "Labradors are friendly, loyal, and intelligent family dogs. They are widely used as guide dogs and rescue dogs.",
        "habitat": "Homes, farms, training centers",
        "diet": "Chicken, rice, dog food, vegetables",
        "exercise": "High",
        "grooming": "Low maintenance",
        "common_diseases": "Obesity, Ear Infection, Hip Dysplasia",
        "climate": "All climates",
        "suitable_for": "Families, beginners"
    },

    "Golden Retriever": {
        "image": "golden.jpeg",
        "origin": "Scotland",
        "lifespan": "10–13 years",
        "temperament": "Gentle, Intelligent, Loyal",
        "info": "Golden Retrievers are gentle, intelligent, and great companion dogs. They are widely used as therapy and service dogs.",
        "habitat": "Homes, farms",
        "diet": "Protein-rich food, boiled chicken",
        "exercise": "High",
        "grooming": "Moderate grooming",
        "common_diseases": "Cancer, Hip Dysplasia",
        "climate": "Moderate climate",
        "suitable_for": "Families, children"
    },

    "German Shepherd": {
        "image": "german.jpg",
        "origin": "Germany",
        "lifespan": "9–13 years",
        "temperament": "Brave, Protective, Intelligent",
        "info": "German Shepherds are brave, smart, and widely used as police and guard dogs.",
        "habitat": "Homes, security areas",
        "diet": "High-protein food, eggs, vegetables",
        "exercise": "Very high",
        "grooming": "Moderate brushing",
        "common_diseases": "Hip Dysplasia, Bloat",
        "climate": "All climates",
        "suitable_for": "Security, families"
    },

    "Pug": {
        "image": "pug.png",
        "origin": "China",
        "lifespan": "12–15 years",
        "temperament": "Playful, Loving, Calm",
        "info": "Pugs are small, loving indoor dogs with playful nature.",
        "habitat": "Indoor homes",
        "diet": "Soft dog food, boiled chicken",
        "exercise": "Low to moderate",
        "grooming": "Low grooming",
        "common_diseases": "Breathing Problems, Obesity",
        "climate": "Moderate climate",
        "suitable_for": "Apartments, elderly people"
    },

    "Beagle": {
        "image": "beagle.webp",
        "origin": "England",
        "lifespan": "12–15 years",
        "temperament": "Friendly, Curious, Energetic",
        "info": "Beagles are active hunting dogs with a friendly personality.",
        "habitat": "Homes, outdoor areas",
        "diet": "Dog food, vegetables, boiled meat",
        "exercise": "High",
        "grooming": "Low",
        "common_diseases": "Epilepsy, Obesity",
        "climate": "All climates",
        "suitable_for": "Families with kids"
    },

    "Rottweiler": {
        "image": "rott.jpg",
        "origin": "Germany",
        "lifespan": "8–12 years",
        "temperament": "Protective, Loyal, Confident",
        "info": "Rottweilers are powerful guard dogs known for loyalty and protection.",
        "habitat": "Homes, farms",
        "diet": "Protein-rich food",
        "exercise": "High",
        "grooming": "Low",
        "common_diseases": "Heart disease, Hip Dysplasia",
        "climate": "Moderate climate",
        "suitable_for": "Security owners"
    },

    "Doberman": {
        "image": "doberman.webp",
        "origin": "Germany",
        "lifespan": "10–13 years",
        "temperament": "Alert, Fearless, Loyal",
        "info": "Dobermans are fast, alert, and excellent security dogs.",
        "habitat": "Security areas, homes",
        "diet": "Meat, dog food",
        "exercise": "Very high",
        "grooming": "Low",
        "common_diseases": "Heart disease",
        "climate": "Moderate climate",
        "suitable_for": "Security, guarding"
    },

    "Pomeranian": {
        "image": "Pomeranian.webp",
        "origin": "Germany",
        "lifespan": "12–16 years",
        "temperament": "Playful, Alert, Intelligent",
        "info": "Pomeranians are small fluffy dogs with high energy and cuteness.",
        "habitat": "Indoor homes",
        "diet": "Small dog feed, chicken",
        "exercise": "Moderate",
        "grooming": "Daily brushing",
        "common_diseases": "Dental issues, hair loss",
        "climate": "Cold & moderate climate",
        "suitable_for": "Apartments"
    },

    "Rajapalayam": {
        "image": "Rajapalayam.png",
        "origin": "India",
        "lifespan": "10–12 years",
        "temperament": "Loyal, Aggressive toward strangers",
        "info": "Rajapalayam is an Indian guard dog breed known for loyalty and bravery.",
        "habitat": "South Indian farms and homes",
        "diet": "Meat-based diet",
        "exercise": "High",
        "grooming": "Low grooming",
        "common_diseases": "Skin problems, deafness",
        "climate": "Hot climate",
        "suitable_for": "Farm security"
    }
},

# ✅ ================== CAT BREEDS ==================
"Cat": {

    "Persian": {
        "image": "persian.jpg",
        "lifespan": "12–17 years",
        "temperament": "Calm, Affectionate",
        "info": "Persian cats are calm, fluffy, and indoor-friendly pets.",
        "habitat": "Indoor homes",
        "diet": "Fish, cat food",
        "grooming": "Daily grooming",
        "common_diseases": "Breathing problems",
        "suitable_for": "Apartments"
    },

    "Siamese": {
        "image": "siamese.jpg",
        "lifespan": "12–15 years",
        "temperament": "Vocal, Social",
        "info": "Siamese cats are vocal, social, and intelligent.",
        "habitat": "Indoor homes",
        "diet": "Fish, cat food",
        "grooming": "Low",
        "common_diseases": "Eye problems",
        "suitable_for": "Families"
    },

    "Maine Coon": {
        "image": "maine.jpg",
        "lifespan": "12–15 years",
        "temperament": "Friendly, Gentle",
        "info": "Maine Coons are large, friendly cats known as gentle giants.",
        "habitat": "Homes, cold areas",
        "diet": "Protein-rich food",
        "grooming": "Moderate",
        "common_diseases": "Heart disease",
        "suitable_for": "Large homes"
    },

    "Bengal": {
        "image": "bengal.webp",
        "lifespan": "12–16 years",
        "temperament": "Energetic, Playful",
        "info": "Bengal cats have wild leopard-like appearance and high energy.",
        "habitat": "Indoor homes",
        "diet": "Protein-rich diet",
        "grooming": "Low",
        "common_diseases": "Heart disease",
        "suitable_for": "Active owners"
    },

    "British Shorthair": {
        "image": "british.jpg",
        "lifespan": "12–15 years",
        "temperament": "Calm, Affectionate",
        "info": "British Shorthair cats are calm, thick-coated, and affectionate.",
        "habitat": "Indoor homes",
        "diet": "Cat food, boiled fish",
        "grooming": "Low",
        "common_diseases": "Obesity",
        "suitable_for": "Families"
    }
},

# ✅ ================== BIRD BREEDS ==================
"Birds": {

    "Parrot": {
        "image": "parrot.jpg",
        "lifespan": "40–80 years",
        "temperament": "Intelligent, Talkative",
        "info": "Parrots are colorful talking birds with high intelligence.",
        "habitat": "Cages, forest areas",
        "diet": "Fruits, seeds, nuts",
        "common_diseases": "Psittacosis",
        "suitable_for": "Experienced owners"
    },

    "Cockatiel": {
        "image": "cockatiels.jpeg",
        "lifespan": "15–25 years",
        "temperament": "Friendly, Calm",
        "info": "Cockatiels are friendly pet birds with head crests.",
        "habitat": "Cages, indoor homes",
        "diet": "Seeds, grains",
        "common_diseases": "Respiratory issues",
        "suitable_for": "Beginners"
    },

    "Budgerigar": {
        "image": "budgie.jpg",
        "lifespan": "7–10 years",
        "temperament": "Playful, Social",
        "info": "Budgies are small, social, and easy-to-care pet birds.",
        "habitat": "Cages, indoor homes",
        "diet": "Seeds, fruits",
        "common_diseases": "Cold, infections",
        "suitable_for": "Children, beginners"
    },

    "Love Birds": {
        "image": "lovebirds.jpg",
        "lifespan": "10–15 years",
        "temperament": "Affectionate, Active",
        "info": "Love birds live in pairs and show strong bonding.",
        "habitat": "Cages, forest regions",
        "diet": "Seeds, fruits",
        "common_diseases": "Feather loss",
        "suitable_for": "Couples"
    },

    "Pigeon": {
        "image": "pigeon.jpg",
        "lifespan": "8–15 years",
        "temperament": "Calm, Intelligent",
        "info": "Pigeons are intelligent birds used for message delivery earlier.",
        "habitat": "Urban buildings, open areas",
        "diet": "Grains, seeds",
        "common_diseases": "Respiratory infection",
        "suitable_for": "Outdoor keepers"
    }
},
# ✅ ================== OTHER PET BREEDS ==================
"Rabbit": {
    "Netherland Dwarf": {
        "image": "netherland_dwarf.avif",
        "lifespan": "7–10 years",
        "temperament": "Playful, Gentle",
        "info": "Small and cute, Netherland Dwarfs are great indoor rabbits.",
        "habitat": "Indoor cages, small enclosures",
        "diet": "Hay, vegetables, rabbit pellets",
        "exercise": "Daily playtime outside cage",
        "grooming": "Weekly brushing",
        "common_diseases": "Dental issues, Obesity",
        "suitable_for": "Apartments, beginners"
    },
    "Flemish Giant": {
        "image": "Flemish.webp",
        "lifespan": "8–12 years",
        "temperament": "Gentle, Friendly",
        "info": "One of the largest rabbit breeds, very gentle with families.",
        "habitat": "Large cages or outdoor hutches",
        "diet": "Hay, vegetables, pellets",
        "exercise": "High – needs space to run",
        "grooming": "Moderate brushing",
        "common_diseases": "Obesity, Arthritis",
        "suitable_for": "Families, large homes"
    }
},

"Hamster": {
    "Syrian": {
        "image": "hamster.webp",
        "lifespan": "2–3 years",
        "temperament": "Friendly, Curious",
        "info": "Syrian hamsters are solitary pets, easy to handle and popular as starters.",
        "habitat": "Cages with tunnels and wheel",
        "diet": "Hamster pellets, seeds, occasional fruits",
        "exercise": "High – running wheel required",
        "grooming": "Self-grooming",
        "common_diseases": "Wet tail, Respiratory infection",
        "suitable_for": "Children (supervised), beginners"
    },
    "Dwarf": {
        "image": "drwaf.jpg",
        "lifespan": "1.5–2 years",
        "temperament": "Active, Fast",
        "info": "Dwarf hamsters are small, fast, and social with same-species hamsters.",
        "habitat": "Cages with tunnels, wheel",
        "diet": "Seeds, pellets, vegetables",
        "exercise": "High",
        "grooming": "Self-grooming",
        "common_diseases": "Respiratory infection, Obesity",
        "suitable_for": "Experienced kids, hobbyists"
    }
},

"Fish": {
    "Goldfish": {
        "image": "goldfish.jpg",
        "lifespan": "10–15 years",
        "temperament": "Calm",
        "info": "Popular freshwater fish, easy to keep in tanks or ponds.",
        "habitat": "Freshwater aquariums or ponds",
        "diet": "Flakes, pellets, vegetables",
        "exercise": "N/A",
        "grooming": "N/A",
        "common_diseases": "Swim bladder disorder, Ich",
        "suitable_for": "Beginners, home aquariums"
    },
    "Betta": {
        "image": "Betta_fish.webp",
        "lifespan": "3–5 years",
        "temperament": "Aggressive (males), colorful",
        "info": "Betta fish are small, colorful, and require separate tanks for males.",
        "habitat": "Freshwater aquariums",
        "diet": "Pellets, live or frozen food",
        "exercise": "N/A",
        "grooming": "N/A",
        "common_diseases": "Fin rot, Swim bladder",
        "suitable_for": "Beginners, small tanks"
    }
},

"Turtle": {
    "Red-Eared Slider": {
        "image": "red-eared.jpeg",
        "lifespan": "20–30 years",
        "temperament": "Friendly, Calm",
        "info": "Red-Eared Sliders are aquatic turtles that enjoy swimming and basking.",
        "habitat": "Aquatic tanks with basking area",
        "diet": "Turtle pellets, vegetables, occasional protein",
        "exercise": "Swimming",
        "grooming": "Clean tank, shell maintenance",
        "common_diseases": "Shell rot, Respiratory infections",
        "suitable_for": "Experienced pet owners"
    },
    "Box Turtle": {
        "image": "box.jpeg",
        "lifespan": "30–50 years",
        "temperament": "Shy, Slow-moving",
        "info": "Box turtles are terrestrial, with domed shells and long lifespans.",
        "habitat": "Outdoor enclosures or terrariums",
        "diet": "Vegetables, fruits, insects",
        "exercise": "Moderate roaming",
        "grooming": "Occasional shell cleaning",
        "common_diseases": "Respiratory infection, Vitamin deficiencies",
        "suitable_for": "Hobbyists, responsible owners"
    }
}


}



# ---------------------- ✅ DISTANCE FUNCTION
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@app.route("/upload_pet_photo/<int:pet_id>", methods=["POST"])
def upload_pet_photo(pet_id):
    file = request.files["photo"]
    filename = f"pet_{pet_id}.jpg"
    file.save(f"static/uploads/{filename}")

    pet = Pet.query.get(pet_id)
    pet.photo = filename
    db.session.commit()

    return redirect(url_for("pet_profile", pet_id=pet_id))

# ---------------------- ✅ AUTH ROUTES
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

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

# ---------------------- ✅ USER PET MANAGEMENT (UNCHANGED)
@app.route("/add_pet", methods=["POST"])
def add_pet():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    name = request.form.get("name")
    species = request.form.get("species")
    breed = request.form.get("breed")
    age_raw = request.form.get("age")

    # ✅ SAFE AGE HANDLING
    age = int(age_raw) if age_raw and age_raw.isdigit() else None

    pet = Pet(
        name=name,
        species=species,
        breed=breed,
        age=age,
        user_id=user.id
    )

    db.session.add(pet)
    db.session.commit()

    flash("Pet added successfully!", "success")

    return redirect(url_for("dashboard"))

@app.route('/delete_pet/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    if pet.photo:
        image_path = os.path.join(app.root_path, 'static/uploads', pet.photo)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(pet)
    db.session.commit()

    flash("Pet deleted successfully!", "success")
    return redirect(url_for('dashboard'))


# ---------------------- ✅ PET PROFILE
@app.route("/pet/<int:pet_id>")
def pet_profile(pet_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    pet = Pet.query.get_or_404(pet_id)
    vaccines = Vaccine.query.filter_by(pet_id=pet.id).all()

    return render_template("pet_profile.html", pet=pet, vaccines=vaccines)

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

# ---------------------- ✅ GENERAL PAGES
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

# ---------------------- ✅ PET BROWSING SYSTEM (NEW)
@app.route("/pet_section")
def pet_section():
    return render_template("pet_home.html")

@app.route("/petshop")
def petshop():
    return render_template("pet_shop.html")

@app.route("/pets")
def pets_list():
    return render_template("pets_list.html", pets=pets_data.keys())

@app.route("/pets/<pet>")
def breed_list(pet):
    breeds = pets_data.get(pet, {})
    return render_template("pet_breeds.html", pet=pet, breeds=breeds)

@app.route("/pets/<pet>/<breed>")
def breed_info(pet, breed):
    info = pets_data.get(pet, {}).get(breed)
    return render_template("breed_info.html", pet=pet, breed=breed, info=info)

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
