"""Front-end: giao diện web, gọi REST API của back-end."""
import os
import secrets
import socket
import sys
from pathlib import Path

from dotenv import load_dotenv

# Windows: khi chuyển đầu ra sang file / pipe, Python ghi theo bảng mã ANSI (cp1252...) nên in tiếng
# Việt gây UnicodeEncodeError. Ép UTF-8 cho stdout / stderr (xem backend/app.py).
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")

load_dotenv(Path(__file__).resolve().parent / ".env")  # phải nạp trước khi import api_client

from flask import (Flask, abort, flash, get_flashed_messages, redirect, render_template,  # noqa: E402
                   render_template_string, request, session, url_for)
from waitress import serve  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

import api_client as api  # noqa: E402
from api_client import ApiError  # noqa: E402

FRONTEND_HOST = os.environ.get("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5000"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

EMPTY_CHART = {"gradeLabels": [], "gradeValues": [], "classLabels": [], "classValues": [],
               "tuitionDue": 0, "tuitionPaid": 0, "tuitionBalance": 0}


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def check_csrf():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        actual = request.form.get("csrf_token", "")
        if not expected or not secrets.compare_digest(expected, actual):
            abort(400, description="Phiên làm việc hết hạn. Hãy tải lại trang.")


def form_data(*fields):
    return {f: request.form.get(f, "") for f in fields}


# Từ khóa tìm kiếm của bảng Sinh viên, Môn học, Bảng điểm, Học phí. Được giữ qua mọi thao tác
# (Sửa, Hủy, lưu, xóa, tìm ở bảng khác); chỉ nút "Tất cả" của bảng đó mới bỏ (FR-32).
SEARCH_PARAMS = ("q", "q_subject", "q_grade", "q_tuition")


def active_searches(source):
    """Các từ khóa đang dùng (bỏ ô rỗng), đọc từ query string (GET) hoặc ô ẩn của form (POST)."""
    searches = {}
    for param in SEARCH_PARAMS:
        value = source.get(param, "").strip()
        if value:
            searches[param] = value
    return searches


def without(searches, param):
    """Bộ lọc Jinja: bỏ một từ khóa, dùng cho nút "Tất cả" và ô ẩn của form tìm kiếm."""
    return {k: v for k, v in searches.items() if k != param}


app.jinja_env.filters["without"] = without


def call_and_redirect(func, *args):
    """Gọi API rồi quay về trang chính (giữ nguyên tìm kiếm). Thông báo thành công / lỗi được lưu
    trong session (flash) và hiện một lần ở trang tiếp theo, không đặt lên URL: như vậy không ai
    tạo được link hiện thông báo giả (BUG-05), và F5 không hiện lại thông báo cũ."""
    searches = active_searches(request.form)
    try:
        result = func(*args)
    except ApiError as exc:
        flash(exc.message, "error")
    else:
        flash(result.get("message", "Thành công."), "success")
    return redirect(url_for("index", **searches))


def save_record(collection, fields):
    """Form có trường ẩn `id` thì sửa (PUT /api/<collection>/<id>), không có thì thêm mới (POST)."""
    data = form_data(*fields)
    record_id = request.form.get("id", "").strip()
    if record_id:
        if not record_id.isdecimal():
            abort(400, description="Mã bản ghi không hợp lệ.")
        return call_and_redirect(api.put, f"/api/{collection}/{record_id}", data)
    return call_and_redirect(api.post, f"/api/{collection}", data)


def plain_number(value):
    """8000000.0 -> '8000000', 7.5 -> '7.5': điền vào ô type=number khi sửa."""
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


app.jinja_env.filters["plain_number"] = plain_number


def editing_first(rows, record):
    """Bộ lọc Jinja (FR-33): dòng của bản ghi đang sửa lên đầu bảng, các dòng khác giữ thứ tự cũ
    (sắp xếp ổn định). Không sửa gì thì giữ nguyên; lưu xong hoặc Hủy thì URL không còn tham số
    sửa, nên dòng tự về vị trí cũ."""
    if not record:
        return rows
    return sorted(rows, key=lambda row: row["id"] != record["id"])


app.jinja_env.filters["editing_first"] = editing_first

# Tham số URL -> (endpoint API, thông báo khi không tìm thấy) cho từng chế độ sửa.
EDIT_PARAMS = {
    "edit": ("students", "Không tìm thấy sinh viên cần sửa."),
    "edit_subject": ("subjects", "Không tìm thấy môn học cần sửa."),
    "edit_grade": ("grades", "Không tìm thấy bản ghi điểm cần sửa."),
    "edit_tuition": ("tuition", "Không tìm thấy bản ghi học phí cần sửa."),
}


def load_editing():
    """Đọc các tham số ?edit*=<id>; trả về (dict bản ghi đang sửa theo tham số, thông báo lỗi)."""
    editing, error = {}, ""
    for param, (collection, not_found) in EDIT_PARAMS.items():
        record_id = request.args.get(param, type=int)
        if not record_id:
            continue
        try:
            editing[param] = api.get(f"/api/{collection}/{record_id}")
        except ApiError as exc:
            if exc.status != 404:
                raise
            error = error or not_found
    return editing, error


def search_list(collection, keyword):
    """(danh sách hiện trong bảng, danh sách đầy đủ). Có từ khóa thì bảng chỉ hiện kết quả tìm
    kiếm, còn danh sách đầy đủ vẫn dùng cho ô chọn và số liệu (gọi thêm 1 lần API không lọc)."""
    everything = api.get(f"/api/{collection}")
    return (api.get(f"/api/{collection}", {"q": keyword}) if keyword else everything), everything


@app.get("/")
def index():
    keyword = request.args.get("q", "").strip()
    subject_keyword = request.args.get("q_subject", "").strip()
    grade_keyword = request.args.get("q_grade", "").strip()
    tuition_keyword = request.args.get("q_tuition", "").strip()
    # Không đọc ?message= / ?error=: chỉ hiện thông báo do chính server tạo.
    flashed = get_flashed_messages(with_categories=True)
    messages = [text for kind, text in flashed if kind == "success"]
    errors = [text for kind, text in flashed if kind != "success"]
    status = 200
    try:
        students = api.get("/api/students", {"q": keyword})
        all_students = api.get("/api/students") if keyword else students
        editing, edit_error = load_editing()
        if edit_error:
            errors.append(edit_error)
        subjects, all_subjects = search_list("subjects", subject_keyword)
        grades, all_grades = search_list("grades", grade_keyword)
        tuition = api.get("/api/tuition", {"q": tuition_keyword})
        stats = api.get("/api/stats")
    except ApiError as exc:
        students, all_students, editing, subjects, grades, tuition = [], [], {}, [], [], []
        all_subjects, all_grades = [], []
        stats = {"total": 0, "subject_count": 0, "grade_count": 0, "tuition_balance": 0,
                 "chart_data": EMPTY_CHART}
        errors.append(exc.message)
        status = 503 if exc.status == 503 else 502
    return render_template("index.html", students=students, all_students=all_students, keyword=keyword,
        subject_keyword=subject_keyword, grade_keyword=grade_keyword, tuition_keyword=tuition_keyword,
        searches=active_searches(request.args),
        editing=editing.get("edit"), editing_subject=editing.get("edit_subject"),
        editing_grade=editing.get("edit_grade"), editing_tuition=editing.get("edit_tuition"),
        all_subjects=all_subjects, all_grades=all_grades,
        total=stats["total"], subjects=subjects, grades=grades, tuition=tuition,
        subject_count=stats["subject_count"], grade_count=stats["grade_count"],
        tuition_balance=stats["tuition_balance"], chart_data=stats["chart_data"],
        messages=messages, errors=errors), status


@app.post("/save")
def save_student():
    return save_record("students", ("student_code", "full_name", "class_name", "email"))


@app.post("/delete/<int:student_id>")
def delete_student(student_id):
    return call_and_redirect(api.delete, f"/api/students/{student_id}")


@app.post("/subjects/save")
def save_subject():
    return save_record("subjects", ("subject_code", "subject_name", "credits"))


@app.post("/subjects/delete/<int:subject_id>")
def delete_subject(subject_id):
    return call_and_redirect(api.delete, f"/api/subjects/{subject_id}")


@app.post("/grades/save")
def save_grade():
    return save_record("grades", ("student_id", "subject_id", "semester", "attendance", "midterm", "final"))


@app.post("/grades/delete/<int:grade_id>")
def delete_grade(grade_id):
    return call_and_redirect(api.delete, f"/api/grades/{grade_id}")


@app.post("/tuition/save")
def save_tuition():
    return save_record("tuition", ("student_id", "semester", "amount_due", "amount_paid", "due_date", "note"))


@app.post("/tuition/delete/<int:tuition_id>")
def delete_tuition(tuition_id):
    return call_and_redirect(api.delete, f"/api/tuition/{tuition_id}")


# Trang lỗi tiếng Việt thay cho trang mặc định tiếng Anh của Flask ("Bad Request", "Not Found"...).
# Thông báo nằm trong thẻ <p> đầu tiên: script của trang chính (fetchPage) đọc nó và hiện thành
# thông báo đỏ ngay trong giao diện, không chuyển trang.
ERROR_MESSAGES = {
    400: "Yêu cầu không hợp lệ.",
    404: "Không tìm thấy trang hoặc bản ghi.",
    405: "Thao tác không được hỗ trợ.",
    500: "Máy chủ gặp lỗi. Hãy thử lại sau.",
}
ERROR_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Lỗi {{ code }} · Quản lý sinh viên</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #f1f5f9; color: #1e293b; }
    main { max-width: 520px; margin: 80px auto; padding: 24px 28px; background: white;
           border-radius: 12px; box-shadow: 0 10px 30px rgba(15, 23, 42, .08); }
    h1 { margin: 0 0 12px; font-size: 20px; }
    p { margin: 0 0 18px; color: #991b1b; }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <main>
    <h1>Lỗi {{ code }}</h1>
    <p>{{ message }}</p>
    <a href="{{ url_for('index') }}">Về trang chính</a>
  </main>
</body>
</html>"""


@app.errorhandler(HTTPException)
def handle_http_error(exc):
    """Giữ mô tả tiếng Việt đã đặt khi abort() (vd lỗi CSRF); mô tả mặc định tiếng Anh của Werkzeug
    thì thay bằng câu tiếng Việt theo mã lỗi."""
    message = exc.description
    if not message or message == type(exc).description:
        message = ERROR_MESSAGES.get(exc.code, "Đã có lỗi xảy ra.")
    return render_template_string(ERROR_PAGE, code=exc.code, message=message), exc.code


@app.get("/health")
def health():
    try:
        backend = api.get("/api/health")
        return {"frontend": "ok", "backend": backend}, 200
    except ApiError as exc:
        return {"frontend": "ok", "backend": {"status": "error", "detail": exc.message}}, 503


def ensure_port_free(host, port):
    """Windows cho 2 process cùng nghe 1 cổng mà không báo lỗi (Waitress bật SO_REUSEADDR):
    thử bind độc quyền trước khi serve(), cổng đã có process khác dùng thì dừng."""
    if os.name != "nt":  # Linux/Docker: chạy trùng cổng đã tự báo lỗi
        return
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        s.bind((host, port))
    except OSError:
        raise SystemExit(f"Cổng {port} đang được dùng (có thể frontend/app.py đang chạy ở cửa sổ khác). "
                         "Hãy tắt nó trước.")
    finally:
        s.close()


if __name__ == "__main__":
    ensure_port_free(FRONTEND_HOST, FRONTEND_PORT)
    print(f"Front-end: http://{FRONTEND_HOST}:{FRONTEND_PORT}  (back-end: {api.BACKEND_URL})", flush=True)
    serve(app, host=FRONTEND_HOST, port=FRONTEND_PORT)
