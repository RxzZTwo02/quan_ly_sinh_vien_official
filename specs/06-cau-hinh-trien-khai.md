# 06 — Cấu hình và triển khai

## 1. Biến môi trường
Đọc từ biến môi trường hoặc file `.env` trong thư mục của từng app (`backend/.env`, `frontend/.env`). Mẫu: `*/.env.example`. Giá trị mặc định khớp MySQL của Laragon nên chạy trực tiếp **không cần** `.env`.

### Back-end
| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `DB_HOST` | `127.0.0.1` | Máy chủ MySQL |
| `DB_PORT` | `3306` | Cổng MySQL |
| `DB_USER` | `root` | Tài khoản MySQL |
| `DB_PASSWORD` | *(rỗng)* | Mật khẩu MySQL |
| `DB_NAME` | `qlsv` | Tên database (tự tạo) |
| `DB_CONNECT_RETRIES` | `1` | Số lần thử kết nối khi khởi động |
| `DB_CONNECT_DELAY` | `2` | Số giây giữa các lần thử |
| `API_HOST` | `127.0.0.1` | Địa chỉ lắng nghe |
| `API_PORT` | `5001` | Cổng lắng nghe |
| `API_TOKEN` | *(rỗng)* | Nếu đặt, bắt buộc header `X-API-Key` |

### Front-end
| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `BACKEND_URL` | `http://127.0.0.1:5001` | Địa chỉ back-end |
| `API_TOKEN` | *(rỗng)* | Phải trùng với back-end nếu có đặt |
| `API_TIMEOUT` | `5` | Timeout (giây) khi gọi back-end |
| `FRONTEND_HOST` | `127.0.0.1` | Địa chỉ lắng nghe |
| `FRONTEND_PORT` | `5000` | Cổng lắng nghe |
| `SECRET_KEY` | ngẫu nhiên mỗi lần chạy | Khóa ký session/CSRF; nên đặt cố định |

## 2. Chạy trực tiếp (Windows + Laragon)
1. Laragon → **Start All** (cần MySQL ở cổng 3306).
2. Back-end (terminal 1):
   ```powershell
   cd backend
   py -m venv .venv                                         # chỉ lần đầu
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt   # chỉ lần đầu
   .\.venv\Scripts\python.exe app.py
   ```
   Kiểm tra: `http://127.0.0.1:5001/api/health`.
3. (Tùy chọn, một lần) `.\.venv\Scripts\python.exe migrate_sqlite_to_mysql.py`.
4. Front-end (terminal 2): như bước 2 trong thư mục `frontend`, rồi mở `http://127.0.0.1:5000`.

**Thứ tự khởi động**: MySQL → back-end → front-end. Back-end dừng ngay khi không kết nối được MySQL (in hướng dẫn bật Laragon).

> Nếu `py -m venv .venv` báo *Unable to copy … venvlauncher.exe*: `.venv` đã tồn tại và `python.exe` bên trong đang bị VS Code dùng. Bỏ qua bước tạo venv, hoặc đóng VS Code rồi xóa `.venv` và tạo lại.

## 3. Chạy bằng Docker Compose
```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f backend frontend
docker compose down        # giữ dữ liệu
docker compose down -v     # xóa cả volume dữ liệu
```
| Service | Image | Ghi chú |
|---|---|---|
| `mysql` | `mysql:8.4` | `utf8mb4`; healthcheck `mysqladmin ping`; **không** mở cổng 3306 ra host (tránh xung đột Laragon); dữ liệu ở volume `mysql_data` |
| `backend` | `qlsv-backend:2.0` (build `./backend`) | Chờ `mysql` healthy; thử kết nối 30 lần; chỉ truy cập nội bộ |
| `frontend` | `qlsv-frontend:2.0` (build `./frontend`) | Mở `127.0.0.1:5000` trên host; gọi `http://backend:5001` |

Biến tùy chọn trong `.env` cạnh `compose.yaml`: `MYSQL_ROOT_PASSWORD` (mặc định `qlsv_root`), `SECRET_KEY`, `API_TOKEN`.

Dockerfile của cả hai app dựa trên `python:3.12-slim`, cài `requirements.txt`, chạy `python app.py` bằng Waitress.

## 4. Bảo mật
| Biện pháp | Vị trí |
|---|---|
| CSRF token cho mọi form POST | `frontend/app.py` |
| Cookie session `HttpOnly`, `SameSite=Lax` | `frontend/app.py` |
| SQL tham số hóa | `backend/app.py` |
| API key tùy chọn, so sánh thời gian hằng | `backend/app.py` |
| Jinja tự escape HTML (chống XSS) | `index.html` |
| Back-end và MySQL không mở ra ngoài khi chạy Docker; mặc định chỉ lắng nghe `127.0.0.1` | `compose.yaml`, `config.py` |

Hệ thống **không có đăng nhập**: ai truy cập được cổng 5000 đều có toàn quyền. Không mở cổng ra mạng ngoài nếu chưa bổ sung xác thực.

## 5. Kiểm tra sau khi chạy
| Kiểm tra | Kết quả mong đợi |
|---|---|
| `GET http://127.0.0.1:5001/api/health` | `{"status":"ok","database":"ok"}` |
| `GET http://127.0.0.1:5000/health` | `{"frontend":"ok","backend":{"status":"ok",...}}` |
| Mở `http://127.0.0.1:5000` | Thấy 4 thẻ KPI và 3 biểu đồ |
