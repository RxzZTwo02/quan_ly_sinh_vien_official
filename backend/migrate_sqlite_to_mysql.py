"""Chép dữ liệu từ file SQLite cũ (data/students.db) sang MySQL.

Cách dùng (trong thư mục backend):
    python migrate_sqlite_to_mysql.py
    python migrate_sqlite_to_mysql.py --sqlite D:/duong/dan/students.db

Id được giữ nguyên và dùng INSERT IGNORE, nên chạy lại nhiều lần không bị nhân đôi.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

import config
from db import init_database, transaction

DEFAULT_SQLITE = Path(__file__).resolve().parent.parent / "data" / "students.db"

# Thứ tự quan trọng: bảng cha trước bảng con (khóa ngoại).
TABLES = {
    "students": ["id", "student_code", "full_name", "class_name", "email"],
    "subjects": ["id", "subject_code", "subject_name", "credits"],
    "grades": ["id", "student_id", "subject_id", "semester", "attendance", "midterm", "final"],
    "tuition": ["id", "student_id", "semester", "amount_due", "amount_paid", "due_date", "note"],
}


def main():
    parser = argparse.ArgumentParser(description="Chép dữ liệu SQLite sang MySQL.")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE, help="đường dẫn file .db")
    args = parser.parse_args()

    if not args.sqlite.is_file():
        sys.exit(f"Không tìm thấy file SQLite: {args.sqlite}")

    init_database()
    source = sqlite3.connect(f"file:{args.sqlite.as_posix()}?mode=ro", uri=True)
    print(f"Nguồn: {args.sqlite}")
    print(f"Đích : MySQL {config.DB_USER}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}\n")
    try:
        with transaction() as cur:
            for table, columns in TABLES.items():
                col_list = ",".join(columns)
                data = source.execute(f"SELECT {col_list} FROM {table} ORDER BY id").fetchall()
                inserted = 0
                if data:
                    placeholders = ",".join(["%s"] * len(columns))
                    inserted = cur.executemany(
                        f"INSERT IGNORE INTO {table}({col_list}) VALUES({placeholders})", data) or 0
                print(f"  {table:<9} đọc {len(data):>4} dòng, chép mới {inserted:>4}, bỏ qua {len(data) - inserted:>4}")
    finally:
        source.close()
    print("\nHoàn tất.")


if __name__ == "__main__":
    main()
