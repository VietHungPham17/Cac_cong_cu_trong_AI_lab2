"""
Tests cho module faculty_db.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, reset_db
from faculty_db import FacultyDB
from validators import ValidationError


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Khởi tạo DB test."""
    reset_db()
    db_path = str(tmp_path / "test.db")
    db = init_db(db_path)
    yield db
    reset_db()


@pytest.fixture
def faculty_db(setup_db):
    return FacultyDB(setup_db)


class TestFacultyCreate:
    """Test tạo khoa."""

    def test_create_faculty(self, faculty_db):
        faculty = faculty_db.create({
            "code": "CNTT",
            "name": "Công nghệ Thông tin"
        })
        assert faculty is not None
        assert faculty.code == "CNTT"

    def test_create_duplicate_code(self, faculty_db):
        faculty_db.create({"code": "CNTT", "name": "CNTT"})
        with pytest.raises((ValueError, ValidationError)):
            faculty_db.create({"code": "CNTT", "name": "CNTT 2"})

    def test_create_missing_code(self, faculty_db):
        with pytest.raises(ValueError):
            faculty_db.create({"name": "Test"})


class TestFacultyRead:
    """Test đọc khoa."""

    def test_get_by_id(self, faculty_db):
        created = faculty_db.create({
            "code": "CNTT",
            "name": "Công nghệ Thông tin"
        })
        found = faculty_db.get_by_id(created.id)
        assert found is not None
        assert found.code == "CNTT"

    def test_get_by_code(self, faculty_db):
        faculty_db.create({"code": "DTVT", "name": "Điện tử VT"})
        found = faculty_db.get_by_code("DTVT")
        assert found is not None

    def test_get_all(self, faculty_db):
        faculty_db.create({"code": "CNTT", "name": "CNTT"})
        faculty_db.create({"code": "DTVT", "name": "DTVT"})
        all_faculties = faculty_db.get_all()
        assert len(all_faculties) == 2


class TestFacultyUpdate:
    """Test cập nhật khoa."""

    def test_update(self, faculty_db):
        created = faculty_db.create({
            "code": "CNTT",
            "name": "Công nghệ Thông tin"
        })
        updated = faculty_db.update(created.id, {"name": "CNTT Updated"})
        assert updated.name == "CNTT Updated"

    def test_update_nonexistent(self, faculty_db):
        with pytest.raises(ValueError):
            faculty_db.update(999, {"name": "Test"})


class TestFacultyDelete:
    """Test xóa khoa."""

    def test_delete_faculty(self, faculty_db):
        created = faculty_db.create({
            "code": "CNTT",
            "name": "Công nghệ Thông tin"
        })
        result = faculty_db.delete(created.id)
        assert result is True

    def test_delete_nonexistent(self, faculty_db):
        with pytest.raises(ValueError):
            faculty_db.delete(999)


class TestFacultyStatistics:
    """Test thống kê khoa."""

    def test_statistics(self, faculty_db):
        faculty_db.create({"code": "CNTT", "name": "CNTT"})
        stats = faculty_db.get_statistics()
        assert stats["total"] >= 1
