# ==============================================================================
# البداية: استيراد المكتبات وإعداد التطبيق وقاعدة البيانات المركزية
# ==============================================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# إعداد قاعدة البيانات الموحدة للمنصة
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'philo_school_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 1. جدول المستخدمين والأدوار
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)

# 2. جدول التلاميذ المسجلين للأقسام
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    teacher_username = db.Column(db.String(80), nullable=False)

# 3. جدول الغيابات اليومية
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='غائب')

# 4. جدول دفتر النصوص الرقمي
class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

# قائمة الأقسام الرسمية المعتمدة
OFFICIAL_SECTIONS = [
    "1ج م ع01", "1ج م ع02", "1ج م ع03", "1ج م ع04", "1ج م ع05",
    "1ج م أ01", "1ج م أ02", "1ج م أ03",
    "2أف1", "2أف2",
    "2ع ت1", "2ع ت2",
    "2لغ", "2ريا", "2تق", "2تر",
    "3أف1", "3أف2", "3لغ", "3ع ت1", "3ع ت2", "3ريا", "3ت ر"
]

# إنشاء الجداول وتوليد الحسابات الافتراضية عند التشغيل الأول
with app.app_context():
    try:
        db.create_all()
        if not User.query.first():
            default_users = [
                User(username='director', password='123456', role='director', fullname='السيد المدير'),
                User(username='deputy', password='123456', role='inspector_deputy', fullname='السيد الناظر'),
                User(username='counselor', password='123456', role='counselor', fullname='السيد مستشار التربية'),
                User(username='teacher', password='123456', role='teacher', fullname='الأستاذ الفاضل')
            ]
            db.session.add_all(default_users)
            db.session.commit()
    except Exception as e:
        print(f"Database error: {e}")

# ==============================================================================
# مسارات المصادقة والتسجيل
# ==============================================================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة تسيير المؤسسة - تسجيل الدخول</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-xl font-bold text-gray-800">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</h1>
            <p class="text-sm text-blue-600 font-semibold mt-1">منصة تسيير المؤسسة التربوية</p>
        </div>
        {% if message %}
        <div class="mb-4 p-3 bg-emerald-50 text-emerald-700 text-xs rounded-lg text-center font-bold border border-emerald-200">
            {{ message }}
        </div>
        {% endif %}
        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" placeholder="مثال: teacher أو director" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" placeholder="123456" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الصفة التربوية (الدور)</label>
                <select name="role" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition bg-white">
                    <option value="" disabled selected>-- اختر صفتك في المؤسسة --</option>
                    <option value="director">المدير (Director)</option>
                    <option value="inspector_deputy">الناظر (Deputy Principal)</option>
                    <option value="counselor">مستشار التربية (Counselor)</option>
                    <option value="teacher">أستاذ (Teacher)</option>
                </select>
            </div>
            <button type="submit" class="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-3 rounded-lg shadow-lg transition duration-300">
                دخول إلى لوحة التحكم
            </button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '')

    user = User.query.filter_by(username=username).first()
    if not user or user.password != password or user.role != role:
        return render_template_string(LOGIN_TEMPLATE, message="بيانات الدخول غير صحيحة!")

    session['username'] = user.username
    session['fullname'] = user.fullname
    session['role'] = user.role

    if role == 'teacher':
        return redirect(url_for('teacher_dashboard_view'))
    elif role == 'counselor':
        return redirect(url_for('counselor_dashboard_view'))
    elif role == 'director':
        return redirect(url_for('director_dashboard_view'))
    elif role == 'inspector_deputy':
        return redirect(url_for('deputy_dashboard_view'))
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ==============================================================================
# لوحة تحكم الأستاذ
# ==============================================================================

@app.route('/teacher/dashboard-view')
def teacher_dashboard_view():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    teacher_uname = session.get('username')
    students = Student.query.filter_by(teacher_username=teacher_uname).all()
    today_date = datetime.now().strftime('%Y-%m-%d')

    section_options_html = "".join([f'<option value="{sec}">{sec}</option>' for sec in OFFICIAL_SECTIONS])

    attendance_rows = ""
    for s in students:
        attendance_rows += f"""
        <tr class="border-b hover:bg-gray-50">
            <td class="py-2.5 px-3 text-sm font-semibold text-gray-800">{s.fullname}</td>
            <td class="py-2.5 px-3 text-sm text-gray-600">{s.section_name}</td>
            <td class="py-2.5 px-3 text-center">
                <form action="/teacher/mark-absence" method="POST" class="inline">
                    <input type="hidden" name="student_name" value="{s.fullname}">
                    <input type="hidden" name="section_name" value="{s.section_name}">
                    <input type="hidden" name="date" value="{today_date}">
                    <button type="submit" class="bg-red-50 text-red-600 border border-red-200 hover:bg-red-600 hover:text-white px-3 py-1 rounded text-xs font-bold transition">تسجيل غياب اليوم</button>
                </form>
            </td>
        </tr>
        """
    if not attendance_rows:
        attendance_rows = "<tr><td colspan='3' class='text-center py-4 text-gray-400 text-xs'>لا توجد تلاميذ مسجلين. قم بإضافة التلاميذ أدناه.</td></tr>"

    student_manage_rows = ""
    for s in students:
        student_manage_rows += f"""
        <tr class="border-b">
            <td class="py-2 px-2 text-xs text-gray-800">{s.fullname}</td>
            <td class="py-2 px-2 text-xs text-gray-600">{s.section_name}</td>
            <td class="py-2 px-2 text-xs text-center">
                <a href="/teacher/delete-student/{s.id}" class="text-red-600 hover:underline font-bold">حذف</a>
            </td>
        </tr>
        """

    return f"""
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>البوابة البيداغوجية - الأستاذ</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Cairo', sans-serif; }}</style>
    </head>
    <body class="bg-slate-100 min-h-screen p-4 md:p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 text-center border-b-4 border-blue-800 space-y-1">
                <p class="text-xs font-bold text-gray-600">الجمهورية الجزائرية الديمقراطية الشعبية</p>
                <p class="text-xs font-semibold text-gray-600">وزارة التربية الوطنية</p>
                <p class="text-xs font-semibold text-gray-600">مديرية التربية لولاية وهران</p>
                <div class="my-2"></div>
                <h2 class="text-lg font-extrabold text-blue-900">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</h2>
                <div class="pt-2 flex justify-between items-center border-t mt-4 text-sm">
                    <span class="font-bold text-gray-700">الأستاذ: {session.get('fullname')} | تاريخ اليوم: {today_date}</span>
                    <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-red-100">تسجيل الخروج</a>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-2 space-y-4">
                    <div class="flex justify-between items-center border-b pb-2">
                        <h3 class="text-md font-bold text-gray-800 flex items-center gap-2">
                            <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span> القائمة الاسمية للأقسام المسندة (تسجيل الغيابات اليومية)
                        </h3>
                    </div>
                    <div class="overflow-x-auto max-h-96">
                        <table class="w-full text-right">
                            <thead>
                                <tr class="bg-gray-50 border-b text-xs font-bold text-gray-500">
                                    <th class="py-2.5 px-3">التلميذ</th>
                                    <th class="py-2.5 px-3">القسم</th>
                                    <th class="py-2.5 px-3 text-center">إجراء الغياب</th>
                                </tr>
                            </thead>
                            <tbody>{attendance_rows}</tbody>
                        </table>
                    </div>
                </div>

                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-1 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2">تسجيل تلميذ بقائمة الأقسام</h3>
                    <form action="/teacher/add-student" method="POST" class="space-y-3">
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">اسم ولقب التلميذ</label>
                            <input type="text" name="student_fullname" placeholder="مثال: أمين بن علي" required class="w-full px-3 py-2 rounded-lg border text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">اختر القسم</label>
                            <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                                <option value="" disabled selected>-- اختر القسم --</option>
                                {section_options_html}
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-lg text-xs transition">إضافة تلميذ للقائمة</button>
                    </form>

                    <div class="mt-4 overflow-x-auto max-h-40 border-t pt-2">
                        <table class="w-full text-right">
                            <thead><tr class="text-[10px] text-gray-500 border-b"><th>التلميذ</th><th>القسم</th><th>حذف</th></tr></thead>
                            <tbody>{student_manage_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-md p-6">
                <h3 class="text-md font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <span class="w-2.5 h-2.5 bg-indigo-500 rounded-full"></span> دفتر النصوص الرقمي (تسجيل الدرس المنجز)
                </h3>
                <form action="/teacher/submit-lesson" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 mb-1">القسم</label>
                        <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                            <option value="" disabled selected>-- اختر القسم --</option>
                            {section_options_html}
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 mb-1">عنوان الدرس</label>
                        <input type="text" name="lesson_title" placeholder="العنوان..." required class="w-full px-3 py-2 rounded-lg border text-xs">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 mb-1">المحتوى الملخص</label>
                        <input type="text" name="content" placeholder="الملخص..." required class="w-full px-3 py-2 rounded-lg border text-xs">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-600 mb-1">التاريخ</label>
                        <div class="flex gap-2">
                            <input type="date" name="date" value="{today_date}" required class="w-full px-3 py-2 rounded-lg border text-xs">
                            <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-lg text-xs transition">حفظ</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/teacher/add-student', methods=['POST'])
def add_student():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    fullname = request.form.get('student_fullname')
    section_name = request.form.get('section_name')
    if fullname and section_name:
        db.session.add(Student(fullname=fullname, section_name=section_name, teacher_username=session.get('username')))
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/delete-student/<int:sid>')
def delete_student(sid):
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    student = Student.query.get(sid)
    if student and student.teacher_username == session.get('username'):
        db.session.delete(student)
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/mark-absence', methods=['POST'])
def mark_absence():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    student_name = request.form.get('student_name')
    section_name = request.form.get('section_name')
    date = request.form.get('date')
    
    if student_name and section_name and date:
        existing = Attendance.query.filter_by(student_name=student_name, date=date).first()
        if not existing:
            db.session.add(Attendance(student_name=student_name, section_name=section_name, teacher_name=session.get('fullname'), date=date, status='غائب'))
            db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/submit-lesson', methods=['POST'])
def submit_lesson():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    section_name = request.form.get('section_name')
    lesson_title = request.form.get('lesson_title')
    content = request.form.get('content')
    date = request.form.get('date')
    if section_name and lesson_title and content and date:
        db.session.add(LessonLog(teacher_name=session.get('fullname'), section_name=section_name, lesson_title=lesson_title, content=content, date=date))
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

# ==============================================================================
# لوحات تحكم الإدارة (مستشار التربية، الناظر، المدير)
# ==============================================================================

@app.route('/counselor/dashboard-view')
def counselor_dashboard_view():
    if session.get('role') != 'counselor':
        return redirect(url_for('home'))
    all_attendances = Attendance.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{a.student_name}</td><td class='py-3 px-4'>{a.section_name}</td><td class='py-3 px-4'>{a.teacher_name}</td><td class='py-3 px-4'>{a.date}</td><td class='py-3 px-4'><span class='bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold'>{a.status}</span></td></tr>" for a in all_attendances]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد غيابات مسجلة.</td></tr>"
    
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-amber-600">
                <div>
                    <h1 class="text-xl font-bold text-gray-800">مكتب الاستشارة التربوية - الحارس العام</h1>
                    <p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">ورقة الغيابات الرقمية اليومية</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-3 px-4">التلميذ</th><th class="py-3 px-4">القسم</th><th class="py-3 px-4">الأستاذ</th><th class="py-3 px-4">التاريخ</th><th class="py-3 px-4">الحالة</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body></html>
    """

@app.route('/deputy/dashboard-view')
def deputy_dashboard_view():
    if session.get('role') != 'inspector_deputy':
        return redirect(url_for('home'))
    logs = LessonLog.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{l.teacher_name}</td><td class='py-3 px-4'>{l.section_name}</td><td class='py-3 px-4 font-bold'>{l.lesson_title}</td><td class='py-3 px-4'>{l.content}</td><td class='py-3 px-4'>{l.date}</td></tr>" for l in logs]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد دروس مسجلة.</td></tr>"
    
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-indigo-600">
                <div>
                    <h1 class="text-xl font-bold text-gray-800">التنسيق البيداغوجي - السيد الناظر</h1>
                    <p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">متابعة دفاتر النصوص الرقمية</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-3 px-4">الأستاذ</th><th class="py-3 px-4">القسم</th><th class="py-3 px-4">الدرس</th><th class="py-3 px-4">المحتوى</th><th class="py-3 px-4">التاريخ</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body></html>
    """

@app.route('/director/dashboard-view')
def director_dashboard_view():
    if session.get('role') != 'director':
        return redirect(url_for('home'))
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-blue-800">
                <div>
                    <h1 class="text-xl font-bold text-gray-800">لوحة القيادة الشاملة - السيد المدير</h1>
                    <p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <p class="text-sm text-gray-700">مرحباً بك سيادة المدير. إشراف شامل ومتابعة لحظية لسيرورة الانضباط والغيابات ودفاتر النصوص.</p>
            </div>
        </div>
    </body></html>
    """

# ==============================================================================
# تشغيل السيرفر
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
