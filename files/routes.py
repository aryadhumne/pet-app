# routes.py
from flask import Blueprint, render_template, url_for, redirect, current_app, request
from models import db, Pet
from sqlalchemy import asc
import os

bp = Blueprint('main', _name_)

# Breed info dictionary - extend as needed
BREED_INFO = {
    "Golden Retriever": {
        "type": "Dog",
        "size": "Large",
        "care": "High exercise needs, regular brushing. Prone to hip dysplasia.",
        "image_hint": "golden_retriever.webp"
    },
    "German Shepherd": {
        "type": "Dog",
        "size": "Large",
        "care": "Intelligent and active. Needs training and socialization.",
        "image_hint": "german_shepherd.webp"
    },
    "Persian": {
        "type": "Cat",
        "size": "Medium",
        "care": "Long coat needs frequent grooming.",
        "image_hint": "persian_cat.webp"
    },
    "Local Cow": {
        "type": "Cow",
        "size": "Large",
        "care": "Dairy breed care, milking schedule and nutrition important.",
        "image_hint": "cow.webp"
    },
    # Add other breeds used by your users...
}

def get_breed_info(breed_name):
    if not breed_name:
        return None
    return BREED_INFO.get(breed_name, {
        "type": "Unknown",
        "size": "Unknown",
        "care": "No breed-specific info available",
        "image_hint": None
    })

@bp.route('/')
def index():
    # redirect to dashboard
    return redirect(url_for('main.dashboard'))

@bp.route('/dashboard')
def dashboard():
    """
    Dashboard shows top bar with pet accounts (all pets for now or current_user's pets)
    """
    # If you use flask-login: import current_user and filter by current_user.id
    # from flask_login import current_user
    if 'user_id' in request.args:
        # optional: show pets for a specific user (debug)
        user_id = request.args.get('user_id')
        pets = Pet.query.filter_by(user_id=user_id).order_by(asc(Pet.created_at)).all()
    else:
        # default: show all pets (or change to current_user.pets if using auth)
        pets = Pet.query.order_by(asc(Pet.created_at)).all()

    return render_template('dashboard.html', pets=pets)

@bp.route('/pet/<int:pet_id>')
def pet_profile(pet_id):
    """
    Show a single pet's profile and breed info
    """
    pet = Pet.query.get_or_404(pet_id)
    breed_info = get_breed_info(pet.breed)
    return render_template('pet_profile.html', pet=pet, breed_info=breed_info)