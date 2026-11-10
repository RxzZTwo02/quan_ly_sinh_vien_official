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


@app.get("/")
def index():
    keyword = request.args.get("q", "").strip()
    edit_id = request.args.get("edit", type=int)
    error = request.args.get("error", "")
    status = 200
    try:
        students = api.get("/api/students", {"q": keyword})
        editing = None
        if edit_id:
            try:
                editing = api.get(f"/api/students/{edit_id}")
            except ApiError as exc:
                if exc.status != 404:
                    raise
                error = error or "Không tìm thấy sinh viên cần sửa."
        subjects = api.get("/api/subjects")
        grades = api.get("/api/grades")
        tuition = api.get("/api/tuition")
        stats = api.get("/api/stats")
    except ApiError as exc:
        students, editing, subjects, grades, tuition = [], None, [], [], []
        stats = {"total": 0, "subject_count": 0, "grade_count": 0, "tuition_balance": 0,
                 "chart_data": EMPTY_CHART}
        error = exc.message
        status = 503 if exc.status == 503 else 502
    return render_template("index.html", students=students, editing=editing, keyword=keyword,
        total=stats["total"], subjects=subjects, grades=grades, tuition=tuition,
        subject_count=stats["subject_count"], grade_count=stats["grade_count"],
        tuition_balance=stats["tuition_balance"], chart_data=stats["chart_data"],
        message=request.args.get("message", ""), error=error), status


@app.post("/save")
def save_student():
    data = form_data("student_code", "full_name", "class_name", "email")
    student_id = request.form.get("id", "").strip()
    if student_id:
        if not student_id.isdecimal():
            abort(400)
        return call_and_redirect(api.put, f"/api/students/{student_id}", data)
    return call_and_redirect(api.post, "/api/students", data)


@app.post("/delete/<int:student_id>")
def delete_student(student_id):
    return call_and_redirect(api.delete, f"/api/students/{student_id}")


@app.post("/subjects/save")
def save_subject():
    return call_and_redirect(api.post, "/api/subjects",
                             form_data("subject_code", "subject_name", "credits"))


@app.post("/subjects/delete/<int:subject_id>")
def delete_subject(subject_id):
    return call_and_redirect(api.delete, f"/api/subjects/{subject_id}")


@app.post("/grades/save")
def save_grade():
    return call_and_redirect(api.post, "/api/grades",
                             form_data("student_id", "subject_id", "semester", "attendance", "midterm", "final"))


@app.post("/tuition/save")
def save_tuition():
    return call_and_redirect(api.post, "/api/tuition",
                             form_data("student_id", "semester", "amount_due", "amount_paid", "due_date", "note"))


@app.post("/grades/delete/<int:grade_id>")
def delete_grade(grade_id):
    return call_and_redirect(api.delete, f"/api/grades/{grade_id}")


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
