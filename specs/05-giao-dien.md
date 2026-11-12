# 05 — Giao diện (front-end)

- Địa chỉ mặc định: `http://127.0.0.1:5000`
- Mã nguồn: `frontend/app.py`, `frontend/api_client.py`, `frontend/templates/index.html`.
- Ứng dụng **một trang**: mọi chức năng nằm ở `/`; form POST xong chuyển hướng về `/` (Post/Redirect/Get).
- Trên trình duyệt có JavaScript, form và các nút Sửa / Hủy / Tất cả được gửi bằng `fetch` và **cập nhật trang tại chỗ, không tải lại** (xem mục 6). Đang nhập dở mà làm thao tác khác thì được hỏi lưu trước (mục 7).

## 1. Route
| Method | Đường dẫn | Xử lý | API back-end gọi tới |
|---|---|---|---|
| GET | `/` | Trang chính. Tham số: `q` (tìm kiếm); `edit`, `edit_subject`, `edit_grade`, `edit_tuition` (id bản ghi sinh viên / môn / điểm / học phí cần sửa); `message`, `error` (thông báo) | `GET /api/students?q=` (bảng sinh viên), `GET /api/students` không lọc (chỉ khi có `q`, cho ô chọn sinh viên ở Bảng điểm và Học phí), `GET /api/<students\|subjects\|grades\|tuition>/<id>` (khi có tham số sửa), `GET /api/subjects`, `GET /api/grades`, `GET /api/tuition`, `GET /api/stats` |
| POST | `/save` | Thêm sinh viên (không có `id`) hoặc sửa (có `id`) | `POST /api/students` / `PUT /api/students/<id>` |
| POST | `/delete/<id>` | Xóa sinh viên | `DELETE /api/students/<id>` |
| POST | `/subjects/save` | Thêm môn học (không có `id`) hoặc sửa (có `id`) | `POST /api/subjects` / `PUT /api/subjects/<id>` |
| POST | `/subjects/delete/<id>` | Xóa môn học | `DELETE /api/subjects/<id>` |
| POST | `/grades/save` | Lưu điểm (không có `id`) hoặc sửa bản ghi điểm (có `id`) | `POST /api/grades` / `PUT /api/grades/<id>` |
| POST | `/grades/delete/<id>` | Xóa điểm | `DELETE /api/grades/<id>` |
| POST | `/tuition/save` | Lưu học phí (không có `id`) hoặc sửa bản ghi học phí (có `id`) | `POST /api/tuition` / `PUT /api/tuition/<id>` |
| POST | `/tuition/delete/<id>` | Xóa học phí | `DELETE /api/tuition/<id>` |
| GET | `/health` | `200 {"frontend":"ok","backend":{...}}` hoặc `503` khi back-end lỗi | `GET /api/health` |

### Xử lý lỗi
- Lỗi từ API khi ghi → chuyển hướng `/?error=<thông điệp của back-end>`.
- Lỗi khi tải trang chính (back-end tắt, MySQL tắt…) → vẫn render trang với dữ liệu rỗng và thông báo lỗi; mã HTTP `503` nếu back-end trả/không kết nối được (503), ngược lại `502`.
- Tham số sửa trỏ tới bản ghi không tồn tại → thông báo "Không tìm thấy sinh viên / môn học / bản ghi điểm / bản ghi học phí cần sửa."
- `id` trong form sửa không phải số → `400`.

## 2. CSRF
- Token 32 byte ngẫu nhiên lưu trong session (cookie `HttpOnly`, `SameSite=Lax`).
- Mọi form POST có trường ẩn `csrf_token`; sai hoặc thiếu → `400 "Phiên làm việc hết hạn. Hãy tải lại trang."`.
- Nếu không đặt `SECRET_KEY`, khóa ký session đổi mỗi lần khởi động front-end → các trang đang mở sẽ bị lỗi CSRF, cần tải lại.

## 3. Bố cục trang (từ trên xuống)
1. **Đầu trang**: tiêu đề "🎓 Quản lý sinh viên" và mô tả.
2. **Thông báo** (`#notices`): hộp xanh (`message`) / đỏ (`error`), nổi cố định ở giữa phía trên màn hình, có nút × để đóng; hộp xanh tự ẩn sau 4 giây.
3. **Thẻ KPI** (4 thẻ): Tổng sinh viên · Môn học · Bản ghi điểm · Học phí còn nợ (định dạng `1,234,567 đ`).
4. **Dashboard** (3 biểu đồ Chart.js):
   | Biểu đồ | Loại | Dữ liệu |
   |---|---|---|
   | Tình hình học phí | Cột dọc | Phải đóng / Đã đóng / Còn nợ; tooltip định dạng VNĐ, trục rút gọn (`8 Tr`) |
   | Phân loại kết quả học tập | Vành khuyên | Số bản ghi theo xếp loại, luôn theo thứ tự và màu cố định: Giỏi (xanh dương) · Khá (xanh lá) · Trung bình (vàng cam) · Cần cố gắng (đỏ) |
   | Sinh viên theo lớp | Cột ngang | Tối đa 8 lớp |
5. **Thanh điều hướng**: liên kết neo `#students`, `#subjects`, `#grades`, `#tuition`.
6. **Sinh viên** (`#students`)
   - Form "Thêm sinh viên" / "Cập nhật sinh viên": Mã SV, Họ tên, Lớp, Email (email dùng `type="email"`); khi sửa có nút **Hủy**.
   - Ô tìm kiếm + nút **Tất cả**.
   - Bảng: Mã SV · Họ tên · Lớp · Email · Thao tác (**Sửa**, **Xóa** có hộp xác nhận).
7. **Môn học** (`#subjects`): form Mã môn, Tên môn, Tín chỉ (1–10, mặc định 3); khi sửa có dòng nhắc, nút **Lưu thay đổi** và **Hủy**. Bảng Mã môn · Tên môn · Tín chỉ · Thao tác (**Sửa**, **Xóa** có hộp xác nhận; nếu môn đã có điểm, hộp xác nhận nêu số bản ghi điểm sẽ bị xóa theo).
8. **Bảng điểm** (`#grades`)
   - Form: chọn sinh viên (luôn đủ danh sách, không bị lọc theo ô tìm kiếm), chọn môn, học kỳ, 3 điểm (0–10, bước 0,1, mặc định 8); khi sửa có dòng nhắc, nút **Lưu thay đổi** và **Hủy**.
   - Bảng: Mã SV · Sinh viên · Môn học · Học kỳ · Chuyên cần · Giữa kỳ · Cuối kỳ · Tổng kết · Thao tác (**Sửa**, **Xóa** có xác nhận).
   - Ba cột điểm thành phần hiển thị gọn bằng bộ lọc `plain_number` (`9` thay vì `9.0`, giữ `8.5`). Cột Tổng kết luôn có 2 chữ số thập phân.
9. **Học phí và công nợ** (`#tuition`)
   - Form: chọn sinh viên (luôn đủ danh sách, như ở Bảng điểm), học kỳ, phải đóng (bước 1.000), đã đóng (mặc định 0), hạn đóng (ô ngày), ghi chú; khi sửa có dòng nhắc, nút **Lưu thay đổi** và **Hủy**.
   - Bảng: Mã SV · Sinh viên · Học kỳ · Phải đóng · Đã đóng · Còn nợ · Hạn đóng (`—` nếu trống) · Trạng thái ("Đã hoàn thành" xanh / "Còn nợ" cam) · Thao tác (**Sửa**, **Xóa** có xác nhận).
10. **Chân trang**: công nghệ và liên kết `/health`.

Trong `<head>` có `<link rel="icon" href="data:,">` (biểu tượng rỗng), để trình duyệt không tự gọi `/favicon.ico` và báo lỗi 404 trong console.

### Chế độ sửa (chung cho 4 mục)
| Mục | Tham số URL | Dấu hiệu đang sửa trên form |
|---|---|---|
| Sinh viên | `edit` | Tiêu đề đổi thành "Cập nhật sinh viên" |
| Môn học | `edit_subject` | Dòng nhắc vàng "Đang sửa môn học **<mã môn>**." |
| Bảng điểm | `edit_grade` | Dòng nhắc vàng "Đang sửa điểm của **<mã SV — họ tên>**, môn **<mã môn>**, học kỳ **<học kỳ>**." |
| Học phí | `edit_tuition` | Dòng nhắc vàng "Đang sửa học phí của **<mã SV — họ tên>**, học kỳ **<học kỳ>**." |

- Nút **Sửa** mở `/?<tham số>=<id>`. Front-end gọi `GET /api/<…>/<id>` rồi điền sẵn form; ô chọn sinh viên / môn học được chọn sẵn.
- Số tiền và điểm hiển thị gọn nhờ bộ lọc Jinja `plain_number`, ví dụ `8000000` thay vì `8000000.0`.
- Form có trường ẩn `id`. Dòng đang sửa trong bảng được tô vàng (`tr.is-editing`). Nút lưu đổi thành **Lưu thay đổi**, có thêm nút **Hủy**.
- Lưu thành công hoặc bấm **Hủy** thì thoát chế độ sửa. Bấm **Hủy** là bỏ mọi thay đổi chưa lưu của form đó, không hỏi lại (mục 7).
- Lưu bị lỗi (ví dụ trùng, 409) thì vẫn ở chế độ sửa và giữ dữ liệu đã nhập (mục 6). Riêng khi tắt JavaScript, trang chuyển hướng về `/?error=…` nên thoát chế độ sửa.
- Mỗi lúc chỉ sửa một bản ghi: nút **Sửa** mới thay cho bản ghi đang sửa trước đó.

## 4. Kiểm tra phía trình duyệt
Các ô nhập có `required`, `maxlength`, `min`/`max` tương ứng quy tắc ở back-end. Đây chỉ là hỗ trợ người dùng; **back-end mới là nơi kiểm tra chính thức**.

## 5. Biểu đồ
- Dữ liệu nhúng vào trang qua `<script type="application/json" id="dashboard-data">` (Jinja `tojson`).
- Chart.js 4.4.9 tải từ `cdn.jsdelivr.net`; không tải được thì mỗi vùng biểu đồ hiện "Không tải được thư viện biểu đồ. Kiểm tra kết nối Internet."
- Sau mỗi thao tác, biểu đồ được cập nhật tại chỗ (`chart.update()`) từ dữ liệu `dashboard-data` của trang mới, có hiệu ứng chuyển.

## 6. Cập nhật tại chỗ (không tải lại trang)
Mã nguồn: khối `<script>` cuối `frontend/templates/index.html`. Phía server **không đổi**: vẫn là Post/Redirect/Get, nên khi tắt JavaScript trang hoạt động như cũ (tải lại trang).

**Luồng xử lý**
1. Bắt sự kiện `submit` của mọi form trong `<main>` và `click` của các link có thuộc tính `data-ajax` (Sửa, Hủy ở cả 4 mục; Tất cả). Giá trị `data-ajax` là id của mục cần cuộn tới và đặt con trỏ sau khi tải (`students`, `subjects`, `grades`, `tuition`), hoặc `search`. Nếu người dùng bấm Hủy ở hộp xác nhận xóa (`onsubmit="return confirm(...)"`) thì không gửi gì. Nếu đang có form nhập dở thì hỏi trước (mục 7).
2. Gửi bằng `fetch` (form POST gửi `FormData` kèm `csrf_token`; form GET và link thì gửi GET). Với POST, `fetch` tự đi theo redirect về `/?message=…` hoặc `/?error=…`.
3. Phân tích HTML trả về bằng `DOMParser`, rồi:
   - luôn thay vùng thông báo `#notices`;
   - nếu **thành công**: thay các vùng `#stats`, `#students`, `#subjects`, `#grades`, `#tuition` và cập nhật 3 biểu đồ;
   - nếu **có lỗi** (trang mới có `.notice.error`): chỉ hiện thông báo, **không** thay các vùng khác, nên form giữ nguyên dữ liệu đã nhập.
4. Giữ vị trí cuộn: đo vị trí của vùng (`section`) chứa form/link vừa dùng trước và sau khi thay nội dung rồi `scrollBy` phần chênh lệch.
5. Địa chỉ trình duyệt:
   - luôn bỏ `message`/`error`, để F5 không hiện lại thông báo cũ;
   - Tìm kiếm, Sửa, Hủy, Tất cả dùng `history.pushState`, nên nút Back/Forward vẫn quay lại đúng trạng thái (sự kiện `popstate` tải lại nội dung tại chỗ);
   - thao tác ghi dùng `replaceState`;
   - bấm menu (`#students`, `#grades`…) cũng phát `popstate` nhưng chỉ đổi phần `#neo`. Script so đường dẫn mới với nội dung đang hiển thị (`shownPath`); nếu chỉ khác `#neo` thì **không tải lại**, trình duyệt chỉ cuộn trang. Trước đây bước này tải lại các vùng dữ liệu và xóa mọi form đang nhập.
6. Con trỏ: lưu thành công thì đặt vào ô đầu tiên của form vừa dùng để nhập tiếp; bấm Sửa / Hủy thì cuộn tới form của mục đó và đặt vào ô nhập đầu tiên; tìm kiếm thì giữ con trỏ ở ô tìm kiếm.

**Trường hợp đặc biệt**
| Tình huống | Hiển thị |
|---|---|
| Đang gửi yêu cầu | Nút của form mờ đi (`aria-busy`), con trỏ chuột dạng chờ; bấm thêm lần nữa bị bỏ qua (chống gửi trùng). |
| Sai/thiếu CSRF (phiên hết hạn) | Thông báo đỏ lấy từ trang lỗi 400: "Phiên làm việc hết hạn. Hãy tải lại trang." |
| Back-end/MySQL tắt | Thông báo đỏ từ front-end; dữ liệu đang hiển thị được giữ nguyên. |
| Front-end tắt (không gọi được `fetch`) | "Không kết nối được máy chủ front-end. Hãy kiểm tra frontend/app.py còn đang chạy." |

## 7. Hỏi trước khi mất dữ liệu đang nhập dở
Mỗi thao tác thành công đều thay toàn bộ các vùng dữ liệu (mục 6), nên dữ liệu đang gõ dở ở các form sẽ mất. Vì vậy script hỏi người dùng **trước** khi thao tác chạy (FR-27). Chỉ áp dụng khi có JavaScript.

**Form "đang nhập dở"**
- Là một trong 4 form nhập liệu (thuộc tính `data-entry` = tên mục, `data-edit-param` = tham số sửa của mục).
- Form đó có ít nhất một ô khác giá trị lúc trang được tạo, tức là `defaultValue` / `defaultSelected` lấy từ HTML. So sánh sau khi bỏ khoảng trắng đầu/cuối; ô số chứa ký tự không hợp lệ (`validity.badInput`) cũng tính là đã đổi.
- Vì so với giá trị ban đầu, bấm **Sửa** chỉ để xem mà không đổi gì thì **không** bị hỏi; gõ rồi xóa hết cũng vậy.

**Khi nào hỏi**
| Thao tác | Form được xét |
|---|---|
| Bấm Sửa / Tất cả, tìm kiếm, xóa một dòng | Mọi form nhập dở |
| Bấm **Hủy** ở form đang sửa | Các form nhập dở ở mục **khác**. Thay đổi của chính form có nút Hủy bị bỏ luôn, không hỏi, vì việc của nút Hủy là bỏ thay đổi và thoát chế độ sửa |
| Lưu một form | Các form nhập dở **khác**; form đang lưu không tính |
| Back / Forward làm đổi nội dung | Mọi form nhập dở. Địa chỉ được trả về trạng thái đang hiển thị rồi mới hỏi |
| F5, đóng tab, mở liên kết khác (`/health`) | Mọi form nhập dở. Trình duyệt hiện hộp thoại "Rời khỏi trang?" của chính nó (sự kiện `beforeunload`) |
| Bấm menu (`#neo`) | Không hỏi, vì chỉ cuộn trang và không mất gì |

Với thao tác xóa, hộp xác nhận xóa (`confirm`) vẫn hiện trước như cũ.

**Hộp thoại** (`<dialog id="unsaved-dialog">`, mở bằng `showModal()`)
- Liệt kê từng mục đang nhập dở, ví dụ: **Môn học** (đang thêm mới): Mã môn, Tên môn học.
- Ba lựa chọn:

| Lựa chọn | Kết quả |
|---|---|
| **Lưu rồi tiếp tục** (con trỏ mặc định ở nút này) | 1. Kiểm tra hợp lệ **tất cả** các form trước (`checkValidity`). Có form còn thiếu hoặc sai thì không lưu form nào: hiện thông báo "Chưa lưu được mục …", rồi trình duyệt chỉ ra ô cần sửa (`reportValidity`).<br>2. Gửi lần lượt từng form (`fetchPage`, **chưa** thay trang, nên các form khác vẫn giữ dữ liệu).<br>3. Lưu được hết thì làm tiếp thao tác ban đầu. Thông báo của các lần lưu hiện kèm phía trên thông báo của thao tác.<br>4. Một form bị back-end từ chối (ví dụ trùng mã) thì dừng ở form đó và hiện lỗi. Nếu trước đó đã lưu được form nào, trang được tải lại để bảng hiện dữ liệu mới, còn các form chưa lưu được điền lại bản nháp (`refreshKeeping` / `restoreDraft`), giữ nguyên chế độ sửa của chúng. |
| **Không lưu** | Làm tiếp thao tác; dữ liệu đang nhập bị bỏ. |
| **Ở lại nhập tiếp** (hoặc phím Esc) | Không làm gì; cuộn tới và đặt con trỏ vào ô đang nhập dở. |
