# 01 — Tổng quan

## 1. Mục tiêu
Website giúp cán bộ quản lý đào tạo theo dõi trên **một trang duy nhất**:
- hồ sơ sinh viên;
- danh mục môn học;
- bảng điểm theo học kỳ;
- học phí và công nợ;
- số liệu tổng quan (KPI) và biểu đồ.

## 2. Phạm vi
**Trong phạm vi**
- Thêm / sửa / xóa / tìm kiếm sinh viên.
- Thêm môn học, xem danh mục môn học.
- Nhập, cập nhật, xóa điểm; tự tính điểm tổng kết.
- Nhập, cập nhật học phí theo học kỳ; tự tính số còn nợ.
- Dashboard: 4 thẻ KPI, 3 biểu đồ.
- Chép dữ liệu cũ từ SQLite sang MySQL.

**Ngoài phạm vi** (chưa có trong mã)
- Đăng nhập, phân quyền người dùng.
- Sửa / xóa môn học, xóa bản ghi học phí.
- Phân trang, xuất Excel/PDF, nhập dữ liệu hàng loạt.

## 3. Người dùng
| Vai trò | Mô tả |
|---|---|
| Người quản lý | Người duy nhất dùng giao diện web; mọi người truy cập được trang đều có toàn quyền. |
| Hệ thống khác (tùy chọn) | Gọi trực tiếp REST API của back-end, có thể yêu cầu `X-API-Key`. |

## 4. Kiến trúc
```
Trình duyệt ──HTTP (HTML form)──▶ Front-end Flask :5000 ──REST/JSON (requests)──▶ Back-end Flask API :5001 ──PyMySQL──▶ MySQL (qlsv)
```
- **Front-end** (`frontend/`): render HTML bằng Jinja, xử lý form, kiểm tra CSRF. **Không truy cập DB**; mọi dữ liệu lấy qua API, gọi phía server nên trình duyệt không gọi thẳng back-end.
- **Back-end** (`backend/`): REST API JSON, kiểm tra dữ liệu, truy vấn MySQL. Khi khởi động tự tạo database `qlsv` và các bảng.
- **CSDL**: MySQL 8 (Laragon khi chạy trực tiếp, image `mysql:8.4` khi chạy Docker).

### Luồng xử lý một thao tác ghi (ví dụ thêm sinh viên)
1. Trình duyệt `POST /save` (form + `csrf_token`) tới front-end.
2. Front-end kiểm tra CSRF, gọi `POST /api/students` (JSON) tới back-end.
3. Back-end kiểm tra dữ liệu, ghi MySQL trong một transaction, trả `{"message": ...}` hoặc `{"error": ...}`.
4. Front-end chuyển hướng `302` về `/?message=...` hoặc `/?error=...` (mẫu Post/Redirect/Get).
5. Trang chủ gọi lại các API đọc và hiển thị thông báo.

## 5. Công nghệ
| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.12+ |
| Web framework | Flask 3.1, phục vụ bằng Waitress 3.0 |
| Kết nối DB | PyMySQL 1.1 (+ `cryptography` cho xác thực MySQL 8) |
| Gọi API | `requests` 2.32 |
| Cấu hình | `python-dotenv` |
| Biểu đồ | Chart.js 4.4.9 (CDN jsDelivr) |
| Đóng gói | Docker, Docker Compose |

## 6. Cấu trúc mã nguồn
```
backend/
  app.py                    # route REST API, kiểm tra dữ liệu, xử lý lỗi
  db.py                     # kết nối, transaction, lược đồ bảng
  config.py                 # đọc biến môi trường / .env
  migrate_sqlite_to_mysql.py
frontend/
  app.py                    # route giao diện, CSRF
  api_client.py             # gọi back-end bằng requests
  templates/index.html      # giao diện một trang + Chart.js
data/students.db            # dữ liệu SQLite cũ (nguồn để chép sang MySQL)
compose.yaml                # mysql + backend + frontend
```
