-- Dữ liệu mẫu QLSV. Back-end chỉ nạp file này khi database rỗng (cả 4 bảng chưa có dòng nào)
-- và SEED_DATA=yes (mặc định). Database đã có dữ liệu thì file này không được đọc tới.
-- Cả file chạy trong MỘT transaction nên chỉ được chứa lệnh INSERT: không CREATE/ALTER/DROP/TRUNCATE,
-- không START TRANSACTION/COMMIT (các lệnh này làm MySQL commit giữa chừng).
-- Thứ tự: bảng cha (students, subjects) trước bảng con (grades, tuition).

INSERT INTO students (id, student_code, full_name, class_name, email) VALUES
    (1,  'SV001', 'Nguyễn Văn An',     'CNTT1', 'an.nv@example.edu.vn'),
    (2,  'SV002', 'Trần Thị Bình',     'CNTT1', 'binh.tt@example.edu.vn'),
    (3,  'SV003', 'Lê Hoàng Cường',    'CNTT1', 'cuong.lh@example.edu.vn'),
    (4,  'SV004', 'Phạm Thị Dung',     'CNTT2', 'dung.pt@example.edu.vn'),
    (5,  'SV005', 'Hoàng Minh Đức',    'CNTT2', 'duc.hm@example.edu.vn'),
    (6,  'SV006', 'Vũ Thu Hà',         'CNTT2', 'ha.vt@example.edu.vn'),
    (7,  'SV007', 'Đặng Quốc Huy',     'KTPM1', 'huy.dq@example.edu.vn'),
    (8,  'SV008', 'Bùi Ngọc Lan',      'KTPM1', 'lan.bn@example.edu.vn'),
    (9,  'SV009', 'Đỗ Thành Long',     'HTTT1', 'long.dt@example.edu.vn'),
    (10, 'SV010', 'Ngô Phương Mai',    'HTTT1', 'mai.np@example.edu.vn');

INSERT INTO subjects (id, subject_code, subject_name, credits) VALUES
    (1, 'INT1001', 'Nhập môn lập trình',          3),
    (2, 'INT1002', 'Cấu trúc dữ liệu và giải thuật', 4),
    (3, 'INT1003', 'Cơ sở dữ liệu',               3),
    (4, 'INT1004', 'Mạng máy tính',               3),
    (5, 'MAT1001', 'Toán rời rạc',                2);

INSERT INTO grades (student_id, subject_id, semester, attendance, midterm, final) VALUES
    (1,  1, 'HK1-2025', 10, 8.0, 8.5),
    (1,  2, 'HK1-2025',  9, 7.0, 7.5),
    (1,  3, 'HK2-2025', 10, 8.5, 9.0),
    (2,  1, 'HK1-2025',  8, 6.5, 7.0),
    (2,  5, 'HK1-2025',  9, 7.5, 8.0),
    (3,  1, 'HK1-2025',  7, 5.0, 4.5),
    (3,  2, 'HK1-2025',  6, 3.5, 3.0),
    (4,  3, 'HK2-2025', 10, 9.0, 9.5),
    (4,  4, 'HK2-2025',  9, 8.0, 8.0),
    (5,  1, 'HK1-2025',  8, 6.0, 6.5),
    (5,  4, 'HK2-2025',  8, 7.0, 6.0),
    (6,  2, 'HK1-2025', 10, 9.5, 9.0),
    (6,  5, 'HK1-2025', 10, 8.0, 8.5),
    (7,  3, 'HK2-2025',  7, 6.0, 5.5),
    (8,  1, 'HK1-2025',  9, 7.0, 7.5),
    (8,  3, 'HK2-2025',  9, 8.0, 7.0),
    (9,  4, 'HK2-2025',  5, 4.0, 3.5),
    (10, 5, 'HK1-2025', 10, 9.0, 8.5);

INSERT INTO tuition (student_id, semester, amount_due, amount_paid, due_date, note) VALUES
    (1,  'HK1-2025', 8500000, 8500000, '2025-09-30', 'Đã đóng đủ'),
    (2,  'HK1-2025', 8500000, 5000000, '2025-09-30', 'Đóng đợt 1'),
    (3,  'HK1-2025', 8500000,       0, '2025-09-30', ''),
    (4,  'HK2-2025', 9000000, 9000000, '2026-02-28', 'Đã đóng đủ'),
    (5,  'HK2-2025', 9000000, 4500000, '2026-02-28', 'Đóng đợt 1'),
    (6,  'HK1-2025', 8500000, 8500000, '2025-09-30', 'Học bổng một phần'),
    (7,  'HK2-2025', 9000000,       0, '2026-02-28', ''),
    (8,  'HK1-2025', 8500000, 8500000, '2025-09-30', 'Đã đóng đủ'),
    (9,  'HK2-2025', 9000000, 3000000, '2026-02-28', 'Xin gia hạn'),
    (10, 'HK1-2025', 8500000, 8500000, '2025-09-30', 'Đã đóng đủ');
