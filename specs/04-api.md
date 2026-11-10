# 04 — REST API (back-end)

- Địa chỉ mặc định: `http://127.0.0.1:5001`
- Định dạng: JSON UTF-8 (tiếng Việt không bị escape). Body request phải là **JSON object**, nếu không trả 400.
- Mã nguồn: `backend/app.py`.

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
| 409 | Trùng mã sinh viên / mã môn học |
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
[{"id": 3, "student_code": "SV003", "full_name": "Lê Thị C", "class_name": "CNTT01", "email": "c@example.com"}]
```

### `GET /api/students/<id>`
`200` một object sinh viên · `404 "Không tìm thấy sinh viên."`

### `POST /api/students`
```json
{"student_code": "sv004", "full_name": "Phạm Văn D", "class_name": "CNTT02", "email": "d@example.com"}
```
- `201 {"message": "Đã thêm sinh viên.", "id": 4}` (mã lưu thành `SV004`)
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
[{"id": 1, "subject_code": "CS101", "subject_name": "Cơ sở dữ liệu", "credits": 3}]
```

### `POST /api/subjects`
```json
{"subject_code": "cs102", "subject_name": "Lập trình Python", "credits": 3}
```
`credits` tùy chọn (mặc định 3), phải là số nguyên 1–10.
- `201 {"message": "Đã thêm môn học.", "id": 2}`
- `400 "Môn học cần có mã, tên và số tín chỉ từ 1 đến 10."`
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
  "id": 1, "student_id": 3, "subject_id": 1, "semester": "2026-1",
  "attendance": 9.0, "midterm": 7.5, "final": 8.0,
  "student_code": "SV003", "full_name": "Lê Thị C",
  "subject_code": "CS101", "subject_name": "Cơ sở dữ liệu", "credits": 3,
  "total": 8.05
}]
```

### `POST /api/grades`
Thêm mới, hoặc cập nhật nếu đã có bộ (`student_id`, `subject_id`, `semester`).
```json
{"student_id": 3, "subject_id": 1, "semester": "2026-1", "attendance": 9, "midterm": 7.5, "final": 8}
```
- `200 "Đã lưu điểm. Điểm tổng kết được tính theo 10% chuyên cần, 30% giữa kỳ, 60% cuối kỳ."`
- `400 "Điểm phải nằm trong khoảng 0–10 và cần chọn sinh viên, môn học, học kỳ."`
- `400 "Sinh viên hoặc môn học không tồn tại."`

### `DELETE /api/grades/<id>`
`200 "Đã xóa bản ghi điểm."` · `404 "Không tìm thấy bản ghi điểm."`

---

### `GET /api/tuition`
Học phí kèm thông tin sinh viên và số còn nợ. Sắp xếp `semester DESC, student_code`.
```json
[{
  "id": 1, "student_id": 3, "semester": "2026-1",
  "amount_due": 8000000.0, "amount_paid": 5000000.0,
  "due_date": "2026-12-31", "note": "Học phí học kỳ",
  "student_code": "SV003", "full_name": "Lê Thị C", "balance": 3000000.0
}]
```

### `POST /api/tuition`
Thêm mới, hoặc cập nhật nếu đã có bộ (`student_id`, `semester`).
```json
{"student_id": 3, "semester": "2026-1", "amount_due": 8000000, "amount_paid": 5000000, "due_date": "2026-12-31", "note": "Học phí học kỳ"}
```
`amount_paid`, `due_date`, `note` tùy chọn.
- `200 "Đã lưu thông tin học phí."`
- `400 "Học phí không hợp lệ; số đã đóng phải từ 0 đến số phải đóng."`
- `400 "Sinh viên không tồn tại."`

---

### `GET /api/stats`
Số liệu cho dashboard.
```json
{
  "total": 12, "subject_count": 5, "grade_count": 30, "tuition_balance": 15000000.0,
  "chart_data": {
    "gradeLabels": ["Giỏi", "Khá"], "gradeValues": [10, 20],
    "classLabels": ["CNTT01", "CNTT02"], "classValues": [7, 5],
    "tuitionDue": 96000000.0, "tuitionPaid": 81000000.0, "tuitionBalance": 15000000.0
  }
}
```
- `gradeLabels/Values`: số bản ghi điểm theo xếp loại (BR-10); chỉ có nhãn xuất hiện trong dữ liệu.
- `classLabels/Values`: tối đa 8 lớp, sắp theo số sinh viên giảm dần rồi tên lớp.
- `tuition*`: tổng trên toàn bảng `tuition`; số dư mỗi bản ghi không âm.

## 4. Ví dụ gọi nhanh (PowerShell)
```powershell
Invoke-RestMethod http://127.0.0.1:5001/api/students
Invoke-RestMethod http://127.0.0.1:5001/api/students -Method Post -ContentType 'application/json; charset=utf-8' `
  -Body '{"student_code":"SV010","full_name":"Nguyen Van A","class_name":"CNTT01","email":"a@example.com"}'
```
