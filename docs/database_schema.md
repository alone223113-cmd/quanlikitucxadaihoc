# Thiết Kế Cơ Sở Dữ Liệu — Hệ Thống Quản Lý KTX

> **Hệ quản trị CSDL:** SQLite 3 (tích hợp sẵn trong Python)  
> **Charset:** UTF-8  
> **Ngày thiết kế:** 14/04/2026

---

## 1. Sơ Đồ Quan Hệ (ERD)

```
┌─────────────┐        ┌──────────────────┐        ┌─────────────┐
│    users    │        │    contracts     │        │    rooms    │
├─────────────┤        ├──────────────────┤        ├─────────────┤
│ id (PK)     │        │ id (PK)          │        │ id (PK)     │
│ username    │        │ student_id (FK)──┼──┐     │ room_number │
│ password_   │        │ room_id (FK) ────┼──┼─────│ building    │
│   hash      │        │ bed_number       │  │     │ floor       │
│ full_name   │        │ start_date       │  │     │ capacity    │
│ role        │        │ end_date         │  │     │ room_type   │
│ created_at  │        │ deposit          │  │     │ price_per_  │
└─────────────┘        │ status           │  │     │   month     │
       │               │ notes            │  │     │ status      │
       │               │ created_at       │  │     │ description │
       │               └──────────────────┘  │     └─────────────┘
       │                        │            │
       │                    has │            │
       │                        ▼            │
       │               ┌──────────────────┐  │
       │               │      fees        │  │
       │               ├──────────────────┤  │
       │               │ id (PK)          │  │
       │               │ contract_id (FK) │  │
       │               │ month            │  │
       │               │ year             │  │
       │               │ room_fee         │  │
       │               │ electricity_fee  │  │
       │               │ water_fee        │  │
       │               │ service_fee      │  │
       │               │ total_amount     │  │
       │               │ paid_amount      │  │
       │               │ paid_date        │  │
       │               │ status           │  │
       │               │ notes            │  │
       │               └──────────────────┘  │
       │                                     │
       │                             has  ┌──┘
       │                                  ▼
       │                        ┌──────────────────┐
       │                        │    students      │
       │                        ├──────────────────┤
       │                        │ id (PK)          │
       │    recorded_by         │ student_id       │
       │    ┌───────────────────│ full_name        │
       │    │                   │ id_card          │
       ▼    ▼                   │ date_of_birth    │
┌──────────────────┐            │ gender           │
│   violations     │            │ faculty          │
├──────────────────┤            │ class_name       │
│ id (PK)          │            │ phone            │
│ student_id (FK)──┼────────────│ email            │
│ violation_type   │            │ hometown_address │
│ description      │            │ created_at       │
│ violation_date   │            └──────────────────┘
│ fine_amount      │
│ is_paid          │
│ recorded_by (FK) │
│ created_at       │
└──────────────────┘
```

---

## 2. Chi Tiết Các Bảng

---

### Bảng `users` — Tài Khoản Hệ Thống

**Mô tả:** Lưu trữ thông tin tài khoản đăng nhập của quản lý viên và nhân viên.

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    full_name     TEXT,
    role          TEXT    CHECK(role IN ('admin', 'staff')) DEFAULT 'staff',
    is_active     INTEGER DEFAULT 1,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INTEGER | PK, Auto | Mã tài khoản |
| `username` | TEXT | UNIQUE, NOT NULL | Tên đăng nhập |
| `password_hash` | TEXT | NOT NULL | Mật khẩu đã mã hóa (bcrypt) |
| `full_name` | TEXT | | Họ và tên đầy đủ |
| `role` | TEXT | CHECK | `admin` hoặc `staff` |
| `is_active` | INTEGER | DEFAULT 1 | 1=Hoạt động, 0=Vô hiệu |
| `created_at` | DATETIME | DEFAULT | Thời điểm tạo |

**Dữ liệu mẫu:**
```sql
INSERT INTO users (username, password_hash, full_name, role) VALUES
('admin', '<hash_of_admin123>', 'Nguyễn Văn A', 'admin'),
('nhanvien1', '<hash_of_123456>', 'Trần Thị B', 'staff');
```

---

### Bảng `rooms` — Phòng KTX

**Mô tả:** Thông tin về các phòng ở trong KTX.

```sql
CREATE TABLE rooms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number     TEXT    UNIQUE NOT NULL,
    building        TEXT    NOT NULL,
    floor           INTEGER NOT NULL CHECK(floor > 0),
    capacity        INTEGER NOT NULL CHECK(capacity IN (2, 4, 6)),
    room_type       TEXT,
    price_per_month REAL    NOT NULL CHECK(price_per_month > 0),
    status          TEXT    CHECK(status IN ('available','full','maintenance'))
                            DEFAULT 'available',
    description     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INTEGER | PK, Auto | Mã phòng (nội bộ) |
| `room_number` | TEXT | UNIQUE, NOT NULL | Mã phòng hiển thị (A101) |
| `building` | TEXT | NOT NULL | Khu nhà (A, B, C...) |
| `floor` | INTEGER | > 0 | Tầng |
| `capacity` | INTEGER | IN (2,4,6) | Sức chứa tối đa |
| `room_type` | TEXT | | Loại phòng (tùy chọn mô tả) |
| `price_per_month` | REAL | > 0 | Giá thuê mỗi tháng (VNĐ) |
| `status` | TEXT | CHECK | `available` / `full` / `maintenance` |
| `description` | TEXT | | Ghi chú thêm về phòng |

**Dữ liệu mẫu:**
```sql
INSERT INTO rooms (room_number, building, floor, capacity, price_per_month, status) VALUES
('A101', 'A', 1, 4, 500000, 'full'),
('A102', 'A', 1, 4, 500000, 'available'),
('B201', 'B', 2, 6, 400000, 'available'),
('B202', 'B', 2, 2, 700000, 'full');
```

---

### Bảng `students` — Sinh Viên

**Mô tả:** Hồ sơ sinh viên đăng ký ở KTX.

```sql
CREATE TABLE students (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id       TEXT    UNIQUE NOT NULL,
    full_name        TEXT    NOT NULL,
    id_card          TEXT    UNIQUE,
    date_of_birth    DATE,
    gender           TEXT    CHECK(gender IN ('Nam', 'Nữ', 'Khác')),
    faculty          TEXT,
    class_name       TEXT,
    phone            TEXT,
    email            TEXT,
    hometown_address TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | INTEGER | PK, Auto | Mã định danh nội bộ |
| `student_id` | TEXT | UNIQUE, NOT NULL | MSSV |
| `full_name` | TEXT | NOT NULL | Họ và tên |
| `id_card` | TEXT | UNIQUE | Số CCCD/CMND |
| `date_of_birth` | DATE | | Ngày sinh (YYYY-MM-DD) |
| `gender` | TEXT | CHECK | Nam / Nữ / Khác |
| `faculty` | TEXT | | Khoa đang học |
| `class_name` | TEXT | | Lớp |
| `phone` | TEXT | | Số điện thoại |
| `email` | TEXT | | Email liên hệ |
| `hometown_address` | TEXT | | Địa chỉ quê quán |

---

### Bảng `contracts` — Hợp Đồng Thuê Phòng

**Mô tả:** Liên kết sinh viên với phòng, quản lý vòng đời thuê phòng.

```sql
CREATE TABLE contracts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    room_id    INTEGER NOT NULL REFERENCES rooms(id),
    bed_number INTEGER CHECK(bed_number > 0),
    start_date DATE    NOT NULL,
    end_date   DATE,
    deposit    REAL    DEFAULT 0,
    status     TEXT    CHECK(status IN ('active','expired','terminated'))
                       DEFAULT 'active',
    notes      TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Ràng buộc: mỗi SV chỉ có 1 HĐ active tại một thời điểm
    UNIQUE(student_id, status) WHERE status = 'active'
);

-- Index để tăng tốc truy vấn
CREATE INDEX idx_contracts_student ON contracts(student_id);
CREATE INDEX idx_contracts_room    ON contracts(room_id);
CREATE INDEX idx_contracts_status  ON contracts(status);
```

| Cột | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `student_id` | INTEGER | FK → students | Sinh viên thuê |
| `room_id` | INTEGER | FK → rooms | Phòng được thuê |
| `bed_number` | INTEGER | > 0 | Số giường cụ thể |
| `start_date` | DATE | NOT NULL | Ngày vào ở |
| `end_date` | DATE | | Ngày dự kiến kết thúc |
| `deposit` | REAL | DEFAULT 0 | Tiền đặt cọc |
| `status` | TEXT | CHECK | `active` / `expired` / `terminated` |

---

### Bảng `fees` — Phiếu Thu Phí

**Mô tả:** Phiếu thu phí hàng tháng cho từng hợp đồng.

```sql
CREATE TABLE fees (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id      INTEGER NOT NULL REFERENCES contracts(id),
    month            INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year             INTEGER NOT NULL CHECK(year >= 2020),
    room_fee         REAL    DEFAULT 0,
    electricity_fee  REAL    DEFAULT 0,
    water_fee        REAL    DEFAULT 0,
    service_fee      REAL    DEFAULT 0,
    total_amount     REAL    NOT NULL,
    paid_amount      REAL    DEFAULT 0,
    paid_date        DATE,
    status           TEXT    CHECK(status IN ('unpaid','partial','paid'))
                             DEFAULT 'unpaid',
    notes            TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Mỗi hợp đồng chỉ có 1 phiếu thu mỗi tháng
    UNIQUE(contract_id, month, year)
);

-- View tiện lợi để xem công nợ
CREATE VIEW v_unpaid_fees AS
SELECT 
    f.id,
    s.student_id  AS mssv,
    s.full_name,
    r.room_number,
    f.month,
    f.year,
    f.total_amount,
    f.paid_amount,
    (f.total_amount - f.paid_amount) AS remaining,
    f.status
FROM fees f
JOIN contracts c ON f.contract_id = c.id
JOIN students s  ON c.student_id = s.id
JOIN rooms r     ON c.room_id = r.id
WHERE f.status != 'paid';
```

| Cột | Kiểu | Mô tả |
|---|---|---|
| `contract_id` | INTEGER | FK → contracts |
| `month` / `year` | INTEGER | Kỳ thu phí |
| `room_fee` | REAL | Tiền phòng |
| `electricity_fee` | REAL | Tiền điện |
| `water_fee` | REAL | Tiền nước |
| `service_fee` | REAL | Phí dịch vụ |
| `total_amount` | REAL | = tổng 4 khoản trên |
| `paid_amount` | REAL | Số tiền đã nộp |
| `status` | TEXT | `unpaid` / `partial` / `paid` |

---

### Bảng `violations` — Vi Phạm Nội Quy

**Mô tả:** Ghi nhận các vi phạm nội quy của sinh viên.

```sql
CREATE TABLE violations (
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
```

| Cột | Kiểu | Mô tả |
|---|---|---|
| `student_id` | INTEGER | FK → students |
| `violation_type` | TEXT | Loại vi phạm |
| `description` | TEXT | Mô tả chi tiết |
| `violation_date` | DATE | Ngày vi phạm |
| `fine_amount` | REAL | Mức phạt (VNĐ) |
| `is_paid` | INTEGER | 0=Chưa nộp, 1=Đã nộp |
| `recorded_by` | INTEGER | FK → users (ai ghi nhận) |

---

## 3. Danh Sách Relationships (Quan Hệ)

| Quan hệ | Kiểu | Mô tả |
|---|---|---|
| students → contracts | 1:N | 1 SV có nhiều HĐ (nhưng 1 active) |
| rooms → contracts | 1:N | 1 phòng có nhiều HĐ qua các thời kỳ |
| contracts → fees | 1:N | 1 HĐ có nhiều phiếu thu (1/tháng) |
| students → violations | 1:N | 1 SV có nhiều lần vi phạm |
| users → violations | 1:N | 1 user ghi nhiều vi phạm |

---

## 4. Các Index & View Hỗ Trợ

```sql
-- Indexes tăng tốc tìm kiếm
CREATE INDEX idx_students_name    ON students(full_name);
CREATE INDEX idx_students_sid     ON students(student_id);
CREATE INDEX idx_rooms_status     ON rooms(status);
CREATE INDEX idx_fees_status      ON fees(status);
CREATE INDEX idx_fees_year_month  ON fees(year, month);

-- View: Phòng còn chỗ trống
CREATE VIEW v_available_rooms AS
SELECT r.*, 
       (r.capacity - COUNT(c.id)) AS available_beds
FROM rooms r
LEFT JOIN contracts c ON r.id = c.room_id AND c.status = 'active'
WHERE r.status = 'available'
GROUP BY r.id
HAVING available_beds > 0;

-- View: Sinh viên đang ở KTX
CREATE VIEW v_current_residents AS
SELECT s.student_id, s.full_name, s.phone, s.faculty,
       r.room_number, r.building,
       c.start_date, c.end_date, c.bed_number
FROM contracts c
JOIN students s ON c.student_id = s.id
JOIN rooms r    ON c.room_id = r.id
WHERE c.status = 'active';
```

---

## 5. Migrations & Seed Data

Script khởi tạo sẽ tự chạy khi mở ứng dụng lần đầu:
1. Tạo tất cả bảng (nếu chưa tồn tại)
2. Tạo tài khoản `admin` mặc định
3. Tạo các view hỗ trợ
4. Tạo indexes

> **Lưu ý:** Database file `ktx.db` sẽ được tạo trong thư mục gốc của ứng dụng.
