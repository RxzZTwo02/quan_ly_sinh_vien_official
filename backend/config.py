"""Cấu hình back-end. Giá trị mặc định khớp với MySQL của Laragon
(root / mật khẩu rỗng / 127.0.0.1:3306), nên file .env là tùy chọn."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env_yes_no(name, default):
    value = (os.environ.get(name) or default).strip().lower()
    if value in ("yes", "y", "true", "1", "on"):
        return True
    if value in ("no", "n", "false", "0", "off"):
        return False
    raise SystemExit(f"{name}='{value}' không hợp lệ, chỉ dùng yes hoặc no (xem backend/.env.example).")


DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "qlsv")

# Số lần thử kết nối MySQL khi khởi động (Docker cần chờ MySQL sẵn sàng).
DB_CONNECT_RETRIES = int(os.environ.get("DB_CONNECT_RETRIES", "1"))
DB_CONNECT_DELAY = float(os.environ.get("DB_CONNECT_DELAY", "2"))

# Database rỗng (cả 4 bảng chưa có dòng nào) thì có nạp dữ liệu mẫu sql/seed.sql không.
SEED_DATA = _env_yes_no("SEED_DATA", "yes")

API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "5001"))
# Nếu đặt, mọi request /api/* (trừ /api/health) phải gửi header X-API-Key khớp.
API_TOKEN = os.environ.get("API_TOKEN", "")
