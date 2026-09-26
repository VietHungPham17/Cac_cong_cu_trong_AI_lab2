"""
Student Management System - Giao diện dòng lệnh (CLI).
"""

import sys
import os
from datetime import datetime

from database import init_db, get_db, reset_db
from student_db import StudentDB
from faculty_db import FacultyDB
from subject_db import SubjectDB
from grade_db import GradeDB
from classroom_db import ClassroomDB
from report import ReportGenerator
from utils import (
    normalize_name, format_gpa, gpa_to_classification,
    get_academic_year, get_current_semester, safe_int, safe_float,
    format_table
)
from config import APP_NAME, APP_VERSION


class CLI:
    """Giao diện dòng lệnh chính."""

    def __init__(self):
        self.db = init_db()
        self.student_db = StudentDB(self.db)
        self.faculty_db = FacultyDB(self.db)
        self.subject_db = SubjectDB(self.db)
        self.grade_db = GradeDB(self.db)
        self.classroom_db = ClassroomDB(self.db)
        self.report = ReportGenerator(self.db)

    def run(self):
        """Chạy CLI chính."""
        self._print_header()
        self._seed_sample_data()

        while True:
            self._print_main_menu()
            choice = input("\n> Chọn chức năng: ").strip()

            if choice == "1":
                self._student_menu()
            elif choice == "2":
                self._faculty_menu()
            elif choice == "3":
                self._subject_menu()
            elif choice == "4":
                self._grade_menu()
            elif choice == "5":
                self._classroom_menu()
            elif choice == "6":
                self._report_menu()
            elif choice == "7":
                self._statistics()
            elif choice == "0":
                print("\nCảm ơn đã sử dụng! Tạm biệt.")
                self.db.close()
                sys.exit(0)
            else:
                print("❌ Lựa chọn không hợp lệ!")

    def _print_header(self):
        """In header ứng dụng."""
        print("=" * 60)
        print(f"  {APP_NAME} v{APP_VERSION}")
        print(f"  Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("=" * 60)

    def _print_main_menu(self):
        """In menu chính."""
        print("\n" + "─" * 40)
        print("  MENU CHÍNH")
        print("─" * 40)
        print("  1. Quản lý Sinh viên")
        print("  2. Quản lý Khoa")
        print("  3. Quản lý Môn học")
        print("  4. Quản lý Điểm")
        print("  5. Quản lý Lớp học")
        print("  6. Xuất báo cáo")
        print("  7. Thống kê")
        print("  0. Thoát")

    # ─── Student Menu ──────────────────────────

    def _student_menu(self):
        """Menu quản lý sinh viên."""
        while True:
            print("\n  QUẢN LÝ SINH VIÊN")
            print("  1. Danh sách SV")
            print("  2. Thêm SV")
            print("  3. Tìm SV")
            print("  4. Cập nhật SV")
            print("  5. Xóa SV")
            print("  0. Quay lại")

            choice = input("> ").strip()

            if choice == "1":
                self._list_students()
            elif choice == "2":
                self._add_student()
            elif choice == "3":
                self._search_student()
            elif choice == "4":
                self._update_student()
            elif choice == "5":
                self._delete_student()
            elif choice == "0":
                break

    def _list_students(self):
        """Liệt kê sinh viên."""
        page = 1
        while True:
            result = self.student_db.get_paginated(page=page, page_size=10)
            if not result.items:
                print("  (Không có sinh viên)")
                break

            headers = ["#", "Mã SV", "Họ tên", "Email", "GPA", "Trạng thái"]
            rows = []
            for i, s in enumerate(result.items, (page - 1) * 10 + 1):
                rows.append([
                    i, s.student_id, s.full_name,
                    s.email or "N/A", f"{s.gpa:.2f}", s.status
                ])

            print(format_table(headers, rows))
            print(f"  Trang {result.page}/{result.total_pages} "
                  f"(Tổng: {result.total})")

            if result.total_pages <= 1:
                break

            nav = input("  [n]ext / [p]rev / [q]uit: ").strip().lower()
            if nav == "n" and result.has_next():
                page += 1
            elif nav == "p" and result.has_prev():
                page -= 1
            else:
                break

    def _add_student(self):
        """Thêm sinh viên mới."""
        print("\n  THÊM SINH VIÊN MỚI")
        data = {}
        data["student_id"] = input("  Mã SV (VD: SV202301): ").strip()
        data["last_name"] = normalize_name(input("  Họ: ").strip())
        data["first_name"] = normalize_name(input("  Tên: ").strip())
        data["email"] = input("  Email: ").strip() or None
        data["phone"] = input("  SĐT: ").strip() or None
        data["gender"] = input("  Giới tính (M/F/O): ").strip().upper() or None
        data["date_of_birth"] = input("  Ngày sinh (YYYY-MM-DD): ").strip() or None
        data["enrollment_year"] = safe_int(input("  Năm nhập học: ").strip()) or None

        try:
            student = self.student_db.create(data)
            print(f"\n  ✅ Đã thêm: {student}")
        except (ValueError, Exception) as e:
            print(f"\n  ❌ Lỗi: {e}")

    def _search_student(self):
        """Tìm kiếm sinh viên."""
        keyword = input("  Từ khóa: ").strip()
        results = self.student_db.search(keyword)
        if not results:
            print("  Không tìm thấy.")
        else:
            for s in results:
                print(f"  {s}")

    def _update_student(self):
        """Cập nhật sinh viên."""
        sid = input("  Mã SV cần cập nhật: ").strip()
        student = self.student_db.get_by_student_id(sid)
        if not student:
            print("  ❌ Không tìm thấy.")
            return

        print(f"  Đang sửa: {student}")
        data = {}
        val = input(f"  Họ mới [{student.last_name}]: ").strip()
        if val:
            data["last_name"] = normalize_name(val)
        val = input(f"  Tên mới [{student.first_name}]: ").strip()
        if val:
            data["first_name"] = normalize_name(val)
        val = input(f"  Email mới [{student.email}]: ").strip()
        if val:
            data["email"] = val

        if data:
            try:
                updated = self.student_db.update(student.id, data)
                print(f"  ✅ Đã cập nhật: {updated}")
            except (ValueError, Exception) as e:
                print(f"  ❌ Lỗi: {e}")

    def _delete_student(self):
        """Xóa sinh viên."""
        sid = input("  Mã SV cần xóa: ").strip()
        student = self.student_db.get_by_student_id(sid)
        if not student:
            print("  ❌ Không tìm thấy.")
            return

        confirm = input(f"  Xác nhận xóa {student}? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                self.student_db.delete(student.id)
                print("  ✅ Đã xóa (soft delete).")
            except (ValueError, Exception) as e:
                print(f"  ❌ Lỗi: {e}")

    # ─── Faculty Menu ──────────────────────────

    def _faculty_menu(self):
        """Menu quản lý khoa."""
        while True:
            print("\n  QUẢN LÝ KHOA")
            print("  1. Danh sách khoa")
            print("  2. Thêm khoa")
            print("  3. Cập nhật khoa")
            print("  4. Xóa khoa")
            print("  0. Quay lại")

            choice = input("> ").strip()

            if choice == "1":
                faculties = self.faculty_db.get_all()
                for f in faculties:
                    count = self.faculty_db.get_student_count(f.id)
                    print(f"  {f} ({count} SV)")
            elif choice == "2":
                self._add_faculty()
            elif choice == "3":
                self._update_faculty()
            elif choice == "4":
                self._delete_faculty()
            elif choice == "0":
                break

    def _add_faculty(self):
        """Thêm khoa mới."""
        data = {
            "code": input("  Mã khoa: ").strip().upper(),
            "name": input("  Tên khoa: ").strip(),
            "head_name": input("  Trưởng khoa: ").strip() or None,
            "email": input("  Email: ").strip() or None,
        }
        try:
            faculty = self.faculty_db.create(data)
            print(f"  ✅ Đã thêm: {faculty}")
        except (ValueError, Exception) as e:
            print(f"  ❌ Lỗi: {e}")

    def _update_faculty(self):
        """Cập nhật khoa."""
        code = input("  Mã khoa: ").strip().upper()
        faculty = self.faculty_db.get_by_code(code)
        if not faculty:
            print("  ❌ Không tìm thấy.")
            return

        data = {}
        val = input(f"  Tên mới [{faculty.name}]: ").strip()
        if val:
            data["name"] = val
        val = input(f"  Trưởng khoa [{faculty.head_name}]: ").strip()
        if val:
            data["head_name"] = val

        if data:
            try:
                updated = self.faculty_db.update(faculty.id, data)
                print(f"  ✅ Đã cập nhật: {updated}")
            except (ValueError, Exception) as e:
                print(f"  ❌ Lỗi: {e}")

    def _delete_faculty(self):
        """Xóa khoa."""
        code = input("  Mã khoa cần xóa: ").strip().upper()
        faculty = self.faculty_db.get_by_code(code)
        if not faculty:
            print("  ❌ Không tìm thấy.")
            return

        confirm = input(f"  Xác nhận xóa {faculty}? (y/n): ").lower()
        if confirm == "y":
            try:
                self.faculty_db.delete(faculty.id)
                print("  ✅ Đã xóa.")
            except (ValueError, Exception) as e:
                print(f"  ❌ Lỗi: {e}")

    # ─── Subject Menu ──────────────────────────

    def _subject_menu(self):
        """Menu quản lý môn học."""
        while True:
            print("\n  QUẢN LÝ MÔN HỌC")
            print("  1. Danh sách môn")
            print("  2. Thêm môn")
            print("  3. Xóa môn")
            print("  0. Quay lại")

            choice = input("> ").strip()

            if choice == "1":
                subjects = self.subject_db.get_all()
                for s in subjects:
                    print(f"  {s}")
            elif choice == "2":
                self._add_subject()
            elif choice == "3":
                code = input("  Mã môn: ").strip()
                subj = self.subject_db.get_by_code(code)
                if subj:
                    try:
                        self.subject_db.delete(subj.id)
                        print("  ✅ Đã xóa.")
                    except ValueError as e:
                        print(f"  ❌ {e}")
            elif choice == "0":
                break

    def _add_subject(self):
        """Thêm môn học."""
        data = {
            "code": input("  Mã môn: ").strip().upper(),
            "name": input("  Tên môn: ").strip(),
            "credits": safe_int(input("  Số tín chỉ: ").strip(), 0),
            "subject_type": input("  Loại (required/elective): ").strip() or "required",
        }
        try:
            subject = self.subject_db.create(data)
            print(f"  ✅ Đã thêm: {subject}")
        except (ValueError, Exception) as e:
            print(f"  ❌ Lỗi: {e}")

    # ─── Grade Menu ────────────────────────────

    def _grade_menu(self):
        """Menu quản lý điểm."""
        while True:
            print("\n  QUẢN LÝ ĐIỂM")
            print("  1. Nhập điểm")
            print("  2. Xem bảng điểm SV")
            print("  3. Thống kê điểm môn")
            print("  4. Tính GPA")
            print("  0. Quay lại")

            choice = input("> ").strip()

            if choice == "1":
                self._input_grade()
            elif choice == "2":
                self._view_transcript()
            elif choice == "3":
                self._subject_grade_stats()
            elif choice == "4":
                self._calculate_gpa()
            elif choice == "0":
                break

    def _input_grade(self):
        """Nhập điểm."""
        sid = input("  Mã SV: ").strip()
        student = self.student_db.get_by_student_id(sid)
        if not student:
            print("  ❌ Không tìm thấy SV.")
            return

        subject_code = input("  Mã môn: ").strip()
        subject = self.subject_db.get_by_code(subject_code)
        if not subject:
            print("  ❌ Không tìm thấy môn.")
            return

        data = {
            "student_id": student.id,
            "subject_id": subject.id,
            "midterm_score": safe_float(input("  Điểm GK: ").strip()),
            "final_score": safe_float(input("  Điểm CK: ").strip()),
            "assignment_score": safe_float(input("  Điểm BT: ").strip()),
            "semester": input("  Học kỳ: ").strip() or get_current_semester(),
            "academic_year": input("  Năm học: ").strip() or get_academic_year(),
        }

        try:
            grade = self.grade_db.create(data)
            print(f"  ✅ Đã nhập: {grade}")
        except (ValueError, Exception) as e:
            print(f"  ❌ Lỗi: {e}")

    def _view_transcript(self):
        """Xem bảng điểm."""
        sid = input("  Mã SV: ").strip()
        student = self.student_db.get_by_student_id(sid)
        if not student:
            print("  ❌ Không tìm thấy.")
            return

        transcript = self.grade_db.get_transcript(student.id)
        if not transcript:
            print("  (Chưa có điểm)")
            return

        print(f"\n  BẢNG ĐIỂM - {student.full_name} ({student.student_id})")
        headers = ["Mã MH", "Tên MH", "TC", "GK", "CK", "BT", "TK", "Chữ"]
        rows = [
            [t["subject_code"], t["subject_name"][:20], t["credits"],
             t["midterm_score"], t["final_score"], t["assignment_score"],
             t["total_score"], t["letter_grade"]]
            for t in transcript
        ]
        print(format_table(headers, rows))

        cum_gpa = self.grade_db.calculate_cumulative_gpa(student.id)
        print(f"  GPA tích lũy: {format_gpa(cum_gpa)} "
              f"- {gpa_to_classification(cum_gpa)}")

    def _subject_grade_stats(self):
        """Thống kê điểm môn học."""
        code = input("  Mã môn: ").strip()
        subject = self.subject_db.get_by_code(code)
        if not subject:
            print("  ❌ Không tìm thấy.")
            return

        stats = self.grade_db.get_subject_statistics(subject.id)
        print(f"\n  THỐNG KÊ - {subject.name}")
        print(f"  Tổng SV: {stats.total_students}")
        print(f"  Điểm TB: {stats.avg_score}")
        print(f"  Cao nhất: {stats.max_score}")
        print(f"  Thấp nhất: {stats.min_score}")
        print(f"  Tỷ lệ đạt: {stats.pass_rate}%")
        if stats.grade_distribution:
            print(f"  Phân bố: {stats.grade_distribution}")

    def _calculate_gpa(self):
        """Tính GPA sinh viên."""
        sid = input("  Mã SV: ").strip()
        student = self.student_db.get_by_student_id(sid)
        if not student:
            print("  ❌ Không tìm thấy.")
            return

        gpa = self.grade_db.calculate_cumulative_gpa(student.id)
        self.student_db.update(student.id, {"gpa": gpa})
        print(f"  GPA: {format_gpa(gpa)} - {gpa_to_classification(gpa)}")

    # ─── Classroom Menu ────────────────────────

    def _classroom_menu(self):
        """Menu quản lý lớp."""
        while True:
            print("\n  QUẢN LÝ LỚP HỌC")
            print("  1. Danh sách lớp")
            print("  2. Thêm lớp")
            print("  3. Đăng ký SV vào lớp")
            print("  4. Điểm danh")
            print("  0. Quay lại")

            choice = input("> ").strip()

            if choice == "1":
                classrooms = self.classroom_db.get_all()
                for c in classrooms:
                    count = self.classroom_db.get_enrollment_count(c.id)
                    print(f"  {c} ({count}/{c.capacity} SV)")
            elif choice == "2":
                self._add_classroom()
            elif choice == "3":
                self._enroll_student()
            elif choice == "4":
                self._take_attendance()
            elif choice == "0":
                break

    def _add_classroom(self):
        """Thêm lớp học."""
        data = {
            "code": input("  Mã lớp: ").strip(),
            "name": input("  Tên lớp: ").strip(),
            "room": input("  Phòng: ").strip() or None,
            "building": input("  Tòa nhà: ").strip() or None,
            "capacity": safe_int(input("  Sĩ số tối đa: ").strip(), 30),
            "semester": input("  Học kỳ: ").strip() or get_current_semester(),
            "academic_year": input("  Năm học: ").strip() or get_academic_year(),
            "lecturer_name": input("  Giảng viên: ").strip() or None,
        }
        try:
            classroom = self.classroom_db.create(data)
            print(f"  ✅ Đã thêm: {classroom}")
        except (ValueError, Exception) as e:
            print(f"  ❌ Lỗi: {e}")

    def _enroll_student(self):
        """Đăng ký SV vào lớp."""
        sid = input("  Mã SV: ").strip()
        student = self.student_db.get_by_student_id(sid)
        if not student:
            print("  ❌ Không tìm thấy SV.")
            return

        class_code = input("  Mã lớp: ").strip()
        classroom = self.classroom_db.get_by_code(class_code)
        if not classroom:
            print("  ❌ Không tìm thấy lớp.")
            return

        try:
            enrollment = self.classroom_db.enroll_student(
                student.id, classroom.id
            )
            print(f"  ✅ Đã đăng ký {student.full_name} vào lớp {classroom.code}")
        except (ValueError, Exception) as e:
            print(f"  ❌ Lỗi: {e}")

    def _take_attendance(self):
        """Điểm danh."""
        class_code = input("  Mã lớp: ").strip()
        classroom = self.classroom_db.get_by_code(class_code)
        if not classroom:
            print("  ❌ Không tìm thấy lớp.")
            return

        date = input("  Ngày (YYYY-MM-DD): ").strip() or datetime.now().strftime("%Y-%m-%d")
        students_in_class = self.classroom_db.get_students_in_class(classroom.id)

        if not students_in_class:
            print("  (Chưa có SV trong lớp)")
            return

        for s in students_in_class:
            status = input(
                f"  {s['student_id']} - {s['last_name']} {s['first_name']} "
                f"(p/a/l/e): "
            ).strip().lower()

            status_map = {"p": "present", "a": "absent", "l": "late", "e": "excused"}
            att_status = status_map.get(status, "present")

            self.classroom_db.record_attendance(
                s["id"], classroom.id, date, att_status
            )

        print("  ✅ Đã điểm danh xong.")

    # ─── Report Menu ───────────────────────────

    def _report_menu(self):
        """Menu xuất báo cáo."""
        while True:
            print("\n  XUẤT BÁO CÁO")
            print("  1. Danh sách SV (CSV)")
            print("  2. Bảng điểm (CSV)")
            print("  3. Tổng hợp khoa (CSV)")
            print("  4. Thống kê tổng (JSON)")
            print("  0. Quay lại")

            choice = input("> ").strip()

            try:
                if choice == "1":
                    path = self.report.student_list_report("csv")
                    print(f"  ✅ Đã xuất: {path}")
                elif choice == "2":
                    path = self.report.grade_report(format="csv")
                    print(f"  ✅ Đã xuất: {path}")
                elif choice == "3":
                    path = self.report.faculty_summary_report("csv")
                    print(f"  ✅ Đã xuất: {path}")
                elif choice == "4":
                    path = self.report.overall_statistics_report("json")
                    print(f"  ✅ Đã xuất: {path}")
                elif choice == "0":
                    break
            except Exception as e:
                print(f"  ❌ Lỗi: {e}")

    # ─── Statistics ────────────────────────────

    def _statistics(self):
        """Hiển thị thống kê tổng hợp."""
        print("\n  THỐNG KÊ TỔNG HỢP")
        print("─" * 40)

        student_stats = self.student_db.get_statistics()
        print(f"  Tổng SV: {student_stats['total']}")
        print(f"  Đang học: {student_stats['active']}")
        print(f"  Tạm ngừng: {student_stats.get('suspended', 0)}")
        print(f"  Đã tốt nghiệp: {student_stats.get('graduated', 0)}")
        print(f"  GPA trung bình: {student_stats.get('avg_gpa', 'N/A')}")

        faculty_stats = self.faculty_db.get_statistics()
        print(f"\n  Tổng khoa: {faculty_stats['total']}")
        if faculty_stats.get("by_faculty"):
            print("  Theo khoa:")
            for name, count in faculty_stats["by_faculty"].items():
                print(f"    {name}: {count} SV")

    # ─── Seed Data ─────────────────────────────

    def _seed_sample_data(self):
        """Tạo dữ liệu mẫu nếu DB trống."""
        if self.db.count("faculties") > 0:
            return

        print("  📦 Đang tạo dữ liệu mẫu...")

        # Tạo khoa
        faculties = [
            {"code": "CNTT", "name": "Công nghệ Thông tin", "head_name": "PGS. Nguyễn Văn A"},
            {"code": "DTVT", "name": "Điện tử Viễn thông", "head_name": "TS. Trần Thị B"},
            {"code": "QTKD", "name": "Quản trị Kinh doanh", "head_name": "PGS. Lê Văn C"},
            {"code": "KHMT", "name": "Khoa học Máy tính", "head_name": "GS. Phạm Thị D"},
        ]
        created_faculties = []
        for fd in faculties:
            try:
                f = self.faculty_db.create(fd)
                created_faculties.append(f)
            except Exception:
                pass

        # Tạo môn học
        subjects = [
            {"code": "CS101", "name": "Nhập môn Lập trình", "credits": 3, "faculty_id": created_faculties[0].id if created_faculties else None},
            {"code": "CS201", "name": "Cấu trúc Dữ liệu", "credits": 4, "faculty_id": created_faculties[0].id if created_faculties else None},
            {"code": "CS301", "name": "Cơ sở Dữ liệu", "credits": 3, "faculty_id": created_faculties[0].id if created_faculties else None},
            {"code": "CS401", "name": "Mạng Máy tính", "credits": 3, "faculty_id": created_faculties[0].id if created_faculties else None},
            {"code": "MA101", "name": "Giải tích 1", "credits": 4, "subject_type": "general"},
            {"code": "MA201", "name": "Đại số Tuyến tính", "credits": 3, "subject_type": "general"},
            {"code": "PH101", "name": "Vật lý Đại cương", "credits": 3, "subject_type": "general"},
            {"code": "EN101", "name": "Tiếng Anh 1", "credits": 2, "subject_type": "general"},
        ]
        created_subjects = []
        for sd in subjects:
            try:
                s = self.subject_db.create(sd)
                created_subjects.append(s)
            except Exception:
                pass

        # Tạo sinh viên mẫu
        students_data = [
            {"student_id": "SV20230001", "first_name": "Hùng", "last_name": "Phạm Việt", "email": "hung.pv@student.edu.vn", "gender": "M", "enrollment_year": 2023, "major_id": 1},
            {"student_id": "SV20230002", "first_name": "Linh", "last_name": "Nguyễn Thùy", "email": "linh.nt@student.edu.vn", "gender": "F", "enrollment_year": 2023, "major_id": 1},
            {"student_id": "SV20230003", "first_name": "Minh", "last_name": "Trần Đức", "email": "minh.td@student.edu.vn", "gender": "M", "enrollment_year": 2023, "major_id": 1},
            {"student_id": "SV20230004", "first_name": "Hoa", "last_name": "Lê Thị", "email": "hoa.lt@student.edu.vn", "gender": "F", "enrollment_year": 2023, "major_id": 2},
            {"student_id": "SV20230005", "first_name": "Tuấn", "last_name": "Vũ Anh", "email": "tuan.va@student.edu.vn", "gender": "M", "enrollment_year": 2023, "major_id": 2},
            {"student_id": "SV20220001", "first_name": "Nam", "last_name": "Đỗ Hoàng", "email": "nam.dh@student.edu.vn", "gender": "M", "enrollment_year": 2022, "major_id": 1},
            {"student_id": "SV20220002", "first_name": "Lan", "last_name": "Bùi Ngọc", "email": "lan.bn@student.edu.vn", "gender": "F", "enrollment_year": 2022, "major_id": 3},
            {"student_id": "SV20220003", "first_name": "Dũng", "last_name": "Hoàng Văn", "email": "dung.hv@student.edu.vn", "gender": "M", "enrollment_year": 2022, "major_id": 3},
        ]
        for sd in students_data:
            try:
                self.student_db.create(sd)
            except Exception:
                pass

        print("  ✅ Dữ liệu mẫu đã được tạo.")


def main():
    """Entry point."""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
