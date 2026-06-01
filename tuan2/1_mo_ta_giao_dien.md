# Mô tả Giao diện Frontend — Tuần 2

## Thông tin chung
- **Framework:** Python Tkinter + ttk
- **Theme:** Dark mode (Nocturnal Concierge)
- **Màu chủ đạo:** `#0a0e1a` (nền) · `#1e2540` (panel) · `#4f8ef7` (accent xanh)
- **Font:** Segoe UI / System default

---

## 1. Màn hình Đăng nhập — `ui/login.py`

**Chức năng:**
- Nhập username và password
- Xác thực với bảng `Users` trong database
- Điều hướng sang `MainWindow` nếu đăng nhập thành công
- Hiển thị thông báo lỗi nếu sai thông tin

**Thành phần giao diện:**
- Logo / tiêu đề ứng dụng
- Ô nhập `Tên đăng nhập`
- Ô nhập `Mật khẩu` (ẩn ký tự)
- Nút **Đăng nhập**

---

## 2. Cửa sổ chính — `ui/main_window.py`

**Chức năng:**
- Khung chứa toàn bộ ứng dụng
- Sidebar điều hướng bên trái với các mục:
  - 🏠 Dashboard
  - 🚪 Quản lý Phòng
  - 👤 Quản lý Sinh viên
  - 💰 Thu phí
  - ⚠️ Vi phạm
  - 📊 Báo cáo
- Nút **Đăng xuất**

---

## 3. Dashboard — `ui/dashboard.py`

**Chức năng:** Hiển thị tổng quan hệ thống theo thời gian thực.

**Thành phần:**
| Card | Nội dung |
|------|----------|
| Tổng phòng | Số phòng trong hệ thống |
| Phòng có chỗ | Số phòng còn giường trống |
| Tổng sinh viên | Số SV đang cư trú (`active`) |
| Doanh thu tháng | Tổng tiền đã thu trong tháng hiện tại |

---

## 4. Quản lý Phòng — `ui/rooms.py`

**Chức năng:**
- Xem danh sách phòng (lọc theo tòa nhà, trạng thái, tìm kiếm)
- Thêm / Sửa / Xóa phòng
- Xem danh sách sinh viên đang ở trong phòng

**Bảng dữ liệu hiển thị:**
`Mã phòng | Tòa nhà | Tầng | Loại phòng | Sức chứa | Đang ở | Trạng thái | Giá/tháng`

**Ràng buộc hiển thị:**
- Phòng `full` → highlight màu khác
- Không cho xóa nếu còn SV `active`

---

## 5. Quản lý Sinh viên — `ui/students.py`

**Chức năng:**
- Xem danh sách sinh viên (lọc theo phòng, trạng thái, tìm kiếm)
- Thêm sinh viên mới (tự động gán phòng, ghi ngày check-in)
- Sửa thông tin sinh viên
- Check-out sinh viên (cập nhật `residency_status = 'inactive'`, ghi ngày check-out)

**Bảng dữ liệu hiển thị:**
`MSSV | Họ tên | Giới tính | SĐT | Phòng | Check-in | Check-out | Trạng thái`

---

## 6. Quản lý Thu phí — `ui/fees.py`

**Chức năng:**
- Xem danh sách khoản phí theo phòng và tháng
- Tạo phí hàng tháng tự động cho tất cả phòng
- Cập nhật trạng thái thanh toán: `pending` → `paid` / `overdue`

**Bảng dữ liệu hiển thị:**
`Phòng | Tháng | Số tiền | Trạng thái | Ngày tạo | Ngày thanh toán`

**Màu trạng thái:**
- `paid` → Xanh lá ✅
- `pending` → Vàng 🕐
- `overdue` → Đỏ ❌

---

## 7. Vi phạm Nội quy — `ui/violations.py`

**Chức năng:**
- Xem danh sách vi phạm
- Ghi nhận vi phạm mới (chọn sinh viên, mô tả, mức phạt)
- Lọc theo sinh viên, mức độ

**Bảng dữ liệu hiển thị:**
`MSSV | Họ tên | Mô tả vi phạm | Mức phạt (VNĐ) | Ngày vi phạm`

---

## 8. Báo cáo — `ui/reports.py`

**Chức năng:**
- Thống kê doanh thu theo tháng
- Tỷ lệ lấp đầy phòng
- Danh sách phí quá hạn chưa thanh toán

**Hiển thị:** Bảng tổng hợp + số liệu tóm tắt
