import psycopg2
from werkzeug.security import generate_password_hash


# Kết nối PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="dental_clinic",
    user="clinic_user",
    password="clinic_password"
)

cur = conn.cursor()


# Danh sách tài khoản
users = [
    (
        "admin",
        "Admin@123",
        "Quản lý phòng khám",
        "manager"
    ),
    (
        "doctor01",
        "Doctor@123",
        "Bác sĩ Nguyễn Văn A",
        "doctor"
    ),
    (
        "letan01",
        "LeTan@123",
        "Nhân viên lễ tân",
        "receptionist"
    )
]


for username, password, full_name, role in users:

    password_hash = generate_password_hash(password)

    cur.execute("""
        INSERT INTO users
        (
            username,
            password_hash,
            full_name,
            role
        )
        VALUES (%s, %s, %s, %s)

        ON CONFLICT (username)
        DO UPDATE SET
            password_hash = EXCLUDED.password_hash,
            full_name = EXCLUDED.full_name,
            role = EXCLUDED.role
    """, (
        username,
        password_hash,
        full_name,
        role
    ))


conn.commit()


print()
print("========================================")
print(" ĐÃ TẠO / CẬP NHẬT TÀI KHOẢN")
print("========================================")
print()
print("Quản lý:")
print("  Username: admin")
print("  Password: Admin@123")
print()
print("Bác sĩ:")
print("  Username: doctor01")
print("  Password: Doctor@123")
print()
print("Lễ tân:")
print("  Username: letan01")
print("  Password: LeTan@123")
print()
print("========================================")


cur.close()
conn.close()