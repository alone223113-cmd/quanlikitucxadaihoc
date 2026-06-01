"""
ui/zones.py — Trang quản lý Khu ký túc xá
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QAbstractItemView, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from models.zone import get_all_zones, get_zone_stats, add_zone, update_zone, delete_zone


GENDER_COLORS = {
    "Nam":      ("#1565C0", "#E3F2FD"),
    "Nữ":       ("#AD1457", "#FCE4EC"),
    "Hỗn hợp":  ("#4A148C", "#EDE7F6"),
}

GENDER_ICONS = {"Nam": "♂", "Nữ": "♀", "Hỗn hợp": "⚥"}


class ZonesPage(QWidget):
    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self.is_admin = current_user.get("role") == "admin"
        self._setup_ui()
        self.refresh()

    # ------------------------------------------------------------------ UI --
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("🏘️  Quản Lý Khu")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5;")

        self.add_btn = QPushButton("➕  Thêm Khu Mới")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setMinimumWidth(160)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setEnabled(self.is_admin)
        self.add_btn.clicked.connect(self._on_add)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4A9EFF,stop:1 #007ACC);
                color:white; border-radius:8px; font-size:13px; font-weight:600; padding:0 16px;
            }
            QPushButton:hover { background: #5AB0FF; }
            QPushButton:disabled { background: #2A3F5F; color:#4A6080; }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # Stats cards
        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(12)
        layout.addLayout(self.cards_row)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Tên Khu", "Loại", "Tổng Phòng", "Trống", "Đầy", "Bảo Trì", "Thao Tác"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(300)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for col in range(2, 7):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.table.setStyleSheet("""
            QTableWidget { background:#131F30; border:1px solid #1E3050; border-radius:8px; }
            QTableWidget::item { padding:6px 8px; color:#C8D8E8; border:none; }
            QTableWidget::item:alternate { background:#0F1A28; }
            QHeaderView::section { background:#1A2D4A; color:#8899B4; font-weight:600;
                                   border:none; padding:8px; font-size:12px; }
        """)
        layout.addWidget(self.table)

    # --------------------------------------------------------------- Refresh --
    def refresh(self):
        stats = get_zone_stats()
        self._rebuild_cards(stats)
        self._populate_table(stats)

    def _rebuild_cards(self, stats: list):
        # Xoá cards cũ
        while self.cards_row.count():
            item = self.cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for s in stats:
            card = self._make_stat_card(s)
            self.cards_row.addWidget(card)
        self.cards_row.addStretch()

    def _make_stat_card(self, s: dict) -> QFrame:
        fg, bg = GENDER_COLORS.get(s["gender_type"], ("#4A9EFF", "#1A2D4A"))
        icon = GENDER_ICONS.get(s["gender_type"], "🏘️")
        card = QFrame()
        card.setFixedSize(200, 100)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #1A2D4A, stop:1 #0F1A28);
                border: 1px solid {fg}55;
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        top = QHBoxLayout()
        name_lbl = QLabel(f"{icon} {s['name']}")
        name_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        name_lbl.setStyleSheet(f"color:{fg};")
        type_lbl = QLabel(s["gender_type"])
        type_lbl.setFont(QFont("Segoe UI", 9))
        type_lbl.setStyleSheet(f"color:#8899B4;")
        top.addWidget(name_lbl)
        top.addStretch()
        top.addWidget(type_lbl)
        lay.addLayout(top)

        rooms_lbl = QLabel(f"🏠 {s['total_rooms']} phòng  |  👤 {s['total_students']} SV")
        rooms_lbl.setFont(QFont("Segoe UI", 10))
        rooms_lbl.setStyleSheet("color:#A0B8CC;")
        lay.addWidget(rooms_lbl)

        avail_lbl = QLabel(
            f"✅ Trống: {s['available_rooms']}   🔴 Đầy: {s['full_rooms']}   🔧 BT: {s['maintenance_rooms']}"
        )
        avail_lbl.setFont(QFont("Segoe UI", 9))
        avail_lbl.setStyleSheet("color:#6A8899;")
        lay.addWidget(avail_lbl)
        return card

    def _populate_table(self, stats: list):
        self.table.setRowCount(len(stats))
        for row, s in enumerate(stats):
            self.table.setRowHeight(row, 48)

            # Tên
            name_item = QTableWidgetItem(f"  {GENDER_ICONS.get(s['gender_type'],'')}  {s['name']}")
            name_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            name_item.setData(Qt.UserRole, s["id"])
            self.table.setItem(row, 0, name_item)

            # Loại
            fg, _ = GENDER_COLORS.get(s["gender_type"], ("#4A9EFF", "#1A2D4A"))
            type_item = QTableWidgetItem(f"  {s['gender_type']}  ")
            type_item.setForeground(QColor(fg))
            type_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, type_item)

            # Số liệu
            for col, val in enumerate([
                s["total_rooms"], s["available_rooms"], s["full_rooms"], s["maintenance_rooms"]
            ], start=2):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if col == 3 and val > 0:
                    item.setForeground(QColor("#4CAF50"))
                elif col == 4 and val > 0:
                    item.setForeground(QColor("#FF5252"))
                elif col == 5 and val > 0:
                    item.setForeground(QColor("#FFA726"))
                self.table.setItem(row, col, item)

            # Thao tác
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            edit_btn = QPushButton("✏️ Sửa")
            edit_btn.setFixedHeight(30)
            edit_btn.setEnabled(self.is_admin)
            edit_btn.setStyleSheet(
                "QPushButton{background:#1A3A5C;color:#4A9EFF;border:1px solid #2A5080;border-radius:6px;padding:0 10px;}"
                "QPushButton:hover{background:#2A4A6C;}"
                "QPushButton:disabled{color:#3A5070;border-color:#1A2A3A;}"
            )
            edit_btn.clicked.connect(lambda _, sid=s["id"]: self._on_edit(sid))

            del_btn = QPushButton("🗑️ Xoá")
            del_btn.setFixedHeight(30)
            del_btn.setEnabled(self.is_admin)
            del_btn.setStyleSheet(
                "QPushButton{background:#3A1A1A;color:#FF5252;border:1px solid #5A2020;border-radius:6px;padding:0 10px;}"
                "QPushButton:hover{background:#4A2020;}"
                "QPushButton:disabled{color:#3A2020;border-color:#1A1A1A;}"
            )
            del_btn.clicked.connect(lambda _, sid=s["id"], sn=s["name"]: self._on_delete(sid, sn))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(row, 6, btn_widget)

    # ------------------------------------------------------------- Dialogs --
    def _on_add(self):
        dlg = ZoneDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            try:
                add_zone(dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã thêm khu mới.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _on_edit(self, zone_id: int):
        from models.zone import get_zone_by_id
        zone = get_zone_by_id(zone_id)
        if not zone:
            return
        dlg = ZoneDialog(parent=self, zone=dict(zone))
        if dlg.exec() == QDialog.Accepted:
            try:
                update_zone(zone_id, dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã cập nhật khu.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _on_delete(self, zone_id: int, zone_name: str):
        reply = QMessageBox.question(
            self, "Xác nhận xoá",
            f"Bạn có chắc muốn xoá khu <b>{zone_name}</b>?<br>"
            "Các phòng thuộc khu này sẽ không còn gắn khu.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                delete_zone(zone_id)
                self.refresh()
                QMessageBox.information(self, "Thành công", f"✅ Đã xoá khu {zone_name}.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))


# ===================================================================== Dialog
class ZoneDialog(QDialog):
    def __init__(self, parent=None, zone: dict = None):
        super().__init__(parent)
        self._zone = zone
        self.setWindowTitle("Thêm Khu Mới" if not zone else "Sửa Thông Tin Khu")
        self.setMinimumWidth(400)
        self._setup_ui()
        if zone:
            self._fill(zone)

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog { background:#0F1724; }
            QLabel { color:#C8D8E8; font-size:13px; }
            QLineEdit, QComboBox, QTextEdit {
                background:#1A2D4A; color:#E8EDF5; border:1px solid #2A4060;
                border-radius:6px; padding:6px 10px; font-size:13px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border-color:#4A9EFF; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Thêm Khu Mới" if not self._zone else "Sửa Thông Tin Khu")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#4A9EFF;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("VD: Khu A, Khu Nam...")
        self.name_edit.setMinimumHeight(38)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Hỗn hợp", "Nam", "Nữ"])
        self.gender_combo.setMinimumHeight(38)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Mô tả khu (tuỳ chọn)...")
        self.desc_edit.setMaximumHeight(80)

        form.addRow("Tên khu *:", self.name_edit)
        form.addRow("Loại:", self.gender_combo)
        form.addRow("Mô tả:", self.desc_edit)
        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Huỷ")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setStyleSheet(
            "QPushButton{background:#1A2D4A;color:#8899B4;border:1px solid #2A3F5F;border-radius:8px;padding:0 20px;}"
            "QPushButton:hover{background:#253D5A;}"
        )
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("💾  Lưu")
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4A9EFF,stop:1 #007ACC);"
            "color:white;border-radius:8px;font-weight:600;padding:0 24px;}"
            "QPushButton:hover{background:#5AB0FF;}"
        )
        save_btn.clicked.connect(self._on_save)

        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _fill(self, z: dict):
        self.name_edit.setText(z.get("name", ""))
        idx = self.gender_combo.findText(z.get("gender_type", "Hỗn hợp"))
        if idx >= 0:
            self.gender_combo.setCurrentIndex(idx)
        self.desc_edit.setPlainText(z.get("description", "") or "")

    def _on_save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên khu.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "gender_type": self.gender_combo.currentText(),
            "description": self.desc_edit.toPlainText().strip() or None,
        }
