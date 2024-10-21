from flask import Flask, request, jsonify
import pyrebase
import json
import os
from firebase_admin import credentials, initialize_app, db as admin_db  # Rename here

app = Flask(__name__)

# Load Firebase configuration from the JSON file
firebase_config_path = os.path.join(os.path.dirname(__file__), 'data/google-services.json')

# Load Firebase credentials
with open(firebase_config_path) as f:
    config = json.load(f)

# Initialize Firebase Admin
cred = credentials.Certificate("data/be-safe-app-c1e4e-firebase-adminsdk-1cw7e-2d372acfa8.json")
initialize_app(cred, {
    'databaseURL': 'https://be-safe-app-c1e4e.firebaseio.com/'
})

# Extract necessary information from google-services.json
api_key = config['client'][0]['api_key'][0]['current_key']
project_id = config['project_info']['project_id']
database_url = f"https://{project_id}.firebaseio.com/"
storage_bucket = config['project_info']['storage_bucket']

# Firebase configuration
firebase_config = {
    "apiKey": api_key,
    "authDomain": f"{project_id}.firebaseapp.com",
    "databaseURL": database_url,
    "storageBucket": storage_bucket,
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firebase_db = firebase.database()  # Renamed to avoid conflict
storage = firebase.storage()


# User login route
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return jsonify({"message": "Login successful", "token": user['idToken'], "userId": user['localId']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# User registration route
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        user = auth.create_user_with_email_and_password(email, password)
        return jsonify({"message": "User registered successfully", "userId": user['localId']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Fetch emergency contacts route
@app.route('/api/emergency-contacts', methods=['GET'])
def fetch_emergency_contacts():
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({"error": "Authorization token missing"}), 401

    try:
        # Clean the token
        if token.startswith('Bearer '):
            token = token[len('Bearer '):]

        # Verify token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']

        # Fetch emergency contacts for the user
        user_contacts_ref = admin_db.reference(f'users/{user_id}/emergencyContacts')
        emergency_contacts = user_contacts_ref.get()

        if emergency_contacts:
            return jsonify({"emergencyContacts": emergency_contacts}), 200
        else:
            return jsonify({"message": "No emergency contacts found for this user."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/emergency-contacts', methods=['POST'])
def save_emergency_contact():
    token = request.headers.get('Authorization')

    if token:
        if token.startswith('Bearer '):
            token = token[len('Bearer '):]

        try:
            # Verify token using Firebase Admin SDK
            decoded_token = admin_auth.verify_id_token(token)

            # Get the user ID from the request body
            data = request.json
            user_id = data.get('userId')
            name = data.get('name')
            phone = data.get('phoneNumber')

            if not user_id or not name or not phone:
                return jsonify({"error": "User ID, name, and phone number are required"}), 400

            # Save the new contact
            new_contact_ref = admin_db.reference(f'users/{user_id}/emergencyContacts').push()
            new_contact_ref.set({
                "name": name,
                "phoneNumber": phone
            })

            return jsonify({"message": "Contact added successfully!"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        return jsonify({"error": "Authorization token missing"}), 401

@app.route('/api/save-language-preference', methods=['POST'])
def save_language_preference():
    try:
        token = request.headers.get('Authorization')

        if token and token.startswith('Bearer '):
            token = token[len('Bearer '):]

            # Verify Firebase token to get the user ID
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Get language preference from the request body
            data = request.json
            language_preference = data.get('languagePreference')

            if not language_preference:
                return jsonify({"error": "Language preference is required"}), 400

            # Save the language preference in Firebase
            user_ref = admin_db.reference(f'users/{user_id}')
            user_ref.update({"languagePreference": language_preference})

            return jsonify({"message": "Language preference saved successfully!"}), 200

        else:
            return jsonify({"error": "Authorization token missing"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-language-preference', methods=['GET'])
def get_language_preference():
    try:
        token = request.headers.get('Authorization')

        if token and token.startswith('Bearer '):
            token = token[len('Bearer '):]

            # Verify Firebase token to get the user ID
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Fetch the language preference from Firebase
            user_ref = admin_db.reference(f'users/{user_id}/languagePreference')
            language_preference = user_ref.get()

            if language_preference:
                return jsonify({"languagePreference": language_preference}), 200
            else:
                return jsonify({"message": "No language preference found"}), 404

        else:
            return jsonify({"error": "Authorization token missing"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
