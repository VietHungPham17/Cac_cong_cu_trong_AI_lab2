"""
Module report - Xuất báo cáo CSV, JSON, TXT.
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from database import get_db
from config import REPORT_OUTPUT_DIR


class ReportGenerator:
    """Tạo và xuất báo cáo."""

    def __init__(self, db=None, output_dir=None):
        self.db = db or get_db()
        self.output_dir = output_dir or REPORT_OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _write_csv(self, filename, headers, rows):
        """Ghi dữ liệu ra file CSV."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return filepath

    def _write_json(self, filename, data):
        """Ghi dữ liệu ra file JSON."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return filepath

    def _write_txt(self, filename, content):
        """Ghi dữ liệu ra file TXT."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def student_list_report(self, format="csv",
                             filters=None) -> str:
        """Xuất báo cáo danh sách sinh viên."""
        sql = """
            SELECT s.student_id, s.first_name, s.last_name,
                   s.email, s.phone, s.gender, s.date_of_birth,
                   s.enrollment_year, s.current_semester, s.gpa,
                   s.status, m.name as major_name, f.name as faculty_name
            FROM students s
            LEFT JOIN majors m ON s.major_id = m.id
            LEFT JOIN faculties f ON m.faculty_id = f.id
        """
        where_parts = []
        params = []

        if filters:
            if filters.get("status"):
                where_parts.append("s.status = ?")
                params.append(filters["status"])
            if filters.get("major_id"):
                where_parts.append("s.major_id = ?")
                params.append(filters["major_id"])
            if filters.get("enrollment_year"):
                where_parts.append("s.enrollment_year = ?")
                params.append(filters["enrollment_year"])

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)
        sql += " ORDER BY s.student_id"

        rows = self.db.fetchall_as_dict(sql, params or None)
        timestamp = self._get_timestamp()

        if format == "csv":
            headers = [
                "Mã SV", "Tên", "Họ", "Email", "SĐT", "Giới tính",
                "Ngày sinh", "Năm nhập học", "HK hiện tại", "GPA",
                "Trạng thái", "Ngành", "Khoa"
            ]
            csv_rows = [
                [r["student_id"], r["first_name"], r["last_name"],
                 r["email"], r["phone"], r["gender"], r["date_of_birth"],
                 r["enrollment_year"], r["current_semester"], r["gpa"],
                 r["status"], r["major_name"], r["faculty_name"]]
                for r in rows
            ]
            return self._write_csv(
                f"student_list_{timestamp}.csv", headers, csv_rows
            )
        elif format == "json":
            return self._write_json(
                f"student_list_{timestamp}.json", rows
            )
        else:
            content = self._format_student_txt(rows)
            return self._write_txt(
                f"student_list_{timestamp}.txt", content
            )

    def grade_report(self, student_id: int = None, subject_id: int = None,
                     semester: str = None, academic_year: str = None,
                     format="csv") -> str:
        """Xuất báo cáo bảng điểm."""
        sql = """
            SELECT s.student_id as sid, s.first_name, s.last_name,
                   sub.code as subject_code, sub.name as subject_name,
                   sub.credits, g.midterm_score, g.final_score,
                   g.assignment_score, g.total_score, g.letter_grade,
                   g.gpa_value, g.semester, g.academic_year
            FROM grades g
            JOIN students s ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
        """
        where_parts = []
        params = []

        if student_id:
            where_parts.append("g.student_id = ?")
            params.append(student_id)
        if subject_id:
            where_parts.append("g.subject_id = ?")
            params.append(subject_id)
        if semester:
            where_parts.append("g.semester = ?")
            params.append(semester)
        if academic_year:
            where_parts.append("g.academic_year = ?")
            params.append(academic_year)

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)
        sql += " ORDER BY g.academic_year, g.semester, s.student_id"

        rows = self.db.fetchall_as_dict(sql, params or None)
        timestamp = self._get_timestamp()

        if format == "csv":
            headers = [
                "Mã SV", "Tên", "Họ", "Mã MH", "Tên MH", "Tín chỉ",
                "Giữa kỳ", "Cuối kỳ", "Bài tập", "Tổng kết",
                "Điểm chữ", "GPA", "Học kỳ", "Năm học"
            ]
            csv_rows = [
                [r["sid"], r["first_name"], r["last_name"],
                 r["subject_code"], r["subject_name"], r["credits"],
                 r["midterm_score"], r["final_score"], r["assignment_score"],
                 r["total_score"], r["letter_grade"], r["gpa_value"],
                 r["semester"], r["academic_year"]]
                for r in rows
            ]
            return self._write_csv(
                f"grade_report_{timestamp}.csv", headers, csv_rows
            )
        elif format == "json":
            return self._write_json(
                f"grade_report_{timestamp}.json", rows
            )
        else:
            content = self._format_grade_txt(rows)
            return self._write_txt(
                f"grade_report_{timestamp}.txt", content
            )

    def faculty_summary_report(self, format="csv") -> str:
        """Xuất báo cáo tổng hợp theo khoa."""
        rows = self.db.fetchall_as_dict("""
            SELECT f.code, f.name,
                   COUNT(DISTINCT m.id) as major_count,
                   COUNT(DISTINCT s.id) as student_count,
                   ROUND(AVG(s.gpa), 2) as avg_gpa
            FROM faculties f
            LEFT JOIN majors m ON f.id = m.faculty_id
            LEFT JOIN students s ON m.id = s.major_id AND s.status = 'active'
            WHERE f.is_active = 1
            GROUP BY f.id, f.code, f.name
            ORDER BY f.code
        """)
        timestamp = self._get_timestamp()

        if format == "csv":
            headers = ["Mã khoa", "Tên khoa", "Số ngành", "Số SV", "GPA TB"]
            csv_rows = [
                [r["code"], r["name"], r["major_count"],
                 r["student_count"], r["avg_gpa"]]
                for r in rows
            ]
            return self._write_csv(
                f"faculty_summary_{timestamp}.csv", headers, csv_rows
            )
        elif format == "json":
            return self._write_json(
                f"faculty_summary_{timestamp}.json", rows
            )
        else:
            content = "BÁO CÁO TỔNG HỢP THEO KHOA\n"
            content += "=" * 60 + "\n\n"
            for r in rows:
                content += f"Khoa: [{r['code']}] {r['name']}\n"
                content += f"  Số ngành: {r['major_count']}\n"
                content += f"  Số sinh viên: {r['student_count']}\n"
                content += f"  GPA trung bình: {r['avg_gpa']}\n\n"
            return self._write_txt(
                f"faculty_summary_{timestamp}.txt", content
            )

    def attendance_report(self, classroom_id: int,
                           format="csv") -> str:
        """Xuất báo cáo điểm danh theo lớp."""
        rows = self.db.fetchall_as_dict("""
            SELECT s.student_id as sid, s.first_name, s.last_name,
                   a.date, a.status, a.notes
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.classroom_id = ?
            ORDER BY a.date, s.student_id
        """, (classroom_id,))
        timestamp = self._get_timestamp()

        if format == "csv":
            headers = ["Mã SV", "Tên", "Họ", "Ngày", "Trạng thái", "Ghi chú"]
            csv_rows = [
                [r["sid"], r["first_name"], r["last_name"],
                 r["date"], r["status"], r["notes"]]
                for r in rows
            ]
            return self._write_csv(
                f"attendance_{timestamp}.csv", headers, csv_rows
            )
        elif format == "json":
            return self._write_json(
                f"attendance_{timestamp}.json", rows
            )
        else:
            content = "BÁO CÁO ĐIỂM DANH\n"
            content += "=" * 60 + "\n\n"
            for r in rows:
                status_map = {
                    "present": "✓", "absent": "✗",
                    "late": "⟐", "excused": "E"
                }
                content += (f"{r['date']} | {r['sid']} | "
                           f"{r['last_name']} {r['first_name']} | "
                           f"{status_map.get(r['status'], '?')}\n")
            return self._write_txt(
                f"attendance_{timestamp}.txt", content
            )

    def overall_statistics_report(self, format="json") -> str:
        """Xuất báo cáo thống kê tổng hợp."""
        stats = {}

        # Tổng quan
        stats["overview"] = {
            "total_students": self.db.count("students"),
            "active_students": self.db.count("students", "status = 'active'"),
            "total_faculties": self.db.count("faculties", "is_active = 1"),
            "total_subjects": self.db.count("subjects", "is_active = 1"),
            "total_classrooms": self.db.count("classrooms", "is_active = 1"),
        }

        # GPA
        gpa_row = self.db.fetchone(
            "SELECT AVG(gpa) as avg, MAX(gpa) as max, MIN(gpa) as min "
            "FROM students WHERE status = 'active'"
        )
        if gpa_row:
            stats["gpa"] = {
                "average": round(gpa_row["avg"] or 0, 2),
                "maximum": gpa_row["max"] or 0,
                "minimum": gpa_row["min"] or 0,
            }

        # Phân bố GPA
        gpa_dist = self.db.fetchall(
            """
            SELECT
                CASE
                    WHEN gpa >= 3.6 THEN 'Xuất sắc (≥3.6)'
                    WHEN gpa >= 3.2 THEN 'Giỏi (3.2-3.59)'
                    WHEN gpa >= 2.5 THEN 'Khá (2.5-3.19)'
                    WHEN gpa >= 2.0 THEN 'TB (2.0-2.49)'
                    ELSE 'Yếu (<2.0)'
                END as category,
                COUNT(*) as count
            FROM students WHERE status = 'active'
            GROUP BY category
            ORDER BY category
            """
        )
        stats["gpa_distribution"] = {
            row["category"]: row["count"] for row in gpa_dist
        }

        timestamp = self._get_timestamp()

        if format == "json":
            return self._write_json(
                f"overall_stats_{timestamp}.json", stats
            )
        else:
            content = "BÁO CÁO THỐNG KÊ TỔNG HỢP\n"
            content += "=" * 60 + "\n\n"
            content += json.dumps(stats, ensure_ascii=False, indent=2)
            return self._write_txt(
                f"overall_stats_{timestamp}.txt", content
            )

    def _format_student_txt(self, rows):
        """Format danh sách sinh viên cho TXT."""
        content = "DANH SÁCH SINH VIÊN\n"
        content += "=" * 80 + "\n\n"
        for i, r in enumerate(rows, 1):
            content += f"{i}. [{r['student_id']}] {r['last_name']} {r['first_name']}\n"
            content += f"   Email: {r['email']} | SĐT: {r['phone']}\n"
            content += f"   Ngành: {r['major_name']} | Khoa: {r['faculty_name']}\n"
            content += f"   GPA: {r['gpa']} | Trạng thái: {r['status']}\n\n"
        content += f"\nTổng: {len(rows)} sinh viên\n"
        return content

    def _format_grade_txt(self, rows):
        """Format bảng điểm cho TXT."""
        content = "BẢNG ĐIỂM\n"
        content += "=" * 80 + "\n\n"
        current_student = None
        for r in rows:
            if r["sid"] != current_student:
                current_student = r["sid"]
                content += f"\n--- {r['sid']} - {r['last_name']} {r['first_name']} ---\n"
            content += (f"  {r['subject_code']} - {r['subject_name']} "
                       f"({r['credits']} TC): "
                       f"GK={r['midterm_score']} CK={r['final_score']} "
                       f"BT={r['assignment_score']} -> "
                       f"{r['total_score']} ({r['letter_grade']})\n")
        return content
