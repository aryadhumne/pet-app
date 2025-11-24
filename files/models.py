# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    _tablename_ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    # optional relationship
    pets = db.relationship('Pet', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Pet(db.Model):
    _tablename_ = "pet"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    species = db.Column(db.String(80), nullable=True)
    breed = db.Column(db.String(120), nullable=True)
    age = db.Column(db.String(40), nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)  # store file name in static/images/
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # optional: link to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)