# Đặc tả hệ thống Quản lý sinh viên

Bộ tài liệu mô tả hệ thống **đúng như mã nguồn hiện tại** (back-end Flask API + front-end Flask + MySQL). Khi sửa mã, cập nhật file đặc tả tương ứng. Hướng dẫn cài đặt và chạy từng bước nằm ở [README.md](../README.md) của dự án.

| File | Nội dung |
|---|---|
| [01-tong-quan.md](01-tong-quan.md) | Mục tiêu, phạm vi, người dùng, kiến trúc, công nghệ |
| [02-yeu-cau-chuc-nang.md](02-yeu-cau-chuc-nang.md) | Yêu cầu chức năng và quy tắc nghiệp vụ |
| [03-co-so-du-lieu.md](03-co-so-du-lieu.md) | Lược đồ MySQL, ràng buộc, seed dữ liệu mẫu |
| [04-api.md](04-api.md) | Đặc tả REST API của back-end |
| [05-giao-dien.md](05-giao-dien.md) | Route front-end, giữ kết quả tìm kiếm, thông báo, trang lỗi, bố cục trang, chế độ sửa, hàng nút và chọn dòng, cập nhật tại chỗ, hỏi lưu dữ liệu đang nhập dở, xác nhận xóa |
| [06-cau-hinh-trien-khai.md](06-cau-hinh-trien-khai.md) | Biến môi trường, chạy trực tiếp, ghi log, Docker, bảo mật |
| [07-han-che.md](07-han-che.md) | Hạn chế đã biết, hướng cải tiến, các hạn chế và lỗi (BUG-xx) đã khắc phục |

Tài liệu lịch sử (giữ nguyên như lúc viết, **không** cập nhật theo mã):

| File | Nội dung |
|---|---|
| [ke-hoach-thay-doi-kien-truc.md](ke-hoach-thay-doi-kien-truc.md) | Kế hoạch tách front-end / back-end và chuyển SQLite → MySQL (09/11/2026). Một số chi tiết đã khác mã hiện tại, ví dụ script chép dữ liệu từ SQLite đã bị bỏ. |
| [08-bao-cao-kiem-thu-2026-11-16.md](08-bao-cao-kiem-thu-2026-11-16.md) | Báo cáo kiểm thử phần Sinh viên (16/11/2026, commit `92f992d`): 39 test case, 9 lỗi BUG-01 … BUG-09. Cách khắc phục ghi ở [07](07-han-che.md) mục 3. |

## Quy ước
- Mã yêu cầu: `FR-xx` (chức năng), `NFR-xx` (phi chức năng), `BR-xx` (quy tắc nghiệp vụ).
- Mã hạn chế: `L-xx` (hạn chế ghi nhận khi đọc mã), `BUG-xx` (lỗi trong báo cáo kiểm thử [08](08-bao-cao-kiem-thu-2026-11-16.md)); cả hai đều theo dõi ở [07](07-han-che.md).
- Đường dẫn file tính từ thư mục gốc dự án.
