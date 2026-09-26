"""
Module classroom_db - CRUD operations cho Lớp học.
"""

import json
from typing import Optional, List, Dict, Any

from database import get_db
from models import Classroom, Enrollment, Attendance, PaginatedResult
from validators import Validator
from config import DEFAULT_PAGE_SIZE


class ClassroomDB:
    """Quản lý CRUD lớp học trong database."""

    def __init__(self, db=None):
        self.db = db or get_db()

    def create(self, data: dict) -> Classroom:
        """Tạo lớp học mới."""
        Validator.validate_required(data.get("code"), "code")
        Validator.validate_required(data.get("name"), "name")
        Validator.validate_required(data.get("semester"), "semester")
        Validator.validate_required(data.get("academic_year"), "academic_year")

        Validator.validate_unique(self.db, "classrooms", "code", data["code"])

        sql = """
            INSERT INTO classrooms
                (code, name, room, building, capacity, semester,
                 academic_year, lecturer_name, schedule, subject_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data["code"],
            data["name"],
            data.get("room"),
            data.get("building"),
            data.get("capacity", 30),
            data["semester"],
            data["academic_year"],
            data.get("lecturer_name"),
            data.get("schedule"),
            data.get("subject_id"),
            data.get("is_active", 1),
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(sql, params)
            classroom_id = cursor.lastrowid

        return self.get_by_id(classroom_id)

    def get_by_id(self, id: int) -> Optional[Classroom]:
        """Lấy lớp theo ID."""
        row = self.db.fetchone("SELECT * FROM classrooms WHERE id = ?", (id,))
        if row:
            return self._row_to_classroom(row)
        return None

    def get_by_code(self, code: str) -> Optional[Classroom]:
        """Lấy lớp theo mã lớp."""
        row = self.db.fetchone(
            "SELECT * FROM classrooms WHERE code = ?", (code,)
        )
        if row:
            return self._row_to_classroom(row)
        return None

    def get_all(self, include_inactive=False) -> List[Classroom]:
        """Lấy tất cả lớp."""
        sql = "SELECT * FROM classrooms"
        if not include_inactive:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY code"
        rows = self.db.fetchall(sql)
        return [self._row_to_classroom(row) for row in rows]

    def get_by_semester(self, semester: str,
                        academic_year: str) -> List[Classroom]:
        """Lấy danh sách lớp theo học kỳ."""
        rows = self.db.fetchall(
            "SELECT * FROM classrooms WHERE semester = ? AND academic_year = ? "
            "AND is_active = 1 ORDER BY code",
            (semester, academic_year)
        )
        return [self._row_to_classroom(row) for row in rows]

    def get_paginated(self, page=1, page_size=None,
                      filters=None) -> PaginatedResult:
        """Lấy danh sách lớp có phân trang."""
        page_size = page_size or DEFAULT_PAGE_SIZE
        offset = (page - 1) * page_size

        where_parts = ["is_active = 1"]
        params = []

        if filters:
            if filters.get("semester"):
                where_parts.append("semester = ?")
                params.append(filters["semester"])
            if filters.get("academic_year"):
                where_parts.append("academic_year = ?")
                params.append(filters["academic_year"])
            if filters.get("subject_id"):
                where_parts.append("subject_id = ?")
                params.append(filters["subject_id"])
            if filters.get("search"):
                where_parts.append("(code LIKE ? OR name LIKE ?)")
                term = f"%{filters['search']}%"
                params.extend([term, term])

        where_sql = " WHERE " + " AND ".join(where_parts)

        total = self.db.fetchone(
            f"SELECT COUNT(*) as cnt FROM classrooms{where_sql}",
            params or None
        )["cnt"]

        data_sql = (f"SELECT * FROM classrooms{where_sql} "
                    f"ORDER BY code LIMIT ? OFFSET ?")
        rows = self.db.fetchall(data_sql, params + [page_size, offset])

        classrooms = [self._row_to_classroom(row) for row in rows]
        return PaginatedResult(
            items=classrooms, total=total,
            page=page, page_size=page_size
        )

    def update(self, id: int, data: dict) -> Optional[Classroom]:
        """Cập nhật lớp học."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy lớp với ID: {id}")

        update_fields = []
        params = []
        allowed = ["name", "room", "building", "capacity", "lecturer_name",
                    "schedule", "subject_id", "is_active"]

        for field in allowed:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])

        if not update_fields:
            return existing

        update_fields.append("updated_at = datetime('now')")
        params.append(id)

        sql = f"UPDATE classrooms SET {', '.join(update_fields)} WHERE id = ?"

        with self.db.transaction() as conn:
            conn.execute(sql, params)

        return self.get_by_id(id)

    def delete(self, id: int) -> bool:
        """Xóa lớp (soft delete)."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy lớp với ID: {id}")

        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE classrooms SET is_active = 0, "
                "updated_at = datetime('now') WHERE id = ?",
                (id,)
            )
        return True

    # --- Enrollment Management ---

    def enroll_student(self, student_id: int,
                       classroom_id: int) -> Enrollment:
        """Đăng ký sinh viên vào lớp."""
        # Kiểm tra sinh viên
        student = self.db.fetchone(
            "SELECT id FROM students WHERE id = ? AND status = 'active'",
            (student_id,)
        )
        if not student:
            raise ValueError("Sinh viên không tồn tại hoặc không active")

        # Kiểm tra lớp
        classroom = self.get_by_id(classroom_id)
        if not classroom:
            raise ValueError("Lớp học không tồn tại")

        # Kiểm tra sĩ số
        current_count = self.get_enrollment_count(classroom_id)
        if current_count >= classroom.capacity:
            raise ValueError("Lớp đã đầy")

        # Kiểm tra đã đăng ký chưa
        existing = self.db.fetchone(
            "SELECT id FROM enrollments WHERE student_id = ? AND classroom_id = ?",
            (student_id, classroom_id)
        )
        if existing:
            raise ValueError("Sinh viên đã đăng ký lớp này")

        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO enrollments (student_id, classroom_id) VALUES (?, ?)",
                (student_id, classroom_id)
            )
            enrollment_id = cursor.lastrowid

        return Enrollment(
            id=enrollment_id,
            student_id=student_id,
            classroom_id=classroom_id,
            status="enrolled"
        )

    def drop_student(self, student_id: int, classroom_id: int) -> bool:
        """Hủy đăng ký sinh viên khỏi lớp."""
        existing = self.db.fetchone(
            "SELECT id FROM enrollments "
            "WHERE student_id = ? AND classroom_id = ? AND status = 'enrolled'",
            (student_id, classroom_id)
        )
        if not existing:
            raise ValueError("Không tìm thấy đăng ký")

        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE enrollments SET status = 'dropped' "
                "WHERE student_id = ? AND classroom_id = ?",
                (student_id, classroom_id)
            )
        return True

    def get_enrollment_count(self, classroom_id: int) -> int:
        """Đếm số sinh viên đã đăng ký lớp."""
        result = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM enrollments "
            "WHERE classroom_id = ? AND status = 'enrolled'",
            (classroom_id,)
        )
        return result["cnt"] if result else 0

    def get_students_in_class(self, classroom_id: int) -> List[Dict]:
        """Lấy danh sách sinh viên trong lớp."""
        rows = self.db.fetchall(
            """
            SELECT s.*, e.enrolled_at, e.status as enrollment_status
            FROM students s
            JOIN enrollments e ON s.id = e.student_id
            WHERE e.classroom_id = ? AND e.status = 'enrolled'
            ORDER BY s.student_id
            """,
            (classroom_id,)
        )
        return [dict(row) for row in rows]

    def get_student_classes(self, student_id: int) -> List[Dict]:
        """Lấy danh sách lớp của sinh viên."""
        rows = self.db.fetchall(
            """
            SELECT c.*, e.enrolled_at, e.status as enrollment_status
            FROM classrooms c
            JOIN enrollments e ON c.id = e.classroom_id
            WHERE e.student_id = ? AND e.status = 'enrolled'
            ORDER BY c.code
            """,
            (student_id,)
        )
        return [dict(row) for row in rows]

    # --- Attendance Management ---

    def record_attendance(self, student_id: int, classroom_id: int,
                          date: str, status: str = "present",
                          notes: str = None) -> Attendance:
        """Ghi nhận điểm danh."""
        valid_statuses = ["present", "absent", "late", "excused"]
        if status not in valid_statuses:
            raise ValueError(f"Trạng thái phải là: {', '.join(valid_statuses)}")

        with self.db.transaction() as conn:
            cursor = conn.execute(
                """INSERT INTO attendance
                   (student_id, classroom_id, date, status, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, classroom_id, date, status, notes)
            )
            att_id = cursor.lastrowid

        return Attendance(
            id=att_id,
            student_id=student_id,
            classroom_id=classroom_id,
            date=date,
            status=status,
            notes=notes
        )

    def get_attendance_report(self, classroom_id: int,
                               date: str = None) -> List[Dict]:
        """Lấy báo cáo điểm danh."""
        sql = """
            SELECT a.*, s.student_id as sid, s.first_name, s.last_name
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.classroom_id = ?
        """
        params = [classroom_id]
        if date:
            sql += " AND a.date = ?"
            params.append(date)
        sql += " ORDER BY a.date, s.student_id"

        rows = self.db.fetchall(sql, params)
        return [dict(row) for row in rows]

    def get_student_attendance_summary(self, student_id: int,
                                       classroom_id: int) -> Dict[str, int]:
        """Tóm tắt điểm danh của sinh viên trong lớp."""
        rows = self.db.fetchall(
            """
            SELECT status, COUNT(*) as cnt
            FROM attendance
            WHERE student_id = ? AND classroom_id = ?
            GROUP BY status
            """,
            (student_id, classroom_id)
        )
        summary = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        for row in rows:
            summary[row["status"]] = row["cnt"]
        summary["total"] = sum(summary.values())
        if summary["total"] > 0:
            summary["attendance_rate"] = round(
                (summary["present"] + summary["late"]) / summary["total"] * 100,
                2
            )
        else:
            summary["attendance_rate"] = 0.0
        return summary

    def _row_to_classroom(self, row) -> Classroom:
        """Chuyển row thành Classroom object."""
        return Classroom(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            room=row["room"],
            building=row["building"],
            capacity=row["capacity"],
            semester=row["semester"],
            academic_year=row["academic_year"],
            lecturer_name=row["lecturer_name"],
            schedule=row["schedule"],
            subject_id=row["subject_id"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
