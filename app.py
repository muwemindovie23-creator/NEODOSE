from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")


# DATABASE CONNECTION
def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


# CREATE TABLE
def create_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS NEODOSE_V1 (
            id SERIAL PRIMARY KEY,
            patient_id VARCHAR(50) NOT NULL,
            medication_type VARCHAR(10) NOT NULL
                CHECK (medication_type IN ('PN', 'IV')),
            antibiotics TEXT,
            weight_kg DECIMAL(5,2),
            infusion_rate DECIMAL(6,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# HOME
@app.route("/")
def home():
    return jsonify({
        "message": "NeoDose Backend Running"
    })


# GET ALL PATIENTS
@app.route("/patients", methods=["GET"])
def get_patients():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM NEODOSE_V1 ORDER BY id DESC")
    patients = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(patients)


# ADD PATIENT
@app.route("/patients", methods=["POST"])
def add_patient():
    data = request.json

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO NEODOSE_V1 (
            patient_id,
            medication_type,
            antibiotics,
            weight_kg,
            infusion_rate
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """, (
        data["patient_id"],
        data["medication_type"],
        data["antibiotics"],
        data["weight_kg"],
        data["infusion_rate"]
    ))

    new_patient = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    return jsonify(new_patient)


# START SERVER
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
