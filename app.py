from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# ENABLE CORS
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# DATABASE CONNECTION
# =========================
def get_connection():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


# =========================
# CREATE TABLE
# =========================
def create_table():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS neo_dose_mod (

            patient_id INTEGER
            PRIMARY KEY
            GENERATED ALWAYS AS IDENTITY,

            medication_type TEXT,

            antibiotic TEXT,

            prescribed_dose_mg NUMERIC,

            concentration_mg_ml NUMERIC,

            infusion_time_hr INTEGER,

            weight_kg NUMERIC,

            infusion_rate_ml_hr NUMERIC,

            safety_check BOOLEAN,

            device_ip INET,

            prescription_ml_kg_day NUMERIC,

            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cur.close()
    conn.close()


# CREATE TABLE ON STARTUP
create_table()


# =========================
# HOME ROUTE
# =========================
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "NeoDose Backend Running"
    })


# =========================
# GET ALL PATIENTS
# =========================
@app.route("/patients", methods=["GET"])
def get_patients():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM neo_dose_mod
        ORDER BY timestamp DESC
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
@app.route("/patients/<int:patient_id>", methods=["GET"])
def get_single_patient(patient_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM neo_dose_mod
        WHERE patient_id = %s
    """, (patient_id,))

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
# =========================
@app.route("/patients", methods=["POST"])
def add_patient():

    data = request.get_json()

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO neo_dose_mod (

                medication_type,
                antibiotic,
                prescribed_dose_mg,
                concentration_mg_ml,
                infusion_time_hr,
                weight_kg,
                infusion_rate_ml_hr,
                safety_check,
                device_ip,
                prescription_ml_kg_day

            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

            RETURNING *
        """, (

            data["medication_type"],
            data["antibiotic"],
            data["prescribed_dose_mg"],
            data["concentration_mg_ml"],
            data["infusion_time_hr"],
            data["weight_kg"],
            data["infusion_rate_ml_hr"],
            data["safety_check"],
            data["device_ip"],
            data["prescription_ml_kg_day"]

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
@app.route("/patients/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):

    data = request.get_json()

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE neo_dose_mod

            SET
                medication_type = %s,
                antibiotic = %s,
                prescribed_dose_mg = %s,
                concentration_mg_ml = %s,
                infusion_time_hr = %s,
                weight_kg = %s,
                infusion_rate_ml_hr = %s,
                safety_check = %s,
                device_ip = %s,
                prescription_ml_kg_day = %s

            WHERE patient_id = %s

            RETURNING *
        """, (

            data["medication_type"],
            data["antibiotic"],
            data["prescribed_dose_mg"],
            data["concentration_mg_ml"],
            data["infusion_time_hr"],
            data["weight_kg"],
            data["infusion_rate_ml_hr"],
            data["safety_check"],
            data["device_ip"],
            data["prescription_ml_kg_day"],
            patient_id

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

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# DELETE PATIENT
# =========================
@app.route("/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM neo_dose_mod
            WHERE patient_id = %s
            RETURNING *
        """, (patient_id,))

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

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
