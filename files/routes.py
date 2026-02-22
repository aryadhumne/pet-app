from werkzeug.utils import secure_filename
from flask import flash, redirect, url_for, request, current_app
import os

@bp.route("/upload_pet_photo/<int:pet_id>", methods=["POST"])
def upload_pet_photo(pet_id):

    if "photo" not in request.files:
        flash("No file selected", "danger")
        return redirect(url_for("main.pet_profile", pet_id=pet_id))

    file = request.files["photo"]

    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(url_for("main.pet_profile", pet_id=pet_id))

    # ✅ Create upload folder if not exists
    upload_folder = os.path.join(current_app.root_path, "static/uploads")
    os.makedirs(upload_folder, exist_ok=True)

    # ✅ Secure filename
    filename = secure_filename(f"pet_{pet_id}.jpg")
    filepath = os.path.join(upload_folder, filename)

    file.save(filepath)

    # ✅ Save image name to DB
    pet = Pet.query.get_or_404(pet_id)
    pet.profile_image = filename
    db.session.commit()

    flash("Profile photo uploaded successfully!", "success")
    return redirect(url_for("main.pet_profile", pet_id=pet_id))
