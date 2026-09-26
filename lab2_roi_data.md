# DỮ LIỆU ĐO LƯỜNG GỢI Ý CỦA AI (LAB 2)

## 1. Bảng 20 dòng dữ liệu thô

| STT | Tác vụ thực hiện trên repository | Phân loại | Bấm chấp nhận (Y/N) | Giữ lại sau 24h (Y/N) | TG hoàn thành (phút) | TG tự làm ước tính (phút) |
|-----|-----------------------------------|-----------|---------------------|-----------------------|----------------------|---------------------------|
| 1 | Viết hàm `create()` trong student_db.py | Viết mới | Y | Y | 3 | 12 |
| 2 | Viết hàm `get_paginated()` với bộ lọc | Viết mới | Y | Y | 5 | 18 |
| 3 | Viết hàm `calculate_total()` trong Grade | Viết mới | Y | N (phải sửa logic) | 2 | 8 |
| 4 | Viết hàm `validate_student_id()` regex | Viết mới | Y | Y | 1 | 5 |
| 5 | Viết hàm `bulk_import()` | Viết mới | Y | Y | 4 | 15 |
| 6 | Viết hàm `enroll_student()` kiểm tra sĩ số | Viết mới | Y | N (thiếu check trùng) | 3 | 10 |
| 7 | Viết hàm `get_transcript()` JOIN query | Viết mới | Y | Y | 2 | 8 |
| 8 | Viết hàm `student_list_report()` CSV export | Viết mới | Y | Y | 3 | 12 |
| 9 | Sửa lỗi foreign key trong `initialize_tables()` | Sửa lỗi | Y | Y | 1 | 3 |
| 10 | Thêm index cho bảng grades | Cải tiến | Y | Y | 1 | 2 |
| 11 | Viết test `test_create_student_success` | Test | Y | Y | 1 | 4 |
| 12 | Viết test `test_pagination` 25 records | Test | Y | N (sửa lại assert) | 2 | 6 |
| 13 | Hoàn tất docstring cho models.py | Tài liệu | Y | Y | 1 | 5 |
| 14 | Gợi ý `format_table()` trong utils.py | Tiện ích | N (sai format) | — | 2 | 4 |
| 15 | Auto-complete các lựa chọn menu CLI | UI | Y | Y | 1 | 3 |
| 16 | Viết `_log_action()` ghi audit trail | Cải tiến | Y | Y | 2 | 7 |
| 17 | Gợi ý SQL query thống kê GPA phân bố | Query | Y | Y | 1 | 5 |
| 18 | Sửa lỗi `validate_unique` với exclude_id | Sửa lỗi | N (gợi ý sai logic) | — | 3 | 4 |
| 19 | Thêm context manager `transaction()` | Cải tiến | Y | Y | 1 | 6 |
| 20 | Auto-complete hàm `_seed_sample_data()` | Viết mới | Y | N (cần sửa data mẫu) | 2 | 8 |

## 2. Các chỉ số đo lường (AR & RR)

- **Tổng số gợi ý:** 20
- **Số gợi ý được chấp nhận (Accept):** 18
- **Số gợi ý giữ nguyên sau 24h:** 14

**Kết quả:**
- **AR (Tỷ lệ chấp nhận - Acceptance Rate):** 18/20 = **90%**
- **RR (Tỷ lệ giữ lại - Retention Rate):** 14/18 = **78%**
- **Độ chênh lệch (AR - RR):** **12%** (đây là tỷ lệ code do AI sinh ra phải chỉnh sửa lại hoặc loại bỏ trong quá trình review/test).

## 3. Ước tính lợi ích ròng theo năm (ROI)

**Dữ liệu đo đạc:**
- Thời gian dùng AI: 41 phút.
- Thời gian ước tính nếu tự làm: 145 phút.
- Tiết kiệm được: 104 phút (~1.7 giờ) cho 20 tác vụ.

**Tính toán lợi ích ròng (Nhóm 8 người):**
- **Tần suất ước tính:** Mỗi lập trình viên thực hiện trung bình 20 tác vụ tương tự mỗi tuần.
- **Tiết kiệm mỗi tuần:** 1.7 giờ/người.
- **Đơn giá giờ công:** Ước tính 150.000 VNĐ/giờ.
- **Số tuần làm việc/năm:** 48 tuần.
- **Tiết kiệm 1 người/năm:** 1.7h × 48 tuần × 150.000đ = 12.240.000 VNĐ.
- **Tiết kiệm nhóm 8 người/năm:** 12.240.000đ × 8 = **97.920.000 VNĐ**.

**Chi phí công cụ AI:**
- Gói Pro (VD: Cursor/Copilot): ~$20/tháng/người ≈ 500.000 VNĐ/tháng.
- Chi phí nhóm 8 người/năm: 500.000đ × 8 × 12 = **48.000.000 VNĐ**.

**Lợi ích ròng (Net Benefit):**
- 97.920.000 VNĐ - 48.000.000 VNĐ = **+49.920.000 VNĐ/năm**.

## 4. Khuyến nghị

**Khuyến nghị:** **CÓ NÊN MUA BẢN PRO.**

**Điều kiện đi kèm:**
1. Các thành viên phải được hướng dẫn cách review mã nguồn do AI sinh ra, đặc biệt là các logic kiểm tra ràng buộc (vì tỷ lệ sửa lại RR thấp hơn AR 12%).
2. Không chấp nhận mù quáng (blind accept), mọi gợi ý từ 5 dòng trở lên bắt buộc phải đọc hiểu.

**Giới hạn đánh giá:**
- Kết luận này thừa nhận giới hạn cỡ mẫu còn khá nhỏ (**n=20**), khoảng biến thiên của AR và RR có thể sai số ±15% trong các loại dự án phức tạp hơn.
- Cần thực hiện đánh giá lại sau 1 tháng sử dụng thực tế (với cỡ mẫu n > 100).
