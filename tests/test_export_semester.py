import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, reset_db
from student_db import StudentDB
from subject_db import SubjectDB
from grade_db import GradeDB
from report import ReportGenerator


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    reset_db()
    db_path = str(tmp_path / "test.db")
    db = init_db(db_path)

    student_db = StudentDB(db)
    student_db.create({
        "student_id": "SV20230001",
        "first_name": "Hùng",
        "last_name": "Phạm",
    })

    subject_db = SubjectDB(db)
    subject_db.create({"code": "CS101", "name": "Môn 1", "credits": 3})
    
    grade_db = GradeDB(db)
    grade_db.create({
        "student_id": 1,
        "subject_id": 1,
        "midterm_score": 8.0,
        "final_score": 7.0,
        "assignment_score": 9.0,
        "semester": "1",
        "academic_year": "2023-2024",
    })
    
    yield db
    reset_db()


def test_export_success(setup_db):
    report = ReportGenerator(setup_db)
    path = report.grade_report_by_semester(1, "1", "2023-2024")
    assert path is not None
    assert os.path.exists(path)
    assert path.endswith(".csv")


def test_export_empty(setup_db):
    report = ReportGenerator(setup_db)
    with pytest.raises(ValueError, match="Không có điểm"):
        report.grade_report_by_semester(1, "2", "2023-2024")
