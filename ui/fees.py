"""
ui/fees.py — Màn hình Quản Lý Thu Phí (Theo Phòng)
  - Tiền điện: nhập chỉ số công tơ đầu/cuối, tự tính kWh × đơn giá
  - Tiền nước: nhập m³, tự tính theo đầu người
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QMessageBox, QHeaderView, QDialog, QFormLayout,
    QSizePolicy, QLabel, QDoubleSpinBox, QSpinBox, QDialogButtonBox,
    QFrame, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from models.fee import (
    get_fees_by_month, create_monthly_fees, update_fee,
    calc_electricity, calc_water_total, calc_water_per_person
)
from utils.helpers import current_year, current_month, format_currency

# ─────────────────────────── Hằng số mặc định ────────────────────────────────
DEFAULT_ELEC_UNIT  = 3_500    # ₫/kWh
DEFAULT_WATER_UNIT = 15_000   # ₫/m³


# ══════════════════════════════════════════════════════════════════════════════
#  Dialog nhập chi phí
# ══════════════════════════════════════════════════════════════════════════════
class FeeEditDialog(QDialog):
    def __init__(self, fee: dict, parent=None):
        super().__init__(parent)
        self.fee = fee
        self.setWindowTitle(
            f"Nhập Chi Phí — Phòng {fee['room_number']}  Tháng {fee['month']}/{fee['year']}"
        )
        self.setMinimumWidth(500)
        self._setup_ui()

    # ─────────────────────────────────────── UI ───────────────────────────────
    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog  { background:#0F1724; }
            QGroupBox {
                color:#8899B4; font-size:12px; font-weight:600;
                border:1px solid #2A3F5F; border-radius:8px; margin-top:10px;
                padding:10px 12px;
            }
            QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 6px; }
            QLabel   { color:#C8D8E8; font-size:12px; }
            QDoubleSpinBox, QSpinBox {
                background:#1A2D4A; color:#E8EDF5; border:1px solid #2A4060;
                border-radius:6px; padding:4px 8px; font-size:13px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus { border-color:#4A9EFF; }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(12)

        # Title
        hdr = QLabel(
            f"🏠 Phòng {self.fee['room_number']} — Tháng {self.fee['month']}/{self.fee['year']}"
        )
        hdr.setFont(QFont("Segoe UI", 14, QFont.Bold))
        hdr.setStyleSheet("color:#4A9EFF;")
        main.addWidget(hdr)

        # ── Section Điện ──────────────────────────────────────────────────────
        elec_box = QGroupBox("🔌  Tiền Điện  (tính theo công tơ)")
        elec_lay = QFormLayout(elec_box)
        elec_lay.setSpacing(8)

        def dbl(val=0, maxv=999999, step=1, suffix=""):
            s = QDoubleSpinBox()
            s.setRange(0, maxv)
            s.setDecimals(1)
            s.setSingleStep(step)
            s.setValue(val or 0)
            if suffix:
                s.setSuffix(f"  {suffix}")
            s.setMinimumHeight(34)
            return s

        f = self.fee
        self.elec_prev = dbl(f.get("elec_prev_reading"), 999999, 1, "kWh")
        self.elec_curr = dbl(f.get("elec_curr_reading"), 999999, 1, "kWh")
        self.elec_unit = dbl(f.get("elec_unit_price") or DEFAULT_ELEC_UNIT, 50000, 100, "₫/kWh")

        # Read-only display
        self.elec_kwh_lbl  = QLabel("0.0 kWh")
        self.elec_kwh_lbl.setStyleSheet("color:#FFD93D; font-weight:600; font-size:13px;")
        self.elec_total_lbl = QLabel("0 ₫")
        self.elec_total_lbl.setStyleSheet("color:#FFB347; font-weight:700; font-size:14px;")

        elec_lay.addRow(_lbl("Chỉ số đầu kỳ:"), self.elec_prev)
        elec_lay.addRow(_lbl("Chỉ số cuối kỳ:"), self.elec_curr)
        elec_lay.addRow(_lbl("Đơn giá:"),         self.elec_unit)
        elec_lay.addRow(_lbl("Tiêu thụ:"),        self.elec_kwh_lbl)
        elec_lay.addRow(_lbl("Thành tiền điện:"), self.elec_total_lbl)

        for w in [self.elec_prev, self.elec_curr, self.elec_unit]:
            w.valueChanged.connect(self._recalc)

        main.addWidget(elec_box)

        # ── Section Nước ──────────────────────────────────────────────────────
        water_box = QGroupBox("💧  Tiền Nước  (tính theo đầu người)")
        water_lay = QFormLayout(water_box)
        water_lay.setSpacing(8)

        self.water_m3   = dbl(f.get("water_cubic_meters"), 9999, 0.5, "m³")
        self.water_unit = dbl(f.get("water_unit_price") or DEFAULT_WATER_UNIT, 100000, 500, "₫/m³")

        self.water_persons = QSpinBox()
        self.water_persons.setRange(1, 20)
        self.water_persons.setMinimumHeight(34)
        self.water_persons.setSuffix("  người")
        self.water_persons.setValue(int(f.get("water_num_persons") or 1))

        self.water_total_lbl  = QLabel("0 ₫  (tổng phòng)")
        self.water_total_lbl.setStyleSheet("color:#74C0FC; font-weight:700; font-size:14px;")
        self.water_person_lbl = QLabel("0 ₫ / người")
        self.water_person_lbl.setStyleSheet("color:#4FC3F7; font-size:12px;")

        water_lay.addRow(_lbl("Tổng m³ (cả phòng):"), self.water_m3)
        water_lay.addRow(_lbl("Đơn giá:"),             self.water_unit)
        water_lay.addRow(_lbl("Số người chia:"),       self.water_persons)
        water_lay.addRow(_lbl("Tổng tiền nước:"),      self.water_total_lbl)
        water_lay.addRow(_lbl("Mỗi người trả:"),       self.water_person_lbl)

        for w in [self.water_m3, self.water_unit]:
            w.valueChanged.connect(self._recalc)
        self.water_persons.valueChanged.connect(self._recalc)

        main.addWidget(water_box)

        # ── Section Phí khác ──────────────────────────────────────────────────
        other_box = QGroupBox("💼  Phí Khác")
        other_lay = QFormLayout(other_box)
        other_lay.setSpacing(8)

        def money_spin(val=0):
            s = QDoubleSpinBox()
            s.setRange(0, 99_999_999)
            s.setDecimals(0)
            s.setSingleStep(10_000)
            s.setSuffix("  ₫")
            s.setValue(val or 0)
            s.setMinimumHeight(34)
            return s

        self.room_fee_inp  = money_spin(f.get("room_fee", 0))
        self.service_inp   = money_spin(f.get("service_fee", 0))

        other_lay.addRow(_lbl("Tiền phòng:"),   self.room_fee_inp)
        other_lay.addRow(_lbl("Phí dịch vụ:"),  self.service_inp)

        self.room_fee_inp.valueChanged.connect(self._recalc)
        self.service_inp.valueChanged.connect(self._recalc)

        main.addWidget(other_box)

        # ── Tổng cộng ────────────────────────────────────────────────────────
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#2A3F5F;")
        main.addWidget(sep)

        self.grand_total_lbl = QLabel()
        self.grand_total_lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.grand_total_lbl.setStyleSheet("color:#51CF66;")
        self.grand_total_lbl.setAlignment(Qt.AlignRight)
        main.addWidget(self.grand_total_lbl)

        # ── Buttons ──────────────────────────────────────────────────────────
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.Save).setText("💾  Lưu")
        btns.button(QDialogButtonBox.Cancel).setText("Hủy")
        main.addWidget(btns)

        self._recalc()  # Initial calculation

    # ─────────────────────────────────── Tính toán live ──────────────────────
    def _recalc(self):
        # Điện
        prev = self.elec_prev.value()
        curr = self.elec_curr.value()
        u_e  = self.elec_unit.value()
        kwh  = max(0.0, curr - prev)
        elec_fee = calc_electricity(prev, curr, u_e)
        self.elec_kwh_lbl.setText(f"{kwh:.1f} kWh")
        self.elec_total_lbl.setText(f"⚡ {format_currency(elec_fee)}")

        # Nước
        m3       = self.water_m3.value()
        u_w      = self.water_unit.value()
        persons  = self.water_persons.value()
        w_total  = calc_water_total(m3, u_w)
        w_person = calc_water_per_person(m3, u_w, persons)
        self.water_total_lbl.setText(f"💧 {format_currency(w_total)}")
        self.water_person_lbl.setText(f"≈ {format_currency(w_person)} / người")

        # Grand total
        grand = (self.room_fee_inp.value() + elec_fee + w_total + self.service_inp.value())
        self.grand_total_lbl.setText(f"💰 Tổng: {format_currency(grand)}")

    # ─────────────────────────────────── Data ────────────────────────────────
    def get_data(self) -> dict:
        prev     = self.elec_prev.value() or None
        curr     = self.elec_curr.value() or None
        u_e      = self.elec_unit.value()
        elec_fee = calc_electricity(prev or 0, curr or 0, u_e)

        m3       = self.water_m3.value() or None
        u_w      = self.water_unit.value()
        persons  = self.water_persons.value()
        w_fee    = calc_water_total(m3 or 0, u_w)

        room_fee = self.room_fee_inp.value()
        service  = self.service_inp.value()
        total    = room_fee + elec_fee + w_fee + service

        d = dict(self.fee)
        d.update({
            "room_fee":          room_fee,
            "elec_prev_reading": prev,
            "elec_curr_reading": curr,
            "elec_unit_price":   u_e,
            "electricity_fee":   elec_fee,
            "water_cubic_meters":m3,
            "water_unit_price":  u_w,
            "water_num_persons": persons,
            "water_fee":         w_fee,
            "service_fee":       service,
            "total_amount":      total,
            "paid_date":         d.get("paid_date"),
            "notes":             d.get("notes"),
        })
        return d


# ─────────────────────── Helper label ────────────────────────────────────────
def _lbl(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#8899B4; font-size:12px;")
    return l


# ══════════════════════════════════════════════════════════════════════════════
#  Trang Thu Phí
# ══════════════════════════════════════════════════════════════════════════════
class FeesPage(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.fees = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet("QFrame { background-color: #1A2537; border-bottom: 1px solid #2A3F5F; }")
        header.setFixedHeight(60)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("💰 Quản Lý Thu Phí")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5; background: transparent;")

        self.gen_btn = QPushButton("⚡  Sinh Hóa Đơn Tự Động")
        self.gen_btn.setFixedHeight(36)
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.clicked.connect(self._generate_fees)

        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.gen_btn)
        layout.addWidget(header)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #0F1724;")
        t_layout = QHBoxLayout(toolbar)
        t_layout.setContentsMargins(24, 10, 24, 10)
        t_layout.setSpacing(10)

        lbl_thang = QLabel("Tháng:")
        lbl_thang.setStyleSheet("color: #8899B4; font-size: 12px;")
        self.month_cb = QComboBox()
        self.month_cb.addItems([str(i) for i in range(1, 13)])
        self.month_cb.setCurrentText(str(current_month()))
        self.month_cb.setFixedWidth(70)

        lbl_nam = QLabel("Năm:")
        lbl_nam.setStyleSheet("color: #8899B4; font-size: 12px;")
        self.year_cb = QComboBox()
        self.year_cb.addItems([str(y) for y in range(2024, 2030)])
        self.year_cb.setCurrentText(str(current_year()))
        self.year_cb.setFixedWidth(90)

        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("color: #8899B4; font-size: 12px;")

        t_layout.addWidget(lbl_thang)
        t_layout.addWidget(self.month_cb)
        t_layout.addWidget(lbl_nam)
        t_layout.addWidget(self.year_cb)
        t_layout.addStretch()
        t_layout.addWidget(self.stats_lbl)
        layout.addWidget(toolbar)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Phòng", "Toà", "Tiền Phòng", "⚡ Điện", "💧 Nước",
            "Tổng Cộng", "Trạng Thái", "Sửa"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(6, QHeaderView.Fixed)
        hh.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 170)
        self.table.setColumnWidth(7, 60)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.table, 1)

        self.month_cb.currentIndexChanged.connect(self.refresh)
        self.year_cb.currentIndexChanged.connect(self.refresh)

    # ─────────────────────────────── Refresh ─────────────────────────────────
    def refresh(self):
        m = int(self.month_cb.currentText())
        y = int(self.year_cb.currentText())
        raw = get_fees_by_month(m, y)
        self.fees = [dict(f) if not isinstance(f, dict) else f for f in raw]
        self.table.setRowCount(len(self.fees))
        self.table.blockSignals(True)

        total_due  = 0
        paid_count = 0

        for i, f in enumerate(self.fees):
            def item(val, color=None):
                it = QTableWidgetItem(str(val))
                it.setTextAlignment(Qt.AlignCenter)
                if color:
                    it.setForeground(QColor(color))
                return it

            self.table.setItem(i, 0, item(f.get("room_number", "")))
            self.table.setItem(i, 1, item(f.get("building", "")))
            self.table.setItem(i, 2, item(format_currency(f.get("room_fee", 0) or 0)))

            # ── Cột Điện: hiển thị kWh nếu có chỉ số công tơ ──────────────
            elec_fee  = f.get("electricity_fee", 0) or 0
            elec_prev = f.get("elec_prev_reading")
            elec_curr = f.get("elec_curr_reading")
            if elec_prev is not None and elec_curr is not None:
                kwh = max(0.0, (elec_curr or 0) - (elec_prev or 0))
                elec_txt = f"{kwh:.0f} kWh → {format_currency(elec_fee)}"
            else:
                elec_txt = format_currency(elec_fee) if elec_fee > 0 else "—"
            self.table.setItem(i, 3, item(elec_txt, "#FFD93D" if elec_fee > 0 else None))

            # ── Cột Nước: hiển thị m³/người nếu có dữ liệu ─────────────────
            water_fee = f.get("water_fee", 0) or 0
            water_m3  = f.get("water_cubic_meters")
            water_persons = f.get("water_num_persons")
            if water_m3 is not None:
                person_str = f"/{water_persons}n" if water_persons else ""
                water_txt = f"{water_m3:.1f}m³{person_str} → {format_currency(water_fee)}"
            else:
                water_txt = format_currency(water_fee) if water_fee > 0 else "—"
            self.table.setItem(i, 4, item(water_txt, "#74C0FC" if water_fee > 0 else None))

            self.table.setItem(i, 5, item(format_currency(f.get("total_amount", 0) or 0), "#E8EDF5"))

            # ── Trạng thái dropdown ─────────────────────────────────────────
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            h = QHBoxLayout(container)
            h.setContentsMargins(4, 2, 4, 2)
            h.setSpacing(0)

            status_cb = QComboBox()
            status_cb.addItems(["Chưa thanh toán", "Đã thanh toán"])
            status_cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            is_paid = f.get("status") == "paid"
            status_cb.setCurrentText("Đã thanh toán" if is_paid else "Chưa thanh toán")
            color = "#51CF66" if is_paid else "#FFB4B4"
            status_cb.setStyleSheet(f"""
                QComboBox {{
                    color: {color};
                    background-color: #1A2537;
                    border: 1px solid #2A3F5F;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-weight: bold;
                }}
                QComboBox::drop-down {{ border: none; width: 20px; }}
                QComboBox QAbstractItemView {{
                    background-color: #1A2537; color: #E8EDF5;
                    selection-background-color: #2A3F5F;
                    border: 1px solid #2A3F5F;
                }}
            """)
            status_cb.currentTextChanged.connect(lambda text, row=i: self._on_status_changed(row, text))
            h.addWidget(status_cb)
            self.table.setCellWidget(i, 6, container)

            # ── Nút sửa ────────────────────────────────────────────────────
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Nhập tiền điện, nước, dịch vụ")
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setFixedSize(36, 36)
            edit_btn.clicked.connect(lambda _, row=i: self._edit_fee(row))
            self.table.setCellWidget(i, 7, edit_btn)
            self.table.setRowHeight(i, 46)

            total_due += f.get("total_amount", 0) or 0
            if is_paid:
                paid_count += 1

        self.table.blockSignals(False)
        self.stats_lbl.setText(
            f"Tháng {m}/{y}  |  Tổng: {len(self.fees)} phòng  |  "
            f"Đã thu: {paid_count}  |  Tổng tiền: {format_currency(total_due)}"
        )

    # ─────────────────────────────── Actions ─────────────────────────────────
    def _on_status_changed(self, row: int, new_status: str):
        f = self.fees[row]
        data = dict(f)
        # Đảm bảo các key mới luôn có mặt
        _ensure_fee_keys(data)
        if new_status == "Đã thanh toán" and f.get("status") != "paid":
            data["paid_amount"] = f.get("total_amount", 0)
            data["status"] = "paid"
            try:
                update_fee(f["id"], data)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))
            self.refresh()
        elif new_status == "Chưa thanh toán" and f.get("status") == "paid":
            data["paid_amount"] = 0
            data["status"] = "unpaid"
            try:
                update_fee(f["id"], data)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))
            self.refresh()

    def _edit_fee(self, row: int):
        f = self.fees[row]
        dlg = FeeEditDialog(f, parent=self)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            # Đảm bảo status & paid_amount được giữ nguyên
            data.setdefault("status",      f.get("status", "unpaid"))
            data.setdefault("paid_amount", f.get("paid_amount", 0))
            try:
                update_fee(f["id"], data)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật:\n{str(e)}")

    def _generate_fees(self):
        m = int(self.month_cb.currentText())
        y = int(self.year_cb.currentText())
        try:
            created = create_monthly_fees(m, y)
            QMessageBox.information(
                self, "Tạo Hóa Đơn",
                f"Đã sinh {created} hóa đơn cho tháng {m}/{y}.\n"
                f"Click ✏️ để nhập chỉ số điện và m³ nước cho từng phòng."
            )
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))


# ─────────────────────── Utility ─────────────────────────────────────────────
def _ensure_fee_keys(data: dict):
    """Đảm bảo dict luôn có đủ các key mới để tránh lỗi khi update."""
    defaults = {
        "elec_prev_reading":  None,
        "elec_curr_reading":  None,
        "elec_unit_price":    DEFAULT_ELEC_UNIT,
        "water_cubic_meters": None,
        "water_unit_price":   DEFAULT_WATER_UNIT,
        "water_num_persons":  None,
        "paid_date":          None,
        "notes":              None,
    }
    for k, v in defaults.items():
        data.setdefault(k, v)
