"""
ui/violations.py — Màn hình Quản Lý Vi Phạm
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox, QDoubleSpinBox,
    QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from models.violation import (
    get_all_violations, add_violation, update_violation,
    mark_violation_paid, get_violation_types
)
from models.student import get_all_students
from database.db import get_connection
from utils.helpers import format_currency, format_date, today_str


class ViolationDialog(QDialog):
    def __init__(self, parent=None, user_id=None, vio_data=None):
        super().__init__(parent)
        self.user_id = user_id
        self.vio_data = vio_data
        self.setWindowTitle("Ghi Nhận Vi Phạm" if not vio_data else "Sửa Vi Phạm")
        self.setMinimumWidth(480)
        self._setup_ui()
        if vio_data:
            self._fill_data(vio_data)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(self.windowTitle())
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #FF6B6B;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet("color: #8899B4; font-size: 12px;")
            return l

        # Chọn sinh viên
        self.student_combo = QComboBox()
        self.student_combo.setFixedHeight(36)
        students = get_all_students()
        for sv in students:
            self.student_combo.addItem(
                f"{sv['id_card']} — {sv['full_name']}",
                sv["id"]
            )

        # Loại vi phạm
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        for vt in get_violation_types():
            self.type_combo.addItem(vt)

        # Mô tả
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Mô tả chi tiết vi phạm...")
        self.desc_input.setMaximumHeight(80)

        # Ngày vi phạm
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd/MM/yyyy")

        # Mức phạt
        self.fine_input = QDoubleSpinBox()
        self.fine_input.setRange(0, 10_000_000)
        self.fine_input.setSingleStep(50000)
        self.fine_input.setDecimals(0)
        self.fine_input.setSuffix(" ₫")

        form.addRow(lbl("Sinh viên *"), self.student_combo)
        form.addRow(lbl("Loại vi phạm *"), self.type_combo)
        form.addRow(lbl("Mô tả"), self.desc_input)
        form.addRow(lbl("Ngày vi phạm *"), self.date_input)
        form.addRow(lbl("Mức phạt (₫)"), self.fine_input)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.Save).setText("💾  Lưu")
        btns.button(QDialogButtonBox.Cancel).setText("Hủy")
        layout.addWidget(btns)

    def _fill_data(self, d):
        idx = self.student_combo.findData(d.get("student_id"))
        if idx >= 0:
            self.student_combo.setCurrentIndex(idx)
        idx2 = self.type_combo.findText(str(d.get("violation_type", "")))
        if idx2 >= 0:
            self.type_combo.setCurrentIndex(idx2)
        else:
            self.type_combo.setCurrentText(str(d.get("violation_type", "")))
        self.desc_input.setPlainText(str(d.get("description", "") or ""))
        vdate = d.get("violation_date", "")
        if vdate:
            try:
                parts = str(vdate)[:10].split("-")
                self.date_input.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except Exception:
                pass
        self.fine_input.setValue(float(d.get("fine_amount", 0) or 0))

    def get_data(self) -> dict:
        return {
            "student_id": self.student_combo.currentData(),
            "violation_type": self.type_combo.currentText().strip(),
            "description": self.desc_input.toPlainText().strip(),
            "violation_date": self.date_input.date().toString("yyyy-MM-dd"),
            "fine_amount": self.fine_input.value(),
            "recorded_by": self.user_id,
        }

    def validate(self) -> str | None:
        d = self.get_data()
        if not d["student_id"]:
            return "Vui lòng chọn sinh viên."
        if not d["violation_type"]:
            return "Loại vi phạm không được để trống."
        return None


class ViolationsPage(QWidget):
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

        title = QLabel("⚠️ Quản Lý Vi Phạm")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5; background: transparent;")

        add_btn = QPushButton("＋  Ghi Nhận Vi Phạm")
        add_btn.setFixedHeight(36)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_violation)

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(add_btn)
        layout.addWidget(header)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0F1724;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(24, 12, 24, 12)
        t_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Tìm sinh viên...")
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.refresh)

        self.type_filter = QComboBox()
        self.type_filter.addItem("Tất cả loại vi phạm", None)
        for vt in get_violation_types():
            self.type_filter.addItem(vt, vt)
        self.type_filter.setFixedWidth(240)
        self.type_filter.currentIndexChanged.connect(self.refresh)

        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd/MM/yy")
        self.from_date.setFixedWidth(110)
        self.from_date.dateChanged.connect(self.refresh)

        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd/MM/yy")
        self.to_date.setFixedWidth(110)
        self.to_date.dateChanged.connect(self.refresh)

        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("color: #8899B4; font-size: 12px;")

        from_lbl = QLabel("Từ:")
        from_lbl.setStyleSheet("color: #8899B4; font-size: 12px;")
        to_lbl = QLabel("→")
        to_lbl.setStyleSheet("color: #8899B4; font-size: 12px;")

        t_layout.addWidget(self.search_input)
        t_layout.addWidget(self.type_filter)
        t_layout.addWidget(from_lbl)
        t_layout.addWidget(self.from_date)
        t_layout.addWidget(to_lbl)
        t_layout.addWidget(self.to_date)
        t_layout.addStretch()
        t_layout.addWidget(self.stats_lbl)
        layout.addWidget(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Sinh Viên", "CCCD", "Loại Vi Phạm", "Ngày VP", "Mức Phạt", "Trạng Thái", "Ghi Bởi", "Thao Tác"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 100)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.table, 1)

    def refresh(self):
        search = self.search_input.text().strip() or None
        vt = self.type_filter.currentData()
        from_d = self.from_date.date().toString("yyyy-MM-dd")
        to_d = self.to_date.date().toString("yyyy-MM-dd")

        violations = get_all_violations(search=search, violation_type=vt,
                                        from_date=from_d, to_date=to_d)
        self.table.setRowCount(len(violations))
        total_fine = 0
        unpaid_count = 0

        for r_idx, v in enumerate(violations):
            is_paid = bool(v["is_paid"])
            row_data = [
                v["full_name"], v["cccd"],
                v["violation_type"], format_date(v["violation_date"]),
                format_currency(v["fine_amount"]),
            ]
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r_idx, col, item)

            # Status
            if is_paid:
                st_text, fg, bg = "✅ Đã nộp", "#51CF66", "#1A3A25"
            else:
                st_text, fg, bg = "🔴 Chưa nộp", "#FF6B6B", "#3A1A1A"
            st_item = QTableWidgetItem(st_text)
            st_item.setTextAlignment(Qt.AlignCenter)
            st_item.setForeground(QColor(fg))
            st_item.setBackground(QColor(bg))
            self.table.setItem(r_idx, 5, st_item)

            recorded_by = v["recorded_by_name"] or "—"
            rb_item = QTableWidgetItem(str(recorded_by))
            rb_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 6, rb_item)

            # Actions
            action_widget = QWidget()
            a_layout = QHBoxLayout(action_widget)
            a_layout.setContentsMargins(4, 0, 4, 0)
            a_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setProperty("class", "icon_btn")
            edit_btn.setToolTip("Sửa vi phạm")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setFixedSize(32, 32)
            edit_btn.clicked.connect(lambda checked, vid=v["id"]: self._edit_violation(vid))

            if not is_paid:
                pay_btn = QPushButton("💵")
                pay_btn.setProperty("class", "icon_btn")
                pay_btn.setToolTip("Đánh dấu đã nộp phạt")
                pay_btn.setCursor(Qt.PointingHandCursor)
                pay_btn.setFixedSize(32, 32)
                pay_btn.setStyleSheet("color: #51CF66;")
                pay_btn.clicked.connect(lambda checked, vid=v["id"]: self._mark_paid(vid))
                a_layout.addWidget(pay_btn)

            a_layout.addWidget(edit_btn)
            self.table.setCellWidget(r_idx, 7, action_widget)
            self.table.setRowHeight(r_idx, 48)

            total_fine += float(v["fine_amount"] or 0)
            if not is_paid:
                unpaid_count += 1

        self.stats_lbl.setText(
            f"Tổng: {len(violations)} vi phạm  |  Chưa nộp: {unpaid_count}  |  Tổng phạt: {format_currency(total_fine)}"
        )

    def _add_violation(self):
        dlg = ViolationDialog(self, user_id=self.user.get("id"))
        if dlg.exec() == QDialog.Accepted:
            err = dlg.validate()
            if err:
                QMessageBox.warning(self, "Lỗi", err)
                return
            try:
                add_violation(dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã ghi nhận vi phạm!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi:\n{str(e)}")

    def _edit_violation(self, vio_id: int):
        conn = get_connection()
        v = conn.execute("SELECT * FROM violations WHERE id=?", (vio_id,)).fetchone()
        conn.close()
        if not v:
            return
        dlg = ViolationDialog(self, user_id=self.user.get("id"), vio_data=dict(v))
        if dlg.exec() == QDialog.Accepted:
            err = dlg.validate()
            if err:
                QMessageBox.warning(self, "Lỗi", err)
                return
            d = dlg.get_data()
            d["is_paid"] = v["is_paid"]
            try:
                update_violation(vio_id, d)
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã cập nhật!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Lỗi:\n{str(e)}")

    def _mark_paid(self, vio_id: int):
        reply = QMessageBox.question(
            self, "Xác Nhận", "Đánh dấu vi phạm này là đã nộp phạt?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            mark_violation_paid(vio_id)
            self.refresh()
