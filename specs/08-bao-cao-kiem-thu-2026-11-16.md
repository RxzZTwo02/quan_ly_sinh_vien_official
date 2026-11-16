# Báo cáo kiểm thử: Chương trình quản lý sinh viên

- **Ngày kiểm thử:** 16/11/2026
- **Ứng dụng:** Web quản lý sinh viên (Flask + MySQL), nhánh `expansion`, commit `92f992d`
- **Người dùng của chương trình:** chỉ giảng viên, dùng để quản lý sinh viên, môn học, điểm và học phí
- **Phạm vi kiểm thử:** chức năng quản lý sinh viên (thêm, sửa, xóa, tìm kiếm), lỗi console/network

Tài liệu có hai phần:

- **Phần A** giải thích các lỗi.
- **Phần B** liệt kê lại bằng thuật ngữ chuyên ngành, dành cho người sửa chương trình.

> Báo cáo được giữ nguyên như lúc kiểm thử. Cách khắc phục từng lỗi (BUG-01 … BUG-09) ghi ở [07-han-che.md](07-han-che.md) mục 3.

---

# Phần A. Giải thích các lỗi

## Chương trình này là gì?

Hãy tưởng tượng chương trình là một **cuốn sổ điện tử của thầy cô**. Trong sổ có tên các bạn học sinh, mã số của từng bạn, lớp và địa chỉ email. Thầy cô có thể **viết thêm** một bạn mới, **sửa** thông tin, **gạch bỏ** một bạn, hoặc **tìm** một bạn trong sổ.

## Chúng tôi đã làm gì?

Chúng tôi đóng vai một người dùng "tinh nghịch": cố tình viết đúng, viết sai, viết thiếu, viết quá dài, viết ký hiệu lạ vào cuốn sổ, rồi xem cuốn sổ có xử lý đúng không. Chúng tôi thử **39 việc**. **33 việc cuốn sổ làm tốt**, 3 việc làm chưa đúng, và 3 việc thuộc phần sẽ làm trong tương lai.

## Những điều cuốn sổ làm tốt

- Không cho viết hai bạn trùng một mã số, kể cả khi viết chữ hoa, chữ thường khác nhau.
- Không cho để trống ô nào.
- Không cho viết quá dài.
- Khi gạch bỏ một bạn, sổ luôn hỏi lại "Bạn có chắc không?".
- Kẻ xấu viết "câu thần chú" của máy tính vào sổ cũng không làm hỏng được sổ.
- Bấm nút lưu liên tục nhiều lần cũng chỉ ghi một lần.

## Những lỗi tìm thấy (9 lỗi, không có lỗi nghiêm trọng)

**Lỗi 1: Mã số học sinh viết kiểu gì cũng được.**
Mã số học sinh lẽ ra chỉ gồm chữ và số, như `SV001`. Nhưng sổ vẫn nhận cả mã `-1` (số âm), mã có dấu cách ở giữa như `QA 013`, hay mã có ký hiệu lạ như `QA/014`. Giống như thẻ thư viện mà ghi số âm thì thật kỳ lạ.

**Lỗi 2: Email sai mà sổ vẫn nhận.**
Một email đúng phải có dạng `ten@trang.com`. Trên màn hình, sổ chặn được email sai. Nhưng nếu ai đó "đi cửa sau" gửi thẳng dữ liệu vào, sổ nhận cả email chỉ có mỗi dấu `@`. Giống như phong bì chỉ ghi "@" thì bưu tá không biết gửi đi đâu.

**Lỗi 3: Tìm kiếm bị "nhầm" với một vài ký hiệu.**
Khi gõ dấu `%` hoặc `_` vào ô tìm, sổ hiểu đó là "tìm tất cả" chứ không phải tìm đúng dấu đó. Giống như bạn hỏi "Ai tên là dấu sao?" mà cả lớp cùng giơ tay.

**Lỗi 4: Chương trình có lúc không chịu khởi động.**
Nếu bật chương trình theo cách ghi nhật ký ra một tệp, chương trình bị "vấp" ở chữ tiếng Việt có dấu và dừng lại ngay. Giống như máy in chỉ in được tiếng Anh, gặp chữ "ữ" là kẹt giấy.

**Lỗi 5: Có thể làm giả thông báo.**
Ai đó có thể gửi cho thầy cô một đường link đặc biệt. Bấm vào thì chương trình hiện một thông báo giả, ví dụ "Tài khoản của bạn đã bị khóa, gọi số này…". Thông báo trông như thật dù chương trình không hề nói vậy. Giống như ai đó dán một tờ giấy giả lên bảng tin của trường.

**Lỗi 6: Họ tên viết linh tinh vẫn được nhận.**
Họ tên `12345 !@#$%` vẫn được lưu, dù không ai tên như vậy.

**Lỗi 7: Chữ quá dài làm bảng bị tràn.**
Nếu một tên rất dài và không có dấu cách, bảng bị kéo rộng ra ngoài màn hình. Phải kéo ngang mới thấy cột Lớp và Email. Giống như một cái tên dài đến mức không vừa tờ giấy.

**Lỗi 8: Báo lỗi không nói rõ sai ở đâu.**
Khi viết sai, sổ chỉ nói "Vui lòng nhập đủ thông tin hợp lệ." mà không nói ô nào sai. Giống như cô giáo nói "Bài em sai rồi" mà không chỉ sai ở câu nào.

**Lỗi 9: Một vài trang báo lỗi bằng tiếng Anh.**
Khi có người cố tình gửi dữ liệu kỳ lạ, chương trình hiện trang báo lỗi bằng tiếng Anh ("Bad Request"), trong khi mọi chỗ khác đều là tiếng Việt.

## Điều sẽ làm trong tương lai: đăng nhập và phân quyền

Hiện tại cuốn sổ **không có ổ khóa**. Ai mở được máy tính thì xem và sửa được hết. Điều này **không phải lỗi**, vì chương trình được làm đơn giản và **chỉ dành cho giảng viên** dùng. Sau này nhóm sẽ thêm "ổ khóa" (đăng nhập), và mỗi người sẽ có "chìa khóa" riêng. Ví dụ học sinh chỉ được xem điểm của chính mình và không được sửa.

---

# Phần B. Chi tiết kỹ thuật

## 1. Tóm tắt

| | Số lượng |
|---|---|
| Test case đã chạy | 39 |
| PASS | 33 |
| Không PASS | 3 (TC-09, TC-13, TC-43) |
| Ngoài phạm vi (định hướng phát triển) | 3 (TC-50, TC-51, TC-53) |
| Lỗi phát hiện | 9 (0 nghiêm trọng, 4 trung bình, 5 nhẹ) |

- **Console:** không có lỗi JavaScript nào trong suốt quá trình kiểm thử.
- **Network:** không có lỗi 5xx. Các mã 400/404/405 chỉ xuất hiện ở những request cố tình gửi sai.
- **Phạm vi người dùng:** chương trình chỉ dành cho giảng viên, nên đăng nhập và phân quyền không được tính là lỗi. Hai nội dung này được chuyển sang mục 4 (Định hướng phát triển).

## 2. Môi trường

| Thành phần | Giá trị |
|---|---|
| Hệ điều hành | Windows 11 |
| Trình duyệt | Google Chrome + tiện ích Claude in Chrome |
| Front-end | `http://localhost:5000` |
| Back-end API | `http://127.0.0.1:5001` |
| Cơ sở dữ liệu | MySQL `127.0.0.1:3306`, database `qlsv` |
| Dữ liệu ban đầu | 10 sinh viên (SV001–SV010), 5 môn học, 18 bản ghi điểm, học phí còn nợ 31.500.000 đ |

**Cách kiểm thử:** thao tác trên giao diện (gõ, bấm, chuột phải), kết hợp gửi request thẳng từ trang có CSRF token hợp lệ. Cách này để vượt qua kiểm tra phía trình duyệt (`maxlength`, `type=email`). Không sửa code.

## 3. Danh sách lỗi

Mức độ:
- **Nghiêm trọng:** vi phạm quy tắc nghiệp vụ hoặc làm mất dữ liệu.
- **Trung bình:** chức năng chạy sai trong một số trường hợp.
- **Nhẹ:** giao diện, thông báo, trải nghiệm.

| Mã lỗi | Chức năng | Các bước tái hiện | Kết quả mong đợi | Kết quả thực tế | Mức độ |
|---|---|---|---|---|---|
| BUG-01 | Thêm/Sửa: Mã sinh viên | Thêm sinh viên với Mã SV lần lượt là: `-1`, `QA 013`, `QA/014`, `QA%015`, `QA<SCRIPT>`, `QA' OR 1=1--` (các ô khác hợp lệ). | Bị từ chối: mã chỉ gồm chữ và số, không âm, không có khoảng trắng hay ký tự đặc biệt. | Cả 6 mã đều được lưu. Ô nhập chỉ có `maxlength="20"` và `required`, không có `pattern`. Back-end chỉ kiểm tra độ dài. | Trung bình |
| BUG-02 | Thêm/Sửa: Email | Gửi form thêm sinh viên (POST `/save`, CSRF hợp lệ) với email lần lượt là `@`, `a@`, `qa mail @ x y`. | Bị từ chối vì email sai định dạng. | Cả 3 đều được lưu, vì back-end chỉ kiểm tra email có ký tự `@` (L-04). Trên giao diện, ô `type=email` chặn được, nhưng gửi request trực tiếp thì không. Hậu quả: khi mở bản ghi này ra sửa, trình duyệt chặn nút "Lưu thay đổi" cho tới khi người dùng sửa lại email. | Trung bình |
| BUG-03 | Tìm kiếm | 1. Có các sinh viên mã `QA_016`, `QA%015`, `QA/014`, `QA 013`, `QA001A`.<br>2. Tìm `%`.<br>3. Tìm `_`.<br>4. Tìm `QA_0`. | `%` và `_` được tìm như ký tự thường. Tìm `QA_0` chỉ ra `QA_016`. | Tìm `%` ra 32/32 sinh viên; tìm `_` cũng ra 32/32. Tìm `QA_0` ra 5 dòng: `QA_016`, `QA%015`, `QA/014`, `QA 013`, `QA001A`. Ký tự `%`, `_`, `\` trong từ khóa bị hiểu là ký tự đại diện của SQL `LIKE`. | Trung bình |
| BUG-04 | Khởi động back-end (ngoài phạm vi, phát hiện khi chuẩn bị môi trường) | Trên Windows, chạy back-end với đầu ra chuyển ra file hoặc pipe, ví dụ `python app.py > log.txt` trong thư mục `backend`. | Server khởi động bình thường. | Crash ngay khi khởi động: `UnicodeEncodeError: 'charmap' codec can't encode character…` tại lệnh `print` tiếng Việt. Chạy với `PYTHONIOENCODING=utf-8` thì bình thường. | Trung bình |
| BUG-05 | Thông báo trên trang | Mở URL: `http://localhost:5000/?error=Tài khoản của bạn đã bị khóa. Gọi 0900000000 để mở khóa.` | Thông báo chỉ do chính server tạo ra sau một thao tác. | Nội dung bất kỳ trên URL hiện thành thông báo đỏ (`error`) hoặc xanh (`message`), giống thông báo thật của hệ thống (content spoofing). Nội dung đã được escape nên không chạy được script. | Nhẹ |
| BUG-06 | Thêm/Sửa: Họ tên | Thêm sinh viên có họ tên `12345 !@#$%^&*()`, hoặc họ tên có ký tự xuống dòng. | Bị từ chối vì họ tên không hợp lệ. | Được lưu. Họ tên và lớp không bị kiểm tra ký tự. | Nhẹ |
| BUG-07 | Giao diện bảng sinh viên | Thêm sinh viên có họ tên 100 ký tự liền nhau không khoảng trắng (hoặc lớp 50, email 120 ký tự), xem bảng danh sách. | Chữ tự xuống dòng, bảng vừa khung. | Chữ không xuống dòng, bảng rộng 2541px trong khung 1234px. Cột Lớp và Email bị đẩy ra ngoài màn hình, phải cuộn ngang. | Nhẹ |
| BUG-08 | Thông báo lỗi khi nhập sai | 1. Thêm sinh viên có họ tên chỉ gồm khoảng trắng.<br>2. Thêm sinh viên có lớp 51 ký tự.<br>3. Thêm sinh viên trùng mã. | Báo rõ ô nào sai và sai thế nào. | Trường hợp 1 và 2 đều báo chung "Vui lòng nhập đủ thông tin hợp lệ.". Trường hợp 3 báo "Mã sinh viên đã tồn tại **hoặc** dữ liệu không hợp lệ.", không rõ là lỗi nào. | Nhẹ |
| BUG-09 | Sửa/Xóa khi request bị sửa tay | 1. Gửi form `/save` với trường ẩn `id=abc` hoặc `id=-5`.<br>2. Gửi `POST /delete/-1`. | Thông báo lỗi bằng tiếng Việt trong giao diện của ứng dụng. | Hiện trang lỗi mặc định của Flask bằng tiếng Anh ("Bad Request", "Not Found"), trái với NFR-01. Người dùng bình thường ít gặp. | Nhẹ |

### Vị trí trong code liên quan

| Mã lỗi | Vị trí |
|---|---|
| BUG-01, BUG-02, BUG-06 | `backend/app.py`, hàm `validate_student` (dòng 111); ô nhập trong `frontend/templates/index.html` (dòng 623–638) |
| BUG-03 | `backend/app.py`, hàm `list_students` (dòng 123–128). `keyword_filter` (dòng 53) của Môn học, Bảng điểm, Học phí cũng ghép `LIKE` theo cách này |
| BUG-04 | `backend/db.py`, các lệnh `print` tiếng Việt (dòng 102–134), crash tại dòng 117 |
| BUG-05 | `frontend/app.py`, hàm `index` đọc `error` / `message` từ URL (dòng 153, 180) |
| BUG-09 | `frontend/app.py`, `abort(400)` trong `save_record` (dòng 90); chưa có trang lỗi 400/404 riêng |

## 4. Định hướng phát triển trong tương lai: đăng nhập và phân quyền

Chương trình hiện chỉ dành cho giảng viên, nên chưa có đăng nhập và phân quyền. Kết quả kiểm thử ghi nhận để làm cơ sở phát triển sau này, **không tính là lỗi**:

| Nội dung | Hiện trạng | Hướng phát triển |
|---|---|---|
| Đăng nhập | Không có trang đăng nhập (`/login`, `/admin` trả 404). Ai mở được trang đều có toàn quyền thêm, sửa, xóa. | Thêm đăng nhập cho giảng viên (Flask-Login hoặc session tự viết), bắt buộc trước khi đưa chương trình lên mạng. |
| Phân quyền theo vai trò | Chưa có vai trò người dùng. | Thêm vai trò giảng viên / sinh viên. Sinh viên chỉ xem được điểm của chính mình, không được sửa. |
| Bảo vệ API back-end | `API_TOKEN` để trống nên `GET http://127.0.0.1:5001/api/students` trả 200 khi không có khóa. API chỉ nghe ở `127.0.0.1` và không bật CORS, nên trang web khác không gọi được từ trình duyệt. | Đặt `API_TOKEN` giống nhau trong `backend/.env` và `frontend/.env`. |

Tài liệu `specs/07-han-che.md` đã ghi nội dung này (L-10, hướng cải tiến số 3).

## 5. Danh sách test case và kết quả

### A. Thêm sinh viên

| TC | Nội dung | Kết quả |
|---|---|---|
| TC-01 | Thêm hợp lệ | PASS: thông báo xanh, dòng mới ở đầu bảng, KPI tăng 10 → 11, F5 vẫn còn |
| TC-02 | Bỏ trống từng ô | PASS: trình duyệt chặn, không gửi request |
| TC-03 | Họ tên chỉ có khoảng trắng | PASS: bị từ chối, form giữ dữ liệu (thông báo chung chung, xem BUG-08) |
| TC-04 | Mã chữ thường `qa002` | PASS: lưu thành `QA002` |
| TC-05 | Khoảng trắng đầu/cuối | PASS: bị cắt bỏ |
| TC-06 | Trùng mã | PASS: báo "Mã sinh viên đã tồn tại…" |
| TC-07 | Trùng mã khác hoa/thường, có khoảng trắng | PASS: vẫn báo trùng |
| TC-08 | Biên độ dài: mã 20/21, họ tên 100/101, lớp 50/51, email 120/121 | PASS (bảng bị tràn, xem BUG-07) |
| TC-09 | Email sai định dạng | **KHÔNG PASS** (BUG-02) |
| TC-10 | HTML/XSS ở các ô | PASS: hiển thị dạng chữ, không chạy script |
| TC-11 | Chuỗi SQL injection | PASS: lưu nguyên văn, không lỗi |
| TC-12 | Tiếng Việt có dấu, emoji | PASS |
| TC-13 | Mã SV bất thường; họ tên chỉ có ký hiệu | **KHÔNG PASS** (BUG-01, BUG-06) |
| TC-14 | Bấm lưu 3 lần liên tiếp | PASS: chỉ 1 request, 1 bản ghi |
| TC-15 | Nút Làm mới | PASS |

### B. Sửa sinh viên

| TC | Nội dung | Kết quả |
|---|---|---|
| TC-20 | Chuột phải chọn dòng → Sửa | PASS: tiêu đề "Cập nhật sinh viên", dòng lên đầu và tô vàng |
| TC-21 | Sửa hợp lệ | PASS: mã tự in hoa, F5 xác nhận |
| TC-22 | Sửa sang mã đã có | PASS: báo trùng, giữ dữ liệu đã nhập |
| TC-23 | Lưu khi không đổi gì | PASS |
| TC-24 | Xóa trống ô khi sửa | PASS: trình duyệt chặn |
| TC-25 | Hủy | PASS: không lưu, không hỏi lại |
| TC-26 | `?edit=` id sai | PASS: báo "Không tìm thấy sinh viên cần sửa." |
| TC-27 | Form sửa có id giả mạo | PASS (trang lỗi tiếng Anh, xem BUG-09) |

### C. Xóa sinh viên

| TC | Nội dung | Kết quả |
|---|---|---|
| TC-30 | Hộp xác nhận → Hủy | PASS: không gửi request |
| TC-31 | Xác nhận xóa | PASS: KPI giảm, F5 xác nhận |
| TC-32 | Xóa sinh viên có điểm và học phí | PASS: xóa kèm, dữ liệu khác không đổi |
| TC-33 | Xóa id không tồn tại | PASS: báo "Không tìm thấy sinh viên." |
| TC-34 | Bỏ chọn dòng | PASS: nút Sửa/Xóa bị vô hiệu |

### D. Tìm kiếm

| TC | Nội dung | Kết quả |
|---|---|---|
| TC-40 | Tìm theo mã, họ tên (có dấu và không dấu), lớp | PASS |
| TC-41 | Từ khóa rỗng / chỉ khoảng trắng | PASS: hiện tất cả |
| TC-42 | Không có kết quả | PASS: "Chưa có sinh viên phù hợp." |
| TC-43 | Ký tự `%`, `_` | **KHÔNG PASS** (BUG-03) |
| TC-44 | SQL injection, HTML trong ô tìm | PASS |
| TC-45 | Từ khóa 5000 ký tự | PASS |
| TC-46 | Giữ kết quả khi Sửa/Hủy; nút Tất cả | PASS |

### E. Phân quyền và bảo mật

| TC | Nội dung | Kết quả |
|---|---|---|
| TC-50 | Truy cập khi chưa đăng nhập | Ngoài phạm vi (mục 4) |
| TC-51 | Sinh viên chỉ xem điểm của mình | Ngoài phạm vi (mục 4) |
| TC-52 | POST thiếu hoặc sai CSRF token | PASS: trả 400, không ghi dữ liệu |
| TC-53 | Gọi API back-end không có khóa | Ngoài phạm vi (mục 4) |

## 6. Dữ liệu kiểm thử và dọn dẹp

- Dữ liệu kiểm thử có mã bắt đầu bằng `QA` (một bản ghi có mã `-1`): 24 sinh viên, 1 bản ghi điểm, 1 bản ghi học phí.
- Không sửa hoặc xóa dữ liệu có sẵn.
- Sau kiểm thử, đã xóa toàn bộ dữ liệu kiểm thử. Database `qlsv` trở về đúng trạng thái ban đầu: 10 sinh viên SV001–SV010 không thay đổi, 5 môn học, 18 bản ghi điểm, còn nợ 31.500.000 đ.
