# 03 — Cơ sở dữ liệu

- Hệ quản trị: MySQL 8, engine InnoDB, bảng mã `utf8mb4` / `utf8mb4_unicode_ci`.
- Database mặc định: `qlsv`, do back-end tự tạo (`CREATE DATABASE IF NOT EXISTS`) khi khởi động.
- Lược đồ khai báo trong `backend/sql/schema.sql`, dùng `CREATE TABLE IF NOT EXISTS`, chạy mỗi lần back-end khởi động; **không có cơ chế migration** nên đổi cột phải sửa DB thủ công.
- Dữ liệu mẫu trong `backend/sql/seed.sql` (10 sinh viên, 5 môn, 18 điểm, 10 học phí), xem mục 8.

## 1. Sơ đồ quan hệ
```
students 1 ──< grades >── 1 subjects
students 1 ──< tuition
```
Xóa sinh viên hoặc môn học sẽ xóa dây chuyền (`ON DELETE CASCADE`) các bản ghi điểm / học phí liên quan.

## 2. Bảng `students`
| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT |
| `student_code` | VARCHAR(20) | NOT NULL, UNIQUE |
| `full_name` | VARCHAR(100) | NOT NULL |
| `class_name` | VARCHAR(50) | NOT NULL |
| `email` | VARCHAR(120) | NOT NULL |

## 3. Bảng `subjects`
| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT |
| `subject_code` | VARCHAR(20) | NOT NULL, UNIQUE |
| `subject_name` | VARCHAR(120) | NOT NULL |
| `credits` | INT | NOT NULL, DEFAULT 3, CHECK `credits > 0` |

## 4. Bảng `grades`
| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT |
| `student_id` | INT | NOT NULL, FK → `students.id` ON DELETE CASCADE |
| `subject_id` | INT | NOT NULL, FK → `subjects.id` ON DELETE CASCADE |
| `semester` | VARCHAR(20) | NOT NULL |
| `attendance` | DOUBLE | NOT NULL, DEFAULT 0, CHECK 0–10 |
| `midterm` | DOUBLE | NOT NULL, DEFAULT 0, CHECK 0–10 |
| `final` | DOUBLE | NOT NULL, DEFAULT 0, CHECK 0–10 |

Khóa duy nhất `uq_grades (student_id, subject_id, semester)`:
- khi thêm (`POST /api/grades`), dùng cho `INSERT … ON DUPLICATE KEY UPDATE`, nên bộ ba đã có điểm thì được cập nhật;
- khi sửa (`PUT /api/grades/<id>`), `UPDATE` vi phạm khóa này (lỗi MySQL 1062) được trả về `409` (BR-17).

## 5. Bảng `tuition`
| Cột | Kiểu | Ràng buộc |
|---|---|---|
| `id` | INT | PK, AUTO_INCREMENT |
| `student_id` | INT | NOT NULL, FK → `students.id` ON DELETE CASCADE |
| `semester` | VARCHAR(20) | NOT NULL |
| `amount_due` | DECIMAL(15,2) | NOT NULL, CHECK ≥ 0 |
| `amount_paid` | DECIMAL(15,2) | NOT NULL, DEFAULT 0, CHECK ≥ 0 |
| `due_date` | VARCHAR(10) | NOT NULL, DEFAULT `''` |
| `note` | VARCHAR(200) | NOT NULL, DEFAULT `''` |

Khóa duy nhất `uq_tuition (student_id, semester)`, dùng giống `uq_grades`:
- `POST` thì cập nhật bản ghi đã có;
- `PUT` trùng với bản ghi khác thì trả `409` (BR-18).

> Ràng buộc `amount_paid ≤ amount_due` chỉ được kiểm tra ở back-end, không có CHECK trong DB.

## 6. Giá trị tính toán (không lưu)
| Giá trị | Biểu thức SQL |
|---|---|
| Điểm tổng kết | `ROUND(attendance*0.1 + midterm*0.3 + final*0.6, 2)` |
| Còn nợ | `GREATEST(amount_due - amount_paid, 0)` |

Cột `DECIMAL` được chuyển sang `float` trước khi trả JSON (`db.to_jsonable`).

## 7. Kết nối
- PyMySQL, `DictCursor`, `autocommit=False`, `connect_timeout=5`.
- Cờ `CLIENT.FOUND_ROWS`: `UPDATE` trả về số dòng **khớp** điều kiện. Vì vậy bấm **Lưu thay đổi** mà không đổi gì (ở cả 4 mục) vẫn được coi là thành công, không bị nhầm thành 404.
- Lỗi `IntegrityError` được xử lý như sau:
  - Sinh viên và môn học: mọi lỗi đều là trùng mã → `409`.
  - Điểm và học phí: phân loại theo mã lỗi MySQL (hằng số trong `db.py`):
    - `1062` (`ER_DUP_ENTRY`, trùng khóa UNIQUE) → `409`;
    - `1452` (`ER_NO_REFERENCED_ROW`, khóa ngoại trỏ tới bản ghi không tồn tại) và các lỗi khác → `400`.
- Mỗi request mở một kết nối mới qua `db.transaction()`: commit khi thành công, rollback khi lỗi, luôn đóng kết nối. Không dùng connection pool.
- Khởi động: thử kết nối `DB_CONNECT_RETRIES` lần, cách nhau `DB_CONNECT_DELAY` giây (Docker đặt 30 lần).

## 8. Seed dữ liệu mẫu
Khi khởi động, `init_database()`:
1. Tạo database `DB_NAME` nếu chưa có và chạy `schema.sql` (`IF NOT EXISTS`, không đổi dữ liệu đã có).
2. Kiểm tra dữ liệu: database **rỗng** khi cả 4 bảng `students`, `subjects`, `grades`, `tuition` đều chưa có dòng nào (gồm cả database vừa tạo, hay database rỗng do `MYSQL_DATABASE` của Docker tạo). Bảng khác trong database không được tính.
3. Database đã có dữ liệu → giữ nguyên, **không đọc** `seed.sql`, in `Dùng dữ liệu hiện có…`.
4. Database rỗng → `SEED_DATA=yes` (mặc định) thì chạy `seed.sql`; `SEED_DATA=no` thì để trống. Giá trị khác `yes`/`no` → back-end dừng và báo lỗi.

- Hai file được chạy nguyên khối nhờ cờ `CLIENT.MULTI_STATEMENTS` (chỉ bật cho kết nối khởi tạo).
- `seed.sql` chạy trong **một** transaction: lỗi hay bị ngắt giữa chừng (Ctrl+C, mất kết nối) thì không dòng nào được lưu, database vẫn rỗng và lần khởi động sau nạp lại. Vì vậy file chỉ được chứa lệnh `INSERT` (bảng cha trước bảng con), không có DDL hay `START TRANSACTION` / `COMMIT`.
- Nạp vào bảng rỗng nên các `id` cố định trong `seed.sql` không thể trùng dữ liệu có sẵn.
- Với `SEED_DATA=yes`, xóa hết dữ liệu rồi khởi động lại thì dữ liệu mẫu được nạp lại.
- Quay về trạng thái gốc: dừng back-end, xóa database `qlsv` (hoặc `docker compose down -v`), khởi động lại; có dữ liệu mẫu hay không tùy `SEED_DATA`.
