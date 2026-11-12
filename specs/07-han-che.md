# 07 — Hạn chế đã biết và hướng cải tiến

Mục 1 ghi các hạn chế còn tồn tại, được ghi nhận khi đọc và chạy thử mã nguồn hiện tại. Mục 3 ghi các hạn chế đã khắc phục. Mã `L-xx` giữ cố định, không đánh số lại khi một hạn chế được khắc phục.

## 1. Hạn chế còn tồn tại
| # | Hạn chế | Ảnh hưởng | Vị trí |
|---|---|---|---|
| L-03 | Xếp loại tính trên **từng bản ghi điểm**, không phải điểm trung bình của sinh viên; không tính trọng số tín chỉ. | Biểu đồ "Phân loại kết quả học tập" đếm lượt điểm, không đếm sinh viên. | `backend/app.py` (`stats`) |
| L-04 | Kiểm tra email chỉ yêu cầu có ký tự `@`. | Có thể lưu email sai định dạng khi gọi API trực tiếp. | `backend/app.py` (`validate_student`) |
| L-07 | Không phân trang; trang chính tải toàn bộ sinh viên, điểm, học phí trong mỗi lần mở. | Chậm dần khi dữ liệu lớn (hàng nghìn bản ghi). | `frontend/app.py` |
| L-08 | Mỗi request mở kết nối MySQL mới, không dùng pool. | Đủ cho quy mô đồ án; tải cao sẽ tốn kết nối. | `backend/db.py` |
| L-09 | Không có migration lược đồ (`CREATE TABLE IF NOT EXISTS`). | Thêm / đổi cột không tự áp dụng cho DB đã tồn tại. | `backend/db.py` |
| L-10 | Không có đăng nhập / phân quyền. | Ai truy cập được trang đều có toàn quyền. | — |
| L-11 | Chart.js tải từ CDN. | Không có Internet thì không có biểu đồ (phần còn lại vẫn dùng được). | `index.html` |
| L-12 | Chưa có kiểm thử tự động. | Sửa mã cần kiểm tra thủ công. | — |
| L-13 | Sau một thao tác **thành công**, toàn bộ các vùng dữ liệu được thay bằng bản mới từ máy chủ. Mỗi lần vẫn tải lại toàn bộ HTML của trang chính: 5 lần gọi API (6 khi đang tìm kiếm), thêm 1 lần cho mỗi tham số sửa. | Form nhập dở ở mục khác không thể giữ lại song song: người dùng được hỏi trước (FR-27) và phải chọn lưu hoặc bỏ. Đang ở chế độ Sửa hoặc đang lọc tìm kiếm thì bị thoát, giống khi tải lại trang. Khi tắt JavaScript thì không có hộp thoại hỏi lưu và hộp xác nhận xóa. | `index.html` (script), `frontend/app.py` |
| L-14 | Phản hồi JSON của back-end có `Content-Type: application/json` **không kèm** `charset`. | Windows PowerShell 5.1 (`Invoke-RestMethod`) đọc phản hồi theo ISO-8859-1, nên tiếng Việt hiển thị sai (ví dụ `ÄÃ£ thÃªm`). Dữ liệu lưu trong DB vẫn đúng; trình duyệt và front-end (`requests`) đọc đúng. | `backend/app.py` |
| L-15 | Waitress luôn bật `SO_REUSEADDR`; trên Windows, tùy chọn này cho phép nhiều process cùng nghe một cổng. | Chạy `app.py` lần thứ hai (cửa sổ cũ chưa tắt) **không báo lỗi trùng cổng**. Request có thể tới bản cũ, khiến thay đổi mã như không có tác dụng. | `backend/app.py`, `frontend/app.py` (`serve`) |
| L-16 | Không có `.gitignore` ở thư mục gốc. `backend/.gitignore` và `frontend/.gitignore` chỉ bỏ qua `.env` trong thư mục của từng app. | File `.env` cạnh `compose.yaml` (chứa `MYSQL_ROOT_PASSWORD`, `API_TOKEN`, `SECRET_KEY` khi chạy Docker) có thể bị commit nhầm lên Git. | thư mục gốc |

## 2. Hướng cải tiến đề xuất
1. Kiểm tra email bằng biểu thức chính quy (L-04).
2. Thêm phân trang cho `/api/students`, `/api/grades`, `/api/tuition` (L-07).
3. Thêm đăng nhập cho front-end (Flask-Login hoặc session tự viết) trước khi đưa lên mạng (L-10).
4. Đóng gói Chart.js cùng ứng dụng để chạy offline (L-11).
5. Viết kiểm thử `pytest` cho các endpoint API với database thử nghiệm (L-12).
6. Đặt `app.json.mimetype = "application/json; charset=utf-8"` trong `backend/app.py` (L-14).
7. Trước khi gọi `serve()`, thử bind cổng với `SO_EXCLUSIVEADDRUSE` và dừng kèm thông báo rõ ràng nếu cổng đã bị dùng (L-15).
8. Thêm `.gitignore` ở thư mục gốc với dòng `/.env` (L-16).

## 3. Đã khắc phục
| # | Hạn chế cũ | Cách khắc phục | Commit |
|---|---|---|---|
| L-01 | Ô chọn sinh viên ở form **Bảng điểm** và **Học phí** lấy từ danh sách đã lọc theo ô tìm kiếm, nên đang tìm kiếm thì thiếu sinh viên để chọn. | Khi có từ khóa, `index()` gọi thêm `GET /api/students` (không lọc) cho hai ô chọn (`all_students`). Bảng sinh viên vẫn hiện kết quả tìm kiếm. | `42475f3` |
| L-02 | Màu biểu đồ vành khuyên gán theo vị trí, còn thứ tự nhãn do `GROUP BY` quyết định, nên cùng một xếp loại có thể đổi màu. | `/api/stats` luôn trả đủ 4 nhãn theo thứ tự cố định `GRADE_LABELS` (Giỏi → Khá → Trung bình → Cần cố gắng), nhãn không có bản ghi thì giá trị 0. Chưa có bản ghi điểm nào thì trả mảng rỗng. | `5f098a0`, `d1d4975` |
| L-05 | `due_date` chỉ giới hạn độ dài, không kiểm tra định dạng ngày. | Kiểm tra bằng `date.fromisoformat()` rồi lưu dạng chuẩn `YYYY-MM-DD` (ví dụ `20261231` → `2026-12-31`). Ngày sai như `2026-02-30` bị từ chối (400). | `3e77d27`, `d1d4975` |
| L-06 | `NaN` (và `inf` với học phí) lọt qua kiểm tra khoảng, gây lỗi 500. | Điều kiện viết dạng `0 <= x <= 10` (điểm) và `0 <= đã đóng <= phải đóng < 1e13` (học phí). So sánh với NaN luôn sai nên NaN bị loại; `inf` vượt giới hạn trên. Kết quả: trả 400. | `3e77d27` |
| — | Xếp loại tính từ điểm tổng kết **chưa làm tròn**, trong khi bảng điểm hiện số đã làm tròn 2 chữ số. Bản ghi ở sát ngưỡng có thể bị xếp loại lệch với số hiển thị. | Bảng điểm và thống kê dùng chung một biểu thức `TOTAL_EXPR` (có `ROUND(…, 2)`). | `ee56d8e` |
