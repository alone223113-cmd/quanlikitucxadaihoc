"""
ui/users.py — Trang quản lý người dùng (Admin only)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QAbstractItemView,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from models.user import get_all_users, add_user, update_user, toggle_user_active, delete_user


ROLE_STYLE = {
    "admin": ("#FFB300", "#3A2A00"),
    "staff": ("#4A9EFF", "#0A1E38"),
}
ROLE_LABEL = {"admin": "👑 Admin", "staff": "👔 Nhân Viên"}


class UsersPage(QWidget):
    def __init__(self, current_user: dict):
        super().__init__()
        self.current_user = current_user
        self._setup_ui()
        self.refresh()

    # ------------------------------------------------------------------ UI --
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("👥  Quản Lý Người Dùng")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #E8EDF5;")

        self.add_btn = QPushButton("➕  Thêm Tài Khoản")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setMinimumWidth(180)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4A9EFF,stop:1 #007ACC);
                color:white; border-radius:8px; font-size:13px; font-weight:600; padding:0 16px;
            }
            QPushButton:hover { background: #5AB0FF; }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        # Info banner
        info = QLabel(
            "ℹ️  Trang này chỉ dành cho Admin. Mỗi hệ thống phải có ít nhất 1 Admin hoạt động."
        )
        info.setStyleSheet(
            "background:#1A2D0A; color:#8BC34A; border:1px solid #2A4A14; border-radius:6px; padding:8px 14px; font-size:12px;"
        )
        layout.addWidget(info)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Họ & Tên", "Tên Đăng Nhập", "Role", "Trạng Thái", "Ngày Tạo", "Thao Tác"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 290)
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
        users = get_all_users()
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.table.setRowHeight(row, 50)
            is_self = u["id"] == self.current_user.get("id")

            # Họ tên
            name_item = QTableWidgetItem(f"  {u['full_name'] or '(Chưa đặt tên)'}")
            name_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            name_item.setData(Qt.UserRole, u["id"])
            if is_self:
                name_item.setForeground(QColor("#4A9EFF"))
                name_item.setText(f"  {u['full_name']} (bạn)")
            self.table.setItem(row, 0, name_item)

            # Username
            uname_item = QTableWidgetItem(f"  {u['username']}")
            uname_item.setForeground(QColor("#8899B4"))
            self.table.setItem(row, 1, uname_item)

            # Role badge
            fg, bg = ROLE_STYLE.get(u["role"], ("#4A9EFF", "#0A1E38"))
            role_item = QTableWidgetItem(f"  {ROLE_LABEL.get(u['role'], u['role'])}  ")
            role_item.setForeground(QColor(fg))
            role_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, role_item)

            # Trạng thái
            active = u["is_active"] == 1
            status_item = QTableWidgetItem("  ✅ Hoạt động  " if active else "  🔒 Đã khoá  ")
            status_item.setForeground(QColor("#4CAF50") if active else QColor("#FF5252"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, status_item)

            # Ngày tạo
            created = (u.get("created_at") or "")[:10]
            date_item = QTableWidgetItem(created)
            date_item.setForeground(QColor("#6A8899"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, date_item)

            # Thao tác
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(6)

            edit_btn = QPushButton("✏️  Sửa")
            edit_btn.setToolTip("Sửa thông tin / đổi mật khẩu")
            edit_btn.setFixedSize(80, 32)
            edit_btn.setStyleSheet(
                "QPushButton{background:#1A3A5C;color:#4A9EFF;border:1px solid #2A5080;border-radius:6px;font-size:12px;font-weight:600;}"
                "QPushButton:hover{background:#2A4A6C;}"
            )
            edit_btn.clicked.connect(lambda _, uid=u["id"]: self._on_edit(uid))

            lock_btn = QPushButton("🔓  Khoá" if active else "🔒  Mở Khoá")
            lock_btn.setToolTip("Khoá tài khoản" if active else "Mở khoá tài khoản")
            lock_btn.setFixedSize(100, 32)
            lock_btn.setEnabled(not is_self)
            lock_btn.setStyleSheet(
                "QPushButton{background:#2A1A10;color:#FFA726;border:1px solid #4A3010;border-radius:6px;font-size:12px;font-weight:600;}"
                "QPushButton:hover{background:#3A2A10;}"
                "QPushButton:disabled{color:#3A2A10;border-color:#1A1A1A;}"
            )
            lock_btn.clicked.connect(lambda _, uid=u["id"]: self._on_toggle_lock(uid))

            del_btn = QPushButton("🗑️  Xoá")
            del_btn.setToolTip("Xoá tài khoản")
            del_btn.setFixedSize(80, 32)
            del_btn.setEnabled(not is_self)
            del_btn.setStyleSheet(
                "QPushButton{background:#3A1A1A;color:#FF5252;border:1px solid #5A2020;border-radius:6px;font-size:12px;font-weight:600;}"
                "QPushButton:hover{background:#4A2020;}"
                "QPushButton:disabled{color:#3A2020;border-color:#1A1A1A;}"
            )
            del_btn.clicked.connect(lambda _, uid=u["id"], un=u["username"]: self._on_delete(uid, un))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(lock_btn)
            btn_layout.addWidget(del_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(row, 5, btn_widget)

    # ------------------------------------------------------------- Actions --
    def _on_add(self):
        dlg = UserDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            try:
                add_user(dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã thêm tài khoản mới.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _on_edit(self, user_id: int):
        from models.user import get_user_by_id
        u = get_user_by_id(user_id)
        if not u:
            return
        dlg = UserDialog(parent=self, user=u)
        if dlg.exec() == QDialog.Accepted:
            try:
                update_user(user_id, dlg.get_data())
                self.refresh()
                QMessageBox.information(self, "Thành công", "✅ Đã cập nhật tài khoản.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def _on_toggle_lock(self, user_id: int):
        try:
            new_status = toggle_user_active(user_id, self.current_user["id"])
            status_text = "mở khoá" if new_status == 1 else "khoá"
            self.refresh()
            QMessageBox.information(self, "Thành công", f"✅ Đã {status_text} tài khoản.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def _on_delete(self, user_id: int, username: str):
        reply = QMessageBox.question(
            self, "Xác nhận xoá",
            f"Bạn có chắc muốn xoá tài khoản <b>{username}</b>?<br>"
            "Hành động này không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                delete_user(user_id, self.current_user["id"])
                self.refresh()
                QMessageBox.information(self, "Thành công", f"✅ Đã xoá tài khoản {username}.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))


# ===================================================================== Dialog
class UserDialog(QDialog):
    def __init__(self, parent=None, user: dict = None):
        super().__init__(parent)
        self._user = user
        self._is_edit = user is not None
        self.setWindowTitle("Thêm Tài Khoản" if not user else f"Sửa: {user.get('username')}")
        self.setMinimumWidth(440)
        self._setup_ui()
        if user:
            self._fill(user)

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog { background:#0F1724; }
            QLabel { color:#C8D8E8; font-size:13px; }
            QLineEdit, QComboBox {
                background:#1A2D4A; color:#E8EDF5; border:1px solid #2A4060;
                border-radius:6px; padding:6px 10px; font-size:13px; min-height:36px;
            }
            QLineEdit:focus, QComboBox:focus { border-color:#4A9EFF; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Thêm Tài Khoản Mới" if not self._is_edit else "Sửa Thông Tin")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#4A9EFF;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("Họ và tên đầy đủ...")

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Tên đăng nhập (không dấu)...")
        if self._is_edit:
            self.username_edit.setReadOnly(True)
            self.username_edit.setStyleSheet(
                "background:#0F1A28; color:#6A8899; border:1px solid #1A2A3A; border-radius:6px; padding:6px 10px;"
            )

        pw_hint = "(để trống = giữ mật khẩu cũ)" if self._is_edit else ""
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText(f"Mật khẩu... {pw_hint}")

        self.role_combo = QComboBox()
        self.role_combo.addItems(["staff", "admin"])

        form.addRow("Họ & tên *:", self.fullname_edit)
        form.addRow("Username *:", self.username_edit)
        form.addRow("Mật khẩu:", self.password_edit)
        form.addRow("Role *:", self.role_combo)
        layout.addLayout(form)

        # Note khi edit
        if self._is_edit:
            note = QLabel("💡 Để trống ô mật khẩu nếu không muốn thay đổi.")
            note.setStyleSheet("color:#6A8899; font-size:11px; font-style:italic;")
            layout.addWidget(note)

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

    def _fill(self, u: dict):
        self.fullname_edit.setText(u.get("full_name", ""))
        self.username_edit.setText(u.get("username", ""))
        idx = self.role_combo.findText(u.get("role", "staff"))
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)

    def _on_save(self):
        if not self.fullname_edit.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập họ tên.")
            return
        if not self._is_edit and not self.username_edit.text().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên đăng nhập.")
            return
        if not self._is_edit and not self.password_edit.text():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập mật khẩu.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "username":  self.username_edit.text().strip(),
            "password":  self.password_edit.text(),   # empty = no change on edit
            "full_name": self.fullname_edit.text().strip(),
            "role":      self.role_combo.currentText(),
        }
