"""
utils/helpers.py — Các hàm tiện ích
"""
from datetime import datetime


def format_currency(amount: float | int) -> str:
    """Định dạng tiền tệ VNĐ."""
    if amount is None:
        return "0₫"
    return f"{int(amount):,}₫".replace(",", ".")


def format_date(date_str: str) -> str:
    """Chuyển YYYY-MM-DD → DD/MM/YYYY."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return str(date_str)


def today_str() -> str:
    """Ngày hôm nay dạng YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def current_month() -> int:
    return datetime.now().month


def current_year() -> int:
    return datetime.now().year


def status_room_vi(status: str) -> str:
    """Chuyển status phòng sang tiếng Việt."""
    mapping = {"available": "Trống", "full": "Đầy", "maintenance": "Bảo trì"}
    return mapping.get(status, status)


