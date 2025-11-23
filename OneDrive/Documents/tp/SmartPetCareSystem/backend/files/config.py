# SmartAgriPetCare/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:admin@123@localhost:5432/smartpetcare'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
