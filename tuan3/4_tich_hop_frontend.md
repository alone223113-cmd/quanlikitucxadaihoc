# Tích hợp Backend với Frontend — KTX Manager

## Kiến trúc tích hợp

Mỗi màn hình UI trong thư mục `ui/` kết nối trực tiếp với lớp `models/` để lấy và ghi dữ liệu.
Không có lớp trung gian (controller), theo mô hình đơn giản hóa phù hợp với ứng dụng desktop.

```
ui/login.py          ←→  database/db.py        (xác thực đăng nhập)
ui/dashboard.py      ←→  database/db.py        (truy vấn thống kê trực tiếp)
ui/rooms.py          ←→  models/room.py        (CRUD phòng + xem SV trong phòng)
ui/students.py       ←→  models/student.py     (CRUD sinh viên & hợp đồng)
ui/fees.py           ←→  models/fee.py         (tạo phiếu thu + nhập điện/nước)
ui/violations.py     ←→  models/violation.py   (CRUD vi phạm)
ui/reports.py        ←→  database/db.py        (biểu đồ doanh thu, công suất phòng, công nợ)
```

---

## 1. Màn hình Đăng nhập (`ui/login.py`)

**Tích hợp với:** `database/db.py`

- Người dùng nhập `username` + `password`
- Truy vấn bảng `users`, gọi `verify_password()` với bcrypt
- Nếu đúng → emit signal `login_success(user_dict)` → mở `MainWindow`
- Nếu sai → hiện thông báo lỗi

---

## 2. Dashboard (`ui/dashboard.py`)

**Tích hợp với:** `database/db.py` (truy vấn trực tiếp)

| Thẻ thống kê | Dữ liệu lấy từ |
|---|---|
| Số phòng đang mở | `SELECT COUNT(*) FROM rooms WHERE status != 'maintenance'` |
| Phòng còn trống | `SELECT COUNT(*) FROM rooms WHERE status='available'` |
| Sinh viên đang lưu trú | `SELECT COUNT(*) FROM students WHERE residency_status='active'` |
| Tổng công nợ | `SELECT SUM(total_amount - paid_amount) FROM fees WHERE status != 'paid'` |

- Cuối trang: Hiển thị **5 hóa đơn trễ hạn gần nhất** (JOIN fees + rooms)
- Hàm `refresh()` được gọi mỗi khi chuyển tab

---

## 3. Quản lý Phòng (`ui/rooms.py`)

**Tích hợp với:** `models/room.py`

| Hành động UI | Hàm Backend gọi |
|---|---|
| Load danh sách | `get_all_rooms(building, status, search)` |
| Bấm "Thêm phòng" | `add_room(data)` |
| Bấm ✏️ Sửa | `update_room(room_id, data)` |
| Bấm 🗑️ Xóa | `delete_room(room_id)` → bắt `ValueError` |
| Bấm 👥 Xem SV | `get_students_by_room(room_id)` → mở dialog danh sách |
| Bộ lọc Tòa nhà | `get_buildings()` |

**Luồng xử lý điển hình:**
```
Người dùng bấm [Thêm Phòng]
    → Mở dialog nhập thông tin
    → Validate đầu vào (không để trống, giá > 0)
    → Gọi add_room(data)
    → Refresh bảng danh sách
    → Hiện thông báo thành công
```

---

## 4. Quản lý Sinh Viên & Hợp Đồng (`ui/students.py`)

**Tích hợp với:** `models/student.py`, `models/room.py`

| Hành động UI | Hàm Backend gọi |
|---|---|
| Load danh sách | `get_all_students(search, status)` → JOIN rooms |
| Bấm "Thêm Mới" | `add_student(data)` → tự cập nhật trạng thái phòng |
| Bấm ✏️ Sửa | `update_student(student_id, data)` |
| Bấm 🗑️ Xóa | `delete_student(student_id)` → bắt `ValueError` |
| Chọn phòng | `get_available_rooms()` → Dropdown chỉ phòng còn chỗ |
| Filter trạng thái | `get_all_students(status='active'/'left'/'none')` |

**Đặc điểm tích hợp:**
- Màn hình **gộp Sinh Viên + Hợp Đồng** trong cùng 1 form
- Form gồm: CCCD, Họ Tên, SĐT + **Phòng, Giường, Ngày Vào, Ngày Ra, Tiền Cọc, Trạng Thái**
- Bảng hiển thị: CCCD | Họ Tên | SĐT | Phòng | Giường | Ngày Vào | Ngày Ra | Trạng Thái
- Sau mỗi thao tác thêm/xóa/cập nhật SV, phòng tự cập nhật trạng thái `available/full`

---

## 5. Quản lý Thu Phí (`ui/fees.py`)

**Tích hợp với:** `models/fee.py`

| Hành động UI | Hàm Backend gọi |
|---|---|
| Load tháng/năm | `get_fees_by_month(month, year)` |
| Bấm "Sinh Hóa Đơn Tự Động" | `create_monthly_fees(month, year)` |
| Bấm ✏️ Sửa phiếu | `update_fee(fee_id, data)` → nhập điện/nước/dịch vụ |
| Đổi dropdown trạng thái | `update_fee(fee_id, {status, paid_amount})` |

**Dialog nhập điện/nước (FeeEditDialog):**
| Trường | Mô tả |
|---|---|
| Tiền phòng | Giá × số SV (tự sinh) |
| Tiền điện | Nhập thủ công theo phòng |
| Tiền nước | Nhập thủ công theo phòng |
| Phí dịch vụ | Nhập thủ công |
| Tổng | Tự tính = Phòng + Điện + Nước + DV |

**Màu trạng thái:**
| Trạng thái | Màu hiển thị |
|---|---|
| `paid` | 🟢 Xanh lá |
| `unpaid` | 🔴 Đỏ |

---

## 6. Quản lý Vi Phạm (`ui/violations.py`)

**Tích hợp với:** `models/violation.py`

| Hành động UI | Hàm Backend gọi |
|---|---|
| Load danh sách | `get_all_violations(search, type, from_date, to_date)` |
| Tìm kiếm | Theo **CCCD** hoặc tên sinh viên |
| Bấm "Thêm vi phạm" | `add_violation(data)` |
| Bấm ✏️ Sửa | `update_violation(vio_id, data)` |
| Bấm "Đã nộp phạt" | `mark_violation_paid(vio_id)` |

---

## 7. Báo Cáo & Thống Kê (`ui/reports.py`)

**Tích hợp với:** `database/db.py` (truy vấn SQL trực tiếp)

| Tab | Nội dung | Nguồn dữ liệu |
|---|---|---|
| 💰 Doanh Thu | Bảng 12 tháng + tổng | `SELECT ... FROM fees WHERE year=?` |
| 🏠 Công Suất | Danh sách phòng + % lấp đầy | JOIN rooms + students |
| 🔴 Công Nợ | Phiếu chưa thanh toán | `fees WHERE status != 'paid'` |

- Hỗ trợ vẽ biểu đồ nếu cài `matplotlib` (tùy chọn)
- Nút **"Xuất CSV Doanh Thu"** (đang là pass — chưa cài đặt)

---

## Quy trình xử lý lỗi chung

Tất cả các màn hình đều tuân theo quy trình xử lý lỗi nhất quán:

```python
try:
    # Gọi hàm backend
    result = some_model_function(data)
    # Hiển thị kết quả
    self.refresh()
    QMessageBox.information(self, "Thành công", "Thao tác hoàn tất!")

except ValueError as e:
    # Lỗi nghiệp vụ (VD: xóa phòng đang có SV)
    QMessageBox.warning(self, "Không thể thực hiện", str(e))

except Exception as e:
    # Lỗi hệ thống
    QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi:\n{str(e)}")
```

---

## Sơ đồ luồng dữ liệu tổng thể

```
                    ┌─────────────────┐
                    │   main.py       │
                    │ initialize_db() │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  ui/login.py    │
                    │ verify_password │
                    └────────┬────────┘
                             │ login_success signal
                    ┌────────▼────────────────────────────────────┐
                    │              ui/main_window.py              │
                    │           QStackedWidget + Sidebar          │
                    └──┬──────┬──────┬──────┬──────┬─────────────┘
                       │      │      │      │      │
               ┌───────▼┐ ┌───▼──┐ ┌▼─────┐┌▼───┐ ┌▼────────┐
               │dashbrd  │ │rooms │ │studs ││fees│ │reports  │
               └───────┬┘ └───┬──┘ └──┬───┘└──┬─┘ └──┬──────┘
                       │      │       │        │      │
               ┌───────▼──────▼───────▼────────▼──────▼───────┐
               │              models/ + database/              │
               │     room.py · student.py · fee.py · db.py     │
               └───────────────────────────┬───────────────────┘
                                           │
                                  ┌────────▼────────┐
                                  │    ktx.db        │
                                  │  (SQLite file)   │
                                  └─────────────────┘
```
