from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, math
from urllib.parse import quote_plus
from datetime import datetime, timedelta, date
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask import Blueprint, request, redirect, url_for, flash
from files.models import db, User,Pet,DietPlan


load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
from chatbot_api import chatbot_bp

app.register_blueprint(chatbot_bp)




app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ---------------------- DATABASE


app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres.yctdbnvldajettbhsdyu:2097199552542884@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------------- DATABASE CONFIG FROM ENV
db_user = os.getenv("SUPABASE_DB_USER")
db_password_raw = os.getenv("SUPABASE_DB_PASSWORD")
db_host = os.getenv("SUPABASE_DB_HOST")
db_port = os.getenv("SUPABASE_DB_PORT", "6543")
db_name = os.getenv("SUPABASE_DB_NAME", "postgres")

if not db_password_raw:
    raise RuntimeError("SUPABASE_DB_PASSWORD not set in .env")

db_password = quote_plus(db_password_raw)

db.init_app(app)
migrate = Migrate(app, db)

# ---------------------- SMSFAST2SMS_API_KEY = "PASTE_YOUR_FAST2SMS_API_KEY_HERE"
def send_sms(phone, message):
    try:
        requests.post(
            "https://www.fast2sms.com/dev/bulkV2",
            json={"route": "q", "message": message, "language": "english", "numbers": phone},
            headers={"authorization": FAST2SMS_API_KEY, "Content-Type": "application/json"}
        )
    except Exception as e:
        print("SMS Failed:", e)
# ====================== MODELS ======================



class PetProfile(db.Model):
    __tablename__ = "pet"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    species = db.Column(db.String(50))
    breed = db.Column(db.String(50))
    age = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    photo = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class PetTimeline(db.Model):
    __tablename__ = "pet_timeline"

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)

    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50))
    date = db.Column(db.Date)

    # relationship to PetProfile (table: pet)
    pet = db.relationship("PetProfile", backref="timeline_events")

class Vaccine(db.Model):
    __tablename__ = "vaccine"

    id = db.Column(db.Integer, primary_key=True)
    vaccine_name = db.Column(db.String(120), nullable=False)
    last_given_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)

    # Correct foreign key reference
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    pet = db.relationship('Pet', backref='vaccines')  # Use the class name 'Pet'
class Clinic(db.Model):
    __tablename__ = "clinic"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
class HealthCheckup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pet.id"))
    date = db.Column(db.Date)
    weight = db.Column(db.Float)
    temperature = db.Column(db.Float)
    notes = db.Column(db.String(255))
    next_checkup = db.Column(db.Date)   # ✅ ADD THIS

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
#AGRI PETS DETAILS
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
            "image": "jaffarabadi.jpg",
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
            "image": "Surti.jpg",
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
            "image": "Mehsana.jpg",
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
        "Sahiwacow": {
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
            "image": "Holstein_Friesiancow.jpeg",
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
            "image": "Rathicow.jpg",
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
    "image": "Kangayam.jpg",
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
    "image": "khillari.jpg",
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
    "image": "Ongole.jpg",
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
    "image": "Malvi.jpg",
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
        "image": "Bikaneri.jpg",
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
        "image": "Jalsalmeri.jpg",
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
        "image": "Kalchchi.jpg",
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
        "image": "marwari.jpg",
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
        "image": "kathiawari.jpg",
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
        "image": "thoroughbred.jpg",
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
        "image": "donkey1.jpg",
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
        "image": "nali.jpg",
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
        "image": "chokla.jpg",
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
        "image": "ghoongroo.jpg",
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
        "image": "hampshire.jpg",
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
        "image": "giriraja.jpg",
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
        "image": "K1.jpg",
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
        "image": "a2.jpg",
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
        "image": "aseel_rooster.jpg",
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
    "image": "giriraj_rooster.jpg",
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
# ---------------------- UTILITIES
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
# ---------------------- ROUTES
@app.route("/")
def welcome():
    return render_template("welcome.html")
@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Please enter username and password", "danger")
            return redirect(url_for("login"))

        user = User.query.filter_by(username=username).first()

        # ✅ FIXED LINE HERE
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")
@app.route("/test-db")
def test_db():
    from models import User, db

    user = User(username="admin")
    user.set_password("admin123")

    db.session.add(user)
    db.session.commit()

    return "User added successfully!"
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmpassword")
        email = request.form.get("email")

        print("DEBUG REGISTER DATA:", username, email)

        # Basic validation
        if not username or not password or not email:
            flash("All fields are required", "danger")
            return redirect(url_for("register"))

        # Confirm password check
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Try another.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        try:
            hashed_password = generate_password_hash(password)

            user = User(
                username=username,
                email=email,
                password_hash=hashed_password
            )

            db.session.add(user)
            db.session.commit()

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

        except IntegrityError as e:
            db.session.rollback()
            print("DB ERROR:", e)
            flash("Registration failed. Try again.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirmpassword")

        if not email or not new_password or not confirm_password:
            flash("All fields are required", "danger")
            return redirect(url_for("forgot_password"))

        if new_password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("forgot_password"))

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not registered", "danger")
            return redirect(url_for("forgot_password"))

        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Password reset successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")
@app.route("/notifications")
def notifications():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # TEMP notifications (replace with DB later)
    notifications = [
        {"title": "Vaccination Due", "message": "Chiku vaccination is pending"},
        {"title": "Appointment Reminder", "message": "Vet visit tomorrow at 10 AM"}
    ]

    return render_template(
        "notifications.html",
        notifications=notifications
    )
@app.context_processor
def inject_notification_count():
    if "user_id" in session:
        # later replace with DB query
        return {"notification_count": 0}
    return {"notification_count": 0}


@app.route("/help")
def help():
    return render_template("help.html")

@app.route('/adopt_pet', methods=['GET', 'POST'])
def adopt():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        amount = request.form['amount']
        message = request.form['message']

        # For now just show success (later you can add payment gateway)
        flash("Thank you for your adoption ❤️", "success")

    return render_template('adopt_pet.html')
    
@app.route('/adopt-pet/<int:pet_id>', methods=['POST'])
def adopt_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    return jsonify({"success": True})
@app.route("/user_info")
def user_info():
    return render_template(
        "user_info.html",
        username=session.get("username"),
        mobile=session.get("mobile"),
        email=session.get("email")
    )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    return render_template("dashboard.html", user=user)
@app.route("/shop")
def shop():
    return render_template("shop.html")
@app.route('/delete_pet/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    if pet.photo:
        image_path = os.path.join(app.root_path, 'static', 'uploads', pet.photo)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(pet)
    db.session.commit()
    return '', 204
@app.route("/pet-home")
def pet_home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = db.session.get(User, session["user_id"])
    return render_template("pet_home.html", user=user)
@app.route('/add_pet', methods=['GET','POST'])
def add_pet():

    name = request.form.get("name")
    species = request.form.get("species")
    breed = request.form.get("breed")
    age = request.form.get("age")
    gender = request.form.get("gender")
    user = db.session.get(User, session["user_id"])
    new_pet = Pet(name=name, species=species, breed=breed, age=age, gender=gender, user_id=user.id)

    db.session.add(new_pet)
    db.session.commit()

    return redirect(url_for("dashboard"))
@app.route("/pet/<int:pet_id>")
def pet_profile(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    vaccinations = Vaccine.query.filter_by(pet_id=pet_id).all()
    healths = HealthCheckup.query.filter_by(pet_id=pet_id).all()
    diets = DietPlan.query.filter_by(pet_id=pet_id).all()

    return render_template(
        "pet_profile.html",
        pet=pet,
        vaccines=Vaccine,
        healths=healths,
        diets=diets
    )
@app.route("/pet/<int:pet_id>/upload-photo", methods=["POST"])
def upload_pet_photo(pet_id):
    file = request.files.get("photo")
    if file:
        import uuid
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)

        pet = Pet.query.get_or_404(pet_id)
        pet.photo = filename
        db.session.commit()

        flash("Photo uploaded successfully!", "success")
    else:
        flash("No file uploaded", "danger")

    return redirect(url_for("pet_profile", pet_id=pet_id))



@app.route('/add_vaccine', methods=['GET', 'POST'])
def add_vaccine():
    pets = Pet.query.all()  # get all pets for the dropdown

    if request.method == 'POST':
        pet_id = request.form.get('pets_id')

        if not pet_id:
            flash("Please select a pet!", "danger")
            return redirect(url_for('add_vaccine'))

        # Ensure pet exists
        pet = Pet.query.get(int(pet_id))
        if not pet:
            flash("Pet not found!", "danger")
            return redirect(url_for('add_vaccine'))

        # Get vaccine details
        vaccine_name = request.form.get('vaccine_name')
        last_given_date_str = request.form.get('last_given_date')
        next_due_date_str = request.form.get('next_due_date')

        try:
            last_given_date = datetime.strptime(last_given_date_str, "%Y-%m-%d").date()
            next_due_date = datetime.strptime(next_due_date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format!", "danger")
            return redirect(url_for('add_vaccine'))

        # Create new vaccine record
        vaccine = Vaccine(
            pet_id=pet.id,
            vaccine_name=vaccine_name,
            last_given_date=last_given_date,
            next_due_date=next_due_date
        )

        db.session.add(vaccine)
        db.session.commit()
        flash("Vaccine added successfully!", "success")
        return redirect(url_for('pet_profile', pet_id=pet.id))

    # GET request → show form
    return render_template('add_vaccine.html', pets=pets)
@app.route('/adopt_agri')
def adopt_agri():
    return render_template('adopt_agri.html')
from datetime import datetime

@app.route("/health_checkup", methods=["GET", "POST"])
def health_checkup():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    pets = user.pets if user else []

    if request.method == "POST":
        try:
            pet_id = int(request.form.get("pet_id"))
            date = datetime.strptime(request.form.get("date"), "%Y-%m-%d").date()
            weight = float(request.form.get("weight"))
            temperature = float(request.form.get("temperature"))

            new_checkup = HealthCheckup(
                pet_id=pet_id,
                date=date,
                weight=weight,
                temperature=temperature
            )

            db.session.add(new_checkup)
            db.session.commit()

            return jsonify({"success": True})

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)})

    return render_template("Checkup.html", user=user, pets=pets)
@app.route("/diet_plan")
def diet_plan():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = db.session.get(User, session["user_id"])
    pets = user.pets if user else []
    
    return render_template("diet_plan.html", user=user, pets=pets)
# ---------------------- ✅ GENERATE DIET PLAN (POST API)
@app.route("/generate_diet_plan", methods=["POST"])
def generate_diet_plan():

    data = request.get_json()

    species = data.get("species")
    weight = float(data.get("weight", 0))
    age_years = int(data.get("ageYears", 0))
    health = (data.get("healthIssue") or "").lower()


    # =====================================================
    #  BASE DIET DICTIONARY FOR ALL YOUR ANIMALS
    # =====================================================
    diets = {

        # ---------------- PET ANIMALS -------------------
        "Dog": {
            "morning": f"{weight * 8:.0f}g boiled chicken + rice",
            "afternoon": f"{weight * 5:.0f}g dry kibble",
            "evening": f"{weight * 8:.0f}g eggs + rice",
            "water": f"{weight * 50:.0f} ml/day"
        },

        "Cat": {
            "morning": f"{weight * 6:.0f}g wet food",
            "afternoon": f"{weight * 4:.0f}g kibble",
            "evening": f"{weight * 5:.0f}g fish or chicken",
            "water": f"{weight * 40:.0f} ml/day"
        },

        "Rabbit": {
            "morning": f"{weight * 8:.0f}g pellets",
            "afternoon": f"{weight * 5:.0f}g vegetables",
            "evening": f"{weight * 6:.0f}g hay",
            "water": f"{weight * 100:.0f} ml/day"
        },

        "Birds": {
            "morning": f"{weight * 4:.0f}g seeds",
            "afternoon": f"{weight * 3:.0f}g fruits",
            "evening": f"{weight * 3:.0f}g grains",
            "water": f"{weight * 30:.0f} ml/day"
        },

        "Fish": {
            "morning": f"{weight * 2:.0f}g pellets",
            "afternoon": f"{weight * 1:.0f}g flakes",
            "evening": f"{weight * 2:.0f}g worms",
            "water": "Clean tank water daily"
        },
         "Hamster": {
            "morning": f"{weight * 5:.0f}g mix feed",
            "afternoon": f"{weight * 2:.0f}g nuts",
            "evening": f"{weight * 3:.0f}g vegetables",
            "water": f"{weight * 25:.0f} ml/day"
        },

        # ---------------- AGRIPET ANIMALS -------------------
        "Cow": {
            "morning": f"{weight * 0.025:.1f} kg green fodder",
            "afternoon": f"{weight * 0.010:.1f} kg dry fodder",
            "evening": f"{weight * 0.020:.1f} kg silage",
            "water": f"{weight * 4:.0f} liters/day"
        },

        "Buffalo": {
            "morning": f"{weight * 0.030:.1f} kg green fodder",
            "afternoon": f"{weight * 0.015:.1f} kg dry feed",
            "evening": f"{weight * 0.020:.1f} kg silage",
            "water": f"{weight * 5:.0f} liters/day"
        },

        "Ox": {
            "morning": f"{weight * 0.020:.1f} kg fodder",
            "afternoon": f"{weight * 0.012:.1f} kg dry feed",
            "evening": f"{weight * 0.018:.1f} kg grains",
            "water": f"{weight * 4:.0f} liters/day"
        },

        "Camel": {
            "morning": f"{weight * 0.015:.1f} kg dry shrubs",
            "afternoon": f"{weight * 0.008:.1f} kg grains",
            "evening": f"{weight * 0.012:.1f} kg grass",
            "water": "Drinks once every 2–3 days (30–40 liters)"
        },

        "Horse": {
            "morning": f"{weight * 0.012:.1f} kg oats",
            "afternoon": f"{weight * 0.010:.1f} kg hay",
            "evening": f"{weight * 0.015:.1f} kg grains",
            "water": f"{weight * 5:.0f} liters/day"
        },

        "Donkey": {
            "morning": f"{weight * 0.015:.1f} kg hay",
            "afternoon": f"{weight * 0.010:.1f} kg grass",
            "evening": f"{weight * 0.012:.1f} kg grains",
            "water": f"{weight * 3:.0f} liters/day"
        },

        "Goat": {
            "morning": f"{weight * 0.030:.1f} kg green fodder",
            "afternoon": f"{weight * 0.015:.1f} kg dry feed",
            "evening": f"{weight * 0.020:.1f} kg grains",
            "water": f"{weight * 0.5:.1f} liters/day"
        },

        "Sheep": {
            "morning": f"{weight * 0.025:.1f} kg fodder",
            "afternoon": f"{weight * 0.012:.1f} kg dry feed",
            "evening": f"{weight * 0.018:.1f} kg grains",
            "water": f"{weight * 0.4:.1f} liters/day"
        },

        "Pig": {
            "morning": f"{weight * 0.030:.1f} kg grains",
            "afternoon": f"{weight * 0.020:.1f} kg pellets",
            "evening": f"{weight * 0.025:.1f} kg vegetables",
            "water": f"{weight * 4:.0f} liters/day"
        },

        "Chicken": {
            "morning": f"{weight * 15:.0f}g layer feed",
            "afternoon": f"{weight * 10:.0f}g grains",
            "evening": f"{weight * 12:.0f}g protein mix",
            "water": f"{weight * 60:.0f} ml/day"
        },

        "Rooster": {
            "morning": f"{weight * 12:.0f}g grains",
            "afternoon": f"{weight * 8:.0f}g seeds",
            "evening": f"{weight * 10:.0f}g protein feed",
            "water": f"{weight * 50:.0f} ml/day"
        }
    }
    # -------- Species Not Found -------
    if species not in diets:
        return jsonify({
            "morning": "",
            "afternoon": "",
            "evening": "",
            "water": "",
            "notes": "Diet not available for this animal"
        })
    # Start with base
    diet = diets[species].copy()
    # =====================================================
    # AGE BASED DIET CHANGES
    # =====================================================
    if age_years < 1:
        diet["notes"] = "Young animal – increase protein by 20%"
        diet["morning"] += " (extra protein)"
        diet["evening"] += " (extra protein)"

    # =====================================================
    # HEALTH CONDITION DIET CHANGES
    # =====================================================
    if "fever" in health:
        diet["notes"] = "Soft diet recommended"
        diet["morning"] = "Warm soup + soft food"
        diet["evening"] = "Electrolytes + digestible food"

    if "diarrhea" in health:
        diet["notes"] = "ORS + boiled rice recommended"
        diet["morning"] = "Boiled rice + curd"
        diet["evening"] = "ORS + soft diet"

    if "obesity" in health or "fat" in health:
        diet["notes"] = "Low calorie diet required"
        diet["evening"] = "Fiber rich vegetables"

    if "pregnant" in health:
        diet["notes"] = "High calcium + protein diet required"
        diet["afternoon"] += " + calcium supplement"

    if "weak" in health:
        diet["notes"] = "High protein recovery diet"
        diet["morning"] += " + vitamins"

    # Default Note
    if "notes" not in diet:
        diet["notes"] = "Healthy balanced diet."

    return jsonify(diet)
@app.route('/health')
def health():
    pets = Pet.query.all()
    return render_template("health.html", pets=pets)
@app.route("/pets")
def pets_list():
    return render_template("pets_list.html", pets=pets_data.keys())
@app.route("/agripet")
def agripet():
    return render_template("Agripet.html")
@app.route("/doctor_finder")
def doctor_finder():
    return render_template("doctor_finder.html")
@app.route("/pets/<pet>")
def breed_list(pet):
    breeds = pets_data.get(pet, {})
    return render_template("pet_breeds.html", pet=pet, breeds=breeds)
@app.route("/pets/<pet>/<breed>")
def breed_info(pet, breed):
    info = pets_data.get(pet, {}).get(breed)
    return render_template("breed_info.html", pet=pet, breed=breed, info=info)
@app.route('/agrishop')
def agrishop():
    return render_template('agrishop.html')
@app.route("/agripets")
def agripets():
    return render_template("agripets.html")
@app.route('/about')
def about():
    return render_template('about.html')
@app.route("/cow_breeds")
def cow_breeds():
    cow_list = [
        {
            "name": "Sahiwal","image": "Sahiwalcow.jpg",
        },
        {
            "name": "Holstein Friesian", "image": "Holstein.jpg",
        },
        {
            "name": "Jersey", "image": "jerseycow.jpg"
        },
        {
            "name": "Rathi","image": "Rathicow.jpg"
        }
    ]
    return render_template("cow_breeds.html", cow_list=cow_list)
@app.route("/buffalo_breeds")
def buffalo_breeds():
    buffalo_list = [
        {"name": "Murrah", "image": "murrahbuffalo.jpg"},
        {"name": "Jaffarabadi", "image": "jaffarabadi.jpg"},
        {"name": "Surti", "image": "Surti.jpg"},
        {"name": "Mehsana", "image": "Mehsana.jpg"}
    ]
    return render_template("buffalo_breeds.html", buffalo_list=buffalo_list)
@app.route("/ox_breeds")
def ox_breeds():
    ox_list = [
        {"name": "Kangayam", "image": "Kangayam.jpg"},
        {"name": "Khillari", "image": "khillari.jpg"},
        {"name": "Ongole", "image": "Ongole.jpg"},
        {"name": "Malvi", "image": "Malvi.jpg"}
    ]
    return render_template("ox_breeds.html", ox_list=ox_list)
@app.route("/camel_breeds")
def camel_breeds():
    camel_list = [
        {"name": "Bikaneri", "image": "Bikaneri.jpg"},
        {"name": "Jaisalmeri", "image": "jalsalmeri.jpg"},
        {"name": "Kachchi", "image": "Kalchchi.jpg"}
        
    ]
    return render_template("camel_breeds.html", camel_list=camel_list)
@app.route("/horse_breeds")
def horse_breeds():
    horse_list = [
        {"name": "Marwari", "image": "marwari.jpg"},
        {"name": "Kathiawari", "image": "kathiawari.jpg"},
        {"name": "Indian Thoroughbred", "image": "thoroughbred.jpg"}
    ]
    return render_template("horse_breeds.html", horse_list=horse_list)
@app.route("/donkey_breeds")
def donkey_breeds():
    donkey_list = [
        {"name": "Indian Wild Donkey", "image": "donkey1.jpg"},
        {"name": "Ghudkhur", "image": "ghudkhur1.jpg"}
    ]
    return render_template("donkey_breeds.html", donkey_list=donkey_list)
@app.route("/sheep_breeds")
def sheep_breeds():
    sheep_list = [
        {"name": "Deccani", "image": "deccani.jpeg"},
        {"name": "Nali", "image": "nali.jpg"},
        {"name": "Chokla", "image": "chokla.jpg"}
    ]
    return render_template("sheep_breeds.html", sheep_list=sheep_list)
@app.route("/pig_breeds")
def pig_breeds():
    pig_list = [
        {"name": "Ghoongroo", "image": "ghoongroo.jpg"},
        {"name": "Hampshire", "image": "hampshire.jpg"}
    ]
    return render_template("pig_breeds.html", pig_list=pig_list)
@app.route("/chicken_breeds")
def chicken_breeds():
    chicken_list = [
        {"name": "Giriraja", "image": "giriraja.jpg"},
        {"name": "Kadaknath", "image": "k1.jpg"},
        {"name": "Aseel", "image": "a2.jpg"}
    ]
    return render_template("chicken_breeds.html", chicken_list=chicken_list)
@app.route("/rooster_breeds")
def rooster_breeds():
    rooster_list = [
        {"name": "Aseel Rooster", "image": "aseel_rooster.jpg"},
       {"name":"Giriraja","image": "giriraj_rooster.jpg"}
    ]
    return render_template("rooster_breeds.html", rooster_list=rooster_list)   
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
# ---------------------- CLINIC API
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
# ---------------------- AUTO SMS REMINDER
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
# ---------------------- RUN APP
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)