"""
models/zone.py — CRUD cho bảng zones (Khu ký túc xá)
"""
from database.db import get_connection


def get_all_zones() -> list:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM zones ORDER BY name"
        ).fetchall()
    finally:
        conn.close()


def get_zone_by_id(zone_id: int):
    conn = get_connection()
    try:
        return conn.execute("SELECT * FROM zones WHERE id = ?", (zone_id,)).fetchone()
    finally:
        conn.close()


def add_zone(data: dict) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO zones (name, description, gender_type) VALUES (:name, :description, :gender_type)",
            data,
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_zone(zone_id: int, data: dict):
    conn = get_connection()
    try:
        data["id"] = zone_id
        conn.execute(
            "UPDATE zones SET name=:name, description=:description, gender_type=:gender_type WHERE id=:id",
            data,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def delete_zone(zone_id: int):
    conn = get_connection()
    try:
        room_count = conn.execute(
            "SELECT COUNT(*) as c FROM rooms WHERE zone_id = ?", (zone_id,)
        ).fetchone()["c"]
        if room_count > 0:
            raise ValueError(f"Không thể xoá khu đang có {room_count} phòng. Hãy chuyển phòng sang khu khác trước.")
        conn.execute("DELETE FROM zones WHERE id = ?", (zone_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_zone_stats() -> list:
    """Trả về thống kê từng khu: tổng phòng, trống, đầy, bảo trì, số SV."""
    conn = get_connection()
    try:
        query = """
            SELECT
                z.id,
                z.name,
                z.gender_type,
                z.description,
                COUNT(r.id)                                          AS total_rooms,
                SUM(CASE WHEN r.status = 'available'    THEN 1 ELSE 0 END) AS available_rooms,
                SUM(CASE WHEN r.status = 'full'         THEN 1 ELSE 0 END) AS full_rooms,
                SUM(CASE WHEN r.status = 'maintenance'  THEN 1 ELSE 0 END) AS maintenance_rooms,
                COALESCE(SUM(sv.sv_count), 0)                        AS total_students
            FROM zones z
            LEFT JOIN rooms r ON z.id = r.zone_id
            LEFT JOIN (
                SELECT room_id, COUNT(*) as sv_count
                FROM students WHERE residency_status = 'active'
                GROUP BY room_id
            ) sv ON r.id = sv.room_id
            GROUP BY z.id
            ORDER BY z.name
        """
        return [dict(r) for r in conn.execute(query).fetchall()]
    finally:
        conn.close()
