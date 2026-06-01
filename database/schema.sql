-- ============================================================
-- Schema: Hệ Thống Quản Lý Ký Túc Xá (Merged Students & Contracts)
-- DB: SQLite 3
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    full_name     TEXT,
    role          TEXT    CHECK(role IN ('admin', 'staff')) DEFAULT 'staff',
    is_active     INTEGER DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    UNIQUE NOT NULL,
    description TEXT,
    gender_type TEXT    CHECK(gender_type IN ('Nam', 'Nữ', 'Hỗn hợp')) DEFAULT 'Hỗn hợp',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number     TEXT    UNIQUE NOT NULL,
    building        TEXT    NOT NULL,
    floor           INTEGER NOT NULL CHECK(floor > 0),
    capacity        INTEGER NOT NULL CHECK(capacity IN (2, 4, 6)),
    room_type       TEXT,
    price_per_month REAL    NOT NULL CHECK(price_per_month > 0),
    status          TEXT    CHECK(status IN ('available','full','maintenance'))
                            DEFAULT 'available',
    zone_id         INTEGER REFERENCES zones(id) ON DELETE SET NULL,
    description     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name        TEXT    NOT NULL,
    id_card          TEXT    UNIQUE NOT NULL, -- CCCD/CMND thay cho MSSV
    date_of_birth    DATE,
    gender           TEXT    CHECK(gender IN ('Nam', 'Nữ', 'Khác')),
    faculty          TEXT,
    class_name       TEXT,
    phone            TEXT,
    email            TEXT,
    hometown_address TEXT,
    
    -- Các trường thay thế Hợp đồng (Contract)
    room_id          INTEGER REFERENCES rooms(id),
    bed_number       INTEGER CHECK(bed_number > 0 OR bed_number IS NULL),
    checkin_date     DATE,
    checkout_date    DATE,
    deposit          REAL    DEFAULT 0,
    residency_status TEXT    CHECK(residency_status IN ('active', 'left', 'none')) DEFAULT 'none',
    
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fees (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id          INTEGER NOT NULL REFERENCES rooms(id),
    month            INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year             INTEGER NOT NULL CHECK(year >= 2020),

    -- Điện: tính theo công tơ
    elec_prev_reading  REAL    DEFAULT NULL,  -- Chỉ số đầu kỳ (kWh)
    elec_curr_reading  REAL    DEFAULT NULL,  -- Chỉ số cuối kỳ (kWh)
    elec_unit_price    REAL    DEFAULT 3500,  -- Đơn giá ₫/kWh
    electricity_fee    REAL    DEFAULT 0,     -- Tổng tiền điện (kết quả)

    -- Nước: tính theo đầu người
    water_cubic_meters REAL    DEFAULT NULL,  -- Tổng m³ cả phòng
    water_unit_price   REAL    DEFAULT 15000, -- Đơn giá ₫/m³
    water_num_persons  INTEGER DEFAULT NULL,  -- Số người chia (snapshot)
    water_fee          REAL    DEFAULT 0,     -- Tổng tiền nước cả phòng (kết quả)

    service_fee      REAL    DEFAULT 0,
    room_fee         REAL    DEFAULT 0,       -- Tổng thu tiền giường của cả phòng
    total_amount     REAL    NOT NULL,
    paid_amount      REAL    DEFAULT 0,
    paid_date        DATE,
    status           TEXT    CHECK(status IN ('unpaid','partial','paid'))
                             DEFAULT 'unpaid',
    notes            TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(room_id, month, year)
);

CREATE TABLE IF NOT EXISTS violations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id     INTEGER NOT NULL REFERENCES students(id),
    violation_type TEXT    NOT NULL,
    description    TEXT,
    violation_date DATE    NOT NULL,
    fine_amount    REAL    DEFAULT 0,
    is_paid        INTEGER DEFAULT 0 CHECK(is_paid IN (0, 1)),
    recorded_by    INTEGER REFERENCES users(id),
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_name     ON students(full_name);
CREATE INDEX IF NOT EXISTS idx_students_cccd     ON students(id_card);
CREATE INDEX IF NOT EXISTS idx_students_room     ON students(room_id);
CREATE INDEX IF NOT EXISTS idx_rooms_status      ON rooms(status);
CREATE INDEX IF NOT EXISTS idx_rooms_zone        ON rooms(zone_id);
CREATE INDEX IF NOT EXISTS idx_fees_status       ON fees(status);
CREATE INDEX IF NOT EXISTS idx_fees_year_month   ON fees(year, month);

-- Views
CREATE VIEW IF NOT EXISTS v_available_rooms AS
SELECT r.*, z.name AS zone_name,
       (r.capacity - COUNT(s.id)) AS available_beds
FROM rooms r
LEFT JOIN zones z ON r.zone_id = z.id
LEFT JOIN students s ON r.id = s.room_id AND s.residency_status = 'active'
WHERE r.status = 'available'
GROUP BY r.id
HAVING available_beds > 0;

CREATE VIEW IF NOT EXISTS v_current_residents AS
SELECT s.id_card, s.full_name, s.phone, s.faculty,
       r.room_number, r.building, z.name AS zone_name,
       s.checkin_date, s.checkout_date, s.bed_number
FROM students s
JOIN rooms r ON s.room_id = r.id
LEFT JOIN zones z ON r.zone_id = z.id
WHERE s.residency_status = 'active';

CREATE VIEW IF NOT EXISTS v_unpaid_fees AS
SELECT
    f.id,
    r.room_number,
    r.building,
    z.name AS zone_name,
    f.month,
    f.year,
    f.total_amount,
    f.paid_amount,
    (f.total_amount - f.paid_amount) AS remaining,
    f.status
FROM fees f
JOIN rooms r ON f.room_id = r.id
LEFT JOIN zones z ON r.zone_id = z.id
WHERE f.status != 'paid';
