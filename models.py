"""
Module models - Định nghĩa các dataclass cho hệ thống.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class Faculty:
    """Đại diện cho một Khoa."""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    description: Optional[str] = None
    head_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    established_date: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"[{self.code}] {self.name}"


@dataclass
class Major:
    """Đại diện cho một Ngành học."""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    faculty_id: Optional[int] = None
    description: Optional[str] = None
    total_credits: int = 0
    duration_years: int = 4
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"[{self.code}] {self.name} ({self.total_credits} tín chỉ)"


@dataclass
class Student:
    """Đại diện cho một Sinh viên."""
    id: Optional[int] = None
    student_id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None  # M, F, O
    address: Optional[str] = None
    major_id: Optional[int] = None
    enrollment_year: Optional[int] = None
    current_semester: int = 1
    gpa: float = 0.0
    status: str = "active"
    scholarship_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"[{self.student_id}] {self.full_name} - GPA: {self.gpa:.2f}"


@dataclass
class Subject:
    """Đại diện cho một Môn học."""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    credits: int = 0
    description: Optional[str] = None
    faculty_id: Optional[int] = None
    prerequisite_id: Optional[int] = None
    subject_type: str = "required"
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"[{self.code}] {self.name} ({self.credits} TC)"


@dataclass
class Classroom:
    """Đại diện cho một Lớp học."""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    room: Optional[str] = None
    building: Optional[str] = None
    capacity: int = 30
    semester: str = ""
    academic_year: str = ""
    lecturer_name: Optional[str] = None
    schedule: Optional[str] = None
    subject_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return f"[{self.code}] {self.name} - {self.room}, {self.building}"


@dataclass
class Grade:
    """Đại diện cho Bảng điểm một môn."""
    id: Optional[int] = None
    student_id: int = 0
    subject_id: int = 0
    classroom_id: Optional[int] = None
    midterm_score: Optional[float] = None
    final_score: Optional[float] = None
    assignment_score: Optional[float] = None
    total_score: Optional[float] = None
    letter_grade: Optional[str] = None
    gpa_value: Optional[float] = None
    semester: str = ""
    academic_year: str = ""
    is_retake: bool = False
    notes: Optional[str] = None
    graded_at: Optional[str] = None
    updated_at: Optional[str] = None

    def calculate_total(self, midterm_weight=0.3, final_weight=0.5,
                        assignment_weight=0.2):
        """Tính điểm tổng kết dựa trên trọng số."""
        scores = []
        weights = []
        if self.midterm_score is not None:
            scores.append(self.midterm_score)
            weights.append(midterm_weight)
        if self.final_score is not None:
            scores.append(self.final_score)
            weights.append(final_weight)
        if self.assignment_score is not None:
            scores.append(self.assignment_score)
            weights.append(assignment_weight)

        if not scores:
            return None

        total_weight = sum(weights)
        if total_weight == 0:
            return None

        self.total_score = round(
            sum(s * w for s, w in zip(scores, weights)) / total_weight, 2
        )
        self.letter_grade = self._score_to_letter(self.total_score)
        self.gpa_value = self._letter_to_gpa(self.letter_grade)
        return self.total_score

    @staticmethod
    def _score_to_letter(score):
        """Chuyển điểm số sang điểm chữ."""
        if score >= 9.0:
            return "A+"
        elif score >= 8.5:
            return "A"
        elif score >= 8.0:
            return "B+"
        elif score >= 7.0:
            return "B"
        elif score >= 6.5:
            return "B-"
        elif score >= 6.0:
            return "C+"
        elif score >= 5.5:
            return "C"
        elif score >= 5.0:
            return "C-"
        elif score >= 4.0:
            return "D+"
        elif score >= 3.0:
            return "D"
        else:
            return "F"

    @staticmethod
    def _letter_to_gpa(letter):
        """Chuyển điểm chữ sang GPA 4.0."""
        from config import GRADE_SCALE
        return GRADE_SCALE.get(letter, 0.0)

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return (f"Student {self.student_id} - Subject {self.subject_id}: "
                f"{self.total_score} ({self.letter_grade})")


@dataclass
class Enrollment:
    """Đại diện cho đăng ký lớp học."""
    id: Optional[int] = None
    student_id: int = 0
    classroom_id: int = 0
    enrolled_at: Optional[str] = None
    status: str = "enrolled"

    def to_dict(self):
        return asdict(self)


@dataclass
class Attendance:
    """Đại diện cho điểm danh."""
    id: Optional[int] = None
    student_id: int = 0
    classroom_id: int = 0
    date: str = ""
    status: str = "present"  # present, absent, late, excused
    notes: Optional[str] = None
    recorded_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class AuditLog:
    """Đại diện cho log hệ thống."""
    id: Optional[int] = None
    table_name: str = ""
    record_id: Optional[int] = None
    action: str = ""
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    performed_by: Optional[str] = None
    performed_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class PaginatedResult:
    """Kết quả phân trang."""
    items: List = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0

    def __post_init__(self):
        if self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size

    def has_next(self):
        return self.page < self.total_pages

    def has_prev(self):
        return self.page > 1


@dataclass
class GradeStatistics:
    """Thống kê điểm."""
    subject_name: str = ""
    total_students: int = 0
    avg_score: float = 0.0
    max_score: float = 0.0
    min_score: float = 0.0
    pass_count: int = 0
    fail_count: int = 0
    pass_rate: float = 0.0
    grade_distribution: dict = field(default_factory=dict)

    def calculate_pass_rate(self):
        if self.total_students > 0:
            self.pass_rate = round(
                self.pass_count / self.total_students * 100, 2
            )
        return self.pass_rate
