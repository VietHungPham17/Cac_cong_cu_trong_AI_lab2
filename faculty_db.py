"""
Module faculty_db - CRUD operations cho Khoa.
"""

import json
from typing import Optional, List, Dict, Any

from database import get_db
from models import Faculty, PaginatedResult
from validators import FacultyValidator, Validator, ValidationError
from config import DEFAULT_PAGE_SIZE


class FacultyDB:
    """Quản lý CRUD khoa trong database."""

    def __init__(self, db=None):
        self.db = db or get_db()

    def create(self, data: dict) -> Faculty:
        """Tạo khoa mới."""
        valid, error = FacultyValidator.validate_create(data)
        if not valid:
            raise ValueError(f"Dữ liệu không hợp lệ: {error}")

        Validator.validate_unique(self.db, "faculties", "code", data["code"])

        sql = """
            INSERT INTO faculties
                (code, name, description, head_name, phone, email,
                 established_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["code"],
            data["name"],
            data.get("description"),
            data.get("head_name"),
            data.get("phone"),
            data.get("email"),
            data.get("established_date"),
            data.get("is_active", 1),
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(sql, params)
            faculty_id = cursor.lastrowid
            self._log_action("INSERT", faculty_id, None, data)

        return self.get_by_id(faculty_id)

    def get_by_id(self, id: int) -> Optional[Faculty]:
        """Lấy khoa theo ID."""
        row = self.db.fetchone("SELECT * FROM faculties WHERE id = ?", (id,))
        if row:
            return self._row_to_faculty(row)
        return None

    def get_by_code(self, code: str) -> Optional[Faculty]:
        """Lấy khoa theo mã khoa."""
        row = self.db.fetchone(
            "SELECT * FROM faculties WHERE code = ?",
            (code,)
        )
        if row:
            return self._row_to_faculty(row)
        return None

    def get_all(self, include_inactive=False) -> List[Faculty]:
        """Lấy tất cả khoa."""
        sql = "SELECT * FROM faculties"
        if not include_inactive:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY code"
        rows = self.db.fetchall(sql)
        return [self._row_to_faculty(row) for row in rows]

    def get_paginated(self, page=1, page_size=None,
                      search=None) -> PaginatedResult:
        """Lấy danh sách khoa có phân trang."""
        page_size = page_size or DEFAULT_PAGE_SIZE
        offset = (page - 1) * page_size

        where_clause = ""
        params = []
        if search:
            where_clause = " WHERE code LIKE ? OR name LIKE ?"
            search_term = f"%{search}%"
            params = [search_term, search_term]

        total = self.db.fetchone(
            f"SELECT COUNT(*) as cnt FROM faculties{where_clause}",
            params or None
        )["cnt"]

        data_sql = (f"SELECT * FROM faculties{where_clause} "
                    f"ORDER BY code LIMIT ? OFFSET ?")
        rows = self.db.fetchall(data_sql, params + [page_size, offset])

        faculties = [self._row_to_faculty(row) for row in rows]
        return PaginatedResult(
            items=faculties,
            total=total,
            page=page,
            page_size=page_size
        )

    def update(self, id: int, data: dict) -> Optional[Faculty]:
        """Cập nhật thông tin khoa."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy khoa với ID: {id}")

        update_fields = []
        params = []
        allowed_fields = [
            "name", "description", "head_name", "phone", "email",
            "established_date", "is_active"
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
            return existing

        update_fields.append("updated_at = datetime('now')")
        params.append(id)

        sql = f"UPDATE faculties SET {', '.join(update_fields)} WHERE id = ?"

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute(sql, params)
            self._log_action("UPDATE", id, old_data, data)

        return self.get_by_id(id)

    def delete(self, id: int) -> bool:
        """Xóa khoa (soft delete)."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy khoa với ID: {id}")

        # Kiểm tra có ngành liên kết không
        major_count = self.db.count("majors", "faculty_id = ?", (id,))
        if major_count > 0:
            raise ValueError(
                f"Không thể xóa khoa '{existing.name}' vì còn "
                f"{major_count} ngành liên kết"
            )

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE faculties SET is_active = 0, "
                "updated_at = datetime('now') WHERE id = ?",
                (id,)
            )
            self._log_action("DELETE", id, old_data, {"is_active": 0})
        return True

    def get_student_count(self, faculty_id: int) -> int:
        """Đếm số sinh viên trong khoa."""
        result = self.db.fetchone(
            """
            SELECT COUNT(*) as cnt FROM students s
            JOIN majors m ON s.major_id = m.id
            WHERE m.faculty_id = ? AND s.status = 'active'
            """,
            (faculty_id,)
        )
        return result["cnt"] if result else 0

    def get_statistics(self) -> Dict[str, Any]:
        """Lấy thống kê khoa."""
        stats = {}
        stats["total"] = self.db.count("faculties")
        stats["active"] = self.db.count("faculties", "is_active = 1")

        # Thống kê sinh viên theo khoa
        rows = self.db.fetchall("""
            SELECT f.name, COUNT(s.id) as student_count
            FROM faculties f
            LEFT JOIN majors m ON f.id = m.faculty_id
            LEFT JOIN students s ON m.id = s.major_id AND s.status = 'active'
            WHERE f.is_active = 1
            GROUP BY f.id, f.name
            ORDER BY student_count DESC
        """)
        stats["by_faculty"] = {
            row["name"]: row["student_count"] for row in rows
        }

        return stats

    def _row_to_faculty(self, row) -> Faculty:
        """Chuyển row thành Faculty object."""
        return Faculty(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            description=row["description"],
            head_name=row["head_name"],
            phone=row["phone"],
            email=row["email"],
            established_date=row["established_date"],
            is_active=bool(row["is_active"]),
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
                ("faculties", record_id, action,
                 json.dumps(old_values, default=str) if old_values else None,
                 json.dumps(new_values, default=str) if new_values else None,
                 "system")
            )
        except Exception:
            pass
