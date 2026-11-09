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
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


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
        message = body.get("error") if isinstance(body, dict) else None
        raise ApiError(response.status_code, message or f"Back-end trả về lỗi HTTP {response.status_code}.")
    return body


def get(path, params=None):
    return _request("GET", path, params=params)


def post(path, json):
    return _request("POST", path, json=json)


def put(path, json):
    return _request("PUT", path, json=json)


def delete(path):
    return _request("DELETE", path)
