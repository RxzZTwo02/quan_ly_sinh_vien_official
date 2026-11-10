"""Kết nối và khởi tạo cơ sở dữ liệu MySQL."""
import time
from contextlib import contextmanager
from decimal import Decimal

import pymysql
from pymysql.constants import CLIENT
from pymysql.cursors import DictCursor

import config

# Mã lỗi MySQL dùng để phân loại IntegrityError.
ER_DUP_ENTRY = 1062          # trùng khóa UNIQUE
ER_NO_REFERENCED_ROW = 1452  # khóa ngoại trỏ tới bản ghi không tồn tại

# Lược đồ và dữ liệu mẫu nằm trong file SQL (backend/sql/).
SQL_DIR = config.BASE_DIR / "sql"
SCHEMA_FILE = SQL_DIR / "schema.sql"
SEED_FILE = SQL_DIR / "seed.sql"
# Bảng do schema.sql tạo, thứ tự bảng con trước để DROP không vướng khóa ngoại.
SEEDED_TABLES = ["tuition", "grades", "subjects", "students"]


def _connect(database=None, multi_statements=False):
    flags = CLIENT.FOUND_ROWS
    if multi_statements:
        # Cho phép một lần execute() chạy cả file .sql nhiều câu lệnh.
        flags |= CLIENT.MULTI_STATEMENTS
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
        client_flag=flags,
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


def _run_sql_file(cur, path):
    """Chạy toàn bộ câu lệnh trong một file .sql (cần kết nối MULTI_STATEMENTS)."""
    sql = path.read_text(encoding="utf-8")
    cur.execute(sql)
    # Phải đọc hết kết quả của từng câu; lỗi ở câu sau được ném ra tại nextset().
    while cur.nextset():
        pass


def _database_state(cur):
    """Trả về (database đã tồn tại?, số bảng hiện có)."""
    cur.execute("SELECT 1 FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (config.DB_NAME,))
    exists = cur.fetchone() is not None
    cur.execute("SELECT COUNT(*) AS n FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s",
                (config.DB_NAME,))
    return exists, cur.fetchone()["n"]


def init_database(seed=True):
    """Tạo database và bảng từ sql/schema.sql; nếu database chưa tồn tại (hoặc chưa có
    bảng nào) thì seed dữ liệu mẫu từ sql/seed.sql. Thử lại nhiều lần nếu MySQL chưa sẵn sàng."""
    retries = max(config.DB_CONNECT_RETRIES, 1)
    for attempt in range(1, retries + 1):
        try:
            conn = _connect(multi_statements=True)
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
            exists, table_count = _database_state(cur)
            # Database do Docker (MYSQL_DATABASE) hoặc người dùng tạo sẵn nhưng còn rỗng
            # cũng được coi là "chưa có" để seed.
            needs_seed = seed and table_count == 0
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE `{config.DB_NAME}`")
            _run_sql_file(cur, SCHEMA_FILE)
            conn.commit()

            if not needs_seed:
                return
            reason = "chưa tồn tại" if not exists else "chưa có bảng nào"
            print(f"Database '{config.DB_NAME}' {reason}, đang seed từ {SEED_FILE.name}...", flush=True)
            try:
                _run_sql_file(cur, SEED_FILE)
                conn.commit()
            except Exception:
                conn.rollback()
                # Bảng vừa được tạo trống; xóa đi để lần khởi động sau còn seed lại.
                cur.execute("DROP TABLE IF EXISTS " + ", ".join(SEEDED_TABLES))
                raise
            print("Seed dữ liệu mẫu hoàn tất.", flush=True)
    finally:
        conn.close()


def to_jsonable(row):
    """Chuyển Decimal (cột DECIMAL/SUM) sang float để JSON và template định dạng được."""
    if row is None:
        return None
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
