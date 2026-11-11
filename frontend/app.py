"""Front-end: giao diện web, gọi REST API của back-end."""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")  # phải nạp trước khi import api_client

from flask import Flask, abort, redirect, render_template, request, session, url_for  # noqa: E402
from waitress import serve  # noqa: E402

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


def call_and_redirect(func, *args):
    """Gọi API rồi quay về trang chính với thông báo thành công hoặc lỗi."""
    try:
        result = func(*args)
    except ApiError as exc:
        return redirect(url_for("index", error=exc.message))
    return redirect(url_for("index", message=result.get("message", "Thành công.")))


def save_record(collection, fields):
    """Form có trường ẩn `id` thì sửa (PUT /api/<collection>/<id>), không có thì thêm mới (POST)."""
    data = form_data(*fields)
    record_id = request.form.get("id", "").strip()
    if record_id:
        if not record_id.isdecimal():
            abort(400)
        return call_and_redirect(api.put, f"/api/{collection}/{record_id}", data)
    return call_and_redirect(api.post, f"/api/{collection}", data)


def plain_number(value):
    """8000000.0 -> '8000000', 7.5 -> '7.5': điền vào ô type=number khi sửa."""
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


app.jinja_env.filters["plain_number"] = plain_number

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


@app.get("/")
def index():
    keyword = request.args.get("q", "").strip()
    error = request.args.get("error", "")
    status = 200
    try:
        students = api.get("/api/students", {"q": keyword})
        all_students = api.get("/api/students") if keyword else students
        editing, edit_error = load_editing()
        error = error or edit_error
        subjects = api.get("/api/subjects")
        grades = api.get("/api/grades")
        tuition = api.get("/api/tuition")
        stats = api.get("/api/stats")
    except ApiError as exc:
        students, all_students, editing, subjects, grades, tuition = [], [], {}, [], [], []
        stats = {"total": 0, "subject_count": 0, "grade_count": 0, "tuition_balance": 0,
                 "chart_data": EMPTY_CHART}
        error = exc.message
        status = 503 if exc.status == 503 else 502
    return render_template("index.html", students=students, all_students=all_students, keyword=keyword,
        editing=editing.get("edit"), editing_subject=editing.get("edit_subject"),
        editing_grade=editing.get("edit_grade"), editing_tuition=editing.get("edit_tuition"),
        total=stats["total"], subjects=subjects, grades=grades, tuition=tuition,
        subject_count=stats["subject_count"], grade_count=stats["grade_count"],
        tuition_balance=stats["tuition_balance"], chart_data=stats["chart_data"],
        message=request.args.get("message", ""), error=error), status


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


@app.get("/health")
def health():
    try:
        backend = api.get("/api/health")
        return {"frontend": "ok", "backend": backend}, 200
    except ApiError as exc:
        return {"frontend": "ok", "backend": {"status": "error", "detail": exc.message}}, 503


if __name__ == "__main__":
    print(f"Front-end: http://{FRONTEND_HOST}:{FRONTEND_PORT}  (back-end: {api.BACKEND_URL})", flush=True)
    serve(app, host=FRONTEND_HOST, port=FRONTEND_PORT)
