"""
models/violation.py — CRUD cho bảng violations
"""
from database.db import get_connection


def get_all_violations(search=None, violation_type=None, from_date=None, to_date=None):
    conn = get_connection()
    try:
        query = """
            SELECT v.*, s.id_card as cccd, s.full_name,
                   u.full_name as recorded_by_name
            FROM violations v
            JOIN students s ON v.student_id = s.id
            LEFT JOIN users u ON v.recorded_by = u.id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (s.id_card LIKE ? OR s.full_name LIKE ?)"
            params += [f"%{search}%", f"%{search}%"]
        if violation_type:
            query += " AND v.violation_type = ?"
            params.append(violation_type)
        if from_date:
            query += " AND v.violation_date >= ?"
            params.append(from_date)
        if to_date:
            query += " AND v.violation_date <= ?"
            params.append(to_date)
        query += " ORDER BY v.violation_date DESC"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def add_violation(data: dict) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO violations (student_id, violation_type, description,
               violation_date, fine_amount, recorded_by)
               VALUES (:student_id, :violation_type, :description,
               :violation_date, :fine_amount, :recorded_by)""",
            data,
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_violation(vio_id: int, data: dict):
    conn = get_connection()
    try:
        data["id"] = vio_id
        conn.execute(
            """UPDATE violations SET violation_type=:violation_type, description=:description,
               violation_date=:violation_date, fine_amount=:fine_amount, is_paid=:is_paid
               WHERE id=:id""",
            data,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def mark_violation_paid(vio_id: int):
    conn = get_connection()
    try:
        conn.execute("UPDATE violations SET is_paid=1 WHERE id=?", (vio_id,))
        conn.commit()
    finally:
        conn.close()


def get_violation_types() -> list:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT violation_type FROM violations ORDER BY violation_type"
        ).fetchall()
        types = [r["violation_type"] for r in rows]
        defaults = ["Về trễ giờ quy định", "Gây ồn ào sau 22h", "Hút thuốc trong phòng",
                    "Mang khách vào phòng trái phép", "Không vệ sinh phòng", "Vi phạm khác"]
        for d in defaults:
            if d not in types:
                types.append(d)
        return sorted(types)
    finally:
        conn.close()


def get_statistics() -> dict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM violations").fetchone()["c"]
        unpaid = conn.execute("SELECT COUNT(*) as c FROM violations WHERE is_paid=0").fetchone()["c"]
        total_fine = conn.execute("SELECT SUM(fine_amount) as s FROM violations").fetchone()["s"] or 0
        return {"total": total, "unpaid": unpaid, "total_fine": total_fine}
    finally:
        conn.close()
