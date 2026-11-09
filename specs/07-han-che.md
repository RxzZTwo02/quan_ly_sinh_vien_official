# 07 — Hạn chế đã biết và hướng cải tiến

Các điểm dưới đây được ghi nhận khi đọc mã nguồn hiện tại; chưa sửa.

## 1. Hành vi cần lưu ý
| # | Hạn chế | Ảnh hưởng | Vị trí |
|---|---|---|---|
| L-01 | Ô chọn sinh viên ở form **Bảng điểm** và **Học phí** lấy từ danh sách đã lọc theo ô tìm kiếm. | Đang tìm kiếm thì chỉ chọn được sinh viên khớp từ khóa; muốn chọn sinh viên khác phải bấm "Tất cả". | `frontend/app.py` (`index`), `index.html` |
| L-02 | Màu biểu đồ vành khuyên gán theo **vị trí**, còn thứ tự nhãn do `GROUP BY` quyết định. | Cùng một xếp loại (ví dụ "Giỏi") có thể đổi màu giữa các lần tải. | `backend/app.py` (`stats`), `index.html` |
| L-03 | Xếp loại tính trên **từng bản ghi điểm**, không phải điểm trung bình của sinh viên; không tính trọng số tín chỉ. | Biểu đồ "Phân loại kết quả học tập" đếm lượt điểm, không đếm sinh viên. | `backend/app.py` (`stats`) |
| L-04 | Kiểm tra email chỉ yêu cầu có ký tự `@`. | Có thể lưu email sai định dạng khi gọi API trực tiếp. | `backend/app.py` (`validate_student`) |
| L-05 | `due_date` chỉ giới hạn độ dài, không kiểm tra định dạng ngày. | Gọi API trực tiếp có thể lưu chuỗi bất kỳ ≤ 10 ký tự. | `backend/app.py` (`save_tuition`) |
| L-06 | Giá trị `NaN` lọt qua kiểm tra khoảng điểm/học phí (so sánh với NaN luôn sai). | Gọi API với `"nan"` gây lỗi 500 thay vì 400. Giao diện web không bị vì ô `type="number"`. | `backend/app.py` |
| L-07 | Không có sửa/xóa môn học, không có xóa học phí trên giao diện lẫn API. | Nhập sai phải sửa trực tiếp trong DB (HeidiSQL/phpMyAdmin). | — |
| L-08 | Không phân trang; trang chính tải toàn bộ sinh viên, điểm, học phí trong mỗi lần mở. | Chậm dần khi dữ liệu lớn (hàng nghìn bản ghi). | `frontend/app.py` |
| L-09 | Mỗi request mở kết nối MySQL mới, không dùng pool. | Đủ cho quy mô đồ án; tải cao sẽ tốn kết nối. | `backend/db.py` |
| L-10 | Không có migration lược đồ (`CREATE TABLE IF NOT EXISTS`). | Thêm/đổi cột không tự áp dụng cho DB đã tồn tại. | `backend/db.py` |
| L-11 | Không có đăng nhập / phân quyền. | Ai truy cập được trang đều có toàn quyền. | — |
| L-12 | Chart.js tải từ CDN. | Không có Internet thì không có biểu đồ (phần còn lại vẫn dùng được). | `index.html` |
| L-13 | Chưa có kiểm thử tự động. | Sửa mã cần kiểm tra thủ công. | — |

## 2. Hướng cải tiến đề xuất
1. Tách danh sách sinh viên cho ô chọn khỏi kết quả tìm kiếm (L-01).
2. Trả `gradeLabels` theo thứ tự cố định Giỏi → Khá → Trung bình → Cần cố gắng (L-02).
3. Kiểm tra email bằng biểu thức chính quy, `due_date` bằng `date.fromisoformat`, chặn NaN/vô cực bằng `math.isfinite` (L-04…L-06).
4. Bổ sung `PUT`/`DELETE` cho môn học và `DELETE` cho học phí (L-07).
5. Thêm phân trang cho `/api/students`, `/api/grades`, `/api/tuition` (L-08).
6. Thêm đăng nhập cho front-end (Flask-Login hoặc session tự viết) trước khi đưa lên mạng (L-11).
7. Đóng gói Chart.js cùng ứng dụng để chạy offline (L-12).
8. Viết kiểm thử `pytest` cho các endpoint API với database thử nghiệm (L-13).
