# 07 — Hạn chế đã biết và hướng cải tiến

Các điểm dưới đây được ghi nhận khi đọc và chạy thử mã nguồn hiện tại; chưa sửa.

## 1. Hành vi cần lưu ý
| # | Hạn chế | Ảnh hưởng | Vị trí |
|---|---|---|---|
| L-01 | Ô chọn sinh viên ở form **Bảng điểm** và **Học phí** lấy từ danh sách đã lọc theo ô tìm kiếm. | Đang tìm kiếm thì chỉ chọn được sinh viên khớp từ khóa; muốn chọn sinh viên khác phải bấm "Tất cả". | `frontend/app.py` (`index`), `index.html` |
| L-02 | Màu biểu đồ vành khuyên gán theo **vị trí**, còn thứ tự nhãn do `GROUP BY` quyết định. | Cùng một xếp loại (ví dụ "Giỏi") có thể đổi màu giữa các lần tải. | `backend/app.py` (`stats`), `index.html` |
| L-03 | Xếp loại tính trên **từng bản ghi điểm**, không phải điểm trung bình của sinh viên; không tính trọng số tín chỉ. | Biểu đồ "Phân loại kết quả học tập" đếm lượt điểm, không đếm sinh viên. | `backend/app.py` (`stats`) |
| L-04 | Kiểm tra email chỉ yêu cầu có ký tự `@`. | Có thể lưu email sai định dạng khi gọi API trực tiếp. | `backend/app.py` (`validate_student`) |
| L-05 | `due_date` chỉ giới hạn độ dài, không kiểm tra định dạng ngày. | Gọi API trực tiếp có thể lưu chuỗi bất kỳ ≤ 10 ký tự. | `backend/app.py` (`validate_tuition`) |
| L-06 | Giá trị `NaN` lọt qua kiểm tra khoảng điểm / học phí, vì so sánh với NaN luôn sai. Với học phí, vô cực (`inf`) cũng lọt qua. PyMySQL sau đó từ chối các giá trị này bằng `ProgrammingError`, mà lỗi này không được bắt. | Gọi API với `"nan"` (hoặc `"inf"` cho học phí) bị lỗi 500 thay vì 400. Giao diện web không bị, vì dùng ô `type="number"`. | `backend/app.py` (`validate_grade`, `validate_tuition`) |
| L-07 | Không phân trang; trang chính tải toàn bộ sinh viên, điểm, học phí trong mỗi lần mở. | Chậm dần khi dữ liệu lớn (hàng nghìn bản ghi). | `frontend/app.py` |
| L-08 | Mỗi request mở kết nối MySQL mới, không dùng pool. | Đủ cho quy mô đồ án; tải cao sẽ tốn kết nối. | `backend/db.py` |
| L-09 | Không có migration lược đồ (`CREATE TABLE IF NOT EXISTS`). | Thêm / đổi cột không tự áp dụng cho DB đã tồn tại. | `backend/db.py` |
| L-10 | Không có đăng nhập / phân quyền. | Ai truy cập được trang đều có toàn quyền. | — |
| L-11 | Chart.js tải từ CDN. | Không có Internet thì không có biểu đồ (phần còn lại vẫn dùng được). | `index.html` |
| L-12 | Chưa có kiểm thử tự động. | Sửa mã cần kiểm tra thủ công. | — |
| L-13 | Sau một thao tác **thành công**, toàn bộ các vùng dữ liệu được thay bằng bản mới từ máy chủ. Mỗi lần vẫn tải lại toàn bộ HTML của trang chính: 5 lần gọi API, thêm 1 lần cho mỗi tham số sửa. | Form nhập dở ở mục khác không thể giữ lại song song: người dùng được hỏi trước (FR-27) và phải chọn lưu hoặc bỏ. Đang ở chế độ Sửa hoặc đang lọc tìm kiếm thì bị thoát, giống khi tải lại trang. Khi tắt JavaScript thì không có hộp thoại hỏi. | `index.html` (script), `frontend/app.py` |
| L-14 | Phản hồi JSON của back-end có `Content-Type: application/json` **không kèm** `charset`. | Windows PowerShell 5.1 (`Invoke-RestMethod`) đọc phản hồi theo ISO-8859-1, nên tiếng Việt hiển thị sai (ví dụ `ÄÃ£ thÃªm`). Dữ liệu lưu trong DB vẫn đúng; trình duyệt và front-end (`requests`) đọc đúng. | `backend/app.py` |
| L-15 | Waitress luôn bật `SO_REUSEADDR`; trên Windows, tùy chọn này cho phép nhiều process cùng nghe một cổng. | Chạy `app.py` lần thứ hai (cửa sổ cũ chưa tắt) **không báo lỗi trùng cổng**. Request có thể tới bản cũ, khiến thay đổi mã như không có tác dụng. | `backend/app.py`, `frontend/app.py` (`serve`) |
| L-16 | Không có `.gitignore` ở thư mục gốc. `backend/.gitignore` và `frontend/.gitignore` chỉ bỏ qua `.env` trong thư mục của từng app. | File `.env` cạnh `compose.yaml` (chứa `MYSQL_ROOT_PASSWORD`, `API_TOKEN`, `SECRET_KEY` khi chạy Docker) có thể bị commit nhầm lên Git. | thư mục gốc |

## 2. Hướng cải tiến đề xuất
1. Tách danh sách sinh viên cho ô chọn khỏi kết quả tìm kiếm (L-01).
2. Trả `gradeLabels` theo thứ tự cố định Giỏi → Khá → Trung bình → Cần cố gắng (L-02).
3. Kiểm tra email bằng biểu thức chính quy, `due_date` bằng `date.fromisoformat`, chặn NaN / vô cực bằng `math.isfinite` (L-04…L-06).
4. Thêm phân trang cho `/api/students`, `/api/grades`, `/api/tuition` (L-07).
5. Thêm đăng nhập cho front-end (Flask-Login hoặc session tự viết) trước khi đưa lên mạng (L-10).
6. Đóng gói Chart.js cùng ứng dụng để chạy offline (L-11).
7. Viết kiểm thử `pytest` cho các endpoint API với database thử nghiệm (L-12).
8. Đặt `app.json.mimetype = "application/json; charset=utf-8"` trong `backend/app.py` (L-14).
9. Trước khi gọi `serve()`, thử bind cổng với `SO_EXCLUSIVEADDRUSE` và dừng kèm thông báo rõ ràng nếu cổng đã bị dùng (L-15).
10. Thêm `.gitignore` ở thư mục gốc với dòng `/.env` (L-16).
