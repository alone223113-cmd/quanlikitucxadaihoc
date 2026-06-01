"""
database/db.py — Kết nối & khởi tạo SQLite database cho KTX Manager
"""
import sqlite3
import os
import bcrypt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "ktx.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def initialize_database():
    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = f.read()

        _execute_schema(conn, schema)
        _seed_default_data(conn)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _execute_schema(conn: sqlite3.Connection, schema: str):
    statements = [s.strip() for s in schema.split(";") if s.strip()]
    for stmt in statements:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                pass
            else:
                print(f"[DB Warning] {e}: {stmt[:80]}")

    # Migration: them zone_id vao rooms neu chua co
    cols = [r[1] for r in conn.execute("PRAGMA table_info(rooms)").fetchall()]
    if "zone_id" not in cols:
        try:
            conn.execute("ALTER TABLE rooms ADD COLUMN zone_id INTEGER REFERENCES zones(id)")
            print("[DB Migration] Da them cot zone_id vao bang rooms.")
        except sqlite3.OperationalError as e:
            print(f"[DB Migration Warning] {e}")

    # Migration: them cac cot dien/nuoc moi vao fees neu chua co
    fee_cols = [r[1] for r in conn.execute("PRAGMA table_info(fees)").fetchall()]
    _fee_new_cols = [
        ("elec_prev_reading",  "ALTER TABLE fees ADD COLUMN elec_prev_reading  REAL    DEFAULT NULL"),
        ("elec_curr_reading",  "ALTER TABLE fees ADD COLUMN elec_curr_reading  REAL    DEFAULT NULL"),
        ("elec_unit_price",    "ALTER TABLE fees ADD COLUMN elec_unit_price    REAL    DEFAULT 3500"),
        ("water_cubic_meters", "ALTER TABLE fees ADD COLUMN water_cubic_meters REAL    DEFAULT NULL"),
        ("water_unit_price",   "ALTER TABLE fees ADD COLUMN water_unit_price   REAL    DEFAULT 15000"),
        ("water_num_persons",  "ALTER TABLE fees ADD COLUMN water_num_persons  INTEGER DEFAULT NULL"),
    ]
    for col_name, alter_stmt in _fee_new_cols:
        if col_name not in fee_cols:
            try:
                conn.execute(alter_stmt)
                print(f"[DB Migration] Da them cot {col_name} vao bang fees.")
            except sqlite3.OperationalError as e:
                print(f"[DB Migration Warning] {e}")

def _seed_default_data(conn: sqlite3.Connection):
    row = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not row:
        admin_pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        staff_pw = bcrypt.hashpw(b"123456", bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ("admin", admin_pw, "Admin", "admin"),
        )
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ("nhanvien", staff_pw, "Trần Thị Nhân Viên", "staff"),
        )

    # Seed zones
    zone_count = conn.execute("SELECT COUNT(*) as c FROM zones").fetchone()["c"]
    if zone_count == 0:
        sample_zones = [
            ("Khu A", "Khu hỗn hợp toà A", "Hỗn hợp"),
            ("Khu B", "Khu dành cho Nam toà B", "Nam"),
            ("Khu C", "Khu dành cho Nữ toà C", "Nữ"),
        ]
        conn.executemany(
            "INSERT INTO zones (name, description, gender_type) VALUES (?,?,?)",
            sample_zones,
        )

    rows = conn.execute("SELECT COUNT(*) as c FROM rooms").fetchone()
    if rows["c"] == 0:
        # Lấy zone_id để gán
        zones = {z["name"]: z["id"] for z in conn.execute("SELECT id, name FROM zones").fetchall()}
        sample_rooms = [
            ("A101", "A", 1, 4, "Phòng 4 người", 500000, "full",      zones.get("Khu A")),
            ("A102", "A", 1, 4, "Phòng 4 người", 500000, "available", zones.get("Khu A")),
            ("A103", "A", 1, 4, "Phòng 4 người", 500000, "available", zones.get("Khu A")),
            ("B201", "B", 2, 6, "Phòng 6 người", 400000, "available", zones.get("Khu B")),
            ("B202", "B", 2, 6, "Phòng 6 người", 400000, "full",      zones.get("Khu B")),
            ("B203", "B", 2, 2, "Phòng 2 người", 700000, "available", zones.get("Khu B")),
            ("C101", "C", 1, 4, "Phòng 4 người", 550000, "available", zones.get("Khu C")),
            ("C102", "C", 1, 4, "Phòng 4 người", 550000, "maintenance",zones.get("Khu C")),
        ]
        conn.executemany(
            "INSERT INTO rooms (room_number, building, floor, capacity, room_type, price_per_month, status, zone_id) VALUES (?,?,?,?,?,?,?,?)",
            sample_rooms,
        )
    else:
        # Migration: gán zone_id cho phòng cũ chưa có zone
        zones = {z["name"]: z["id"] for z in conn.execute("SELECT id, name FROM zones").fetchall()}
        for building, zone_name in [("A", "Khu A"), ("B", "Khu B"), ("C", "Khu C")]:
            zid = zones.get(zone_name)
            if zid:
                conn.execute(
                    "UPDATE rooms SET zone_id = ? WHERE building = ? AND zone_id IS NULL",
                    (zid, building),
                )

    rows = conn.execute("SELECT COUNT(*) as c FROM students").fetchone()
    if rows["c"] == 0:
        rm_ids = {r["room_number"]: r["id"] for r in conn.execute("SELECT id, room_number FROM rooms").fetchall()}
        
        sample_students = [
            ("Nguyễn Văn An", "001234567890", "2003-05-15", "Nam", "CNTT", "CNTT01", "0912345678", "an.nv@email.com", "Hà Nội", rm_ids.get("A101"), 1, "2025-09-01", "2026-06-30", 500000, "active"),
            ("Trần Thị Bình", "001234567891", "2004-03-22", "Nữ", "KT", "KT02", "0987654321", "binh.tt@email.com", "Hải Phòng", rm_ids.get("B201"), 2, "2025-09-01", "2026-06-30", 400000, "active"),
            ("Lê Văn Cường", "001234567892", "2003-11-08", "Nam", "Cơ khí", "CK01", "0978123456", "cuong.lv@email.com", "Nam Định", rm_ids.get("A101"), 2, "2025-09-01", "2026-06-30", 500000, "active"),
            ("Phạm Thị Dung", "001234567893", "2004-07-19", "Nữ", "CNTT", "CNTT02", "0965432109", "dung.pt@email.com", "Thái Bình", rm_ids.get("A101"), 3, "2025-09-01", "2026-06-30", 500000, "active"),
            ("Hoàng Văn Em", "001234567894", "2003-01-30", "Nam", "Điện tử", "DD01", "0923456789", "em.hv@email.com", "Nghệ An", rm_ids.get("A101"), 4, "2025-09-01", "2026-06-30", 500000, "active"),
            ("Vũ Thị Phương", "001234567895", "2004-09-12", "Nữ", "QTKD", "QTKD01", "0912987654", "phuong.vt@email.com", "Hà Tĩnh", rm_ids.get("B202"), 1, "2025-09-01", "2026-06-30", 400000, "active"),
        ]
        
        conn.executemany(
            """INSERT INTO students (full_name, id_card, date_of_birth, gender, faculty, class_name, phone, email, hometown_address,
               room_id, bed_number, checkin_date, checkout_date, deposit, residency_status) 
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            sample_students,
        )

    rows = conn.execute("SELECT COUNT(*) as c FROM fees").fetchone()
    if rows["c"] == 0:
        rooms = conn.execute("SELECT id, room_number, price_per_month FROM rooms WHERE status != 'maintenance'").fetchall()
        import random
        for r in rooms:
            sv_count = conn.execute("SELECT COUNT(*) as c FROM students WHERE room_id = ? AND residency_status = 'active'", (r["id"],)).fetchone()["c"]
            if sv_count == 0: continue
            
            for month in [2, 3, 4]:
                elec = random.randint(50000, 120000)
                water = random.randint(30000, 60000)
                service = sv_count * 20000
                room_f = sv_count * r["price_per_month"]
                total = room_f + elec + water + service
                paid = total if month < 4 else 0
                status = "paid" if month < 4 else "unpaid"
                try:
                    conn.execute(
                        """INSERT INTO fees (room_id, month, year, room_fee, electricity_fee, water_fee, service_fee, total_amount, paid_amount, status) 
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (r["id"], month, 2026, room_f, elec, water, service, total, paid, status),
                    )
                except sqlite3.IntegrityError:
                    pass

    rows = conn.execute("SELECT COUNT(*) as c FROM violations").fetchone()
    if rows["c"] == 0:
        sv_ids = [r["id"] for r in conn.execute("SELECT id FROM students LIMIT 3").fetchall()]
        if sv_ids:
            admin_id = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchone()["id"]
            sample_vio = [
                (sv_ids[0], "Về trễ giờ quy định", "Về sau 23:00", "2026-04-10", 50000, 0, admin_id),
                (sv_ids[1] if len(sv_ids)>1 else sv_ids[0], "Gây ồn ào sau 22h", "Mở nhạc to gây ảnh hưởng", "2026-04-12", 100000, 1, admin_id),
                (sv_ids[2] if len(sv_ids)>2 else sv_ids[0], "Hút thuốc trong phòng", "Vi phạm nội quy phòng ở", "2026-04-08", 150000, 0, admin_id),
            ]
            conn.executemany(
                "INSERT INTO violations (student_id, violation_type, description, violation_date, fine_amount, is_paid, recorded_by) VALUES (?,?,?,?,?,?,?)",
                sample_vio,
            )

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
