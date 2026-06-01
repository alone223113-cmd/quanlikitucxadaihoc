"""
ui/login.py — Màn hình đăng nhập
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap
from database.db import get_connection, verify_password


class LoginWindow(QWidget):
    login_success = Signal(dict)  # Phát ra thông tin user khi đăng nhập thành công

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KTX Manager — Đăng Nhập")
        self.setMinimumSize(900, 600)
        self._setup_ui()

    def _setup_ui(self):
        # Layout chính: hai cột
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Panel trái (brand)
        left_panel = self._create_left_panel()
        # Panel phải (form)
        right_panel = self._create_right_panel()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("left_panel")
        panel.setStyleSheet("""
            QWidget#left_panel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0A1930, stop:0.5 #1A2D50, stop:1 #0F2040);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        logo = QLabel("🏛️")
        logo.setFont(QFont("Segoe UI", 64))
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("KTX MANAGER")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4A9EFF; letter-spacing: 4px;")

        subtitle = QLabel("Hệ Thống Quản Lý\nKý Túc Xá Trường Đại Học")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #8899B4; line-height: 1.5;")

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #2A3F5F; margin: 16px 40px;")

        features = [
            "📊  Dashboard tổng quan trực quan",
            "🏠  Quản lý phòng & sinh viên",
            "📝  Hợp đồng & thu phí tự động",
            "📈  Báo cáo & thống kê chi tiết",
        ]
        for f in features:
            lbl = QLabel(f)
            lbl.setFont(QFont("Segoe UI", 12))
            lbl.setStyleSheet("color: #A0B4CC; padding: 2px 0;")
            layout.addWidget(lbl)

        layout.insertWidget(0, logo)
        layout.insertWidget(1, title)
        layout.insertWidget(2, subtitle)
        layout.insertWidget(3, divider)

        copyright_lbl = QLabel("© 2026 Ban Quản Lý KTX")
        copyright_lbl.setFont(QFont("Segoe UI", 10))
        copyright_lbl.setAlignment(Qt.AlignCenter)
        copyright_lbl.setStyleSheet("color: #4A6080;")
        layout.addStretch()
        layout.addWidget(copyright_lbl)

        return panel

    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("right_panel")
        panel.setStyleSheet("QWidget#right_panel { background-color: #0F1724; }")

        outer = QVBoxLayout(panel)
        outer.setAlignment(Qt.AlignCenter)

        # Login card
        card = QWidget()
        card.setObjectName("login_container")
        card.setFixedWidth(400)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(40, 40, 40, 40)

        # Title
        title = QLabel("Đăng Nhập Hệ Thống")
        title.setObjectName("login_title")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4A9EFF;")

        subtitle = QLabel("Nhập thông tin tài khoản để tiếp tục")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #8899B4; font-size: 13px; margin-bottom: 8px;")

        # Username
        lbl_user = QLabel("Tên đăng nhập")
        lbl_user.setStyleSheet("color: #8899B4; font-size: 12px; font-weight: 600;")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("👤  Nhập tên đăng nhập...")
        self.username_input.setMinimumHeight(44)
        self.username_input.returnPressed.connect(self._do_login)

        # Password
        lbl_pw = QLabel("Mật khẩu")
        lbl_pw.setStyleSheet("color: #8899B4; font-size: 12px; font-weight: 600;")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("🔒  Nhập mật khẩu...")
        self.password_input.setMinimumHeight(44)
        self.password_input.returnPressed.connect(self._do_login)

        # Error label (ẩn mặc định)
        self.error_label = QLabel()
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        # Login button
        self.login_btn = QPushButton("ĐĂNG NHẬP")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._do_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4A9EFF, stop:1 #007ACC);
                color: white; border-radius: 24px;
                font-size: 14px; font-weight: 700;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6AB4FF, stop:1 #1A8ADE);
            }
            QPushButton:pressed {
                background: #2D7FDF;
            }
        """)

        # Hint
        hint = QLabel("💡 Tài khoản mặc định: admin / admin123")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #4A6080; font-size: 11px;")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(8)
        card_layout.addWidget(lbl_user)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(lbl_pw)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_btn)
        card_layout.addSpacing(16)
        card_layout.addWidget(hint)

        outer.addWidget(card)
        return panel

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Đang xác thực...")

        try:
            conn = get_connection()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
            ).fetchone()
            conn.close()

            if user and verify_password(password, user["password_hash"]):
                self.error_label.hide()
                self.login_success.emit(dict(user))
            else:
                self._show_error("❌ Tên đăng nhập hoặc mật khẩu không đúng.")
        except Exception as e:
            self._show_error(f"Lỗi hệ thống: {str(e)}")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("ĐĂNG NHẬP")

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()
        self.password_input.clear()
        self.password_input.setFocus()
