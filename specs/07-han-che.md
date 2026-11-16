# 07 — Hạn chế đã biết và hướng cải tiến

Mục 1 ghi các hạn chế còn tồn tại, được ghi nhận khi đọc và chạy thử mã nguồn hiện tại. Mục 3 ghi các hạn chế đã khắc phục. Mã `L-xx` giữ cố định, không đánh số lại khi một hạn chế được khắc phục. Mã `BUG-xx` là lỗi tìm thấy trong [báo cáo kiểm thử 16/11/2026](08-bao-cao-kiem-thu-2026-11-16.md).

## 1. Hạn chế còn tồn tại
| # | Hạn chế | Ảnh hưởng | Vị trí |
|---|---|---|---|
| L-03 | Xếp loại tính trên **từng bản ghi điểm**, không phải điểm trung bình của sinh viên; không tính trọng số tín chỉ. | Biểu đồ "Phân loại kết quả học tập" đếm lượt điểm, không đếm sinh viên. | `backend/app.py` (`stats`) |
| L-07 | Không phân trang; trang chính tải toàn bộ sinh viên, điểm, học phí trong mỗi lần mở. | Chậm dần khi dữ liệu lớn (hàng nghìn bản ghi). | `frontend/app.py` |
| L-08 | Mỗi request mở kết nối MySQL mới, không dùng pool. | Đủ cho quy mô đồ án; tải cao sẽ tốn kết nối. | `backend/db.py` |
| L-09 | Không có migration lược đồ (`CREATE TABLE IF NOT EXISTS`). | Thêm / đổi cột không tự áp dụng cho DB đã tồn tại. | `backend/db.py` |
| L-10 | Không có đăng nhập / phân quyền. | Ai truy cập được trang đều có toàn quyền. | — |
| L-11 | Chart.js tải từ CDN. | Không có Internet thì không có biểu đồ (phần còn lại vẫn dùng được). | `index.html` |
| L-12 | Chưa có kiểm thử tự động. | Sửa mã cần kiểm tra thủ công. | — |
| L-13 | Sau một thao tác **thành công**, toàn bộ các vùng dữ liệu được thay bằng bản mới từ máy chủ. Mỗi lần vẫn tải lại toàn bộ HTML của trang chính: 5 lần gọi API, thêm 1 lần cho mỗi bảng Sinh viên / Môn học / Bảng điểm đang tìm kiếm (lấy danh sách đầy đủ cho ô chọn và số liệu), và 1 lần cho mỗi tham số sửa. | Form nhập dở ở mục khác không thể giữ lại song song: người dùng được hỏi trước (FR-27) và phải chọn lưu hoặc bỏ. Đang ở chế độ Sửa thì bị thoát, giống khi tải lại trang (kết quả tìm kiếm thì được giữ, FR-32). Khi tắt JavaScript thì không có hộp thoại hỏi lưu và hộp xác nhận xóa. | `index.html` (script), `frontend/app.py` |
| L-16 | Không có `.gitignore` ở thư mục gốc. `backend/.gitignore` và `frontend/.gitignore` chỉ bỏ qua `.env` trong thư mục của từng app. | File `.env` cạnh `compose.yaml` (chứa `MYSQL_ROOT_PASSWORD`, `API_TOKEN`, `SECRET_KEY` khi chạy Docker) có thể bị commit nhầm lên Git. | thư mục gốc |
| L-17 | Chọn dòng để Sửa / Xóa dựa vào sự kiện chuột phải (`contextmenu`). Màn hình cảm ứng không có chuột phải: Android thường phát sự kiện này khi giữ lâu, còn Safari trên iPhone / iPad thì không. Chưa thử trên thiết bị thật. | Trên iPhone / iPad có thể không chọn được dòng, nên không Sửa / Xóa được từ giao diện (dù vẫn thêm mới được). | `index.html` (script) |

## 2. Hướng cải tiến đề xuất
1. Thêm phân trang cho `/api/students`, `/api/grades`, `/api/tuition` (L-07).
2. Thêm đăng nhập cho front-end (Flask-Login hoặc session tự viết) trước khi đưa lên mạng (L-10).
3. Đóng gói Chart.js cùng ứng dụng để chạy offline (L-11).
4. Viết kiểm thử `pytest` cho các endpoint API với database thử nghiệm (L-12).
5. Thêm `.gitignore` ở thư mục gốc với dòng `/.env` (L-16).
6. Trên màn hình cảm ứng, cho chọn dòng bằng cách giữ lâu (tự đo bằng sự kiện `touchstart` / `touchend`) hoặc chạm (L-17).

## 3. Đã khắc phục
| # | Hạn chế cũ | Cách khắc phục | Commit |
|---|---|---|---|
| L-01 | Ô chọn sinh viên ở form **Bảng điểm** và **Học phí** lấy từ danh sách đã lọc theo ô tìm kiếm, nên đang tìm kiếm thì thiếu sinh viên để chọn. | Khi có từ khóa, `index()` gọi thêm `GET /api/students` (không lọc) cho hai ô chọn (`all_students`). Bảng sinh viên vẫn hiện kết quả tìm kiếm. | `42475f3` |
| L-02 | Màu biểu đồ vành khuyên gán theo vị trí, còn thứ tự nhãn do `GROUP BY` quyết định, nên cùng một xếp loại có thể đổi màu. | `/api/stats` luôn trả đủ 4 nhãn theo thứ tự cố định `GRADE_LABELS` (Giỏi → Khá → Trung bình → Cần cố gắng), nhãn không có bản ghi thì giá trị 0. Chưa có bản ghi điểm nào thì trả mảng rỗng. | `5f098a0`, `d1d4975` |
| L-04, BUG-02 | Kiểm tra email chỉ yêu cầu có ký tự `@`, nên gửi thẳng tới API thì lưu được cả `@`, `a@`, `qa mail @ x y`. Mở bản ghi đó ra sửa thì trình duyệt chặn nút Lưu thay đổi. | `validate_student()` dùng `EMAIL_RE` (`<tên>@<miền>.<đuôi>`, không khoảng trắng, một dấu `@`), báo "Email không đúng định dạng (ví dụ an@example.com)". Ô Email có thêm `pattern` giống vậy. | `13b4461` |
| L-05 | `due_date` chỉ giới hạn độ dài, không kiểm tra định dạng ngày. | Kiểm tra bằng `date.fromisoformat()` rồi lưu dạng chuẩn `YYYY-MM-DD` (ví dụ `20261231` → `2026-12-31`). Ngày sai như `2026-02-30` bị từ chối (400). | `3e77d27`, `d1d4975` |
| L-06 | `NaN` (và `inf` với học phí) lọt qua kiểm tra khoảng, gây lỗi 500. | Điều kiện viết dạng `0 <= x <= 10` (điểm) và `0 <= đã đóng <= phải đóng < 1e13` (học phí). So sánh với NaN luôn sai nên NaN bị loại; `inf` vượt giới hạn trên. Kết quả: trả 400. | `3e77d27` |
| L-14 | Phản hồi JSON của back-end có `Content-Type: application/json` **không kèm** `charset`, nên Windows PowerShell 5.1 (`Invoke-RestMethod`) đọc theo ISO-8859-1 và hiển thị sai tiếng Việt (ví dụ `ÄÃ£ thÃªm`). | Đặt `app.json.mimetype = "application/json; charset=utf-8"` trong `backend/app.py`. Mọi phản hồi JSON, kể cả lỗi 4xx / 5xx, đều kèm `charset=utf-8`; `Invoke-RestMethod` đọc đúng tiếng Việt. | `f808faf` |
| L-15 | Waitress luôn bật `SO_REUSEADDR`; trên Windows, chạy `app.py` lần thứ hai (cửa sổ cũ chưa tắt) **không báo lỗi trùng cổng**, hai bản cùng nghe một cổng. Request có thể tới bản cũ (sửa mã như không có tác dụng), hoặc tới bản đang trỏ tới **database khác**, khiến dữ liệu bị ghi nhầm database (đã xảy ra khi chạy thử). | Trước `serve()`, `ensure_port_free()` thử bind cổng với `SO_EXCLUSIVEADDRUSE`; cổng đã có process khác nghe thì dừng, báo `Cổng … đang được dùng…`. Back-end kiểm tra **trước** `init_database()` nên bản chạy trùng không đụng tới database. Chỉ kiểm tra trên Windows (Linux / Docker tự báo lỗi trùng cổng). Vừa tắt app, cổng còn kết nối `TIME_WAIT` thì vẫn chạy lại được ngay. | `5726f74` |
| BUG-01 | Mã SV (và mã môn) chỉ bị kiểm tra độ dài, nên lưu được `-1`, `QA 013`, `QA/014`, `QA%015`, `QA<SCRIPT>`… | Sau khi chuyển in hoa, mã phải khớp `[A-Z0-9]+` (`CODE_RE`, BR-02, BR-05); ô nhập có `pattern` tương ứng. | `727668d` |
| BUG-03 | `%`, `_` trong từ khóa tìm kiếm là ký tự đại diện của `LIKE`: tìm `%` hay `_` ra cả danh sách, tìm `QA_0` ra cả `QA%015`. | `keyword_filter()` thoát `! % _` bằng `!` và dùng `LIKE … ESCAPE '!'`; `list_students()` dùng chung hàm này, nên cả 4 bảng tìm như nhau (FR-02). | `8477656` |
| BUG-04 | Trên Windows, chạy app với đầu ra chuyển ra file / pipe thì `print` tiếng Việt gây `UnicodeEncodeError`, back-end dừng ngay. | Đầu `backend/app.py` và `frontend/app.py` đặt `stdout` / `stderr` sang UTF-8 trước khi import `config` ([06](06-cau-hinh-trien-khai.md) mục 2). | `5698654` |
| BUG-05 | Trang chính hiện nội dung bất kỳ của `?error=` / `?message=` thành thông báo, nên có thể gửi link chứa thông báo giả (content spoofing). | Thông báo đi qua session (`flash`) và hiện một lần; trang chính không đọc thông báo từ URL ([05](05-giao-dien.md) mục 1). | `29135bb` |
| BUG-06 | Họ tên và lớp không bị kiểm tra ký tự (lưu được `12345 !@#$%`, có xuống dòng). | `NAME_RE` / `CLASS_RE` theo BR-20, chuẩn hóa NFC trước khi kiểm tra; ô nhập có `pattern` dùng `\p{L}`. | `b425a50` |
| BUG-07 | Mọi ô bảng `nowrap`: chuỗi dài không có khoảng trắng kéo bảng rộng gấp đôi khung. | Cột chữ tự do có class `wrap` (`overflow-wrap: anywhere`); đo bằng Edge headless với họ tên 100 ký tự: 2267px → 1155px (vừa khung). | `90cfb34` |
| BUG-08 | Nhập sai chỉ báo chung "Vui lòng nhập đủ thông tin hợp lệ."; trùng mã báo "… đã tồn tại **hoặc** dữ liệu không hợp lệ.". | Liệt kê từng ô sai và lý do trong một câu (BR-19); chỉ khi trùng khóa UNIQUE mới báo "Mã … đã tồn tại." (409). Áp dụng cho Sinh viên và Môn học. | `96d35e4` |
| BUG-09 | Request bị sửa tay (`id=abc`, `POST /delete/-1`) hiện trang lỗi tiếng Anh của Flask. | Trang lỗi tiếng Việt cho mọi `HTTPException` của front-end; `id` sai báo "Mã bản ghi không hợp lệ." ([05](05-giao-dien.md) mục 1). | `282e24e` |
| — | Xếp loại tính từ điểm tổng kết **chưa làm tròn**, trong khi bảng điểm hiện số đã làm tròn 2 chữ số. Bản ghi ở sát ngưỡng có thể bị xếp loại lệch với số hiển thị. | Bảng điểm và thống kê dùng chung một biểu thức `TOTAL_EXPR` (có `ROUND(…, 2)`). | `ee56d8e` |
