"""
ui/dashboard.py — Màn hình Trang Chủ / Thống Kê Tổng Quan
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor
from database.db import get_connection
from utils.helpers import format_currency

class StatCard(QFrame):
    def __init__(self, title, value, color, icon):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1E2D42;
                border-radius: 12px;
                border: 1px solid #2A3F5F;
            }}
            QFrame:hover {{
                border: 1px solid {color};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 28))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(50, 50)
        icon_lbl.setStyleSheet(f"background: rgba(255,255,255,0.05); border-radius: 25px; color: {color};")
        layout.addWidget(icon_lbl)

        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #8899B4; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold; border: none; background: transparent;")
        vbox.addWidget(title_lbl)
        vbox.addWidget(val_lbl)
        vbox.addStretch()

        layout.addLayout(vbox)
        layout.addStretch()

class DashboardPage(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("QFrame { background-color: #1A2537; border-bottom: 1px solid #2A3F5F; }")
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(32, 0, 32, 0)

        title = QLabel("Cổng Quản Trị KTX")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5; background: transparent;")
        
        user_lbl = QLabel(f"👤 {self.user['full_name']} ({'Quản trị viên' if self.user['role'] == 'admin' else 'Nhân viên'})")
        user_lbl.setStyleSheet("color: #4A9EFF; font-weight: bold; font-size: 14px; background: transparent;")

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(user_lbl)
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #0F1724;")
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(32, 32, 32, 32)
        self.content_layout.setSpacing(32)

        self.grid = QGridLayout()
        self.grid.setSpacing(24)
        self.content_layout.addLayout(self.grid)

        self.activity_area = QVBoxLayout()
        self.activity_area.setSpacing(16)
        lbl = QLabel("🔥 Hoạt Động Gần Đây / Hóa Đơn Trễ Hạn")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet("color: #E8EDF5;")
        self.activity_area.addWidget(lbl)
        
        self.content_layout.addLayout(self.activity_area)
        self.content_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        while self.activity_area.count() > 1:
            item = self.activity_area.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        try:
            conn = get_connection()
            rooms = conn.execute("SELECT COUNT(*) as c FROM rooms WHERE status != 'maintenance'").fetchone()["c"]
            available = conn.execute("SELECT COUNT(*) as c FROM rooms WHERE status='available'").fetchone()["c"]
            students = conn.execute("SELECT COUNT(DISTINCT id_card) as c FROM students WHERE residency_status='active'").fetchone()["c"]
            
            debts = conn.execute("SELECT SUM(total_amount - paid_amount) as c FROM fees WHERE status != 'paid'").fetchone()["c"] or 0

            self.grid.addWidget(StatCard("SỐ PHÒNG ĐANG MỞ", f"{rooms}", "#4A9EFF", "🚪"), 0, 0)
            self.grid.addWidget(StatCard("PHÒNG CÒN TRỐNG", f"{available}", "#51CF66", "🛏️"), 0, 1)
            self.grid.addWidget(StatCard("SINH VIÊN ĐANG LƯU TRÚ", f"{students}", "#Fcc419", "🧑‍🎓"), 1, 0)
            self.grid.addWidget(StatCard("TỔNG CÔNG NỢ", format_currency(debts), "#FF6B6B", "💵"), 1, 1)

            recent_fees = conn.execute("""
                SELECT r.room_number, f.month, f.year, (f.total_amount - f.paid_amount) as debt
                FROM fees f
                JOIN rooms r ON f.room_id = r.id
                WHERE f.status != 'paid'
                ORDER BY f.created_at DESC LIMIT 5
            """).fetchall()
            
            for rf in recent_fees:
                lbl = QLabel(f"🔴 Phòng {rf['room_number']}: Còn nợ {format_currency(rf['debt'])} (Tháng {rf['month']}/{rf['year']})")
                lbl.setStyleSheet("color: #FFB4B4; background-color: rgba(255,107,107,0.1); padding: 12px; border-left: 4px solid #FF6B6B; border-radius: 4px;")
                self.activity_area.addWidget(lbl)

        except Exception as e:
            err = QLabel(f"Lỗi tải dữ liệu: {e}")
            err.setStyleSheet("color: red;")
            self.activity_area.addWidget(err)
        finally:
            if 'conn' in locals(): conn.close()
