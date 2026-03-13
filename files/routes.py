
from flask import flash, redirect, url_for, request, current_app


import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_pet_photo', methods=['POST'])
def upload_pet_photo():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No file'}), 400

    file  = request.files['photo']
    pet_id = request.form.get('pet_id')

    if not file or not pet_id or not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f'pet_{pet_id}.{ext}'

    save_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(save_dir, exist_ok=True)
    file.save(os.path.join(save_dir, filename))

    # Save filename to DB
    pet = Pet.query.get(pet_id)
    if not pet:
        return jsonify({'success': False, 'error': 'Pet not found'}), 404

    pet.photo = filename
    db.session.commit()

    return jsonify({'success': True, 'photo': filename})