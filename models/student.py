"""
models/student.py — CRUD cho bảng students (Đã gộp Hợp đồng, dùng CCCD/CMND)
"""
from database.db import get_connection

def get_all_students(search=None, faculty=None, status=None):
    conn = get_connection()
    try:
        query = """
            SELECT s.*,
                   r.room_number,
                   r.building
            FROM students s
            LEFT JOIN rooms r ON s.room_id = r.id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (s.id_card LIKE ? OR s.full_name LIKE ? OR s.phone LIKE ?)"
            params += [f"%{search}%", f"%{search}%", f"%{search}%"]
        if faculty:
            query += " AND s.faculty = ?"
            params.append(faculty)
        if status:
            query += " AND s.residency_status = ?"
            params.append(status)
        query += " ORDER BY s.full_name"
        return [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()

def get_student_by_id(student_id: int):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT s.*, r.room_number, r.building
            FROM students s
            LEFT JOIN rooms r ON s.room_id = r.id
            WHERE s.id = ?
        """, (student_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_student_by_id_card(id_card: str):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM students WHERE id_card = ?", (id_card,)).fetchone()
    finally:
        conn.close()

def add_student(data: dict) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO students (full_name, id_card, date_of_birth, gender,
               faculty, class_name, phone, email, hometown_address,
               room_id, bed_number, checkin_date, checkout_date, deposit, residency_status)
               VALUES (:full_name, :id_card, :date_of_birth, :gender,
               :faculty, :class_name, :phone, :email, :hometown_address,
               :room_id, :bed_number, :checkin_date, :checkout_date, :deposit, :residency_status)""",
            {
                "full_name": data.get("full_name"),
                "id_card": data.get("id_card"),
                "date_of_birth": data.get("date_of_birth", "2000-01-01"),
                "gender": data.get("gender", "Nam"),
                "faculty": data.get("faculty"),
                "class_name": data.get("class_name"),
                "phone": data.get("phone"),
                "email": data.get("email"),
                "hometown_address": data.get("hometown_address"),
                "room_id": data.get("room_id"),
                "bed_number": data.get("bed_number"),
                "checkin_date": data.get("checkin_date"),
                "checkout_date": data.get("checkout_date"),
                "deposit": data.get("deposit", 0),
                "residency_status": data.get("residency_status", "none"),
            },
        )
        conn.commit()
        # Tự động cập nhật trạng thái phòng
        if data.get("room_id"):
            _update_room_status(conn, data["room_id"])
            conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_student(student_id: int, data: dict):
    conn = get_connection()
    try:
        # Lấy room_id cũ để cập nhật trạng thái phòng
        old = conn.execute("SELECT room_id FROM students WHERE id=?", (student_id,)).fetchone()
        old_room_id = old["room_id"] if old else None

        data["id"] = student_id
        conn.execute(
            """UPDATE students SET
               full_name=:full_name, id_card=:id_card, date_of_birth=:date_of_birth, gender=:gender,
               faculty=:faculty, class_name=:class_name, phone=:phone,
               email=:email, hometown_address=:hometown_address,
               room_id=:room_id, bed_number=:bed_number, checkin_date=:checkin_date,
               checkout_date=:checkout_date, deposit=:deposit, residency_status=:residency_status
               WHERE id=:id""",
            data,
        )
        conn.commit()

        # Cập nhật trạng thái phòng (phòng cũ và mới)
        new_room_id = data.get("room_id")
        if old_room_id:
            _update_room_status(conn, old_room_id)
        if new_room_id and new_room_id != old_room_id:
            _update_room_status(conn, new_room_id)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_student(student_id: int):
    conn = get_connection()
    try:
        student = conn.execute(
            "SELECT residency_status, room_id FROM students WHERE id=?", (student_id,)
        ).fetchone()
        if student and student["residency_status"] == 'active':
            raise ValueError("Không thể xóa người đang lưu trú tại KTX.")

        room_id = student["room_id"] if student else None
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()

        if room_id:
            _update_room_status(conn, room_id)
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def _update_room_status(conn, room_id: int):
    """Tự động cập nhật trạng thái phòng dựa theo số SV active."""
    room = conn.execute("SELECT capacity, status FROM rooms WHERE id=?", (room_id,)).fetchone()
    if not room or room["status"] == "maintenance":
        return
    count = conn.execute(
        "SELECT COUNT(*) as c FROM students WHERE room_id=? AND residency_status='active'",
        (room_id,)
    ).fetchone()["c"]
    new_status = "full" if count >= room["capacity"] else "available"
    conn.execute("UPDATE rooms SET status=? WHERE id=?", (new_status, room_id))

