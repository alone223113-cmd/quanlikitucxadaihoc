# Tuần 2 — Xây dựng Frontend (Giao diện)

## Mục tiêu tuần 2
- Thiết kế và code các giao diện chính của ứng dụng bằng **Tkinter**
- Demo hoạt động của giao diện (điều hướng, hiển thị dữ liệu mẫu)

## Công nghệ sử dụng
- **Python Tkinter** + `ttk` (CustomTkinter-style theming)
- **SQLite** (kết nối dữ liệu thực tế)
- Theme: Dark mode — Nocturnal Concierge

## Danh sách màn hình đã xây dựng

| STT | File | Màn hình | Mô tả |
|-----|------|----------|-------|
| 1 | `ui/login.py` | Đăng nhập | Xác thực tài khoản quản trị viên |
| 2 | `ui/main_window.py` | Cửa sổ chính | Khung điều hướng sidebar, tích hợp các tab |
| 3 | `ui/dashboard.py` | Dashboard | Tổng quan thống kê: phòng, sinh viên, doanh thu |
| 4 | `ui/rooms.py` | Quản lý Phòng | CRUD phòng, lọc theo tòa nhà, trạng thái |
| 5 | `ui/students.py` | Quản lý Sinh viên | CRUD sinh viên, check-in/check-out |
| 6 | `ui/fees.py` | Quản lý Thu phí | Tạo phí theo phòng, cập nhật trạng thái thanh toán |
| 7 | `ui/violations.py` | Vi phạm | Ghi nhận và tra cứu vi phạm nội quy |
| 8 | `ui/reports.py` | Báo cáo | Thống kê doanh thu, tỷ lệ lấp đầy phòng |

## Tài liệu tham khảo
- Thiết kế UI: [`docs/thiet_ke_ui.md`](../docs/thiet_ke_ui.md)
- Mô tả chức năng: [`docs/mo_ta_chuc_nang.md`](../docs/mo_ta_chuc_nang.md)
- Source code giao diện: thư mục [`ui/`](../ui/)
