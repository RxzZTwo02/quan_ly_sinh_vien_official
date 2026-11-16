# 05 — Giao diện (front-end)

- Địa chỉ mặc định: `http://127.0.0.1:5000`
- Mã nguồn: `frontend/app.py`, `frontend/api_client.py`, `frontend/templates/index.html`.
- Ứng dụng **một trang**: mọi chức năng nằm ở `/`; form POST xong chuyển hướng về `/` (Post/Redirect/Get).
- Trên trình duyệt có JavaScript, form và các nút Sửa / Hủy / Tất cả được gửi bằng `fetch` và **cập nhật trang tại chỗ, không tải lại** (xem mục 6). Đang nhập dở mà làm thao tác khác thì được hỏi lưu trước (mục 7). Bấm Hủy ở form đang sửa thì bỏ thay đổi ngay, không hỏi. Bấm Xóa thì hiện hộp xác nhận của chương trình (mục 8). Sửa / Xóa thực hiện bằng cách chọn dòng (chuột phải) rồi bấm nút ở hàng nút của form (mục 3, "Hàng nút và chọn dòng").

## 1. Route
| Method | Đường dẫn | Xử lý | API back-end gọi tới |
|---|---|---|---|
| GET | `/` | Trang chính. Tham số: `q`, `q_subject`, `q_grade`, `q_tuition` (từ khóa tìm kiếm của bảng sinh viên / môn học / điểm / học phí); `edit`, `edit_subject`, `edit_grade`, `edit_tuition` (id bản ghi sinh viên / môn / điểm / học phí cần sửa). Tham số `message` / `error` của link cũ bị bỏ qua (xem "Thông báo" bên dưới) | `GET /api/students?q=` (bảng sinh viên), `GET /api/students` không lọc (chỉ khi có `q`, cho ô chọn sinh viên ở Bảng điểm và Học phí), `GET /api/<students\|subjects\|grades\|tuition>/<id>` (khi có tham số sửa), `GET /api/subjects`, `GET /api/grades` (luôn gọi không lọc: ô chọn môn ở Bảng điểm, số bản ghi điểm của môn), thêm `GET /api/subjects?q=` / `GET /api/grades?q=` khi có `q_subject` / `q_grade`, `GET /api/tuition?q=`, `GET /api/stats` |
| POST | `/save` | Thêm sinh viên (không có `id`) hoặc sửa (có `id`) | `POST /api/students` / `PUT /api/students/<id>` |
| POST | `/delete/<id>` | Xóa sinh viên | `DELETE /api/students/<id>` |
| POST | `/subjects/save` | Thêm môn học (không có `id`) hoặc sửa (có `id`) | `POST /api/subjects` / `PUT /api/subjects/<id>` |
| POST | `/subjects/delete/<id>` | Xóa môn học | `DELETE /api/subjects/<id>` |
| POST | `/grades/save` | Lưu điểm (không có `id`) hoặc sửa bản ghi điểm (có `id`) | `POST /api/grades` / `PUT /api/grades/<id>` |
| POST | `/grades/delete/<id>` | Xóa điểm | `DELETE /api/grades/<id>` |
| POST | `/tuition/save` | Lưu học phí (không có `id`) hoặc sửa bản ghi học phí (có `id`) | `POST /api/tuition` / `PUT /api/tuition/<id>` |
| POST | `/tuition/delete/<id>` | Xóa học phí | `DELETE /api/tuition/<id>` |
| GET | `/health` | `200 {"frontend":"ok","backend":{...}}` hoặc `503` khi back-end lỗi | `GET /api/health` |

### Giữ kết quả tìm kiếm (FR-32)
- Hằng `SEARCH_PARAMS = ("q", "q_subject", "q_grade", "q_tuition")` và hàm `active_searches()` trong `frontend/app.py` lấy các từ khóa đang dùng (bỏ ô rỗng); template nhận chúng qua biến `searches`.
- Link **Sửa** và **Hủy** ở cả 4 mục: `url_for('index', <tham số sửa>, **searches)`, nên giữ mọi từ khóa.
- Mọi form POST (4 form nhập liệu, 4 loại form xóa) có ô ẩn chứa các từ khóa (macro Jinja `keep_search`). `call_and_redirect()` đọc lại chúng từ form và đưa vào địa chỉ chuyển hướng `/?q=…`. Ô ẩn không được tính khi xét "đang nhập dở" (mục 7).
- Form tìm kiếm của mỗi mục có ô ẩn chứa từ khóa của 3 mục kia, nên tìm ở bảng này không bỏ kết quả của bảng khác.
- Nút **Tất cả** của mỗi mục chỉ bỏ từ khóa của mục đó (bộ lọc Jinja `without`).
- Không có từ khóa nào thì các địa chỉ giữ dạng cũ, không có tham số rỗng.

### Thông báo (chống giả mạo, BUG-05)
- Sau khi lưu / xóa, `call_and_redirect()` ghi thông báo của back-end vào session bằng `flash(…, "success" | "error")` rồi chuyển hướng về `/` (kèm các từ khóa đang tìm). `index()` đọc `get_flashed_messages(with_categories=True)`: mỗi thông báo hiện **một lần**, F5 không hiện lại.
- Trang chính **không** đọc thông báo từ URL. Trước đây `/?error=<chữ bất kỳ>` hiện thành hộp đỏ giống thông báo thật, nên có thể gửi link chứa thông báo giả (content spoofing).
- Thông báo lỗi khác do chính server tạo khi tải trang (không tìm thấy bản ghi cần sửa, back-end tắt) vẫn hiện như cũ.

### Xử lý lỗi
- Lỗi từ API khi ghi → flash thông điệp của back-end (hộp đỏ) rồi chuyển hướng về `/` (kèm các từ khóa đang tìm).
- Lỗi khi tải trang chính (back-end tắt, MySQL tắt…) → vẫn render trang với dữ liệu rỗng và thông báo lỗi; mã HTTP `503` nếu back-end trả/không kết nối được (503), ngược lại `502`.
- Tham số sửa trỏ tới bản ghi không tồn tại → thông báo "Không tìm thấy sinh viên / môn học / bản ghi điểm / bản ghi học phí cần sửa."
- `id` trong form sửa không phải số → `400`.

## 2. CSRF
- Token 32 byte ngẫu nhiên lưu trong session (cookie `HttpOnly`, `SameSite=Lax`).
- Mọi form POST có trường ẩn `csrf_token`; sai hoặc thiếu → `400 "Phiên làm việc hết hạn. Hãy tải lại trang."`.
- Nếu không đặt `SECRET_KEY`, khóa ký session đổi mỗi lần khởi động front-end → các trang đang mở sẽ bị lỗi CSRF, cần tải lại.

## 3. Bố cục trang (từ trên xuống)
1. **Đầu trang**: tiêu đề "🎓 Quản lý sinh viên" và mô tả.
2. **Thông báo** (`#notices`): hộp xanh (thành công) / đỏ (lỗi), chỉ do server tạo (mục 1, "Thông báo"), nổi cố định ở giữa phía trên màn hình, có nút × để đóng; hộp xanh tự ẩn sau 4 giây.
3. **Thẻ KPI** (4 thẻ): Tổng sinh viên · Môn học · Bản ghi điểm · Học phí còn nợ (định dạng `1,234,567 đ`).
4. **Dashboard** (3 biểu đồ Chart.js):
   | Biểu đồ | Loại | Dữ liệu |
   |---|---|---|
   | Tình hình học phí | Cột dọc | Phải đóng / Đã đóng / Còn nợ; tooltip định dạng VNĐ, trục rút gọn (`8 Tr`) |
   | Phân loại kết quả học tập | Vành khuyên | Số bản ghi theo xếp loại, luôn theo thứ tự và màu cố định: Giỏi (xanh dương) · Khá (xanh lá) · Trung bình (vàng cam) · Cần cố gắng (đỏ) |
   | Sinh viên theo lớp | Cột ngang | Tối đa 8 lớp |
5. **Thanh điều hướng**: liên kết neo `#students`, `#subjects`, `#grades`, `#tuition`.

Mỗi mục 6–9 gồm form, hàng nút (xem "Hàng nút và chọn dòng" bên dưới), dòng gợi ý "Nhấp chuột phải vào một dòng để chọn…" và bảng dữ liệu.

6. **Sinh viên** (`#students`)
   - Form "Thêm sinh viên" / "Cập nhật sinh viên": Mã SV, Họ tên, Lớp, Email (email dùng `type="email"`).
   - Ô tìm kiếm + nút **Tất cả**.
   - Bảng: Mã SV · Họ tên · Lớp · Email.
7. **Môn học** (`#subjects`): form Mã môn, Tên môn, Tín chỉ (1–10, mặc định 3); khi sửa có dòng nhắc. Ô tìm kiếm (`q_subject`) + nút **Tất cả**. Bảng Mã môn · Tên môn · Tín chỉ. Nếu môn đã có điểm, hộp xác nhận xóa nêu số bản ghi điểm sẽ bị xóa theo.
8. **Bảng điểm** (`#grades`)
   - Form: chọn sinh viên và chọn môn (luôn đủ danh sách, không bị lọc theo ô tìm kiếm), học kỳ, 3 điểm (0–10, bước 0,1, mặc định 8); khi sửa có dòng nhắc.
   - Ô tìm kiếm (`q_grade`) + nút **Tất cả**.
   - Bảng: Mã SV · Sinh viên · Môn học · Học kỳ · Chuyên cần · Giữa kỳ · Cuối kỳ · Tổng kết.
   - Ba cột điểm thành phần hiển thị gọn bằng bộ lọc `plain_number` (`9` thay vì `9.0`, giữ `8.5`). Cột Tổng kết luôn có 2 chữ số thập phân.
9. **Học phí và công nợ** (`#tuition`)
   - Form: chọn sinh viên (luôn đủ danh sách, như ở Bảng điểm), học kỳ, phải đóng (bước 1.000), đã đóng (mặc định 0), hạn đóng (ô ngày), ghi chú; khi sửa có dòng nhắc.
   - Ô tìm kiếm (`q_tuition`) + nút **Tất cả**.
   - Bảng: Mã SV · Sinh viên · Học kỳ · Phải đóng · Đã đóng · Còn nợ · Hạn đóng (`—` nếu trống) · Trạng thái ("Đã hoàn thành" xanh / "Còn nợ" cam).
10. **Chân trang**: công nghệ và liên kết `/health`.

Mỗi bảng vẫn có cột **Thao tác** (link Sửa, nút Xóa trên từng dòng) trong HTML, nhưng cột này bị ẩn khi có JavaScript. Xem "Khi tắt JavaScript" bên dưới.

Trong `<head>` có `<link rel="icon" href="data:,">` (biểu tượng rỗng), để trình duyệt không tự gọi `/favicon.ico` và báo lỗi 404 trong console.

### Chế độ sửa (chung cho 4 mục)
| Mục | Tham số URL | Dấu hiệu đang sửa trên form |
|---|---|---|
| Sinh viên | `edit` | Tiêu đề đổi thành "Cập nhật sinh viên" |
| Môn học | `edit_subject` | Dòng nhắc vàng "Đang sửa môn học **<mã môn>**." |
| Bảng điểm | `edit_grade` | Dòng nhắc vàng "Đang sửa điểm của **<mã SV — họ tên>**, môn **<mã môn>**, học kỳ **<học kỳ>**." |
| Học phí | `edit_tuition` | Dòng nhắc vàng "Đang sửa học phí của **<mã SV — họ tên>**, học kỳ **<học kỳ>**." |

- Chọn dòng rồi bấm **Sửa** ở hàng nút: mở `/?<tham số>=<id>`. Front-end gọi `GET /api/<…>/<id>` rồi điền sẵn form; ô chọn sinh viên / môn học được chọn sẵn.
- Số tiền và điểm hiển thị gọn nhờ bộ lọc Jinja `plain_number`, ví dụ `8000000` thay vì `8000000.0`.
- Form có trường ẩn `id` và thuộc tính `data-editing-label` (mã, tên của bản ghi đang sửa, dùng trong hộp thoại ở mục 7). Dòng đang sửa trong bảng được tô vàng, có thêm vạch cam bên trái (`tr.is-editing`) để phân biệt với dòng đang chọn. Nút lưu đổi thành **Lưu thay đổi**, có thêm nút **Hủy**.
- Dòng đang sửa được đưa lên **đầu bảng** (FR-33), kể cả khi bảng đang hiện kết quả tìm kiếm; các dòng khác giữ thứ tự cũ. Việc này làm ở phía server bằng bộ lọc Jinja `editing_first` (sắp xếp ổn định) trên vòng lặp của 4 bảng, không áp dụng cho ô chọn sinh viên / môn học, và vẫn đúng khi tắt JavaScript.
- Lưu thành công hoặc bấm **Hủy** thì thoát chế độ sửa; địa chỉ không còn tham số sửa nên dòng về lại vị trí cũ và hết tô vàng. Bấm **Hủy** là bỏ mọi thay đổi chưa lưu của form đó, không hỏi lại (mục 7).
- Lưu bị lỗi (ví dụ trùng, 409) thì vẫn ở chế độ sửa và giữ dữ liệu đã nhập (mục 6). Riêng khi tắt JavaScript, trang chuyển hướng về `/` (kèm thông báo lỗi) nên thoát chế độ sửa.
- Mỗi lúc chỉ sửa một bản ghi trên cả trang, vì link Sửa chỉ mang một tham số sửa. Đang sửa mà bấm **Sửa** bản ghi khác (cùng mục hay mục khác) thì luôn hỏi trước "Chưa hoàn tất sửa thông tin", kể cả khi chưa đổi gì (mục 7).
- Khi sửa, nút **Làm mới** bị ẩn; nhóm nút bên trái chỉ còn **Lưu thay đổi** và **Hủy**. Sửa / Xóa bên phải vẫn giữ.

### Hàng nút và chọn dòng (chung cho 4 mục)
Hàng nút dưới mỗi form, từ trái sang:

| Nút | Khi nào hiện | Tác dụng |
|---|---|---|
| **Thêm …** / **Lưu điểm** / **Lưu học phí** / **Lưu thay đổi** | Luôn | Gửi form |
| **Hủy** | Đang sửa | Bỏ thay đổi, thoát chế độ sửa, form trở về thêm mới |
| **Làm mới** | Chỉ khi **thêm mới** (đang sửa thì ẩn) | Làm trống mọi ô của form trước khi lưu thành dữ liệu chính thức, kể cả ô có giá trị mặc định (tín chỉ 3, điểm 8, đã đóng 0) và ô chọn. Không hỏi lại. Con trỏ về ô đầu tiên. |
| **Sửa** (xanh lá) | Luôn, nằm bên phải | Sửa dòng đang chọn trong bảng của mục |
| **Xóa** (đỏ) | Luôn, nằm bên phải | Xóa dòng đang chọn, sau hộp xác nhận (mục 8) |

**Chọn dòng**
- Chưa chọn dòng nào: **Sửa** và **Xóa** màu đen, bị vô hiệu (`disabled`).
- Nhấp chuột phải vào một dòng: dòng được chọn, tô vàng (`tr.is-selected`, cùng màu với dòng đang sửa); **Sửa** sáng xanh lá, **Xóa** sáng đỏ.
- Nhấp chuột phải lần nữa vào dòng đó: bỏ chọn, dòng và hai nút trở về như ban đầu. Nhấp chuột phải dòng khác: chuyển lựa chọn sang dòng đó.
- Mỗi mục chọn riêng một dòng. Menu chuột phải của trình duyệt chỉ bị chặn trên các dòng dữ liệu; chỗ khác vẫn như thường.
- Bàn phím: mỗi dòng nhận focus bằng Tab (`tabindex="0"`); phím Menu hoặc Shift+F10 có tác dụng như chuột phải.
- Dòng đang sửa đã được tô vàng nên không chọn được; thoát sửa bằng **Hủy**.
- Lựa chọn được giữ khi trang cập nhật do thao tác khác, nếu dòng còn tồn tại. Bấm **Sửa** thì dòng chuyển sang "đang sửa"; xóa xong thì dòng biến mất; cả hai trường hợp đều tự bỏ chọn.
- Dòng "Chưa có …" khi bảng rỗng không chọn được.

**Cách làm**: nút **Sửa** gọi `click()` link Sửa của dòng, nút **Xóa** gọi `requestSubmit()` form xóa của dòng (cả hai nằm trong cột Thao tác bị ẩn). Vì vậy hai nút đi qua đúng luồng cũ: cập nhật tại chỗ (mục 6), hỏi lưu dữ liệu đang nhập dở (mục 7) và hộp xác nhận xóa (mục 8).

**Khi tắt JavaScript**
- Thẻ `<html>` không có class `js`, nên cột **Thao tác** hiện như cũ (link Sửa, nút Xóa trên từng dòng; xóa không có hộp xác nhận).
- Nút **Sửa** / **Xóa** ở hàng nút và dòng gợi ý bị ẩn.
- **Làm mới** là nút `type="reset"` thông thường: đưa form về giá trị lúc mở trang, tức là trống trừ các giá trị mặc định.

## 4. Kiểm tra phía trình duyệt
Các ô nhập có `required`, `maxlength`, `min`/`max` tương ứng quy tắc ở back-end. Ô Mã SV và Mã môn có thêm `pattern="\s*[A-Za-z0-9]+\s*"` (BR-02, BR-05; cho phép khoảng trắng hai đầu vì back-end tự cắt), kèm `title` giải thích để trình duyệt hiện khi nhập sai. Ô Email (`type="email"`) có thêm `pattern` theo BR-03, vì `type="email"` vẫn nhận `a@b` (không có dấu chấm). Ô Họ tên và Lớp cũng có `pattern` theo BR-20 (dùng `\p{L}`, `\p{N}`: trình duyệt hiện nay biên dịch `pattern` với cờ `v` nên hiểu được). Đây chỉ là hỗ trợ người dùng; **back-end mới là nơi kiểm tra chính thức**.

## 5. Biểu đồ
- Dữ liệu nhúng vào trang qua `<script type="application/json" id="dashboard-data">` (Jinja `tojson`).
- Chart.js 4.4.9 tải từ `cdn.jsdelivr.net`; không tải được thì mỗi vùng biểu đồ hiện "Không tải được thư viện biểu đồ. Kiểm tra kết nối Internet."
- Sau mỗi thao tác, biểu đồ được cập nhật tại chỗ (`chart.update()`) từ dữ liệu `dashboard-data` của trang mới, có hiệu ứng chuyển.

## 6. Cập nhật tại chỗ (không tải lại trang)
Mã nguồn: khối `<script>` cuối `frontend/templates/index.html`. Phía server vẫn là Post/Redirect/Get, nên khi tắt JavaScript trang hoạt động như cũ (tải lại trang).

**Luồng xử lý**
1. Bắt sự kiện `submit` của mọi form trong `<main>` và `click` của các link có thuộc tính `data-ajax` (Sửa, Hủy ở cả 4 mục; Tất cả). Nút Sửa / Xóa ở hàng nút gọi lại đúng link Sửa / form Xóa của dòng đang chọn (mục 3). Giá trị `data-ajax` là id của mục cần cuộn tới và đặt con trỏ sau khi tải (`students`, `subjects`, `grades`, `tuition`), hoặc `search`. Form xóa thì hiện hộp xác nhận xóa trước (mục 8); người dùng bấm **Hủy** thì không gửi gì. Nếu đang có form nhập dở thì hỏi trước (mục 7).
2. Gửi bằng `fetch` (form POST gửi `FormData` kèm `csrf_token`; form GET và link thì gửi GET). Với POST, `fetch` tự đi theo redirect về `/` (kèm cookie session), nên trang kết quả đã có sẵn thông báo flash.
3. Phân tích HTML trả về bằng `DOMParser`, rồi:
   - luôn thay vùng thông báo `#notices`;
   - nếu **thành công**: thay các vùng `#stats`, `#students`, `#subjects`, `#grades`, `#tuition`, cập nhật 3 biểu đồ, rồi chọn lại các dòng đang chọn còn tồn tại (`syncSelection`);
   - nếu **có lỗi** (trang mới có `.notice.error`): chỉ hiện thông báo, **không** thay các vùng khác, nên form giữ nguyên dữ liệu đã nhập.
4. Giữ vị trí cuộn: đo vị trí của vùng (`section`) chứa form/link vừa dùng trước và sau khi thay nội dung rồi `scrollBy` phần chênh lệch.
5. Địa chỉ trình duyệt:
   - luôn bỏ `message`/`error` còn sót ở link cũ (server không còn đặt chúng lên URL);
   - Tìm kiếm, Sửa, Hủy, Tất cả dùng `history.pushState`, nên nút Back/Forward vẫn quay lại đúng trạng thái (sự kiện `popstate` tải lại nội dung tại chỗ);
   - thao tác ghi dùng `replaceState`;
   - bấm menu (`#students`, `#grades`…) cũng phát `popstate` nhưng chỉ đổi phần `#neo`. Script so đường dẫn mới với nội dung đang hiển thị (`shownPath`); nếu chỉ khác `#neo` thì **không tải lại**, trình duyệt chỉ cuộn trang. Trước đây bước này tải lại các vùng dữ liệu và xóa mọi form đang nhập.
6. Con trỏ: lưu thành công thì đặt vào ô đầu tiên của form vừa dùng để nhập tiếp; bấm Sửa / Hủy thì cuộn tới form của mục đó và đặt vào ô nhập đầu tiên; tìm kiếm hoặc bấm Tất cả thì giữ con trỏ ở ô tìm kiếm của đúng mục vừa dùng.

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
- Form **đang thêm mới**: ô để trống (hoặc ô chọn ở "Chọn …") **không** tính, vì không có dữ liệu để mất. Vì vậy gõ rồi xóa hết, hoặc vừa bấm **Làm mới**, thì không bị hỏi. Gõ lại bất kỳ ô nào thì form lại là "đang nhập dở".
- Form **đang sửa**: xóa trắng một ô cũng tính là thay đổi so với bản ghi.
- Bấm **Sửa** chỉ để xem, không đổi gì, thì form không "nhập dở". Riêng thao tác bấm **Sửa** bản ghi khác thì vẫn hỏi (xem "Chưa hoàn tất sửa thông tin" bên dưới).

**Khi nào hỏi**
| Thao tác | Form được xét |
|---|---|
| Bấm Sửa / Tất cả, tìm kiếm, xóa một dòng | Mọi form nhập dở |
| Đang sửa một bản ghi, bấm **Sửa** bản ghi khác (cùng mục hay mục khác) | Form đang sửa, **kể cả khi chưa đổi gì**, cùng các form nhập dở khác |
| Bấm **Hủy** ở form đang sửa | Các form nhập dở ở mục **khác**. Thay đổi của chính form có nút Hủy bị bỏ luôn, không hỏi, vì việc của nút Hủy là bỏ thay đổi và thoát chế độ sửa |
| Lưu một form | Các form nhập dở **khác**; form đang lưu không tính |
| Back / Forward làm đổi nội dung | Mọi form nhập dở. Địa chỉ được trả về trạng thái đang hiển thị rồi mới hỏi |
| F5, đóng tab, mở liên kết khác (`/health`) | Mọi form nhập dở. Trình duyệt hiện hộp thoại "Rời khỏi trang?" của chính nó (sự kiện `beforeunload`) |
| Bấm menu (`#neo`) | Không hỏi, vì chỉ cuộn trang và không mất gì |

Với thao tác xóa, hộp xác nhận xóa (mục 8) hiện trước. Bấm **Hủy** ở đó thì dừng luôn, không hỏi gì thêm. Chọn dòng, bỏ chọn hay bấm **Làm mới** không làm thay trang nên không hỏi.

**Chưa hoàn tất sửa thông tin**
- Đang sửa mà bấm **Sửa** bản ghi khác thì chế độ sửa hiện tại sẽ bị bỏ, nên luôn hỏi trước, dù đã đổi gì hay chưa.
- Các thao tác khác làm thay trang (xóa, lưu mục khác, tìm kiếm, Tất cả, Back / Forward) chỉ hỏi khi form đang sửa đã có thay đổi (bảng "Khi nào hỏi" ở trên); chưa đổi gì thì thoát chế độ sửa mà không hỏi, vì không có gì để mất ([07](07-han-che.md) L-13).
- Script nhận ra trường hợp này khi link Sửa (`unfinishedEdits`) có tham số sửa khác với form đang sửa.

**Hộp thoại** (`<dialog id="unsaved-dialog">`, mở bằng `showModal()`)
- Liệt kê từng mục, mỗi mục ghi chế độ và các ô đã đổi:
  - **Môn học** (đang thêm mới): Mã môn, Tên môn học
  - **Sinh viên** (đang sửa SV003 — Lê Hoàng Cường): Email
  - **Sinh viên** (đang sửa SV005 — Hoàng Minh Đức): chưa thay đổi gì
- Tiêu đề và lời dẫn đổi theo trường hợp:

| Trường hợp | Tiêu đề | Lời dẫn | Ghi chú cuối |
|---|---|---|---|
| Chỉ có form **đang sửa** | Chưa hoàn tất sửa thông tin | Bạn chưa sửa xong: | Chọn **Không lưu** thì bỏ phần đang sửa, bản ghi giữ nguyên như trước khi sửa. |
| Có form **đang thêm mới** | Dữ liệu đang nhập chưa được lưu | Bạn đang nhập dở ở: | Chọn **Không lưu** thì dữ liệu đang nhập sẽ bị xóa. |

- Ba lựa chọn:

| Lựa chọn | Kết quả |
|---|---|
| **Lưu rồi tiếp tục** (con trỏ mặc định ở nút này) | 0. Form đang sửa mà chưa đổi gì thì không có gì để lưu, không gửi lại.<br>1. Kiểm tra hợp lệ **tất cả** các form cần lưu trước (`checkValidity`). Có form còn thiếu hoặc sai thì không lưu form nào: hiện thông báo "Chưa lưu được mục …", rồi trình duyệt chỉ ra ô cần sửa (`reportValidity`).<br>2. Gửi lần lượt từng form (`fetchPage`, **chưa** thay trang, nên các form khác vẫn giữ dữ liệu).<br>3. Lưu được hết thì làm tiếp thao tác ban đầu. Thông báo của các lần lưu hiện kèm phía trên thông báo của thao tác.<br>4. Một form bị back-end từ chối (ví dụ trùng mã) thì dừng ở form đó và hiện lỗi. Nếu trước đó đã lưu được form nào, trang được tải lại để bảng hiện dữ liệu mới, còn các form chưa lưu được điền lại bản nháp (`refreshKeeping` / `restoreDraft`), giữ nguyên chế độ sửa của chúng. |
| **Không lưu** | Làm tiếp thao tác; dữ liệu đang nhập bị bỏ. |
| **Ở lại nhập tiếp** (hoặc phím Esc) | Không làm gì; cuộn tới và đặt con trỏ vào ô đang nhập dở. |

## 8. Xác nhận xóa
Chọn dòng rồi bấm **Xóa** ở bất kỳ mục nào sẽ hiện hộp thoại của chương trình (`<dialog id="delete-dialog">`, cùng kiểu với mục 7). Chương trình không dùng hộp `confirm()` của trình duyệt, vì hộp đó luôn có dòng tiêu đề "localhost:5000 says" mà trang web không đổi được.

| Bảng | Tiêu đề | Câu hỏi | Ghi chú (chữ đỏ) |
|---|---|---|---|
| Sinh viên | Xác nhận xóa sinh viên | Bạn có chắc muốn xóa sinh viên **<mã> — <họ tên>**? | Toàn bộ điểm và học phí của sinh viên này cũng bị xóa. Thao tác này không thể hoàn tác. |
| Môn học | Xác nhận xóa môn học | Bạn có chắc muốn xóa môn học **<mã môn> — <tên môn>**? | Môn này có N bản ghi điểm, sẽ bị xóa theo. (chỉ khi môn đã có điểm) Thao tác này không thể hoàn tác. |
| Bảng điểm | Xác nhận xóa bản ghi điểm | Bạn có chắc muốn xóa bản ghi điểm **<mã SV> — <họ tên>, môn <mã môn> — <tên môn>, học kỳ <học kỳ>**? | Thao tác này không thể hoàn tác. |
| Học phí | Xác nhận xóa bản ghi học phí | Bạn có chắc muốn xóa bản ghi học phí **<mã SV> — <họ tên>, học kỳ <học kỳ>**? | Thao tác này không thể hoàn tác. |

- Hai nút: **Xóa** (đỏ) gửi yêu cầu xóa; **Hủy** (xám), phím Esc hoặc đóng hộp thoại thì không làm gì.
- Con trỏ mặc định ở nút **Hủy**, nên lỡ nhấn Enter cũng không xóa nhầm.
- Nội dung lấy từ các thuộc tính `data-confirm-what`, `data-confirm-target`, `data-confirm-note` của form xóa. Script đưa vào hộp thoại dưới dạng chữ thuần (`textContent`), nên tên có dấu nháy hay ký tự đặc biệt vẫn hiện đúng.
- Bấm **Xóa** xong, nếu có form ở mục khác đang nhập dở thì hộp thoại ở mục 7 hiện tiếp.
- Đang mở hộp xác nhận mà bấm Back / Forward thì bị bỏ qua, giống mục 7.
- Hộp xác nhận cần JavaScript. Khi tắt JavaScript, bấm Xóa là xóa ngay (NFR-08).
