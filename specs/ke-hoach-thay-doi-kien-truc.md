> **Prompt gốc (Plan mode, 09/11/2026):** Thay đổi kiến trúc hệ thống, tách front-end, back-end thành 2 ứng dụng flask khác nhau. Thay đổi database từ sqlite3 thành mysql và làm app tương thích với database mysql laragon khi chạy trực tiếp mà không qua Docker.
>
> Khôi phục từ `~/.claude/plans/thay-i-ki-n-tr-c-shimmering-sunrise.md`. Plan này đã được triển khai trong commit `2d3fe36`; các link `app.py#L…` trỏ tới file `app.py` cũ ở thư mục gốc (đã bị xoá).

# Kế hoạch: Tách front-end / back-end thành 2 ứng dụng Flask + chuyển SQLite → MySQL (Laragon)

## Context
Hiện tại toàn bộ hệ thống nằm trong một file [app.py](app.py) (247 dòng): kết nối SQLite, khởi tạo bảng, xử lý form, render Jinja `templates/index.html`. Yêu cầu:
1. Tách thành **2 ứng dụng Flask độc lập**: back-end (REST API JSON, truy cập DB) và front-end (giao diện Jinja, gọi API).
2. Đổi DB từ **sqlite3 → MySQL**, chạy được trực tiếp với **MySQL của Laragon** (đã có `C:/laragon/bin/mysql/mysql-8.4.3-winx64`, mặc định `root` / mật khẩu rỗng / `127.0.0.1:3306`) mà không cần Docker.

Quyết định đã chốt với người dùng:
- Front-end gọi back-end **phía server** bằng `requests` (giữ nguyên giao diện, form, CSRF; không cần CORS).
- **Cập nhật Docker** thành 3 service: `mysql` + `backend` + `frontend`.
- Thêm **script migrate** dữ liệu từ `data/students.db` (4 SV, 2 môn, 1 điểm, 2 học phí) sang MySQL.

## Cấu trúc thư mục mới
```
backend/
  app.py                     # Flask REST API (waitress, cổng 5001)
  config.py                  # đọc .env (python-dotenv), giá trị mặc định = Laragon
  db.py                      # PyMySQL: get_connection(), init_database()
  migrate_sqlite_to_mysql.py # copy dữ liệu SQLite → MySQL (chạy 1 lần)
  requirements.txt           # Flask, waitress, PyMySQL, cryptography, python-dotenv
  .env.example  Dockerfile  .dockerignore
frontend/
  app.py                     # Flask UI (waitress, cổng 5000), route giữ nguyên tên cũ
  api_client.py              # wrapper requests.Session gọi back-end, chuẩn hoá lỗi
  templates/index.html       # chuyển từ templates/index.html, sửa tối thiểu
  requirements.txt           # Flask, waitress, requests, python-dotenv
  .env.example  Dockerfile  .dockerignore
data/students.db             # giữ lại làm nguồn migrate
compose.yaml  README.md
```
Xoá ở gốc: `app.py`, `templates/`, `Dockerfile`, `requirements.txt`, `.env` (rỗng), `.dockerignore` (thay bằng file riêng mỗi app).

## Back-end (`backend/`)

### Cấu hình (`config.py`) — mặc định khớp Laragon, `.env` là tuỳ chọn
`DB_HOST=127.0.0.1`, `DB_PORT=3306`, `DB_USER=root`, `DB_PASSWORD=` (rỗng), `DB_NAME=qlsv`, `API_HOST=127.0.0.1`, `API_PORT=5001`, `API_TOKEN=` (tuỳ chọn; nếu đặt thì mọi request `/api/*` trừ health phải có header `X-API-Key` khớp).

### `db.py`
- `get_connection()`: `pymysql.connect(..., charset="utf8mb4", cursorclass=DictCursor, autocommit=False, client_flag=CLIENT.FOUND_ROWS)`.
  **`FOUND_ROWS` bắt buộc**: thiếu nó, UPDATE sinh viên không đổi giá trị trả rowcount=0 → bị 404 nhầm.
- Context manager `transaction()` commit/rollback + close, thay cho `with conn:` của sqlite.
- `init_database()`: kết nối không chọn DB → `CREATE DATABASE IF NOT EXISTS qlsv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci` → tạo bảng. Có vòng retry (vd 30 lần × 2s) để chờ MySQL trong Docker sẵn sàng; báo lỗi rõ ràng "Hãy bật MySQL trong Laragon" khi chạy trực tiếp mà không kết nối được.

### Chuyển schema SQLite → MySQL (ENGINE=InnoDB, utf8mb4)
| SQLite | MySQL |
|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `TEXT NOT NULL UNIQUE` (mã SV/môn) | `VARCHAR(20) NOT NULL UNIQUE` (TEXT không UNIQUE được nếu không có độ dài) |
| `full_name/class_name/email/subject_name/semester` TEXT | `VARCHAR(100/50/120/120/20)` khớp maxlength của form |
| điểm `REAL` | `DOUBLE` + giữ các `CHECK` (MySQL ≥ 8.0.16 có enforce CHECK) |
| tiền `REAL` | `DECIMAL(15,2)` |
| `due_date TEXT DEFAULT ''`, `note TEXT DEFAULT ''` | `VARCHAR(10)` / `VARCHAR(200) NOT NULL DEFAULT ''` (TEXT không có DEFAULT) |
| `FOREIGN KEY ... ON DELETE CASCADE` | giữ nguyên (InnoDB) |

### Chuyển câu SQL
- Placeholder `?` → `%s`.
- `MAX(a-b, 0)` (scalar) → `GREATEST(a-b, 0)`; `SUM(MAX(...))` → `SUM(GREATEST(...))`.
- `ON CONFLICT(...) DO UPDATE SET x=excluded.x` → `ON DUPLICATE KEY UPDATE x=VALUES(x)` (chạy trên cả MySQL 8.4 và MariaDB).
- `sqlite3.IntegrityError` → `pymysql.err.IntegrityError` (1062 trùng khoá → 409, 1452 FK không tồn tại → 400).
- Kết quả `DECIMAL` → ép `float` trước khi trả JSON (helper `to_jsonable(row)`), để template `"{:,.0f}".format(...)` vẫn chạy.

### REST API (JSON; lỗi dạng `{"error": "..."}`, thành công dạng `{"message": "...", ...}`)
| Method | Endpoint | Thay cho logic cũ |
|---|---|---|
| GET | `/api/health` | `/health`, có thêm `SELECT 1` kiểm tra DB |
| GET | `/api/students?q=` | truy vấn tìm kiếm trong `index()` |
| GET | `/api/students/<id>` | truy vấn `editing` |
| POST | `/api/students` | nhánh INSERT của `save_student` |
| PUT | `/api/students/<id>` | nhánh UPDATE của `save_student` |
| DELETE | `/api/students/<id>` | `delete_student` |
| GET / POST | `/api/subjects` | danh sách môn / `save_subject` |
| GET / POST | `/api/grades` | bảng điểm (kèm `total`) / `save_grade` (upsert) |
| DELETE | `/api/grades/<id>` | `delete_grade` |
| GET / POST | `/api/tuition` | học phí (kèm `balance`) / `save_tuition` (upsert) |
| GET | `/api/stats` | các COUNT/SUM + `chart_data` (gradeLabels…tuitionBalance) |

Toàn bộ validation hiện có ([app.py:144](app.py#L144), [178-181](app.py#L178-L181), [192-198](app.py#L192-L198), [213-219](app.py#L213-L219)) chuyển nguyên sang back-end, giữ đúng thông báo tiếng Việt. Back-end chỉ nhận JSON nên không cần CSRF; mặc định bind `127.0.0.1` để trình duyệt/máy khác không gọi thẳng.

## Front-end (`frontend/`)
- `config`: `BACKEND_URL=http://127.0.0.1:5001`, `SECRET_KEY`, `FRONTEND_HOST=127.0.0.1`, `FRONTEND_PORT=5000`, `API_TOKEN`, `API_TIMEOUT=5`.
- `api_client.py`: `requests.Session`, các hàm `get(path, params)`, `post/put/delete(path, json)`; gắn `X-API-Key` nếu có; ném `ApiError(status, message)` lấy từ `{"error"}`; `ConnectionError`/`Timeout` → `ApiError(503, "Không kết nối được back-end tại …")`.
- `app.py`: giữ **nguyên tên endpoint** (`index`, `save_student`, `delete_student`, `save_subject`, `save_grade`, `save_tuition`, `delete_grade`, `health`) để các `url_for` trong template không đổi. Giữ cơ chế CSRF (`csrf_token`, `check_csrf`) và session cookie từ [app.py:9-11](app.py#L9-L11), [66-78](app.py#L66-L78). Mỗi route POST: đọc form → gọi API → `redirect(url_for("index", message=...|error=...))` như cũ. `save_student` chọn PUT khi có `id`, ngược lại POST.
- `index()`: gọi `/api/students?q=`, `/api/students/<edit>` (nếu có), `/api/subjects`, `/api/grades`, `/api/tuition`, `/api/stats` rồi render với **đúng các biến template cũ**. Nếu back-end lỗi → render trang với thông báo lỗi (HTTP 503) thay vì traceback.
- `/health` của front-end: trả trạng thái front-end + kết quả `/api/health`.
- `templates/index.html`: chỉ sửa chữ "SQLite · Docker" → "MySQL · Flask API" ở header ([index.html:376](templates/index.html#L376)) và footer ([index.html:743](templates/index.html#L743)). Jinja đọc `s.student_code` / `editing['id']` trên dict bình thường nên phần còn lại giữ nguyên.

## Script migrate (`backend/migrate_sqlite_to_mysql.py`)
`python migrate_sqlite_to_mysql.py [--sqlite ../data/students.db]`: mở SQLite ở chế độ read-only → gọi `init_database()` → copy theo thứ tự students → subjects → grades → tuition, **giữ nguyên id** (`INSERT IGNORE`, nên chạy lại không bị nhân đôi) trong một transaction → in số dòng đã chép/bỏ qua mỗi bảng. AUTO_INCREMENT tự điều chỉnh theo id lớn nhất.

## Docker (`compose.yaml` + Dockerfile mỗi app)
- `mysql`: `mysql:8.4`, `MYSQL_DATABASE=qlsv`, `MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-qlsv_root}`, volume `mysql_data`, healthcheck `mysqladmin ping`. **Không publish cổng 3306** để không đụng MySQL của Laragon.
- `backend`: build `./backend`, `DB_HOST=mysql`, `API_HOST=0.0.0.0`, `depends_on: mysql (service_healthy)`, không publish cổng.
- `frontend`: build `./frontend`, `BACKEND_URL=http://backend:5001`, `FRONTEND_HOST=0.0.0.0`, `ports: 127.0.0.1:5000:5000`.
- Dockerfile dựa trên `python:3.12-slim` như hiện tại, mỗi app copy đúng file của mình.

## README
Viết lại phần kiến trúc (sơ đồ Trình duyệt → Front-end :5000 → Back-end :5001 → MySQL), cách chạy với Laragon (bật MySQL bằng "Start All", tạo venv cho từng app, mở 2 terminal chạy `backend/app.py` và `frontend/app.py`, chạy migrate), bảng API, biến môi trường, cách chạy bằng Docker.

## Verification
1. Bật MySQL trong Laragon. Trong `backend/`: tạo venv, `pip install -r requirements.txt`, `python app.py` → log thấy đã tạo DB `qlsv`; `curl http://127.0.0.1:5001/api/health` → `{"status":"ok","database":"ok"}`.
2. `python migrate_sqlite_to_mysql.py` → báo 4/2/1/2 dòng; kiểm tra bằng `C:/laragon/bin/mysql/mysql-8.4.3-winx64/bin/mysql -u root qlsv -e "SELECT COUNT(*) FROM students"`. Chạy lại lần 2 → 0 dòng mới.
3. Trong `frontend/`: venv + `python app.py`, mở http://127.0.0.1:5000 → thấy dữ liệu đã migrate, KPI và 3 biểu đồ.
4. Thử trên giao diện: thêm/sửa (kể cả lưu mà không đổi gì → không bị 404)/xoá sinh viên (dữ liệu điểm/học phí bị xoá theo cascade), tìm kiếm, trùng mã SV → báo lỗi, thêm môn, lưu điểm 2 lần cùng SV/môn/kỳ → cập nhật thay vì nhân đôi, học phí đã đóng > phải đóng → báo lỗi, tên tiếng Việt có dấu hiển thị đúng.
5. Tắt back-end → front-end hiện thông báo "Không kết nối được back-end" (503), không ra traceback.
6. `docker compose up --build -d` (khi Laragon đang chạy vẫn không xung đột cổng) → http://localhost:5000 chạy được; `docker compose down`.
