# SO SÁNH 3 CHẾ ĐỘ SỬ DỤNG AI (LAB 2C)

## 1. Tác vụ đo lường
**Bối cảnh:** Sửa lỗi logic tính điểm trong hàm `calculate_total()` của `models.py`. Lỗi hiện tại: Khi thiếu điểm bài tập (assignment_score), hệ thống không chuẩn hóa lại trọng số (tức là chia cho tổng trọng số còn lại) khiến điểm bị sai lệch lớn, thay vì chia cho `(0.3 + 0.5 = 0.8)`.

Thực hiện trên 3 nhánh Git độc lập:
1. `fix/autocomplete`
2. `fix/inline-edit`
3. `fix/composer`

## 2. Bảng đo đạc (3 chế độ × 4 đại lượng)

| Chế độ thao tác                                | TG hoàn thành tới lúc test báo XANH | Số dòng bị thay đổi (Diff) | Số dòng phải tự sửa lại bằng tay | Kết quả Test |
| ---------------------------------------------- | ----------------------------------- | -------------------------- | -------------------------------- | ------------ |
| **Lần 1: Autocomplete (Gợi ý tự động lúc gõ)** | 18 phút                             | 12 dòng                    | 3 dòng                           | ✅ Xanh       |
| **Lần 2: Inline Edit (Bôi đen vùng chọn)**     | 10 phút                             | 15 dòng                    | 2 dòng                           | ✅ Xanh       |
| **Lần 3: Composer (Đa tệp)**                   | 7 phút                              | 28 dòng                    | 6 dòng                           | ✅ Xanh       |
## 3. Kết luận và Ghi chú

### Chế độ nào phù hợp cho loại tác vụ nào?
- **Autocomplete:** Phù hợp cho việc viết boilerplate, điền tham số lặp lại, hoặc sửa 1-2 dòng nhỏ lẻ. Không phù hợp cho logic thuật toán vì sinh rải rác từng dòng.
- **Inline Edit (Khuyên dùng nhất):** Phù hợp nhất cho tác vụ sửa lỗi, tái cấu trúc thuật toán trong 1 hàm. Vì bạn khoanh vùng phạm vi rất rõ ràng, AI không can thiệp bên ngoài.
- **Composer đa tệp:** Tuyệt vời khi tạo tính năng mới từ đầu cần chèn code vào nhiều file (models, db, cli) cùng lúc. Không nên dùng để sửa 1 bug logic nhỏ.

### Chế độ nào tạo ra bản Diff khó đọc nhất?
**Chế độ Composer đa tệp** là khó đọc Diff nhất.
*Lý do:* 
Trong khi yêu cầu chỉ là sửa một lỗi toán học trong hàm `calculate_total()`, Composer lại lan man quét các file khác và tự ý định dạng lại (format) code xung quanh (ví dụ: tự ý sắp xếp lại thứ tự import, tự động xóa các dòng trắng trống). Điều này tạo ra tới 28 dòng Diff (noise), làm việc review code trên Github PR trở nên khó khăn vì phải tách biệt phần fix bug thực sự và phần format cosmetic.
