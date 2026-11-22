"""Gọi REST API của back-end từ phía server front-end."""
import os

import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5001").rstrip("/")
API_TOKEN = os.environ.get("API_TOKEN", "")
API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "5"))

_session = requests.Session()
if API_TOKEN:
    _session.headers["X-API-Key"] = API_TOKEN


class ApiError(Exception):
    """Lỗi từ back-end. `field`: tên ô bị sai do back-end chỉ ra (vd "semester"), hoặc None."""
    def __init__(self, status, message, field=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.field = field


def _request(method, path, **kwargs):
    url = f"{BACKEND_URL}{path}"
    try:
        response = _session.request(method, url, timeout=API_TIMEOUT, **kwargs)
    except (requests.ConnectionError, requests.Timeout):
        raise ApiError(503, f"Không kết nối được back-end tại {BACKEND_URL}. Hãy chạy backend/app.py.")
    try:
        body = response.json()
    except ValueError:
        body = {}
    if not response.ok:
        if not isinstance(body, dict):
            body = {}
        message = body.get("error")
        field = body.get("field")
        raise ApiError(response.status_code, message or f"Back-end trả về lỗi HTTP {response.status_code}.",
                       field if isinstance(field, str) else None)
    return body


def get(path, params=None):
    return _request("GET", path, params=params)


def post(path, json):
    return _request("POST", path, json=json)


def put(path, json):
    return _request("PUT", path, json=json)


def delete(path):
    return _request("DELETE", path)
