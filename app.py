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

# 2. جدول التلاميذ المسجلين يدوياً للأقسام المسندة
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
# البداية: مسارات المصادقة والتسجيل والاستعادة ودخول النظام
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

        <div class="flex justify-between items-center mt-5 text-sm">
            <a href="/register" class="text-blue-600 hover:underline font-bold">إنشاء حساب جديد</a>
            <a href="/forgot-password" class="text-gray-500 hover:underline">نسيت كلمة المرور؟</a>
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
    <title>إنشاء حساب جديد</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-gray-800">إنشاء حساب جديد</h1>
        </div>
        <form action="/register-action" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الاسم واللقب</label>
                <input type="text" name="fullname" placeholder="مثال: محمد بن علي" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" placeholder="مثال: m.benali" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الصفة التربوية</label>
                <select name="role" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white">
                    <option value="" disabled selected>-- اختر صفتك --</option>
                    <option value="director">المدير</option>
                    <option value="inspector_deputy">الناظر</option>
                    <option value="counselor">مستشار التربية</option>
                    <option value="teacher">أستاذ</option>
                </select>
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-lg shadow-lg">تسجيل الحساب</button>
        </form>
        <div class="text-center mt-5"><a href="/" class="text-sm text-blue-600 hover:underline font-bold">العودة لتسجيل الدخول</a></div>
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
        <div class="text-center mb-6"><h1 class="text-2xl font-bold text-gray-800">استعادة كلمة المرور</h1></div>
        <form action="/forgot-action" method="POST" class="space-y-4">
            <div><label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label><input type="text" name="username" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300"></div>
            <div><label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور الجديدة</label><input type="password" name="new_password" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300"></div>
            <button type="submit" class="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 rounded-lg shadow-lg">تحديث كلمة المرور</button>
        </form>
        <div class="text-center mt-5"><a href="/" class="text-sm text-blue-600 hover:underline font-bold">العودة لتسجيل الدخول</a></div>
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
    
    if User.query.filter_by(username=username).first():
        return render_template_string(REGISTER_TEMPLATE)
        
    db.session.add(User(username=username, password=password, role=role, fullname=fullname))
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
        return render_template_string(LOGIN_TEMPLATE, message="تم تحديث كلمة المرور بنجاح!")
    return render_template_string(LOGIN_TEMPLATE, message="اسم المستخدم غير موجود.")

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
# النهاية: مسارات المصادقة والتسجيل والاستعادة ودخول النظام
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الأستاذ (مع الترويسة الرسمية وقائمة الأقسام الشاملة وإدارة التلاميذ)
# ==============================================================================

@app.route('/teacher/dashboard-view')
def teacher_dashboard_view():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    teacher_uname = session.get('username')
    students = Student.query.filter_by(teacher_username=teacher_uname).all()
    
    students_options = ""
    for s in students:
        students_options += f"<option value='{s.fullname}'>({s.section_name}) - {s.fullname}</option>"

    student_rows = ""
    for s in students:
        student_rows += f"""
        <tr class="border-b">
            <td class="py-2 px-3 text-sm text-gray-800">{s.fullname}</td>
            <td class="py-2 px-3 text-sm text-gray-600">{s.section_name}</td>
            <td class="py-2 px-3 text-sm">
                <a href="/teacher/delete-student/{s.id}" class="text-red-600 hover:underline text-xs">حذف</a>
            </td>
        </tr>
        """
    if not student_rows:
        student_rows = "<tr><td colspan='3' class='text-center py-3 text-gray-400 text-xs'>لم تقم بإضافة تلاميذ بعد.</td></tr>"

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
        <div class="max-w-5xl mx-auto space-y-6">
            
            <!-- الترويسة الرسمية في الوسط -->
            <div class="bg-white rounded-2xl shadow-md p-6 text-center border-b-4 border-blue-800 space-y-1">
                <p class="text-xs font-bold text-gray-600">الجمهورية الجزائرية الديمقراطية الشعبية</p>
                <p class="text-xs font-semibold text-gray-600">وزارة التربية الوطنية</p>
                <p class="text-xs font-semibold text-gray-600">مديرية التربية لولاية وهران</p>
                <div class="my-2"></div>
                <h2 class="text-lg font-extrabold text-blue-900">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</h2>
                <div class="pt-2 flex justify-between items-center border-t mt-4 text-sm">
                    <span class="font-bold text-gray-700">الأستاذ: {session.get('fullname')}</span>
                    <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-red-100">تسجيل الخروج</a>
                </div>
            </div>

            <!-- شبكة الإدارة والبيداغوجيا -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                <!-- 1. إضافة التلاميذ يدوياً للأقسام المسندة -->
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-1 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2">تسجيل تلميذ بأقسامك</h3>
                    <form action="/teacher/add-student" method="POST" class="space-y-3">
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">اسم ولقب التلميذ</label>
                            <input type="text" name="student_fullname" placeholder="مثال: أمين بن علي" required class="w-full px-3 py-2 rounded-lg border text-xs focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">اختر القسم المسند</label>
                            <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                                <option value="" disabled selected>-- اختر القسم --</option>
                                <optgroup label="السنة الأولى ثانوي (جذوع مشتركة)">
                                    <option value="1 ج م ع ت 1">1 ج م ع ت 1</option>
                                    <option value="1 ج م ع ت 2">1 ج م ع ت 2</option>
                                    <option value="1 ج م ع ت 3">1 ج م ع ت 3</option>
                                    <option value="1 ج م ع ت 4">1 ج م ع ت 4</option>
                                    <option value="1 ج م ع ت 5">1 ج م ع ت 5</option>
                                    <option value="1 ج م ع ت 6">1 ج م ع ت 6</option>
                                    <option value="1 ج م ع ت 7">1 ج م ع ت 7</option>
                                    <option value="1 ج م أدب 1">1 ج م أدب 1</option>
                                    <option value="1 ج م أدب 2">1 ج م أدب 2</option>
                                    <option value="1 ج م أدب 3">1 ج م أدب 3</option>
                                    <option value="1 ج م أدب 4">1 ج م أدب 4</option>
                                    <option value="1 ج م أدب 5">1 ج م أدب 5</option>
                                </optgroup>
                                <optgroup label="السنة الثانية ثانوي">
                                    <option value="2 آداب وفلسفة">2 آداب وفلسفة</option>
                                    <option value="2 لغات أجنبية">2 لغات أجنبية</option>
                                    <option value="2 علوم تجريبية">2 علوم تجريبية</option>
                                    <option value="2 رياضيات">2 رياضيات</option>
                                    <option value="2 تقني رياضي">2 تقني رياضي</option>
                                    <option value="2 تسيير واقتصاد">2 تسيير واقتصاد</option>
                                </optgroup>
                                <optgroup label="السنة الثالثة ثانوي (الأقسام النهائية)">
                                    <option value="3 آداب وفلسفة">3 آداب وفلسفة</option>
                                    <option value="3 لغات أجنبية">3 لغات أجنبية</option>
                                    <option value="3 علوم تجريبية">3 علوم تجريبية</option>
                                    <option value="3 رياضيات">3 رياضيات</option>
                                    <option value="3 تقني رياضي (هم)">3 تقني رياضي (هم)</option>
                                    <option value="3 تقني رياضي (هك)">3 تقني رياضي (هك)</option>
                                    <option value="3 تقني رياضي (همك)">3 تقني رياضي (همك)</option>
                                    <option value="3 تقني رياضي (هط)">3 تقني رياضي (هط)</option>
                                    <option value="3 تسيير واقتصاد">3 تسيير واقتصاد</option>
                                </optgroup>
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-lg text-xs transition">إضافة التلميذ للقائمة</button>
                    </form>

                    <div class="mt-4 overflow-x-auto max-h-48">
                        <table class="w-full text-right">
                            <thead><tr class="text-[10px] text-gray-500 border-b"><th>التلميذ</th><th>القسم</th><th>حذف</th></tr></thead>
                            <tbody>{student_rows}</tbody>
                        </table>
                    </div>
                </div>

                <!-- 2. ورقة الغيابات الرقمية -->
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-1 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2 flex items-center gap-2">
                        <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span> ورقة الغيابات الرقمية
                    </h3>
                    <form action="/teacher/submit-attendance" method="POST" class="space-y-3">
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">اختر التلميذ الغائب</label>
                            <select name="student_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                                <option value="" disabled selected>-- قائمة تلاميذك --</option>
                                {students_options}
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">تاريخ الحصة</label>
                            <input type="date" name="date" required class="w-full px-3 py-2 rounded-lg border text-xs">
                        </div>
                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-lg text-xs transition">إرسال ورقة الغيابات للاستشارة</button>
                    </form>
                </div>

                <!-- 3. دفتر النصوص الرقمي -->
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-1 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2 flex items-center gap-2">
                        <span class="w-2.5 h-2.5 bg-indigo-500 rounded-full"></span> دفتر النصوص الرقمي
                    </h3>
                    <form action="/teacher/submit-lesson" method="POST" class="space-y-3">
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">القسم المعني</label>
                            <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                                <option value="" disabled selected>-- اختر القسم --</option>
                                <option value="1 ج م ع ت">1 ج م ع ت</option>
                                <option value="1 ج م أدب">1 ج م أدب</option>
                                <option value="2 آداب وفلسفة">2 آداب وفلسفة</option>
                                <option value="2 علوم تجريبية">2 علوم تجريبية</option>
                                <option value="3 آداب وفلسفة">3 آداب وفلسفة</option>
                                <option value="3 علوم تجريبية">3 علوم تجريبية</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">عنوان الدرس</label>
                            <input type="text" name="lesson_title" placeholder="عنوان الدرس..." required class="w-full px-3 py-2 rounded-lg border text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">محتوى الدرس</label>
                            <input type="text" name="content" placeholder="الملخص..." required class="w-full px-3 py-2 rounded-lg border text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-600 mb-1">التاريخ</label>
                            <input type="date" name="date" required class="w-full px-3 py-2 rounded-lg border text-xs">
                        </div>
                        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 rounded-lg text-xs transition">تسجيل الدرس</button>
                    </form>
                </div>

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

@app.route('/teacher/submit-attendance', methods=['POST'])
def submit_attendance():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    student_name = request.form.get('student_name')
    date = request.form.get('date')
    
    # استخراج اسم القسم تلقائياً من التلاميذ المسجلين
    st = Student.query.filter_by(fullname=student_name, teacher_username=session.get('username')).first()
    section_name = st.section_name if st else 'قسم عام'
    
    if student_name and date:
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
# النهاية: لوحة تحكم الأستاذ
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الحارس العام (مستشار التربية)
# ==============================================================================

@app.route('/counselor/dashboard-view')
def counselor_dashboard_view():
    if session.get('role') != 'counselor':
        return redirect(url_for('home'))
    all_attendances = Attendance.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{a.student_name}</td><td class='py-3 px-4'>{a.section_name}</td><td class='py-3 px-4'>{a.teacher_name}</td><td class='py-3 px-4'>{a.date}</td><td class='py-3 px-4'><span class='bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold'>{a.status}</span></td></tr>" for a in all_attendances]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد غيابات.</td></tr>"
    
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-amber-600">
                <div><h1 class="text-xl font-bold text-gray-800">مكتب الاستشارة التربوية - الحارس العام</h1></div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">ورقة الغيابات الرقمية الواردة</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-3 px-4">التلميذ</th><th class="py-3 px-4">القسم</th><th class="py-3 px-4">الأستاذ</th><th class="py-3 px-4">التاريخ</th><th class="py-3 px-4">الحالة</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body></html>
    """

# ==============================================================================
# النهاية: لوحة تحكم الحارس العام
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الناظر
# ==============================================================================

@app.route('/deputy/dashboard-view')
def deputy_dashboard_view():
    if session.get('role') != 'inspector_deputy':
        return redirect(url_for('home'))
    logs = LessonLog.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{l.teacher_name}</td><td class='py-3 px-4'>{l.section_name}</td><td class='py-3 px-4 font-bold'>{l.lesson_title}</td><td class='py-3 px-4'>{l.content}</td><td class='py-3 px-4'>{l.date}</td></tr>" for l in logs]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد دروس.</td></tr>"
    
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-indigo-600">
                <div><h1 class="text-xl font-bold text-gray-800">التنسيق البيداغوجي - السيد الناظر</h1></div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">دفاتر النصوص الرقمية</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs font-bold text-gray-500"><th class="py-3 px-4">الأستاذ</th><th class="py-3 px-4">القسم</th><th class="py-3 px-4">الدرس</th><th class="py-3 px-4">المحتوى</th><th class="py-3 px-4">التاريخ</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body></html>
    """

# ==============================================================================
# النهاية: لوحة تحكم الناظر
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم المدير
# ==============================================================================

@app.route('/director/dashboard-view')
def director_dashboard_view():
    if session.get('role') != 'director':
        return redirect(url_for('home'))
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-blue-800">
                <div><h1 class="text-xl font-bold text-gray-800">لوحة القيادة الشاملة - السيد المدير</h1></div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <p class="text-sm text-gray-700">مرحباً بك سيادة المدير. إشراف شامل على المؤسسة ومتابعة سيرورة الانضباط والدروس.</p>
            </div>
        </div>
    </body></html>
    """

# ==============================================================================
# النهاية: لوحة تحكم المدير
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
