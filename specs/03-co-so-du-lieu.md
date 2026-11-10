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

Khóa duy nhất `uq_grades (student_id, subject_id, semester)` — dùng cho `INSERT … ON DUPLICATE KEY UPDATE`.

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

Khóa duy nhất `uq_tuition (student_id, semester)`.

> Ràng buộc `amount_paid ≤ amount_due` chỉ được kiểm tra ở back-end, không có CHECK trong DB.

## 6. Giá trị tính toán (không lưu)
| Giá trị | Biểu thức SQL |
|---|---|
| Điểm tổng kết | `ROUND(attendance*0.1 + midterm*0.3 + final*0.6, 2)` |
| Còn nợ | `GREATEST(amount_due - amount_paid, 0)` |

Cột `DECIMAL` được chuyển sang `float` trước khi trả JSON (`db.to_jsonable`).

## 7. Kết nối
- PyMySQL, `DictCursor`, `autocommit=False`, `connect_timeout=5`.
- Cờ `CLIENT.FOUND_ROWS`: `UPDATE` trả về số dòng **khớp** điều kiện, nên lưu sinh viên không đổi gì vẫn được coi là thành công (không bị nhầm thành 404).
- Mỗi request mở một kết nối mới qua `db.transaction()`: commit khi thành công, rollback khi lỗi, luôn đóng kết nối. Không dùng connection pool.
- Khởi động: thử kết nối `DB_CONNECT_RETRIES` lần, cách nhau `DB_CONNECT_DELAY` giây (Docker đặt 30 lần).

## 8. Seed dữ liệu mẫu
Khi khởi động, `init_database()` kiểm tra `information_schema`:
- Database `DB_NAME` **chưa tồn tại**, hoặc tồn tại nhưng **chưa có bảng nào** (vd database rỗng do `MYSQL_DATABASE` của Docker tạo) → tạo database, chạy `schema.sql`, rồi chạy `seed.sql`.
- Database đã có bảng → chỉ chạy `schema.sql` (không đổi dữ liệu), **không seed**.
- Hai file được chạy nguyên khối nhờ cờ `CLIENT.MULTI_STATEMENTS` (chỉ bật cho kết nối khởi tạo).
- Seed chạy trong một transaction; nếu lỗi thì rollback và xóa các bảng vừa tạo để lần khởi động sau seed lại.
- Muốn seed lại từ đầu: xóa database `qlsv` (hoặc `docker compose down -v`) rồi khởi động back-end.
