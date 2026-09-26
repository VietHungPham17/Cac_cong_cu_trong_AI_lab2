"""
Module kết nối và quản lý cơ sở dữ liệu SQLite.
Tạo bảng, migration, backup, và các hàm tiện ích DB.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from contextlib import contextmanager

from config import DATABASE_PATH, DATABASE_BACKUP_DIR


class DatabaseManager:
    """Quản lý kết nối và thao tác với SQLite database."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self._connection = None

    def get_connection(self):
        """Lấy kết nối database (tạo mới nếu chưa có)."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    def close(self):
        """Đóng kết nối database."""
        if self._connection:
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        """Context manager cho transaction."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, sql, params=None):
        """Thực thi câu lệnh SQL."""
        conn = self.get_connection()
        if params:
            return conn.execute(sql, params)
        return conn.execute(sql)

    def executemany(self, sql, params_list):
        """Thực thi nhiều câu lệnh SQL cùng lúc."""
        conn = self.get_connection()
        return conn.executemany(sql, params_list)

    def fetchone(self, sql, params=None):
        """Lấy một bản ghi."""
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def fetchall(self, sql, params=None):
        """Lấy tất cả bản ghi."""
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def fetchall_as_dict(self, sql, params=None):
        """Lấy tất cả bản ghi dưới dạng list of dict."""
        rows = self.fetchall(sql, params)
        return [dict(row) for row in rows]

    def count(self, table_name, where_clause=None, params=None):
        """Đếm số bản ghi trong bảng."""
        sql = f"SELECT COUNT(*) as cnt FROM {table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        result = self.fetchone(sql, params)
        return result["cnt"] if result else 0

    def table_exists(self, table_name):
        """Kiểm tra bảng có tồn tại không."""
        result = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def get_table_info(self, table_name):
        """Lấy thông tin cấu trúc bảng."""
        return self.fetchall(f"PRAGMA table_info({table_name})")

    def backup(self):
        """Tạo bản sao lưu database."""
        if not os.path.exists(DATABASE_BACKUP_DIR):
            os.makedirs(DATABASE_BACKUP_DIR)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(
            DATABASE_BACKUP_DIR,
            f"sms_backup_{timestamp}.db"
        )
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def initialize_tables(self):
        """Tạo tất cả các bảng cần thiết."""
        with self.transaction() as conn:
            # Bảng Khoa (Faculty)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS faculties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    head_name TEXT,
                    phone TEXT,
                    email TEXT,
                    established_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # Bảng Ngành (Major)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS majors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    faculty_id INTEGER NOT NULL,
                    description TEXT,
                    total_credits INTEGER DEFAULT 0,
                    duration_years INTEGER DEFAULT 4,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (faculty_id) REFERENCES faculties(id)
                        ON DELETE RESTRICT
                )
            """)

            # Bảng Sinh viên (Student)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    date_of_birth TEXT,
                    gender TEXT CHECK(gender IN ('M', 'F', 'O')),
                    address TEXT,
                    major_id INTEGER,
                    enrollment_year INTEGER,
                    current_semester INTEGER DEFAULT 1,
                    gpa REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active'
                        CHECK(status IN ('active', 'inactive', 'graduated',
                                         'suspended', 'expelled')),
                    scholarship_type TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (major_id) REFERENCES majors(id)
                        ON DELETE SET NULL
                )
            """)

            # Bảng Lớp học (Classroom)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS classrooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    room TEXT,
                    building TEXT,
                    capacity INTEGER DEFAULT 30,
                    semester TEXT NOT NULL,
                    academic_year TEXT NOT NULL,
                    lecturer_name TEXT,
                    schedule TEXT,
                    subject_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                        ON DELETE SET NULL
                )
            """)

            # Bảng Môn học (Subject)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    credits INTEGER NOT NULL CHECK(credits > 0),
                    description TEXT,
                    faculty_id INTEGER,
                    prerequisite_id INTEGER,
                    subject_type TEXT DEFAULT 'required'
                        CHECK(subject_type IN ('required', 'elective',
                                                'general', 'thesis')),
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (faculty_id) REFERENCES faculties(id)
                        ON DELETE SET NULL,
                    FOREIGN KEY (prerequisite_id) REFERENCES subjects(id)
                        ON DELETE SET NULL
                )
            """)

            # Bảng Đăng ký lớp (Enrollment)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enrollments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    classroom_id INTEGER NOT NULL,
                    enrolled_at TEXT DEFAULT (datetime('now')),
                    status TEXT DEFAULT 'enrolled'
                        CHECK(status IN ('enrolled', 'dropped', 'completed')),
                    FOREIGN KEY (student_id) REFERENCES students(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (classroom_id) REFERENCES classrooms(id)
                        ON DELETE CASCADE,
                    UNIQUE(student_id, classroom_id)
                )
            """)

            # Bảng Điểm (Grade)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS grades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    classroom_id INTEGER,
                    midterm_score REAL CHECK(midterm_score >= 0 AND midterm_score <= 10),
                    final_score REAL CHECK(final_score >= 0 AND final_score <= 10),
                    assignment_score REAL CHECK(assignment_score >= 0 AND assignment_score <= 10),
                    total_score REAL,
                    letter_grade TEXT,
                    gpa_value REAL,
                    semester TEXT NOT NULL,
                    academic_year TEXT NOT NULL,
                    is_retake INTEGER DEFAULT 0,
                    notes TEXT,
                    graded_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (student_id) REFERENCES students(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (subject_id) REFERENCES subjects(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (classroom_id) REFERENCES classrooms(id)
                        ON DELETE SET NULL,
                    UNIQUE(student_id, subject_id, semester, academic_year)
                )
            """)

            # Bảng Attendance (Điểm danh)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    classroom_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    status TEXT DEFAULT 'present'
                        CHECK(status IN ('present', 'absent', 'late', 'excused')),
                    notes TEXT,
                    recorded_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (student_id) REFERENCES students(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (classroom_id) REFERENCES classrooms(id)
                        ON DELETE CASCADE
                )
            """)

            # Bảng Audit Log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER,
                    action TEXT NOT NULL CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
                    old_values TEXT,
                    new_values TEXT,
                    performed_by TEXT,
                    performed_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_students_major ON students(major_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_students_status ON students(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_grades_subject ON grades(subject_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_grades_semester ON grades(semester, academic_year)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_enrollment_student ON enrollments(student_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name)")


# Singleton instance
_db_instance = None


def get_db(db_path=None):
    """Lấy instance database (Singleton pattern)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance


def init_db(db_path=None):
    """Khởi tạo database và tạo bảng."""
    db = get_db(db_path)
    db.initialize_tables()
    return db


def reset_db():
    """Reset singleton instance (dùng cho testing)."""
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None
