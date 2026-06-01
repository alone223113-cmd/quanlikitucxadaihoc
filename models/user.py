"""
models/user.py — CRUD cho bảng users (Quản lý tài khoản & role)
"""
from database.db import get_connection, hash_password


def get_all_users() -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, full_name, role, is_active, created_at FROM users ORDER BY role DESC, full_name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, username, full_name, role, is_active, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_user(data: dict) -> int:
    """data: {username, password, full_name, role}"""
    conn = get_connection()
    try:
        pw_hash = hash_password(data["password"])
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (data["username"], pw_hash, data.get("full_name", ""), data.get("role", "staff")),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_user(user_id: int, data: dict):
    """data: {full_name, role, password (tuỳ chọn)}"""
    conn = get_connection()
    try:
        if data.get("password"):
            conn.execute(
                "UPDATE users SET full_name=?, role=?, password_hash=? WHERE id=?",
                (data["full_name"], data["role"], hash_password(data["password"]), user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET full_name=?, role=? WHERE id=?",
                (data["full_name"], data["role"], user_id),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def toggle_user_active(user_id: int, current_user_id: int):
    """Khoá/mở khoá user. Không cho khoá chính mình."""
    if user_id == current_user_id:
        raise ValueError("Không thể khoá tài khoản đang đăng nhập.")
    conn = get_connection()
    try:
        user = conn.execute("SELECT is_active, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError("Không tìm thấy người dùng.")
        # Nếu đang khoá admin duy nhất đang active
        if user["role"] == "admin" and user["is_active"] == 1:
            active_admins = conn.execute(
                "SELECT COUNT(*) as c FROM users WHERE role = 'admin' AND is_active = 1"
            ).fetchone()["c"]
            if active_admins <= 1:
                raise ValueError("Không thể khoá admin duy nhất đang hoạt động.")
        new_status = 0 if user["is_active"] == 1 else 1
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
        return new_status
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_user(user_id: int, current_user_id: int):
    """Xoá user. Không cho xoá chính mình hoặc admin cuối."""
    if user_id == current_user_id:
        raise ValueError("Không thể xoá tài khoản đang đăng nhập.")
    conn = get_connection()
    try:
        user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise ValueError("Không tìm thấy người dùng.")
        if user["role"] == "admin":
            admin_count = conn.execute(
                "SELECT COUNT(*) as c FROM users WHERE role = 'admin'"
            ).fetchone()["c"]
            if admin_count <= 1:
                raise ValueError("Không thể xoá admin duy nhất trong hệ thống.")
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
