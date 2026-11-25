import json
import os
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template_string, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

# ==============================================================================
# منصة تسيير المؤسسة - ثانوية الشهيد قوديد أحمد (سيدي الشحمي)
# ==============================================================================

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "qadid-ahmed-school-secret-key-2026")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///school_management.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

OFFICIAL_SECTIONS = [
    "1 ج م آ 1", "1 ج م آ 2", "1 ج م ع 1", "1 ج م ع 2",
    "2 آداب وفلسفة 1", "2 آداب وفلسفة 2",
    "2 لغات أجنبية 1", "2 لغات أجنبية 2",
    "2 علوم تجريبية 1", "2 علوم تجريبية 2",
    "2 تسيير واقتصاد 1", "2 رياضيات 1",
    "3 آداب وفلسفة 1", "3 آداب وفلسفة 2", "3 آداب وفلسفة 3",
    "3 لغات أجنبية 1", "3 لغات أجنبية 2", "3 لغات أجنبية 3",
    "3 علوم تجريبية 1", "3 علوم تجريبية 2", "3 علوم تجريبية 3",
    "3 تسيير واقتصاد 1", "3 رياضيات 1",
]


def format_hours(value):
    try:
        val = float(value or 0)
        return f"{val:g}"
    except (ValueError, TypeError):
        return "0"


# ==============================================================================
# نماذج قاعدة البيانات
# ==============================================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(40), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    weekly_hours = db.Column(db.Float, default=0.0)
    sections_json = db.Column(db.Text, default="[]")

    @property
    def sections(self):
        try:
            data = json.loads(self.sections_json or "[]")
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @sections.setter
    def sections(self, value):
        self.sections_json = json.dumps(list(value or []), ensure_ascii=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)


class TeacherSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(80), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)


class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(80), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(30), nullable=False)
    hours = db.Column(db.Float, default=1.0)
    approval_status = db.Column(db.String(30), default="pending")
    approved_by = db.Column(db.String(120), default="")


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)
    teacher_username = db.Column(db.String(80), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), default="غائب")
    hours = db.Column(db.Float, default=1.0)
    approval_status = db.Column(db.String(30), default="pending")
    approved_by = db.Column(db.String(120), default="")


def get_declared_teachers():
    return User.query.filter(
        User.role == "teacher",
        User.weekly_hours.isnot(None),
        User.weekly_hours > 0,
    ).all()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def init_database():
    db.create_all()
    if User.query.count() == 0:
        users = [
            User(username="teacher", password="123456", role="teacher", fullname="الأستاذ فغلو عبد الله", weekly_hours=13.0),
            User(username="counselor", password="123456", role="counselor", fullname="الحارس العام"),
            User(username="censor", password="123456", role="censor", fullname="السيد الناظر"),
            User(username="director", password="123456", role="director", fullname="السيد المدير"),
        ]
        db.session.add_all(users)
        db.session.commit()

    if TeacherSection.query.filter_by(teacher_username="teacher").count() == 0:
        default_secs = ["3 آداب وفلسفة 1", "3 لغات أجنبية 1", "3 علوم تجريبية 1"]
        for s in default_secs:
            db.session.add(TeacherSection(teacher_username="teacher", section_name=s))
        t_user = User.query.filter_by(username="teacher").first()
        if t_user and not t_user.sections:
            t_user.sections = default_secs
        db.session.commit()

    if Student.query.count() == 0:
        sample_students = [
            Student(fullname="بن علي محمد", section_name="3 آداب وفلسفة 1"),
            Student(fullname="سعيدي أمينة", section_name="3 آداب وفلسفة 1"),
            Student(fullname="مرابط يوسف", section_name="3 لغات أجنبية 1"),
            Student(fullname="بوعزة خديجة", section_name="3 علوم تجريبية 1"),
        ]
        db.session.add_all(sample_students)
        db.session.commit()


with app.app_context():
    init_database()


# ==============================================================================
# الدخول والخروج والتوجيه حسب الرتبة
# ==============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = (request.form.get("username") or "").strip()
        pwd = (request.form.get("password") or "").strip()
        user = User.query.filter_by(username=uname, password=pwd).first()
        if user:
            session["username"] = user.username
            session["fullname"] = user.fullname
            session["role"] = user.role
            return redirect(url_for("home"))
        flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "danger")

    return """
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{font-family:'Cairo',sans-serif;}</style></head>
    <body class="bg-slate-100 min-h-screen flex items-center justify-center p-4">
        <div class="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md border-t-4 border-blue-800 space-y-5">
            <div class="text-center space-y-1">
                <p class="text-xs font-bold text-gray-500">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
                <h1 class="text-xl font-extrabold text-blue-950">تسجيل الدخول إلى المنصة</h1>
            </div>
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-700 mb-1">اسم المستخدم</label>
                    <input type="text" name="username" required class="w-full px-3 py-2 border rounded-lg text-sm">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-700 mb-1">كلمة المرور</label>
                    <input type="password" name="password" required class="w-full px-3 py-2 border rounded-lg text-sm">
                </div>
                <button type="submit" class="w-full bg-blue-800 hover:bg-blue-900 text-white font-bold py-2.5 rounded-lg text-sm">دخول</button>
            </form>
        </div>
    </body>
    </html>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    role = session.get("role")
    if role == "teacher":
        return redirect(url_for("teacher_dashboard_view"))
    if role in ("counselor", "advisor", "guidance_counselor"):
        return redirect(url_for("counselor_dashboard_view"))
    if role in ("director", "principal"):
        return redirect(url_for("director_dashboard_view"))
    return redirect(url_for("teacher_dashboard_view"))


# ==============================================================================
# مسارات الأستاذ المساعدة (الساعات والأقسام)
# ==============================================================================

@app.route("/teacher/set-hours", methods=["POST"])
@login_required
def set_teacher_hours():
    if session.get("role") != "teacher":
        return redirect(url_for("home"))
    raw_hours = (request.form.get("weekly_hours") or "").strip()
    try:
        val = float(raw_hours)
        if val > 0:
            user = User.query.filter_by(username=session.get("username")).first()
            if user:
                user.weekly_hours = val
                db.session.commit()
                flash("تم حفظ الحجم الساعي بنجاح.", "success")
    except ValueError:
        pass
    return redirect(url_for("teacher_dashboard_view"))


@app.route("/teacher/add-section", methods=["POST"])
@login_required
def add_section():
    if session.get("role") != "teacher":
        return redirect(url_for("home"))
    sec = request.form.get("section_name")
    uname = session.get("username")
    if sec in OFFICIAL_SECTIONS and not TeacherSection.query.filter_by(
        teacher_username=uname, section_name=sec
    ).first():
        db.session.add(TeacherSection(teacher_username=uname, section_name=sec))
        user = User.query.filter_by(username=uname).first()
        if user and sec not in user.sections:
            user.sections = user.sections + [sec]
        db.session.commit()
    return redirect(url_for("teacher_dashboard_view", section=sec))


@app.route("/teacher/remove-section/<int:sid>")
@login_required
def remove_section(sid):
    if session.get("role") != "teacher":
        return redirect(url_for("home"))
    ts = TeacherSection.query.get(sid)
    if ts and ts.teacher_username == session.get("username"):
        sec_name = ts.section_name
        db.session.delete(ts)
        user = User.query.filter_by(username=session.get("username")).first()
        if user and sec_name in user.sections:
            user.sections = [s for s in user.sections if s != sec_name]
        db.session.commit()
    return redirect(url_for("teacher_dashboard_view"))


# ==============================================================================
# [بداية التعديل المنفرد] دفتر النصوص المباشر + الغياب المشترك + تقرير الحارس العام للمدير
# ==============================================================================

COUNSELOR_ROLES = ("counselor", "advisor", "guidance_counselor")
DIRECTOR_ROLES = ("director", "principal")
TEACHER_ROLES = ("teacher",)


def _mod_bind_view(rule, endpoint_name, view_func, **options):
    """ربط أو استبدال endpoint في view_functions بأمان دون لمس url_map._rules."""
    app.view_functions[endpoint_name] = view_func
    existing_rule = None
    for r in app.url_map.iter_rules():
        if r.rule == rule:
            existing_rule = r
            break
    if existing_rule is not None:
        existing_rule.endpoint = endpoint_name
        app.url_map._rules_by_endpoint.setdefault(endpoint_name, []).append(existing_rule)
    else:
        options["endpoint"] = endpoint_name
        app.add_url_rule(rule, view_func=view_func, **options)
    return view_func


with app.app_context():
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS counselor_director_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            counselor_username VARCHAR(80),
            counselor_name VARCHAR(120),
            created_at VARCHAR(50),
            total_student_absences INTEGER DEFAULT 0,
            total_student_absent_hours FLOAT DEFAULT 0.0,
            total_teacher_absences INTEGER DEFAULT 0,
            total_teacher_absent_hours FLOAT DEFAULT 0.0,
            counselor_members_count INTEGER DEFAULT 0,
            report_summary TEXT,
            sent_to_director BOOLEAN DEFAULT 1
        )
    """))
    db.session.commit()


def _mod_get_counselor_members():
    return User.query.filter(User.role.in_(COUNSELOR_ROLES)).all()


def _mod_get_teacher_absences_stats():
    inspector = inspect(db.engine)
    if "teacher_attendance" in inspector.get_table_names():
        rows = db.session.execute(
            text("SELECT teacher_name, hours FROM teacher_attendance")
        ).fetchall()
        count = len(rows)
        hours = sum(float(r[1] or 0) for r in rows)
        return count, hours, rows
    return 0, 0.0, []


def _mod_build_counselor_report_data():
    student_absences = Attendance.query.all()
    student_absence_count = len(student_absences)
    student_absence_hours = sum(float(a.hours or 1.0) for a in student_absences)
    teacher_absence_count, teacher_absence_hours, _ = _mod_get_teacher_absences_stats()
    counselor_members = _mod_get_counselor_members()
    return {
        "student_absence_count": student_absence_count,
        "student_absence_hours": student_absence_hours,
        "teacher_absence_count": teacher_absence_count,
        "teacher_absence_hours": teacher_absence_hours,
        "counselor_members": counselor_members,
        "counselor_members_count": len(counselor_members),
    }


@login_required
def mod_submit_lesson():
    if session.get("role") not in TEACHER_ROLES:
        return redirect(url_for("home"))
    sec = (request.form.get("section_name") or "").strip()
    title = (request.form.get("lesson_title") or "").strip()
    content = (request.form.get("content") or "").strip()
    date = (request.form.get("date") or datetime.now().strftime("%Y-%m-%d")).strip()
    try:
        hours_val = float(request.form.get("hours") or 1.0)
        if hours_val <= 0:
            hours_val = 1.0
    except ValueError:
        hours_val = 1.0

    if sec and title and content and date:
        db.session.add(
            LessonLog(
                teacher_username=session.get("username"),
                teacher_name=session.get("fullname"),
                section_name=sec,
                lesson_title=title,
                content=content,
                date=date,
                hours=hours_val,
                approval_status="approved",
                approved_by="مباشر - الأستاذ",
            )
        )
        db.session.commit()
        flash("تم تسجيل الحصة في دفتر النصوص الخاص بك مباشرة.", "success")
    return redirect(url_for("teacher_dashboard_view", section=sec))


_mod_bind_view("/teacher/submit-lesson", "submit_lesson", mod_submit_lesson, methods=["POST"])


@login_required
def mod_send_lesson_to_director(lid):
    if session.get("role") not in TEACHER_ROLES:
        return redirect(url_for("home"))
    lesson = LessonLog.query.get(lid)
    if lesson and lesson.teacher_username == session.get("username"):
        lesson.approved_by = "مرسل للمدير"
        db.session.commit()
        flash(f"تم إرسال الحصة ({lesson.lesson_title}) إلى السيد المدير فقط.", "success")
    return redirect(url_for("teacher_dashboard_view", section=lesson.section_name if lesson else ""))


_mod_bind_view("/teacher/send-lesson-to-director/<int:lid>", "mod_send_lesson_to_director", mod_send_lesson_to_director, methods=["POST"])


@login_required
def mod_mark_absence():
    if session.get("role") not in TEACHER_ROLES:
        return redirect(url_for("home"))
    student_name = (request.form.get("student_name") or "").strip()
    section_name = (request.form.get("section_name") or "").strip()
    date = (request.form.get("date") or datetime.now().strftime("%Y-%m-%d")).strip()
    selected_section = (request.form.get("selected_section") or section_name).strip()
    try:
        hours_val = float(request.form.get("hours") or 1.0)
        if hours_val <= 0:
            hours_val = 1.0
    except ValueError:
        hours_val = 1.0

    if student_name and section_name and date:
        existing = Attendance.query.filter_by(student_name=student_name, date=date).first()
        if not existing:
            db.session.add(
                Attendance(
                    student_name=student_name,
                    section_name=section_name,
                    teacher_username=session.get("username"),
                    teacher_name=session.get("fullname"),
                    date=date,
                    status="غائب",
                    hours=hours_val,
                    approval_status="approved",
                    approved_by="مسجل آنياً (أستاذ + حارس عام)",
                )
            )
            db.session.commit()
            flash("تم تسجيل الغياب في لوحتك ولوحة الحارس العام في الوقت نفسه.", "success")
        else:
            flash("غياب هذا التلميذ مسجل مسبقاً في هذا التاريخ.", "danger")
    return redirect(url_for("teacher_dashboard_view", section=selected_section))


_mod_bind_view("/teacher/mark-absence", "mark_absence", mod_mark_absence, methods=["POST"])


@login_required
def mod_teacher_dashboard_view():
    if session.get("role") not in TEACHER_ROLES:
        return redirect(url_for("home"))

    teacher_uname = session.get("username")
    teacher_user = User.query.filter_by(username=teacher_uname).first()
    today_date = datetime.now().strftime("%Y-%m-%d")

    assigned_sections = TeacherSection.query.filter_by(teacher_username=teacher_uname).all()
    assigned_section_names = [ts.section_name for ts in assigned_sections]
    selected_section = request.args.get("section", assigned_section_names[0] if assigned_section_names else "")
    students_in_section = Student.query.filter_by(section_name=selected_section).all() if selected_section else []

    my_sections_options = "".join([
        f'<option value="{sec}" {"selected" if sec == selected_section else ""}>{sec}</option>'
        for sec in assigned_section_names
    ])
    all_sections_options = "".join([
        f'<option value="{sec}">{sec}</option>'
        for sec in OFFICIAL_SECTIONS
        if sec not in assigned_section_names
    ])

    declared_hours = (
        teacher_user.weekly_hours
        if teacher_user and teacher_user.weekly_hours is not None and float(teacher_user.weekly_hours) > 0
        else None
    )
    hours_display = f"{format_hours(declared_hours)} سا/أسبوع" if declared_hours is not None else "غير محدد بعد"
    hours_input_val = format_hours(declared_hours) if declared_hours is not None else ""

    my_lessons = LessonLog.query.filter_by(teacher_username=teacher_uname).all()
    my_absences = Attendance.query.filter_by(teacher_username=teacher_uname).all()
    sent_to_director_count = sum(1 for l in my_lessons if l.approved_by == "مرسل للمدير")
    total_lesson_hours = sum(float(l.hours or 0) for l in my_lessons)

    attendance_rows = "".join([f"""
    <tr class="border-b hover:bg-gray-50">
        <td class="py-2.5 px-3 text-sm font-semibold text-gray-800">{s.fullname}</td>
        <td class="py-2.5 px-3 text-sm text-gray-600">{s.section_name}</td>
        <td class="py-2.5 px-3 text-center">
            <form action="/teacher/mark-absence" method="POST" class="inline-flex items-center gap-1.5">
                <input type="hidden" name="student_name" value="{s.fullname}">
                <input type="hidden" name="section_name" value="{s.section_name}">
                <input type="hidden" name="date" value="{today_date}">
                <input type="hidden" name="selected_section" value="{selected_section}">
                <input type="number" step="0.5" min="0.5" max="12" name="hours" value="1" class="w-16 px-2 py-1 border rounded text-xs text-center font-bold">
                <button type="submit" class="bg-red-50 text-red-600 border border-red-200 hover:bg-red-600 hover:text-white px-3 py-1 rounded text-xs font-bold transition">تسجيل غياب (أستاذ + حارس عام)</button>
            </form>
        </td>
    </tr>
    """ for s in students_in_section]) or "<tr><td colspan='3' class='text-center py-4 text-gray-400 text-xs'>اختر قسماً لعرض قائمة المناداة.</td></tr>"

    my_sections_list_html = "".join([f"""
    <div class="flex justify-between items-center bg-gray-50 px-3 py-2 rounded-lg border text-xs">
        <span class="font-bold text-blue-900">{ts.section_name}</span>
        <a href="/teacher/remove-section/{ts.id}" class="text-red-600 hover:underline">حذف</a>
    </div>
    """ for ts in assigned_sections]) or "<p class='text-xs text-gray-400'>لم تضف أي قسم بعد.</p>"

    lessons_rows = "".join([f"""
    <tr class='border-b text-xs'>
        <td class='py-2 px-3 font-bold'>{l.section_name}</td>
        <td class='py-2 px-3'>{l.lesson_title}</td>
        <td class='py-2 px-3 font-bold'>{format_hours(l.hours)} سا</td>
        <td class='py-2 px-3'>{l.date}</td>
        <td class='py-2 px-3'>
            {"<span class='bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-bold'>مُرسلة للمدير</span>" if l.approved_by == "مرسل للمدير" else "<span class='bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-bold'>محفوظة عند الأستاذ</span>"}
        </td>
        <td class='py-2 px-3'>
            {"<span class='text-emerald-700 font-bold'>تم الإرسال</span>" if l.approved_by == "مرسل للمدير" else f"<form action='/teacher/send-lesson-to-director/{l.id}' method='POST' class='inline'><button type='submit' class='bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded font-bold'>إرسال للمدير</button></form>"}
        </td>
    </tr>
    """ for l in reversed(my_lessons)]) or "<tr><td colspan='6' class='text-center py-4 text-gray-400 text-xs'>لا توجد حصص مسجلة في دفتر النصوص بعد.</td></tr>"

    return f"""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-4 md:p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 border-b-4 border-blue-800 space-y-4">
                <div class="text-center space-y-1">
                    <p class="text-xs font-bold text-gray-600">الجمهورية الجزائرية الديمقراطية الشعبية | وزارة التربية الوطنية</p>
                    <h2 class="text-lg font-extrabold text-blue-900">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</h2>
                </div>
                <div class="pt-3 flex flex-wrap justify-between items-center border-t text-sm gap-2">
                    <span class="font-bold text-gray-700">الأستاذ: {session.get('fullname')} | التاريخ: {today_date}</span>
                    <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-red-100">تسجيل الخروج</a>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
                    <div class="bg-blue-50 border border-blue-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-blue-700">حجمي الساعي الفعلي</div>
                        <div class="text-base font-extrabold text-blue-950 mt-1">{hours_display}</div>
                    </div>
                    <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-emerald-700">ساعات حصص دفتر النصوص</div>
                        <div class="text-base font-extrabold text-emerald-950 mt-1">{format_hours(total_lesson_hours)} سا</div>
                    </div>
                    <div class="bg-indigo-50 border border-indigo-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-indigo-700">حصص مرسلة للمدير</div>
                        <div class="text-base font-extrabold text-indigo-950 mt-1">{sent_to_director_count}</div>
                    </div>
                    <div class="bg-rose-50 border border-rose-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-rose-700">غيابات مسجلة من طرفي</div>
                        <div class="text-base font-extrabold text-rose-950 mt-1">{len(my_absences)}</div>
                    </div>
                </div>
                <form action="/teacher/set-hours" method="POST" class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3">
                    <div class="text-xs font-bold text-slate-700">تحديد/تعديل حجمك الساعي الفعلي:</div>
                    <div class="flex items-center gap-2">
                        <input type="number" step="0.5" min="1" max="50" name="weekly_hours" value="{hours_input_val}" placeholder="مثال: 13" required class="w-28 px-3 py-1.5 border rounded-lg text-xs font-bold text-center bg-white">
                        <button type="submit" class="bg-blue-700 hover:bg-blue-800 text-white font-bold px-4 py-1.5 rounded-lg text-xs transition">حفظ الحجم الساعي</button>
                    </div>
                </form>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white rounded-2xl shadow-md p-5 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2">إدارة أقسامي المسندة</h3>
                    <form action="/teacher/add-section" method="POST" class="space-y-3">
                        <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                            <option value="" disabled selected>-- اختر قسماً لإضافته --</option>
                            {all_sections_options}
                        </select>
                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-lg text-xs transition">إضافة إلى أقسامي</button>
                    </form>
                    <div class="space-y-2 mt-3 max-h-48 overflow-y-auto border-t pt-2">{my_sections_list_html}</div>
                </div>

                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-2 space-y-4">
                    <div class="flex justify-between items-center border-b pb-2">
                        <h3 class="text-md font-bold text-gray-800">قائمة المناداة وتسجيل الغيابات</h3>
                        <form method="GET" action="/teacher/dashboard-view" class="flex gap-2">
                            <select name="section" onchange="this.form.submit()" class="px-3 py-1.5 rounded-lg border text-xs bg-white font-bold text-blue-800">
                                <option value="" disabled selected>-- اختر القسم --</option>
                                {my_sections_options}
                            </select>
                        </form>
                    </div>
                    <div class="overflow-x-auto max-h-96">
                        <table class="w-full text-right">
                            <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-2.5 px-3">التلميذ</th><th class="py-2.5 px-3">القسم</th><th class="py-2.5 px-3 text-center">إجراء الغياب</th></tr></thead>
                            <tbody>{attendance_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-md p-6 space-y-4">
                <h3 class="text-md font-bold text-gray-800">دفتر النصوص (تسجيل مباشر عند الأستاذ — يُرسل للمدير عند الطلب)</h3>
                <form action="/teacher/submit-lesson" method="POST" class="grid grid-cols-1 md:grid-cols-5 gap-3">
                    <div><select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white"><option value="" disabled selected>-- اختر القسم --</option>{my_sections_options}</select></div>
                    <div><input type="text" name="lesson_title" placeholder="عنوان الدرس..." required class="w-full px-3 py-2 rounded-lg border text-xs"></div>
                    <div><input type="text" name="content" placeholder="الملخص..." required class="w-full px-3 py-2 rounded-lg border text-xs"></div>
                    <div><input type="number" step="0.5" min="0.5" max="12" name="hours" value="1" placeholder="عدد الساعات" required class="w-full px-3 py-2 rounded-lg border text-xs font-bold"></div>
                    <div class="flex gap-2">
                        <input type="date" name="date" value="{today_date}" required class="w-full px-3 py-2 rounded-lg border text-xs">
                        <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-lg text-xs whitespace-nowrap">تسجيل الحصة</button>
                    </div>
                </form>

                <div class="overflow-x-auto pt-2">
                    <table class="w-full text-right">
                        <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-2 px-3">القسم</th><th class="py-2 px-3">الدرس</th><th class="py-2 px-3">الساعات</th><th class="py-2 px-3">التاريخ</th><th class="py-2 px-3">الحالة</th><th class="py-2 px-3">إرسال للمدير</th></tr></thead>
                        <tbody>{lessons_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


_mod_bind_view("/teacher/dashboard-view", "teacher_dashboard_view", mod_teacher_dashboard_view, methods=["GET"])


@login_required
def mod_submit_report_to_director():
    if session.get("role") not in COUNSELOR_ROLES:
        return redirect(url_for("home"))

    stats = _mod_build_counselor_report_data()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_text = (
        f"تقرير شامل بتاريخ {now_str}: "
        f"غيابات التلاميذ ({stats['student_absence_count']} حالة / {format_hours(stats['student_absence_hours'])} سا)، "
        f"غيابات الأساتذة ({stats['teacher_absence_count']} حالة / {format_hours(stats['teacher_absence_hours'])} سا)، "
        f"أعضاء الاستشارة ({stats['counselor_members_count']} عضو)."
    )

    db.session.execute(
        text(
            "INSERT INTO counselor_director_report ("
            "counselor_username, counselor_name, created_at, "
            "total_student_absences, total_student_absent_hours, "
            "total_teacher_absences, total_teacher_absent_hours, "
            "counselor_members_count, report_summary, sent_to_director"
            ") VALUES ("
            ":u, :n, :dt, :sa, :sah, :ta, :tah, :cm, :sm, 1"
            ")"
        ),
        {
            "u": session.get("username"),
            "n": session.get("fullname"),
            "dt": now_str,
            "sa": stats["student_absence_count"],
            "sah": stats["student_absence_hours"],
            "ta": stats["teacher_absence_count"],
            "tah": stats["teacher_absence_hours"],
            "cm": stats["counselor_members_count"],
            "sm": summary_text,
        },
    )
    db.session.commit()
    flash("تم رفع تقرير الغيابات الشامل إلى السيد المدير.", "success")
    return redirect(url_for("counselor_dashboard_view"))


_mod_bind_view("/counselor/submit-report-to-director", "mod_submit_report_to_director", mod_submit_report_to_director, methods=["POST"])


@login_required
def mod_counselor_dashboard_view():
    if session.get("role") not in COUNSELOR_ROLES:
        return redirect(url_for("home"))

    attendances = Attendance.query.all()
    stats = _mod_build_counselor_report_data()
    declared_teachers = get_declared_teachers()

    counselor_members_html = "".join([
        (
            "<span class='bg-amber-50 text-amber-900 border border-amber-200 px-3 py-1 rounded-lg text-xs font-bold'>"
            f"{m.fullname}"
            "</span>"
        )
        for m in stats["counselor_members"]
    ]) or "<span class='text-xs text-gray-400'>لا يوجد أعضاء استشارة مسجلون حالياً.</span>"

    declared_teachers_cards = "".join([
        (
            "<div class='bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs flex justify-between items-center gap-3'>"
            f"<span class='font-bold text-slate-800'>{t.fullname}</span>"
            f"<span class='bg-blue-100 text-blue-900 font-extrabold px-2.5 py-1 rounded-lg'>{format_hours(t.weekly_hours)} سا/أسبوع</span>"
            "</div>"
        )
        for t in declared_teachers
    ]) or "<p class='text-xs text-slate-400'>لم يحدد أي أستاذ حجمه الساعي بعد.</p>"

    att_rows = "".join([
        (
            "<tr class='border-b text-xs'>"
            f"<td class='py-2.5 px-3 font-bold'>{a.student_name}</td>"
            f"<td class='py-2.5 px-3'>{a.section_name}</td>"
            f"<td class='py-2.5 px-3'>{a.teacher_name}</td>"
            f"<td class='py-2.5 px-3'>{a.date}</td>"
            f"<td class='py-2.5 px-3 font-extrabold text-red-700'>{format_hours(a.hours)} سا</td>"
            "</tr>"
        )
        for a in reversed(attendances)
    ]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400 text-xs'>لا توجد غيابات مسجلة بعد.</td></tr>"

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 border-r-8 border-amber-600 space-y-4">
                <div class="flex flex-wrap justify-between items-center gap-2">
                    <div>
                        <h1 class="text-xl font-bold text-gray-800">مكتب الاستشارة التربوية - الحارس العام</h1>
                        <p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
                    </div>
                    <div class="flex items-center gap-2">
                        <form action="/counselor/submit-report-to-director" method="POST" class="inline">
                            <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-xs font-bold shadow">رفع تقرير الغيابات للمدير</button>
                        </form>
                        <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
                    </div>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <div class="bg-rose-50 border border-rose-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-rose-700">غيابات التلاميذ (حالات / ساعات)</div>
                        <div class="text-base font-extrabold text-rose-950 mt-1">{stats['student_absence_count']} / {format_hours(stats['student_absence_hours'])} سا</div>
                    </div>
                    <div class="bg-orange-50 border border-orange-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-orange-800">غيابات الأساتذة (حالات / ساعات)</div>
                        <div class="text-base font-extrabold text-orange-950 mt-1">{stats['teacher_absence_count']} / {format_hours(stats['teacher_absence_hours'])} سا</div>
                    </div>
                    <div class="bg-amber-50 border border-amber-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-amber-800">عدد أعضاء الاستشارة</div>
                        <div class="text-base font-extrabold text-amber-950 mt-1">{stats['counselor_members_count']}</div>
                    </div>
                    <div class="bg-blue-50 border border-blue-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-blue-700">أساتذة حددوا حجمهم الساعي</div>
                        <div class="text-base font-extrabold text-blue-950 mt-1">{len(declared_teachers)}</div>
                    </div>
                </div>
                <div class="border-t pt-3 space-y-2">
                    <div class="text-xs font-bold text-slate-700">أعضاء الاستشارة التربوية:</div>
                    <div class="flex flex-wrap gap-2">{counselor_members_html}</div>
                </div>
                <div class="border-t pt-3 space-y-2">
                    <div class="text-xs font-bold text-slate-700">الحجم الساعي الفعلي للأساتذة:</div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">{declared_teachers_cards}</div>
                </div>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">سجل غيابات التلاميذ الواردة من لوحة الأستاذ تلقائياً</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-right">
                        <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-2.5 px-3">التلميذ</th><th class="py-2.5 px-3">القسم</th><th class="py-2.5 px-3">الأستاذ</th><th class="py-2.5 px-3">التاريخ</th><th class="py-2.5 px-3">الساعات</th></tr></thead>
                        <tbody>{att_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </body></html>
    """


_mod_bind_view("/counselor/dashboard-view", "counselor_dashboard_view", mod_counselor_dashboard_view, methods=["GET"])


@login_required
def mod_director_dashboard_view():
    if session.get("role") not in DIRECTOR_ROLES:
        return redirect(url_for("home"))

    sent_lessons = LessonLog.query.filter_by(approved_by="مرسل للمدير").all()
    declared_teachers = get_declared_teachers()
    reports = db.session.execute(
        text(
            "SELECT id, counselor_name, created_at, total_student_absences, "
            "total_student_absent_hours, total_teacher_absences, "
            "total_teacher_absent_hours, counselor_members_count, report_summary "
            "FROM counselor_director_report ORDER BY id DESC"
        )
    ).fetchall()

    latest_report = reports[0] if reports else None
    latest_student_abs = (
        f"{latest_report[3]} / {format_hours(latest_report[4])} سا"
        if latest_report
        else "لم يُرفع تقرير بعد"
    )
    latest_teacher_abs = (
        f"{latest_report[5]} / {format_hours(latest_report[6])} سا"
        if latest_report
        else "لم يُرفع تقرير بعد"
    )
    latest_counselor_cnt = f"{latest_report[7]}" if latest_report else "0"

    declared_teachers_html = "".join([
        (
            "<div class='bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs flex justify-between items-center'>"
            f"<span class='font-bold text-slate-800'>{t.fullname}</span>"
            f"<span class='bg-blue-100 text-blue-900 font-extrabold px-3 py-1 rounded-lg'>{format_hours(t.weekly_hours)} سا/أسبوع</span>"
            "</div>"
        )
        for t in declared_teachers
    ]) or "<p class='text-xs text-slate-400'>لا توجد حجوم ساعية محددة من طرف الأساتذة بعد.</p>"

    sent_lessons_rows = "".join([
        (
            "<tr class='border-b text-xs'>"
            f"<td class='py-2.5 px-3'>{l.teacher_name}</td>"
            f"<td class='py-2.5 px-3'>{l.section_name}</td>"
            f"<td class='py-2.5 px-3 font-bold'>{l.lesson_title}</td>"
            f"<td class='py-2.5 px-3 font-bold'>{format_hours(l.hours)} سا</td>"
            f"<td class='py-2.5 px-3'>{l.date}</td>"
            "</tr>"
        )
        for l in reversed(sent_lessons)
    ]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400 text-xs'>لم يرسل أي أستاذ حصصاً للمدير بعد.</td></tr>"

    reports_rows = "".join([
        (
            "<tr class='border-b text-xs'>"
            f"<td class='py-2.5 px-3 font-bold'>{r[1] or '-'}</td>"
            f"<td class='py-2.5 px-3'>{r[2] or '-'}</td>"
            f"<td class='py-2.5 px-3'>{r[3]} ({format_hours(r[4])} سا)</td>"
            f"<td class='py-2.5 px-3'>{r[5]} ({format_hours(r[6])} سا)</td>"
            f"<td class='py-2.5 px-3 font-bold'>{r[7]}</td>"
            "</tr>"
        )
        for r in reports
    ]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400 text-xs'>لا توجد تقارير مرفوعة من الحارس العام بعد.</td></tr>"

    return f"""
    <html lang="ar" dir="rtl"><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 border-r-8 border-blue-800 space-y-4">
                <div class="flex flex-wrap justify-between items-center gap-2">
                    <div>
                        <h1 class="text-xl font-bold text-gray-800">لوحة القيادة الشاملة - السيد المدير</h1>
                        <p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
                    </div>
                    <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    <div class="bg-rose-50 border border-rose-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-rose-700">غيابات التلاميذ (آخر تقرير مرفوع)</div>
                        <div class="text-base font-extrabold text-rose-950 mt-1">{latest_student_abs}</div>
                    </div>
                    <div class="bg-orange-50 border border-orange-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-orange-800">غيابات الأساتذة (آخر تقرير مرفوع)</div>
                        <div class="text-base font-extrabold text-orange-950 mt-1">{latest_teacher_abs}</div>
                    </div>
                    <div class="bg-amber-50 border border-amber-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-amber-800">أعضاء الاستشارة (آخر تقرير مرفوع)</div>
                        <div class="text-base font-extrabold text-amber-950 mt-1">{latest_counselor_cnt}</div>
                    </div>
                    <div class="bg-blue-50 border border-blue-200 rounded-xl p-3.5">
                        <div class="text-[11px] font-bold text-blue-700">أساتذة حددوا حجمهم الساعي</div>
                        <div class="text-base font-extrabold text-blue-950 mt-1">{len(declared_teachers)}</div>
                    </div>
                </div>
                <div class="border-t pt-3 space-y-2">
                    <div class="text-xs font-bold text-slate-700">الحجم الساعي الفعلي للأساتذة:</div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">{declared_teachers_html}</div>
                </div>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">تقارير الغيابات المرفوعة من الحارس العام</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-right">
                        <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-2.5 px-3">الحارس العام</th><th class="py-2.5 px-3">تاريخ الرفع</th><th class="py-2.5 px-3">غيابات التلاميذ</th><th class="py-2.5 px-3">غيابات الأساتذة</th><th class="py-2.5 px-3">أعضاء الاستشارة</th></tr></thead>
                        <tbody>{reports_rows}</tbody>
                    </table>
                </div>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">حصص دفتر النصوص المرسلة للمدير فقط</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-right">
                        <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-2.5 px-3">الأستاذ</th><th class="py-2.5 px-3">القسم</th><th class="py-2.5 px-3">الدرس</th><th class="py-2.5 px-3">الساعات</th><th class="py-2.5 px-3">التاريخ</th></tr></thead>
                        <tbody>{sent_lessons_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </body></html>
    """


_mod_bind_view("/director/dashboard-view", "director_dashboard_view", mod_director_dashboard_view, methods=["GET"])

# ==============================================================================
# [نهاية التعديل المنفرد]
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
