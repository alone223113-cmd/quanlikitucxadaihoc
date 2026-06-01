"""
models/room.py — CRUD cho bảng rooms (Tính toán theo Hợp đồng gộp chung Sinh viên)
"""
from database.db import get_connection

def get_all_rooms(building=None, status=None, search=None, zone_id=None):
    conn = get_connection()
    try:
        query = """
            SELECT r.*,
                   z.name AS zone_name,
                   (r.capacity - COALESCE(cnt.active_count, 0)) AS available_beds,
                   COALESCE(cnt.active_count, 0) AS occupied
            FROM rooms r
            LEFT JOIN zones z ON r.zone_id = z.id
            LEFT JOIN (
                SELECT room_id, COUNT(*) as active_count
                FROM students WHERE residency_status = 'active'
                GROUP BY room_id
            ) cnt ON r.id = cnt.room_id
            WHERE 1=1
        """
        params = []
        if zone_id:
            query += " AND r.zone_id = ?"
            params.append(zone_id)
        if building:
            query += " AND r.building = ?"
            params.append(building)
        if status:
            query += " AND r.status = ?"
            params.append(status)
        if search:
            query += " AND r.room_number LIKE ?"
            params.append(f"%{search}%")
        query += " ORDER BY z.name, r.building, r.floor, r.room_number"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()

def get_room_by_id(room_id: int):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    finally:
        conn.close()

def get_available_rooms(capacity=None, building=None, zone_id=None):
    conn = get_connection()
    try:
        query = """
            SELECT r.*,
                   z.name AS zone_name,
                   (r.capacity - COALESCE(cnt.active_count, 0)) AS available_beds
            FROM rooms r
            LEFT JOIN zones z ON r.zone_id = z.id
            LEFT JOIN (
                SELECT room_id, COUNT(*) as active_count
                FROM students WHERE residency_status = 'active'
                GROUP BY room_id
            ) cnt ON r.id = cnt.room_id
            WHERE r.status = 'available'
              AND (r.capacity - COALESCE(cnt.active_count, 0)) > 0
        """
        params = []
        if capacity:
            query += " AND r.capacity = ?"
            params.append(capacity)
        if building:
            query += " AND r.building = ?"
            params.append(building)
        if zone_id:
            query += " AND r.zone_id = ?"
            params.append(zone_id)
        query += " ORDER BY z.name, r.building, r.room_number"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()

def add_room(data: dict) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO rooms (room_number, building, floor, capacity, room_type, price_per_month, status, zone_id, description)
               VALUES (:room_number, :building, :floor, :capacity, :room_type, :price_per_month, :status, :zone_id, :description)""",
            data,
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_room(room_id: int, data: dict):
    conn = get_connection()
    try:
        data["id"] = room_id
        conn.execute(
            """UPDATE rooms SET room_number=:room_number, building=:building, floor=:floor,
               capacity=:capacity, room_type=:room_type, price_per_month=:price_per_month,
               status=:status, zone_id=:zone_id, description=:description WHERE id=:id""",
            data,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_room(room_id: int):
    conn = get_connection()
    try:
        active = conn.execute(
            "SELECT COUNT(*) as c FROM students WHERE room_id=? AND residency_status='active'", (room_id,)
        ).fetchone()["c"]
        if active > 0:
            raise ValueError("Không thể xóa phòng đang có sinh viên ở.")
        conn.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_buildings() -> list:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT DISTINCT building FROM rooms ORDER BY building").fetchall()
        return [r["building"] for r in rows]
    finally:
        conn.close()

def update_room_status_auto(room_id: int):
    conn = get_connection()
    try:
        room = conn.execute("SELECT capacity, status FROM rooms WHERE id=?", (room_id,)).fetchone()
        if not room or room["status"] == "maintenance":
            return
        count = conn.execute(
            "SELECT COUNT(*) as c FROM students WHERE room_id=? AND residency_status='active'", (room_id,)
        ).fetchone()["c"]
        new_status = "full" if count >= room["capacity"] else "available"
        conn.execute("UPDATE rooms SET status=? WHERE id=?", (new_status, room_id))
        conn.commit()
    finally:
        conn.close()

def get_students_by_room(room_id: int) -> list:
    conn = get_connection()
    try:
        query = """
            SELECT id, id_card, full_name, phone, faculty, bed_number, checkin_date
            FROM students
            WHERE room_id = ? AND residency_status = 'active'
            ORDER BY bed_number
        """
        return [dict(r) for r in conn.execute(query, (room_id,)).fetchall()]
    finally:
        conn.close()
