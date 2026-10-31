from flask import Blueprint, flash, redirect, render_template, request, url_for
from extensions import mysql

student_bp = Blueprint("students", __name__)


def get_student_columns():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SHOW COLUMNS FROM students")
        columns = [row[0] for row in cur.fetchall()]
        cur.close()
        return columns
    except Exception:
        return []


def normalize_student_record(record):
    if not record:
        return {}

    if isinstance(record, dict):
        normalized = dict(record)
    else:
        keys = ["id", "student_name", "name", "email", "email_address", "phone", "phone_number"]
        normalized = {}
        for index, value in enumerate(record):
            key = keys[index] if index < len(keys) else f"column_{index + 1}"
            normalized[key] = value

    if "student_name" not in normalized and "name" in normalized:
        normalized["student_name"] = normalized["name"]
    elif "name" not in normalized and "student_name" in normalized:
        normalized["name"] = normalized["student_name"]

    if "email_address" not in normalized and "email" in normalized:
        normalized["email_address"] = normalized["email"]
    elif "email" not in normalized and "email_address" in normalized:
        normalized["email"] = normalized["email_address"]

    if "phone_number" not in normalized and "phone" in normalized:
        normalized["phone_number"] = normalized["phone"]
    elif "phone" not in normalized and "phone_number" in normalized:
        normalized["phone"] = normalized["phone_number"]

    return normalized


def get_student_field_names():
    columns = get_student_columns()
    if not columns:
        return {
            "id": "id",
            "name": "name",
            "email": "email",
            "phone": "phone",
        }

    name_field = next((col for col in columns if col.lower() in {"student_name", "name", "full_name"}), "name")
    email_field = next((col for col in columns if col.lower() in {"email", "email_address", "student_email"}), "email")
    phone_field = next((col for col in columns if col.lower() in {"phone", "phone_number", "mobile", "contact_number"}), "phone")
    id_field = next((col for col in columns if col.lower() in {"id", "student_id"}), "id")

    return {
        "id": id_field,
        "name": name_field,
        "email": email_field,
        "phone": phone_field,
    }


def fetch_students(search_term=""):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students ORDER BY id ASC")
        rows = cur.fetchall()
        column_names = [column[0] for column in cur.description] if cur.description else []
        cur.close()

        students = []
        for row in rows:
            record = {}
            for index, column_name in enumerate(column_names):
                record[column_name] = row[index]
            students.append(normalize_student_record(record))

        search_value = (search_term or "").strip().lower()
        if search_value:
            students = [
                student for student in students
                if search_value in str(student.get("student_name", "") or "").lower()
                or search_value in str(student.get("name", "") or "").lower()
                or search_value in str(student.get("email_address", "") or "").lower()
                or search_value in str(student.get("email", "") or "").lower()
                or search_value in str(student.get("phone_number", "") or "").lower()
                or search_value in str(student.get("phone", "") or "").lower()
            ]

        return students
    except Exception:
        return []


@student_bp.route("/db-test")
def db_test():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT DATABASE()")
        database_name = cur.fetchone()[0]
        cur.close()
        return f"Connected successfully to: {database_name}"
    except Exception as exc:
        return f"Database connection failed: {exc}", 500


@student_bp.route("/", methods=["GET"])
def home():
    search_term = request.args.get("search", "").strip()
    students = fetch_students(search_term)
    return render_template(
        "index.html",
        students=students,
        total_students=len(students),
        search_term=search_term,
    )


@student_bp.route("/students", methods=["GET"])
def directory():
    return redirect(url_for("students.home"))


@student_bp.route("/students/new", methods=["GET"])
def new_student():
    return render_template("student_form.html")


@student_bp.route("/students/add", methods=["POST"])
def add_student():
    student_name = (request.form.get("student_name") or "").strip()
    email = (request.form.get("email_address") or "").strip()
    phone = (request.form.get("phone_number") or "").strip()

    if not student_name or not email or not phone:
        flash("All fields (Student Name, Email Address, and Phone Number) are required.", "warning")
        return redirect(url_for("students.home") + "#students")

    try:
        fields = get_student_field_names()
        cur = mysql.connection.cursor()
        cur.execute(
            f"INSERT INTO students ({fields['name']}, {fields['email']}, {fields['phone']}) VALUES (%s, %s, %s)",
            (student_name, email, phone),
        )
        mysql.connection.commit()
        cur.close()
        flash(f"Student '{student_name}' added successfully!", "success")
    except Exception as exc:
        mysql.connection.rollback()
        error_msg = str(exc)
        if "Duplicate entry" in error_msg:
            flash(f"A student with email '{email}' already exists.", "danger")
        else:
            flash(f"Error adding student: {error_msg}", "danger")

    return redirect(url_for("students.home") + "#students")


@student_bp.route("/students/update/<int:student_id>", methods=["POST"])
def update_student(student_id):
    student_name = (request.form.get("student_name") or "").strip()
    email = (request.form.get("email_address") or "").strip()
    phone = (request.form.get("phone_number") or "").strip()

    if not student_name or not email or not phone:
        flash("All fields (Student Name, Email Address, and Phone Number) are required.", "warning")
        return redirect(url_for("students.home") + "#students")

    try:
        fields = get_student_field_names()
        cur = mysql.connection.cursor()
        cur.execute(
            f"UPDATE students SET {fields['name']} = %s, {fields['email']} = %s, {fields['phone']} = %s WHERE {fields['id']} = %s",
            (student_name, email, phone, student_id),
        )
        mysql.connection.commit()
        cur.close()
        flash(f"Student #{student_id} updated successfully!", "success")
    except Exception as exc:
        mysql.connection.rollback()
        error_msg = str(exc)
        if "Duplicate entry" in error_msg:
            flash(f"A student with email '{email}' already exists.", "danger")
        else:
            flash(f"Error updating student: {error_msg}", "danger")

    return redirect(url_for("students.home") + "#students")


@student_bp.route("/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    try:
        fields = get_student_field_names()
        cur = mysql.connection.cursor()
        cur.execute(f"DELETE FROM students WHERE {fields['id']} = %s", (student_id,))
        mysql.connection.commit()
        cur.close()
        flash(f"Student #{student_id} deleted successfully!", "success")
    except Exception as exc:
        mysql.connection.rollback()
        flash(f"Error deleting student: {exc}", "danger")

    return redirect(url_for("students.home") + "#students")