# 02 — Yêu cầu chức năng

## 1. Sinh viên
| Mã | Yêu cầu |
|---|---|
| FR-01 | Hiển thị danh sách sinh viên, mới nhất trước (sắp xếp `id` giảm dần). |
| FR-02 | Tìm sinh viên theo từ khóa; khớp **một phần** trên mã SV, họ tên hoặc lớp. Từ khóa rỗng thì hiển thị tất cả. |
| FR-03 | Thêm sinh viên gồm: mã SV, họ tên, lớp, email. |
| FR-04 | Sửa sinh viên: bấm **Sửa** đưa dữ liệu lên form, bấm **Hủy** để thoát chế độ sửa. Ở mọi mục, khi đang sửa thì dòng đang sửa trong bảng được tô vàng, form hiện dòng nhắc "Đang sửa …" và nút lưu đổi thành **Lưu thay đổi**. |
| FR-05 | Xóa sinh viên sau khi người dùng xác nhận; xóa kèm toàn bộ điểm và học phí của sinh viên đó. |

**Quy tắc**
- BR-01: Cả 4 trường bắt buộc; khoảng trắng đầu/cuối bị cắt bỏ.
- BR-02: Mã SV tự chuyển thành **chữ in hoa**, tối đa 20 ký tự, **duy nhất**.
- BR-03: Họ tên ≤ 100, lớp ≤ 50, email ≤ 120 ký tự; email phải chứa `@`.
- BR-04: Trùng mã SV → báo lỗi "Mã sinh viên đã tồn tại…".

## 2. Môn học
| Mã | Yêu cầu |
|---|---|
| FR-06 | Hiển thị danh mục môn học, sắp xếp theo tên môn. |
| FR-07 | Thêm môn học gồm: mã môn, tên môn, số tín chỉ (mặc định 3). |
| FR-21 | Xóa môn học sau khi người dùng xác nhận; hộp xác nhận báo số bản ghi điểm của môn sẽ bị xóa theo. |
| FR-23 | Sửa môn học: bấm **Sửa** đưa dữ liệu lên form (mã, tên, tín chỉ), bấm **Hủy** để thoát chế độ sửa. |

**Quy tắc**
- BR-05: Mã môn in hoa, ≤ 20 ký tự, duy nhất; tên môn ≤ 120 ký tự.
- BR-06: Số tín chỉ là số nguyên từ **1 đến 10**.
- BR-16: Xóa môn học thì xóa kèm toàn bộ điểm của môn đó (cascade); thông báo kết quả nêu số bản ghi điểm đã xóa.

## 3. Bảng điểm
| Mã | Yêu cầu |
|---|---|
| FR-08 | Hiển thị bảng điểm kèm mã SV, họ tên, môn, học kỳ, 3 điểm thành phần và điểm tổng kết. Sắp xếp: học kỳ giảm dần → mã SV → tên môn. |
| FR-09 | Lưu điểm cho một (sinh viên, môn học, học kỳ). Nếu bộ ba này đã có điểm thì **cập nhật** thay vì tạo mới. |
| FR-10 | Xóa một bản ghi điểm sau khi người dùng xác nhận. |
| FR-24 | Sửa một bản ghi điểm: bấm **Sửa** đưa sinh viên, môn, học kỳ và 3 điểm lên form; có thể đổi cả sinh viên / môn / học kỳ. Bấm **Hủy** để thoát. |

**Quy tắc**
- BR-07: Điểm chuyên cần, giữa kỳ, cuối kỳ là số thực trong `[0, 10]`.
- BR-08: Học kỳ bắt buộc, ≤ 20 ký tự, dạng tự do (gợi ý `2026-1`).
- BR-09: **Điểm tổng kết** = `chuyên cần × 0,1 + giữa kỳ × 0,3 + cuối kỳ × 0,6`, làm tròn 2 chữ số. Được tính khi truy vấn, không lưu trong DB.
- BR-10: **Xếp loại** theo điểm tổng kết: Giỏi ≥ 8; Khá ≥ 6,5; Trung bình ≥ 5; còn lại là "Cần cố gắng".
- BR-11: Sinh viên hoặc môn học không tồn tại → báo lỗi.
- BR-17: Khi **sửa** một bản ghi điểm sang bộ (sinh viên, môn học, học kỳ) đã thuộc về bản ghi khác → báo lỗi trùng, không gộp hay ghi đè bản ghi kia.

## 4. Học phí
| Mã | Yêu cầu |
|---|---|
| FR-11 | Hiển thị học phí: mã SV, họ tên, học kỳ, phải đóng, đã đóng, còn nợ, hạn đóng, trạng thái. Sắp xếp: học kỳ giảm dần → mã SV. |
| FR-12 | Lưu học phí cho một (sinh viên, học kỳ); nếu đã có thì **cập nhật**. |
| FR-25 | Sửa một bản ghi học phí: bấm **Sửa** đưa toàn bộ thông tin lên form; bấm **Hủy** để thoát. |
| FR-26 | Xóa một bản ghi học phí sau khi người dùng xác nhận. |

**Quy tắc**
- BR-12: Mỗi sinh viên có tối đa **một** bản ghi học phí cho mỗi học kỳ.
- BR-13: `0 ≤ đã đóng ≤ phải đóng`; để trống "đã đóng" thì coi là 0.
- BR-14: **Còn nợ** = `max(phải đóng − đã đóng, 0)`. Trạng thái "Đã hoàn thành" khi còn nợ = 0, ngược lại "Còn nợ".
- BR-15: Hạn đóng tùy chọn (chuỗi ≤ 10 ký tự, giao diện dùng ô chọn ngày `YYYY-MM-DD`); ghi chú ≤ 200 ký tự.
- BR-18: Khi **sửa** một bản ghi học phí sang (sinh viên, học kỳ) đã có bản ghi khác → báo lỗi trùng.

## 5. Dashboard
| Mã | Yêu cầu |
|---|---|
| FR-13 | 4 thẻ KPI: tổng sinh viên, số môn học, số bản ghi điểm, tổng học phí còn nợ (VNĐ). |
| FR-14 | Biểu đồ cột "Tình hình học phí": tổng phải đóng / đã đóng / còn nợ. |
| FR-15 | Biểu đồ vành khuyên "Phân loại kết quả học tập": số bản ghi điểm theo xếp loại (BR-10). |
| FR-16 | Biểu đồ cột ngang "Sinh viên theo lớp": tối đa 8 lớp đông nhất. |
| FR-17 | Khi chưa có dữ liệu, biểu đồ hiện nhãn "Chưa có dữ liệu"; khi không tải được Chart.js, hiện thông báo kiểm tra Internet. |

## 6. Hệ thống
| Mã | Yêu cầu |
|---|---|
| FR-18 | Sau mỗi thao tác ghi, hiển thị thông báo thành công (xanh) hoặc lỗi (đỏ) nổi ở đầu màn hình, nhìn thấy được dù đang cuộn ở bất kỳ đâu. Thông báo thành công tự ẩn sau 4 giây; thông báo lỗi giữ lại tới khi người dùng bấm ×. |
| FR-19 | Endpoint health cho cả back-end (`/api/health`) và front-end (`/health`). |
| FR-20 | Công cụ dòng lệnh chép dữ liệu từ SQLite sang MySQL, chạy lại không tạo bản trùng. |
| FR-22 | Thêm / sửa / xóa / tìm kiếm **không tải lại trang**: chỉ các vùng dữ liệu (thẻ KPI, bảng, ô chọn) và biểu đồ được cập nhật; vị trí cuộn được giữ nguyên. Khi thao tác bị lỗi, form giữ nguyên dữ liệu đã nhập để sửa lại. |

## 7. Yêu cầu phi chức năng
| Mã | Yêu cầu |
|---|---|
| NFR-01 | Toàn bộ văn bản, dữ liệu dùng tiếng Việt có dấu (UTF-8 / `utf8mb4`). |
| NFR-02 | Mọi form POST được bảo vệ bằng CSRF token. |
| NFR-03 | Mọi truy vấn SQL dùng tham số hóa (chống SQL injection). |
| NFR-04 | Mỗi request ghi chạy trong một transaction; lỗi thì rollback. |
| NFR-05 | Khi back-end hoặc MySQL không chạy, front-end vẫn hiển thị trang với thông báo lỗi rõ ràng (HTTP 502/503) thay vì sập. |
| NFR-06 | Giao diện dùng được trên màn hình điện thoại (CSS responsive). |
| NFR-07 | Front-end gọi back-end có timeout (mặc định 5 giây, biến `API_TIMEOUT`). |
| NFR-08 | Trình duyệt tắt JavaScript vẫn dùng được đầy đủ chức năng (form gửi theo cách truyền thống, tải lại trang). |
