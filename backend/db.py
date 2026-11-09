"""Kết nối và khởi tạo cơ sở dữ liệu MySQL."""
import time
from contextlib import contextmanager
from decimal import Decimal

import pymysql
from pymysql.constants import CLIENT
from pymysql.cursors import DictCursor

import config

# Mã lỗi MySQL dùng để phân loại IntegrityError.
ER_NO_REFERENCED_ROW = 1452

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS students (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_code VARCHAR(20) NOT NULL UNIQUE,
        full_name VARCHAR(100) NOT NULL,
        class_name VARCHAR(50) NOT NULL,
        email VARCHAR(120) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS subjects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        subject_code VARCHAR(20) NOT NULL UNIQUE,
        subject_name VARCHAR(120) NOT NULL,
        credits INT NOT NULL DEFAULT 3,
        CONSTRAINT chk_subjects_credits CHECK (credits > 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS grades (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS tuition (
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]


def _connect(database=None):
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        # FOUND_ROWS: UPDATE trả về số dòng khớp điều kiện, không phải số dòng
        # thực sự thay đổi -> lưu sinh viên mà không đổi gì vẫn được coi là thành công.
        client_flag=CLIENT.FOUND_ROWS,
        connect_timeout=5,
    )


def get_connection():
    return _connect(config.DB_NAME)


@contextmanager
def transaction():
    """Mở kết nối, trả về cursor; commit nếu thành công, rollback nếu lỗi."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Tạo database (nếu chưa có) và các bảng. Thử lại nhiều lần nếu MySQL chưa sẵn sàng."""
    retries = max(config.DB_CONNECT_RETRIES, 1)
    for attempt in range(1, retries + 1):
        try:
            conn = _connect()
            break
        except pymysql.err.OperationalError as exc:
            if attempt == retries:
                raise RuntimeError(
                    f"Không kết nối được MySQL tại {config.DB_HOST}:{config.DB_PORT} "
                    f"(user '{config.DB_USER}'). Hãy bật MySQL trong Laragon (Start All) "
                    f"hoặc kiểm tra cấu hình trong backend/.env. Chi tiết: {exc}"
                ) from exc
            print(f"Chờ MySQL sẵn sàng ({attempt}/{retries})...", flush=True)
            time.sleep(config.DB_CONNECT_DELAY)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE `{config.DB_NAME}`")
            for statement in SCHEMA:
                cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


def to_jsonable(row):
    """Chuyển Decimal (cột DECIMAL/SUM) sang float để JSON và template định dạng được."""
    if row is None:
        return None
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
