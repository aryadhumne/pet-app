from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint("chatbot_bp", __name__)

# ================= MEMORY =================
memory = {
    "animal": None,
    "symptom": None
}

# ================= PET NAMES =================
ANIMALS = {
    "dog": ["dog", "puppy", "कुत्ता", "कुत्रा", "श्वान"],
    "cat": ["cat", "kitten", "बिल्ली", "मांजर"]
}

# ================= SYMPTOMS =================
SYMPTOMS = {
    "fever": ["fever", "bukhar", "बुखार", "ताप"],
    "vomiting": ["vomit", "vomiting", "ulti", "उलटी", "ओकारी"],
    "diarrhea": ["diarrhea", "loose motion", "दस्त", "जुलाब"]
}

# ================= FEEDING KEYWORDS =================
FEEDING_WORDS = [
    "feed", "food", "eat", "diet", "khilau", "khana",
    "खिलाऊ", "खाना", "काय खाऊ", "काय खायला"
]

# ================= RESPONSES =================
RESPONSES = {

# ---------- FEEDING ----------
"feeding": {
    "dog": {
        "en-IN": (
            "🐶 **Dog Feeding Guide**\n"
            "✔ Rice + boiled chicken\n"
            "✔ Roti + vegetables\n"
            "✔ Eggs (boiled)\n"
            "✔ Dog food (recommended)\n\n"
            "❌ Avoid chocolate, onion, grapes"
        ),
        "hi-IN": (
            "🐶 **कुत्ते का खाना**\n"
            "✔ चावल + उबला चिकन\n"
            "✔ रोटी + सब्ज़ी\n"
            "✔ उबला अंडा\n"
            "✔ डॉग फूड\n\n"
            "❌ चॉकलेट, प्याज, अंगूर न दें"
        ),
        "mr-IN": (
            "🐶 **कुत्र्याचे अन्न**\n"
            "✔ भात + उकडलेले चिकन\n"
            "✔ पोळी + भाज्या\n"
            "✔ उकडलेले अंडे\n"
            "✔ डॉग फूड\n\n"
            "❌ चॉकलेट, कांदा, द्राक्षे देऊ नका"
        )
    },

    "cat": {
        "en-IN": (
            "🐱 **Cat Feeding Guide**\n"
            "✔ Boiled fish or chicken\n"
            "✔ Rice in small amount\n"
            "✔ Eggs (occasionally)\n"
            "✔ Cat food\n\n"
            "❌ Avoid milk & spices"
        ),
        "hi-IN": (
            "🐱 **बिल्ली का खाना**\n"
            "✔ उबली मछली या चिकन\n"
            "✔ थोड़ा चावल\n"
            "✔ कभी-कभी अंडा\n"
            "✔ कैट फूड\n\n"
            "❌ दूध और मसाले न दें"
        ),
        "mr-IN": (
            "🐱 **मांजराचे अन्न**\n"
            "✔ उकडलेली मासळी किंवा चिकन\n"
            "✔ थोडा भात\n"
            "✔ कधीकधी अंडे\n"
            "✔ कॅट फूड\n\n"
            "❌ दूध व मसाले देऊ नका"
        )
    }
},

# ---------- VACCINATION ----------
"vaccine": {
    "dog": {
        "en-IN": "🐶 **Dog Vaccines**\n✔ 6–8 weeks: DHPP\n✔ 12 weeks: Rabies\n✔ Yearly booster",
        "hi-IN": "🐶 **कुत्ते के टीके**\n✔ 6–8 हफ्ते: DHPP\n✔ 12 हफ्ते: रेबीज\n✔ हर साल बूस्टर",
        "mr-IN": "🐶 **कुत्र्याचे लसीकरण**\n✔ 6–8 आठवडे: DHPP\n✔ 12 आठवडे: रेबीज\n✔ दरवर्षी बूस्टर"
    },
    "cat": {
        "en-IN": "🐱 **Cat Vaccines**\n✔ 6–8 weeks: FVRCP\n✔ 12 weeks: Rabies\n✔ Yearly booster",
        "hi-IN": "🐱 **बिल्ली के टीके**\n✔ 6–8 हफ्ते: FVRCP\n✔ 12 हफ्ते: रेबीज\n✔ हर साल बूस्टर",
        "mr-IN": "🐱 **मांजराचे लसीकरण**\n✔ 6–8 आठवडे: FVRCP\n✔ 12 आठवडे: रेबीज\n✔ दरवर्षी बूस्टर"
    }
}
}

# ================= HELPERS =================
def detect_animal(msg):
    for animal, words in ANIMALS.items():
        for w in words:
            if w in msg:
                return animal
    return None

def detect_symptom(msg):
    for symptom, words in SYMPTOMS.items():
        for w in words:
            if w in msg:
                return symptom
    return None

def is_feeding_question(msg):
    return any(w in msg for w in FEEDING_WORDS)

# ================= CHATBOT ROUTE =================
@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    msg = data.get("message", "").lower()
    lang = data.get("lang", "en-IN")

    if not msg:
        return jsonify({"reply": "Please type your question 😊"})

    animal = detect_animal(msg)
    symptom = detect_symptom(msg)

    if animal:
        memory["animal"] = animal

    # ---------- FEEDING ----------
    if is_feeding_question(msg):
        pet = memory["animal"]
        if pet:
            return jsonify({"reply": RESPONSES["feeding"][pet][lang]})
        else:
            return jsonify({
                "reply": {
                    "en-IN": "Which pet? Dog or Cat 🐶🐱",
                    "hi-IN": "कौन सा पालतू? कुत्ता या बिल्ली 🐶🐱",
                    "mr-IN": "कोणता पाळीव प्राणी? कुत्रा की मांजर 🐶🐱"
                }[lang]
            })

    # ---------- SYMPTOMS ----------
    if symptom:
        memory["symptom"] = symptom
        return jsonify({"reply": RESPONSES[symptom][lang]})

    # ---------- VACCINE ----------
    if "vaccine" in msg or "लस" in msg or "टीका" in msg:
        pet = memory["animal"]
        if pet:
            return jsonify({"reply": RESPONSES["vaccine"][pet][lang]})

    # ---------- DEFAULT ----------
    return jsonify({
        "reply": {
            "en-IN": "Please tell pet problem or ask about food or vaccine 🐾",
            "hi-IN": "पालतू जानवर की समस्या या खाने के बारे में पूछें 🐾",
            "mr-IN": "पाळीव प्राण्याची समस्या किंवा अन्नाबद्दल विचारा 🐾"
        }[lang]
    })