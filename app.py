import os
from pathlib import Path
from datetime import datetime

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    url_for,
    session
)

from dotenv import load_dotenv
import psycopg2
from werkzeug.security import check_password_hash


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "dental-clinic-development-secret-key"
)


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        database=os.getenv("DB_NAME", "dental_clinic"),
        user=os.getenv("DB_USER", "clinic_user"),
        password=os.getenv("DB_PASSWORD", "clinic_password")
    )


# =========================================================
# LOGIN + ROLE
# =========================================================

@app.before_request
def check_login_and_permission():

    # Các trang không cần đăng nhập
    public_paths = [
        "/login",
        "/logout",
        "/static",
        "/db-test"
    ]

    for path in public_paths:
        if request.path == path or request.path.startswith(path + "/"):
            return

    # Chưa đăng nhập
    if "user_id" not in session:
        return redirect(url_for("login"))

    role = session.get("role")

    # Trang chủ: tất cả tài khoản đều được vào
    if request.path == "/":
        return

    # =====================================================
    # QUYỀN RECEPTIONIST
    # =====================================================

    receptionist_paths = [
        "/patients",
        "/appointments",
        "/services",
        "/invoices"
    ]

    # =====================================================
    # QUYỀN DOCTOR
    # =====================================================

    doctor_paths = [
        "/patients",
        "/appointments",
        "/doctors",
        "/medical-records",
        "/services",
        "/invoices"
    ]

    # =====================================================
    # QUYỀN MANAGER
    # =====================================================

    manager_paths = [
        "/patients",
        "/appointments",
        "/doctors",
        "/medical-records",
        "/services",
        "/invoices"
    ]

    # =====================================================
    # MANAGER
    # =====================================================

    if role == "manager":
        return

    # =====================================================
    # RECEPTIONIST
    # =====================================================

    if role == "receptionist":

        for path in receptionist_paths:

            if (
                request.path == path
                or request.path.startswith(path + "/")
            ):
                return

    # =====================================================
    # DOCTOR
    # =====================================================

    if role == "doctor":

        for path in doctor_paths:

            if (
                request.path == path
                or request.path.startswith(path + "/")
            ):
                return

    # =====================================================
    # KHÔNG CÓ QUYỀN
    # =====================================================

    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Không có quyền truy cập</title>
    </head>

    <body>

        <div style="
            font-family: Arial;
            max-width: 700px;
            margin: 80px auto;
            text-align: center;
        ">

            <h1>⛔ Không có quyền truy cập</h1>

            <p>
                Tài khoản của bạn không được phép sử dụng chức năng này.
            </p>

            <a href="/" style="
                display:inline-block;
                margin-top:20px;
                padding:12px 20px;
                background:#24547d;
                color:white;
                text-decoration:none;
                border-radius:8px;
            ">
                ← Về trang chủ
            </a>

        </div>

    </body>
    </html>
    """, 403


@app.context_processor
def inject_user():

    return {
        "current_user": session
    }


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            error = (
                "Vui lòng nhập đầy đủ "
                "tên đăng nhập và mật khẩu."
            )

            return render_template(
                "login.html",
                error=error
            )

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                username,
                password_hash,
                full_name,
                role
            FROM users
            WHERE username = %s
        """, (username,))

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user is None:

            error = (
                "Tên đăng nhập hoặc mật khẩu không đúng."
            )

            return render_template(
                "login.html",
                error=error
            )

        (
            user_id,
            db_username,
            password_hash,
            full_name,
            role
        ) = user

        try:

            password_correct = check_password_hash(
                password_hash,
                password
            )

        except Exception:

            password_correct = False

        if not password_correct:

            error = (
                "Tên đăng nhập hoặc mật khẩu không đúng."
            )

            return render_template(
                "login.html",
                error=error
            )

        session.clear()

        session["user_id"] = user_id
        session["username"] = db_username
        session["full_name"] = full_name
        session["role"] = role

        return redirect(url_for("index"))

    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def index():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM patients
    """)

    patient_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM doctors
    """)

    doctor_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM appointments
    """)

    appointment_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM services
    """)

    service_count = cur.fetchone()[0]

    try:

        cur.execute("""
            SELECT COUNT(*)
            FROM invoices
        """)

        invoice_count = cur.fetchone()[0]

    except Exception:

        conn.rollback()
        invoice_count = 0

    cur.execute("""
        SELECT
            a.id,
            a.appointment_date,
            a.status,
            a.reason,
            p.patient_code,
            p.full_name AS patient_name,
            d.doctor_code,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN patients p
            ON a.patient_id = p.id
        JOIN doctors d
            ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC
        LIMIT 10
    """)

    appointments = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        patient_count=patient_count,
        doctor_count=doctor_count,
        appointment_count=appointment_count,
        service_count=service_count,
        invoice_count=invoice_count,
        appointments=appointments
    )


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/db-test")
def db_test():

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                current_database(),
                current_user
        """)

        database, user = cur.fetchone()

        cur.close()
        conn.close()

        return jsonify({
            "status": "success",
            "database": database,
            "user": user
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =========================================================
# PATIENTS
# =========================================================

@app.route("/patients")
def patients():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()
    cur = conn.cursor()

    if search:

        keyword = f"%{search}%"

        cur.execute("""
            SELECT
                id,
                patient_code,
                full_name,
                date_of_birth,
                gender,
                phone,
                email,
                address
            FROM patients
            WHERE patient_code ILIKE %s
               OR full_name ILIKE %s
               OR phone ILIKE %s
               OR email ILIKE %s
            ORDER BY id DESC
        """, (
            keyword,
            keyword,
            keyword,
            keyword
        ))

    else:

        cur.execute("""
            SELECT
                id,
                patient_code,
                full_name,
                date_of_birth,
                gender,
                phone,
                email,
                address
            FROM patients
            ORDER BY id DESC
        """)

    patients_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "patients.html",
        patients=patients_data,
        search=search
    )


@app.route("/patients/add", methods=["GET", "POST"])
def add_patient():

    if request.method == "POST":

        patient_code = request.form.get(
            "patient_code",
            ""
        ).strip()

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        date_of_birth = (
            request.form.get("date_of_birth")
            or None
        )

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO patients
                (
                    patient_code,
                    full_name,
                    date_of_birth,
                    gender,
                    phone,
                    email,
                    address
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                patient_code,
                full_name,
                date_of_birth,
                gender,
                phone,
                email,
                address
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi thêm bệnh nhân: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("patients")
        )

    return render_template(
        "patient_form.html",
        patient=None
    )


@app.route("/patients/edit/<int:id>", methods=["GET", "POST"])
def edit_patient(id):

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        patient_code = request.form.get(
            "patient_code",
            ""
        ).strip()

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        date_of_birth = (
            request.form.get("date_of_birth")
            or None
        )

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        try:

            cur.execute("""
                UPDATE patients
                SET
                    patient_code = %s,
                    full_name = %s,
                    date_of_birth = %s,
                    gender = %s,
                    phone = %s,
                    email = %s,
                    address = %s
                WHERE id = %s
            """, (
                patient_code,
                full_name,
                date_of_birth,
                gender,
                phone,
                email,
                address,
                id
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi cập nhật bệnh nhân: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("patients")
        )

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name,
            date_of_birth,
            gender,
            phone,
            email,
            address
        FROM patients
        WHERE id = %s
    """, (id,))

    patient = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "patient_form.html",
        patient=patient
    )


@app.route("/patients/delete/<int:id>", methods=["POST"])
def delete_patient(id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM patients WHERE id = %s",
            (id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        cur.close()
        conn.close()

        return (
            f"Lỗi xóa bệnh nhân: {e}",
            400
        )

    cur.close()
    conn.close()

    return redirect(
        url_for("patients")
    )


# =========================================================
# DOCTORS
# =========================================================

@app.route("/doctors")
def doctors():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()
    cur = conn.cursor()

    if search:

        keyword = f"%{search}%"

        cur.execute("""
            SELECT
                id,
                doctor_code,
                full_name,
                specialty,
                phone,
                email
            FROM doctors
            WHERE doctor_code ILIKE %s
               OR full_name ILIKE %s
               OR specialty ILIKE %s
               OR phone ILIKE %s
            ORDER BY id DESC
        """, (
            keyword,
            keyword,
            keyword,
            keyword
        ))

    else:

        cur.execute("""
            SELECT
                id,
                doctor_code,
                full_name,
                specialty,
                phone,
                email
            FROM doctors
            ORDER BY id DESC
        """)

    doctors_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "doctors.html",
        doctors=doctors_data,
        search=search
    )


@app.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():

    if request.method == "POST":

        doctor_code = request.form.get(
            "doctor_code",
            ""
        ).strip()

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        specialty = request.form.get(
            "specialty",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO doctors
                (
                    doctor_code,
                    full_name,
                    specialty,
                    phone,
                    email
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                doctor_code,
                full_name,
                specialty,
                phone,
                email
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi thêm bác sĩ: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("doctors")
        )

    return render_template(
        "doctor_form.html",
        doctor=None
    )


@app.route("/doctors/edit/<int:id>", methods=["GET", "POST"])
def edit_doctor(id):

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        doctor_code = request.form.get(
            "doctor_code",
            ""
        ).strip()

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        specialty = request.form.get(
            "specialty",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        try:

            cur.execute("""
                UPDATE doctors
                SET
                    doctor_code = %s,
                    full_name = %s,
                    specialty = %s,
                    phone = %s,
                    email = %s
                WHERE id = %s
            """, (
                doctor_code,
                full_name,
                specialty,
                phone,
                email,
                id
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi cập nhật bác sĩ: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("doctors")
        )

    cur.execute("""
        SELECT
            id,
            doctor_code,
            full_name,
            specialty,
            phone,
            email
        FROM doctors
        WHERE id = %s
    """, (id,))

    doctor = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "doctor_form.html",
        doctor=doctor
    )


@app.route("/doctors/delete/<int:id>", methods=["POST"])
def delete_doctor(id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM doctors WHERE id = %s",
            (id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        cur.close()
        conn.close()

        return (
            f"Lỗi xóa bác sĩ: {e}",
            400
        )

    cur.close()
    conn.close()

    return redirect(
        url_for("doctors")
    )


# =========================================================
# APPOINTMENTS
# =========================================================

@app.route("/appointments")
def appointments():

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            a.id,
            a.appointment_date,
            a.status,
            a.reason,
            a.notes,
            p.patient_code,
            p.full_name AS patient_name,
            d.doctor_code,
            d.full_name AS doctor_name
        FROM appointments a
        JOIN patients p
            ON a.patient_id = p.id
        JOIN doctors d
            ON a.doctor_id = d.id
        WHERE 1 = 1
    """

    params = []

    if search:

        keyword = f"%{search}%"

        query += """
            AND (
                p.patient_code ILIKE %s
                OR p.full_name ILIKE %s
                OR d.doctor_code ILIKE %s
                OR d.full_name ILIKE %s
                OR a.reason ILIKE %s
            )
        """

        params.extend([
            keyword,
            keyword,
            keyword,
            keyword,
            keyword
        ])

    if status:

        query += """
            AND a.status = %s
        """

        params.append(status)

    query += """
        ORDER BY a.appointment_date DESC
    """

    cur.execute(query, params)

    appointments_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointments_data,
        search=search,
        status=status
    )


@app.route("/appointments/add", methods=["GET", "POST"])
def add_appointment():

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")

        status = request.form.get(
            "status",
            "scheduled"
        )

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        try:

            appointment_date = datetime.fromisoformat(
                appointment_date
            )

            cur.execute("""
                INSERT INTO appointments
                (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    status,
                    reason,
                    notes
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                patient_id,
                doctor_id,
                appointment_date,
                status,
                reason,
                notes
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi thêm lịch hẹn: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("appointments")
        )

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name
        FROM patients
        ORDER BY full_name
    """)

    patients_data = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            doctor_code,
            full_name
        FROM doctors
        ORDER BY full_name
    """)

    doctors_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "appointment_form.html",
        appointment=None,
        patients=patients_data,
        doctors=doctors_data
    )


@app.route("/appointments/edit/<int:id>", methods=["GET", "POST"])
def edit_appointment(id):

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")

        status = request.form.get(
            "status",
            "scheduled"
        )

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        try:

            appointment_date = datetime.fromisoformat(
                appointment_date
            )

            cur.execute("""
                UPDATE appointments
                SET
                    patient_id = %s,
                    doctor_id = %s,
                    appointment_date = %s,
                    status = %s,
                    reason = %s,
                    notes = %s
                WHERE id = %s
            """, (
                patient_id,
                doctor_id,
                appointment_date,
                status,
                reason,
                notes,
                id
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi cập nhật lịch hẹn: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("appointments")
        )

    cur.execute("""
        SELECT
            id,
            patient_id,
            doctor_id,
            appointment_date,
            status,
            reason,
            notes
        FROM appointments
        WHERE id = %s
    """, (id,))

    appointment = cur.fetchone()

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name
        FROM patients
        ORDER BY full_name
    """)

    patients_data = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            doctor_code,
            full_name
        FROM doctors
        ORDER BY full_name
    """)

    doctors_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "appointment_form.html",
        appointment=appointment,
        patients=patients_data,
        doctors=doctors_data
    )


@app.route("/appointments/delete/<int:id>", methods=["POST"])
def delete_appointment(id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM appointments WHERE id = %s",
            (id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        cur.close()
        conn.close()

        return (
            f"Lỗi xóa lịch hẹn: {e}",
            400
        )

    cur.close()
    conn.close()

    return redirect(
        url_for("appointments")
    )


# =========================================================
# MEDICAL RECORDS
# =========================================================

@app.route("/medical-records")
def medical_records():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()
    cur = conn.cursor()

    if search:

        keyword = f"%{search}%"

        cur.execute("""
            SELECT
                m.id,
                p.patient_code,
                p.full_name AS patient_name,
                d.doctor_code,
                d.full_name AS doctor_name,
                a.appointment_date,
                m.diagnosis,
                m.treatment,
                m.notes
            FROM medical_records m
            JOIN patients p
                ON m.patient_id = p.id
            JOIN doctors d
                ON m.doctor_id = d.id
            LEFT JOIN appointments a
                ON m.appointment_id = a.id
            WHERE
                p.patient_code ILIKE %s
                OR p.full_name ILIKE %s
                OR d.doctor_code ILIKE %s
                OR d.full_name ILIKE %s
                OR m.diagnosis ILIKE %s
                OR m.treatment ILIKE %s
                OR m.notes ILIKE %s
            ORDER BY m.id DESC
        """, (
            keyword,
            keyword,
            keyword,
            keyword,
            keyword,
            keyword,
            keyword
        ))

    else:

        cur.execute("""
            SELECT
                m.id,
                p.patient_code,
                p.full_name AS patient_name,
                d.doctor_code,
                d.full_name AS doctor_name,
                a.appointment_date,
                m.diagnosis,
                m.treatment,
                m.notes
            FROM medical_records m
            JOIN patients p
                ON m.patient_id = p.id
            JOIN doctors d
                ON m.doctor_id = d.id
            LEFT JOIN appointments a
                ON m.appointment_id = a.id
            ORDER BY m.id DESC
        """)

    records = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "medical_records.html",
        records=records,
        search=search
    )


@app.route(
    "/medical-records/add",
    methods=["GET", "POST"]
)
def add_medical_record():

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")

        appointment_id = (
            request.form.get("appointment_id")
            or None
        )

        diagnosis = request.form.get(
            "diagnosis",
            ""
        ).strip()

        treatment = request.form.get(
            "treatment",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        try:

            cur.execute("""
                INSERT INTO medical_records
                (
                    patient_id,
                    doctor_id,
                    appointment_id,
                    diagnosis,
                    treatment,
                    notes
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                patient_id,
                doctor_id,
                appointment_id,
                diagnosis,
                treatment,
                notes
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi thêm hồ sơ khám: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("medical_records")
        )

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name
        FROM patients
        ORDER BY full_name
    """)

    patients_data = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            doctor_code,
            full_name
        FROM doctors
        ORDER BY full_name
    """)

    doctors_data = cur.fetchall()

    cur.execute("""
        SELECT
            a.id,
            a.appointment_date,
            p.patient_code,
            p.full_name AS patient_name
        FROM appointments a
        JOIN patients p
            ON a.patient_id = p.id
        ORDER BY a.appointment_date DESC
    """)

    appointments_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "medical_record_form.html",
        record=None,
        patients=patients_data,
        doctors=doctors_data,
        appointments=appointments_data
    )


@app.route(
    "/medical-records/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_medical_record(id):

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")

        appointment_id = (
            request.form.get("appointment_id")
            or None
        )

        diagnosis = request.form.get(
            "diagnosis",
            ""
        ).strip()

        treatment = request.form.get(
            "treatment",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        try:

            cur.execute("""
                UPDATE medical_records
                SET
                    patient_id = %s,
                    doctor_id = %s,
                    appointment_id = %s,
                    diagnosis = %s,
                    treatment = %s,
                    notes = %s
                WHERE id = %s
            """, (
                patient_id,
                doctor_id,
                appointment_id,
                diagnosis,
                treatment,
                notes,
                id
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi cập nhật hồ sơ khám: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("medical_records")
        )

    cur.execute("""
        SELECT
            id,
            patient_id,
            doctor_id,
            appointment_id,
            diagnosis,
            treatment,
            notes
        FROM medical_records
        WHERE id = %s
    """, (id,))

    record = cur.fetchone()

    if not record:

        cur.close()
        conn.close()

        return (
            "Không tìm thấy hồ sơ khám.",
            404
        )

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name
        FROM patients
        ORDER BY full_name
    """)

    patients_data = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            doctor_code,
            full_name
        FROM doctors
        ORDER BY full_name
    """)

    doctors_data = cur.fetchall()

    cur.execute("""
        SELECT
            a.id,
            a.appointment_date,
            p.patient_code,
            p.full_name AS patient_name
        FROM appointments a
        JOIN patients p
            ON a.patient_id = p.id
        ORDER BY a.appointment_date DESC
    """)

    appointments_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "medical_record_form.html",
        record=record,
        patients=patients_data,
        doctors=doctors_data,
        appointments=appointments_data
    )


@app.route(
    "/medical-records/delete/<int:id>",
    methods=["POST"]
)
def delete_medical_record(id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM medical_records WHERE id = %s",
            (id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        cur.close()
        conn.close()

        return (
            f"Lỗi xóa hồ sơ khám: {e}",
            400
        )

    cur.close()
    conn.close()

    return redirect(
        url_for("medical_records")
    )


# =========================================================
# SERVICES
# =========================================================

@app.route("/services")
def services():

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()
    cur = conn.cursor()

    if search:

        keyword = f"%{search}%"

        cur.execute("""
            SELECT
                id,
                service_code,
                service_name,
                description,
                price
            FROM services
            WHERE service_code ILIKE %s
               OR service_name ILIKE %s
               OR description ILIKE %s
            ORDER BY id DESC
        """, (
            keyword,
            keyword,
            keyword
        ))

    else:

        cur.execute("""
            SELECT
                id,
                service_code,
                service_name,
                description,
                price
            FROM services
            ORDER BY id DESC
        """)

    services_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "services.html",
        services=services_data,
        search=search
    )


@app.route(
    "/services/add",
    methods=["GET", "POST"]
)
def add_service():

    if request.method == "POST":

        service_code = request.form.get(
            "service_code",
            ""
        ).strip()

        service_name = request.form.get(
            "service_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()

        try:

            price = float(price)

            if price < 0:
                return (
                    "Giá dịch vụ không được âm.",
                    400
                )

        except ValueError:

            return (
                "Giá dịch vụ không hợp lệ.",
                400
            )

        conn = get_db_connection()
        cur = conn.cursor()

        try:

            cur.execute("""
                INSERT INTO services
                (
                    service_code,
                    service_name,
                    description,
                    price
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                service_code,
                service_name,
                description,
                price
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi thêm dịch vụ: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("services")
        )

    return render_template(
        "service_form.html",
        service=None
    )


@app.route(
    "/services/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_service(id):

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        service_code = request.form.get(
            "service_code",
            ""
        ).strip()

        service_name = request.form.get(
            "service_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            "0"
        ).strip()

        try:

            price = float(price)

            if price < 0:
                return (
                    "Giá dịch vụ không được âm.",
                    400
                )

        except ValueError:

            return (
                "Giá dịch vụ không hợp lệ.",
                400
            )

        try:

            cur.execute("""
                UPDATE services
                SET
                    service_code = %s,
                    service_name = %s,
                    description = %s,
                    price = %s
                WHERE id = %s
            """, (
                service_code,
                service_name,
                description,
                price,
                id
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi cập nhật dịch vụ: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("services")
        )

    cur.execute("""
        SELECT
            id,
            service_code,
            service_name,
            description,
            price
        FROM services
        WHERE id = %s
    """, (id,))

    service = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        "service_form.html",
        service=service
    )


@app.route(
    "/services/delete/<int:id>",
    methods=["POST"]
)
def delete_service(id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM services WHERE id = %s",
            (id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        cur.close()
        conn.close()

        return (
            f"Lỗi xóa dịch vụ: {e}",
            400
        )

    cur.close()
    conn.close()

    return redirect(
        url_for("services")
    )


# =========================================================
# INVOICES
# =========================================================

@app.route("/invoices")
def invoices():

    search = request.args.get(
        "search",
        ""
    ).strip()

    payment_status = request.args.get(
        "payment_status",
        ""
    ).strip()

    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            i.id,
            i.invoice_code,
            p.patient_code,
            p.full_name AS patient_name,
            s.service_code,
            s.service_name,
            i.quantity,
            i.unit_price,
            i.total_amount,
            i.payment_status,
            i.payment_date,
            i.notes,
            i.created_at
        FROM invoices i
        JOIN patients p
            ON i.patient_id = p.id
        JOIN services s
            ON i.service_id = s.id
        WHERE 1 = 1
    """

    params = []

    if search:

        keyword = f"%{search}%"

        query += """
            AND (
                i.invoice_code ILIKE %s
                OR p.patient_code ILIKE %s
                OR p.full_name ILIKE %s
                OR s.service_code ILIKE %s
                OR s.service_name ILIKE %s
            )
        """

        params.extend([
            keyword,
            keyword,
            keyword,
            keyword,
            keyword
        ])

    if payment_status:

        query += """
            AND i.payment_status = %s
        """

        params.append(payment_status)

    query += """
        ORDER BY i.id DESC
    """

    cur.execute(
        query,
        params
    )

    invoices_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "invoices.html",
        invoices=invoices_data,
        search=search,
        payment_status=payment_status
    )


@app.route(
    "/invoices/add",
    methods=["GET", "POST"]
)
def add_invoice():

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        invoice_code = request.form.get(
            "invoice_code",
            ""
        ).strip()

        patient_id = request.form.get("patient_id")
        service_id = request.form.get("service_id")

        quantity = request.form.get(
            "quantity",
            "1"
        )

        payment_status = request.form.get(
            "payment_status",
            "unpaid"
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if not invoice_code:

            cur.close()
            conn.close()

            return (
                "Mã hóa đơn không được để trống.",
                400
            )

        try:

            quantity = int(quantity)

            if quantity < 1:
                raise ValueError

        except ValueError:

            cur.close()
            conn.close()

            return (
                "Số lượng phải là số nguyên lớn hơn hoặc bằng 1.",
                400
            )

        allowed_statuses = [
            "unpaid",
            "paid",
            "cancelled"
        ]

        if payment_status not in allowed_statuses:

            cur.close()
            conn.close()

            return (
                "Trạng thái thanh toán không hợp lệ.",
                400
            )

        try:

            cur.execute("""
                SELECT price
                FROM services
                WHERE id = %s
            """, (service_id,))

            service = cur.fetchone()

            if not service:
                raise ValueError(
                    "Không tìm thấy dịch vụ."
                )

            unit_price = float(service[0])

            total_amount = unit_price * quantity

            if payment_status == "paid":
                payment_date = datetime.now()
            else:
                payment_date = None

            cur.execute("""
                INSERT INTO invoices
                (
                    invoice_code,
                    patient_id,
                    service_id,
                    quantity,
                    unit_price,
                    total_amount,
                    payment_status,
                    payment_date,
                    notes
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                invoice_code,
                patient_id,
                service_id,
                quantity,
                unit_price,
                total_amount,
                payment_status,
                payment_date,
                notes
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi thêm hóa đơn: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("invoices")
        )

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name
        FROM patients
        ORDER BY full_name
    """)

    patients_data = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            service_code,
            service_name,
            price
        FROM services
        ORDER BY service_name
    """)

    services_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "invoice_form.html",
        invoice=None,
        patients=patients_data,
        services=services_data
    )


@app.route(
    "/invoices/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_invoice(id):

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":

        invoice_code = request.form.get(
            "invoice_code",
            ""
        ).strip()

        patient_id = request.form.get("patient_id")
        service_id = request.form.get("service_id")

        quantity = request.form.get(
            "quantity",
            "1"
        )

        payment_status = request.form.get(
            "payment_status",
            "unpaid"
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if not invoice_code:

            cur.close()
            conn.close()

            return (
                "Mã hóa đơn không được để trống.",
                400
            )

        try:

            quantity = int(quantity)

            if quantity < 1:
                raise ValueError

        except ValueError:

            cur.close()
            conn.close()

            return (
                "Số lượng phải là số nguyên lớn hơn hoặc bằng 1.",
                400
            )

        allowed_statuses = [
            "unpaid",
            "paid",
            "cancelled"
        ]

        if payment_status not in allowed_statuses:

            cur.close()
            conn.close()

            return (
                "Trạng thái thanh toán không hợp lệ.",
                400
            )

        try:

            cur.execute("""
                SELECT price
                FROM services
                WHERE id = %s
            """, (service_id,))

            service = cur.fetchone()

            if not service:
                raise ValueError(
                    "Không tìm thấy dịch vụ."
                )

            unit_price = float(service[0])

            total_amount = unit_price * quantity

            if payment_status == "paid":
                payment_date = datetime.now()
            else:
                payment_date = None

            cur.execute("""
                UPDATE invoices
                SET
                    invoice_code = %s,
                    patient_id = %s,
                    service_id = %s,
                    quantity = %s,
                    unit_price = %s,
                    total_amount = %s,
                    payment_status = %s,
                    payment_date = %s,
                    notes = %s
                WHERE id = %s
            """, (
                invoice_code,
                patient_id,
                service_id,
                quantity,
                unit_price,
                total_amount,
                payment_status,
                payment_date,
                notes,
                id
            ))

            conn.commit()

        except Exception as e:

            conn.rollback()
            cur.close()
            conn.close()

            return (
                f"Lỗi cập nhật hóa đơn: {e}",
                400
            )

        cur.close()
        conn.close()

        return redirect(
            url_for("invoices")
        )

    cur.execute("""
        SELECT
            id,
            invoice_code,
            patient_id,
            service_id,
            quantity,
            unit_price,
            total_amount,
            payment_status,
            payment_date,
            notes
        FROM invoices
        WHERE id = %s
    """, (id,))

    invoice = cur.fetchone()

    if not invoice:

        cur.close()
        conn.close()

        return (
            "Không tìm thấy hóa đơn.",
            404
        )

    cur.execute("""
        SELECT
            id,
            patient_code,
            full_name
        FROM patients
        ORDER BY full_name
    """)

    patients_data = cur.fetchall()

    cur.execute("""
        SELECT
            id,
            service_code,
            service_name,
            price
        FROM services
        ORDER BY service_name
    """)

    services_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "invoice_form.html",
        invoice=invoice,
        patients=patients_data,
        services=services_data
    )


@app.route(
    "/invoices/delete/<int:id>",
    methods=["POST"]
)
def delete_invoice(id):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "DELETE FROM invoices WHERE id = %s",
            (id,)
        )

        conn.commit()

    except Exception as e:

        conn.rollback()
        cur.close()
        conn.close()

        return (
            f"Lỗi xóa hóa đơn: {e}",
            400
        )

    cur.close()
    conn.close()

    return redirect(
        url_for("invoices")
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )