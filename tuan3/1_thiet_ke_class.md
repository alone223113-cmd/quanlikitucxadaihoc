# Thiết kế Class — KTX Manager

## Kiến trúc tổng thể

Dự án sử dụng kiến trúc **3 lớp** (Three-tier):

```
┌─────────────────────────────────┐
│        UI Layer (ui/)           │  ← Giao diện người dùng (PySide6)
├─────────────────────────────────┤
│      Model Layer (models/)      │  ← Business Logic + CRUD
├─────────────────────────────────┤
│    Database Layer (database/)   │  ← SQLite + db.py
└─────────────────────────────────┘
```

---

## 1. Class Room — `models/room.py`

**Mục đích:** Quản lý toàn bộ nghiệp vụ liên quan đến phòng ký túc xá.

| Hàm | Mô tả |
|-----|-------|
| `get_all_rooms(building, status, search)` | Lấy danh sách phòng, kèm số giường còn trống |
| `get_room_by_id(room_id)` | Lấy thông tin 1 phòng theo ID |
| `get_available_rooms()` | Lấy danh sách phòng còn chỗ trống |
| `add_room(data)` | Thêm phòng mới, trả về ID vừa tạo |
| `update_room(room_id, data)` | Cập nhật thông tin phòng |
| `delete_room(room_id)` | Xóa phòng (kiểm tra không có SV đang ở) |
| `get_buildings()` | Lấy danh sách tòa nhà |
| `get_students_by_room(room_id)` | Lấy danh sách sinh viên đang ở trong phòng |

**Hàm nội bộ (private):**
| Hàm | Mô tả |
|-----|-------|
| `_update_room_status(conn, room_id)` | Tự động cập nhật `available/full` khi SV check-in/out |

**Ràng buộc nghiệp vụ:**
- Không thể xóa phòng khi còn sinh viên `residency_status='active'`
- Sức chứa chỉ cho phép: 2, 4, hoặc 6 người
- Trạng thái phòng tự động cập nhật: `available` / `full` / `maintenance`

---

## 2. Class Student — `models/student.py`

**Mục đích:** Quản lý sinh viên, đồng thời tích hợp luôn thông tin hợp đồng (check-in/check-out). Không có bảng `contracts` riêng.

| Hàm | Mô tả |
|-----|-------|
| `get_all_students(search, faculty, status)` | Lấy danh sách sinh viên, kèm thông tin phòng |
| `get_student_by_id(student_id)` | Lấy thông tin 1 sinh viên |
| `get_student_by_id_card(id_card)` | Tìm sinh viên theo CCCD/CMND |
| `add_student(data)` | Thêm sinh viên mới kèm thông tin lưu trú |
| `update_student(student_id, data)` | Cập nhật thông tin (tự cập nhật trạng thái phòng) |
| `delete_student(student_id)` | Xóa sinh viên (không xóa được nếu đang lưu trú) |

**Ràng buộc nghiệp vụ:**
- CCCD/CMND (`id_card`) là định danh duy nhất
- Không thể xóa sinh viên có `residency_status = 'active'`
- Trạng thái lưu trú: `active` (đang ở) | `left` (đã rời) | `none` (chưa nhận phòng)
- Khi cập nhật phòng: tự động cập nhật trạng thái phòng cũ và mới

---

## 3. Class Fee — `models/fee.py`

**Mục đích:** Quản lý thu phí theo phòng (điện, nước, dịch vụ, tiền giường).

| Hàm | Mô tả |
|-----|-------|
| `get_fees_by_month(month, year, search, status)` | Lấy phiếu thu theo tháng/năm |
| `create_monthly_fees(month, year)` | Tự động tạo phiếu thu cho tất cả phòng có SV |
| `update_fee(fee_id, data)` | Cập nhật phiếu thu (điện, nước, dịch vụ, trạng thái) |

**Ràng buộc nghiệp vụ:**
- Mỗi phòng chỉ có 1 phiếu thu / tháng (UNIQUE constraint)
- Trạng thái: `unpaid` → `partial` → `paid`
- Tiền phòng mặc định = đơn giá × số SV đang ở

---

## 4. Class Violation — `models/violation.py`

**Mục đích:** Quản lý vi phạm nội quy của sinh viên.

| Hàm | Mô tả |
|-----|-------|
| `get_all_violations(search, violation_type, from_date, to_date)` | Lọc danh sách vi phạm (tìm theo CCCD/tên) |
| `add_violation(data)` | Ghi nhận vi phạm mới |
| `update_violation(vio_id, data)` | Cập nhật thông tin vi phạm |
| `mark_violation_paid(vio_id)` | Đánh dấu đã nộp phạt |
| `get_violation_types()` | Lấy danh sách loại vi phạm |
| `get_statistics()` | Thống kê số vi phạm, số tiền phạt |

---

## 5. Database Layer — `database/db.py`

| Hàm | Mô tả |
|-----|-------|
| `get_connection()` | Mở kết nối SQLite, bật `foreign_keys` và `WAL` mode |
| `initialize_database()` | Đọc `schema.sql`, tạo bảng, seed dữ liệu mẫu |
| `verify_password(plain, hashed)` | Xác thực mật khẩu với bcrypt |
| `hash_password(plain)` | Mã hóa mật khẩu bằng bcrypt |

---

## Sơ đồ quan hệ giữa các Class

```
USERS ────────────────────────────────────────────────┐
                                                      │ recorded_by
ROOMS ◄──── room_id ──── STUDENTS ◄── student_id ─── VIOLATIONS
  │
  └── room_id ──── FEES
```

| Quan hệ | Loại | Mô tả |
|---------|------|-------|
| ROOMS → STUDENTS | 1–N | 1 phòng chứa nhiều SV |
| ROOMS → FEES | 1–N | 1 phòng có nhiều phiếu thu (mỗi tháng 1 phiếu) |
| STUDENTS → VIOLATIONS | 1–N | 1 SV có thể vi phạm nhiều lần |
| USERS → VIOLATIONS | 1–N | 1 nhân viên ghi nhiều vi phạm |
