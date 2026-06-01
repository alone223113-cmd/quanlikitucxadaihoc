"""
ui/main_window.py — Cửa sổ chính với sidebar navigation
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from ui.dashboard import DashboardPage
from ui.zones import ZonesPage
from ui.rooms import RoomsPage
from ui.students import StudentsPage
from ui.fees import FeesPage
from ui.violations import ViolationsPage
from ui.reports import ReportsPage
from ui.users import UsersPage


class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.current_user = user
        self.setWindowTitle("KTX Manager — Hệ Thống Quản Lý Ký Túc Xá")
        self.setMinimumSize(1280, 800)
        self._setup_ui()
        self._navigate(0)  # Mở Dashboard mặc định

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._create_sidebar()
        # Content area
        content = self._create_content_area()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo area
        logo_area = QWidget()
        logo_area.setStyleSheet("background-color: #152033; border-bottom: 1px solid #2A3F5F;")
        logo_layout = QVBoxLayout(logo_area)
        logo_layout.setContentsMargins(16, 20, 16, 20)
        logo_layout.setSpacing(4)

        logo_icon = QLabel("🏛️")
        logo_icon.setFont(QFont("Segoe UI", 28))
        logo_icon.setAlignment(Qt.AlignCenter)

        logo_text = QLabel("KTX Manager")
        logo_text.setFont(QFont("Segoe UI", 14, QFont.Bold))
        logo_text.setAlignment(Qt.AlignCenter)
        logo_text.setStyleSheet("color: #4A9EFF; letter-spacing: 1px;")

        logo_sub = QLabel("Quản Lý Ký Túc Xá")
        logo_sub.setFont(QFont("Segoe UI", 10))
        logo_sub.setAlignment(Qt.AlignCenter)
        logo_sub.setStyleSheet("color: #8899B4;")

        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_text)
        logo_layout.addWidget(logo_sub)

        # Nav items
        nav_items = [
            ("📊", "Dashboard", 0),
            ("🏘️", "Quản Lý Khu", 1),
            ("🏠", "Quản Lý Phòng", 2),
            ("👤", "Sinh Viên / HĐ", 3),
            ("💰", "Thu Phí", 4),
            ("⚠️", "Vi Phạm", 5),
            ("📈", "Báo Cáo", 6),
        ]
        if self.current_user.get("role") == "admin":
            nav_items.append(("👥", "Người Dùng", 7))

        self._nav_buttons = []
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 16, 8, 8)
        nav_layout.setSpacing(2)

        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("nav_btn")
            btn.setProperty("active", "false")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(44)
            btn.setFont(QFont("Segoe UI", 13))
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            nav_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        nav_layout.addStretch()

        # User info at bottom
        user_area = QWidget()
        user_area.setStyleSheet("background-color: #152033; border-top: 1px solid #2A3F5F;")
        user_layout = QVBoxLayout(user_area)
        user_layout.setContentsMargins(16, 12, 16, 12)
        user_layout.setSpacing(4)

        role_text = "👑 Quản trị viên" if self.current_user.get("role") == "admin" else "👔 Nhân viên"
        user_name_lbl = QLabel(self.current_user.get("full_name", ""))
        user_name_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        user_name_lbl.setStyleSheet("color: #E8EDF5;")

        role_lbl = QLabel(role_text)
        role_lbl.setFont(QFont("Segoe UI", 11))
        role_lbl.setStyleSheet("color: #4A9EFF;")

        logout_btn = QPushButton("🚪  Đăng Xuất")
        logout_btn.setProperty("class", "ghost")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setMinimumHeight(36)
        logout_btn.clicked.connect(self._logout)

        user_layout.addWidget(user_name_lbl)
        user_layout.addWidget(role_lbl)
        user_layout.addWidget(logout_btn)

        layout.addWidget(logo_area)
        layout.addWidget(nav_widget, 1)
        layout.addWidget(user_area)
        return sidebar

    def _create_content_area(self) -> QWidget:
        content = QWidget()
        content.setObjectName("content_panel")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked pages
        self.stack = QStackedWidget()
        self.pages = [
            DashboardPage(self.current_user),   # 0
            ZonesPage(self.current_user),        # 1
            RoomsPage(self.current_user),        # 2
            StudentsPage(self.current_user),     # 3
            FeesPage(self.current_user),         # 4
            ViolationsPage(self.current_user),   # 5
            ReportsPage(self.current_user),      # 6
        ]
        if self.current_user.get("role") == "admin":
            self.pages.append(UsersPage(self.current_user))  # 7
        for page in self.pages:
            self.stack.addWidget(page)

        layout.addWidget(self.stack)
        return content

    def _navigate(self, index: int):
        self.stack.setCurrentIndex(index)
        # Cập nhật trạng thái các nút nav
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Refresh page nếu có method refresh
        page = self.pages[index]
        if hasattr(page, "refresh"):
            page.refresh()

    def _logout(self):
        reply = QMessageBox.question(
            self, "Đăng Xuất",
            "Bạn có chắc muốn đăng xuất?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.close()  # main.py sẽ xử lý việc quay lại màn hình login
