"""
models/fee.py — CRUD cho bảng fees (Tính theo Phòng)
  - Tiền điện: tính theo chỉ số công tơ (prev/curr kWh × đơn giá)
  - Tiền nước: tính theo m³ chia đầu người
"""
from database.db import get_connection


# ─────────────────────────────── Helpers tính toán ───────────────────────────

def calc_electricity(prev: float, curr: float, unit_price: float) -> float:
    """Tính tiền điện: (curr - prev) × unit_price. Trả 0 nếu thiếu dữ liệu."""
    if prev is None or curr is None or curr < prev:
        return 0.0
    return round((curr - prev) * unit_price, 0)


def calc_water_total(cubic_m: float, unit_price: float) -> float:
    """Tổng tiền nước cả phòng: m³ × đơn giá."""
    if cubic_m is None or cubic_m <= 0:
        return 0.0
    return round(cubic_m * unit_price, 0)


def calc_water_per_person(cubic_m: float, unit_price: float, num_persons: int) -> float:
    """Tiền nước mỗi người: tổng / số người (chỉ để hiển thị)."""
    total = calc_water_total(cubic_m, unit_price)
    if not num_persons or num_persons <= 0:
        return total
    return round(total / num_persons, 0)


# ─────────────────────────────── Queries ─────────────────────────────────────

def get_fees_by_month(month: int, year: int, search=None, status=None):
    conn = get_connection()
    try:
        query = """
            SELECT f.*,
                   r.room_number, r.building,
                   (f.total_amount - f.paid_amount) AS remaining
            FROM fees f
            JOIN rooms r ON f.room_id = r.id
            WHERE f.month = ? AND f.year = ?
        """
        params = [month, year]
        if search:
            query += " AND (r.room_number LIKE ?)"
            params += [f"%{search}%"]
        if status:
            query += " AND f.status = ?"
            params.append(status)
        query += " ORDER BY r.room_number"
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def create_monthly_fees(month: int, year: int) -> int:
    """Tự động tạo phiếu thu cho tất cả phòng đang có sinh viên lưu trú.
    Snapshot water_num_persons = số SV đang ở tại thời điểm tạo.
    """
    conn = get_connection()
    try:
        rooms = conn.execute("""
            SELECT r.id, r.price_per_month, COUNT(s.id) as active_students
            FROM rooms r
            LEFT JOIN students s ON r.id = s.room_id AND s.residency_status = 'active'
            WHERE r.status != 'maintenance'
            GROUP BY r.id
            HAVING active_students > 0
        """).fetchall()

        created = 0
        for r in rooms:
            try:
                room_fee = r["price_per_month"] * r["active_students"]
                conn.execute(
                    """INSERT OR IGNORE INTO fees
                       (room_id, month, year, room_fee, total_amount, status, water_num_persons)
                       VALUES (?, ?, ?, ?, ?, 'unpaid', ?)""",
                    (r["id"], month, year, room_fee, room_fee, r["active_students"]),
                )
                created += 1
            except Exception:
                pass
        conn.commit()
        return created
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_fee(fee_id: int, data: dict):
    """Cập nhật hóa đơn. data phải chứa đầy đủ các trường."""
    conn = get_connection()
    try:
        data["id"] = fee_id
        conn.execute(
            """UPDATE fees SET
               room_fee=:room_fee,
               elec_prev_reading=:elec_prev_reading,
               elec_curr_reading=:elec_curr_reading,
               elec_unit_price=:elec_unit_price,
               electricity_fee=:electricity_fee,
               water_cubic_meters=:water_cubic_meters,
               water_unit_price=:water_unit_price,
               water_num_persons=:water_num_persons,
               water_fee=:water_fee,
               service_fee=:service_fee,
               total_amount=:total_amount,
               paid_amount=:paid_amount,
               paid_date=:paid_date,
               status=:status,
               notes=:notes
               WHERE id=:id""",
            data,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
