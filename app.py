from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory
import os
import mysql.connector
from mysql.connector import Error

app = Flask(__name__, template_folder=".")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "aadhar-card-processing-system")

# Existing MySQL database details from the project.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "AADHAR_CARD_PROCESSING_SYSTEM")
}


def get_db():
    """Create a new MySQL connection for each request."""
    return mysql.connector.connect(**DB_CONFIG)


def close_db(cursor=None, db=None):
    """Safely close a cursor and database connection."""
    if cursor is not None:
        cursor.close()
    if db is not None and db.is_connected():
        db.close()


def get_report_data():
    """Return report rows and dynamic application counts."""
    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        report_query = """
            SELECT
                a.application_id,
                c.name AS citizen_name,
                a.application_type,
                a.application_date,
                a.status AS application_status,
                v.verification_result,
                v.remarks,
                ac.aadhaar_number,
                ac.issue_date,
                ac.card_status
            FROM Application a
            JOIN Citizen c
                ON a.citizen_id = c.citizen_id
            LEFT JOIN Verification v
                ON a.application_id = v.application_id
            LEFT JOIN Aadhaar_Card ac
                ON a.application_id = ac.application_id
            ORDER BY a.application_id DESC
        """
        cursor.execute(report_query)
        reports = cursor.fetchall()

        count_query = """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN LOWER(COALESCE(status, 'Pending')) = 'approved' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN LOWER(COALESCE(status, 'Pending')) = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN LOWER(COALESCE(status, 'Pending')) = 'rejected' THEN 1 ELSE 0 END) AS rejected
            FROM Application
        """
        cursor.execute(count_query)
        counts = cursor.fetchone()

        return reports, {
            "total": counts["total"] or 0,
            "approved": counts["approved"] or 0,
            "pending": counts["pending"] or 0,
            "rejected": counts["rejected"] or 0
        }

    except Error as e:
        flash("Unable to load reports: " + str(e), "error")
        return [], {"total": 0, "approved": 0, "pending": 0, "rejected": 0}
    finally:
        close_db(cursor, db)


def render_home(**context):
    """Render the single-page application with fresh report data."""
    reports, counts = get_report_data()
    context.setdefault("reports", reports)
    context.setdefault("counts", counts)
    return render_template("index.html", **context)


@app.route("/style.css")
def style():
    """Serve the existing CSS file from the project root."""
    return send_from_directory(".", "style.css")


@app.route("/")
def home():
    return render_home()


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    dob = request.form.get("dob", "").strip()
    gender = request.form.get("gender", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()

    if not all([name, dob, gender, phone, address, city, state]):
        flash("Please fill in all citizen registration fields.", "error")
        return redirect(url_for("home") + "#register")

    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor()

        query = """
            INSERT INTO Citizen
            (name, date_of_birth, gender, phone, address, city, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, dob, gender, phone, address, city, state))
        db.commit()

        citizen_id = cursor.lastrowid
        flash(
            f"Citizen registered successfully! Citizen ID: {citizen_id}",
            "success"
        )

    except Error as e:
        if db is not None:
            db.rollback()
        flash("Citizen registration failed: " + str(e), "error")
    finally:
        close_db(cursor, db)

    return redirect(url_for("home") + "#register")


@app.route("/apply", methods=["POST"])
def apply_aadhaar():
    citizen_id = request.form.get("citizen_id", "").strip()
    application_type = request.form.get("application_type", "").strip()
    application_date = request.form.get("application_date", "").strip()

    if not all([citizen_id, application_type, application_date]):
        flash("Please fill in all Aadhaar application fields.", "error")
        return redirect(url_for("home") + "#application")

    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor()

        # Validate the Citizen ID before inserting the application.
        cursor.execute(
            "SELECT citizen_id FROM Citizen WHERE citizen_id = %s",
            (citizen_id,)
        )
        citizen = cursor.fetchone()

        if not citizen:
            flash(f"Citizen ID {citizen_id} does not exist.", "error")
            return redirect(url_for("home") + "#application")

        query = """
            INSERT INTO Application
            (citizen_id, application_type, application_date)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (citizen_id, application_type, application_date))
        db.commit()

        application_id = cursor.lastrowid
        flash(
            f"Aadhaar application submitted successfully! Application ID: {application_id}",
            "success"
        )

    except Error as e:
        if db is not None:
            db.rollback()
        flash("Application submission failed: " + str(e), "error")
    finally:
        close_db(cursor, db)

    return redirect(url_for("home") + "#application")


@app.route("/verify", methods=["POST"])
def verify_documents():
    application_id = request.form.get("application_id", "").strip()
    result = request.form.get("verification_result", "").strip()
    remarks = request.form.get("remarks", "").strip()

    if result not in ("Approved", "Rejected"):
        flash("Please select Approved or Rejected.", "error")
        return redirect(url_for("home") + "#verification")

    if not application_id:
        flash("Please enter an Application ID.", "error")
        return redirect(url_for("home") + "#verification")

    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor()

        # First make sure the application exists.
        cursor.execute(
            "SELECT application_id FROM Application WHERE application_id = %s",
            (application_id,)
        )
        application = cursor.fetchone()

        if not application:
            flash(f"Application ID {application_id} does not exist.", "error")
            return redirect(url_for("home") + "#verification")

        # Update an existing verification record or create one.
        cursor.execute(
            "SELECT application_id FROM Verification WHERE application_id = %s",
            (application_id,)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE Verification
                SET verification_date = CURDATE(),
                    verified_by = 'Officer',
                    verification_result = %s,
                    remarks = %s
                WHERE application_id = %s
                """,
                (result, remarks, application_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO Verification
                (application_id, verification_date, verified_by,
                 verification_result, remarks)
                VALUES (%s, CURDATE(), 'Officer', %s, %s)
                """,
                (application_id, result, remarks)
            )

        # Keep Application status synchronized with the verification result.
        # Aadhaar_Card is intentionally NOT inserted here; any existing
        # database trigger/logic remains responsible for card creation.
        cursor.execute(
            "UPDATE Application SET status = %s WHERE application_id = %s",
            (result, application_id)
        )

        db.commit()
        flash(
            f"Document verification updated successfully. Application {application_id}: {result}.",
            "success"
        )

    except Error as e:
        if db is not None:
            db.rollback()
        flash("Document verification failed: " + str(e), "error")
    finally:
        close_db(cursor, db)

    return redirect(url_for("home") + "#verification")


@app.route("/status", methods=["GET"])
def application_status():
    application_id = request.args.get("application_id", "").strip()
    status_result = None

    if application_id:
        db = None
        cursor = None
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)

            query = """
                SELECT a.application_id,
                       c.name AS citizen_name,
                       a.application_type,
                       a.application_date,
                       a.status AS application_status,
                       v.verification_result,
                       v.remarks
                FROM Application a
                JOIN Citizen c ON a.citizen_id = c.citizen_id
                LEFT JOIN Verification v ON a.application_id = v.application_id
                WHERE a.application_id = %s
            """
            cursor.execute(query, (application_id,))
            status_result = cursor.fetchone()

            if not status_result:
                flash(f"Application ID {application_id} not found.", "error")

        except Error as e:
            flash("Unable to check application status: " + str(e), "error")
        finally:
            close_db(cursor, db)

    return render_home(status_result=status_result)


@app.route("/search", methods=["GET"])
def search_citizen():
    citizen_id = request.args.get("citizen_id", "").strip()
    citizen_result = None

    if citizen_id:
        db = None
        cursor = None
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT citizen_id, name, date_of_birth, gender,
                       phone, address, city, state
                FROM Citizen
                WHERE citizen_id = %s
                """,
                (citizen_id,)
            )
            citizen_result = cursor.fetchone()

            if not citizen_result:
                flash(f"Citizen ID {citizen_id} not found.", "error")

        except Error as e:
            flash("Unable to search citizen: " + str(e), "error")
        finally:
            close_db(cursor, db)

    return render_home(citizen_result=citizen_result)


@app.route("/update-request", methods=["POST"])
def update_request():
    citizen_id = request.form.get("citizen_id", "").strip()
    update_type = request.form.get("update_type", "").strip()
    new_value = request.form.get("new_value", "").strip()

    if update_type not in ("Address", "Phone Number"):
        flash("Please select Address or Phone Number as the update type.", "error")
        return redirect(url_for("home") + "#updates")

    if not all([citizen_id, new_value]):
        flash("Please enter the Citizen ID and new value.", "error")
        return redirect(url_for("home") + "#updates")

    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor()

        column = "address" if update_type == "Address" else "phone"
        cursor.execute(
            f"SELECT {column} FROM Citizen WHERE citizen_id = %s",
            (citizen_id,)
        )
        result = cursor.fetchone()

        if not result:
            flash(f"Citizen ID {citizen_id} not found.", "error")
            return redirect(url_for("home") + "#updates")

        old_value = result[0]

        cursor.execute(
            """
            INSERT INTO Update_Request
            (citizen_id, update_type, old_value, new_value, request_date, status)
            VALUES (%s, %s, %s, %s, CURDATE(), 'Pending')
            """,
            (citizen_id, update_type, old_value, new_value)
        )
        db.commit()

        request_id = cursor.lastrowid
        flash(
            f"Update request submitted successfully! Request ID: {request_id}",
            "success"
        )

    except Error as e:
        if db is not None:
            db.rollback()
        flash("Update request failed: " + str(e), "error")
    finally:
        close_db(cursor, db)

    return redirect(url_for("home") + "#updates")


if __name__ == "__main__":
    app.run(debug=True)
