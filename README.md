# Website quản lý sinh viên — kiến trúc front-end / back-end + MySQL

## Kiến trúc
```
Trình duyệt ──HTTP──▶ Front-end Flask (:5000) ──REST/JSON──▶ Back-end Flask API (:5001) ──▶ MySQL (qlsv)
                      frontend/                               backend/                      Laragon hoặc Docker
```
- **frontend/**: giao diện (Jinja + Chart.js), form, CSRF. Không truy cập DB; mọi dữ liệu lấy qua API của back-end (gọi phía server bằng `requests`, nên trình duyệt không gọi thẳng API).
- **backend/**: REST API JSON, kiểm tra dữ liệu, truy vấn MySQL bằng PyMySQL. Tự tạo database `qlsv`, các bảng (`backend/sql/schema.sql`) và nạp dữ liệu mẫu (`backend/sql/seed.sql`) khi database còn rỗng (tắt bằng `SEED_DATA=no`).

## Công nghệ
- Python 3.12+ · Flask · Waitress
- MySQL 8 (Laragon khi chạy trực tiếp, image `mysql:8.4` khi chạy Docker) · PyMySQL
- Chart.js (tải từ CDN) cho biểu đồ

## Chạy trực tiếp với Laragon (không cần Docker)
Các lệnh dưới đây dùng **PowerShell** trên Windows và chạy từ thư mục gốc của dự án (thư mục chứa `compose.yaml`).

### Bước 0 — Kiểm tra Python
```powershell
py --version    # phiên bản Python mặc định, cần 3.12 trở lên
py -0           # liệt kê các phiên bản Python đã cài
```
Nếu máy có nhiều phiên bản và muốn dùng đúng bản giống Docker, thay `py` bằng `py -3.12` ở bước tạo venv.

### Bước 1 — Bật MySQL
Mở **Laragon** → **Start All** (hoặc chỉ bật MySQL). Mặc định Laragon dùng `root` / mật khẩu rỗng / cổng 3306; ứng dụng dùng sẵn các giá trị này nên **không cần tạo file `.env`**. Database `qlsv`, các bảng và dữ liệu mẫu được back-end tạo tự động; không muốn dữ liệu mẫu thì xem [Dữ liệu mẫu (seed)](#dữ-liệu-mẫu-seed) **trước** khi chạy back-end lần đầu.

### Bước 2 — Tạo môi trường ảo (venv) và cài thư viện (chỉ làm lần đầu)
Back-end và front-end dùng thư viện khác nhau nên **mỗi app có một `.venv` riêng** nằm trong thư mục của app đó.

Back-end:
```powershell
cd backend
py -m venv .venv                                                 # tạo backend\.venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip          # (tùy chọn) nâng cấp pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt    # Flask, waitress, PyMySQL, cryptography, python-dotenv
.\.venv\Scripts\python.exe -m pip list                           # kiểm tra các gói đã cài
cd ..
```

Front-end:
```powershell
cd frontend
py -m venv .venv                                                 # tạo frontend\.venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt    # Flask, waitress, requests, python-dotenv
.\.venv\Scripts\python.exe -m pip list
cd ..
```

Kết quả: hai thư mục `backend\.venv` và `frontend\.venv`, cả hai đã nằm trong `.gitignore` nên không bị đưa lên Git.

### Bước 3 — Chạy chương trình
Cần **hai cửa sổ terminal** chạy song song. Thứ tự: MySQL → back-end → front-end.

Terminal 1 — back-end:
```powershell
cd backend
.\.venv\Scripts\python.exe app.py
```
Nếu chạy được sẽ in ra (lần chạy đầu, khi database `qlsv` còn rỗng):
```
Database 'qlsv' đang trống, đang nạp dữ liệu mẫu từ seed.sql...
Đã nạp dữ liệu mẫu: 10 sinh viên, 5 môn học, 18 bản ghi điểm, 10 bản ghi học phí. (Không muốn dữ liệu mẫu: đặt SEED_DATA=no, xem README.)
Back-end API: http://127.0.0.1:5001  (MySQL root@127.0.0.1:3306/qlsv)
```
Các lần chạy sau, khi database đã có dữ liệu, dòng đầu đổi thành `Dùng dữ liệu hiện có trong database 'qlsv' (… sinh viên), không nạp dữ liệu mẫu.`
Nếu không kết nối được MySQL, back-end dừng ngay và in hướng dẫn bật Laragon.

Terminal 2 — front-end:
```powershell
cd frontend
.\.venv\Scripts\python.exe app.py
```
Nếu chạy được sẽ in ra:
```
Front-end: http://127.0.0.1:5000  (back-end: http://127.0.0.1:5001)
```
Mở trình duyệt tại http://127.0.0.1:5000. Nhấn **Ctrl+C** trong từng terminal để dừng.

### Bước 4 — Kiểm tra bằng dòng lệnh
Mở terminal thứ ba trong khi hai app đang chạy:
```powershell
Invoke-RestMethod http://127.0.0.1:5001/api/health    # back-end  → status: ok, database: ok
Invoke-RestMethod http://127.0.0.1:5000/health        # front-end → frontend: ok, backend: {...}
Invoke-RestMethod http://127.0.0.1:5001/api/students  # danh sách sinh viên (JSON)
Invoke-RestMethod http://127.0.0.1:5001/api/stats     # số liệu cho dashboard
```
Có thể dùng `curl.exe` thay cho `Invoke-RestMethod`, ví dụ `curl.exe http://127.0.0.1:5001/api/health`. Nếu đã đặt `API_TOKEN`, thêm header: `curl.exe -H "X-API-Key: <token>" http://127.0.0.1:5001/api/students`.

Xem dữ liệu trực tiếp: dùng HeidiSQL/phpMyAdmin của Laragon, mở database `qlsv`.

### Dữ liệu mẫu (seed)
Không cần lệnh riêng. Mỗi lần khởi động, back-end tạo các bảng nếu chưa có (`backend/sql/schema.sql`) rồi kiểm tra dữ liệu trong database `qlsv`:

| Tình trạng database | `SEED_DATA=yes` (mặc định) | `SEED_DATA=no` |
|---|---|---|
| **Rỗng**: chưa tồn tại, chưa có bảng, hoặc cả 4 bảng đều chưa có dòng nào | Nạp dữ liệu mẫu từ `backend/sql/seed.sql` | Để trống |
| **Đã có dữ liệu** (dù chỉ 1 dòng ở bất kỳ bảng nào) | Giữ nguyên, **không** đọc `seed.sql` | Giữ nguyên |

Dữ liệu mẫu gồm 10 sinh viên (`SV001`–`SV010`), 5 môn học, 18 bản ghi điểm, 10 bản ghi học phí. Sau khi nạp, mọi thao tác thêm / sửa / xóa (trên giao diện hay trong phpMyAdmin / HeidiSQL) chỉ lưu vào MySQL, **không** ghi ngược vào file `.sql`, nên `seed.sql` luôn là bản gốc. Back-end đọc thẳng MySQL ở mỗi request: sửa dữ liệu trong phpMyAdmin xong chỉ cần tải lại trang.

**Không muốn dữ liệu mẫu** — làm một lần, **trước** khi chạy back-end lần đầu: sao chép `backend\.env.example` → `backend\.env` và đặt `SEED_DATA=no`. Nếu lỡ chạy rồi thì làm thêm bước "quay về database trống" bên dưới.

> Với `SEED_DATA=yes`, nếu xóa hết dữ liệu (cả 4 bảng trống) rồi khởi động lại, dữ liệu mẫu sẽ được nạp lại. Muốn dùng database trống thì đặt `SEED_DATA=no`.

**Quay về trạng thái gốc** (⚠️ mất toàn bộ dữ liệu đang có trong `qlsv`; muốn giữ thì vào phpMyAdmin chọn `qlsv` → **Export** trước):

| Muốn về | Đặt trong `backend\.env` |
|---|---|
| Dữ liệu mẫu ban đầu | `SEED_DATA=yes` (hoặc không có file `.env`) |
| Database trống | `SEED_DATA=no` |

1. Dừng back-end (Ctrl+C). Nếu không dừng, back-end vẫn chạy nhưng mọi request sẽ lỗi cho tới khi khởi động lại.
2. Xóa database `qlsv`: trong phpMyAdmin chọn `qlsv` → tab **Operations** → **Drop the database (DROP)**. Hoặc dùng lệnh (MySQL của Laragon thường không nằm trong PATH; đổi `mysql-8.4.3-winx64` cho đúng phiên bản trên máy):
   ```powershell
   & "C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" -uroot -e "DROP DATABASE qlsv"
   ```
3. Chạy lại back-end: database và các bảng được tạo lại, có hoặc không có dữ liệu mẫu theo `SEED_DATA`.

**Giữ database cũ, thử dữ liệu mẫu ở database khác:** trong `backend\.env` đặt `DB_NAME=qlsv_demo` rồi chạy lại back-end. `qlsv` cũ giữ nguyên; đổi lại `DB_NAME=qlsv` để quay về.

**Kiểm tra đã nạp dữ liệu mẫu:** mở http://127.0.0.1:5000 thấy 10 sinh viên và biểu đồ có số liệu, hoặc:
```powershell
(Invoke-RestMethod http://127.0.0.1:5001/api/students).Count    # 10
```

> Không import `seed.sql` thủ công vào database đã có dữ liệu: id trùng sẽ báo lỗi. Muốn đổi dữ liệu mẫu thì sửa `backend/sql/seed.sql` rồi quay về trạng thái gốc như trên. File này chạy trong một transaction nên chỉ được chứa lệnh `INSERT` (bảng cha `students`, `subjects` trước bảng con), không có `CREATE` / `ALTER` / `DROP` hay `START TRANSACTION` / `COMMIT`. Lưu ý điều này nếu thay bằng file xuất từ phpMyAdmin, vì file xuất mặc định có các lệnh đó.

### Cách khác: kích hoạt venv rồi gọi `python`
Thay vì gõ `.\.venv\Scripts\python.exe` mỗi lần, có thể kích hoạt venv để dùng lệnh `python` / `pip` ngắn gọn:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1     # đầu dòng lệnh hiện (.venv)
python app.py
deactivate                       # thoát venv khi xong
```
| Shell | Lệnh kích hoạt |
|---|---|
| PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Command Prompt (cmd) | `.venv\Scripts\activate.bat` |
| Git Bash | `source .venv/Scripts/activate` |

Nếu PowerShell báo *running scripts is disabled on this system*, cho phép chạy script trong cửa sổ hiện tại rồi kích hoạt lại:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Xóa và tạo lại venv
Dùng khi muốn cài lại từ đầu (ví dụ đổi phiên bản Python hoặc thư viện bị lỗi). Trước khi xóa, dừng hai app (Ctrl+C) và đóng các terminal đang kích hoạt venv:
```powershell
Remove-Item -Recurse -Force backend\.venv, frontend\.venv
```
Sau đó làm lại **Bước 2**.

> Nếu `py -m venv .venv` báo *Unable to copy … venvlauncher.exe*: `.venv` vẫn còn và `python.exe` bên trong đang bị VS Code hoặc một terminal khác dùng. Đóng chương trình đó rồi xóa `.venv` và tạo lại.

## Biến môi trường
Sao chép `backend/.env.example` → `backend/.env`, `frontend/.env.example` → `frontend/.env` nếu cần đổi.

| App | Biến | Mặc định | Ý nghĩa |
|---|---|---|---|
| backend | `DB_HOST` / `DB_PORT` | `127.0.0.1` / `3306` | địa chỉ MySQL |
| backend | `DB_USER` / `DB_PASSWORD` | `root` / *(rỗng)* | tài khoản MySQL |
| backend | `DB_NAME` | `qlsv` | tên database (tự tạo nếu chưa có) |
| backend | `SEED_DATA` | `yes` | database rỗng thì nạp dữ liệu mẫu; `no` để bắt đầu với database trống |
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
| GET · PUT · DELETE | `/api/subjects/<id>` | xem / sửa / xóa môn học (xóa kèm điểm của môn đó) |
| GET · POST | `/api/grades` | bảng điểm / lưu điểm (trùng SV + môn + học kỳ thì cập nhật) |
| GET · PUT · DELETE | `/api/grades/<id>` | xem / sửa / xóa bản ghi điểm |
| GET · POST | `/api/tuition` | học phí / lưu học phí (trùng SV + học kỳ thì cập nhật) |
| GET · PUT · DELETE | `/api/tuition/<id>` | xem / sửa / xóa bản ghi học phí |
| GET | `/api/stats` | số liệu KPI và dữ liệu biểu đồ |

Lỗi trả về dạng `{"error": "..."}` với mã 400/404/409/503; thành công kèm `{"message": "..."}`.

## Chạy bằng Docker
```powershell
docker compose up --build -d
docker compose ps
docker compose logs -f backend frontend
```
Truy cập http://localhost:5000. Gồm 3 service: `mysql`, `backend`, `frontend`. MySQL trong Docker **không mở cổng 3306** ra máy host nên chạy song song với Laragon không bị xung đột. Dữ liệu nằm trong volume `mysql_data` (`docker compose down` không xóa volume; `docker compose down -v` thì có).

Dữ liệu mẫu: lần đầu chạy (volume còn trống) back-end tự nạp như khi chạy trực tiếp; không muốn thì đặt `SEED_DATA=no` trong file `.env` cạnh `compose.yaml` trước lần chạy đầu. Đây là database riêng trong Docker, không dùng chung với `qlsv` của Laragon. Muốn quay về trạng thái gốc (⚠️ mất dữ liệu trong Docker): `docker compose down -v` rồi `docker compose up --build -d`. Luôn dùng `--build` sau khi sửa `backend/sql/*.sql` vì các file này được chép vào image.

Có thể đặt `MYSQL_ROOT_PASSWORD`, `SECRET_KEY`, `API_TOKEN`, `SEED_DATA` trong file `.env` cạnh `compose.yaml`.

## Dashboard
- Thẻ KPI: tổng sinh viên, môn học, bản ghi điểm, học phí còn nợ.
- Biểu đồ học phí phải đóng / đã đóng / còn nợ, phân loại kết quả học tập, số sinh viên theo lớp — dữ liệu truy vấn trực tiếp từ MySQL.
- Chart.js tải từ CDN nên trình duyệt cần Internet để hiển thị biểu đồ.
- Thêm / sửa / xóa / tìm kiếm **không tải lại trang**: bảng, thẻ KPI và biểu đồ cập nhật tại chỗ, vị trí cuộn giữ nguyên; thông báo nổi ở đầu màn hình. Nhập sai thì form giữ nguyên dữ liệu để sửa lại. Trình duyệt tắt JavaScript vẫn dùng được (tải lại trang như cũ).
