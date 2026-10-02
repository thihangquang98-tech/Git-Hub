-- =========================================================
-- DATABASE: DENTAL CLINIC MANAGEMENT SYSTEM
-- =========================================================

-- =========================
-- 1. USERS
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'receptionist',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2. PATIENTS
-- =========================
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    patient_code VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 3. DOCTORS
-- =========================
CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    doctor_code VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 4. DENTAL SERVICES
-- =========================
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    service_code VARCHAR(20) UNIQUE NOT NULL,
    service_name VARCHAR(150) NOT NULL,
    description TEXT,
    price NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 5. APPOINTMENTS
-- =========================
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,

    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,

    appointment_date TIMESTAMP NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'scheduled',

    reason TEXT,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_appointment_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_appointment_doctor
        FOREIGN KEY (doctor_id)
        REFERENCES doctors(id)
        ON DELETE CASCADE
);

-- =========================
-- 6. MEDICAL RECORDS
-- =========================
CREATE TABLE IF NOT EXISTS medical_records (
    id SERIAL PRIMARY KEY,

    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_id INTEGER,

    diagnosis TEXT,
    treatment TEXT,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_record_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_record_doctor
        FOREIGN KEY (doctor_id)
        REFERENCES doctors(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_record_appointment
        FOREIGN KEY (appointment_id)
        REFERENCES appointments(id)
        ON DELETE SET NULL
);

-- =========================
-- SAMPLE USERS
-- =========================
INSERT INTO users
(username, password_hash, full_name, role)
VALUES
('admin', 'admin123', 'Quản trị viên', 'admin'),
('reception', 'reception123', 'Nhân viên lễ tân', 'receptionist'),
('doctor01', 'doctor123', 'Bác sĩ Nguyễn Văn A', 'doctor')
ON CONFLICT (username) DO NOTHING;

-- =========================
-- SAMPLE DOCTORS
-- =========================
INSERT INTO doctors
(doctor_code, full_name, specialty, phone, email)
VALUES
('BS001', 'Nguyễn Văn A', 'Nha khoa tổng quát', '0901000001', 'doctor1@dental.local'),
('BS002', 'Trần Thị B', 'Chỉnh nha', '0901000002', 'doctor2@dental.local'),
('BS003', 'Lê Văn C', 'Nha khoa thẩm mỹ', '0901000003', 'doctor3@dental.local')
ON CONFLICT (doctor_code) DO NOTHING;

-- =========================
-- SAMPLE SERVICES
-- =========================
INSERT INTO services
(service_code, service_name, description, price)
VALUES
('DV001', 'Khám răng tổng quát', 'Kiểm tra tình trạng răng miệng', 100000),
('DV002', 'Lấy cao răng', 'Vệ sinh và lấy cao răng', 200000),
('DV003', 'Trám răng', 'Trám răng sâu hoặc răng bị tổn thương', 300000),
('DV004', 'Nhổ răng', 'Nhổ răng theo chỉ định của bác sĩ', 500000),
('DV005', 'Tẩy trắng răng', 'Dịch vụ tẩy trắng răng thẩm mỹ', 1500000),
('DV006', 'Niềng răng', 'Tư vấn và điều trị chỉnh nha', 30000000)
ON CONFLICT (service_code) DO NOTHING;

-- =========================
-- SAMPLE PATIENTS
-- =========================
INSERT INTO patients
(patient_code, full_name, date_of_birth, gender, phone, email, address)
VALUES
('BN001', 'Nguyễn Thị Lan', '2000-05-15', 'Nữ',
 '0912000001', 'lan@gmail.com', 'Thái Nguyên'),

('BN002', 'Trần Văn Nam', '1998-08-20', 'Nam',
 '0912000002', 'nam@gmail.com', 'Hà Nội'),

('BN003', 'Lê Minh Anh', '2005-02-10', 'Nữ',
 '0912000003', 'anh@gmail.com', 'Thái Nguyên')
ON CONFLICT (patient_code) DO NOTHING;

-- =========================
-- SAMPLE APPOINTMENTS
-- =========================
INSERT INTO appointments
(patient_id, doctor_id, appointment_date, status, reason, notes)
VALUES
(
    1,
    1,
    CURRENT_TIMESTAMP + INTERVAL '1 day',
    'scheduled',
    'Khám răng tổng quát',
    'Bệnh nhân đặt lịch khám lần đầu'
),
(
    2,
    2,
    CURRENT_TIMESTAMP + INTERVAL '2 days',
    'scheduled',
    'Tư vấn chỉnh nha',
    'Tư vấn niềng răng'
);

-- =========================
-- SAMPLE MEDICAL RECORD
-- =========================
INSERT INTO medical_records
(patient_id, doctor_id, appointment_id, diagnosis, treatment, notes)
VALUES
(
    1,
    1,
    1,
    'Sâu răng nhẹ',
    'Trám răng',
    'Cần tái khám sau 6 tháng'
);