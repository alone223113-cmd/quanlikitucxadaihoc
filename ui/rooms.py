"""
ui/rooms.py — Màn hình Quản Lý Phòng
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QSizePolicy,
    QSpinBox, QDoubleSpinBox, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

from models.room import get_all_rooms, add_room, update_room, delete_room, get_buildings, get_students_by_room
from models.zone import get_all_zones
from utils.helpers import format_currency, status_room_vi


class RoomStudentsDialog(QDialog):
    """Dialog hiển thị danh sách sinh viên đang ở trong phòng."""
    def __init__(self, room_id: int, room_number: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Sinh viên trong phòng {room_number}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"🏠 Phòng {room_number} — Danh sách sinh viên đang ở")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #4A9EFF;")
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["CCCD", "Họ Tên", "SĐT", "Giường", "Ngày Vào"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)

        students = get_students_by_room(room_id)
        table.setRowCount(len(students))
        if not students:
            table.setRowCount(1)
            empty = QTableWidgetItem("Phòng chưa có sinh viên nào")
            empty.setTextAlignment(Qt.AlignCenter)
            empty.setForeground(QColor("#8899B4"))
            table.setItem(0, 0, empty)
            table.setSpan(0, 0, 1, 5)
        else:
            for i, sv in enumerate(students):
                vals = [
                    sv.get("id_card") or "",
                    sv.get("full_name") or "",
                    sv.get("phone") or "",
                    str(sv.get("bed_number") or "—"),
                    sv.get("checkin_date") or "—",
                ]
                for col, val in enumerate(vals):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(i, col, item)
                table.setRowHeight(i, 40)

        layout.addWidget(table)

        close_btn = QPushButton("❌  Đóng")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)


STATUS_COLORS = {
    "available": ("#51CF66", "#1A3A25"),
    "full": ("#FF6B6B", "#3A1A1A"),
    "maintenance": ("#FFB347", "#3A2A10"),
}


class RoomDialog(QDialog):
    def __init__(self, parent=None, room_data=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm Phòng Mới" if not room_data else "Sửa Thông Tin Phòng")
        self.setMinimumWidth(420)
        self.room_data = room_data
        self._setup_ui()
        if room_data:
            self._fill_data(room_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #4A9EFF;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        self.room_number_input = QLineEdit()
        self.room_number_input.setPlaceholderText("VD: A101")
        self.building_input = QComboBox()
        self.building_input.addItems(["A", "B", "C", "D", "E"])
        self.building_input.setEditable(True)
        self.floor_input = QSpinBox()
        self.floor_input.setRange(1, 20)
        self.capacity_input = QComboBox()
        self.capacity_input.addItems(["2", "4", "6"])
        self.capacity_input.setCurrentText("4")
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 10_000_000)
        self.price_input.setSingleStep(50000)
        self.price_input.setValue(500000)
        self.price_input.setSuffix(" ₫")
        self.price_input.setDecimals(0)
        self.status_input = QComboBox()
        self.status_input.addItems(["available", "full", "maintenance"])
        self.zone_input = QComboBox()
        self.zone_input.addItem("-- Chưa phân khu --", None)
        for z in get_all_zones():
            self.zone_input.addItem(z["name"], z["id"])
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ghi chú thêm...")

        def lbl(t): return self._lbl(t)
        form.addRow(lbl("Mã phòng *"), self.room_number_input)
        form.addRow(lbl("Khu nhà *"), self.building_input)
        form.addRow(lbl("Tầng *"), self.floor_input)
        form.addRow(lbl("Sức chứa *"), self.capacity_input)
        form.addRow(lbl("Giá/tháng *"), self.price_input)
        form.addRow(lbl("Trạng thái *"), self.status_input)
        form.addRow(lbl("Khu"), self.zone_input)
        form.addRow(lbl("Mô tả"), self.desc_input)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.Save).setText("💾  Lưu")
        btns.button(QDialogButtonBox.Cancel).setText("Hủy")
        layout.addWidget(btns)

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("color: #8899B4; font-size: 12px;")
        return l

    def _fill_data(self, d):
        self.room_number_input.setText(str(d["room_number"]))
        idx = self.building_input.findText(str(d["building"]))
        if idx >= 0:
            self.building_input.setCurrentIndex(idx)
        else:
            self.building_input.setCurrentText(str(d["building"]))
        self.floor_input.setValue(int(d["floor"]))
        self.capacity_input.setCurrentText(str(d["capacity"]))
        self.price_input.setValue(float(d["price_per_month"]))
        idx2 = self.status_input.findText(str(d["status"]))
        if idx2 >= 0:
            self.status_input.setCurrentIndex(idx2)
        # Khu
        zone_id = d.get("zone_id")
        if zone_id:
            zi = self.zone_input.findData(zone_id)
            if zi >= 0:
                self.zone_input.setCurrentIndex(zi)
        self.desc_input.setText(str(d["description"] or ""))

    def get_data(self) -> dict:
        return {
            "room_number": self.room_number_input.text().strip(),
            "building": self.building_input.currentText().strip(),
            "floor": self.floor_input.value(),
            "capacity": int(self.capacity_input.currentText()),
            "room_type": f"{self.capacity_input.currentText()} người",
            "price_per_month": self.price_input.value(),
            "status": self.status_input.currentText(),
            "zone_id": self.zone_input.currentData(),
            "description": self.desc_input.text().strip(),
        }

    def validate(self) -> str | None:
        d = self.get_data()
        if not d["room_number"]:
            return "Mã phòng không được để trống."
        if not d["building"]:
            return "Khu nhà không được để trống."
        if d["price_per_month"] <= 0:
            return "Giá phòng phải lớn hơn 0."
        return None


class RoomsPage(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("QFrame { background-color: #1A2537; border-bottom: 1px solid #2A3F5F; }")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("🏠 Quản Lý Phòng")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5; background: transparent;")

        add_btn = QPushButton("＋  Thêm Phòng")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_room)

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(add_btn)
        layout.addWidget(header)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0F1724; padding: 12px 24px;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(24, 12, 24, 12)
        t_layout.setSpacing(12)

        self.filter_zone = QComboBox()
        self.filter_zone.addItem("Tất cả Khu", None)
        self.filter_zone.setFixedWidth(150)
        self.filter_zone.currentIndexChanged.connect(self.refresh)

        self.filter_building = QComboBox()
        self.filter_building.addItem("Tất cả Toà", None)
        self.filter_building.setFixedWidth(130)
        self.filter_building.currentIndexChanged.connect(self.refresh)

        self.filter_status = QComboBox()
        self.filter_status.addItems(["Tất cả TT", "available", "full", "maintenance"])
        self.filter_status.setFixedWidth(160)
        self.filter_status.currentIndexChanged.connect(self.refresh)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Tìm theo mã phòng...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.refresh)

        t_layout.addWidget(self.filter_zone)
        t_layout.addWidget(self.filter_building)
        t_layout.addWidget(self.filter_status)
        t_layout.addWidget(self.search_input)
        t_layout.addStretch()

        # Stats mini
        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("color: #8899B4; font-size: 12px;")
        t_layout.addWidget(self.stats_lbl)
        layout.addWidget(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Mã Phòng", "Toà", "Khu", "Tầng", "Sức Chứa", "Đang Ở", "Còn Trống",
            "Giá/Tháng", "Trạng Thái", "Thao Tác"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Fixed)
        self.table.setColumnWidth(9, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.table, 1)

    def refresh(self):
        # Load zones vào filter
        cur_zone = self.filter_zone.currentData()
        self.filter_zone.blockSignals(True)
        self.filter_zone.clear()
        self.filter_zone.addItem("Tất cả Khu", None)
        for z in get_all_zones():
            self.filter_zone.addItem(z["name"], z["id"])
        if cur_zone:
            zi = self.filter_zone.findData(cur_zone)
            if zi >= 0:
                self.filter_zone.setCurrentIndex(zi)
        self.filter_zone.blockSignals(False)

        # Load buildings vào filter
        current_building = self.filter_building.currentData()
        self.filter_building.blockSignals(True)
        self.filter_building.clear()
        self.filter_building.addItem("Tất cả Toà", None)
        for b in get_buildings():
            self.filter_building.addItem(f"Toà {b}", b)
        if current_building:
            idx = self.filter_building.findData(current_building)
            if idx >= 0:
                self.filter_building.setCurrentIndex(idx)
        self.filter_building.blockSignals(False)

        zone_id  = self.filter_zone.currentData()
        building = self.filter_building.currentData()
        status_text = self.filter_status.currentText()
        status = None if "Tất cả" in status_text else status_text
        search = self.search_input.text().strip()

        rooms = get_all_rooms(building=building, status=status, search=search, zone_id=zone_id)
        self.table.setRowCount(len(rooms))

        available_total = 0
        full_total = 0
        for r_idx, room in enumerate(rooms):
            zone_name = room["zone_name"] if room["zone_name"] else "—"
            items = [
                QTableWidgetItem(str(room["room_number"])),
                QTableWidgetItem(str(room["building"])),
                QTableWidgetItem(zone_name),
                QTableWidgetItem(str(room["floor"])),
                QTableWidgetItem(f"{room['capacity']} người"),
                QTableWidgetItem(str(room["occupied"])),
                QTableWidgetItem(str(room["available_beds"])),
                QTableWidgetItem(format_currency(room["price_per_month"])),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r_idx, col, item)

            # Status badge
            status_val = room["status"]
            color, bg = STATUS_COLORS.get(status_val, ("#E8EDF5", "#1E2D42"))
            status_item = QTableWidgetItem(status_room_vi(status_val))
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(color))
            status_item.setBackground(QColor(bg))
            self.table.setItem(r_idx, 8, status_item)

            if status_val == "available":
                available_total += 1
            elif status_val == "full":
                full_total += 1

            # Actions
            action_widget = QWidget()
            a_layout = QHBoxLayout(action_widget)
            a_layout.setContentsMargins(4, 0, 4, 0)
            a_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setProperty("class", "icon_btn")
            edit_btn.setToolTip("Sửa thông tin phòng")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setFixedSize(32, 32)
            edit_btn.clicked.connect(lambda checked, rid=room["id"]: self._edit_room(rid))

            del_btn = QPushButton("🗑️")
            del_btn.setProperty("class", "icon_btn_danger")
            del_btn.setToolTip("Xóa phòng")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedSize(32, 32)
            del_btn.clicked.connect(lambda checked, rid=room["id"]: self._delete_room(rid))

            view_sv_btn = QPushButton("👥")
            view_sv_btn.setProperty("class", "icon_btn")
            view_sv_btn.setToolTip("Xem sinh viên trong phòng")
            view_sv_btn.setCursor(Qt.PointingHandCursor)
            view_sv_btn.setFixedSize(32, 32)
            view_sv_btn.clicked.connect(
                lambda checked, rid=room["id"], rn=room["room_number"]: self._view_students(rid, rn)
            )

            a_layout.addWidget(edit_btn)
            a_layout.addWidget(view_sv_btn)
            a_layout.addWidget(del_btn)
            self.table.setCellWidget(r_idx, 9, action_widget)
            self.table.setRowHeight(r_idx, 48)

        self.stats_lbl.setText(f"Tổng: {len(rooms)} phòng  |  Trống: {available_total}  |  Đầy: {full_total}")

    def _add_room(self):
        dlg = RoomDialog(self)
        if dlg.exec() == QDialog.Accepted:
            err = dlg.validate()
            if err:
                QMessageBox.warning(self, "Lỗi", err)
                return
            try:
                add_room(dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã thêm phòng thành công!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể thêm phòng:\n{str(e)}")

    def _edit_room(self, room_id: int):
        from models.room import get_room_by_id
        room = get_room_by_id(room_id)
        if not room:
            return
        dlg = RoomDialog(self, room_data=dict(room))
        if dlg.exec() == QDialog.Accepted:
            err = dlg.validate()
            if err:
                QMessageBox.warning(self, "Lỗi", err)
                return
            try:
                update_room(room_id, dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã cập nhật thông tin phòng!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật:\n{str(e)}")

    def _delete_room(self, room_id: int):
        reply = QMessageBox.question(
            self, "Xác Nhận Xóa",
            "Bạn có chắc muốn xóa phòng này?\nHành động này không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                delete_room(room_id)
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã xóa phòng!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa:\n{str(e)}")

    def _view_students(self, room_id: int, room_number: str):
        dlg = RoomStudentsDialog(room_id, room_number, parent=self)
        dlg.exec()
