# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
def _get_models():
    from files.models import (
        Appointment, DoctorSchedule, DoctorHoliday, VetVaccineInfo
    )
    return Appointment, DoctorSchedule, DoctorHoliday, VetVaccineInfo

db = SQLAlchemy()
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), nullable=True)   # ← must exist

    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role            = db.Column(db.String(20),  nullable=False, default='pet_owner')
    doctor_fullname = db.Column(db.String(120), nullable=True)
    specialization  = db.Column(db.String(120), nullable=True)
    clinic_name     = db.Column(db.String(150), nullable=True)
    clinic_address  = db.Column(db.String(250), nullable=True)
    experience      = db.Column(db.Integer,     nullable=True)
    license_number  = db.Column(db.String(60),  nullable=True)
    is_on_duty      = db.Column(db.Boolean,     default=True)


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
    gender = db.Column(db.String(20))   # ✅ added
    image_filename = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    photo = db.Column(db.String(200), nullable=True, default=None)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
class DietPlan(db.Model):
    __tablename__ = "diet_plan"
 
    id        = db.Column(db.Integer, primary_key=True)
    pet_id    = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    species   = db.Column(db.String(50))
    weight    = db.Column(db.Float)
    age_years = db.Column(db.Integer)
    morning   = db.Column(db.String(255))
    afternoon = db.Column(db.String(255))
    evening   = db.Column(db.String(255))
    water     = db.Column(db.String(100))
    notes     = db.Column(db.String(255))
    created_at = db.Column(db.Date, default=date.today)
 
    pet = db.relationship('Pet', backref='diet_plans')
class Vaccination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pet.id"), nullable=False)
    vaccine_name = db.Column(db.String(100), nullable=False)
    last_given_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date)
class DoctorSchedule(db.Model):
     _tablename__ = "doctor_schedule"    
     id          = db.Column(db.Integer, primary_key=True)
     doctor_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
     day_name    = db.Column(db.String(20))          # "Monday" … "Sunday"
     is_open     = db.Column(db.Boolean, default=True)
     from_time   = db.Column(db.String(10))           # "09:00"
     to_time     = db.Column(db.String(10))           # "18:00"

class DoctorHoliday(db.Model):
     __tablename__ = "doctor_holiday"
     id          = db.Column(db.Integer, primary_key=True)
     doctor_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
     holiday_date = db.Column(db.Date, nullable=False)
     note        = db.Column(db.String(200))

class VetVaccineInfo(db.Model):
     __tablename__ = "vet_vaccine_info"
     id           = db.Column(db.Integer, primary_key=True)
     doctor_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
     vaccine_name = db.Column(db.String(120), nullable=False)
     species      = db.Column(db.String(80))
     symptoms     = db.Column(db.Text)                # comma-separated
     rec_age      = db.Column(db.String(100))
     dosage       = db.Column(db.String(150))
     side_effects = db.Column(db.String(200))
     price_range  = db.Column(db.String(80))
     notes        = db.Column(db.Text)
     created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
     __tablename__ = "appointment"
     id            = db.Column(db.Integer, primary_key=True)
     ref_code      = db.Column(db.String(20), unique=True, nullable=False)
     doctor_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
     owner_name    = db.Column(db.String(120))
     owner_phone   = db.Column(db.String(30))
     owner_email   = db.Column(db.String(120))
     pet_name      = db.Column(db.String(80))
     pet_type      = db.Column(db.String(40))
     pet_breed     = db.Column(db.String(80))
     pet_age       = db.Column(db.String(40))
     vaccination_history = db.Column(db.Text)
     symptoms      = db.Column(db.Text)
     symptom_tags  = db.Column(db.String(300))
     visit_type    = db.Column(db.String(30))
     pref_date     = db.Column(db.Date)
     pref_time     = db.Column(db.String(10))
     alt_date      = db.Column(db.Date, nullable=True)
     extra_notes   = db.Column(db.Text)
     status        = db.Column(db.String(20), default='pending')  # pending/confirmed/rejected
     doctor_message = db.Column(db.Text)
     created_at    = db.Column(db.DateTime, default=datetime.utcnow)
     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # add this
