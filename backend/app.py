"""Back-end: REST API JSON cho hệ thống quản lý sinh viên (MySQL)."""
import os
import re
import secrets
import socket
import sys
import unicodedata
from datetime import date

# Windows: khi chuyển đầu ra sang file / pipe (vd `python app.py > log.txt`), Python ghi theo bảng mã
# ANSI (cp1252...) nên mọi lệnh print tiếng Việt (kể cả trong db.py) gây UnicodeEncodeError và app
# dừng ngay. Ép UTF-8 cho stdout / stderr, trước khi import config (config có thể báo lỗi tiếng Việt).
for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")

import pymysql
from flask import Flask, jsonify, request
from waitress import serve
from werkzeug.exceptions import HTTPException

import config
from db import ER_DUP_ENTRY, ER_NO_REFERENCED_ROW, init_database, to_jsonable, transaction

app = Flask(__name__)
app.json.ensure_ascii = False  # trả tiếng Việt có dấu nguyên vẹn
app.json.sort_keys = False
# Ghi rõ charset: thiếu nó, Windows PowerShell 5.1 (Invoke-RestMethod) đọc theo ISO-8859-1, lỗi tiếng Việt.
app.json.mimetype = "application/json; charset=utf-8"

TOTAL_EXPR = "ROUND(attendance*0.1 + midterm*0.3 + final*0.6, 2)" # công thức tính điểm tổng kết theo 10% chuyên cần, 30% giữa kỳ, 60% cuối kỳ
GRADE_LABELS = ["Giỏi", "Khá", "Trung bình", "Cần cố gắng"]  # theo điểm tổng kết
# Mã SV, mã môn (đã chuyển in hoa): chỉ chữ cái không dấu và chữ số, như SV001, INT1001.
CODE_RE = re.compile(r"[A-Z0-9]+")
# Họ tên: bắt đầu bằng chữ cái (kể cả chữ có dấu), sau đó chỉ có chữ cái, khoảng trắng và ' . -
# ([^\W\d_] = chữ cái Unicode). Không nhận chữ số, ký hiệu, xuống dòng / tab.
NAME_RE = re.compile(r"[^\W\d_](?:[^\W\d_]|[ '.\-])*")
# Lớp: bắt đầu bằng chữ hoặc số, sau đó chỉ có chữ, số, khoảng trắng và - _ . (ví dụ CNTT1, K65-CNTT).
CLASS_RE = re.compile(r"[^\W_][\w .\-]*")
# Email: <tên>@<miền>.<đuôi>, không có khoảng trắng và chỉ một dấu @ (ví dụ an@example.com).
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
# Học kỳ hợp lệ: HK1, HK2 của 3 năm học 2024–2026, mới nhất trước (HK2-2026 ... HK1-2024).
# Giữ giống hằng SEMESTERS trong frontend/app.py (danh sách của ô chọn học kỳ).
SEMESTERS = [f"HK{term}-{year}" for year in (2026, 2025, 2024) for term in (2, 1)]
SEMESTER_ERROR = "Học kỳ phải chọn trong danh sách (HK1 hoặc HK2, năm 2024–2026)."
# Sắp xếp học kỳ theo thời gian (năm giảm dần rồi HK2 trước HK1); sắp theo chữ thì HK2-2025 đứng trước HK1-2026.
SEMESTER_ORDER = "RIGHT({col},4) DESC, {col} DESC"


class ApiError(Exception):
    """Lỗi trả về cho client. `field`: tên ô bị sai (vd "semester"), để giao diện báo ngay tại ô đó."""
    def __init__(self, message, status=400, field=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.field = field


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


def keyword_filter(*columns):
    """Tham số ?q=: trả về (" WHERE c1 LIKE %s ESCAPE '!' OR ...", tham số) để khớp một phần
    trên các cột đã cho. Không có q (hoặc chỉ toàn khoảng trắng) thì ("", None): không lọc
    (None để pymysql không thay %s trong câu SQL).
    % và _ trong từ khóa được tìm như ký tự thường (thoát bằng '!'), không phải ký tự đại diện
    của LIKE: tìm "QA_0" chỉ ra mã có đúng "QA_0". Dùng '!' thay cho '\\' để không phụ thuộc
    chế độ NO_BACKSLASH_ESCAPES của MySQL."""
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return "", None
    escaped = keyword.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    like = f"%{escaped}%"
    return (" WHERE " + " OR ".join(f"{col} LIKE %s ESCAPE '!'" for col in columns),
            (like,) * len(columns))


def check_text(errors, label, value, limit):
    """Kiểm tra một ô chữ bắt buộc; ghi lỗi (nêu rõ ô nào, sai thế nào) vào `errors`.
    Trả về True khi ô hợp lệ về độ dài, để bước kiểm tra định dạng sau đó chỉ chạy khi cần."""
    if not value:
        errors.append(f"{label} không được để trống")
        return False
    if len(value) > limit:
        errors.append(f"{label} tối đa {limit} ký tự (đang có {len(value)})")
        return False
    return True


def raise_if_invalid(errors, what):
    """Có lỗi thì báo một câu liệt kê từng ô sai, ví dụ:
    "Thông tin sinh viên chưa hợp lệ: Họ tên không được để trống; Lớp tối đa 50 ký tự (đang có 51)." """
    if errors:
        raise ApiError(f"Thông tin {what} chưa hợp lệ: " + "; ".join(errors) + ".")


def duplicate_error(exc, duplicate_message, other_message, field):
    """IntegrityError khi thêm / sửa: trùng khóa UNIQUE thì 409 với câu báo trùng, gắn với ô `field`
    (ô mã) để giao diện báo ngay tại ô đó; lỗi khác thì 400."""
    if exc.args and exc.args[0] == ER_DUP_ENTRY:
        return ApiError(duplicate_message, 409, field=field)
    return ApiError(other_message)


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
    if exc.field:
        return jsonify(error=exc.message, field=exc.field), exc.status
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
    # NFC: chữ có dấu gõ theo kiểu tổ hợp (chữ + dấu rời) được gộp lại trước khi kiểm tra và lưu.
    full_name = unicodedata.normalize("NFC", text(data, "full_name"))
    class_name = unicodedata.normalize("NFC", text(data, "class_name"))
    email = text(data, "email")
    errors = []
    if check_text(errors, "Mã SV", student_code, 20) and not CODE_RE.fullmatch(student_code):
        errors.append("Mã SV chỉ gồm chữ cái không dấu và chữ số (ví dụ SV001)")
    if check_text(errors, "Họ tên", full_name, 100) and not NAME_RE.fullmatch(full_name):
        errors.append("Họ tên phải bắt đầu bằng chữ cái và chỉ gồm chữ cái, khoảng trắng, dấu ' . - "
                      "(ví dụ Nguyễn Văn An)")
    if check_text(errors, "Lớp", class_name, 50) and not CLASS_RE.fullmatch(class_name):
        errors.append("Lớp phải bắt đầu bằng chữ hoặc số và chỉ gồm chữ, số, khoảng trắng, dấu - _ . "
                      "(ví dụ CNTT1)")
    if check_text(errors, "Email", email, 120) and not EMAIL_RE.fullmatch(email):
        errors.append("Email không đúng định dạng (ví dụ an@example.com)")
    raise_if_invalid(errors, "sinh viên")
    return student_code, full_name, class_name, email


@app.get("/api/students")
def list_students():
    where, params = keyword_filter("student_code", "full_name", "class_name")
    with transaction() as cur:
        cur.execute("SELECT * FROM students" + where + " ORDER BY id DESC", params)
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
    except pymysql.err.IntegrityError as exc:
        raise duplicate_error(exc, f"Mã sinh viên {values[0]} đã tồn tại.", "Dữ liệu sinh viên không hợp lệ.",
                              "student_code")
    return ok("Đã thêm sinh viên.", 201, id=new_id)


@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    values = validate_student(payload())
    try:
        with transaction() as cur:
            affected = cur.execute(
                "UPDATE students SET student_code=%s,full_name=%s,class_name=%s,email=%s WHERE id=%s",
                (*values, student_id))
    except pymysql.err.IntegrityError as exc:
        raise duplicate_error(exc, f"Mã sinh viên {values[0]} đã tồn tại.", "Dữ liệu sinh viên không hợp lệ.",
                              "student_code")
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

def validate_subject(data):
    code = text(data, "subject_code").upper()
    name = text(data, "subject_name")
    errors = []
    if check_text(errors, "Mã môn", code, 20) and not CODE_RE.fullmatch(code):
        errors.append("Mã môn chỉ gồm chữ cái không dấu và chữ số (ví dụ INT1001)")
    check_text(errors, "Tên môn", name, 120)
    try:
        credits = int(text(data, "credits", "3"))
    except ValueError:
        credits = 0
    if not 1 <= credits <= 10:
        errors.append("Số tín chỉ phải là số nguyên từ 1 đến 10")
    raise_if_invalid(errors, "môn học")
    return code, name, credits


@app.get("/api/subjects")
def list_subjects():
    where, params = keyword_filter("subject_code", "subject_name")
    with transaction() as cur:
        cur.execute("SELECT * FROM subjects" + where + " ORDER BY subject_name", params)
        return jsonify(rows(cur))


@app.get("/api/subjects/<int:subject_id>")
def get_subject(subject_id):
    with transaction() as cur:
        cur.execute("SELECT * FROM subjects WHERE id=%s", (subject_id,))
        subject = cur.fetchone()
    if not subject:
        raise ApiError("Không tìm thấy môn học.", 404)
    return jsonify(to_jsonable(subject))


@app.post("/api/subjects")
def create_subject():
    values = validate_subject(payload())
    try:
        with transaction() as cur:
            cur.execute("INSERT INTO subjects(subject_code,subject_name,credits) VALUES(%s,%s,%s)", values)
            new_id = cur.lastrowid
    except pymysql.err.IntegrityError as exc:
        raise duplicate_error(exc, f"Mã môn học {values[0]} đã tồn tại.", "Dữ liệu môn học không hợp lệ.",
                              "subject_code")
    return ok("Đã thêm môn học.", 201, id=new_id)


@app.put("/api/subjects/<int:subject_id>")
def update_subject(subject_id):
    values = validate_subject(payload())
    try:
        with transaction() as cur:
            affected = cur.execute(
                "UPDATE subjects SET subject_code=%s,subject_name=%s,credits=%s WHERE id=%s",
                (*values, subject_id))
    except pymysql.err.IntegrityError as exc:
        raise duplicate_error(exc, f"Mã môn học {values[0]} đã tồn tại.", "Dữ liệu môn học không hợp lệ.",
                              "subject_code")
    if not affected:
        raise ApiError("Không tìm thấy môn học.", 404)
    return ok("Đã cập nhật môn học.")


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

GRADE_SELECT = f"""SELECT g.*, s.student_code, s.full_name, sub.subject_code, sub.subject_name,
    sub.credits, {TOTAL_EXPR} AS total
    FROM grades g JOIN students s ON s.id=g.student_id
    JOIN subjects sub ON sub.id=g.subject_id"""


def validate_grade(data):
    semester = text(data, "semester")
    if semester not in SEMESTERS:
        raise ApiError(SEMESTER_ERROR, field="semester")
    try:
        student_id = int(text(data, "student_id"))
        subject_id = int(text(data, "subject_id"))
        attendance = float(text(data, "attendance"))
        midterm = float(text(data, "midterm"))
        final = float(text(data, "final"))
        if not all(0 <= x <= 10 for x in (attendance, midterm, final)):
            raise ValueError()
    except ValueError:
        raise ApiError("Điểm phải nằm trong khoảng 0–10 và cần chọn sinh viên, môn học, học kỳ.")
    return student_id, subject_id, semester, attendance, midterm, final


def grade_integrity_error(exc):
    code = exc.args[0] if exc.args else None
    if code == ER_NO_REFERENCED_ROW:
        return ApiError("Sinh viên hoặc môn học không tồn tại.")
    if code == ER_DUP_ENTRY:  # trùng (sinh viên, môn học, học kỳ): khóa uq_grades
        return ApiError("Một sinh viên không thể có nhiều bảng điểm ở cùng một học kỳ.", 409, field="semester")
    return ApiError("Dữ liệu điểm không hợp lệ.")


@app.get("/api/grades")
def list_grades():
    where, params = keyword_filter("s.student_code", "s.full_name", "sub.subject_code",
                                   "sub.subject_name", "g.semester")
    with transaction() as cur:
        cur.execute(GRADE_SELECT + where + " ORDER BY " + SEMESTER_ORDER.format(col="g.semester")
                    + ", s.student_code, sub.subject_name", params)
        return jsonify(rows(cur))


@app.get("/api/grades/<int:grade_id>")
def get_grade(grade_id):
    with transaction() as cur:
        cur.execute(GRADE_SELECT + " WHERE g.id=%s", (grade_id,))
        grade = cur.fetchone()
    if not grade:
        raise ApiError("Không tìm thấy bản ghi điểm.", 404)
    return jsonify(to_jsonable(grade))


@app.post("/api/grades")
def save_grade():
    values = validate_grade(payload())
    try:
        with transaction() as cur:
            # Không ghi đè: bộ (sinh viên, môn học, học kỳ) đã có điểm thì báo trùng (409).
            cur.execute("""INSERT INTO grades(student_id,subject_id,semester,attendance,midterm,final)
                VALUES(%s,%s,%s,%s,%s,%s)""", values)
            new_id = cur.lastrowid
    except pymysql.err.IntegrityError as exc:
        raise grade_integrity_error(exc)
    return ok("Đã lưu điểm. Điểm tổng kết được tính theo 10% chuyên cần, 30% giữa kỳ, 60% cuối kỳ.",
              201, id=new_id)


@app.put("/api/grades/<int:grade_id>")
def update_grade(grade_id):
    values = validate_grade(payload())
    try:
        with transaction() as cur:
            affected = cur.execute("""UPDATE grades SET student_id=%s, subject_id=%s, semester=%s,
                attendance=%s, midterm=%s, final=%s WHERE id=%s""", (*values, grade_id))
    except pymysql.err.IntegrityError as exc:
        raise grade_integrity_error(exc)
    if not affected:
        raise ApiError("Không tìm thấy bản ghi điểm.", 404)
    return ok("Đã cập nhật bản ghi điểm.")


@app.delete("/api/grades/<int:grade_id>")
def delete_grade(grade_id):
    with transaction() as cur:
        affected = cur.execute("DELETE FROM grades WHERE id=%s", (grade_id,))
    if not affected:
        raise ApiError("Không tìm thấy bản ghi điểm.", 404)
    return ok("Đã xóa bản ghi điểm.")


# ---------------------------------------------------------------- học phí

TUITION_SELECT = """SELECT t.*, s.student_code, s.full_name,
    GREATEST(t.amount_due-t.amount_paid, 0) AS balance
    FROM tuition t JOIN students s ON s.id=t.student_id"""


def money(data, key, label, default=""):
    """Đọc một ô số tiền: số thực trong [0, 10^13) (giới hạn của cột DECIMAL(15,2)).
    Sai thì báo lỗi gắn với đúng ô đó. `nan` / `inf` bị từ chối vì không thỏa so sánh."""
    try:
        value = float(text(data, key, default) or default)
    except ValueError:
        raise ApiError(f"{label} phải là một số.", field=key)
    if not 0 <= value < 1e13:
        raise ApiError(f"{label} phải từ 0 đến dưới 10.000 tỷ đồng.", field=key)
    return value


def validate_tuition(data):
    """Kiểm tra lần lượt từng ô; lỗi đầu tiên được báo kèm tên ô (`field`) để giao diện chỉ ra ô đó."""
    try:
        student_id = int(text(data, "student_id"))
    except ValueError:
        raise ApiError("Cần chọn sinh viên.", field="student_id")
    semester = text(data, "semester")
    if semester not in SEMESTERS:
        raise ApiError(SEMESTER_ERROR, field="semester")
    due = money(data, "amount_due", "Học phí phải đóng")
    paid = money(data, "amount_paid", "Số đã đóng", "0")
    if paid > due:
        raise ApiError("Số tiền phải đóng bắt buộc phải lớn hơn hoặc bằng số tiền đã đóng.", field="amount_due")
    due_date = text(data, "due_date")
    if not due_date:
        raise ApiError("Phải nhập thời gian đã đóng học phí.", field="due_date")
    try:
        due_date = date.fromisoformat(due_date).isoformat()  # ngày có thật, lưu dạng YYYY-MM-DD
    except ValueError:
        raise ApiError("Ngày đóng học phí phải là ngày có thật, dạng YYYY-MM-DD.", field="due_date")
    note = text(data, "note")
    if len(note) > 200:
        raise ApiError(f"Ghi chú tối đa 200 ký tự (đang có {len(note)}).", field="note")
    return student_id, semester, due, paid, due_date, note


def tuition_integrity_error(exc):
    if exc.args and exc.args[0] == ER_DUP_ENTRY:  # trùng (sinh viên, học kỳ): khóa uq_tuition
        return ApiError("Một sinh viên không thể đóng nhiều học phí trong cùng một học kỳ.", 409, field="semester")
    return ApiError("Sinh viên không tồn tại.")


@app.get("/api/tuition")
def list_tuition():
    where, params = keyword_filter("s.student_code", "s.full_name", "t.semester")
    with transaction() as cur:
        cur.execute(TUITION_SELECT + where + " ORDER BY " + SEMESTER_ORDER.format(col="t.semester")
                    + ", s.student_code", params)
        return jsonify(rows(cur))


@app.get("/api/tuition/<int:tuition_id>")
def get_tuition(tuition_id):
    with transaction() as cur:
        cur.execute(TUITION_SELECT + " WHERE t.id=%s", (tuition_id,))
        record = cur.fetchone()
    if not record:
        raise ApiError("Không tìm thấy bản ghi học phí.", 404)
    return jsonify(to_jsonable(record))


@app.post("/api/tuition")
def save_tuition():
    values = validate_tuition(payload())
    try:
        with transaction() as cur:
            # Không ghi đè: (sinh viên, học kỳ) đã có học phí thì báo trùng (409).
            cur.execute("""INSERT INTO tuition(student_id,semester,amount_due,amount_paid,due_date,note)
                VALUES(%s,%s,%s,%s,%s,%s)""", values)
            new_id = cur.lastrowid
    except pymysql.err.IntegrityError as exc:
        raise tuition_integrity_error(exc)
    return ok("Đã lưu thông tin học phí.", 201, id=new_id)


@app.put("/api/tuition/<int:tuition_id>")
def update_tuition(tuition_id):
    values = validate_tuition(payload())
    try:
        with transaction() as cur:
            affected = cur.execute("""UPDATE tuition SET student_id=%s, semester=%s, amount_due=%s,
                amount_paid=%s, due_date=%s, note=%s WHERE id=%s""", (*values, tuition_id))
    except pymysql.err.IntegrityError as exc:
        raise tuition_integrity_error(exc)
    if not affected:
        raise ApiError("Không tìm thấy bản ghi học phí.", 404)
    return ok("Đã cập nhật thông tin học phí.")


@app.delete("/api/tuition/<int:tuition_id>")
def delete_tuition(tuition_id):
    with transaction() as cur:
        affected = cur.execute("DELETE FROM tuition WHERE id=%s", (tuition_id,))
    if not affected:
        raise ApiError("Không tìm thấy bản ghi học phí.", 404)
    return ok("Đã xóa bản ghi học phí.")


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
        by_label = {r["label"]: r["amount"] for r in grade_summary}
        grade_labels = GRADE_LABELS if by_label else []
    return jsonify(
        total=counts["total"],
        subject_count=counts["subject_count"],
        grade_count=counts["grade_count"],
        tuition_balance=money["balance"],
        chart_data={
            "gradeLabels": grade_labels,
            "gradeValues": [by_label.get(l, 0) for l in grade_labels],
            "classLabels": [r["label"] for r in class_summary],
            "classValues": [r["amount"] for r in class_summary],
            "tuitionDue": money["due"],
            "tuitionPaid": money["paid"],
            "tuitionBalance": money["balance"],
        },
    )


# ---------------------------------------------------------------- khởi động

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
        raise SystemExit(f"Cổng {port} đang được dùng (có thể backend/app.py đang chạy ở cửa sổ khác). "
                         "Hãy tắt nó trước.")
    finally:
        s.close()


if __name__ == "__main__":
    ensure_port_free(config.API_HOST, config.API_PORT)  # trước init_database: không đụng tới DB
    init_database()
    print(f"Back-end API: http://{config.API_HOST}:{config.API_PORT}  "
          f"(MySQL {config.DB_USER}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME})", flush=True)
    serve(app, host=config.API_HOST, port=config.API_PORT)
