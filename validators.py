"""
Module validators - Xác thực dữ liệu đầu vào.
"""

import re
from datetime import datetime
from typing import Optional, Tuple

from config import STUDENT_ID_PATTERN, EMAIL_PATTERN, PHONE_PATTERN


class ValidationError(Exception):
    """Exception cho lỗi xác thực."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class Validator:
    """Lớp xác thực dữ liệu chung."""

    @staticmethod
    def validate_required(value, field_name):
        """Kiểm tra trường bắt buộc."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValidationError(field_name, "Trường này là bắt buộc")
        return True

    @staticmethod
    def validate_string_length(value, field_name, min_len=0, max_len=255):
        """Kiểm tra độ dài chuỗi."""
        if value and (len(value) < min_len or len(value) > max_len):
            raise ValidationError(
                field_name,
                f"Độ dài phải từ {min_len} đến {max_len} ký tự"
            )
        return True

    @staticmethod
    def validate_email(email, field_name="email"):
        """Kiểm tra định dạng email."""
        if email and not re.match(EMAIL_PATTERN, email):
            raise ValidationError(field_name, "Email không hợp lệ")
        return True

    @staticmethod
    def validate_phone(phone, field_name="phone"):
        """Kiểm tra định dạng số điện thoại."""
        if phone and not re.match(PHONE_PATTERN, phone):
            raise ValidationError(field_name, "Số điện thoại không hợp lệ")
        return True

    @staticmethod
    def validate_student_id(student_id, field_name="student_id"):
        """Kiểm tra mã sinh viên (VD: SV202301)."""
        if not re.match(STUDENT_ID_PATTERN, student_id):
            raise ValidationError(
                field_name,
                "Mã sinh viên phải có dạng 2 chữ cái + 6-8 số (VD: SV202301)"
            )
        return True

    @staticmethod
    def validate_date(date_str, field_name="date", fmt="%Y-%m-%d"):
        """Kiểm tra định dạng ngày tháng."""
        if date_str:
            try:
                datetime.strptime(date_str, fmt)
            except ValueError:
                raise ValidationError(
                    field_name,
                    f"Ngày không hợp lệ, định dạng cần: {fmt}"
                )
        return True

    @staticmethod
    def validate_gender(gender, field_name="gender"):
        """Kiểm tra giới tính."""
        valid_values = ["M", "F", "O"]
        if gender and gender not in valid_values:
            raise ValidationError(
                field_name,
                f"Giới tính phải là một trong: {', '.join(valid_values)}"
            )
        return True

    @staticmethod
    def validate_score(score, field_name="score", min_val=0, max_val=10):
        """Kiểm tra điểm số."""
        if score is not None:
            try:
                score = float(score)
            except (ValueError, TypeError):
                raise ValidationError(field_name, "Điểm phải là số")
            if score < min_val or score > max_val:
                raise ValidationError(
                    field_name,
                    f"Điểm phải từ {min_val} đến {max_val}"
                )
        return True

    @staticmethod
    def validate_positive_integer(value, field_name):
        """Kiểm tra số nguyên dương."""
        if value is not None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError(field_name, "Phải là số nguyên")
            if value <= 0:
                raise ValidationError(field_name, "Phải là số dương")
        return True

    @staticmethod
    def validate_year(year, field_name="year"):
        """Kiểm tra năm hợp lệ."""
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                raise ValidationError(field_name, "Năm phải là số nguyên")
            current_year = datetime.now().year
            if year < 1900 or year > current_year + 5:
                raise ValidationError(
                    field_name,
                    f"Năm phải từ 1900 đến {current_year + 5}"
                )
        return True

    @staticmethod
    def validate_status(status, valid_statuses, field_name="status"):
        """Kiểm tra trạng thái."""
        if status and status not in valid_statuses:
            raise ValidationError(
                field_name,
                f"Trạng thái phải là: {', '.join(valid_statuses)}"
            )
        return True

    @staticmethod
    def validate_unique(db, table, field, value, exclude_id=None):
        """Kiểm tra giá trị duy nhất trong bảng."""
        sql = f"SELECT id FROM {table} WHERE {field} = ?"
        params = [value]
        if exclude_id:
            sql += " AND id != ?"
            params.append(exclude_id)
        result = db.fetchone(sql, params)
        if result:
            raise ValidationError(
                field,
                f"Giá trị '{value}' đã tồn tại"
            )
        return True


class StudentValidator:
    """Xác thực dữ liệu sinh viên."""

    @staticmethod
    def validate_create(data: dict) -> Tuple[bool, Optional[str]]:
        """Xác thực dữ liệu tạo sinh viên mới."""
        try:
            v = Validator
            v.validate_required(data.get("student_id"), "student_id")
            v.validate_student_id(data.get("student_id"))
            v.validate_required(data.get("first_name"), "first_name")
            v.validate_string_length(data.get("first_name"), "first_name", 1, 50)
            v.validate_required(data.get("last_name"), "last_name")
            v.validate_string_length(data.get("last_name"), "last_name", 1, 50)
            v.validate_email(data.get("email"))
            v.validate_phone(data.get("phone"))
            v.validate_date(data.get("date_of_birth"), "date_of_birth")
            v.validate_gender(data.get("gender"))
            if data.get("enrollment_year"):
                v.validate_year(data.get("enrollment_year"), "enrollment_year")
            return True, None
        except ValidationError as e:
            return False, str(e)

    @staticmethod
    def validate_update(data: dict) -> Tuple[bool, Optional[str]]:
        """Xác thực dữ liệu cập nhật sinh viên."""
        try:
            v = Validator
            if "first_name" in data:
                v.validate_required(data["first_name"], "first_name")
                v.validate_string_length(data["first_name"], "first_name", 1, 50)
            if "last_name" in data:
                v.validate_required(data["last_name"], "last_name")
                v.validate_string_length(data["last_name"], "last_name", 1, 50)
            if "email" in data:
                v.validate_email(data.get("email"))
            if "phone" in data:
                v.validate_phone(data.get("phone"))
            if "date_of_birth" in data:
                v.validate_date(data["date_of_birth"], "date_of_birth")
            if "gender" in data:
                v.validate_gender(data["gender"])
            if "status" in data:
                v.validate_status(
                    data["status"],
                    ["active", "inactive", "graduated", "suspended", "expelled"]
                )
            return True, None
        except ValidationError as e:
            return False, str(e)


class GradeValidator:
    """Xác thực dữ liệu điểm."""

    @staticmethod
    def validate_grade(data: dict) -> Tuple[bool, Optional[str]]:
        """Xác thực dữ liệu nhập điểm."""
        try:
            v = Validator
            v.validate_required(data.get("student_id"), "student_id")
            v.validate_required(data.get("subject_id"), "subject_id")
            v.validate_required(data.get("semester"), "semester")
            v.validate_required(data.get("academic_year"), "academic_year")
            v.validate_score(data.get("midterm_score"), "midterm_score")
            v.validate_score(data.get("final_score"), "final_score")
            v.validate_score(data.get("assignment_score"), "assignment_score")
            return True, None
        except ValidationError as e:
            return False, str(e)


class FacultyValidator:
    """Xác thực dữ liệu khoa."""

    @staticmethod
    def validate_create(data: dict) -> Tuple[bool, Optional[str]]:
        """Xác thực dữ liệu tạo khoa mới."""
        try:
            v = Validator
            v.validate_required(data.get("code"), "code")
            v.validate_string_length(data.get("code"), "code", 2, 10)
            v.validate_required(data.get("name"), "name")
            v.validate_string_length(data.get("name"), "name", 2, 100)
            v.validate_email(data.get("email"))
            v.validate_phone(data.get("phone"))
            return True, None
        except ValidationError as e:
            return False, str(e)


class SubjectValidator:
    """Xác thực dữ liệu môn học."""

    @staticmethod
    def validate_create(data: dict) -> Tuple[bool, Optional[str]]:
        """Xác thực dữ liệu tạo môn học mới."""
        try:
            v = Validator
            v.validate_required(data.get("code"), "code")
            v.validate_string_length(data.get("code"), "code", 2, 20)
            v.validate_required(data.get("name"), "name")
            v.validate_string_length(data.get("name"), "name", 2, 100)
            v.validate_required(data.get("credits"), "credits")
            v.validate_positive_integer(data.get("credits"), "credits")
            return True, None
        except ValidationError as e:
            return False, str(e)
