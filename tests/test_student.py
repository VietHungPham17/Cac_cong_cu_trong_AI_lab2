"""
Tests cho module student_db.
"""

import pytest
import os
import sys

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, reset_db, get_db
from student_db import StudentDB
from faculty_db import FacultyDB
from validators import ValidationError


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Khởi tạo DB test cho mỗi test case."""
    reset_db()
    db_path = str(tmp_path / "test.db")
    db = init_db(db_path)

    # Tạo dữ liệu khoa mẫu
    faculty_db = FacultyDB(db)
    faculty_db.create({"code": "CNTT", "name": "Công nghệ Thông tin"})

    yield db
    reset_db()


@pytest.fixture
def student_db(setup_db):
    return StudentDB(setup_db)


class TestStudentCreate:
    """Test tạo sinh viên."""

    def test_create_student_success(self, student_db):
        data = {
            "student_id": "SV20230001",
            "first_name": "Hùng",
            "last_name": "Phạm",
            "email": "hung@test.com",
            "gender": "M",
            "enrollment_year": 2023,
        }
        student = student_db.create(data)
        assert student is not None
        assert student.student_id == "SV20230001"
        assert student.first_name == "Hùng"
        assert student.status == "active"

    def test_create_student_missing_required(self, student_db):
        with pytest.raises(ValueError, match="bắt buộc"):
            student_db.create({"first_name": "Test"})

    def test_create_student_invalid_id(self, student_db):
        with pytest.raises(ValueError):
            student_db.create({
                "student_id": "invalid",
                "first_name": "Test",
                "last_name": "User"
            })

    def test_create_student_duplicate_id(self, student_db):
        data = {
            "student_id": "SV20230001",
            "first_name": "Test",
            "last_name": "User"
        }
        student_db.create(data)
        with pytest.raises((ValueError, ValidationError)):
            student_db.create(data)

    def test_create_student_duplicate_email(self, student_db):
        student_db.create({
            "student_id": "SV20230001",
            "first_name": "Test1",
            "last_name": "User1",
            "email": "same@test.com"
        })
        with pytest.raises((ValueError, ValidationError)):
            student_db.create({
                "student_id": "SV20230002",
                "first_name": "Test2",
                "last_name": "User2",
                "email": "same@test.com"
            })


class TestStudentRead:
    """Test đọc sinh viên."""

    def test_get_by_id(self, student_db):
        created = student_db.create({
            "student_id": "SV20230001",
            "first_name": "Hùng",
            "last_name": "Phạm",
        })
        found = student_db.get_by_id(created.id)
        assert found is not None
        assert found.student_id == "SV20230001"

    def test_get_by_student_id(self, student_db):
        student_db.create({
            "student_id": "SV20230001",
            "first_name": "Test",
            "last_name": "User",
        })
        found = student_db.get_by_student_id("SV20230001")
        assert found is not None

    def test_get_nonexistent(self, student_db):
        found = student_db.get_by_id(999)
        assert found is None

    def test_get_all(self, student_db):
        for i in range(3):
            student_db.create({
                "student_id": f"SV2023000{i+1}",
                "first_name": f"Test{i}",
                "last_name": "User",
            })
        students = student_db.get_all()
        assert len(students) == 3

    def test_search(self, student_db):
        student_db.create({
            "student_id": "SV20230001",
            "first_name": "Hùng",
            "last_name": "Phạm",
        })
        results = student_db.search("Hùng")
        assert len(results) >= 1
        assert results[0].first_name == "Hùng"


class TestStudentUpdate:
    """Test cập nhật sinh viên."""

    def test_update_success(self, student_db):
        created = student_db.create({
            "student_id": "SV20230001",
            "first_name": "Hùng",
            "last_name": "Phạm",
        })
        updated = student_db.update(created.id, {"first_name": "Minh"})
        assert updated.first_name == "Minh"

    def test_update_nonexistent(self, student_db):
        with pytest.raises(ValueError):
            student_db.update(999, {"first_name": "Test"})

    def test_update_status(self, student_db):
        created = student_db.create({
            "student_id": "SV20230001",
            "first_name": "Test",
            "last_name": "User",
        })
        updated = student_db.update(created.id, {"status": "graduated"})
        assert updated.status == "graduated"


class TestStudentDelete:
    """Test xóa sinh viên."""

    def test_soft_delete(self, student_db):
        created = student_db.create({
            "student_id": "SV20230001",
            "first_name": "Test",
            "last_name": "User",
        })
        result = student_db.delete(created.id)
        assert result is True

        # Vẫn tìm thấy nhưng status = inactive
        found = student_db.get_by_id(created.id)
        assert found.status == "inactive"

    def test_hard_delete(self, student_db):
        created = student_db.create({
            "student_id": "SV20230001",
            "first_name": "Test",
            "last_name": "User",
        })
        result = student_db.hard_delete(created.id)
        assert result is True

        found = student_db.get_by_id(created.id)
        assert found is None

    def test_delete_nonexistent(self, student_db):
        with pytest.raises(ValueError):
            student_db.delete(999)


class TestStudentPagination:
    """Test phân trang."""

    def test_pagination(self, student_db):
        for i in range(25):
            student_db.create({
                "student_id": f"SV2023{i:04d}",
                "first_name": f"Test{i}",
                "last_name": "User",
            })

        result = student_db.get_paginated(page=1, page_size=10)
        assert len(result.items) == 10
        assert result.total == 25
        assert result.total_pages == 3
        assert result.has_next() is True

    def test_pagination_filter(self, student_db):
        student_db.create({
            "student_id": "SV20230001",
            "first_name": "Active",
            "last_name": "User",
            "status": "active"
        })
        student_db.create({
            "student_id": "SV20230002",
            "first_name": "Grad",
            "last_name": "User",
        })
        student_db.update(2, {"status": "graduated"})

        result = student_db.get_paginated(
            filters={"status": "active"}
        )
        assert result.total >= 1


class TestStudentStatistics:
    """Test thống kê."""

    def test_statistics(self, student_db):
        student_db.create({
            "student_id": "SV20230001",
            "first_name": "Test",
            "last_name": "User",
            "gender": "M",
            "enrollment_year": 2023,
        })
        stats = student_db.get_statistics()
        assert stats["total"] >= 1
        assert stats["active"] >= 1
        assert "by_gender" in stats
