# Thiết kế Cơ Sở Dữ Liệu — KTX Manager

## Hệ quản trị CSDL
- **Loại:** SQLite 3
- **File:** `ktx.db`
- **Schema file:** `database/schema.sql`
- **Tính năng bật:** `FOREIGN KEYS = ON`, `WAL mode` (hiệu năng cao hơn journal mode)

---

## Sơ đồ ERD (Entity Relationship Diagram)

```
┌─────────────────┐          ┌──────────────────────────────────────────────────┐
│      users      │          │                     students                     │
│─────────────────│          │──────────────────────────────────────────────────│
│ id (PK)         │          │ id (PK)                                          │
│ username        │          │ id_card (UNIQUE) ← Dùng CCCD/CMND thay MSSV     │
│ password_hash   │          │ full_name                                        │
│ full_name       │          │ date_of_birth                                    │
│ role            │          │ gender                                           │
│ is_active       │          │ faculty, class_name                              │
└────────┬────────┘          │ phone, email, hometown_address                   │
         │                   │ room_id (FK → rooms.id) ← Thay bảng contracts   │
         │ recorded_by (FK)  │ bed_number                                       │
         │                   │ checkin_date, checkout_date                      │
         │                   │ deposit                                          │
         │                   │ residency_status (active/left/none)              │
         │                   └─────────────────┬────────────────────────────────┘
         │                                     │ room_id (FK)
         │                   ┌─────────────────▼────────┐       ┌──────────────────┐
         │                   │          rooms            │       │       fees        │
         │                   │──────────────────────────│       │──────────────────│
         │                   │ id (PK)                  │◄──────│ id (PK)          │
         │                   │ room_number (UNIQUE)      │room_id│ room_id (FK)     │
         │                   │ building                 │       │ month, year      │
         │                   │ floor                    │       │ electricity_fee  │
         │                   │ capacity (2/4/6)         │       │ water_fee        │
         │                   │ room_type                │       │ service_fee      │
         │                   │ price_per_month          │       │ room_fee         │
         │                   │ status                   │       │ total_amount     │
         │                   └──────────────────────────┘       │ paid_amount      │
         │                                                       │ status           │
         │                   ┌──────────────────────────┐       └──────────────────┘
         │                   │        violations         │
         └──────────────────►│──────────────────────────│
           recorded_by (FK)  │ id (PK)                  │
                             │ student_id (FK→students)  │◄──── students.id
                             │ violation_type            │
                             │ description               │
                             │ violation_date            │
                             │ fine_amount               │
                             │ is_paid (0/1)             │
                             │ recorded_by (FK→users)    │
                             └──────────────────────────┘
```

---

## Chi tiết các bảng

### Bảng `users` — Tài khoản người dùng
| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| id | INTEGER | PK, AUTOINCREMENT | Khóa chính |
| username | TEXT | UNIQUE, NOT NULL | Tên đăng nhập |
| password_hash | TEXT | NOT NULL | Mật khẩu đã mã hóa bcrypt |
| full_name | TEXT | - | Họ tên |
| role | TEXT | IN ('admin','staff') | Vai trò |
| is_active | INTEGER | DEFAULT 1 | Trạng thái tài khoản |
| created_at | DATETIME | DEFAULT NOW | Ngày tạo |

### Bảng `rooms` — Phòng ký túc xá
| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| id | INTEGER | PK | Khóa chính |
| room_number | TEXT | UNIQUE, NOT NULL | Số phòng (VD: A101) |
| building | TEXT | NOT NULL | Tòa nhà |
| floor | INTEGER | > 0 | Tầng |
| capacity | INTEGER | IN (2,4,6) | Sức chứa |
| room_type | TEXT | - | Loại phòng |
| price_per_month | REAL | > 0 | Giá thuê/tháng/giường |
| status | TEXT | available/full/maintenance | Trạng thái |
| description | TEXT | - | Mô tả thêm |

### Bảng `students` — Sinh viên (đã gộp Hợp đồng)

> **Quyết định thiết kế:** Gộp thông tin lưu trú (trước đây là bảng `contracts`) trực tiếp vào `students` để đơn giản hóa, tránh JOIN không cần thiết.

| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| id | INTEGER | PK | Khóa chính |
| id_card | TEXT | UNIQUE, NOT NULL | **CCCD/CMND** (định danh chính, thay MSSV) |
| full_name | TEXT | NOT NULL | Họ tên |
| date_of_birth | DATE | - | Ngày sinh |
| gender | TEXT | Nam/Nữ/Khác | Giới tính |
| faculty | TEXT | - | Khoa |
| class_name | TEXT | - | Lớp |
| phone | TEXT | - | Số điện thoại |
| email | TEXT | - | Email |
| hometown_address | TEXT | - | Địa chỉ quê quán |
| **room_id** | INTEGER | FK → rooms.id | **Phòng đang ở** |
| **bed_number** | INTEGER | > 0 | **Số giường** |
| **checkin_date** | DATE | - | **Ngày nhận phòng** |
| **checkout_date** | DATE | - | **Ngày trả phòng dự kiến** |
| **deposit** | REAL | DEFAULT 0 | **Tiền cọc** |
| **residency_status** | TEXT | active/left/none | **Trạng thái lưu trú** |
| created_at | DATETIME | DEFAULT NOW | Ngày tạo |

### Bảng `fees` — Phiếu thu phí (theo phòng)
| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| id | INTEGER | PK | Khóa chính |
| room_id | INTEGER | FK → rooms, NOT NULL | Phòng |
| month | INTEGER | 1–12 | Tháng |
| year | INTEGER | ≥ 2020 | Năm |
| electricity_fee | REAL | DEFAULT 0 | Tiền điện |
| water_fee | REAL | DEFAULT 0 | Tiền nước |
| service_fee | REAL | DEFAULT 0 | Phí dịch vụ |
| room_fee | REAL | DEFAULT 0 | Tiền phòng (giá × số SV) |
| total_amount | REAL | NOT NULL | Tổng phải thu |
| paid_amount | REAL | DEFAULT 0 | Đã thanh toán |
| paid_date | DATE | - | Ngày nộp |
| status | TEXT | unpaid/partial/paid | Trạng thái |
| notes | TEXT | - | Ghi chú |
| UNIQUE | - | (room_id, month, year) | 1 phiếu/phòng/tháng |

### Bảng `violations` — Vi phạm nội quy
| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| id | INTEGER | PK | Khóa chính |
| student_id | INTEGER | FK → students, NOT NULL | Sinh viên vi phạm |
| violation_type | TEXT | NOT NULL | Loại vi phạm |
| description | TEXT | - | Mô tả chi tiết |
| violation_date | DATE | NOT NULL | Ngày vi phạm |
| fine_amount | REAL | DEFAULT 0 | Số tiền phạt |
| is_paid | INTEGER | 0 hoặc 1 | Đã nộp phạt chưa |
| recorded_by | INTEGER | FK → users | Người ghi nhận |
| created_at | DATETIME | DEFAULT NOW | Ngày tạo |

---

## Views (View SQL)

### `v_available_rooms` — Phòng còn chỗ trống
```sql
SELECT r.*, (r.capacity - COUNT(s.id)) AS available_beds
FROM rooms r
LEFT JOIN students s ON r.id = s.room_id AND s.residency_status = 'active'
WHERE r.status = 'available'
GROUP BY r.id HAVING available_beds > 0;
```

### `v_current_residents` — Sinh viên đang lưu trú
```sql
SELECT s.id_card, s.full_name, s.phone, s.faculty,
       r.room_number, r.building, s.checkin_date, s.checkout_date, s.bed_number
FROM students s JOIN rooms r ON s.room_id = r.id
WHERE s.residency_status = 'active';
```

### `v_unpaid_fees` — Phiếu thu chưa thanh toán
```sql
SELECT f.id, r.room_number, r.building, f.month, f.year,
       f.total_amount, f.paid_amount, (f.total_amount - f.paid_amount) AS remaining, f.status
FROM fees f JOIN rooms r ON f.room_id = r.id
WHERE f.status != 'paid';
```

---

## Indexes (Chỉ mục tối ưu hiệu năng)

| Index | Bảng | Cột | Mục đích |
|-------|------|-----|---------|
| idx_students_name | students | full_name | Tìm kiếm theo tên |
| idx_students_cccd | students | id_card | Tìm theo CCCD |
| idx_students_room | students | room_id | JOIN với rooms |
| idx_rooms_status | rooms | status | Lọc trạng thái phòng |
| idx_fees_status | fees | status | Lọc phiếu thu |
| idx_fees_year_month | fees | year, month | Lọc theo tháng/năm |
