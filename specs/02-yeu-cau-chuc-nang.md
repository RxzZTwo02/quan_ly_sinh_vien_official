# 02 — Yêu cầu chức năng

## 1. Sinh viên
| Mã | Yêu cầu |
|---|---|
| FR-01 | Hiển thị danh sách sinh viên, mới nhất trước (sắp xếp `id` giảm dần). |
| FR-02 | Tìm sinh viên theo từ khóa; khớp **một phần** trên mã SV, họ tên hoặc lớp. Từ khóa rỗng thì hiển thị tất cả. Mọi ký tự trong từ khóa, kể cả `%` và `_`, được tìm đúng như đã gõ (áp dụng cho cả ô tìm kiếm của FR-31). Tìm kiếm chỉ lọc bảng sinh viên; ô chọn sinh viên ở form Bảng điểm và Học phí luôn có đủ sinh viên. |
| FR-03 | Thêm sinh viên gồm: mã SV, họ tên, lớp, email. |
| FR-04 | Sửa sinh viên: chọn dòng (FR-29) rồi bấm **Sửa** đưa dữ liệu lên form, tiêu đề form đổi thành "Cập nhật sinh viên"; bấm **Hủy** để bỏ mọi thay đổi chưa lưu và thoát chế độ sửa, không hỏi lại (áp dụng cho nút Hủy ở cả 4 mục). Ở mọi mục, khi đang sửa thì dòng đang sửa trong bảng được tô vàng và nút lưu đổi thành **Lưu thay đổi**; form Môn học, Bảng điểm, Học phí còn hiện dòng nhắc "Đang sửa …". |
| FR-05 | Xóa sinh viên: chọn dòng (FR-29) rồi bấm **Xóa**, sau khi người dùng xác nhận; xóa kèm toàn bộ điểm và học phí của sinh viên đó. Ở cả 4 mục, việc xác nhận xóa dùng hộp thoại của chương trình (không dùng hộp "localhost:5000 says" của trình duyệt), nêu rõ bản ghi sẽ bị xóa, có hai nút **Xóa** / **Hủy**. Chi tiết: [05](05-giao-dien.md) mục 8. |

**Quy tắc**
- BR-01: Cả 4 trường bắt buộc; khoảng trắng đầu/cuối bị cắt bỏ.
- BR-02: Mã SV tự chuyển thành **chữ in hoa**, tối đa 20 ký tự, **duy nhất**, và **chỉ gồm chữ cái không dấu và chữ số** (`A–Z`, `0–9`, ví dụ `SV001`): không có dấu `-`, khoảng trắng hay ký tự đặc biệt.
- BR-03: Họ tên ≤ 100, lớp ≤ 50, email ≤ 120 ký tự; email phải đúng dạng `<tên>@<miền>.<đuôi>`, không có khoảng trắng và chỉ một dấu `@` (ví dụ `an@example.com`). Các giá trị như `@`, `a@`, `a@b`, `qa mail @ x y` bị từ chối, kể cả khi gửi thẳng tới API.
- BR-20: **Họ tên** bắt đầu bằng chữ cái (kể cả chữ có dấu), sau đó chỉ gồm chữ cái, khoảng trắng và các dấu `'` `.` `-` (ví dụ `Nguyễn Văn An`, `O'Neil`); không có chữ số, ký hiệu, xuống dòng. **Lớp** bắt đầu bằng chữ hoặc số, sau đó chỉ gồm chữ, số, khoảng trắng và `-` `_` `.` (ví dụ `CNTT1`, `K65-CNTT`). Hai ô này được chuẩn hóa Unicode NFC trước khi kiểm tra và lưu.
- BR-04: Trùng mã SV → báo lỗi "Mã sinh viên <mã> đã tồn tại.".
- BR-19: Nhập sai thì thông báo nêu **rõ ô nào sai và sai thế nào**, liệt kê mọi ô sai trong một câu, ví dụ "Thông tin sinh viên chưa hợp lệ: Họ tên không được để trống; Lớp tối đa 50 ký tự (đang có 51)." Áp dụng cho Sinh viên và Môn học.

## 2. Môn học
| Mã | Yêu cầu |
|---|---|
| FR-06 | Hiển thị danh mục môn học, sắp xếp theo tên môn. |
| FR-07 | Thêm môn học gồm: mã môn, tên môn, số tín chỉ (mặc định 3). |
| FR-21 | Xóa môn học sau khi người dùng xác nhận; hộp xác nhận báo số bản ghi điểm của môn sẽ bị xóa theo. |
| FR-23 | Sửa môn học: bấm **Sửa** đưa dữ liệu lên form (mã, tên, tín chỉ), bấm **Hủy** để thoát chế độ sửa. |

**Quy tắc**
- BR-05: Mã môn in hoa, ≤ 20 ký tự, chỉ gồm chữ cái không dấu và chữ số (như BR-02, ví dụ `INT1001`), duy nhất (trùng → "Mã môn học <mã> đã tồn tại."); tên môn ≤ 120 ký tự. Nhập sai thì báo rõ ô nào sai (BR-19).
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
- BR-08: Học kỳ bắt buộc, ≤ 20 ký tự, dạng tự do (giao diện gợi ý `HK1-2026`, dữ liệu mẫu dùng `HK1-2025`, `HK2-2025`).
- BR-09: **Điểm tổng kết** = `chuyên cần × 0,1 + giữa kỳ × 0,3 + cuối kỳ × 0,6`, làm tròn 2 chữ số. Được tính khi truy vấn, không lưu trong DB.
- BR-10: **Xếp loại** theo điểm tổng kết **đã làm tròn** (đúng số hiển thị trong bảng): Giỏi ≥ 8; Khá ≥ 6,5; Trung bình ≥ 5; còn lại là "Cần cố gắng".
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
- BR-13: `0 ≤ đã đóng ≤ phải đóng < 10¹³` (giới hạn của cột `DECIMAL(15,2)`); để trống "đã đóng" thì coi là 0.
- BR-14: **Còn nợ** = `max(phải đóng − đã đóng, 0)`. Trạng thái "Đã hoàn thành" khi còn nợ = 0, ngược lại "Còn nợ".
- BR-15: Hạn đóng tùy chọn. Nếu nhập thì phải là ngày có thật theo ISO 8601, được lưu dạng `YYYY-MM-DD` (ví dụ `20261231` lưu thành `2026-12-31`; `2026-02-30` hay `31/12/2026` bị từ chối). Giao diện dùng ô chọn ngày. Ghi chú ≤ 200 ký tự.
- BR-18: Khi **sửa** một bản ghi học phí sang (sinh viên, học kỳ) đã có bản ghi khác → báo lỗi trùng.

## 5. Dashboard
| Mã | Yêu cầu |
|---|---|
| FR-13 | 4 thẻ KPI: tổng sinh viên, số môn học, số bản ghi điểm, tổng học phí còn nợ (VNĐ). |
| FR-14 | Biểu đồ cột "Tình hình học phí": tổng phải đóng / đã đóng / còn nợ. |
| FR-15 | Biểu đồ vành khuyên "Phân loại kết quả học tập": số bản ghi điểm theo xếp loại (BR-10). Luôn đủ 4 xếp loại theo thứ tự cố định Giỏi → Khá → Trung bình → Cần cố gắng (kể cả xếp loại có 0 bản ghi), nên mỗi xếp loại giữ một màu cố định. |
| FR-16 | Biểu đồ cột ngang "Sinh viên theo lớp": tối đa 8 lớp đông nhất. |
| FR-17 | Khi chưa có dữ liệu, biểu đồ hiện nhãn "Chưa có dữ liệu"; khi không tải được Chart.js, hiện thông báo kiểm tra Internet. |

## 6. Hệ thống
| Mã | Yêu cầu |
|---|---|
| FR-18 | Sau mỗi thao tác ghi, hiển thị thông báo thành công (xanh) hoặc lỗi (đỏ) nổi ở đầu màn hình, nhìn thấy được dù đang cuộn ở bất kỳ đâu. Thông báo thành công tự ẩn sau 4 giây; thông báo lỗi giữ lại tới khi người dùng bấm ×. |
| FR-19 | Endpoint health cho cả back-end (`/api/health`) và front-end (`/health`). |
| FR-20 | Khi khởi động, tự tạo database và bảng từ `schema.sql` nếu chưa có. Nếu database rỗng (cả 4 bảng chưa có dòng nào) và `SEED_DATA=yes` (mặc định) thì nạp dữ liệu mẫu từ `seed.sql`; `SEED_DATA=no` thì để trống. Database đã có dữ liệu thì không bị thay đổi và không đọc `seed.sql`. |
| FR-22 | Thêm / sửa / xóa / tìm kiếm **không tải lại trang**: chỉ các vùng dữ liệu (thẻ KPI, bảng, ô chọn) và biểu đồ được cập nhật; vị trí cuộn được giữ nguyên. Khi thao tác bị lỗi, form giữ nguyên dữ liệu đã nhập để sửa lại. Bấm menu (Sinh viên, Môn học, Bảng điểm, Học phí) chỉ cuộn trang, không làm mất dữ liệu đang nhập. |
| FR-27 | Khi đang nhập dở ở một form mà người dùng làm thao tác khác (Sửa / Tất cả, tìm kiếm, xóa, lưu form khác, Hủy ở form khác, Back / Forward), hỏi trước khi làm: **Lưu rồi tiếp tục** / **Không lưu** / **Ở lại nhập tiếp**. Chọn lưu mà dữ liệu chưa đủ hoặc bị từ chối thì dừng lại, chỉ ra chỗ cần sửa và giữ nguyên dữ liệu. Riêng nút **Hủy** của chính form đang sửa thì không hỏi về form đó (FR-04); chỉ hỏi nếu form ở mục khác đang nhập dở. F5 hoặc đóng tab khi đang nhập dở thì trình duyệt hỏi "Rời khỏi trang?". Khi thêm mới, ô để trống không tính là đang nhập dở. Chi tiết: [05](05-giao-dien.md) mục 7. |
| FR-28 | Mỗi form (Sinh viên, Môn học, Bảng điểm, Học phí) có nút **Làm mới** khi **thêm mới**: làm trống mọi ô đã nhập (kể cả ô có giá trị mặc định và ô chọn) trước khi lưu thành dữ liệu chính thức, không hỏi lại. Khi **đang sửa**, nút Làm mới bị ẩn; nhóm nút bên trái chỉ còn **Lưu thay đổi** và **Hủy** (Hủy thoát chế độ sửa), Sửa / Xóa bên phải vẫn giữ. Khác với **Tất cả** (chỉ bỏ kết quả tìm kiếm của bảng, FR-02 / FR-31). |
| FR-29 | Bảng của 4 mục không có cột Thao tác. Nút **Sửa** (xanh lá) và **Xóa** (đỏ) nằm cùng hàng nút của form; khi chưa chọn dòng nào thì màu đen và bị vô hiệu. Nhấp chuột phải vào một dòng để chọn (dòng tô vàng, hai nút sáng lên); nhấp chuột phải lần nữa để bỏ chọn, dòng trở về như ban đầu. Mỗi mục chọn riêng một dòng; dòng đang sửa không chọn được. Áp dụng cho Sửa / Xóa ở cả 4 mục (FR-04, FR-05, FR-10, FR-21, FR-23 – FR-26). Chi tiết: [05](05-giao-dien.md) mục 3. |
| FR-30 | Đang sửa mà bấm **Sửa** bản ghi khác (cùng mục hay mục khác) thì luôn hỏi trước, **kể cả khi chưa đổi gì**. Các thao tác khác làm thay trang (xóa, lưu mục khác, tìm kiếm, Tất cả, Back / Forward) chỉ hỏi khi form đang sửa đã có thay đổi (FR-27); chưa đổi gì thì thoát chế độ sửa mà không hỏi ([07](07-han-che.md) L-13). Hộp thoại "Chưa hoàn tất sửa thông tin" nêu mục và bản ghi đang sửa (ví dụ "Sinh viên (đang sửa SV005 — Hoàng Minh Đức): chưa thay đổi gì"), với 3 lựa chọn như FR-27. Chưa đổi gì mà chọn **Lưu rồi tiếp tục** thì không gửi lưu lại, chỉ chuyển sang bản ghi mới. Áp dụng cho cả 4 mục. Chi tiết: [05](05-giao-dien.md) mục 7. |
| FR-31 | Môn học, Bảng điểm, Học phí cũng có ô tìm kiếm + nút **Tất cả** như bảng sinh viên (FR-02), khớp **một phần**: Môn học theo mã hoặc tên môn; Bảng điểm theo mã SV, họ tên, mã / tên môn hoặc học kỳ; Học phí theo mã SV, họ tên hoặc học kỳ. Tìm kiếm chỉ lọc bảng của mục đó: ô chọn môn học ở form Bảng điểm luôn đủ danh sách, và hộp xác nhận xóa môn vẫn đếm đủ số bản ghi điểm của môn. Không có kết quả thì bảng ghi "Không có … phù hợp." |
| FR-32 | Kết quả tìm kiếm của mỗi bảng được **giữ nguyên** cho đến khi bấm nút **Tất cả** của chính bảng đó: bấm Sửa, Hủy, lưu, xóa (ở bất kỳ mục nào) hay tìm kiếm ở bảng khác đều không làm bảng quay về danh sách đầy đủ. Vì vậy sau khi tìm và bấm Sửa, bản ghi đang sửa vẫn nằm trong danh sách kết quả, được tô vàng. Lưu thay đổi xong mà bản ghi không còn khớp từ khóa thì nó rời khỏi danh sách kết quả. |
| FR-33 | Bấm **Sửa** ở bất kỳ mục nào thì dòng đang sửa được đưa lên **đầu bảng** (đầu danh sách kết quả nếu đang tìm kiếm) và tô vàng; các dòng khác giữ thứ tự cũ. Lưu thay đổi thành công hoặc bấm **Hủy** thì dòng về lại vị trí và trạng thái ban đầu theo thứ tự sắp xếp của bảng (FR-01, FR-06, FR-08, FR-11). Ô chọn sinh viên / môn học ở các form không bị đổi thứ tự. |

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
| NFR-08 | Trình duyệt tắt JavaScript vẫn dùng được đầy đủ chức năng (form gửi theo cách truyền thống, tải lại trang). Khi đó Sửa / Xóa dùng cột Thao tác trên từng dòng thay cho chọn dòng (FR-29). Riêng hộp thoại hỏi lưu dữ liệu đang nhập dở (FR-27, FR-30) và hộp xác nhận xóa cần JavaScript; khi tắt JavaScript, bấm Xóa là xóa ngay, và **Làm mới** đưa form về giá trị mặc định thay vì làm trống. |
