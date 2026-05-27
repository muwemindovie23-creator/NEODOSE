from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# ALLOW WEBSITE ACCESS
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
        CREATE TABLE IF NOT EXISTS neo_dose_mod (
            id SERIAL PRIMARY KEY,
            patient_id VARCHAR(50) NOT NULL,
            medication_type VARCHAR(10) NOT NULL
                CHECK (medication_type IN ('PN', 'IV')),
            antibiotics TEXT,
            weight_kg DECIMAL(10,2),
            infusion_rate DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ENSURE COLUMN TYPES
    cur.execute("""
        ALTER TABLE neo_dose_mod
        ALTER COLUMN weight_kg TYPE DECIMAL(10,2)
    """)

    cur.execute("""
        ALTER TABLE neo_dose_mod
        ALTER COLUMN infusion_rate TYPE DECIMAL(10,2)
    """)

    conn.commit()

    cur.close()
    conn.close()


# CREATE TABLE ON STARTUP
create_table()


# HOME ROUTE
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "NeoDose Backend Running"
    })


# =========================
# GET ALL PATIENTS
# WEBSITE FETCHES FROM HERE
# =========================
@app.route("/patients", methods=["GET"])
def get_patients():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM neo_dose_mod
        ORDER BY created_at DESC
    """)

    patients = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "success": True,
        "count": len(patients),
        "patients": patients
    })


# =========================
# GET SINGLE PATIENT
# =========================
@app.route("/patients/<int:id>", methods=["GET"])
def get_single_patient(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM neo_dose_mod
        WHERE id = %s
    """, (id,))

    patient = cur.fetchone()

    cur.close()
    conn.close()

    if not patient:

        return jsonify({
            "success": False,
            "message": "Patient not found"
        }), 404

    return jsonify({
        "success": True,
        "patient": patient
    })


# =========================
# ADD PATIENT
# ESP32 SENDS DATA HERE
# =========================
@app.route("/patients", methods=["POST"])
def add_patient():

    data = request.get_json()

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO neo_dose_mod (
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

        return jsonify({
            "success": True,
            "message": "Patient added successfully",
            "patient": new_patient
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# UPDATE PATIENT
# =========================
@app.route("/patients/<int:id>", methods=["PUT"])
def update_patient(id):

    data = request.get_json()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE neo_dose_mod
        SET
            patient_id = %s,
            medication_type = %s,
            antibiotics = %s,
            weight_kg = %s,
            infusion_rate = %s
        WHERE id = %s
        RETURNING *
    """, (
        data["patient_id"],
        data["medication_type"],
        data["antibiotics"],
        data["weight_kg"],
        data["infusion_rate"],
        id
    ))

    updated = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not updated:

        return jsonify({
            "success": False,
            "message": "Patient not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Patient updated successfully",
        "patient": updated
    })


# =========================
# DELETE PATIENT
# =========================
@app.route("/patients/<int:id>", methods=["DELETE"])
def delete_patient(id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM neo_dose_mod
        WHERE id = %s
        RETURNING *
    """, (id,))

    deleted = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not deleted:

        return jsonify({
            "success": False,
            "message": "Patient not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Patient deleted successfully",
        "patient": deleted
    })


# RUN SERVER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
