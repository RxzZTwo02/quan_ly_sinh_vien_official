-- Lược đồ cơ sở dữ liệu QLSV (MySQL 8, InnoDB, utf8mb4).
-- Chạy mỗi lần back-end khởi động; dùng IF NOT EXISTS nên không ảnh hưởng dữ liệu đã có.

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_code VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    email VARCHAR(120) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_code VARCHAR(20) NOT NULL UNIQUE,
    subject_name VARCHAR(120) NOT NULL,
    credits INT NOT NULL DEFAULT 3,
    CONSTRAINT chk_subjects_credits CHECK (credits > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    semester VARCHAR(20) NOT NULL,
    attendance DOUBLE NOT NULL DEFAULT 0,
    midterm DOUBLE NOT NULL DEFAULT 0,
    final DOUBLE NOT NULL DEFAULT 0,
    UNIQUE KEY uq_grades (student_id, subject_id, semester),
    CONSTRAINT chk_grades_attendance CHECK (attendance BETWEEN 0 AND 10),
    CONSTRAINT chk_grades_midterm CHECK (midterm BETWEEN 0 AND 10),
    CONSTRAINT chk_grades_final CHECK (final BETWEEN 0 AND 10),
    CONSTRAINT fk_grades_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_grades_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tuition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester VARCHAR(20) NOT NULL,
    amount_due DECIMAL(15,2) NOT NULL,
    amount_paid DECIMAL(15,2) NOT NULL DEFAULT 0,
    due_date VARCHAR(10) NOT NULL DEFAULT '',
    note VARCHAR(200) NOT NULL DEFAULT '',
    UNIQUE KEY uq_tuition (student_id, semester),
    CONSTRAINT chk_tuition_due CHECK (amount_due >= 0),
    CONSTRAINT chk_tuition_paid CHECK (amount_paid >= 0),
    CONSTRAINT fk_tuition_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
