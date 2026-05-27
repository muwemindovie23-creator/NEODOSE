from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os

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


# CREATE TABLE ON STARTUP
create_table()


# HOME ROUTE
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "NeoDose Backend Running"
    })


# GET ALL PATIENTS
@app.route("/patients", methods=["GET"])
def get_patients():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM NEODOSE_V1
        ORDER BY id DESC
    """)

    patients = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(patients)


# ADD PATIENT
@app.route("/patients", methods=["POST"])
def add_patient():
    data = request.get_json()

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

    return jsonify(new_patient), 201


# DELETE PATIENT
@app.route("/patients/<int:id>", methods=["DELETE"])
def delete_patient(id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM NEODOSE_V1
        WHERE id = %s
        RETURNING *
    """, (id,))

    deleted = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not deleted:
        return jsonify({
            "error": "Patient not found"
        }), 404

    return jsonify({
        "message": "Patient deleted successfully",
        "patient": deleted
    })


# UPDATE PATIENT
@app.route("/patients/<int:id>", methods=["PUT"])
def update_patient(id):
    data = request.get_json()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE NEODOSE_V1
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
            "error": "Patient not found"
        }), 404

    return jsonify(updated)


# RUN SERVER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
