"""
main.py — Điểm khởi động ứng dụng KTX Manager
"""
import sys
import os

# Đảm bảo import path đúng
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# MUST import matplotlib TRƯỚC PySide6 để tránh xung đột shiboken/six hook
try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot  # noqa: F401 – pre-load toàn bộ matplotlib
except Exception:
    pass  # Nếu không có matplotlib thì app vẫn chạy, biểu đồ bị ẩn


from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.db import initialize_database
from ui.login import LoginWindow
from ui.main_window import MainWindow


def load_stylesheet(app: QApplication):
    """Tải file QSS stylesheet."""
    qss_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"[Warning] Không tìm thấy stylesheet: {qss_path}")


def main():
    # Khởi tạo QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("KTX Manager")
    app.setApplicationDisplayName("Hệ Thống Quản Lý Ký Túc Xá")
    app.setApplicationVersion("1.0.0")

    # Tắt tính năng DPI scaling tự động nếu cần
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Set font mặc định
    font = QFont("Segoe UI", 13)
    app.setFont(font)

    # Tải stylesheet
    load_stylesheet(app)

    # Khởi tạo database (chạy lần đầu sẽ tạo schema + seed data)
    try:
        initialize_database()
        print("[OK] Database đã được khởi tạo.")
    except Exception as e:
        print(f"[ERROR] Không thể khởi tạo database: {e}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None, "Lỗi Khởi Động",
            f"Không thể khởi tạo cơ sở dữ liệu:\n{str(e)}\n\n"
            "Vui lòng kiểm tra lại cài đặt và thử lại."
        )
        sys.exit(1)

    # Biến lưu cửa sổ hiện tại
    current_window = [None]

    def show_login():
        """Hiển thị màn hình đăng nhập."""
        login = LoginWindow()
        login.login_success.connect(show_main)
        login.show()
        current_window[0] = login

    def show_main(user: dict):
        """Sau khi đăng nhập thành công, mở cửa sổ chính."""
        if current_window[0]:
            current_window[0].close()
        main_win = MainWindow(user)
        main_win.show()
        # Khi cửa sổ chính bị đóng (đăng xuất), quay lại login
        main_win.destroyed.connect(show_login)
        current_window[0] = main_win

    # Bắt đầu ứng dụng từ màn hình đăng nhập
    show_login()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
