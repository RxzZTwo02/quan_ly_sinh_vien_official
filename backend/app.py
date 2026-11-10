"""Back-end: REST API JSON cho hệ thống quản lý sinh viên (MySQL)."""
import secrets

import pymysql
from flask import Flask, jsonify, request
from waitress import serve
from werkzeug.exceptions import HTTPException

import config
from db import ER_NO_REFERENCED_ROW, init_database, to_jsonable, transaction

app = Flask(__name__)
app.json.ensure_ascii = False  # trả tiếng Việt có dấu nguyên vẹn
app.json.sort_keys = False

TOTAL_EXPR = "(attendance*0.1 + midterm*0.3 + final*0.6)"


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def ok(message=None, status=200, **data):
    payload = {"message": message} if message else {}
    payload.update(data)
    return jsonify(payload), status


def rows(cur):
    return [to_jsonable(r) for r in cur.fetchall()]


def payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Dữ liệu gửi lên phải là JSON object.")
    return data


def text(data, key, default=""):
    value = data.get(key, default)
    return "" if value is None else str(value).strip()


# ---------------------------------------------------------------- xử lý chung

@app.before_request
def check_api_token():
    if not config.API_TOKEN or request.path == "/api/health":
        return None
    supplied = request.headers.get("X-API-Key", "")
    if not secrets.compare_digest(config.API_TOKEN, supplied):
        return jsonify(error="Thiếu hoặc sai API key."), 401
    return None


@app.errorhandler(ApiError)
def handle_api_error(exc):
    return jsonify(error=exc.message), exc.status


@app.errorhandler(HTTPException)
def handle_http_error(exc):
    return jsonify(error=exc.description), exc.code


@app.errorhandler(pymysql.err.OperationalError)
def handle_db_down(exc):
    app.logger.error("Lỗi kết nối MySQL: %s", exc)
    return jsonify(error="Không kết nối được cơ sở dữ liệu MySQL."), 503


@app.errorhandler(pymysql.err.DataError)
def handle_bad_data(exc):
    return jsonify(error="Dữ liệu không hợp lệ hoặc quá dài."), 400


# ---------------------------------------------------------------- health

@app.get("/api/health")
def health():
    try:
        with transaction() as cur:
            cur.execute("SELECT 1")
        return jsonify(status="ok", database="ok"), 200
    except pymysql.err.MySQLError as exc:
        return jsonify(status="degraded", database="error", detail=str(exc)), 503


# ---------------------------------------------------------------- sinh viên

def validate_student(data):
    student_code = text(data, "student_code").upper()
    full_name = text(data, "full_name")
    class_name = text(data, "class_name")
    email = text(data, "email")
    if (not all([student_code, full_name, class_name, email]) or len(student_code) > 20
            or len(full_name) > 100 or len(class_name) > 50 or len(email) > 120 or "@" not in email):
        raise ApiError("Vui lòng nhập đủ thông tin hợp lệ.")
    return student_code, full_name, class_name, email


@app.get("/api/students")
def list_students():
    keyword = request.args.get("q", "").strip()
    like = f"%{keyword}%"
    with transaction() as cur:
        cur.execute("""SELECT * FROM students
            WHERE student_code LIKE %s OR full_name LIKE %s OR class_name LIKE %s
            ORDER BY id DESC""", (like, like, like))
        return jsonify(rows(cur))


@app.get("/api/students/<int:student_id>")
def get_student(student_id):
    with transaction() as cur:
        cur.execute("SELECT * FROM students WHERE id=%s", (student_id,))
        student = cur.fetchone()
    if not student:
        raise ApiError("Không tìm thấy sinh viên.", 404)
    return jsonify(to_jsonable(student))


@app.post("/api/students")
def create_student():
    values = validate_student(payload())
    try:
        with transaction() as cur:
            cur.execute("INSERT INTO students(student_code,full_name,class_name,email) VALUES(%s,%s,%s,%s)",
                        values)
            new_id = cur.lastrowid
    except pymysql.err.IntegrityError:
        raise ApiError("Mã sinh viên đã tồn tại hoặc dữ liệu không hợp lệ.", 409)
    return ok("Đã thêm sinh viên.", 201, id=new_id)


@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    values = validate_student(payload())
    try:
        with transaction() as cur:
            affected = cur.execute(
                "UPDATE students SET student_code=%s,full_name=%s,class_name=%s,email=%s WHERE id=%s",
                (*values, student_id))
    except pymysql.err.IntegrityError:
        raise ApiError("Mã sinh viên đã tồn tại hoặc dữ liệu không hợp lệ.", 409)
    if not affected:
        raise ApiError("Không tìm thấy sinh viên.", 404)
    return ok("Đã cập nhật sinh viên.")


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    with transaction() as cur:
        affected = cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
    if not affected:
        raise ApiError("Không tìm thấy sinh viên.", 404)
    return ok("Đã xóa sinh viên và dữ liệu điểm/học phí liên quan.")


# ---------------------------------------------------------------- môn học

@app.get("/api/subjects")
def list_subjects():
    with transaction() as cur:
        cur.execute("SELECT * FROM subjects ORDER BY subject_name")
        return jsonify(rows(cur))


@app.post("/api/subjects")
def create_subject():
    data = payload()
    code = text(data, "subject_code").upper()
    name = text(data, "subject_name")
    try:
        credits = int(text(data, "credits", "3"))
    except ValueError:
        credits = 0
    if not code or not name or len(code) > 20 or len(name) > 120 or credits < 1 or credits > 10:
        raise ApiError("Môn học cần có mã, tên và số tín chỉ từ 1 đến 10.")
    try:
        with transaction() as cur:
            cur.execute("INSERT INTO subjects(subject_code,subject_name,credits) VALUES(%s,%s,%s)",
                        (code, name, credits))
            new_id = cur.lastrowid
    except pymysql.err.IntegrityError:
        raise ApiError("Mã môn học đã tồn tại.", 409)
    return ok("Đã thêm môn học.", 201, id=new_id)


@app.delete("/api/subjects/<int:subject_id>")
def delete_subject(subject_id):
    with transaction() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM grades WHERE subject_id=%s", (subject_id,))
        grade_count = cur.fetchone()["n"]
        affected = cur.execute("DELETE FROM subjects WHERE id=%s", (subject_id,))
    if not affected:
        raise ApiError("Không tìm thấy môn học.", 404)
    if grade_count:
        return ok(f"Đã xóa môn học và {grade_count} bản ghi điểm liên quan.", deleted_grades=grade_count)
    return ok("Đã xóa môn học.", deleted_grades=0)


# ---------------------------------------------------------------- bảng điểm

@app.get("/api/grades")
def list_grades():
    with transaction() as cur:
        cur.execute("""SELECT g.*, s.student_code, s.full_name, sub.subject_code, sub.subject_name,
            sub.credits, ROUND(g.attendance*0.1 + g.midterm*0.3 + g.final*0.6, 2) AS total
            FROM grades g JOIN students s ON s.id=g.student_id
            JOIN subjects sub ON sub.id=g.subject_id
            ORDER BY g.semester DESC, s.student_code, sub.subject_name""")
        return jsonify(rows(cur))


@app.post("/api/grades")
def save_grade():
    data = payload()
    try:
        student_id = int(text(data, "student_id"))
        subject_id = int(text(data, "subject_id"))
        semester = text(data, "semester")
        attendance = float(text(data, "attendance"))
        midterm = float(text(data, "midterm"))
        final = float(text(data, "final"))
        if not semester or len(semester) > 20 or any(x < 0 or x > 10 for x in [attendance, midterm, final]):
            raise ValueError()
    except ValueError:
        raise ApiError("Điểm phải nằm trong khoảng 0–10 và cần chọn sinh viên, môn học, học kỳ.")
    try:
        with transaction() as cur:
            cur.execute("""INSERT INTO grades(student_id,subject_id,semester,attendance,midterm,final)
                VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE
                attendance=VALUES(attendance), midterm=VALUES(midterm), final=VALUES(final)""",
                        (student_id, subject_id, semester, attendance, midterm, final))
    except pymysql.err.IntegrityError as exc:
        if exc.args and exc.args[0] == ER_NO_REFERENCED_ROW:
            raise ApiError("Sinh viên hoặc môn học không tồn tại.")
        raise ApiError("Dữ liệu điểm không hợp lệ.")
    return ok("Đã lưu điểm. Điểm tổng kết được tính theo 10% chuyên cần, 30% giữa kỳ, 60% cuối kỳ.")


@app.delete("/api/grades/<int:grade_id>")
def delete_grade(grade_id):
    with transaction() as cur:
        affected = cur.execute("DELETE FROM grades WHERE id=%s", (grade_id,))
    if not affected:
        raise ApiError("Không tìm thấy bản ghi điểm.", 404)
    return ok("Đã xóa bản ghi điểm.")


# ---------------------------------------------------------------- học phí

@app.get("/api/tuition")
def list_tuition():
    with transaction() as cur:
        cur.execute("""SELECT t.*, s.student_code, s.full_name,
            GREATEST(t.amount_due-t.amount_paid, 0) AS balance
            FROM tuition t JOIN students s ON s.id=t.student_id
            ORDER BY t.semester DESC, s.student_code""")
        return jsonify(rows(cur))


@app.post("/api/tuition")
def save_tuition():
    data = payload()
    try:
        student_id = int(text(data, "student_id"))
        semester = text(data, "semester")
        due = float(text(data, "amount_due"))
        paid = float(text(data, "amount_paid", "0") or "0")
        due_date = text(data, "due_date")
        note = text(data, "note")
        if (not semester or len(semester) > 20 or len(due_date) > 10 or len(note) > 200
                or due < 0 or paid < 0 or paid > due):
            raise ValueError()
    except ValueError:
        raise ApiError("Học phí không hợp lệ; số đã đóng phải từ 0 đến số phải đóng.")
    try:
        with transaction() as cur:
            cur.execute("""INSERT INTO tuition(student_id,semester,amount_due,amount_paid,due_date,note)
                VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE
                amount_due=VALUES(amount_due), amount_paid=VALUES(amount_paid),
                due_date=VALUES(due_date), note=VALUES(note)""",
                        (student_id, semester, due, paid, due_date, note))
    except pymysql.err.IntegrityError:
        raise ApiError("Sinh viên không tồn tại.")
    return ok("Đã lưu thông tin học phí.")


# ---------------------------------------------------------------- thống kê

@app.get("/api/stats")
def stats():
    with transaction() as cur:
        cur.execute("""SELECT
            (SELECT COUNT(*) FROM students) AS total,
            (SELECT COUNT(*) FROM subjects) AS subject_count,
            (SELECT COUNT(*) FROM grades) AS grade_count""")
        counts = cur.fetchone()
        cur.execute("""SELECT COALESCE(SUM(amount_due),0) AS due, COALESCE(SUM(amount_paid),0) AS paid,
            COALESCE(SUM(GREATEST(amount_due-amount_paid,0)),0) AS balance FROM tuition""")
        money = to_jsonable(cur.fetchone())
        cur.execute(f"""SELECT CASE
                WHEN {TOTAL_EXPR} >= 8 THEN 'Giỏi'
                WHEN {TOTAL_EXPR} >= 6.5 THEN 'Khá'
                WHEN {TOTAL_EXPR} >= 5 THEN 'Trung bình'
                ELSE 'Cần cố gắng'
            END AS label, COUNT(*) AS amount
            FROM grades GROUP BY label""")
        grade_summary = cur.fetchall()
        cur.execute("""SELECT class_name AS label, COUNT(*) AS amount
            FROM students GROUP BY class_name ORDER BY amount DESC, label LIMIT 8""")
        class_summary = cur.fetchall()
    return jsonify(
        total=counts["total"],
        subject_count=counts["subject_count"],
        grade_count=counts["grade_count"],
        tuition_balance=money["balance"],
        chart_data={
            "gradeLabels": [r["label"] for r in grade_summary],
            "gradeValues": [r["amount"] for r in grade_summary],
            "classLabels": [r["label"] for r in class_summary],
            "classValues": [r["amount"] for r in class_summary],
            "tuitionDue": money["due"],
            "tuitionPaid": money["paid"],
            "tuitionBalance": money["balance"],
        },
    )


if __name__ == "__main__":
    init_database()
    print(f"Back-end API: http://{config.API_HOST}:{config.API_PORT}  "
          f"(MySQL {config.DB_USER}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME})", flush=True)
    serve(app, host=config.API_HOST, port=config.API_PORT)
