# ==============================================================================
# البداية: استيراد المكتبات وإعداد التطبيق وقاعدة البيانات الأساسية
# ==============================================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# إعداد قاعدة البيانات المحلية SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 1. جدول المستخدمين والأدوار
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)

# 2. جدول الغيابات اليومية
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='غائب')

# 3. جدول دفتر النصوص الرقمي
class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

# إنشاء الجداول بحماية تامة وإضافة حسابات افتراضية
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
# النهاية: إعداد القاعدة الأساسية وجداول النظام
# ==============================================================================


# ==============================================================================
# البداية: مسارات المصادقة والتسجيل والاستعادة والدخول العام
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
            <h1 class="text-2xl font-bold text-gray-800">منصة تسيير المؤسسة</h1>
            <p class="text-sm text-gray-500 mt-2">تسجيل الدخول إلى حسابك التربوي</p>
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

        <div class="flex justify-between items-center mt-5 text-sm">
            <a href="/register" class="text-blue-600 hover:underline font-bold">إنشاء حساب جديد</a>
            <a href="/forgot-password" class="text-gray-500 hover:underline">نسيت كلمة المرور؟</a>
        </div>

        <div class="mt-5 p-3 bg-slate-100 rounded-lg text-xs text-slate-600 text-center">
            <p class="font-bold mb-1 text-slate-700">حسابات التجربة (كلمة المرور: 123456):</p>
            <span>مدير: <b>director</b> | ناظر: <b>deputy</b> | مستشار: <b>counselor</b> | أستاذ: <b>teacher</b></span>
        </div>
    </div>
</body>
</html>
"""

REGISTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إنشاء حساب جديد - منصة تسيير المؤسسة</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-gray-800">إنشاء حساب جديد</h1>
            <p class="text-sm text-gray-500 mt-2">سجل عضويتك الجديدة في النظام</p>
        </div>

        <form action="/register-action" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الاسم واللقب</label>
                <input type="text" name="fullname" placeholder="مثال: محمد بن علي" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم (للدخول)</label>
                <input type="text" name="username" placeholder="مثال: m.benali" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" placeholder="******" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الصفة التربوية</label>
                <select name="role" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition bg-white">
                    <option value="" disabled selected>-- اختر صفتك --</option>
                    <option value="director">المدير</option>
                    <option value="inspector_deputy">الناظر</option>
                    <option value="counselor">مستشار التربية</option>
                    <option value="teacher">أستاذ</option>
                </select>
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-lg shadow-lg transition duration-300">
                تسجيل الحساب
            </button>
        </form>
        <div class="text-center mt-5">
            <a href="/" class="text-sm text-blue-600 hover:underline font-bold">العودة إلى تسجيل الدخول</a>
        </div>
    </div>
</body>
</html>
"""

FORGOT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>استعادة كلمة المرور</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-gray-800">استعادة كلمة المرور</h1>
            <p class="text-sm text-gray-500 mt-2">أدخل اسم المستخدم لتعيين كلمة مرور جديدة</p>
        </div>

        <form action="/forgot-action" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور الجديدة</label>
                <input type="password" name="new_password" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <button type="submit" class="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 rounded-lg shadow-lg transition duration-300">
                تحديث كلمة المرور
            </button>
        </form>
        <div class="text-center mt-5">
            <a href="/" class="text-sm text-blue-600 hover:underline font-bold">العودة إلى تسجيل الدخول</a>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register')
def register():
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/forgot-password')
def forgot_password():
    return render_template_string(FORGOT_TEMPLATE)

@app.route('/register-action', methods=['POST'])
def register_action():
    fullname = request.form.get('fullname')
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    role = request.form.get('role')
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        return render_template_string(REGISTER_TEMPLATE)
        
    new_user = User(username=username, password=password, role=role, fullname=fullname)
    db.session.add(new_user)
    db.session.commit()
    
    return render_template_string(LOGIN_TEMPLATE, message="تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.")

@app.route('/forgot-action', methods=['POST'])
def forgot_action():
    username = request.form.get('username', '').strip()
    new_password = request.form.get('new_password')
    
    user = User.query.filter_by(username=username).first()
    if user:
        user.password = new_password
        db.session.commit()
        return render_template_string(LOGIN_TEMPLATE, message="تم تحديث كلمة المرور بنجاح! سجل دخولك الآن.")
    else:
        return render_template_string(LOGIN_TEMPLATE, message="اسم المستخدم غير موجود في النظام.")

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
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ==============================================================================
# النهاية: مسارات المصادقة والتسجيل والاستعادة ودخول النظام
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الأستاذ (ورقة الغيابات الرقمية ودفتر النصوص)
# ==============================================================================

@app.route('/teacher/dashboard-view')
def teacher_dashboard_view():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    return """
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة تحكم الأستاذ - منصة تسيير المؤسسة</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Cairo', sans-serif; }</style>
    </head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-4xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-blue-600">
                <div>
                    <h1 class="text-2xl font-bold text-gray-800">البوابة البيداغوجية - الأستاذ</h1>
                    <p class="text-sm text-gray-500 mt-1">تسيير الحصص والغيابات ودفتر النصوص</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-red-100">تسجيل الخروج</a>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- نموذج الغيابات -->
                <div class="bg-white rounded-2xl shadow-md p-6">
                    <h2 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <span class="w-3 h-3 bg-emerald-500 rounded-full"></span> ورقة الغيابات الرقمية
                    </h2>
                    <form action="/teacher/submit-attendance" method="POST" class="space-y-4">
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">اسم التلميذ المعني بالغياب</label>
                            <input type="text" name="student_name" placeholder="مثال: محمد امين" required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">القسم / الفوج التربوي</label>
                            <input type="text" name="section_name" placeholder="مثال: 2 آداب وفلسفة 1" required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">تاريخ الحصة</label>
                            <input type="date" name="date" required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        </div>
                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-lg text-sm transition">
                            إرسال ورقة الغيابات للاستشارة
                        </button>
                    </form>
                </div>

                <!-- نموذج دفتر النصوص -->
                <div class="bg-white rounded-2xl shadow-md p-6">
                    <h2 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <span class="w-3 h-3 bg-indigo-500 rounded-full"></span> دفتر النصوص الرقمي
                    </h2>
                    <form action="/teacher/submit-lesson" method="POST" class="space-y-4">
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">القسم / الفوج التربوي</label>
                            <input type="text" name="section_name" placeholder="مثال: 2 آداب وفلسفة 1" required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">عنوان الدرس</label>
                            <input type="text" name="lesson_title" placeholder="مثال: الشعور بالأنا والغير" required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">محتوى الدرس الملخص</label>
                            <input type="text" name="content" placeholder="إطروحات الخصوم، التركيب..." required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">تاريخ إنجاز الدرس</label>
                            <input type="date" name="date" required class="w-full px-3 py-2 rounded-lg border text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none">
                        </div>
                        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-lg text-sm transition">
                            تسجيل في دفتر النصوص
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/teacher/submit-attendance', methods=['POST'])
def submit_attendance():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    student_name = request.form.get('student_name')
    section_name = request.form.get('section_name')
    date = request.form.get('date')
    
    if student_name and section_name and date:
        new_att = Attendance(
            student_name=student_name,
            section_name=section_name,
            teacher_name=session.get('fullname', 'أستاذ'),
            date=date,
            status='غائب'
        )
        db.session.add(new_att)
        db.session.commit()
    
    return """
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{font-family:'Cairo',sans-serif;}</style></head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
        <div class="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center border-t-8 border-emerald-600">
            <h1 class="text-2xl font-bold text-gray-800 mb-2">تم إرسال ورقة الغيابات بنجاح</h1>
            <p class="text-emerald-600 font-semibold mb-6">تم تحويل بيانات الغياب إلى مصلحة الاستشارة التربوية.</p>
            <a href="/teacher/dashboard-view" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800">العودة للوحة الأستاذ</a>
        </div>
    </body></html>
    """

@app.route('/teacher/submit-lesson', methods=['POST'])
def submit_lesson():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    section_name = request.form.get('section_name')
    lesson_title = request.form.get('lesson_title')
    content = request.form.get('content')
    date = request.form.get('date')
    
    if section_name and lesson_title and content and date:
        new_log = LessonLog(
            teacher_name=session.get('fullname', 'أستاذ'),
            section_name=section_name,
            lesson_title=lesson_title,
            content=content,
            date=date
        )
        db.session.add(new_log)
        db.session.commit()
    
    return """
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{font-family:'Cairo',sans-serif;}</style></head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
        <div class="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center border-t-8 border-indigo-600">
            <h1 class="text-2xl font-bold text-gray-800 mb-2">تم تسجيل الدرس بنجاح</h1>
            <p class="text-indigo-600 font-semibold mb-6">تم حفظ محتوى الدرس في دفتر النصوص الرقمي.</p>
            <a href="/teacher/dashboard-view" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800">العودة للوحة الأستاذ</a>
        </div>
    </body></html>
    """

# ==============================================================================
# النهاية: لوحة تحكم الأستاذ (ورقة الغيابات الرقمية ودفتر النصوص)
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الحارس العام (مستشار التربية) لمتابعة الغيابات
# ==============================================================================

@app.route('/counselor/dashboard-view')
def counselor_dashboard_view():
    if session.get('role') != 'counselor':
        return redirect(url_for('home'))
        
    all_attendances = Attendance.query.all()
    rows_html = ""
    if not all_attendances:
        rows_html = "<tr><td colspan='5' class='text-center py-6 text-gray-400'>لا توجد غيابات مسجلة حالياً.</td></tr>"
    else:
        for att in all_attendances:
            rows_html += f"""
            <tr class='border-b hover:bg-gray-50 transition'>
                <td class='py-3 px-4 text-sm font-semibold text-gray-800'>{att.student_name}</td>
                <td class='py-3 px-4 text-sm text-gray-600'>{att.section_name}</td>
                <td class='py-3 px-4 text-sm text-gray-600'>{att.teacher_name}</td>
                <td class='py-3 px-4 text-sm text-gray-600'>{att.date}</td>
                <td class='py-3 px-4 text-sm'>
                    <span class='bg-red-100 text-red-700 px-2.5 py-1 rounded-full text-xs font-bold'>{att.status}</span>
                </td>
            </tr>
            """

    return f"""
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مكتب التوجيه والمتابعة - الحارس العام</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Cairo', sans-serif; }}</style>
    </head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-amber-600">
                <div>
                    <h1 class="text-2xl font-bold text-gray-800">مكتب التوجيه والمتابعة - الاستشارة التربوية</h1>
                    <p class="text-sm text-gray-500 mt-1">تسيير الانضباط والغيابات اليومية الواردة من الأقسام</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-red-100">تسجيل الخروج</a>
            </div>

            <div class="bg-white rounded-2xl shadow-md p-6 overflow-hidden">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-gray-800 flex items-center gap-2">
                        <span class="w-3 h-3 bg-amber-500 rounded-full"></span> ورقة الغيابات الرقمية الواردة من الأساتذة
                    </h2>
                    <span class="text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-lg font-semibold">محدث آنياً</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-right border-collapse">
                        <thead>
                            <tr class="bg-gray-50 border-b text-xs font-bold text-gray-500 uppercase">
                                <th class="py-3 px-4">التلميذ المعني</th>
                                <th class="py-3 px-4">القسم</th>
                                <th class="py-3 px-4">الأستاذ المرسل</th>
                                <th class="py-3 px-4">التاريخ</th>
                                <th class="py-3 px-4">الحالة</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ==============================================================================
# النهاية: لوحة تحكم الحارس العام (مستشار التربية) لمتابعة الغيابات
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الناظر (متابعة دفاتر النصوص والمناهج)
# ==============================================================================

@app.route('/deputy/dashboard-view')
def deputy_dashboard_view():
    if session.get('role') != 'inspector_deputy':
        return redirect(url_for('home'))
        
    all_logs = LessonLog.query.all()
    rows_html = ""
    if not all_logs:
        rows_html = "<tr><td colspan='5' class='text-center py-6 text-gray-400'>لا توجد دروس مسجلة في دفاتر النصوص حالياً.</td></tr>"
    else:
        for log in all_logs:
            rows_html += f"""
            <tr class='border-b hover:bg-gray-50 transition'>
                <td class='py-3 px-4 text-sm font-semibold text-gray-800'>{log.teacher_name}</td>
                <td class='py-3 px-4 text-sm text-gray-600'>{log.section_name}</td>
                <td class='py-3 px-4 text-sm text-gray-800 font-bold'>{log.lesson_title}</td>
                <td class='py-3 px-4 text-sm text-gray-600'>{log.content}</td>
                <td class='py-3 px-4 text-sm text-gray-500'>{log.date}</td>
            </tr>
            """

    return f"""
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>التنسيق البيداغوجي - الناظر</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Cairo', sans-serif; }}</style>
    </head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-indigo-600">
                <div>
                    <h1 class="text-2xl font-bold text-gray-800">التنسيق البيداغوجي - السيد الناظر</h1>
                    <p class="text-sm text-gray-500 mt-1">متابعة إنجاز المناهج ودفاتر النصوص الرقمية للأساتذة</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-red-100">تسجيل الخروج</a>
            </div>

            <div class="bg-white rounded-2xl shadow-md p-6 overflow-hidden">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-gray-800 flex items-center gap-2">
                        <span class="w-3 h-3 bg-indigo-500 rounded-full"></span> متابعة دفاتر النصوص الرقمية للأساتذة
                    </h2>
                    <span class="text-xs bg-gray-100 text-gray-600 px-3 py-1 rounded-lg font-semibold">محدث آنياً</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-right border-collapse">
                        <thead>
                            <tr class="bg-gray-50 border-b text-xs font-bold text-gray-500 uppercase">
                                <th class="py-3 px-4">الأستاذ</th>
                                <th class="py-3 px-4">القسم</th>
                                <th class="py-3 px-4">عنوان الدرس</th>
                                <th class="py-3 px-4">الملخص والمحتوى</th>
                                <th class="py-3 px-4">التاريخ</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ==============================================================================
# النهاية: لوحة تحكم الناظر (متابعة دفاتر النصوص والمناهج)
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم المدير (الإشراف الشامل والمؤشرات)
# ==============================================================================

@app.route('/director/dashboard-view')
def director_dashboard_view():
    if session.get('role') != 'director':
        return redirect(url_for('home'))
        
    total_att = Attendance.query.count()
    total_logs = LessonLog.query.count()
    total_users = User.query.count()

    return f"""
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>لوحة القيادة الشاملة - السيد المدير</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Cairo', sans-serif; }}</style>
    </head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-blue-800">
                <div>
                    <h1 class="text-2xl font-bold text-gray-800">لوحة القيادة الشاملة - السيد المدير</h1>
                    <p class="text-sm text-gray-500 mt-1">إشراف شامل، مؤشرات الغياب، متابعة التقارير والقرارات الإدارية</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-red-100">تسجيل الخروج</a>
            </div>

            <!-- بطاقات الإحصائيات المؤشرة -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-white rounded-2xl shadow-md p-6 border-t-4 border-emerald-500">
                    <h3 class="text-sm font-bold text-gray-500 mb-1">إجمالي الغيابات المسجلة</h3>
                    <p class="text-3xl font-extrabold text-gray-800">{total_att}</p>
                </div>
                <div class="bg-white rounded-2xl shadow-md p-6 border-t-4 border-indigo-500">
                    <h3 class="text-sm font-bold text-gray-500 mb-1">الدروس المسجلة في دفاتر النصوص</h3>
                    <p class="text-3xl font-extrabold text-gray-800">{total_logs}</p>
                </div>
                <div class="bg-white rounded-2xl shadow-md p-6 border-t-4 border-blue-500">
                    <h3 class="text-sm font-bold text-gray-500 mb-1">عدد المستخدمين في المنصة</h3>
                    <p class="text-3xl font-extrabold text-gray-800">{total_users}</p>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-lg font-bold text-gray-800 mb-3">تقارير اتخاذ القرار الإداري</h2>
                <p class="text-sm text-gray-600 mb-4">تستطيع من خلال هذه اللوحة مراقبة سيرورة العمل البيداغوجي والانضباط العام للمؤسسة لحظة بلحظة بناءً على المعطيات المرفوعة من الأساتذة ومصالح الاستشارة والناظر.</p>
                <div class="p-4 bg-blue-50 rounded-xl text-blue-800 text-sm font-semibold">
                    النظام يعمل بانتظام وقاعدة البيانات الدائمة تسجل كافة التحديثات والتقارير بدقة عالية.
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ==============================================================================
# النهاية: لوحة تحكم المدير (الإشراف الشامل والمؤشرات)
# ==============================================================================


# ==============================================================================
# البداية: تشغيل السيرفر
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# ==============================================================================
# النهاية: تشغيل السيرفر
# ==============================================================================
