# Đặc tả hệ thống Quản lý sinh viên

Bộ tài liệu mô tả hệ thống **đúng như mã nguồn hiện tại** (back-end Flask API + front-end Flask + MySQL). Khi sửa mã, cập nhật file đặc tả tương ứng. Hướng dẫn cài đặt và chạy từng bước nằm ở [README.md](../README.md) của dự án.

| File | Nội dung |
|---|---|
| [01-tong-quan.md](01-tong-quan.md) | Mục tiêu, phạm vi, người dùng, kiến trúc, công nghệ |
| [02-yeu-cau-chuc-nang.md](02-yeu-cau-chuc-nang.md) | Yêu cầu chức năng và quy tắc nghiệp vụ |
| [03-co-so-du-lieu.md](03-co-so-du-lieu.md) | Lược đồ MySQL, ràng buộc, seed dữ liệu mẫu |
| [04-api.md](04-api.md) | Đặc tả REST API của back-end |
| [05-giao-dien.md](05-giao-dien.md) | Route front-end, bố cục trang, chế độ sửa, cập nhật tại chỗ, hỏi lưu dữ liệu đang nhập dở |
| [06-cau-hinh-trien-khai.md](06-cau-hinh-trien-khai.md) | Biến môi trường, chạy trực tiếp, Docker, bảo mật |
| [07-han-che.md](07-han-che.md) | Hạn chế đã biết và hướng cải tiến |

Tài liệu lịch sử (giữ nguyên như lúc viết, **không** cập nhật theo mã):

| File | Nội dung |
|---|---|
| [ke-hoach-thay-doi-kien-truc.md](ke-hoach-thay-doi-kien-truc.md) | Kế hoạch tách front-end / back-end và chuyển SQLite → MySQL (09/11/2026). Một số chi tiết đã khác mã hiện tại, ví dụ script chép dữ liệu từ SQLite đã bị bỏ. |

## Quy ước
- Mã yêu cầu: `FR-xx` (chức năng), `NFR-xx` (phi chức năng), `BR-xx` (quy tắc nghiệp vụ).
- Đường dẫn file tính từ thư mục gốc dự án.
