# 04 — REST API (back-end)

- Địa chỉ mặc định: `http://127.0.0.1:5001`
- Định dạng: JSON UTF-8 (tiếng Việt không bị escape). Body request phải là **JSON object**, nếu không trả 400.
- Mã nguồn: `backend/app.py`.
- Ví dụ trong tài liệu này là phản hồi thật của back-end với [dữ liệu mẫu](03-co-so-du-lieu.md) (`seed.sql`) vừa nạp.

## 1. Xác thực
Nếu biến `API_TOKEN` được đặt, mọi request (trừ `GET /api/health`) phải có header:
```
X-API-Key: <API_TOKEN>
```
Thiếu hoặc sai → `401 {"error": "Thiếu hoặc sai API key."}`. So sánh bằng `secrets.compare_digest`.

## 2. Định dạng phản hồi
| Trường hợp | Body |
|---|---|
| Đọc thành công | object hoặc mảng dữ liệu |
| Ghi thành công | `{"message": "..."}`, khi tạo mới kèm `"id"` |
| Lỗi | `{"error": "..."}` |

| Mã | Ý nghĩa |
|---|---|
| 200 | Thành công |
| 201 | Đã tạo (sinh viên, môn học) |
| 400 | Dữ liệu không hợp lệ, body không phải JSON, dữ liệu quá dài (`DataError`), khóa ngoại không tồn tại |
| 401 | Sai API key |
| 404 | Không tìm thấy bản ghi hoặc route |
| 405 | Sai method |
| 409 | Trùng mã sinh viên / mã môn học; khi sửa, trùng (SV, môn, học kỳ) của điểm hoặc (SV, học kỳ) của học phí |
| 503 | Không kết nối được MySQL |

## 3. Endpoint

### `GET /api/health`
Kiểm tra API và kết nối DB; không cần API key.
- `200 {"status": "ok", "database": "ok"}`
- `503 {"status": "degraded", "database": "error", "detail": "<lỗi MySQL>"}`

---

### `GET /api/students?q=<từ khóa>`
Danh sách sinh viên, `id` giảm dần. `q` (tùy chọn) khớp `LIKE %q%` trên `student_code`, `full_name`, `class_name`.
```json
[{"id": 10, "student_code": "SV010", "full_name": "Ngô Phương Mai", "class_name": "HTTT1", "email": "mai.np@example.edu.vn"}]
```

### `GET /api/students/<id>`
`200` một object sinh viên · `404 "Không tìm thấy sinh viên."`

### `POST /api/students`
```json
{"student_code": "sv011", "full_name": "Nguyễn Thị Thử", "class_name": "CNTT1", "email": "thu.nt@example.edu.vn"}
```
- `201 {"message": "Đã thêm sinh viên.", "id": 11}` (mã lưu thành `SV011`)
- `400 "Vui lòng nhập đủ thông tin hợp lệ."` — xem BR-01…BR-03
- `409 "Mã sinh viên đã tồn tại hoặc dữ liệu không hợp lệ."`

### `PUT /api/students/<id>`
Body và kiểm tra như `POST`. `200 "Đã cập nhật sinh viên."` · `400` · `404` · `409`.

### `DELETE /api/students/<id>`
Xóa sinh viên và (cascade) điểm, học phí. `200 "Đã xóa sinh viên và dữ liệu điểm/học phí liên quan."` · `404`.

---

### `GET /api/subjects`
Danh sách môn học, sắp xếp theo `subject_name`.
```json
[{"id": 2, "subject_code": "INT1002", "subject_name": "Cấu trúc dữ liệu và giải thuật", "credits": 4}]
```

### `POST /api/subjects`
```json
{"subject_code": "int1005", "subject_name": "Lập trình Python", "credits": 3}
```
`credits` tùy chọn (mặc định 3), phải là số nguyên 1–10.
- `201 {"message": "Đã thêm môn học.", "id": 6}` (mã lưu thành `INT1005`)
- `400 "Môn học cần có mã, tên và số tín chỉ từ 1 đến 10."`
- `409 "Mã môn học đã tồn tại."`

### `GET /api/subjects/<id>`
Một môn học. `404 "Không tìm thấy môn học."`

### `PUT /api/subjects/<id>`
Body và kiểm tra giống `POST /api/subjects`.
- `200 "Đã cập nhật môn học."` (kể cả khi dữ liệu không đổi)
- `400 "Môn học cần có mã, tên và số tín chỉ từ 1 đến 10."`
- `404 "Không tìm thấy môn học."`
- `409 "Mã môn học đã tồn tại."`

### `DELETE /api/subjects/<id>`
Xóa môn học và (cascade) mọi bản ghi điểm của môn đó. `deleted_grades` là số bản ghi điểm bị xóa theo.
- `200 {"message": "Đã xóa môn học.", "deleted_grades": 0}`
- `200 {"message": "Đã xóa môn học và 3 bản ghi điểm liên quan.", "deleted_grades": 3}`
- `404 "Không tìm thấy môn học."`

---

### `GET /api/grades`
Bảng điểm kèm thông tin sinh viên, môn học và điểm tổng kết. Sắp xếp `semester DESC, student_code, subject_name`.
```json
[{
  "id": 3, "student_id": 1, "subject_id": 3, "semester": "HK2-2025",
  "attendance": 10.0, "midterm": 8.5, "final": 9.0,
  "student_code": "SV001", "full_name": "Nguyễn Văn An",
  "subject_code": "INT1003", "subject_name": "Cơ sở dữ liệu", "credits": 3,
  "total": 8.95
}]
```

### `POST /api/grades`
Thêm mới, hoặc cập nhật nếu đã có bộ (`student_id`, `subject_id`, `semester`).
```json
{"student_id": 2, "subject_id": 3, "semester": "HK2-2025", "attendance": 9, "midterm": 7.5, "final": 8}
```
- `200 "Đã lưu điểm. Điểm tổng kết được tính theo 10% chuyên cần, 30% giữa kỳ, 60% cuối kỳ."`
- `400 "Điểm phải nằm trong khoảng 0–10 và cần chọn sinh viên, môn học, học kỳ."`
- `400 "Sinh viên hoặc môn học không tồn tại."`

### `GET /api/grades/<id>`
Một bản ghi điểm, cùng các trường như một phần tử của `GET /api/grades`. `404 "Không tìm thấy bản ghi điểm."`

### `PUT /api/grades/<id>`
Sửa bản ghi điểm theo `id`; body và kiểm tra giống `POST /api/grades`. Khác `POST`: được đổi cả `student_id`, `subject_id`, `semester`, và **không** gộp vào bản ghi khác.
- `200 "Đã cập nhật bản ghi điểm."`
- `400 "Điểm phải nằm trong khoảng 0–10 và cần chọn sinh viên, môn học, học kỳ."`
- `400 "Sinh viên hoặc môn học không tồn tại."`
- `404 "Không tìm thấy bản ghi điểm."`
- `409 "Sinh viên này đã có điểm của môn học này trong học kỳ này."` (bộ ba mới trùng với bản ghi khác)

### `DELETE /api/grades/<id>`
`200 "Đã xóa bản ghi điểm."` · `404 "Không tìm thấy bản ghi điểm."`

---

### `GET /api/tuition`
Học phí kèm thông tin sinh viên và số còn nợ. Sắp xếp `semester DESC, student_code`.
```json
[{
  "id": 5, "student_id": 5, "semester": "HK2-2025",
  "amount_due": 9000000.0, "amount_paid": 4500000.0,
  "due_date": "2026-02-28", "note": "Đóng đợt 1",
  "student_code": "SV005", "full_name": "Hoàng Minh Đức", "balance": 4500000.0
}]
```

### `POST /api/tuition`
Thêm mới, hoặc cập nhật nếu đã có bộ (`student_id`, `semester`).
```json
{"student_id": 1, "semester": "HK2-2025", "amount_due": 9000000, "amount_paid": 0, "due_date": "2026-02-28", "note": "Học phí học kỳ"}
```
`amount_paid`, `due_date`, `note` tùy chọn.
- `200 "Đã lưu thông tin học phí."`
- `400 "Học phí không hợp lệ; số đã đóng phải từ 0 đến số phải đóng."`
- `400 "Sinh viên không tồn tại."`

### `GET /api/tuition/<id>`
Một bản ghi học phí, cùng các trường như một phần tử của `GET /api/tuition`. `404 "Không tìm thấy bản ghi học phí."`

### `PUT /api/tuition/<id>`
Sửa bản ghi học phí theo `id`; body và kiểm tra giống `POST /api/tuition`, được đổi cả `student_id`, `semester`.
- `200 "Đã cập nhật thông tin học phí."`
- `400 "Học phí không hợp lệ; số đã đóng phải từ 0 đến số phải đóng."`
- `400 "Sinh viên không tồn tại."`
- `404 "Không tìm thấy bản ghi học phí."`
- `409 "Sinh viên này đã có bản ghi học phí cho học kỳ này."`

### `DELETE /api/tuition/<id>`
`200 "Đã xóa bản ghi học phí."` · `404 "Không tìm thấy bản ghi học phí."`

---

### `GET /api/stats`
Số liệu cho dashboard.
```json
{
  "total": 10, "subject_count": 5, "grade_count": 18, "tuition_balance": 31500000.0,
  "chart_data": {
    "gradeLabels": ["Giỏi", "Khá", "Cần cố gắng", "Trung bình"], "gradeValues": [7, 7, 3, 1],
    "classLabels": ["CNTT1", "CNTT2", "HTTT1", "KTPM1"], "classValues": [3, 3, 2, 2],
    "tuitionDue": 87000000.0, "tuitionPaid": 55500000.0, "tuitionBalance": 31500000.0
  }
}
```
- `gradeLabels/Values`: số bản ghi điểm theo xếp loại (BR-10); chỉ có nhãn xuất hiện trong dữ liệu, thứ tự không cố định (xem [07](07-han-che.md) L-02).
- `classLabels/Values`: tối đa 8 lớp, sắp theo số sinh viên giảm dần rồi tên lớp.
- `tuition*`: tổng trên toàn bảng `tuition`; số dư mỗi bản ghi không âm.

## 4. Ví dụ gọi nhanh (PowerShell)
Thêm → xem → sửa → xóa một sinh viên thử. Chạy được nhiều lần trên dữ liệu mẫu, không đụng tới dữ liệu có sẵn.
```powershell
$api  = 'http://127.0.0.1:5001'
$json = 'application/json; charset=utf-8'    # phải có charset=utf-8 để gửi đúng tiếng Việt

(Invoke-RestMethod "$api/api/students?q=CNTT1").Count          # số sinh viên khớp từ khóa

$r = Invoke-RestMethod "$api/api/students" -Method Post -ContentType $json `
  -Body '{"student_code":"sv011","full_name":"Nguyễn Thị Thử","class_name":"CNTT1","email":"thu.nt@example.edu.vn"}'
$r.id                                                            # id của sinh viên vừa thêm

Invoke-RestMethod "$api/api/students/$($r.id)" -Method Put -ContentType $json `
  -Body '{"student_code":"SV011","full_name":"Nguyễn Thị Thử","class_name":"CNTT2","email":"thu.nt@example.edu.vn"}'

Invoke-RestMethod "$api/api/students/$($r.id)" -Method Delete
```
- Lỗi (4xx/5xx) làm `Invoke-RestMethod` ném ngoại lệ; mã HTTP nằm ở `$_.Exception.Response.StatusCode` trong khối `catch`.
- Phản hồi có `Content-Type: application/json` **không kèm** `charset`. Vì vậy Windows PowerShell 5.1 hiển thị sai tiếng Việt trong kết quả (ví dụ `ÄÃ£ thÃªm sinh viÃªn.`), dù dữ liệu gửi lên và lưu trong DB vẫn đúng. Xem JSON bằng trình duyệt nếu cần đọc tiếng Việt (xem [07](07-han-che.md) L-14).
