"""
Module utils - Tiện ích chung.
"""

import os
import re
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def generate_student_id(prefix="SV", year=None):
    """Tạo mã sinh viên tự động."""
    year = year or datetime.now().year
    random_part = "".join(random.choices(string.digits, k=4))
    return f"{prefix}{year}{random_part}"


def generate_random_password(length=12):
    """Tạo mật khẩu ngẫu nhiên."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choices(chars, k=length))


def hash_password(password):
    """Hash mật khẩu (đơn giản, chỉ cho demo)."""
    return hashlib.sha256(password.encode()).hexdigest()


def format_date(date_str, from_fmt="%Y-%m-%d", to_fmt="%d/%m/%Y"):
    """Chuyển đổi định dạng ngày."""
    try:
        date_obj = datetime.strptime(date_str, from_fmt)
        return date_obj.strftime(to_fmt)
    except (ValueError, TypeError):
        return date_str


def format_currency(amount, currency="VND"):
    """Định dạng số tiền."""
    if currency == "VND":
        return f"{amount:,.0f} VNĐ"
    return f"${amount:,.2f}"


def calculate_age(date_of_birth, fmt="%Y-%m-%d"):
    """Tính tuổi."""
    try:
        dob = datetime.strptime(date_of_birth, fmt)
        today = datetime.now()
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        return age
    except (ValueError, TypeError):
        return None


def normalize_name(name):
    """Chuẩn hóa tên (viết hoa chữ cái đầu)."""
    if not name:
        return name
    return " ".join(word.capitalize() for word in name.strip().split())


def slugify(text):
    """Tạo slug từ text (cho URL)."""
    text = text.lower().strip()
    text = re.sub(r"[àáạảãâầấậẩẫăằắặẳẵ]", "a", text)
    text = re.sub(r"[èéẹẻẽêềếệểễ]", "e", text)
    text = re.sub(r"[ìíịỉĩ]", "i", text)
    text = re.sub(r"[òóọỏõôồốộổỗơờớợởỡ]", "o", text)
    text = re.sub(r"[ùúụủũưừứựửữ]", "u", text)
    text = re.sub(r"[ỳýỵỷỹ]", "y", text)
    text = re.sub(r"đ", "d", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def paginate_list(items: list, page: int = 1, page_size: int = 20):
    """Phân trang cho danh sách."""
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


def get_academic_year():
    """Lấy năm học hiện tại."""
    now = datetime.now()
    if now.month >= 9:
        return f"{now.year}-{now.year + 1}"
    return f"{now.year - 1}-{now.year}"


def get_current_semester():
    """Lấy học kỳ hiện tại."""
    month = datetime.now().month
    if 9 <= month <= 12 or month == 1:
        return "1"
    elif 2 <= month <= 6:
        return "2"
    else:
        return "he"  # Học kỳ hè


def format_gpa(gpa, scale=4):
    """Định dạng GPA."""
    if gpa is None:
        return "N/A"
    return f"{gpa:.2f}/{scale}.00"


def gpa_to_classification(gpa):
    """Chuyển GPA thành xếp loại."""
    if gpa >= 3.6:
        return "Xuất sắc"
    elif gpa >= 3.2:
        return "Giỏi"
    elif gpa >= 2.5:
        return "Khá"
    elif gpa >= 2.0:
        return "Trung bình"
    elif gpa >= 1.0:
        return "Yếu"
    else:
        return "Kém"


def truncate_string(text, max_length=50, suffix="..."):
    """Cắt ngắn chuỗi."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_table(headers, rows, col_widths=None):
    """Tạo bảng dạng text."""
    if not col_widths:
        col_widths = []
        for i, h in enumerate(headers):
            max_w = len(str(h))
            for row in rows:
                if i < len(row):
                    max_w = max(max_w, len(str(row[i])))
            col_widths.append(min(max_w + 2, 40))

    # Header
    header_line = "|"
    for i, h in enumerate(headers):
        header_line += f" {str(h):<{col_widths[i]}} |"

    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    lines = [separator, header_line, separator]

    for row in rows:
        line = "|"
        for i in range(len(headers)):
            value = str(row[i]) if i < len(row) else ""
            line += f" {value:<{col_widths[i]}} |"
        lines.append(line)

    lines.append(separator)
    return "\n".join(lines)


def validate_file_path(filepath):
    """Kiểm tra đường dẫn file hợp lệ."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return True


def safe_int(value, default=0):
    """Chuyển sang int an toàn."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Chuyển sang float an toàn."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_date_range(period="week"):
    """Lấy khoảng ngày."""
    today = datetime.now()
    if period == "week":
        start = today - timedelta(days=7)
    elif period == "month":
        start = today - timedelta(days=30)
    elif period == "semester":
        start = today - timedelta(days=120)
    elif period == "year":
        start = today - timedelta(days=365)
    else:
        start = today
    return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def merge_dicts(base: dict, override: dict) -> dict:
    """Merge hai dict, override ghi đè base."""
    result = base.copy()
    result.update(override)
    return result
