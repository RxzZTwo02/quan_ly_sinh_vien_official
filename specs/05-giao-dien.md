# 05 — Giao diện (front-end)

- Địa chỉ mặc định: `http://127.0.0.1:5000`
- Mã nguồn: `frontend/app.py`, `frontend/api_client.py`, `frontend/templates/index.html`.
- Ứng dụng **một trang**: mọi chức năng nằm ở `/`; form POST xong chuyển hướng về `/` (Post/Redirect/Get).

## 1. Route
| Method | Đường dẫn | Xử lý | API back-end gọi tới |
|---|---|---|---|
| GET | `/` | Trang chính. Tham số: `q` (tìm kiếm), `edit` (id sinh viên cần sửa), `message`, `error` (thông báo) | `GET /api/students?q=`, `GET /api/students/<edit>`, `GET /api/subjects`, `GET /api/grades`, `GET /api/tuition`, `GET /api/stats` |
| POST | `/save` | Thêm sinh viên (không có `id`) hoặc sửa (có `id`) | `POST /api/students` / `PUT /api/students/<id>` |
| POST | `/delete/<id>` | Xóa sinh viên | `DELETE /api/students/<id>` |
| POST | `/subjects/save` | Thêm môn học | `POST /api/subjects` |
| POST | `/grades/save` | Lưu điểm | `POST /api/grades` |
| POST | `/grades/delete/<id>` | Xóa điểm | `DELETE /api/grades/<id>` |
| POST | `/tuition/save` | Lưu học phí | `POST /api/tuition` |
| GET | `/health` | `200 {"frontend":"ok","backend":{...}}` hoặc `503` khi back-end lỗi | `GET /api/health` |

### Xử lý lỗi
- Lỗi từ API khi ghi → chuyển hướng `/?error=<thông điệp của back-end>`.
- Lỗi khi tải trang chính (back-end tắt, MySQL tắt…) → vẫn render trang với dữ liệu rỗng và thông báo lỗi; mã HTTP `503` nếu back-end trả/không kết nối được (503), ngược lại `502`.
- `?edit=<id>` không tồn tại → thông báo "Không tìm thấy sinh viên cần sửa."
- `id` trong form sửa không phải số → `400`.

## 2. CSRF
- Token 32 byte ngẫu nhiên lưu trong session (cookie `HttpOnly`, `SameSite=Lax`).
- Mọi form POST có trường ẩn `csrf_token`; sai hoặc thiếu → `400 "Phiên làm việc hết hạn. Hãy tải lại trang."`.
- Nếu không đặt `SECRET_KEY`, khóa ký session đổi mỗi lần khởi động front-end → các trang đang mở sẽ bị lỗi CSRF, cần tải lại.

## 3. Bố cục trang (từ trên xuống)
1. **Đầu trang**: tiêu đề "🎓 Quản lý sinh viên" và mô tả.
2. **Thông báo**: hộp xanh (`message`) / đỏ (`error`).
3. **Thẻ KPI** (4 thẻ): Tổng sinh viên · Môn học · Bản ghi điểm · Học phí còn nợ (định dạng `1,234,567 đ`).
4. **Dashboard** (3 biểu đồ Chart.js):
   | Biểu đồ | Loại | Dữ liệu |
   |---|---|---|
   | Tình hình học phí | Cột dọc | Phải đóng / Đã đóng / Còn nợ; tooltip định dạng VNĐ, trục rút gọn (`8 Tr`) |
   | Phân loại kết quả học tập | Vành khuyên | Số bản ghi theo Giỏi / Khá / Trung bình / Cần cố gắng |
   | Sinh viên theo lớp | Cột ngang | Tối đa 8 lớp |
5. **Thanh điều hướng**: liên kết neo `#students`, `#subjects`, `#grades`, `#tuition`.
6. **Sinh viên** (`#students`)
   - Form "Thêm sinh viên" / "Cập nhật sinh viên": Mã SV, Họ tên, Lớp, Email (email dùng `type="email"`); khi sửa có nút **Hủy**.
   - Ô tìm kiếm + nút **Tất cả**.
   - Bảng: Mã SV · Họ tên · Lớp · Email · Thao tác (**Sửa**, **Xóa** có hộp xác nhận).
7. **Môn học** (`#subjects`): form Mã môn, Tên môn, Tín chỉ (1–10, mặc định 3); bảng Mã môn · Tên môn · Tín chỉ.
8. **Bảng điểm** (`#grades`)
   - Form: chọn sinh viên, chọn môn, học kỳ, 3 điểm (0–10, bước 0,1, mặc định 8).
   - Bảng: Mã SV · Sinh viên · Môn học · Học kỳ · Chuyên cần · Giữa kỳ · Cuối kỳ · Tổng kết (2 chữ số) · nút **Xóa** có xác nhận.
9. **Học phí và công nợ** (`#tuition`)
   - Form: chọn sinh viên, học kỳ, phải đóng (bước 1.000), đã đóng (mặc định 0), hạn đóng (ô ngày), ghi chú.
   - Bảng: Mã SV · Sinh viên · Học kỳ · Phải đóng · Đã đóng · Còn nợ · Hạn đóng (`—` nếu trống) · Trạng thái ("Đã hoàn thành" xanh / "Còn nợ" cam).
10. **Chân trang**: công nghệ và liên kết `/health`.

## 4. Kiểm tra phía trình duyệt
Các ô nhập có `required`, `maxlength`, `min`/`max` tương ứng quy tắc ở back-end. Đây chỉ là hỗ trợ người dùng; **back-end mới là nơi kiểm tra chính thức**.

## 5. Biểu đồ
- Dữ liệu nhúng vào trang qua `<script type="application/json" id="dashboard-data">` (Jinja `tojson`).
- Chart.js 4.4.9 tải từ `cdn.jsdelivr.net`; không tải được thì mỗi vùng biểu đồ hiện "Không tải được thư viện biểu đồ. Kiểm tra kết nối Internet."
- Biểu đồ không tự làm mới; dữ liệu cập nhật khi tải lại trang.
