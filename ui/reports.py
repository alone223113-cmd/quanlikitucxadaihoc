"""
ui/reports.py — Báo Cáo & Thống Kê
  - Tab Doanh Thu: biểu đồ cột có/chưa thu theo tháng + summary cards
  - Tab Hiệu Suất Phòng: biểu đồ occupancy theo tháng/năm + pie chart
  - Tab Công Nợ: danh sách phòng nợ chi tiết, nhóm theo phòng, xuất CSV
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QFileDialog, QSizePolicy, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import csv, os

from database.db import get_connection
from utils.helpers import format_currency, current_year, current_month

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False


# ─────────────────────── Palette ─────────────────────────────────────────────
BG       = "#0F1724"
CARD_BG  = "#1A2D4A"
BORDER   = "#2A3F5F"
BLUE     = "#4A9EFF"
GREEN    = "#51CF66"
RED      = "#FF5252"
ORANGE   = "#FFA726"
YELLOW   = "#FFD93D"
CYAN     = "#74C0FC"
MPL_BG   = "#131F30"
MPL_GRID = "#1E3050"


# ══════════════════════════════════════════════════════════════════════════════
class ReportsPage(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self._setup_ui()
        self.refresh()

    # ──────────────────────────────────────── Layout ──────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet(f"QFrame{{background:#1A2537;border-bottom:1px solid {BORDER};}}")
        hdr.setFixedHeight(60)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 0, 24, 0)

        title = QLabel("📈  Báo Cáo & Thống Kê")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color:#E8EDF5;background:transparent;")

        self.year_cb = QComboBox()
        for y in range(2024, 2030):
            self.year_cb.addItem(str(y), y)
        self.year_cb.setCurrentText(str(current_year()))
        self.year_cb.setFixedWidth(90)
        self.year_cb.currentIndexChanged.connect(self.refresh)

        self.month_cb = QComboBox()
        self.month_cb.addItem("Cả năm", 0)
        for m in range(1, 13):
            self.month_cb.addItem(f"Tháng {m}", m)
        self.month_cb.setCurrentIndex(current_month())
        self.month_cb.setFixedWidth(110)
        self.month_cb.currentIndexChanged.connect(self.refresh)

        exp_btn = QPushButton("📄  Xuất CSV Công Nợ")
        exp_btn.setFixedHeight(36)
        exp_btn.setCursor(Qt.PointingHandCursor)
        exp_btn.clicked.connect(self._export_debt_csv)

        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(QLabel("Năm:"))
        hl.addWidget(self.year_cb)
        hl.addWidget(self.month_cb)
        hl.addWidget(exp_btn)
        root.addWidget(hdr)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane{{border:none;background:{BG};}}
            QTabBar::tab{{background:#1A2537;color:#8899B4;padding:10px 20px;font-size:13px;border:none;}}
            QTabBar::tab:selected{{background:{BG};color:{BLUE};border-bottom:2px solid {BLUE};}}
            QTabBar::tab:hover{{color:#C8D8E8;}}
        """)
        root.addWidget(self.tabs, 1)

        self._build_revenue_tab()
        self._build_efficiency_tab()
        self._build_debt_tab()
        self.tabs.currentChanged.connect(lambda _: self.refresh())

    # ══════════════════════════════ TAB DOANH THU ════════════════════════════
    def _build_revenue_tab(self):
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Summary cards row
        self._rev_cards = QHBoxLayout()
        lay.addLayout(self._rev_cards)

        # Chart
        if HAS_MPL:
            self._rev_fig = Figure(facecolor=MPL_BG, figsize=(10, 3.5))
            self._rev_canvas = FigureCanvas(self._rev_fig)
            self._rev_canvas.setStyleSheet(f"background:{MPL_BG};border:1px solid {BORDER};border-radius:8px;")
            lay.addWidget(self._rev_canvas)
        else:
            lay.addWidget(_no_mpl_label())

        # Table
        self._rev_tbl = _make_table(["Tháng", "Phải Thu", "Đã Thu", "Còn Nợ", "Tỷ Lệ %"])
        lay.addWidget(self._rev_tbl)
        self.tabs.addTab(w, "💰  Doanh Thu")

    # ══════════════════════════ TAB HIỆU SUẤT PHÒNG ══════════════════════════
    def _build_efficiency_tab(self):
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Cards
        self._eff_cards = QHBoxLayout()
        lay.addLayout(self._eff_cards)

        if HAS_MPL:
            charts_row = QHBoxLayout(); charts_row.setSpacing(12)

            self._eff_fig_bar = Figure(facecolor=MPL_BG, figsize=(7, 3.5))
            self._eff_canvas_bar = FigureCanvas(self._eff_fig_bar)
            self._eff_canvas_bar.setStyleSheet(f"background:{MPL_BG};border:1px solid {BORDER};border-radius:8px;")

            self._eff_fig_pie = Figure(facecolor=MPL_BG, figsize=(3.5, 3.5))
            self._eff_canvas_pie = FigureCanvas(self._eff_fig_pie)
            self._eff_canvas_pie.setStyleSheet(f"background:{MPL_BG};border:1px solid {BORDER};border-radius:8px;")

            charts_row.addWidget(self._eff_canvas_bar, 2)
            charts_row.addWidget(self._eff_canvas_pie, 1)
            lay.addLayout(charts_row)
        else:
            lay.addWidget(_no_mpl_label())

        self._eff_tbl = _make_table(["Phòng", "Khu", "Toà", "Sức Chứa", "Đang Ở", "Trống", "Hiệu Suất %", "Trạng Thái"])
        lay.addWidget(self._eff_tbl, 1)
        self.tabs.addTab(w, "🏠  Hiệu Suất Phòng")

    # ═══════════════════════════════ TAB CÔNG NỢ ════════════════════════════
    def _build_debt_tab(self):
        w = QWidget(); w.setStyleSheet(f"background:{BG};")
        lay = QVBoxLayout(w); lay.setContentsMargins(20, 16, 20, 16); lay.setSpacing(12)

        # Summary banner
        self._debt_banner = QLabel()
        self._debt_banner.setStyleSheet(
            f"background:#2A0A0A;color:{RED};border:1px solid #5A1A1A;"
            "border-radius:8px;padding:10px 16px;font-size:13px;font-weight:600;"
        )
        lay.addWidget(self._debt_banner)

        # Cards
        self._debt_cards = QHBoxLayout()
        lay.addLayout(self._debt_cards)

        # Table công nợ chi tiết
        self._debt_tbl = _make_table([
            "Phòng", "Khu / Toà", "Tháng/Năm", "Tổng Phải Thu",
            "Đã Đóng", "Còn Nợ", "% Nợ", "Trạng Thái"
        ])
        self._debt_tbl.setColumnWidth(7, 120)
        lay.addWidget(self._debt_tbl, 1)
        self.tabs.addTab(w, "🔴  Công Nợ")

    # ══════════════════════════════ REFRESH ══════════════════════════════════
    def refresh(self):
        year  = self.year_cb.currentData()
        month = self.month_cb.currentData()
        self._load_revenue(year)
        self._load_efficiency(year)
        self._load_debt(year, month)

    # ─────────────────────────── Doanh thu ───────────────────────────────────
    def _load_revenue(self, year: int):
        conn = get_connection()
        rows = conn.execute("""
            SELECT month,
                   SUM(total_amount) as due,
                   SUM(paid_amount)  as paid
            FROM fees WHERE year=? GROUP BY month ORDER BY month
        """, (year,)).fetchall()
        conn.close()

        md = {r["month"]: r for r in rows}
        months, dues, paids, rems = [], [], [], []
        total_due = total_paid = 0

        self._rev_tbl.setRowCount(12)
        for m in range(1, 13):
            d   = md.get(m)
            due = (d["due"]  or 0) if d else 0
            paid= (d["paid"] or 0) if d else 0
            rem = due - paid
            pct = f"{(paid/due*100):.1f}%" if due > 0 else "—"
            total_due  += due
            total_paid += paid
            months.append(f"T{m}"); dues.append(due); paids.append(paid); rems.append(rem)

            for c, v in enumerate([f"Tháng {m}", format_currency(due),
                                    format_currency(paid), format_currency(rem), pct]):
                it = QTableWidgetItem(v)
                it.setTextAlignment(Qt.AlignCenter)
                if c == 3 and rem > 0: it.setForeground(QColor(RED))
                elif c == 2 and paid > 0: it.setForeground(QColor(GREEN))
                self._rev_tbl.setItem(m-1, c, it)

        # Cards
        _clear_layout(self._rev_cards)
        for txt, val, color in [
            ("💰 Phải Thu", total_due,  BLUE),
            ("✅ Đã Thu",   total_paid, GREEN),
            ("🔴 Còn Nợ",  total_due - total_paid, RED),
            ("📊 Tỷ Lệ",   f"{(total_paid/total_due*100):.1f}%" if total_due>0 else "—", ORANGE),
        ]:
            self._rev_cards.addWidget(_stat_card(txt, val if isinstance(val, str) else format_currency(val), color))
        self._rev_cards.addStretch()

        # Chart
        if HAS_MPL:
            self._rev_fig.clear()
            ax = self._rev_fig.add_subplot(111, facecolor=MPL_BG)
            x = range(12)
            w = 0.35
            bars1 = ax.bar([i-w/2 for i in x], dues,  width=w, label="Phải Thu", color="#4A9EFF", alpha=0.85)
            bars2 = ax.bar([i+w/2 for i in x], paids, width=w, label="Đã Thu",   color="#51CF66", alpha=0.85)
            ax.set_xticks(list(x)); ax.set_xticklabels(months, color="#8899B4", fontsize=8)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"{v/1e6:.1f}M" if v>=1e6 else f"{v/1e3:.0f}K"))
            ax.tick_params(axis="y", colors="#8899B4", labelsize=8)
            ax.set_facecolor(MPL_BG); ax.grid(axis="y", color=MPL_GRID, linestyle="--", alpha=0.5)
            for sp in ax.spines.values(): sp.set_color(BORDER)
            ax.legend(facecolor=CARD_BG, edgecolor=BORDER, labelcolor="#C8D8E8", fontsize=9)
            ax.set_title(f"Doanh Thu Theo Tháng — Năm {year}", color="#C8D8E8", fontsize=11, pad=8)
            self._rev_fig.tight_layout()
            self._rev_canvas.draw()

    # ─────────────────────────── Hiệu suất phòng ─────────────────────────────
    def _load_efficiency(self, year: int):
        conn = get_connection()
        rooms = conn.execute("""
            SELECT r.id, r.room_number, r.building, r.capacity, r.status,
                   z.name AS zone_name,
                   COALESCE(cnt.c, 0) as occupied
            FROM rooms r
            LEFT JOIN zones z ON r.zone_id = z.id
            LEFT JOIN (
                SELECT room_id, COUNT(*) as c FROM students
                WHERE residency_status='active' GROUP BY room_id
            ) cnt ON r.id = cnt.room_id
            ORDER BY z.name, r.building, r.room_number
        """).fetchall()
        conn.close()

        total = len(rooms)
        avail = sum(1 for r in rooms if r["status"] == "available")
        full  = sum(1 for r in rooms if r["status"] == "full")
        maint = sum(1 for r in rooms if r["status"] == "maintenance")
        total_cap = sum(r["capacity"] for r in rooms)
        total_occ = sum(r["occupied"] for r in rooms)
        occ_rate  = total_occ / total_cap * 100 if total_cap else 0

        _clear_layout(self._eff_cards)
        for txt, val, color in [
            ("🏠 Tổng Phòng", str(total), BLUE),
            ("✅ Trống", str(avail), GREEN),
            ("🔴 Đầy",   str(full),  RED),
            ("🔧 Bảo Trì", str(maint), ORANGE),
            ("📊 Hiệu Suất", f"{occ_rate:.1f}%", YELLOW),
        ]:
            self._eff_cards.addWidget(_stat_card(txt, val, color))
        self._eff_cards.addStretch()

        # Table
        self._eff_tbl.setRowCount(len(rooms))
        STATUS_VI = {"available": "Còn Trống", "full": "Đầy", "maintenance": "Bảo Trì"}
        STATUS_C  = {"available": GREEN, "full": RED, "maintenance": ORANGE}
        for i, r in enumerate(rooms):
            avail_b = r["capacity"] - r["occupied"]
            eff = r["occupied"] / r["capacity"] * 100 if r["capacity"] else 0
            vals = [
                r["room_number"], r["zone_name"] or "—", r["building"],
                str(r["capacity"]), str(r["occupied"]), str(avail_b),
                f"{eff:.0f}%", STATUS_VI.get(r["status"], r["status"])
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v); it.setTextAlignment(Qt.AlignCenter)
                if c == 6:
                    it.setForeground(QColor(GREEN if eff >= 80 else ORANGE if eff >= 50 else RED))
                elif c == 7:
                    it.setForeground(QColor(STATUS_C.get(r["status"], "#E8EDF5")))
                self._eff_tbl.setItem(i, c, it)
            self._eff_tbl.setRowHeight(i, 42)

        # Charts
        if HAS_MPL:
            # Bar: occupancy per room
            self._eff_fig_bar.clear()
            ax = self._eff_fig_bar.add_subplot(111, facecolor=MPL_BG)
            labels = [r["room_number"] for r in rooms]
            occs   = [r["occupied"] / r["capacity"] * 100 if r["capacity"] else 0 for r in rooms]
            colors = [("#51CF66" if v >= 80 else "#FFA726" if v >= 50 else "#FF5252") for v in occs]
            ax.bar(labels, occs, color=colors, alpha=0.85)
            ax.axhline(y=occ_rate, color="#4A9EFF", linestyle="--", linewidth=1, label=f"TB: {occ_rate:.1f}%")
            ax.set_ylim(0, 110)
            ax.set_ylabel("Hiệu Suất %", color="#8899B4", fontsize=9)
            ax.tick_params(axis="x", colors="#8899B4", labelsize=7, rotation=45)
            ax.tick_params(axis="y", colors="#8899B4", labelsize=8)
            ax.set_facecolor(MPL_BG); ax.grid(axis="y", color=MPL_GRID, linestyle="--", alpha=0.5)
            for sp in ax.spines.values(): sp.set_color(BORDER)
            ax.legend(facecolor=CARD_BG, edgecolor=BORDER, labelcolor="#C8D8E8", fontsize=9)
            ax.set_title("Hiệu Suất Lấp Đầy Từng Phòng", color="#C8D8E8", fontsize=10, pad=8)
            self._eff_fig_bar.tight_layout()
            self._eff_canvas_bar.draw()

            # Pie: room status
            self._eff_fig_pie.clear()
            ax2 = self._eff_fig_pie.add_subplot(111, facecolor=MPL_BG)
            pie_data   = [avail, full, maint]
            pie_labels = ["Trống", "Đầy", "Bảo Trì"]
            pie_colors = ["#51CF66", "#FF5252", "#FFA726"]
            non_zero   = [(d, l, c) for d, l, c in zip(pie_data, pie_labels, pie_colors) if d > 0]
            if non_zero:
                d_, l_, c_ = zip(*non_zero)
                wedges, texts, autotexts = ax2.pie(
                    d_, labels=l_, colors=c_,
                    autopct="%1.0f%%", startangle=90,
                    textprops={"color": "#C8D8E8", "fontsize": 9},
                    wedgeprops={"linewidth": 0.5, "edgecolor": MPL_BG}
                )
                for at in autotexts: at.set_fontsize(9)
            ax2.set_title("Phân Bổ Trạng Thái", color="#C8D8E8", fontsize=10, pad=8)
            self._eff_fig_pie.tight_layout()
            self._eff_canvas_pie.draw()

    # ─────────────────────────── Công nợ ─────────────────────────────────────
    def _load_debt(self, year: int, month: int):
        conn = get_connection()
        q = """
            SELECT r.room_number, r.building,
                   z.name AS zone_name,
                   f.month, f.year,
                   f.total_amount, f.paid_amount,
                   (f.total_amount - f.paid_amount) AS remaining,
                   f.status
            FROM fees f
            JOIN rooms r ON f.room_id = r.id
            LEFT JOIN zones z ON r.zone_id = z.id
            WHERE f.status != 'paid' AND f.year = ?
        """
        params = [year]
        if month:
            q += " AND f.month = ?"
            params.append(month)
        q += " ORDER BY remaining DESC, r.room_number"
        debts = conn.execute(q, params).fetchall()
        conn.close()

        self._last_debts = [dict(d) for d in debts]
        total_rem  = sum(d["remaining"] for d in debts)
        rooms_debt = len({d["room_number"] for d in debts})
        max_debt   = max((d["remaining"] for d in debts), default=0)

        period = f"Tháng {month}/{year}" if month else f"Năm {year}"
        self._debt_banner.setText(
            f"🔴  {period}  —  {len(debts)} hóa đơn chưa thu  |  "
            f"{rooms_debt} phòng nợ  |  Tổng nợ: {format_currency(total_rem)}"
        )

        _clear_layout(self._debt_cards)
        for txt, val, color in [
            ("📋 HĐ Chưa Thu", str(len(debts)), RED),
            ("🏠 Phòng Nợ",    str(rooms_debt), ORANGE),
            ("💸 Tổng Nợ",     format_currency(total_rem), RED),
            ("⚠️ Cao Nhất",    format_currency(max_debt), YELLOW),
        ]:
            self._debt_cards.addWidget(_stat_card(txt, val, color))
        self._debt_cards.addStretch()

        self._debt_tbl.setRowCount(len(debts))
        for i, d in enumerate(debts):
            pct_debt = (d["remaining"] / d["total_amount"] * 100) if d["total_amount"] else 0
            zone_str = f"{d['zone_name'] or '—'} / {d['building']}"
            vals = [
                d["room_number"], zone_str,
                f"{d['month']}/{d['year']}",
                format_currency(d["total_amount"]),
                format_currency(d["paid_amount"]),
                format_currency(d["remaining"]),
                f"{pct_debt:.0f}%",
                "⚠️ Nợ Một Phần" if d["status"] == "partial" else "❌ Chưa Thanh Toán"
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v); it.setTextAlignment(Qt.AlignCenter)
                if c == 5: it.setForeground(QColor(RED if pct_debt >= 80 else ORANGE))
                elif c == 6: it.setForeground(QColor(RED if pct_debt >= 80 else ORANGE))
                self._debt_tbl.setItem(i, c, it)
            self._debt_tbl.setRowHeight(i, 42)

    # ─────────────────────────── Export CSV ──────────────────────────────────
    def _export_debt_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu CSV Công Nợ", f"cong_no_{self.year_cb.currentData()}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return
        debts = getattr(self, "_last_debts", [])
        headers = ["Phòng", "Khu", "Toà", "Tháng", "Năm",
                   "Phải Thu", "Đã Đóng", "Còn Nợ", "Trạng Thái"]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(headers)
                for d in debts:
                    w.writerow([
                        d["room_number"], d.get("zone_name", ""),
                        d["building"], d["month"], d["year"],
                        d["total_amount"], d["paid_amount"],
                        d["remaining"], d["status"]
                    ])
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Xuất CSV", f"✅ Đã xuất {len(debts)} dòng\n{path}")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Lỗi", str(e))


# ══════════════════════════════ Helpers ═══════════════════════════════════════
def _make_table(headers: list) -> QTableWidget:
    t = QTableWidget()
    t.setColumnCount(len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setFocusPolicy(Qt.NoFocus)
    t.setShowGrid(False)
    t.setStyleSheet(f"""
        QTableWidget{{background:{MPL_BG};border:1px solid {BORDER};border-radius:8px;}}
        QTableWidget::item{{padding:4px 8px;color:#C8D8E8;border:none;}}
        QTableWidget::item:alternate{{background:#0F1A28;}}
        QHeaderView::section{{background:#1A2D4A;color:#8899B4;font-weight:600;
                              border:none;padding:8px;font-size:12px;}}
    """)
    return t


def _stat_card(label: str, value: str, color: str) -> QFrame:
    card = QFrame()
    card.setFixedSize(170, 72)
    card.setStyleSheet(f"""
        QFrame{{background:{CARD_BG};border:1px solid {color}55;border-radius:10px;}}
    """)
    lay = QVBoxLayout(card); lay.setContentsMargins(12, 8, 12, 8); lay.setSpacing(2)
    lbl = QLabel(label); lbl.setFont(QFont("Segoe UI", 10)); lbl.setStyleSheet(f"color:#8899B4;")
    val = QLabel(value); val.setFont(QFont("Segoe UI", 13, QFont.Bold))
    val.setStyleSheet(f"color:{color};"); val.setWordWrap(True)
    lay.addWidget(lbl); lay.addWidget(val)
    return card


def _clear_layout(lay):
    while lay.count():
        item = lay.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def _no_mpl_label() -> QLabel:
    lbl = QLabel("📦  Cài matplotlib để xem biểu đồ:\n  pip install matplotlib")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color:#6A8899;background:{CARD_BG};border:1px solid {BORDER};border-radius:8px;padding:30px;font-size:13px;")
    lbl.setFixedHeight(150)
    return lbl
