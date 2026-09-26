"""
Tests cho module grade_db.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, reset_db
from student_db import StudentDB
from faculty_db import FacultyDB
from subject_db import SubjectDB
from grade_db import GradeDB


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Khởi tạo DB test."""
    reset_db()
    db_path = str(tmp_path / "test.db")
    db = init_db(db_path)

    # Seed data
    faculty_db = FacultyDB(db)
    faculty_db.create({"code": "CNTT", "name": "Công nghệ Thông tin"})

    subject_db = SubjectDB(db)
    subject_db.create({"code": "CS101", "name": "Nhập môn LP", "credits": 3})
    subject_db.create({"code": "CS201", "name": "CTDL", "credits": 4})

    student_db = StudentDB(db)
    student_db.create({
        "student_id": "SV20230001",
        "first_name": "Hùng",
        "last_name": "Phạm",
    })

    yield db
    reset_db()


@pytest.fixture
def grade_db(setup_db):
    return GradeDB(setup_db)


class TestGradeCreate:
    """Test tạo điểm."""

    def test_create_grade(self, grade_db):
        grade = grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 8.0,
            "final_score": 7.5,
            "assignment_score": 9.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })
        assert grade is not None
        assert grade.total_score is not None
        assert grade.letter_grade is not None

    def test_create_grade_missing_fields(self, grade_db):
        with pytest.raises(ValueError):
            grade_db.create({"student_id": 1})

    def test_create_grade_invalid_student(self, grade_db):
        with pytest.raises(ValueError, match="Sinh viên"):
            grade_db.create({
                "student_id": 999,
                "subject_id": 1,
                "semester": "1",
                "academic_year": "2023-2024",
            })


class TestGradeCalculation:
    """Test tính điểm."""

    def test_calculate_total(self, grade_db):
        grade = grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 8.0,
            "final_score": 7.0,
            "assignment_score": 9.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })
        # 8*0.3 + 7*0.5 + 9*0.2 = 2.4 + 3.5 + 1.8 = 7.7
        assert abs(grade.total_score - 7.7) < 0.1

    def test_letter_grade_A_plus(self, grade_db):
        grade = grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 9.5,
            "final_score": 9.5,
            "assignment_score": 9.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })
        assert grade.letter_grade == "A+"

    def test_semester_gpa(self, grade_db):
        grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 8.0,
            "final_score": 8.0,
            "assignment_score": 8.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })
        grade_db.create({
            "student_id": 1,
            "subject_id": 2,
            "midterm_score": 7.0,
            "final_score": 7.0,
            "assignment_score": 7.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })

        gpa = grade_db.calculate_semester_gpa(1, "1", "2023-2024")
        assert gpa > 0

    def test_cumulative_gpa(self, grade_db):
        grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 8.0,
            "final_score": 8.0,
            "assignment_score": 8.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })

        gpa = grade_db.calculate_cumulative_gpa(1)
        assert gpa > 0


class TestGradeStatistics:
    """Test thống kê điểm."""

    def test_subject_statistics(self, grade_db):
        grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 8.0,
            "final_score": 7.0,
            "assignment_score": 6.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })

        stats = grade_db.get_subject_statistics(1)
        assert stats.total_students == 1
        assert stats.avg_score > 0

    def test_transcript(self, grade_db):
        grade_db.create({
            "student_id": 1,
            "subject_id": 1,
            "midterm_score": 8.0,
            "final_score": 7.0,
            "assignment_score": 9.0,
            "semester": "1",
            "academic_year": "2023-2024",
        })

        transcript = grade_db.get_transcript(1)
        assert len(transcript) >= 1
        assert "subject_code" in transcript[0]
