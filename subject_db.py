"""
Module subject_db - CRUD operations cho Môn học.
"""

import json
from typing import Optional, List

from database import get_db
from models import Subject, PaginatedResult
from validators import SubjectValidator, Validator, ValidationError
from config import DEFAULT_PAGE_SIZE


class SubjectDB:
    """Quản lý CRUD môn học trong database."""

    def __init__(self, db=None):
        self.db = db or get_db()

    def create(self, data: dict) -> Subject:
        """Tạo môn học mới."""
        valid, error = SubjectValidator.validate_create(data)
        if not valid:
            raise ValueError(f"Dữ liệu không hợp lệ: {error}")

        Validator.validate_unique(self.db, "subjects", "code", data["code"])

        # Kiểm tra prerequisite tồn tại
        if data.get("prerequisite_id"):
            prereq = self.get_by_id(data["prerequisite_id"])
            if not prereq:
                raise ValueError("Môn tiên quyết không tồn tại")

        sql = """
            INSERT INTO subjects
                (code, name, credits, description, faculty_id,
                 prerequisite_id, subject_type, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["code"],
            data["name"],
            data["credits"],
            data.get("description"),
            data.get("faculty_id"),
            data.get("prerequisite_id"),
            data.get("subject_type", "required"),
            data.get("is_active", 1),
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(sql, params)
            subject_id = cursor.lastrowid
            self._log_action("INSERT", subject_id, None, data)

        return self.get_by_id(subject_id)

    def get_by_id(self, id: int) -> Optional[Subject]:
        """Lấy môn học theo ID."""
        row = self.db.fetchone("SELECT * FROM subjects WHERE id = ?", (id,))
        if row:
            return self._row_to_subject(row)
        return None

    def get_by_code(self, code: str) -> Optional[Subject]:
        """Lấy môn học theo mã."""
        row = self.db.fetchone(
            "SELECT * FROM subjects WHERE code = ?", (code,)
        )
        if row:
            return self._row_to_subject(row)
        return None

    def get_all(self, include_inactive=False) -> List[Subject]:
        """Lấy tất cả môn học."""
        sql = "SELECT * FROM subjects"
        if not include_inactive:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY code"
        rows = self.db.fetchall(sql)
        return [self._row_to_subject(row) for row in rows]

    def get_by_faculty(self, faculty_id: int) -> List[Subject]:
        """Lấy môn học theo khoa."""
        rows = self.db.fetchall(
            "SELECT * FROM subjects WHERE faculty_id = ? AND is_active = 1 "
            "ORDER BY code",
            (faculty_id,)
        )
        return [self._row_to_subject(row) for row in rows]

    def get_by_type(self, subject_type: str) -> List[Subject]:
        """Lấy môn học theo loại."""
        rows = self.db.fetchall(
            "SELECT * FROM subjects WHERE subject_type = ? AND is_active = 1 "
            "ORDER BY code",
            (subject_type,)
        )
        return [self._row_to_subject(row) for row in rows]

    def get_prerequisites(self, subject_id: int) -> List[Subject]:
        """Lấy danh sách môn tiên quyết (đệ quy)."""
        prerequisites = []
        current = self.get_by_id(subject_id)

        visited = set()
        while current and current.prerequisite_id:
            if current.prerequisite_id in visited:
                break  # Tránh vòng lặp
            visited.add(current.prerequisite_id)
            prereq = self.get_by_id(current.prerequisite_id)
            if prereq:
                prerequisites.append(prereq)
                current = prereq
            else:
                break

        return prerequisites

    def get_paginated(self, page=1, page_size=None,
                      search=None, faculty_id=None) -> PaginatedResult:
        """Lấy danh sách môn học có phân trang."""
        page_size = page_size or DEFAULT_PAGE_SIZE
        offset = (page - 1) * page_size

        where_parts = ["is_active = 1"]
        params = []

        if search:
            where_parts.append("(code LIKE ? OR name LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if faculty_id:
            where_parts.append("faculty_id = ?")
            params.append(faculty_id)

        where_sql = " WHERE " + " AND ".join(where_parts)

        total = self.db.fetchone(
            f"SELECT COUNT(*) as cnt FROM subjects{where_sql}",
            params or None
        )["cnt"]

        data_sql = (f"SELECT * FROM subjects{where_sql} "
                    f"ORDER BY code LIMIT ? OFFSET ?")
        rows = self.db.fetchall(data_sql, params + [page_size, offset])

        subjects = [self._row_to_subject(row) for row in rows]
        return PaginatedResult(
            items=subjects, total=total,
            page=page, page_size=page_size
        )

    def update(self, id: int, data: dict) -> Optional[Subject]:
        """Cập nhật môn học."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy môn học với ID: {id}")

        update_fields = []
        params = []
        allowed = ["name", "credits", "description", "faculty_id",
                    "prerequisite_id", "subject_type", "is_active"]

        for field in allowed:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
            return existing

        update_fields.append("updated_at = datetime('now')")
        params.append(id)

        sql = f"UPDATE subjects SET {', '.join(update_fields)} WHERE id = ?"

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute(sql, params)
            self._log_action("UPDATE", id, old_data, data)

        return self.get_by_id(id)

    def delete(self, id: int) -> bool:
        """Xóa môn học (soft delete)."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy môn học với ID: {id}")

        # Kiểm tra có điểm liên kết không
        grade_count = self.db.count("grades", "subject_id = ?", (id,))
        if grade_count > 0:
            raise ValueError(
                f"Không thể xóa môn '{existing.name}' vì còn "
                f"{grade_count} bản ghi điểm liên kết"
            )

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE subjects SET is_active = 0, "
                "updated_at = datetime('now') WHERE id = ?",
                (id,)
            )
            self._log_action("DELETE", id, old_data, {"is_active": 0})
        return True

    def get_total_credits(self, subject_ids: List[int]) -> int:
        """Tính tổng số tín chỉ từ danh sách môn."""
        if not subject_ids:
            return 0
        placeholders = ",".join("?" * len(subject_ids))
        result = self.db.fetchone(
            f"SELECT SUM(credits) as total FROM subjects "
            f"WHERE id IN ({placeholders})",
            subject_ids
        )
        return result["total"] or 0

    def _row_to_subject(self, row) -> Subject:
        """Chuyển row thành Subject object."""
        return Subject(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            credits=row["credits"],
            description=row["description"],
            faculty_id=row["faculty_id"],
            prerequisite_id=row["prerequisite_id"],
            subject_type=row["subject_type"],
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
                ("subjects", record_id, action,
                 json.dumps(old_values, default=str) if old_values else None,
                 json.dumps(new_values, default=str) if new_values else None,
                 "system")
            )
        except Exception:
            pass
