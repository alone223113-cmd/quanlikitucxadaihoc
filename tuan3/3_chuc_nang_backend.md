# Các Chức Năng Backend (Business Logic) — KTX Manager

## Tổng quan

Lớp Backend nằm trong thư mục `models/` và `database/`. Mỗi file đảm nhiệm một nhóm nghiệp vụ cụ thể, hoàn toàn tách biệt khỏi giao diện.

---

## 1. Quản lý Phòng (`models/room.py`)

### Chức năng đã cài đặt

**Lấy danh sách phòng với bộ lọc:**
```python
from models.room import get_all_rooms

# Lấy tất cả phòng tòa A còn trống
rooms = get_all_rooms(building="A", status="available")
# Mỗi phòng kèm theo: available_beds, occupied (số SV đang ở)
```

**Tự động cập nhật trạng thái phòng:**
```python
from models.room import update_room_status_auto

# Sau khi thêm/xóa sinh viên, gọi hàm này để cập nhật available/full
update_room_status_auto(room_id=5)
```

**Kiểm tra nghiệp vụ khi xóa:**
```python
from models.room import delete_room

try:
    delete_room(room_id=3)
except ValueError as e:
    print(e)  # "Không thể xóa phòng đang có sinh viên ở."
```

---

## 2. Quản lý Sinh Viên (`models/student.py`)

### Chức năng đã cài đặt

**Tìm kiếm sinh viên:**
```python
from models.student import get_all_students

# Tìm theo tên, CCCD, hoặc SĐT
students = get_all_students(search="Nguyễn", faculty="CNTT")
```

**Thêm sinh viên mới (đã gộp hợp đồng):**
```python
from models.student import add_student

data = {
    "full_name": "Nguyễn Văn A",
    "id_card": "001234567899",       # CCCD/CMND
    "date_of_birth": "2004-01-01",
    "gender": "Nam",
    "faculty": "CNTT",
    "class_name": "CNTT01",
    "phone": "0912345678",
    "room_id": 2,
    "bed_number": 3,
    "checkin_date": "2026-09-01",
    "checkout_date": "2027-06-30",
    "deposit": 500000,
    "residency_status": "active"
}
student_id = add_student(data)
```

**Kiểm tra nghiệp vụ khi xóa:**
```python
from models.student import delete_student

try:
    delete_student(student_id=1)
except ValueError as e:
    print(e)  # "Không thể xóa người đang lưu trú tại KTX."
```

---

## 3. Quản lý Thu Phí (`models/fee.py`)

### Chức năng đã cài đặt

**Tự động tạo phiếu thu hàng tháng:**
```python
from models.fee import create_monthly_fees

# Tạo phiếu thu cho tháng 5/2026 cho tất cả phòng đang có SV
count = create_monthly_fees(month=5, year=2026)
print(f"Đã tạo {count} phiếu thu")
```

**Ghi nhận thanh toán (cộng dồn):**
```python
from models.fee import mark_paid

# SV trả 500,000đ cho phiếu thu ID=3
mark_paid(fee_id=3, amount=500000, paid_date="2026-05-10")
# Hệ thống tự tính: unpaid → partial → paid
```

**Thống kê doanh thu:**
```python
from models.fee import get_monthly_summary, get_revenue_by_month

# Tổng kết tháng 4/2026
summary = get_monthly_summary(month=4, year=2026)
# → {'total_due': 5000000, 'total_paid': 4500000, 'total_remaining': 500000, 'total_records': 6}

# Doanh thu từng tháng trong năm 2026 (dùng cho biểu đồ)
revenue = get_revenue_by_month(year=2026)
```

---

## 4. Quản lý Vi Phạm (`models/violation.py`)

### Chức năng đã cài đặt

**Lọc vi phạm theo nhiều tiêu chí:**
```python
from models.violation import get_all_violations

violations = get_all_violations(
    search="Nguyễn",
    violation_type="Gây ồn ào sau 22h",
    from_date="2026-04-01",
    to_date="2026-04-30"
)
```

**Ghi nhận vi phạm mới:**
```python
from models.violation import add_violation

data = {
    "student_id": 1,
    "violation_type": "Về trễ giờ quy định",
    "description": "Về sau 23:00 ngày 27/04/2026",
    "violation_date": "2026-04-27",
    "fine_amount": 50000,
    "recorded_by": 1   # ID của user đang đăng nhập
}
add_violation(data)
```

**Thống kê vi phạm:**
```python
from models.violation import get_statistics

stats = get_statistics()
# → {'total': 10, 'unpaid': 3, 'total_fine': 850000}
```

---

## 5. Database & Xác thực (`database/db.py`)

### Chức năng đã cài đặt

**Khởi tạo database tự động:**
```python
from database.db import initialize_database

# Chỉ cần gọi 1 lần khi khởi động app
# Tự tạo bảng + seed dữ liệu mẫu nếu chưa có
initialize_database()
```

**Xác thực mật khẩu (bcrypt):**
```python
from database.db import verify_password, hash_password

# Đăng nhập
hashed = user["password_hash"]
if verify_password("admin123", hashed):
    print("Đăng nhập thành công")

# Tạo tài khoản mới
new_hash = hash_password("matkhaumoi")
```

---

## Luồng nghiệp vụ chính

```
[Khởi động app]
    └─→ initialize_database()
        └─→ Tạo schema, seed data mẫu

[Đăng nhập]
    └─→ Truy vấn users, verify_password() với bcrypt

[Thêm sinh viên]
    └─→ add_student(data)
        └─→ update_room_status_auto(room_id)
            └─→ Tự cập nhật phòng: available → full

[Thu phí hàng tháng]
    └─→ create_monthly_fees(month, year)
        └─→ Tạo phiếu theo từng phòng có SV
    └─→ mark_paid(fee_id, amount, date)
        └─→ Cộng dồn, tự tính trạng thái

[Báo cáo]
    └─→ get_revenue_by_month(year) → Biểu đồ cột
    └─→ get_monthly_summary() → Tổng kết
    └─→ get_statistics() → Thống kê vi phạm
```
