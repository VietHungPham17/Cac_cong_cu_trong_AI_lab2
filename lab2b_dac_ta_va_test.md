# ĐẶC TẢ TÍNH NĂNG VÀ TEST TDD (LAB 2B)

## 1. Đặc tả 7 thành phần của tính năng (Đã khóa)

| Thuộc tính | Chi tiết Đặc tả |
|---|---|
| **1. Tên tính năng** | Export Grade Report theo Học kỳ (Semester) cho một sinh viên cụ thể. |
| **2. Bối cảnh** | Hiện tại hệ thống xuất toàn bộ bảng điểm, nhưng user cần tính năng chỉ xuất điểm của 1 học kỳ cụ thể để gửi bảng điểm cuối kỳ. |
| **3. Input** | `student_id` (str), `semester` (str), `academic_year` (str), `format` (str mặc định là 'csv') |
| **4. Output** | Trả về chuỗi `filepath` chứa đường dẫn tới file CSV (trong thư mục `reports/`). |
| **5. Module ảnh hưởng** | `report.py` (chứa logic xuất), `main.py` (cập nhật menu CLI). |
| **6. Ràng buộc** | 1. SV phải tồn tại.<br>2. Nếu HK đó không có môn nào, văng exception `ValueError("Không có điểm trong học kỳ này")` thay vì tạo file rỗng. |
| **7. Acceptance Criteria** | 1. Input đúng → Tạo file CSV với N môn + 1 dòng header.<br>2. Input sai/trống → Báo lỗi rõ ràng. |

---

## 2. Bản ghi chạy Test (Test Đỏ trước, Test Xanh sau)

Bằng chứng áp dụng Test-Driven Development (TDD).

### Giai đoạn 1: Test Đỏ (Red - Viết test trước khi sinh mã)
```bash
$ python3 -m pytest tests/test_export_semester.py -v
========================= test session starts ==========================
collected 2 items

tests/test_export_semester.py::test_export_success FAILED       [ 50%]
tests/test_export_semester.py::test_export_empty FAILED         [100%]

============================== FAILURES ==============================
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
    def test_export_success():
>       report = ReportGenerator()
>       path = report.grade_report_by_semester(1, "1", "2023-2024")
E       AttributeError: 'ReportGenerator' object has no attribute 'grade_report_by_semester'
====================== 2 failed in 0.05s =============================
```

### Giai đoạn 2: Test Xanh (Green - Sau khi dùng AI Composer sinh mã)
```bash
$ python3 -m pytest tests/test_export_semester.py -v
========================= test session starts ==========================
collected 2 items

tests/test_export_semester.py::test_export_success PASSED       [ 50%]
tests/test_export_semester.py::test_export_empty PASSED         [100%]

========================== 2 passed in 0.03s ===========================
```

---

## 3. Ba thay đổi do AI đề xuất đã bị từ chối

Trong quá trình dùng AI sinh mã, tôi đã đọc diff và **TỪ CHỐI** các đề xuất sau kèm lý do kỹ thuật rõ ràng:

1. **AI đề xuất thêm cột GPA học kỳ trực tiếp vào file Report CSV.**
   - **Lý do từ chối:** Vi phạm Single Responsibility Principle (SRP). Việc tính GPA yêu cầu loop qua các credits và weights, thuộc về logic của DB/Models. `report.py` chỉ có nhiệm vụ dump dữ liệu thô. Tôi ép AI gọi hàm tính GPA bên ngoài thay vì mix vào report.
2. **AI dùng thư viện Pandas để ghi CSV.**
   - **Lý do từ chối:** Đưa vào một dependency quá nặng (Pandas) chỉ để ghi 1 mảng dictionary ra CSV là over-engineering. Tôi yêu cầu AI dùng built-in `csv` module như kiến trúc hiện tại để nhẹ và nhất quán.
3. **AI bắt lỗi Exception chung chung bằng `try: ... except Exception: return None`.**
   - **Lý do từ chối:** Xử lý lỗi (Error swallowing) rất tệ. Nếu thư mục reports không có quyền ghi, file sẽ không sinh ra mà caller không nhận được lỗi cụ thể. Tôi từ chối và yêu cầu AI để nguyên exception sụp đổ hoặc raise ValueError cụ thể theo đặc tả.
