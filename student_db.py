"""
Module student_db - CRUD operations cho Sinh viên.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from database import get_db
from models import Student, PaginatedResult
from validators import StudentValidator, Validator, ValidationError
from config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class StudentDB:
    """Quản lý CRUD sinh viên trong database."""

    def __init__(self, db=None):
        self.db = db or get_db()

    def create(self, data: dict) -> Student:
        """Tạo sinh viên mới."""
        # Validate
        valid, error = StudentValidator.validate_create(data)
        if not valid:
            raise ValueError(f"Dữ liệu không hợp lệ: {error}")

        # Kiểm tra trùng mã sinh viên
        Validator.validate_unique(self.db, "students", "student_id", data["student_id"])

        # Kiểm tra trùng email
        if data.get("email"):
            Validator.validate_unique(self.db, "students", "email", data["email"])

        # Insert
        sql = """
            INSERT INTO students
                (student_id, first_name, last_name, email, phone,
                 date_of_birth, gender, address, major_id, enrollment_year,
                 current_semester, gpa, status, scholarship_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["student_id"],
            data["first_name"],
            data["last_name"],
            data.get("email"),
            data.get("phone"),
            data.get("date_of_birth"),
            data.get("gender"),
            data.get("address"),
            data.get("major_id"),
            data.get("enrollment_year"),
            data.get("current_semester", 1),
            data.get("gpa", 0.0),
            data.get("status", "active"),
            data.get("scholarship_type"),
            data.get("notes"),
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(sql, params)
            student_id = cursor.lastrowid

            # Audit log
            self._log_action("INSERT", student_id, None, data)

        return self.get_by_id(student_id)

    def get_by_id(self, id: int) -> Optional[Student]:
        """Lấy sinh viên theo ID nội bộ."""
        row = self.db.fetchone("SELECT * FROM students WHERE id = ?", (id,))
        if row:
            return self._row_to_student(row)
        return None

    def get_by_student_id(self, student_id: str) -> Optional[Student]:
        """Lấy sinh viên theo mã sinh viên."""
        row = self.db.fetchone(
            "SELECT * FROM students WHERE student_id = ?",
            (student_id,)
        )
        if row:
            return self._row_to_student(row)
        return None

    def get_all(self, include_inactive=False) -> List[Student]:
        """Lấy tất cả sinh viên."""
        sql = "SELECT * FROM students"
        if not include_inactive:
            sql += " WHERE status = 'active'"
        sql += " ORDER BY student_id"
        rows = self.db.fetchall(sql)
        return [self._row_to_student(row) for row in rows]

    def get_paginated(self, page=1, page_size=None, filters=None,
                      sort_by="student_id", sort_order="ASC") -> PaginatedResult:
        """Lấy danh sách sinh viên có phân trang và lọc."""
        page_size = page_size or DEFAULT_PAGE_SIZE
        page_size = min(page_size, MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        where_clauses = []
        params = []

        if filters:
            if filters.get("status"):
                where_clauses.append("status = ?")
                params.append(filters["status"])
            if filters.get("major_id"):
                where_clauses.append("major_id = ?")
                params.append(filters["major_id"])
            if filters.get("enrollment_year"):
                where_clauses.append("enrollment_year = ?")
                params.append(filters["enrollment_year"])
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                where_clauses.append(
                    "(student_id LIKE ? OR first_name LIKE ? "
                    "OR last_name LIKE ? OR email LIKE ?)"
                )
                params.extend([search_term] * 4)
            if filters.get("min_gpa") is not None:
                where_clauses.append("gpa >= ?")
                params.append(filters["min_gpa"])
            if filters.get("max_gpa") is not None:
                where_clauses.append("gpa <= ?")
                params.append(filters["max_gpa"])
            if filters.get("gender"):
                where_clauses.append("gender = ?")
                params.append(filters["gender"])

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Validate sort
        valid_sorts = ["student_id", "first_name", "last_name", "gpa",
                        "enrollment_year", "created_at"]
        if sort_by not in valid_sorts:
            sort_by = "student_id"
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        # Count
        count_sql = f"SELECT COUNT(*) as cnt FROM students{where_sql}"
        total = self.db.fetchone(count_sql, params or None)["cnt"]

        # Fetch
        data_sql = (f"SELECT * FROM students{where_sql} "
                    f"ORDER BY {sort_by} {sort_order} "
                    f"LIMIT ? OFFSET ?")
        data_params = params + [page_size, offset]
        rows = self.db.fetchall(data_sql, data_params)

        students = [self._row_to_student(row) for row in rows]
        return PaginatedResult(
            items=students,
            total=total,
            page=page,
            page_size=page_size
        )

    def update(self, id: int, data: dict) -> Optional[Student]:
        """Cập nhật thông tin sinh viên."""
        # Kiểm tra tồn tại
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy sinh viên với ID: {id}")

        # Validate
        valid, error = StudentValidator.validate_update(data)
        if not valid:
            raise ValueError(f"Dữ liệu không hợp lệ: {error}")

        # Kiểm tra trùng email
        if "email" in data and data["email"] != existing.email:
            Validator.validate_unique(
                self.db, "students", "email", data["email"], exclude_id=id
            )

        # Build UPDATE query
        update_fields = []
        params = []
        allowed_fields = [
            "first_name", "last_name", "email", "phone", "date_of_birth",
            "gender", "address", "major_id", "enrollment_year",
            "current_semester", "gpa", "status", "scholarship_type", "notes"
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
            return existing

        update_fields.append("updated_at = datetime('now')")
        params.append(id)

        sql = f"UPDATE students SET {', '.join(update_fields)} WHERE id = ?"

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute(sql, params)
            self._log_action("UPDATE", id, old_data, data)

        return self.get_by_id(id)

    def delete(self, id: int) -> bool:
        """Xóa sinh viên (soft delete - chuyển trạng thái)."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy sinh viên với ID: {id}")

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE students SET status = 'inactive', "
                "updated_at = datetime('now') WHERE id = ?",
                (id,)
            )
            self._log_action("DELETE", id, old_data, {"status": "inactive"})
        return True

    def hard_delete(self, id: int) -> bool:
        """Xóa vĩnh viễn sinh viên."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy sinh viên với ID: {id}")

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM students WHERE id = ?", (id,))
            self._log_action("DELETE", id, old_data, None)
        return True

    def search(self, keyword: str) -> List[Student]:
        """Tìm kiếm sinh viên theo từ khóa."""
        search_term = f"%{keyword}%"
        sql = """
            SELECT * FROM students
            WHERE student_id LIKE ? OR first_name LIKE ?
                OR last_name LIKE ? OR email LIKE ?
            ORDER BY student_id
        """
        rows = self.db.fetchall(sql, (search_term,) * 4)
        return [self._row_to_student(row) for row in rows]

    def get_by_major(self, major_id: int) -> List[Student]:
        """Lấy danh sách sinh viên theo ngành."""
        rows = self.db.fetchall(
            "SELECT * FROM students WHERE major_id = ? AND status = 'active' "
            "ORDER BY student_id",
            (major_id,)
        )
        return [self._row_to_student(row) for row in rows]

    def get_by_enrollment_year(self, year: int) -> List[Student]:
        """Lấy danh sách sinh viên theo năm nhập học."""
        rows = self.db.fetchall(
            "SELECT * FROM students WHERE enrollment_year = ? ORDER BY student_id",
            (year,)
        )
        return [self._row_to_student(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê sinh viên."""
        stats = {}
        stats["total"] = self.db.count("students")
        stats["active"] = self.db.count("students", "status = 'active'")
        stats["inactive"] = self.db.count("students", "status = 'inactive'")
        stats["graduated"] = self.db.count("students", "status = 'graduated'")
        stats["suspended"] = self.db.count("students", "status = 'suspended'")

        avg_row = self.db.fetchone(
            "SELECT AVG(gpa) as avg_gpa, MAX(gpa) as max_gpa, "
            "MIN(gpa) as min_gpa FROM students WHERE status = 'active'"
        )
        if avg_row:
            stats["avg_gpa"] = round(avg_row["avg_gpa"] or 0, 2)
            stats["max_gpa"] = avg_row["max_gpa"] or 0
            stats["min_gpa"] = avg_row["min_gpa"] or 0

        # Thống kê theo giới tính
        gender_rows = self.db.fetchall(
            "SELECT gender, COUNT(*) as cnt FROM students "
            "WHERE status = 'active' GROUP BY gender"
        )
        stats["by_gender"] = {row["gender"]: row["cnt"] for row in gender_rows}

        # Thống kê theo năm nhập học
        year_rows = self.db.fetchall(
            "SELECT enrollment_year, COUNT(*) as cnt FROM students "
            "WHERE status = 'active' AND enrollment_year IS NOT NULL "
            "GROUP BY enrollment_year ORDER BY enrollment_year DESC"
        )
        stats["by_year"] = {
            row["enrollment_year"]: row["cnt"] for row in year_rows
        }

        return stats

    def update_gpa(self, student_id: int) -> float:
        """Tính toán lại GPA cho sinh viên dựa trên bảng điểm."""
        gpa_row = self.db.fetchone(
            """
            SELECT AVG(g.gpa_value) as avg_gpa
            FROM grades g
            WHERE g.student_id = ? AND g.gpa_value IS NOT NULL
            """,
            (student_id,)
        )
        new_gpa = round(gpa_row["avg_gpa"] or 0, 2) if gpa_row else 0.0

        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE students SET gpa = ?, updated_at = datetime('now') WHERE id = ?",
                (new_gpa, student_id)
            )
        return new_gpa

    def bulk_import(self, students_data: List[dict]) -> dict:
        """Import hàng loạt sinh viên."""
        results = {"success": 0, "failed": 0, "errors": []}

        for i, data in enumerate(students_data):
            try:
                self.create(data)
                results["success"] += 1
            except (ValueError, ValidationError) as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": i + 1,
                    "data": data.get("student_id", "N/A"),
                    "error": str(e)
                })

        return results

    def _row_to_student(self, row) -> Student:
        """Chuyển sqlite3.Row thành Student object."""
        return Student(
            id=row["id"],
            student_id=row["student_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            date_of_birth=row["date_of_birth"],
            gender=row["gender"],
            address=row["address"],
            major_id=row["major_id"],
            enrollment_year=row["enrollment_year"],
            current_semester=row["current_semester"],
            gpa=row["gpa"] or 0.0,
            status=row["status"],
            scholarship_type=row["scholarship_type"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _log_action(self, action, record_id, old_values, new_values):
        """Ghi audit log."""
        try:
            self.db.execute(
                """INSERT INTO audit_log
                   (table_name, record_id, action, old_values, new_values, performed_by)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    "students",
                    record_id,
                    action,
                    json.dumps(old_values, default=str) if old_values else None,
                    json.dumps(new_values, default=str) if new_values else None,
                    "system"
                )
            )
        except Exception:
            pass  # Không để log lỗi ảnh hưởng business logic
