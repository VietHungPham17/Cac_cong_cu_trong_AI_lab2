"""
Module grade_db - CRUD operations cho Điểm số.
"""

import json
from typing import Optional, List, Dict, Any

from database import get_db
from models import Grade, GradeStatistics, PaginatedResult
from validators import GradeValidator, Validator
from config import DEFAULT_PAGE_SIZE


class GradeDB:
    """Quản lý CRUD điểm trong database."""

    def __init__(self, db=None):
        self.db = db or get_db()

    def create(self, data: dict) -> Grade:
        """Tạo bản ghi điểm mới."""
        valid, error = GradeValidator.validate_grade(data)
        if not valid:
            raise ValueError(f"Dữ liệu không hợp lệ: {error}")

        # Kiểm tra sinh viên tồn tại
        student = self.db.fetchone(
            "SELECT id FROM students WHERE id = ?", (data["student_id"],)
        )
        if not student:
            raise ValueError("Sinh viên không tồn tại")

        # Kiểm tra môn học tồn tại
        subject = self.db.fetchone(
            "SELECT id FROM subjects WHERE id = ?", (data["subject_id"],)
        )
        if not subject:
            raise ValueError("Môn học không tồn tại")

        # Tính điểm tổng kết
        grade = Grade(
            student_id=data["student_id"],
            subject_id=data["subject_id"],
            classroom_id=data.get("classroom_id"),
            midterm_score=data.get("midterm_score"),
            final_score=data.get("final_score"),
            assignment_score=data.get("assignment_score"),
            semester=data["semester"],
            academic_year=data["academic_year"],
            is_retake=data.get("is_retake", False),
            notes=data.get("notes"),
        )
        grade.calculate_total()

        sql = """
            INSERT INTO grades
                (student_id, subject_id, classroom_id, midterm_score,
                 final_score, assignment_score, total_score, letter_grade,
                 gpa_value, semester, academic_year, is_retake, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            grade.student_id,
            grade.subject_id,
            grade.classroom_id,
            grade.midterm_score,
            grade.final_score,
            grade.assignment_score,
            grade.total_score,
            grade.letter_grade,
            grade.gpa_value,
            grade.semester,
            grade.academic_year,
            int(grade.is_retake),
            grade.notes,
        )

        with self.db.transaction() as conn:
            cursor = conn.execute(sql, params)
            grade_id = cursor.lastrowid
            self._log_action("INSERT", grade_id, None, data)

        return self.get_by_id(grade_id)

    def get_by_id(self, id: int) -> Optional[Grade]:
        """Lấy bản ghi điểm theo ID."""
        row = self.db.fetchone("SELECT * FROM grades WHERE id = ?", (id,))
        if row:
            return self._row_to_grade(row)
        return None

    def get_by_student(self, student_id: int) -> List[Grade]:
        """Lấy tất cả điểm của một sinh viên."""
        rows = self.db.fetchall(
            "SELECT * FROM grades WHERE student_id = ? ORDER BY academic_year DESC, semester DESC",
            (student_id,)
        )
        return [self._row_to_grade(row) for row in rows]

    def get_by_student_and_semester(self, student_id: int,
                                    semester: str,
                                    academic_year: str) -> List[Grade]:
        """Lấy điểm sinh viên theo học kỳ."""
        rows = self.db.fetchall(
            """SELECT * FROM grades
               WHERE student_id = ? AND semester = ? AND academic_year = ?
               ORDER BY subject_id""",
            (student_id, semester, academic_year)
        )
        return [self._row_to_grade(row) for row in rows]

    def get_by_subject(self, subject_id: int,
                       semester: str = None,
                       academic_year: str = None) -> List[Grade]:
        """Lấy điểm theo môn học."""
        sql = "SELECT * FROM grades WHERE subject_id = ?"
        params = [subject_id]

        if semester:
            sql += " AND semester = ?"
            params.append(semester)
        if academic_year:
            sql += " AND academic_year = ?"
            params.append(academic_year)

        sql += " ORDER BY student_id"
        rows = self.db.fetchall(sql, params)
        return [self._row_to_grade(row) for row in rows]

    def get_paginated(self, page=1, page_size=None,
                      filters=None) -> PaginatedResult:
        """Lấy danh sách điểm có phân trang."""
        page_size = page_size or DEFAULT_PAGE_SIZE
        offset = (page - 1) * page_size

        where_parts = []
        params = []

        if filters:
            if filters.get("student_id"):
                where_parts.append("g.student_id = ?")
                params.append(filters["student_id"])
            if filters.get("subject_id"):
                where_parts.append("g.subject_id = ?")
                params.append(filters["subject_id"])
            if filters.get("semester"):
                where_parts.append("g.semester = ?")
                params.append(filters["semester"])
            if filters.get("academic_year"):
                where_parts.append("g.academic_year = ?")
                params.append(filters["academic_year"])
            if filters.get("min_score") is not None:
                where_parts.append("g.total_score >= ?")
                params.append(filters["min_score"])
            if filters.get("letter_grade"):
                where_parts.append("g.letter_grade = ?")
                params.append(filters["letter_grade"])

        where_sql = " WHERE " + " AND ".join(where_parts) if where_parts else ""

        total = self.db.fetchone(
            f"SELECT COUNT(*) as cnt FROM grades g{where_sql}",
            params or None
        )["cnt"]

        data_sql = (f"SELECT g.* FROM grades g{where_sql} "
                    f"ORDER BY g.academic_year DESC, g.semester DESC "
                    f"LIMIT ? OFFSET ?")
        rows = self.db.fetchall(data_sql, params + [page_size, offset])

        grades = [self._row_to_grade(row) for row in rows]
        return PaginatedResult(
            items=grades, total=total,
            page=page, page_size=page_size
        )

    def update(self, id: int, data: dict) -> Optional[Grade]:
        """Cập nhật điểm."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy bản ghi điểm với ID: {id}")

        # Cập nhật các trường điểm
        if "midterm_score" in data:
            existing.midterm_score = data["midterm_score"]
        if "final_score" in data:
            existing.final_score = data["final_score"]
        if "assignment_score" in data:
            existing.assignment_score = data["assignment_score"]

        # Tính lại điểm tổng
        existing.calculate_total()

        update_fields = [
            "midterm_score = ?", "final_score = ?", "assignment_score = ?",
            "total_score = ?", "letter_grade = ?", "gpa_value = ?",
            "updated_at = datetime('now')"
        ]
        params = [
            existing.midterm_score, existing.final_score,
            existing.assignment_score, existing.total_score,
            existing.letter_grade, existing.gpa_value, id
        ]

        if "notes" in data:
            update_fields.insert(-1, "notes = ?")
            params.insert(-1, data["notes"])

        sql = f"UPDATE grades SET {', '.join(update_fields)} WHERE id = ?"

        old_data = {"midterm_score": existing.midterm_score}
        with self.db.transaction() as conn:
            conn.execute(sql, params)
            self._log_action("UPDATE", id, old_data, data)

        return self.get_by_id(id)

    def delete(self, id: int) -> bool:
        """Xóa bản ghi điểm."""
        existing = self.get_by_id(id)
        if not existing:
            raise ValueError(f"Không tìm thấy bản ghi điểm với ID: {id}")

        old_data = existing.to_dict()
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM grades WHERE id = ?", (id,))
            self._log_action("DELETE", id, old_data, None)
        return True

    def calculate_semester_gpa(self, student_id: int, semester: str,
                                academic_year: str) -> float:
        """Tính GPA theo học kỳ."""
        rows = self.db.fetchall(
            """
            SELECT g.gpa_value, s.credits
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = ? AND g.semester = ?
                AND g.academic_year = ?
                AND g.gpa_value IS NOT NULL
            """,
            (student_id, semester, academic_year)
        )

        if not rows:
            return 0.0

        total_credits = sum(row["credits"] for row in rows)
        if total_credits == 0:
            return 0.0

        weighted_sum = sum(
            row["gpa_value"] * row["credits"] for row in rows
        )
        return round(weighted_sum / total_credits, 2)

    def calculate_cumulative_gpa(self, student_id: int) -> float:
        """Tính GPA tích lũy."""
        rows = self.db.fetchall(
            """
            SELECT g.gpa_value, s.credits
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = ? AND g.gpa_value IS NOT NULL
            """,
            (student_id,)
        )

        if not rows:
            return 0.0

        total_credits = sum(row["credits"] for row in rows)
        if total_credits == 0:
            return 0.0

        weighted_sum = sum(
            row["gpa_value"] * row["credits"] for row in rows
        )
        return round(weighted_sum / total_credits, 2)

    def get_subject_statistics(self, subject_id: int,
                                semester: str = None,
                                academic_year: str = None) -> GradeStatistics:
        """Lấy thống kê điểm theo môn học."""
        subject = self.db.fetchone(
            "SELECT name FROM subjects WHERE id = ?", (subject_id,)
        )

        sql = """
            SELECT
                COUNT(*) as total,
                AVG(total_score) as avg_score,
                MAX(total_score) as max_score,
                MIN(total_score) as min_score,
                SUM(CASE WHEN total_score >= 4.0 THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN total_score < 4.0 THEN 1 ELSE 0 END) as fail_count
            FROM grades
            WHERE subject_id = ? AND total_score IS NOT NULL
        """
        params = [subject_id]

        if semester:
            sql += " AND semester = ?"
            params.append(semester)
        if academic_year:
            sql += " AND academic_year = ?"
            params.append(academic_year)

        row = self.db.fetchone(sql, params)

        stats = GradeStatistics(
            subject_name=subject["name"] if subject else "",
            total_students=row["total"] or 0,
            avg_score=round(row["avg_score"] or 0, 2),
            max_score=row["max_score"] or 0,
            min_score=row["min_score"] or 0,
            pass_count=row["pass_count"] or 0,
            fail_count=row["fail_count"] or 0,
        )
        stats.calculate_pass_rate()

        # Phân bố điểm chữ
        dist_rows = self.db.fetchall(
            """
            SELECT letter_grade, COUNT(*) as cnt
            FROM grades
            WHERE subject_id = ? AND letter_grade IS NOT NULL
            GROUP BY letter_grade
            ORDER BY letter_grade
            """,
            (subject_id,)
        )
        stats.grade_distribution = {
            row["letter_grade"]: row["cnt"] for row in dist_rows
        }

        return stats

    def get_transcript(self, student_id: int) -> List[Dict[str, Any]]:
        """Lấy bảng điểm đầy đủ của sinh viên."""
        rows = self.db.fetchall(
            """
            SELECT g.*, s.code as subject_code, s.name as subject_name,
                   s.credits
            FROM grades g
            JOIN subjects s ON g.subject_id = s.id
            WHERE g.student_id = ?
            ORDER BY g.academic_year, g.semester, s.code
            """,
            (student_id,)
        )
        return [dict(row) for row in rows]

    def bulk_import_grades(self, grades_data: List[dict]) -> dict:
        """Import hàng loạt điểm."""
        results = {"success": 0, "failed": 0, "errors": []}

        for i, data in enumerate(grades_data):
            try:
                self.create(data)
                results["success"] += 1
            except (ValueError, Exception) as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": i + 1,
                    "error": str(e)
                })

        return results

    def _row_to_grade(self, row) -> Grade:
        """Chuyển row thành Grade object."""
        return Grade(
            id=row["id"],
            student_id=row["student_id"],
            subject_id=row["subject_id"],
            classroom_id=row["classroom_id"],
            midterm_score=row["midterm_score"],
            final_score=row["final_score"],
            assignment_score=row["assignment_score"],
            total_score=row["total_score"],
            letter_grade=row["letter_grade"],
            gpa_value=row["gpa_value"],
            semester=row["semester"],
            academic_year=row["academic_year"],
            is_retake=bool(row["is_retake"]),
            notes=row["notes"],
            graded_at=row["graded_at"],
            updated_at=row["updated_at"],
        )

    def _log_action(self, action, record_id, old_values, new_values):
        """Ghi audit log."""
        try:
            self.db.execute(
                """INSERT INTO audit_log
                   (table_name, record_id, action, old_values, new_values, performed_by)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ("grades", record_id, action,
                 json.dumps(old_values, default=str) if old_values else None,
                 json.dumps(new_values, default=str) if new_values else None,
                 "system")
            )
        except Exception:
            pass
