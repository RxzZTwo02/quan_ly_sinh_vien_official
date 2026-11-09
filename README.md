# Website quản lý sinh viên — kiến trúc front-end / back-end + MySQL

## Kiến trúc
```
Trình duyệt ──HTTP──▶ Front-end Flask (:5000) ──REST/JSON──▶ Back-end Flask API (:5001) ──▶ MySQL (qlsv)
                      frontend/                               backend/                      Laragon hoặc Docker
```
- **frontend/**: giao diện (Jinja + Chart.js), form, CSRF. Không truy cập DB; mọi dữ liệu lấy qua API của back-end (gọi phía server bằng `requests`, nên trình duyệt không gọi thẳng API).
- **backend/**: REST API JSON, kiểm tra dữ liệu, truy vấn MySQL bằng PyMySQL. Tự tạo database `qlsv` và các bảng khi khởi động.

## Công nghệ
- Python 3.12+ · Flask · Waitress
- MySQL 8 (Laragon khi chạy trực tiếp, image `mysql:8.4` khi chạy Docker) · PyMySQL
- Chart.js (tải từ CDN) cho biểu đồ

## Chạy trực tiếp với Laragon (không cần Docker)
1. Mở **Laragon** → **Start All** (hoặc chỉ bật MySQL). Mặc định Laragon dùng `root` / mật khẩu rỗng / cổng 3306; ứng dụng dùng sẵn các giá trị này nên **không cần tạo file `.env`**. Database `qlsv` được tạo tự động.
2. Terminal 1 — back-end:
   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```
   Kiểm tra: http://127.0.0.1:5001/api/health → `{"status":"ok","database":"ok"}`
3. (Tùy chọn, chạy một lần) chép dữ liệu cũ từ SQLite `data/students.db` sang MySQL:
   ```powershell
   .\.venv\Scripts\python.exe migrate_sqlite_to_mysql.py
   ```
   Script giữ nguyên id và bỏ qua dòng đã có, nên chạy lại không bị trùng.
4. Terminal 2 — front-end:
   ```powershell
   cd frontend
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe app.py
   ```
   Truy cập http://127.0.0.1:5000

Xem dữ liệu: dùng HeidiSQL/phpMyAdmin của Laragon, mở database `qlsv`.

## Biến môi trường
Sao chép `backend/.env.example` → `backend/.env`, `frontend/.env.example` → `frontend/.env` nếu cần đổi.

| App | Biến | Mặc định | Ý nghĩa |
|---|---|---|---|
| backend | `DB_HOST` / `DB_PORT` | `127.0.0.1` / `3306` | địa chỉ MySQL |
| backend | `DB_USER` / `DB_PASSWORD` | `root` / *(rỗng)* | tài khoản MySQL |
| backend | `DB_NAME` | `qlsv` | tên database (tự tạo) |
| backend | `API_HOST` / `API_PORT` | `127.0.0.1` / `5001` | nơi API lắng nghe |
| cả hai | `API_TOKEN` | *(rỗng)* | nếu đặt, front-end gửi header `X-API-Key`; hai bên phải trùng nhau |
| frontend | `BACKEND_URL` | `http://127.0.0.1:5001` | địa chỉ back-end |
| frontend | `FRONTEND_HOST` / `FRONTEND_PORT` | `127.0.0.1` / `5000` | nơi giao diện lắng nghe |
| frontend | `SECRET_KEY` | ngẫu nhiên mỗi lần chạy | nên đặt cố định để phiên không mất khi khởi động lại |

## REST API (back-end)
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/health` | trạng thái API và kết nối DB |
| GET | `/api/students?q=` | danh sách / tìm sinh viên |
| GET · PUT · DELETE | `/api/students/<id>` | xem / sửa / xóa (xóa kèm điểm, học phí) |
| POST | `/api/students` | thêm sinh viên |
| GET · POST | `/api/subjects` | danh sách / thêm môn học |
| GET · POST | `/api/grades` | bảng điểm / lưu điểm (trùng SV + môn + học kỳ thì cập nhật) |
| DELETE | `/api/grades/<id>` | xóa bản ghi điểm |
| GET · POST | `/api/tuition` | học phí / lưu học phí (trùng SV + học kỳ thì cập nhật) |
| GET | `/api/stats` | số liệu KPI và dữ liệu biểu đồ |

Lỗi trả về dạng `{"error": "..."}` với mã 400/404/409/503; thành công kèm `{"message": "..."}`.

## Chạy bằng Docker
```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f backend frontend
```
Truy cập http://localhost:5000. Gồm 3 service: `mysql`, `backend`, `frontend`. MySQL trong Docker **không mở cổng 3306** ra máy host nên chạy song song với Laragon không bị xung đột. Dữ liệu nằm trong volume `mysql_data` (`docker compose down` không xóa volume; `docker compose down -v` thì có).

Có thể đặt `MYSQL_ROOT_PASSWORD`, `SECRET_KEY`, `API_TOKEN` trong file `.env` cạnh `compose.yaml`.

## Dashboard
- Thẻ KPI: tổng sinh viên, môn học, bản ghi điểm, học phí còn nợ.
- Biểu đồ học phí phải đóng / đã đóng / còn nợ, phân loại kết quả học tập, số sinh viên theo lớp — dữ liệu truy vấn trực tiếp từ MySQL.
- Chart.js tải từ CDN nên trình duyệt cần Internet để hiển thị biểu đồ.
