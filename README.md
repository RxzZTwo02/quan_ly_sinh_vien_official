# Website quản lý sinh viên

Ứng dụng web một trang để quản lý **sinh viên, môn học, bảng điểm và học phí**, kèm dashboard thống kê. Hệ thống gồm hai ứng dụng Flask (giao diện và REST API) dùng chung một database MySQL. Có thể chạy trực tiếp với **Laragon** hoặc chạy bằng **Docker**.

Mã nguồn: https://github.com/RxzZTwo02/quan_ly_sinh_vien_official

## Mục lục
- [Tính năng](#tính-năng)
- [Kiến trúc và công nghệ](#kiến-trúc-và-công-nghệ)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Lấy mã nguồn về máy](#lấy-mã-nguồn-về-máy)
- [Chạy trực tiếp với Laragon](#chạy-trực-tiếp-với-laragon)
- [Chạy bằng Docker](#chạy-bằng-docker)
- [Dữ liệu mẫu (seed)](#dữ-liệu-mẫu-seed)
- [Biến môi trường](#biến-môi-trường)
- [REST API](#rest-api)
- [Xử lý sự cố](#xử-lý-sự-cố)
- [Tài liệu đặc tả](#tài-liệu-đặc-tả)

## Tính năng
| Mục | Thao tác | Ghi chú |
|---|---|---|
| Sinh viên | Thêm, sửa, xóa, tìm kiếm | Tìm theo mã, họ tên hoặc lớp. Tìm kiếm chỉ lọc bảng sinh viên; ô chọn sinh viên ở Bảng điểm và Học phí vẫn đủ danh sách. Xóa sinh viên thì xóa kèm điểm và học phí của sinh viên đó. |
| Môn học | Thêm, sửa, xóa | Xóa môn thì xóa kèm các bản ghi điểm của môn; hộp xác nhận báo trước số bản ghi sẽ mất. |
| Bảng điểm | Thêm, sửa, xóa | Điểm tổng kết tự tính: 10% chuyên cần + 30% giữa kỳ + 60% cuối kỳ, làm tròn 2 chữ số. Xếp loại Giỏi (≥ 8) / Khá (≥ 6,5) / Trung bình (≥ 5) / Cần cố gắng dựa trên đúng số đã làm tròn này. |
| Học phí | Thêm, sửa, xóa | Tự tính số còn nợ và trạng thái *Đã hoàn thành* / *Còn nợ*. Hạn đóng (tùy chọn) phải là ngày có thật. |
| Dashboard | Xem | 4 thẻ KPI (tổng sinh viên, môn học, bản ghi điểm, học phí còn nợ) và 3 biểu đồ (tình hình học phí, phân loại kết quả học tập, sinh viên theo lớp). Biểu đồ phân loại luôn đủ 4 xếp loại, mỗi xếp loại một màu cố định. |

**Cách thao tác**
- **Sửa**: bấm **Sửa** ở một dòng. Dữ liệu được đưa lên form, dòng đó được tô vàng và nút lưu đổi thành **Lưu thay đổi**. Bấm **Hủy** để thoát chế độ sửa.
- **Xóa**: luôn hỏi xác nhận trước khi xóa.
- **Thêm điểm / học phí đã có**: nếu bộ *(sinh viên, môn, học kỳ)* đã có điểm, hoặc *(sinh viên, học kỳ)* đã có học phí, thì bản ghi cũ được **cập nhật**.
- **Sửa thành bản ghi trùng**: khi **sửa** mà đổi sang bộ đã thuộc về một bản ghi khác, chương trình **báo trùng** và không ghi đè.
- **Không tải lại trang**: bảng, thẻ KPI và biểu đồ cập nhật tại chỗ, vị trí cuộn được giữ nguyên, thông báo nổi ở đầu màn hình. Nhập sai thì form giữ nguyên dữ liệu để sửa lại. Trình duyệt tắt JavaScript vẫn dùng được, khi đó trang tải lại như bình thường.
- **Không mất dữ liệu đang nhập dở**:
  - Bấm menu (Sinh viên, Môn học, Bảng điểm, Học phí) chỉ cuộn trang, dữ liệu đang gõ vẫn còn.
  - Đang nhập dở mà bấm Sửa / Hủy / Tất cả, tìm kiếm, xóa, lưu ở mục khác hay nhấn Back, chương trình hỏi trước:
    - **Lưu rồi tiếp tục**: chưa nhập đủ thì chỉ ra ô còn thiếu và không làm tiếp.
    - **Không lưu**: bỏ dữ liệu đang nhập và làm tiếp.
    - **Ở lại nhập tiếp**: quay về ô đang nhập.
  - F5 hoặc đóng tab khi đang nhập dở thì trình duyệt hỏi "Rời khỏi trang?".
- **Biểu đồ cần Internet**: Chart.js được tải từ CDN. Không có mạng thì chỉ biểu đồ không hiển thị, các phần khác vẫn dùng được.

## Kiến trúc và công nghệ
```
Trình duyệt ──HTTP──▶ Front-end Flask (:5000) ──REST/JSON──▶ Back-end Flask API (:5001) ──▶ MySQL (qlsv)
                      frontend/                               backend/                      Laragon hoặc Docker
```
- **frontend/**: giao diện (Jinja + Chart.js), form, CSRF. Không truy cập database. Mọi dữ liệu được lấy qua API của back-end, gọi từ phía server bằng `requests`, nên trình duyệt không gọi thẳng API.
- **backend/**: REST API JSON, kiểm tra dữ liệu, truy vấn MySQL bằng PyMySQL. Khi khởi động, back-end tự tạo database `qlsv` và các bảng. Nếu database còn rỗng, nó nạp [dữ liệu mẫu](#dữ-liệu-mẫu-seed).

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ, web server | Python 3.12+ · Flask 3.1 · Waitress |
| Cơ sở dữ liệu | MySQL 8 (Laragon khi chạy trực tiếp, image `mysql:8.4` khi chạy Docker) · PyMySQL |
| Biểu đồ | Chart.js 4.4.9 (tải từ CDN jsDelivr) |
| Đóng gói | Docker, Docker Compose |

## Cấu trúc thư mục
```
backend/                    REST API (cổng 5001)
  app.py                    route API, kiểm tra dữ liệu, xử lý lỗi
  db.py                     kết nối MySQL, transaction, tạo bảng và nạp dữ liệu mẫu
  config.py                 đọc biến môi trường / backend\.env
  sql/schema.sql            lược đồ 4 bảng: students, subjects, grades, tuition
  sql/seed.sql              dữ liệu mẫu
  requirements.txt · .env.example · Dockerfile
frontend/                   giao diện web (cổng 5000)
  app.py                    route giao diện, CSRF
  api_client.py             gọi back-end bằng requests
  templates/index.html      trang duy nhất: form, bảng, biểu đồ, script cập nhật tại chỗ
  requirements.txt · .env.example · Dockerfile
specs/                      tài liệu đặc tả hệ thống
compose.yaml                chạy mysql + backend + frontend bằng Docker
```

## Lấy mã nguồn về máy
Phần này dành cho việc cài dự án trên một máy khác. Sau khi clone, máy mới có **toàn bộ mã nguồn và toàn bộ lịch sử commit**, giống hệt repo trên GitHub.

### Phần mềm cần cài
| Phần mềm | Dùng để | Kiểm tra sau khi cài |
|---|---|---|
| [Git for Windows](https://git-scm.com/download/win) | Clone mã nguồn và lịch sử commit, cập nhật bản mới | `git --version` |
| [Python 3.12+](https://www.python.org/downloads/) | Chạy back-end và front-end | `py --version` |
| [Laragon](https://laragon.org/download/) | Cung cấp MySQL 8 khi chạy trực tiếp | Mở Laragon → **Start All** |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) *(tùy chọn)* | Chạy bằng Docker, thay cho Python + Laragon | `docker compose version` |

### Clone kèm đầy đủ lịch sử commit
Mở PowerShell tại thư mục muốn đặt dự án, rồi chạy:
```powershell
cd D:\                                                                  # thư mục chứa dự án, đổi tùy ý
git clone https://github.com/RxzZTwo02/quan_ly_sinh_vien_official.git    # tải mã nguồn + toàn bộ commit
cd quan_ly_sinh_vien_official                                           # thư mục gốc của dự án
```
- `git clone` không kèm tùy chọn nào sẽ tải **toàn bộ** lịch sử commit và checkout nhánh `main`. Thư mục `quan_ly_sinh_vien_official` vừa tạo là *thư mục gốc của dự án* được nhắc tới ở các phần sau.
- Clone bằng VS Code (**Ctrl+Shift+P** → *Git: Clone*, dán địa chỉ repo) cũng tải đầy đủ lịch sử.

Nếu cần đầy đủ commit thì **không** dùng các cách sau:

| Cách | Kết quả | Khắc phục |
|---|---|---|
| GitHub → **Code** → **Download ZIP** | Chỉ có file của commit mới nhất, **không có** thư mục `.git`. Không xem được lịch sử, không `git pull` được | Xóa thư mục đó và clone lại bằng lệnh trên |
| `git clone --depth 1 …` (shallow clone) | Chỉ có commit mới nhất | Chạy `git fetch --unshallow` trong thư mục dự án để tải phần lịch sử còn thiếu |

### Kiểm tra đã có đủ lịch sử
Chạy trong thư mục gốc của dự án:
```powershell
git rev-parse --is-shallow-repository   # false = có đầy đủ lịch sử
git rev-list --count HEAD               # tổng số commit, khớp số "commits" trên trang GitHub
git log --oneline                       # danh sách commit, mới nhất ở trên (nhấn q để thoát)
```

### Những gì không có trong repo
Các thứ sau không được đưa lên Git, nên máy mới phải tự tạo:

| Thứ | Vì sao không có | Trên máy mới |
|---|---|---|
| `backend\.venv`, `frontend\.venv` | Phụ thuộc từng máy, đã nằm trong `.gitignore` | Tạo lại ở [Bước 3](#bước-3--tạo-môi-trường-ảo-venv-và-cài-thư-viện-chỉ-làm-lần-đầu) |
| `backend\.env`, `frontend\.env` | Có thể chứa mật khẩu, đã nằm trong `.gitignore` | Không cần nếu dùng Laragon mặc định. Cần đổi thì sao chép từ `.env.example` (xem [Biến môi trường](#biến-môi-trường)) |
| Dữ liệu trong MySQL (database `qlsv`) | Dữ liệu nằm trong MySQL của từng máy, không nằm trong thư mục dự án | Back-end tự tạo database và nạp dữ liệu mẫu ở lần chạy đầu. Muốn mang dữ liệu từ máy cũ sang, xem [bên dưới](#mang-dữ-liệu-từ-máy-cũ-sang-tùy-chọn) |

### Cập nhật bản mới nhất
Khi repo trên GitHub có commit mới, chạy trong thư mục gốc của dự án:
```powershell
git pull        # tải các commit mới và cập nhật nhánh main
```
`git pull` in ra danh sách file thay đổi. Dựa vào đó:
- **`requirements.txt` thay đổi**: chạy lại lệnh `pip install -r requirements.txt` của app đó ([Bước 3](#bước-3--tạo-môi-trường-ảo-venv-và-cài-thư-viện-chỉ-làm-lần-đầu)).
- **`backend/sql/schema.sql` thay đổi**: database đã có không tự cập nhật theo, vì hệ thống không có migration. Hãy [quay về trạng thái gốc](#quay-về-trạng-thái-gốc), hoặc tự sửa bảng trong phpMyAdmin.
- **Luôn luôn**: dừng rồi chạy lại cả hai app. Với Docker, chạy `docker compose up --build -d`.

Dữ liệu đang có trong database không bị ảnh hưởng, vì dữ liệu mẫu chỉ nạp khi database rỗng.

Nếu đã sửa file trong máy và `git pull` báo *Your local changes … would be overwritten*:
1. `git stash` để cất tạm thay đổi;
2. `git pull`;
3. `git stash pop` để lấy lại thay đổi đã cất.

### Mang dữ liệu từ máy cũ sang (tùy chọn)
Clone chỉ chép mã nguồn. Muốn máy mới có đúng dữ liệu đang dùng ở máy cũ:
1. **Máy cũ — xuất dữ liệu**: phpMyAdmin → chọn database `qlsv` → tab **Export** → định dạng **SQL** → **Export**. Lưu file (ví dụ `qlsv.sql`) rồi chép sang máy mới.
2. **Máy mới — nhập dữ liệu, *trước* khi chạy back-end lần đầu**:
   1. phpMyAdmin → **New** → tạo database tên `qlsv`, collation `utf8mb4_unicode_ci`.
   2. Chọn `qlsv` → tab **Import** → chọn file `qlsv.sql` → **Import**.
3. **Chạy back-end** như bình thường. Database đã có dữ liệu nên back-end giữ nguyên và không nạp dữ liệu mẫu; log in ra `Dùng dữ liệu hiện có trong database 'qlsv' (… sinh viên)…`.

Nếu đã lỡ chạy back-end trên máy mới (database đã có dữ liệu mẫu), hãy xóa database `qlsv` trước. Cách xóa xem bước 1–2 của [Quay về trạng thái gốc](#quay-về-trạng-thái-gốc). Sau đó làm lại bước 2 ở trên.

## Chạy trực tiếp với Laragon
Cần đã [lấy mã nguồn về máy](#lấy-mã-nguồn-về-máy) và cài **Python 3.12+**, **Laragon** (có sẵn MySQL 8). Các lệnh dưới đây dùng **PowerShell** và chạy từ thư mục gốc của dự án (thư mục `quan_ly_sinh_vien_official` vừa clone, chứa `compose.yaml`).

### Bước 1 — Kiểm tra Python
```powershell
py --version    # phiên bản Python mặc định, cần 3.12 trở lên
py -0           # liệt kê các phiên bản Python đã cài
```
Nếu máy có nhiều phiên bản và muốn dùng đúng bản giống Docker, thay `py` bằng `py -3.12` ở bước tạo venv.

### Bước 2 — Bật MySQL
Mở **Laragon** → **Start All** (hoặc chỉ bật MySQL). Laragon mặc định dùng `root`, mật khẩu rỗng, cổng 3306. Ứng dụng dùng sẵn các giá trị này nên **không cần tạo file `.env`**.

Database `qlsv`, các bảng và dữ liệu mẫu do back-end tạo tự động. Nếu không muốn có dữ liệu mẫu, hãy đọc [Dữ liệu mẫu (seed)](#dữ-liệu-mẫu-seed) **trước** khi chạy back-end lần đầu.

### Bước 3 — Tạo môi trường ảo (venv) và cài thư viện (chỉ làm lần đầu)
Back-end và front-end dùng thư viện khác nhau, nên **mỗi app có một `.venv` riêng** nằm trong thư mục của app đó.

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

Kết quả là hai thư mục `backend\.venv` và `frontend\.venv`. Cả hai đã nằm trong `.gitignore` nên không bị đưa lên Git.

### Bước 4 — Chạy chương trình
Cần **hai cửa sổ terminal** chạy song song. Thứ tự khởi động: MySQL → back-end → front-end.

Terminal 1 — back-end:
```powershell
cd backend
.\.venv\Scripts\python.exe app.py
```
Lần chạy đầu, khi database `qlsv` còn rỗng, màn hình sẽ in ra:
```
Database 'qlsv' đang trống, đang nạp dữ liệu mẫu từ seed.sql...
Đã nạp dữ liệu mẫu: 10 sinh viên, 5 môn học, 18 bản ghi điểm, 10 bản ghi học phí. (Không muốn dữ liệu mẫu: đặt SEED_DATA=no, xem README.)
Back-end API: http://127.0.0.1:5001  (MySQL root@127.0.0.1:3306/qlsv)
```
Từ lần chạy sau, khi database đã có dữ liệu, dòng đầu đổi thành `Dùng dữ liệu hiện có trong database 'qlsv' (… sinh viên), không nạp dữ liệu mẫu.`

Nếu không kết nối được MySQL, back-end dừng ngay và in hướng dẫn bật Laragon.

Terminal 2 — front-end:
```powershell
cd frontend
.\.venv\Scripts\python.exe app.py
```
Nếu chạy được, màn hình in ra:
```
Front-end: http://127.0.0.1:5000  (back-end: http://127.0.0.1:5001)
```
Mở trình duyệt tại **http://127.0.0.1:5000**.

**Dừng chương trình**: nhấn **Ctrl+C** trong từng terminal.

**Sau khi sửa mã nguồn** (`.py`, `templates/index.html`): phải dừng rồi chạy lại app tương ứng, vì app không tự nạp lại thay đổi.

### Bước 5 — Kiểm tra
Mở terminal thứ ba trong khi hai app đang chạy:
```powershell
Invoke-RestMethod http://127.0.0.1:5001/api/health            # back-end  → status: ok, database: ok
Invoke-RestMethod http://127.0.0.1:5000/health                # front-end → frontend: ok, backend: {...}
(Invoke-RestMethod http://127.0.0.1:5001/api/students).Count  # số sinh viên (10 với dữ liệu mẫu)
```

**Xem dữ liệu JSON**: mở thẳng địa chỉ API trong trình duyệt, ví dụ http://127.0.0.1:5001/api/students hoặc http://127.0.0.1:5001/api/stats. Không nên in bằng `Invoke-RestMethod`, vì Windows PowerShell 5.1 hiển thị sai tiếng Việt (xem [Xử lý sự cố](#xử-lý-sự-cố)).

**Nếu đã đặt `API_TOKEN`**: trình duyệt không gửi được header, nên hãy dùng
```powershell
curl.exe -H "X-API-Key: <token>" http://127.0.0.1:5001/api/students
```

**Xem trực tiếp trong MySQL**: dùng HeidiSQL hoặc phpMyAdmin của Laragon, mở database `qlsv`.

### Mẹo: kích hoạt venv để gõ lệnh ngắn hơn
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

### Xóa và tạo lại venv
Dùng khi muốn cài lại từ đầu, ví dụ khi đổi phiên bản Python hoặc thư viện bị lỗi. Trước khi xóa, dừng hai app (Ctrl+C) và đóng các terminal đang kích hoạt venv:
```powershell
Remove-Item -Recurse -Force backend\.venv, frontend\.venv
```
Sau đó làm lại **Bước 3**.

## Chạy bằng Docker
Cần đã [lấy mã nguồn về máy](#lấy-mã-nguồn-về-máy) và cài **Docker Desktop** (đang chạy). Các lệnh chạy từ thư mục gốc của dự án; không cần cài Python hay Laragon.
```powershell
docker compose up --build -d             # build image và chạy nền
docker compose ps                        # trạng thái 3 service
docker compose logs -f backend frontend  # xem log
docker compose down                      # dừng, GIỮ dữ liệu
docker compose down -v                   # dừng và XÓA dữ liệu (volume mysql_data)
```
Mở **http://localhost:5000**.

- **3 service**: `mysql` (image `mysql:8.4`), `backend`, `frontend`.
- **Cổng**: chỉ front-end mở cổng ra máy host (`127.0.0.1:5000`). MySQL và back-end chỉ truy cập được bên trong Docker, nên không xung đột với MySQL 3306 của Laragon. Tuy vậy, đừng chạy cùng lúc với front-end chạy trực tiếp, vì cả hai đều dùng cổng 5000.
- **Dữ liệu**: database trong Docker là database riêng, không dùng chung với `qlsv` của Laragon. Dữ liệu nằm trong volume `mysql_data`. Lần đầu chạy, khi volume còn trống, back-end tự nạp dữ liệu mẫu.
- **Tùy chọn**: đặt trong file `.env` cạnh `compose.yaml`:
  - `MYSQL_ROOT_PASSWORD` (mặc định `qlsv_root`)
  - `SECRET_KEY`
  - `API_TOKEN`
  - `SEED_DATA` (mặc định `yes`)
- **Sau khi sửa mã nguồn hoặc `backend/sql/*.sql`**: luôn chạy lại với `--build`, vì các file này được chép vào image.

## Dữ liệu mẫu (seed)
Không cần lệnh riêng. Mỗi lần khởi động, back-end tạo các bảng nếu chưa có (`backend/sql/schema.sql`), rồi kiểm tra dữ liệu trong database:

| Tình trạng database | `SEED_DATA=yes` (mặc định) | `SEED_DATA=no` |
|---|---|---|
| **Rỗng**: chưa tồn tại, chưa có bảng, hoặc cả 4 bảng đều chưa có dòng nào | Nạp dữ liệu mẫu từ `backend/sql/seed.sql` | Để trống |
| **Đã có dữ liệu** (dù chỉ 1 dòng ở bất kỳ bảng nào) | Giữ nguyên, **không** đọc `seed.sql` | Giữ nguyên |

Dữ liệu mẫu gồm 10 sinh viên (`SV001`–`SV010`), 5 môn học, 18 bản ghi điểm và 10 bản ghi học phí.

Sau khi nạp, mọi thao tác thêm / sửa / xóa (trên giao diện, hay trong phpMyAdmin / HeidiSQL) chỉ lưu vào MySQL. Chúng **không** được ghi ngược vào file `.sql`, nên `seed.sql` luôn là bản gốc. Back-end đọc thẳng MySQL ở mỗi request, nên sửa dữ liệu trong phpMyAdmin xong chỉ cần tải lại trang.

### Không muốn dữ liệu mẫu
Làm **trước** khi chạy back-end lần đầu:
- **Chạy trực tiếp**: sao chép `backend\.env.example` thành `backend\.env`, rồi đặt `SEED_DATA=no`.
- **Docker**: đặt `SEED_DATA=no` trong file `.env` cạnh `compose.yaml`.

Nếu đã lỡ chạy, hãy [quay về trạng thái gốc](#quay-về-trạng-thái-gốc) với `SEED_DATA=no`.

> Với `SEED_DATA=yes`, nếu xóa hết dữ liệu (cả 4 bảng trống) rồi khởi động lại, dữ liệu mẫu sẽ được nạp lại. Muốn dùng database trống thì đặt `SEED_DATA=no`.

### Quay về trạng thái gốc
⚠️ **Mất toàn bộ dữ liệu đang có.** Muốn giữ lại thì vào phpMyAdmin, chọn `qlsv` → **Export** trước.

Trạng thái sau khi làm lại phụ thuộc vào `SEED_DATA`:

| Muốn về | `SEED_DATA` |
|---|---|
| Dữ liệu mẫu ban đầu | `yes` (hoặc không có file `.env`) |
| Database trống | `no` |

**Chạy trực tiếp (Laragon):**
1. Dừng back-end (Ctrl+C). Nếu không dừng, back-end vẫn chạy nhưng mọi request sẽ lỗi cho tới khi khởi động lại.
2. Xóa database `qlsv`. Trong phpMyAdmin: chọn `qlsv` → tab **Operations** → **Drop the database (DROP)**.

   Hoặc dùng lệnh dưới đây. MySQL của Laragon thường không nằm trong PATH; đổi `mysql-8.4.3-winx64` cho đúng phiên bản trên máy:
   ```powershell
   & "C:\laragon\bin\mysql\mysql-8.4.3-winx64\bin\mysql.exe" -uroot -e "DROP DATABASE qlsv"
   ```
3. Chạy lại back-end. Database và các bảng được tạo lại, có hoặc không có dữ liệu mẫu tùy theo `SEED_DATA`.

**Docker:** chạy `docker compose down -v` rồi `docker compose up --build -d`.

### Thử dữ liệu mẫu mà không xóa database cũ
1. Trong `backend\.env`, đặt `DB_NAME=qlsv_demo`.
2. Chạy lại back-end. Database `qlsv` cũ vẫn giữ nguyên.
3. Muốn quay về database cũ thì đổi lại `DB_NAME=qlsv`.

### Kiểm tra đã nạp dữ liệu mẫu
Một trong các cách sau:
- Log back-end có dòng `Đã nạp dữ liệu mẫu: …`.
- Mở http://127.0.0.1:5000 thấy 10 sinh viên và biểu đồ có số liệu.
- Chạy lệnh:
  ```powershell
  (Invoke-RestMethod http://127.0.0.1:5001/api/students).Count    # 10
  ```

### Sửa dữ liệu mẫu
Không import `seed.sql` thủ công vào database đã có dữ liệu, vì id trùng sẽ báo lỗi. Muốn đổi dữ liệu mẫu thì sửa `backend/sql/seed.sql`, rồi [quay về trạng thái gốc](#quay-về-trạng-thái-gốc).

File này chạy trong một transaction, nên:
- chỉ được chứa lệnh `INSERT`;
- phải chèn bảng cha (`students`, `subjects`) trước bảng con (`grades`, `tuition`);
- không được có `CREATE` / `ALTER` / `DROP`, hay `START TRANSACTION` / `COMMIT`.

Lưu ý điều này nếu thay bằng file xuất từ phpMyAdmin, vì file xuất mặc định có các lệnh đó.

## Biến môi trường
Không bắt buộc, vì giá trị mặc định đã khớp với MySQL của Laragon. Khi cần đổi:
1. Sao chép `backend\.env.example` thành `backend\.env`, và `frontend\.env.example` thành `frontend\.env`.
2. Sửa giá trị trong file `.env`.
3. Khởi động lại app để áp dụng.

| App | Biến | Mặc định | Ý nghĩa |
|---|---|---|---|
| backend | `DB_HOST` / `DB_PORT` | `127.0.0.1` / `3306` | Địa chỉ MySQL |
| backend | `DB_USER` / `DB_PASSWORD` | `root` / *(rỗng)* | Tài khoản MySQL |
| backend | `DB_NAME` | `qlsv` | Tên database (tự tạo nếu chưa có) |
| backend | `SEED_DATA` | `yes` | Database rỗng thì nạp dữ liệu mẫu; `no` để bắt đầu với database trống |
| backend | `DB_CONNECT_RETRIES` / `DB_CONNECT_DELAY` | `1` / `2` | Số lần thử kết nối MySQL khi khởi động / số giây giữa các lần (Docker đặt 30 lần) |
| backend | `API_HOST` / `API_PORT` | `127.0.0.1` / `5001` | Nơi API lắng nghe |
| cả hai | `API_TOKEN` | *(rỗng)* | Nếu đặt, mọi request API (trừ `/api/health`) phải có header `X-API-Key`; hai app phải đặt giống nhau |
| frontend | `BACKEND_URL` | `http://127.0.0.1:5001` | Địa chỉ back-end |
| frontend | `API_TIMEOUT` | `5` | Số giây chờ back-end trả lời |
| frontend | `FRONTEND_HOST` / `FRONTEND_PORT` | `127.0.0.1` / `5000` | Nơi giao diện lắng nghe |
| frontend | `SECRET_KEY` | ngẫu nhiên mỗi lần chạy | Nên đặt cố định để phiên làm việc không mất khi khởi động lại |

Biến dùng khi chạy Docker: xem [Chạy bằng Docker](#chạy-bằng-docker).

## REST API
Back-end chạy tại `http://127.0.0.1:5001`. Body gửi lên phải là JSON object.
- Thành công: trả về `{"message": "..."}`; khi thêm mới thì kèm `"id"`.
- Lỗi: trả về `{"error": "..."}`.

Chi tiết từng endpoint, body mẫu và thông báo lỗi: [specs/04-api.md](specs/04-api.md).

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/health` | Trạng thái API và kết nối DB (không cần API key) |
| GET · POST | `/api/students` | Danh sách sinh viên (`?q=` để tìm theo mã / họ tên / lớp) · thêm sinh viên |
| GET · PUT · DELETE | `/api/students/<id>` | Xem · sửa · xóa sinh viên (xóa kèm điểm, học phí) |
| GET · POST | `/api/subjects` | Danh sách · thêm môn học |
| GET · PUT · DELETE | `/api/subjects/<id>` | Xem · sửa · xóa môn học (xóa kèm điểm của môn) |
| GET · POST | `/api/grades` | Bảng điểm · lưu điểm (trùng sinh viên + môn + học kỳ thì cập nhật) |
| GET · PUT · DELETE | `/api/grades/<id>` | Xem · sửa · xóa bản ghi điểm |
| GET · POST | `/api/tuition` | Học phí · lưu học phí (trùng sinh viên + học kỳ thì cập nhật) |
| GET · PUT · DELETE | `/api/tuition/<id>` | Xem · sửa · xóa bản ghi học phí |
| GET | `/api/stats` | Số liệu cho thẻ KPI và biểu đồ |

| Mã lỗi | Khi nào |
|---|---|
| 400 | Dữ liệu thiếu hoặc không hợp lệ (gồm cả số `nan` / `inf`, hạn đóng không phải ngày `YYYY-MM-DD` có thật), body không phải JSON, sinh viên / môn học được chọn không tồn tại |
| 401 | Thiếu hoặc sai `X-API-Key` (khi có đặt `API_TOKEN`) |
| 404 | Không tìm thấy bản ghi |
| 409 | Trùng mã sinh viên / mã môn học; khi **sửa** điểm hoặc học phí, trùng với một bản ghi khác |
| 503 | Không kết nối được MySQL |

Front-end có thêm `GET /health` (http://127.0.0.1:5000/health), báo trạng thái của cả front-end và back-end.

## Xử lý sự cố
| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Back-end dừng ngay, báo `Không kết nối được MySQL tại 127.0.0.1:3306…` | MySQL chưa chạy, hoặc sai tài khoản | Laragon → **Start All**; kiểm tra các biến `DB_*` trong `backend\.env` |
| Back-end dừng, báo `SEED_DATA='…' không hợp lệ` | Giá trị khác `yes` / `no` | Sửa `SEED_DATA` trong `backend\.env` |
| Trang báo `Không kết nối được back-end tại http://127.0.0.1:5001…` | Back-end chưa chạy hoặc đã dừng | Chạy back-end ([Bước 4](#bước-4--chạy-chương-trình)) rồi tải lại trang |
| Trang báo `Không kết nối được cơ sở dữ liệu MySQL.` | MySQL bị tắt trong lúc back-end đang chạy | Bật lại MySQL trong Laragon rồi tải lại trang |
| Bấm lưu / xóa thì báo `Phiên làm việc hết hạn. Hãy tải lại trang.` | Front-end vừa khởi động lại mà chưa đặt `SECRET_KEY` | Tải lại trang (F5). Đặt `SECRET_KEY` cố định trong `frontend\.env` để không gặp lại |
| Báo `Thiếu hoặc sai API key.` | `API_TOKEN` ở hai app khác nhau | Đặt cùng một giá trị trong `backend\.env` và `frontend\.env`, rồi khởi động lại cả hai |
| Biểu đồ báo `Không tải được thư viện biểu đồ…` | Không có Internet (Chart.js tải từ CDN) | Kết nối mạng rồi tải lại trang. Các chức năng khác vẫn dùng được |
| Đã sửa code / template nhưng trang vẫn như cũ | App chưa được chạy lại; hoặc một bản cũ vẫn đang chạy ở cửa sổ khác. Trên Windows, chạy `app.py` lần thứ hai **không báo lỗi trùng cổng**: cả hai bản cùng nghe một cổng, nên request có thể vẫn tới bản cũ | Dừng app (Ctrl+C) rồi chạy lại. Kiểm tra còn bản nào đang chạy bằng `Get-NetTCPConnection -LocalPort 5000,5001 -State Listen`, rồi dừng bằng `Stop-Process -Id <OwningProcess>`. Docker thì chạy `docker compose up --build -d` |
| Tiếng Việt bị lỗi font (ví dụ `ÄÃ£ thÃªm`) khi in kết quả `Invoke-RestMethod` | Windows PowerShell 5.1 đọc sai bảng mã của phản hồi. Dữ liệu trong database vẫn đúng | Xem JSON bằng trình duyệt (mở thẳng địa chỉ API) |
| `py -m venv .venv` báo *Unable to copy … venvlauncher.exe* | `.venv` vẫn còn, và `python.exe` bên trong đang bị VS Code hoặc một terminal khác dùng | Đóng chương trình đó, xóa `.venv` rồi tạo lại |
| Kích hoạt venv thì PowerShell báo *running scripts is disabled on this system* | Chính sách chạy script của PowerShell | Chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi kích hoạt lại (chỉ áp dụng cho cửa sổ hiện tại) |

## Tài liệu đặc tả
Thư mục [specs/](specs/README.md) mô tả hệ thống đúng như mã nguồn hiện tại:
- yêu cầu chức năng và quy tắc nghiệp vụ;
- lược đồ cơ sở dữ liệu;
- đặc tả API;
- giao diện;
- cấu hình triển khai;
- hạn chế đã biết.
