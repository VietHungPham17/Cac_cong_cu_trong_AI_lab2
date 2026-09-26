# Student Management System (SMS)

Hệ thống quản lý sinh viên sử dụng Python + SQLite.

## Tính năng
- Quản lý sinh viên (CRUD)
- Quản lý khoa/ngành
- Quản lý môn học và điểm
- Quản lý lớp học
- Xuất báo cáo CSV

## Cấu trúc thư mục
```
├── main.py              # CLI chính
├── student_db.py         # CRUD sinh viên
├── faculty_db.py         # CRUD khoa
├── subject_db.py         # CRUD môn học
├── grade_db.py           # CRUD điểm
├── classroom_db.py       # CRUD lớp
├── report.py             # Xuất báo cáo
├── database.py           # Kết nối DB
├── models.py             # Models
├── validators.py         # Validation
├── utils.py              # Tiện ích
├── config.py             # Cấu hình
└── tests/
    ├── test_student.py
    ├── test_faculty.py
    └── test_grade.py
```

## Cài đặt
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Chạy test
```bash
pytest tests/ -v
```
