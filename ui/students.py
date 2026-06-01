"""
ui/students.py — Quản lý Sinh viên & Hợp Đồng (schema gộp)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMessageBox, QDialog, QFormLayout,
    QHeaderView, QLabel, QFrame, QDialogButtonBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from models.student import get_all_students, add_student, update_student, delete_student
from models.room import get_available_rooms
from datetime import datetime


STATUS_COLORS = {
    "active":  ("#51CF66", "#1A3A25"),
    "left":    ("#FF6B6B", "#3A1A1A"),
    "none":    ("#8899B4", "#1E2D42"),
}
STATUS_VI = {
    "active": "Đang ở",
    "left":   "Đã rời",
    "none":   "Chưa xếp",
}


class StudentDialog(QDialog):
    def __init__(self, student_data=None, parent=None):
        super().__init__(parent)
        self.student_data = student_data
        self.setWindowTitle("Chỉnh Sửa Lưu Trú" if student_data else "Tạo Phiếu Lưu Trú")
        self.setMinimumWidth(480)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel(self.windowTitle())
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #4A9EFF;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet("color: #8899B4; font-size: 12px;")
            return l

        # ── Thông tin cá nhân ──
        sep1 = QLabel("── Thông tin cá nhân ──")
        sep1.setStyleSheet("color: #4A9EFF; font-size: 11px; font-weight: bold;")
        form.addRow(sep1)

        self.id_card_inp = QLineEdit()
        self.id_card_inp.setPlaceholderText("VD: 001234567890")
        self.name_inp = QLineEdit()
        self.name_inp.setPlaceholderText("Họ và tên đầy đủ")
        self.phone_inp = QLineEdit()
        self.phone_inp.setPlaceholderText("SĐT liên hệ")

        form.addRow(lbl("CCCD/CMND *:"), self.id_card_inp)
        form.addRow(lbl("Họ Tên *:"), self.name_inp)
        form.addRow(lbl("SĐT:"), self.phone_inp)

        # ── Thông tin lưu trú ──
        sep2 = QLabel("── Thông tin lưu trú ──")
        sep2.setStyleSheet("color: #4A9EFF; font-size: 11px; font-weight: bold;")
        form.addRow(sep2)

        self.room_cb = QComboBox()
        self.room_cb.addItem("-- Chưa xếp phòng --", None)
        rooms = get_available_rooms()
        if self.student_data and self.student_data.get("room_id"):
            room_ids = [r["id"] for r in rooms]
            if self.student_data["room_id"] not in room_ids:
                self.room_cb.addItem(
                    f"{self.student_data.get('room_number','?')} (Đang ở)",
                    self.student_data["room_id"]
                )
        for r in rooms:
            self.room_cb.addItem(
                f"{r['room_number']} - Khu {r['building']} ({r['available_beds']} chỗ trống)",
                r["id"]
            )

        self.bed_inp = QLineEdit()
        self.bed_inp.setPlaceholderText("Số giường")
        self.checkin_inp = QLineEdit(datetime.today().strftime("%Y-%m-%d"))
        self.checkout_inp = QLineEdit()
        self.checkout_inp.setPlaceholderText("YYYY-MM-DD")
        self.deposit_inp = QLineEdit("0")
        self.deposit_inp.setPlaceholderText("0")
        self.status_cb = QComboBox()
        self.status_cb.addItems(["active", "left", "none"])

        form.addRow(lbl("Phòng:"), self.room_cb)
        form.addRow(lbl("Giường số:"), self.bed_inp)
        form.addRow(lbl("Ngày vào:"), self.checkin_inp)
        form.addRow(lbl("Ngày kết thúc:"), self.checkout_inp)
        form.addRow(lbl("Tiền cọc (₫):"), self.deposit_inp)
        form.addRow(lbl("Trạng thái:"), self.status_cb)

        # Fill dữ liệu nếu đang sửa
        if self.student_data:
            self.id_card_inp.setText(self.student_data.get("id_card", ""))
            self.name_inp.setText(self.student_data.get("full_name", ""))
            self.phone_inp.setText(self.student_data.get("phone", ""))
            idx = self.room_cb.findData(self.student_data.get("room_id"))
            if idx >= 0:
                self.room_cb.setCurrentIndex(idx)
            self.bed_inp.setText(str(self.student_data.get("bed_number") or ""))
            self.checkin_inp.setText(self.student_data.get("checkin_date") or "")
            self.checkout_inp.setText(self.student_data.get("checkout_date") or "")
            self.deposit_inp.setText(str(self.student_data.get("deposit", 0) or 0))
            self.status_cb.setCurrentText(self.student_data.get("residency_status", "none"))

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.Save).setText("💾  Lưu")
        btns.button(QDialogButtonBox.Cancel).setText("Hủy")
        layout.addWidget(btns)

    def get_data(self) -> dict:
        try:
            bed = int(self.bed_inp.text()) if self.bed_inp.text().strip() else None
        except ValueError:
            bed = None
        try:
            dep = float(self.deposit_inp.text()) if self.deposit_inp.text().strip() else 0.0
        except ValueError:
            dep = 0.0
        return {
            "full_name": self.name_inp.text().strip(),
            "id_card": self.id_card_inp.text().strip(),
            "date_of_birth": "2000-01-01",
            "gender": "Nam",
            "faculty": "",
            "class_name": "",
            "phone": self.phone_inp.text().strip(),
            "email": "",
            "hometown_address": "",
            "room_id": self.room_cb.currentData(),
            "bed_number": bed,
            "checkin_date": self.checkin_inp.text().strip() or None,
            "checkout_date": self.checkout_inp.text().strip() or None,
            "deposit": dep,
            "residency_status": self.status_cb.currentText(),
        }

    def validate(self) -> str | None:
        d = self.get_data()
        if not d["id_card"]:
            return "CCCD/CMND không được để trống."
        if not d["full_name"]:
            return "Họ tên không được để trống."
        return None


class StudentsPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.students = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QFrame()
        header.setStyleSheet("QFrame { background-color: #1A2537; border-bottom: 1px solid #2A3F5F; }")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("👤 Sinh Viên & Hợp Đồng")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5; background: transparent;")

        add_btn = QPushButton("＋  Thêm Mới")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_student)

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(add_btn)
        layout.addWidget(header)

        # ── Toolbar ──
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0F1724;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(24, 12, 24, 12)
        t_layout.setSpacing(12)

        self.search_inp = QLineEdit()
        self.search_inp.setPlaceholderText("🔍  Tìm theo CCCD, Tên, SĐT...")
        self.search_inp.setFixedWidth(280)
        self.search_inp.textChanged.connect(self.refresh)

        self.filter_status = QComboBox()
        self.filter_status.addItem("Tất cả TT", None)
        self.filter_status.addItem("Đang ở", "active")
        self.filter_status.addItem("Đã rời", "left")
        self.filter_status.addItem("Chưa xếp", "none")
        self.filter_status.setFixedWidth(140)
        self.filter_status.currentIndexChanged.connect(self.refresh)

        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("color: #8899B4; font-size: 12px;")

        t_layout.addWidget(self.search_inp)
        t_layout.addWidget(self.filter_status)
        t_layout.addStretch()
        t_layout.addWidget(self.stats_lbl)
        layout.addWidget(toolbar)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "CCCD", "Họ Tên", "SĐT",
            "Phòng", "Giường", "Ngày Vào", "Ngày Ra",
            "Trạng Thái", "Thao Tác"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(8, 160)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.table, 1)

    def refresh(self):
        search = self.search_inp.text().strip() or None
        status = self.filter_status.currentData()
        self.students = get_all_students(search=search, status=status)
        self.table.setRowCount(len(self.students))

        active_cnt = 0
        for i, s in enumerate(self.students):
            # Kiểm tra ngày kết thúc có quá hạn không
            checkout = s.get("checkout_date") or ""
            checkout_str = checkout or "—"
            is_overdue = False
            if checkout:
                try:
                    d = datetime.strptime(checkout[:10], "%Y-%m-%d")
                    is_overdue = d < datetime.now()
                except Exception:
                    pass

            room_str = s.get("room_number") or "—"
            if s.get("building"):
                room_str = f"{s['room_number']} ({s['building']})"

            cols = [
                s.get("id_card") or "",
                s.get("full_name") or "",
                s.get("phone") or "",
                room_str,
                str(s.get("bed_number") or "—"),
                s.get("checkin_date") or "—",
                checkout_str,
            ]
            for col, val in enumerate(cols):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                if col == 6 and is_overdue:
                    item.setForeground(QColor("#FF6B6B"))
                self.table.setItem(i, col, item)

            # Trạng thái badge
            st = s.get("residency_status") or "none"
            fg, bg = STATUS_COLORS.get(st, ("#8899B4", "#1E2D42"))
            st_item = QTableWidgetItem(STATUS_VI.get(st, st))
            st_item.setTextAlignment(Qt.AlignCenter)
            st_item.setForeground(QColor(fg))
            st_item.setBackground(QColor(bg))
            self.table.setItem(i, 7, st_item)

            # Nút thao tác
            action_w = QWidget()
            a_lay = QHBoxLayout(action_w)
            a_lay.setContentsMargins(4, 4, 4, 4)
            a_lay.setSpacing(6)

            edit_btn = QPushButton("✏️ Sửa")
            edit_btn.setToolTip("Sửa thông tin sinh viên")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setFixedHeight(30)
            edit_btn.setStyleSheet(
                "QPushButton{background:#1A3A5C;color:#4A9EFF;"
                "border:1px solid #2A5080;border-radius:6px;"
                "font-size:12px;padding:0 8px;}"
                "QPushButton:hover{background:#2A4A6C;}"
            )
            edit_btn.clicked.connect(lambda _, idx=i: self._edit_student(idx))

            del_btn = QPushButton("🗑 Xoá")
            del_btn.setToolTip("Xoá sinh viên")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setFixedHeight(30)
            del_btn.setStyleSheet(
                "QPushButton{background:#3A1A1A;color:#FF5252;"
                "border:1px solid #5A2020;border-radius:6px;"
                "font-size:12px;padding:0 8px;}"
                "QPushButton:hover{background:#4A2020;}"
            )
            del_btn.clicked.connect(lambda _, idx=i: self._delete_student(idx))

            a_lay.addWidget(edit_btn)
            a_lay.addWidget(del_btn)
            self.table.setCellWidget(i, 8, action_w)
            self.table.setRowHeight(i, 48)

            if st == "active":
                active_cnt += 1

        self.stats_lbl.setText(
            f"Tổng: {len(self.students)} người  |  Đang ở: {active_cnt}"
        )

    def _add_student(self):
        dlg = StudentDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            err = dlg.validate()
            if err:
                QMessageBox.warning(self, "Lỗi", err)
                return
            try:
                add_student(dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã thêm sinh viên!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể thêm:\n{str(e)}")

    def _edit_student(self, row_idx: int):
        s = self.students[row_idx]
        dlg = StudentDialog(student_data=dict(s), parent=self)
        if dlg.exec() == QDialog.Accepted:
            err = dlg.validate()
            if err:
                QMessageBox.warning(self, "Lỗi", err)
                return
            try:
                update_student(s["id"], dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã cập nhật!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật:\n{str(e)}")

    def _delete_student(self, row_idx: int):
        s = self.students[row_idx]
        reply = QMessageBox.question(
            self, "Xác Nhận Xóa",
            f"Xóa sinh viên {s['full_name']}?\nHành động này không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                delete_student(s["id"])
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))
