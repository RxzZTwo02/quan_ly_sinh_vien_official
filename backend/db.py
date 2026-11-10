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
# Bảng do schema.sql tạo. Database được coi là "rỗng" khi cả 4 bảng đều chưa có dòng nào.
APP_TABLES = ["students", "subjects", "grades", "tuition"]


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


def _has_data(cur):
    """True nếu ít nhất một bảng của ứng dụng có dữ liệu."""
    checks = " OR ".join(f"EXISTS(SELECT 1 FROM `{t}`)" for t in APP_TABLES)
    cur.execute(f"SELECT {checks} AS has_data")
    return bool(cur.fetchone()["has_data"])


def _row_counts(cur):
    cur.execute("SELECT " + ", ".join(f"(SELECT COUNT(*) FROM `{t}`) AS `{t}`" for t in APP_TABLES))
    return cur.fetchone()


def init_database():
    """Tạo database và bảng từ sql/schema.sql nếu chưa có. Nếu database rỗng (cả 4 bảng chưa
    có dòng nào) và SEED_DATA=yes thì nạp dữ liệu mẫu từ sql/seed.sql; database đã có dữ liệu
    thì giữ nguyên, không đọc seed.sql. Thử lại nhiều lần nếu MySQL chưa sẵn sàng."""
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
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE `{config.DB_NAME}`")
            _run_sql_file(cur, SCHEMA_FILE)  # IF NOT EXISTS: không đụng tới dữ liệu đã có
            conn.commit()

            name = config.DB_NAME
            if _has_data(cur):
                students = _row_counts(cur)["students"]
                print(f"Dùng dữ liệu hiện có trong database '{name}' ({students} sinh viên), "
                      "không nạp dữ liệu mẫu.", flush=True)
                return
            if not config.SEED_DATA:
                print(f"Database '{name}' đang trống, không nạp dữ liệu mẫu (SEED_DATA=no).", flush=True)
                return

            print(f"Database '{name}' đang trống, đang nạp dữ liệu mẫu từ {SEED_FILE.name}...", flush=True)
            # Cả file chạy trong MỘT transaction: lỗi hay bị ngắt giữa chừng thì không dòng nào
            # được lưu, database vẫn rỗng và lần khởi động sau sẽ nạp lại.
            try:
                _run_sql_file(cur, SEED_FILE)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            n = _row_counts(cur)
            print(f"Đã nạp dữ liệu mẫu: {n['students']} sinh viên, {n['subjects']} môn học, "
                  f"{n['grades']} bản ghi điểm, {n['tuition']} bản ghi học phí. "
                  "(Không muốn dữ liệu mẫu: đặt SEED_DATA=no, xem README.)", flush=True)
    finally:
        conn.close()


def to_jsonable(row):
    """Chuyển Decimal (cột DECIMAL/SUM) sang float để JSON và template định dạng được."""
    if row is None:
        return None
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
