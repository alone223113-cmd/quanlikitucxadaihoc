# Mô Tả Chức Năng — Hệ Thống Quản Lý KTX

> **Môn học:** Lập Trình Python  
> **Đề tài:** Xây dựng phần mềm quản lý Ký Túc Xá Trường Đại Học  
> **Loại ứng dụng:** Desktop Application (Python + PySide6 + SQLite)

---

## 1. Tổng Quan Hệ Thống

### 1.1 Mục Đích

Phần mềm nhằm hỗ trợ **Ban Quản Lý Ký Túc Xá** trường đại học thực hiện các nghiệp vụ hàng ngày một cách nhanh chóng, chính xác và có hệ thống, thay thế phương pháp quản lý thủ công bằng sổ sách.

### 1.2 Đối Tượng Người Dùng

| Vai trò | Mô tả | Quyền hạn |
|---|---|---|
| **Quản trị viên (Admin)** | Trưởng ban quản lý KTX | Toàn quyền: thêm/sửa/xóa dữ liệu, phân quyền tài khoản, xem báo cáo |
| **Nhân viên (Staff)** | Nhân viên trực KTX | Xem và cập nhật thông tin, ghi nhận thanh toán, tạo phiếu thu |

### 1.3 Sơ Đồ Chức Năng Tổng Quát

```
HỆ THỐNG QUẢN LÝ KTX
├── 1. Đăng nhập & Phân quyền
├── 2. Dashboard Tổng Quan
├── 3. Quản lý Phòng
│   ├── 3.1 Danh sách phòng
│   ├── 3.2 Thêm/Sửa/Xóa phòng
│   └── 3.3 Chi tiết phòng
├── 4. Quản lý Sinh Viên
│   ├── 4.1 Danh sách sinh viên
│   ├── 4.2 Thêm/Sửa/Xóa sinh viên
│   └── 4.3 Lịch sử ở KTX
├── 5. Quản lý Hợp Đồng
│   ├── 5.1 Danh sách hợp đồng
│   ├── 5.2 Đăng ký ở KTX (wizard)
│   ├── 5.3 Gia hạn hợp đồng
│   └── 5.4 Trả phòng / Kết thúc HĐ
├── 6. Quản lý Thu Phí
│   ├── 6.1 Tạo phiếu thu hàng tháng
│   ├── 6.2 Ghi nhận thanh toán
│   └── 6.3 Theo dõi công nợ
├── 7. Quản lý Vi Phạm
│   ├── 7.1 Ghi nhận vi phạm
│   └── 7.2 Lịch sử vi phạm
└── 8. Báo Cáo & Thống Kê
    ├── 8.1 Báo cáo doanh thu
    ├── 8.2 Báo cáo công suất phòng
    └── 8.3 Xuất file báo cáo
```

---

## 2. Mô Tả Chi Tiết Từng Chức Năng

---

### Chức Năng 1: Đăng Nhập & Quản Lý Tài Khoản

#### 1.1 Đăng Nhập
| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Xác thực người dùng trước khi vào hệ thống |
| **Đầu vào** | Tên đăng nhập, mật khẩu |
| **Xử lý** | So sánh mật khẩu đã được băm (hash) với database |
| **Đầu ra** | Chuyển vào màn hình chính theo phân quyền |
| **Lỗi** | Hiển thị thông báo nếu sai tài khoản/mật khẩu |

#### 1.2 Đăng Xuất
- Người dùng có thể đăng xuất bất cứ lúc nào
- Hệ thống xóa session và quay lại màn hình đăng nhập

#### 1.3 Quản Lý Tài Khoản (Admin)
- Xem danh sách tài khoản hệ thống
- Thêm tài khoản mới cho nhân viên
- Phân vai trò: Admin / Nhân viên
- Vô hiệu hóa / kích hoạt tài khoản
- Đặt lại mật khẩu

---

### Chức Năng 2: Dashboard Tổng Quan

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Cung cấp cái nhìn nhanh về tình trạng KTX |
| **Người dùng** | Admin + Nhân viên |

#### Các thành phần hiển thị:

**Thẻ thống kê nhanh (Summary Cards):**
- 🏠 **Tổng số phòng** — Tổng phòng trong hệ thống
- ✅ **Phòng trống** — Số phòng còn chỗ
- 👥 **Sinh viên đang ở** — Tổng SV có hợp đồng active
- 💰 **Doanh thu tháng này** — Tổng phí đã thu trong tháng

**Biểu đồ:**
- Biểu đồ cột: Doanh thu 6 tháng gần nhất
- Biểu đồ tròn: Tỷ lệ phòng trống / đầy / bảo trì

**Danh sách hoạt động gần nhất:**
- Hợp đồng mới tạo
- Thanh toán vừa ghi nhận
- Vi phạm mới ghi nhận

---

### Chức Năng 3: Quản Lý Phòng

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Quản lý toàn bộ thông tin về các phòng ở KTX |
| **Người dùng** | Admin (thêm/sửa/xóa), Nhân viên (xem) |

#### 3.1 Danh Sách Phòng

**Thông tin hiển thị cho mỗi phòng:**

| Trường dữ liệu | Kiểu | Mô tả |
|---|---|---|
| Mã phòng | Text | VD: A101, B205 |
| Khu nhà | Text | A, B, C, D... |
| Tầng | Số nguyên | 1, 2, 3... |
| Loại phòng | Text | Phòng 2/4/6 người |
| Sức chứa | Số nguyên | Tối đa bao nhiêu người |
| Đang ở | Số nguyên | Số người hiện tại |
| Giá/tháng | Tiền | Đơn vị VNĐ |
| Trạng thái | Enum | Trống / Đầy / Bảo trì |

**Tính năng lọc:**
- Lọc theo Khu nhà (A, B, C...)
- Lọc theo Trạng thái
- Tìm kiếm theo mã phòng

#### 3.2 Thêm Phòng Mới
- Form nhập liệu với validation đầy đủ
- Tự động cập nhật trạng thái khi sức chứa thay đổi

#### 3.3 Sửa Thông Tin Phòng
- Chỉnh sửa tất cả thông tin trừ mã phòng (primary key)
- Lưu lịch sử thay đổi

#### 3.4 Xóa Phòng
- Kiểm tra ràng buộc: không xóa khi có sinh viên đang ở
- Xác nhận trước khi xóa

#### 3.5 Chi Tiết Phòng
- Xem danh sách sinh viên đang ở trong phòng
- Xem lịch sử thuê phòng

---

### Chức Năng 4: Quản Lý Sinh Viên

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Lưu trữ và quản lý hồ sơ sinh viên ở KTX |
| **Người dùng** | Admin + Nhân viên |

#### Thông Tin Hồ Sơ Sinh Viên:

| Trường dữ liệu | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| MSSV | Text | ✅ | Mã số sinh viên, định danh duy nhất |
| Họ và tên | Text | ✅ | Tên đầy đủ |
| Số CCCD | Text | ✅ | Căn cước công dân |
| Ngày sinh | Date | ✅ | Định dạng DD/MM/YYYY |
| Giới tính | Enum | ✅ | Nam / Nữ / Khác |
| Khoa | Text | ✅ | Khoa đang học |
| Lớp | Text | ✅ | Tên lớp |
| Số điện thoại | Text | ✅ | 10 chữ số |
| Email | Text | Không | Email liên hệ |
| Địa chỉ quê | Text | Không | Địa chỉ gia đình |

#### Tính Năng:
- **Tìm kiếm:** Theo MSSV, họ tên, số điện thoại
- **Lọc:** Theo khoa, giới tính, trạng thái (đang ở / đã rời)
- **Xem lịch sử:** Toàn bộ các hợp đồng đã ở KTX

#### Ràng Buộc:
- MSSV và CCCD phải là duy nhất trong hệ thống
- Số điện thoại phải đúng định dạng 10 chữ số
- Không xóa sinh viên đang có hợp đồng active

---

### Chức Năng 5: Quản Lý Hợp Đồng

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Xử lý toàn bộ vòng đời hợp đồng thuê phòng |
| **Người dùng** | Admin + Nhân viên |

#### 5.1 Đăng Ký Ở KTX (Tạo Hợp Đồng Mới)

Quy trình **3 bước (Wizard)**:

**Bước 1: Chọn Sinh Viên**
- Tìm kiếm sinh viên theo MSSV hoặc tên
- Kiểm tra sinh viên chưa có hợp đồng active

**Bước 2: Chọn Phòng**
- Hiển thị danh sách phòng còn trống
- Lọc theo khu, loại phòng, mức giá
- Xem chi tiết phòng trước khi chọn
- Chọn số giường cụ thể còn trống

**Bước 3: Thông Tin Hợp Đồng**
- Ngày vào ở (mặc định: hôm nay)
- Ngày dự kiến kết thúc
- Tiền cọc
- Ghi chú đặc biệt

#### Thông Tin Hợp Đồng:

| Trường | Kiểu | Mô tả |
|---|---|---|
| Sinh viên | FK | Liên kết bảng students |
| Phòng | FK | Liên kết bảng rooms |
| Số giường | Số | Giường cụ thể trong phòng |
| Ngày vào | Date | Ngày bắt đầu ở |
| Ngày ra (dự kiến) | Date | Ngày kết thúc hợp đồng |
| Tiền cọc | Tiền | Số tiền đặt cọc |
| Trạng thái | Enum | Đang hiệu lực / Hết hạn / Đã kết thúc |

#### 5.2 Gia Hạn Hợp Đồng
- Cập nhật ngày kết thúc mới
- Ghi chú lý do gia hạn

#### 5.3 Kết Thúc Hợp Đồng / Trả Phòng
- Ghi ngày thực tế kết thúc
- Kiểm tra công nợ chưa trả → cảnh báo
- Xử lý hoàn tiền cọc (ghi chú)
- Tự động cap nhật trạng thái phòng

---

### Chức Năng 6: Quản Lý Thu Phí

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Quản lý việc thu phí hàng tháng từ sinh viên |
| **Người dùng** | Admin + Nhân viên |

#### 6.1 Tạo Phiếu Thu Hàng Tháng

Các khoản phí trong mỗi phiếu thu:

| Khoản phí | Mô tả | Cách tính |
|---|---|---|
| Tiền phòng | Phí thuê phòng | Theo hợp đồng (cố định) |
| Tiền điện | Điện tiêu thụ | Chỉ số điện × đơn giá |
| Tiền nước | Nước tiêu thụ | Chỉ số nước × đơn giá |
| Phí dịch vụ | Vệ sinh, bảo vệ... | Cố định theo tháng |
| **Tổng cộng** | Tổng các khoản | Tự động tính |

#### 6.2 Ghi Nhận Thanh Toán
- Nhập số tiền thanh toán (có thể thanh toán từng phần)
- Ghi ngày thanh toán
- Tự động cập nhật trạng thái: Chưa TT → Thanh toán 1 phần → Đã thanh toán

#### 6.3 Theo Dõi Công Nợ
- Danh sách sinh viên còn nợ phí
- Sắp xếp theo số tiền nợ / số tháng nợ
- Cảnh báo trực quan (màu đỏ) cho nợ quá hạn

---

### Chức Năng 7: Quản Lý Vi Phạm

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Ghi nhận và theo dõi vi phạm nội quy KTX |
| **Người dùng** | Admin + Nhân viên |

#### Các Loại Vi Phạm Phổ Biến:

| Loại vi phạm | Mức phạt gợi ý |
|---|---|
| Về trễ giờ quy định | 50,000 VNĐ |
| Gây ồn ào sau 22h | 100,000 VNĐ |
| Hút thuốc trong phòng | 200,000 VNĐ |
| Phá hoại tài sản chung | Theo thiệt hại thực tế |
| Tụ tập đông người | 150,000 VNĐ |
| Vi phạm khác | Tùy mức độ |

#### Thông Tin Ghi Nhận Vi Phạm:
- Sinh viên vi phạm
- Loại vi phạm
- Mô tả chi tiết
- Ngày vi phạm
- Mức phạt tiền
- Trạng thái phạt: Chưa nộp / Đã nộp

---

### Chức Năng 8: Báo Cáo & Thống Kê

| Thông tin | Mô tả |
|---|---|
| **Mục đích** | Cung cấp báo cáo thống kê hỗ trợ ra quyết định |
| **Người dùng** | Admin |

#### Các Loại Báo Cáo:

**8.1 Báo Cáo Doanh Thu**
- Tổng thu theo tháng / quý / năm
- Biểu đồ cột so sánh doanh thu các tháng
- Phân tích theo khu nhà

**8.2 Báo Cáo Công Suất Phòng**
- Tỷ lệ lấp đầy theo khu / toàn KTX
- Biểu đồ tròn phòng trống vs đầy
- Xu hướng theo thời gian

**8.3 Báo Cáo Công Nợ**
- Danh sách sinh viên nợ phí
- Tổng công nợ chưa thu

**8.4 Xuất File**
- Xuất bảng dữ liệu ra CSV (mở được bằng Excel)
- Xuất báo cáo tổng hợp ra PDF

---

## 3. Quy Tắc Nghiệp Vụ Quan Trọng

### 3.1 Ràng Buộc Dữ Liệu
- Một sinh viên chỉ có **tối đa 1 hợp đồng active** tại một thời điểm
- Không thể xóa phòng khi có sinh viên đang ở
- Không thể xóa sinh viên khi có hợp đồng active
- Phòng tự động chuyển trạng thái **Đầy** khi số người = sức chứa

### 3.2 Tính Toán Tự Động
- Tổng phiếu thu = Tiền phòng + Điện + Nước + Dịch vụ
- Tiền còn lại = Tổng phiếu - Đã thanh toán
- Trạng thái phòng tự cập nhật khi có hợp đồng mới / kết thúc

### 3.3 Cảnh Báo Hệ Thống
- ⚠️ Hợp đồng sắp hết hạn (trong vòng 30 ngày)
- 🔴 Sinh viên nợ phí quá 2 tháng
- 📋 Phòng bảo trì quá 30 ngày chưa hoàn thành

---

## 4. Yêu Cầu Phi Chức Năng

| Yêu cầu | Mô tả |
|---|---|
| **Hiệu năng** | Tải danh sách ≤ 1000 bản ghi trong < 2 giây |
| **Giao diện** | Responsive, thân thiện, dark mode |
| **Bảo mật** | Mật khẩu được hash (bcrypt), phân quyền theo role |
| **Dữ liệu** | Không mất dữ liệu khi tắt đột ngột (SQLite ACID) |
| **Nền tảng** | Windows 10/11 (primary), hỗ trợ cross-platform |
