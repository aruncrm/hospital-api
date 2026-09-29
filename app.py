import os
import sqlite3

from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)


# --------------------------------------------------
# CREATE FLASK APP
# --------------------------------------------------

app = Flask(__name__)


# --------------------------------------------------
# JWT CONFIGURATION
# --------------------------------------------------

# Local fallback secret.
# When deploying to Render, set JWT_SECRET_KEY
# in Render Environment Variables.
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY",
    "local-development-secret"
)

jwt = JWTManager(app)


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE_NAME = "patients.db"


def create_database():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    print("Database and patients table created successfully")


# Create database/table when app starts
create_database()


# --------------------------------------------------
# HOME API
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "Hospital API is working"
    }), 200


# --------------------------------------------------
# LOGIN API
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({
            "error": "Username and password are required"
        }), 400

    # Temporary credentials for testing
    if username != "admin" or password != "admin123":
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    # Create JWT access token
    access_token = create_access_token(
        identity=username
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token
    }), 200


# --------------------------------------------------
# GET HOSPITAL DETAILS
# --------------------------------------------------

@app.route("/hospital", methods=["GET"])
def get_hospital():

    hospital_details = {
        "hospital_name": "ABC Hospital",
        "hospital_code": "CH01",
        "location": "Chennai"
    }

    return jsonify(hospital_details), 200


# --------------------------------------------------
# POST PATIENT
# JWT TOKEN REQUIRED
# --------------------------------------------------

@app.route("/patient", methods=["POST"])
@jwt_required()
def add_patient():

    current_user = get_jwt_identity()

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    patient_name = data.get("patient_name")

    if not patient_name:
        return jsonify({
            "error": "patient_name is required"
        }), 400

    patient_name = patient_name.strip()

    if not patient_name:
        return jsonify({
            "error": "patient_name cannot be empty"
        }), 400

    # Connect to SQLite
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Insert patient
    cursor.execute(
        """
        INSERT INTO patients (patient_name)
        VALUES (?)
        """,
        (patient_name,)
    )

    connection.commit()

    # Get newly created ID
    patient_id = cursor.lastrowid

    connection.close()

    print("Patient Saved:", patient_name)
    print("Added By:", current_user)

    return jsonify({
        "message": "Patient saved successfully",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "added_by": current_user
    }), 201


# --------------------------------------------------
# GET ALL PATIENTS
# JWT TOKEN REQUIRED
# --------------------------------------------------

@app.route("/patients", methods=["GET"])
@jwt_required()
def get_patients():

    connection = sqlite3.connect(DATABASE_NAME)

    # Return SQLite records with column names
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            patient_name
        FROM patients
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    patients = []

    for row in rows:
        patients.append({
            "id": row["id"],
            "patient_name": row["patient_name"]
        })

    return jsonify({
        "count": len(patients),
        "patients": patients
    }), 200


# --------------------------------------------------
# START FLASK
# --------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    print(f"Starting Hospital API on port {port}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )