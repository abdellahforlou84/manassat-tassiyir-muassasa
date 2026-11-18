# ==============================================================================
# البداية: استيراد المكتبات وإعداد التطبيق وقاعدة البيانات الأساسية
# ==============================================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

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

# 2. جدول الحجم الساعي الفعلي للأستاذ (يحدده المدير/الناظر مرة واحدة)
class TeacherWorkload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(80), unique=True, nullable=False)
    teacher_fullname = db.Column(db.String(120), nullable=False)
    expected_hours = db.Column(db.Float, nullable=False) # ساعات العمل المفترضة أسبوعياً

# 3. جدول التلاميذ المسجلين للأقسام المسندة
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    teacher_username = db.Column(db.String(80), nullable=False)

# 4. جدول الغيابات اليومية للتلاميذ
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='غائب')

# 5. جدول تأكيد حضور الأستاذ اليومي بالساعة
class TeacherPresence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    teacher_username = db.Column(db.String(80), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    hour_slot = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), default='في انتظار مصادقة الحارس العام')

# 6. جدول دفتر النصوص الرقمي
class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

# إنشاء الجداول بحماية تامة
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
            
        # إسناد حجم ساعي افتراضي للأستاذ التجريبي
        if not TeacherWorkload.query.filter_by(teacher_username='teacher').first():
            db.session.add(TeacherWorkload(teacher_username='teacher', teacher_fullname='الأستاذ الفاضل', expected_hours=18.0))
            db.session.commit()
    except Exception as e:
        print(f"Database error: {e}")

# ==============================================================================
# النهاية: إعداد القاعدة الأساسية وجداول النظام
# ==============================================================================


# ==============================================================================
# البداية: مسارات المصادقة والتسجيل
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
                <input type="text" name="username" placeholder="مثال: teacher أو director" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" placeholder="123456" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الصفة التربوية (الدور)</label>
                <select name="role" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white">
                    <option value="" disabled selected>-- اختر صفتك في المؤسسة --</option>
                    <option value="director">المدير</option>
                    <option value="inspector_deputy">الناظر</option>
                    <option value="counselor">مستشار التربية</option>
                    <option value="teacher">أستاذ</option>
                </select>
            </div>
            <button type="submit" class="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-3 rounded-lg shadow-lg">دخول إلى لوحة التحكم</button>
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
        <div class="text-center mb-6"><h1 class="text-2xl font-bold text-gray-800">إنشاء حساب جديد</h1></div>
        <form action="/register-action" method="POST" class="space-y-4">
            <div><label class="block text-sm font-semibold text-gray-700 mb-1">الاسم واللقب</label><input type="text" name="fullname" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300"></div>
            <div><label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label><input type="text" name="username" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300"></div>
            <div><label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label><input type="password" name="password" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300"></div>
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
    
    # إذا كان المستخدم أستاذ، ننشئ له سجلاً افتراضياً للحجم الساعي
    if role == 'teacher':
        if not TeacherWorkload.query.filter_by(teacher_username=username).first():
            db.session.add(TeacherWorkload(teacher_username=username, teacher_fullname=fullname, expected_hours=18.0))
            db.session.commit()
            
    return render_template_string(LOGIN_TEMPLATE, message="تم إنشاء الحساب بنجاح!")

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
# النهاية: مسارات المصادقة والتسجيل
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الأستاذ (مع عرض ساعاته المفترضة والفعليا والغياب)
# ==============================================================================

@app.route('/teacher/dashboard-view')
def teacher_dashboard_view():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    teacher_uname = session.get('username')
    teacher_fullname = session.get('fullname')
    students = Student.query.filter_by(teacher_username=teacher_uname).all()
    today_date = datetime.now().strftime('%Y-%m-%d')

    # حساب ساعات العمل المفترضة والفعلية والغياب للأستاذ
    workload = TeacherWorkload.query.filter_by(teacher_username=teacher_uname).first()
    expected_hrs = workload.expected_hours if workload else 18.0
    
    # عدد ساعات الحضور المصادق عليها رسمياً من الحارس العام
    approved_presence_count = TeacherPresence.query.filter_by(teacher_username=teacher_uname, status='مصادق عليه (حضور مسجل بالساعة)').count()
    actual_hrs = float(approved_presence_count) * 1.0 # افترضنا كل حصة معتمدة تساوي ساعة
    absent_hrs = max(0.0, expected_hrs - actual_hrs)

    attendance_rows = "".join([f"""
    <tr class="border-b hover:bg-gray-50">
        <td class="py-2 px-3 text-sm font-semibold text-gray-800">{s.fullname}</td>
        <td class="py-2 px-3 text-sm text-gray-600">{s.section_name}</td>
        <td class="py-2 px-3 text-center">
            <form action="/teacher/mark-absence" method="POST" class="inline">
                <input type="hidden" name="student_name" value="{s.fullname}">
                <input type="hidden" name="section_name" value="{s.section_name}">
                <input type="hidden" name="date" value="{today_date}">
                <button type="submit" class="bg-red-50 text-red-600 border border-red-200 hover:bg-red-600 hover:text-white px-3 py-1 rounded text-xs font-bold transition">تسجيل غياب</button>
            </form>
        </td>
    </tr>
    """ for s in students]) or "<tr><td colspan='3' class='text-center py-4 text-gray-400 text-xs'>لا توجد تلاميذ مسجلين.</td></tr>"

    student_manage_rows = "".join([f"""
    <tr class="border-b"><td class="py-2 px-2 text-xs">{s.fullname}</td><td class="py-2 px-2 text-xs">{s.section_name}</td><td class="py-2 px-2 text-xs text-center"><a href="/teacher/delete-student/{s.id}" class="text-red-600 hover:underline font-bold">حذف</a></td></tr>
    """ for s in students]) or "<tr><td colspan='3' class='text-center py-2 text-gray-400 text-xs'>لا توجد بيانات.</td></tr>"

    my_presence = TeacherPresence.query.filter_by(teacher_username=teacher_uname, date=today_date).all()
    presence_rows = "".join([f"""
    <tr class="border-b"><td class="py-2 px-3 text-xs">{p.section_name}</td><td class="py-2 px-3 text-xs">{p.hour_slot}</td><td class="py-2 px-3 text-xs"><span class="{'bg-amber-100 text-amber-700' if 'انتظار' in p.status else 'bg-emerald-100 text-emerald-700'} px-2 py-0.5 rounded font-bold">{p.status}</span></td></tr>
    """ for p in my_presence]) or "<tr><td colspan='3' class='text-center py-3 text-gray-400 text-xs'>لم تسجل حضوراً اليوم بعد.</td></tr>"

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
            
            <!-- الترويسة الرسمية -->
            <div class="bg-white rounded-2xl shadow-md p-6 text-center border-b-4 border-blue-800 space-y-1">
                <p class="text-xs font-bold text-gray-600">الجمهورية الجزائرية الديمقراطية الشعبية</p>
                <p class="text-xs font-semibold text-gray-600">وزارة التربية الوطنية | مديرية التربية لولاية وهران</p>
                <h2 class="text-lg font-extrabold text-blue-900 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</h2>
                <div class="pt-2 flex justify-between items-center border-t mt-4 text-sm">
                    <span class="font-bold text-gray-700">الأستاذ: {teacher_fullname}</span>
                    <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-semibold">تسجيل الخروج</a>
                </div>
            </div>

            <!-- بطاقات مؤشرات الحجم الساعي والغياب للأستاذ -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-white rounded-xl shadow p-4 border-r-4 border-blue-600">
                    <p class="text-xs text-gray-500 font-bold">ساعات العمل المفترضة (الأسبوعية)</p>
                    <p class="text-2xl font-extrabold text-blue-900 mt-1">{expected_hrs} س</p>
                </div>
                <div class="bg-white rounded-xl shadow p-4 border-r-4 border-emerald-600">
                    <p class="text-xs text-gray-500 font-bold">ساعات العمل الفعلية (المصادق عليها)</p>
                    <p class="text-2xl font-extrabold text-emerald-700 mt-1">{actual_hrs} س</p>
                </div>
                <div class="bg-white rounded-xl shadow p-4 border-r-4 border-red-600">
                    <p class="text-xs text-gray-500 font-bold">ساعات الغياب المقدرة</p>
                    <p class="text-2xl font-extrabold text-red-700 mt-1">{absent_hrs} س</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- 1. غيابات التلاميذ وتأكيد الحضور -->
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-2 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2 flex items-center gap-2">
                        <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span> تسجيل غيابات التلاميذ اليومية
                    </h3>
                    <div class="overflow-x-auto max-h-64">
                        <table class="w-full text-right">
                            <thead><tr class="bg-gray-50 border-b text-xs text-gray-500"><th class="py-2 px-3">التلميذ</th><th class="py-2 px-3">القسم</th><th class="py-2 px-3 text-center">إجراء</th></tr></thead>
                            <tbody>{attendance_rows}</tbody>
                        </table>
                    </div>

                    <div class="border-t pt-4 space-y-3">
                        <h3 class="text-md font-bold text-gray-800">تأكيد حضور الأستاذ اليومي (بالساعة)</h3>
                        <form action="/teacher/confirm-presence" method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <input type="text" name="section_name" placeholder="القسم (مثال: 3 آداب)" required class="px-3 py-2 rounded-lg border text-xs">
                            <select name="hour_slot" required class="px-3 py-2 rounded-lg border text-xs bg-white">
                                <option value="" disabled selected>-- اختر الحصة --</option>
                                <option value="الساعة الأولى (08:00 - 09:00)">الساعة الأولى (08:00 - 09:00)</option>
                                <option value="الساعة الثانية (09:00 - 10:00)">الساعة الثانية (09:00 - 10:00)</option>
                                <option value="الساعة الثالثة (10:15 - 11:15)">الساعة الثالثة (10:15 - 11:15)</option>
                                <option value="الساعة الرابعة (11:15 - 12:15)">الساعة الرابعة (11:15 - 12:15)</option>
                            </select>
                            <button type="submit" class="bg-blue-700 hover:bg-blue-800 text-white font-bold py-2 rounded-lg text-xs">إثبات الحضور للحارس العام</button>
                        </form>
                        <div class="overflow-x-auto max-h-32 pt-2">
                            <table class="w-full text-right">
                                <thead><tr class="text-[10px] text-gray-500 border-b"><th>القسم</th><th>الحصة</th><th>الحالة</th></tr></thead>
                                <tbody>{presence_rows}</tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- 2. إضافة التلاميذ يدوياً -->
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-1 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2">تسجيل تلميذ بالقسم</h3>
                    <form action="/teacher/add-student" method="POST" class="space-y-3">
                        <input type="text" name="student_fullname" placeholder="اسم ولقب التلميذ" required class="w-full px-3 py-2 rounded-lg border text-xs">
                        <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                            <option value="" disabled selected>-- اختر القسم --</option>
                            <option value="1 ج م ع ت 1">1 ج م ع ت 1</option>
                            <option value="2 آداب وفلسفة 1">2 آداب وفلسفة 1</option>
                            <option value="3 آداب وفلسفة">3 آداب وفلسفة</option>
                            <option value="3 علوم تجريبية">3 علوم تجريبية</option>
                        </select>
                        <button type="submit" class="w-full bg-slate-800 text-white font-bold py-2 rounded-lg text-xs">إضافة تلميذ</button>
                    </form>
                    <div class="overflow-x-auto max-h-40 border-t pt-2">
                        <table class="w-full text-right">
                            <thead><tr class="text-[10px] text-gray-500 border-b"><th>التلميذ</th><th>القسم</th><th>حذف</th></tr></thead>
                            <tbody>{student_manage_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- 3. دفتر النصوص الرقمي -->
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h3 class="text-md font-bold text-gray-800 mb-3">دفتر النصوص الرقمي</h3>
                <form action="/teacher/submit-lesson" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <input type="text" name="section_name" placeholder="القسم" required class="px-3 py-2 rounded-lg border text-xs">
                    <input type="text" name="lesson_title" placeholder="عنوان الدرس" required class="px-3 py-2 rounded-lg border text-xs">
                    <input type="text" name="content" placeholder="الملخص" required class="px-3 py-2 rounded-lg border text-xs">
                    <div class="flex gap-2">
                        <input type="date" name="date" value="{today_date}" required class="px-3 py-2 rounded-lg border text-xs">
                        <button type="submit" class="bg-indigo-600 text-white font-bold px-4 py-2 rounded-lg text-xs">حفظ</button>
                    </div>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/teacher/add-student', methods=['POST'])
def add_student():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    if request.form.get('student_fullname') and request.form.get('section_name'):
        db.session.add(Student(fullname=request.form.get('student_fullname'), section_name=request.form.get('section_name'), teacher_username=session.get('username')))
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/delete-student/<int:sid>')
def delete_student(sid):
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    student = Student.query.get(sid)
    if student and student.teacher_username == session.get('username'):
        db.session.delete(student); db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/mark-absence', methods=['POST'])
def mark_absence():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    if request.form.get('student_name') and request.form.get('date'):
        if not Attendance.query.filter_by(student_name=request.form.get('student_name'), date=request.form.get('date')).first():
            db.session.add(Attendance(student_name=request.form.get('student_name'), section_name=request.form.get('section_name'), teacher_name=session.get('fullname'), date=request.form.get('date'), status='غائب'))
            db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/confirm-presence', methods=['POST'])
def confirm_presence():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    if request.form.get('section_name') and request.form.get('hour_slot'):
        db.session.add(TeacherPresence(teacher_name=session.get('fullname'), teacher_username=session.get('username'), section_name=request.form.get('section_name'), hour_slot=request.form.get('hour_slot'), date=datetime.now().strftime('%Y-%m-%d'), status='في انتظار مصادقة الحارس العام'))
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/submit-lesson', methods=['POST'])
def submit_lesson():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    if request.form.get('section_name') and request.form.get('lesson_title'):
        db.session.add(LessonLog(teacher_name=session.get('fullname'), section_name=request.form.get('section_name'), lesson_title=request.form.get('lesson_title'), content=request.form.get('content'), date=request.form.get('date')))
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
    if session.get('role') != 'counselor': return redirect(url_for('home'))
    all_attendances = Attendance.query.all()
    att_rows = "".join([f"<tr class='border-b'><td class='py-2.5 px-3'>{a.student_name}</td><td class='py-2.5 px-3'>{a.section_name}</td><td class='py-2.5 px-3'>{a.teacher_name}</td><td class='py-2.5 px-3'>{a.date}</td><td class='py-2.5 px-3'><span class='bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold'>{a.status}</span></td></tr>" for a in all_attendances]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد غيابات.</td></tr>"
    
    presences = TeacherPresence.query.all()
    pres_rows = "".join([f"""
    <tr class="border-b">
        <td class="py-2 px-3 text-xs font-semibold">{p.teacher_name}</td>
        <td class="py-2 px-3 text-xs">{p.section_name}</td>
        <td class="py-2 px-3 text-xs">{p.hour_slot}</td>
        <td class="py-2 px-3 text-xs">{p.date}</td>
        <td class="py-2 px-3 text-center">{'<a href="/counselor/approve-presence/' + str(p.id) + '" class="bg-emerald-600 text-white px-3 py-1 rounded text-xs font-bold">مصادقة</a>' if 'انتظار' in p.status else '<span class="text-emerald-700 font-bold text-xs">معتمد</span>'}</td>
    </tr>
    """ for p in presences]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400 text-xs'>لا توجد طلبات.</td></tr>"

    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-amber-600">
                <div><h1 class="text-xl font-bold text-gray-800">مكتب الاستشارة التربوية - الحارس العام</h1></div>
                <a href="/logout" class="bg-red-50 text-red-600 border px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6 space-y-4">
                <h2 class="text-md font-bold text-gray-800 border-b pb-2">مصادقة حضور الأساتذة اليومي بالساعة</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs text-gray-500"><th class="py-2 px-3">الأستاذ</th><th class="py-2 px-3">القسم</th><th class="py-2 px-3">الحصة</th><th class="py-2 px-3">التاريخ</th><th class="py-2 px-3 text-center">إجراء</th></tr></thead>
                    <tbody>{pres_rows}</tbody>
                </table>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6 space-y-4">
                <h2 class="text-md font-bold text-gray-800 border-b pb-2">غيابات التلاميذ</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs text-gray-500"><th class="py-2 px-3">التلميذ</th><th class="py-2 px-3">القسم</th><th class="py-2 px-3">الأستاذ</th><th class="py-2 px-3">التاريخ</th><th class="py-2 px-3">الحالة</th></tr></thead>
                    <tbody>{att_rows}</tbody>
                </table>
            </div>
        </div>
    </body></html>
    """

@app.route('/counselor/approve-presence/<int:pid>')
def approve_presence(pid):
    if session.get('role') != 'counselor': return redirect(url_for('home'))
    p = TeacherPresence.query.get(pid)
    if p: p.status = 'مصادق عليه (حضور مسجل بالساعة)'; db.session.commit()
    return redirect(url_for('counselor_dashboard_view'))

# ==============================================================================
# النهاية: لوحة تحكم الحارس العام
# ==============================================================================


# ==============================================================================
# البداية: لوحة تحكم الناظر (متابعة دفاتر النصوص)
# ==============================================================================

@app.route('/deputy/dashboard-view')
def deputy_dashboard_view():
    if session.get('role') != 'inspector_deputy': return redirect(url_for('home'))
    logs = LessonLog.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{l.teacher_name}</td><td class='py-3 px-4'>{l.section_name}</td><td class='py-3 px-4 font-bold'>{l.lesson_title}</td><td class='py-3 px-4'>{l.content}</td><td class='py-3 px-4'>{l.date}</td></tr>" for l in logs]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد دروس.</td></tr>"
    
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-indigo-600">
                <div><h1 class="text-xl font-bold text-gray-800">التنسيق البيداغوجي - السيد الناظر</h1></div>
                <a href="/logout" class="bg-red-50 text-red-600 border px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">متابعة دفاتر النصوص الرقمية</h2>
                <table class="w-full text-right">
                    <thead><tr class="bg-gray-50 border-b text-xs text-gray-500"><th class="py-3 px-4">الأستاذ</th><th class="py-3 px-4">القسم</th><th class="py-3 px-4">الدرس</th><th class="py-3 px-4">المحتوى</th><th class="py-3 px-4">التاريخ</th></tr></thead>
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
# البداية: لوحة تحكم المدير (تحديد الساعات الفعلية ومتابعة غياب الأساتذة)
# ==============================================================================

@app.route('/director/dashboard-view')
def director_dashboard_view():
    if session.get('role') != 'director': return redirect(url_for('home'))
    
    teachers = User.query.filter_by(role='teacher').all()
    teacher_rows = ""
    for t in teachers:
        wl = TeacherWorkload.query.filter_by(teacher_username=t.username).first()
        exp = wl.expected_hours if wl else 18.0
        approved_cnt = TeacherPresence.query.filter_by(teacher_username=t.username, status='مصادق عليه (حضور مسجل بالساعة)').count()
        act = float(approved_cnt) * 1.0
        absent = max(0.0, exp - act)
        
        teacher_rows += f"""
        <tr class="border-b">
            <td class="py-3 px-4 text-sm font-semibold">{t.fullname}</td>
            <td class="py-3 px-4 text-sm font-bold text-blue-700">{exp} س</td>
            <td class="py-3 px-4 text-sm font-bold text-emerald-700">{act} س</td>
            <td class="py-3 px-4 text-sm font-bold text-red-700">{absent} س</td>
            <td class="py-3 px-4 text-center">
                <form action="/director/update-workload" method="POST" class="inline-flex gap-2">
                    <input type="hidden" name="teacher_username" value="{t.username}">
                    <input type="number" step="0.5" name="expected_hours" value="{exp}" class="w-20 px-2 py-1 rounded border text-xs">
                    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs font-bold">تحديث النصاب</button>
                </form>
            </td>
        </tr>
        """

    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-blue-800">
                <div>
                    <h1 class="text-xl font-bold text-gray-800">لوحة القيادة الشاملة - السيد المدير</h1>
                    <p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي | مؤشرات الحجم الساعي والغياب للأساتذة</p>
                </div>
                <a href="/logout" class="bg-red-50 text-red-600 border px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>

            <div class="bg-white rounded-2xl shadow-md p-6 space-y-4">
                <h2 class="text-md font-bold text-gray-800 border-b pb-2">إدارة الحجم الساعي ومتابعة ساعات غياب الأساتذة</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-right">
                        <thead>
                            <tr class="bg-gray-50 border-b text-xs text-gray-500">
                                <th class="py-3 px-4">الأستاذ</th>
                                <th class="py-3 px-4">الساعات المفترضة (النصاب)</th>
                                <th class="py-3 px-4">الساعات الفعلية (المصادق عليها)</th>
                                <th class="py-3 px-4">ساعات الغياب المقدرة</th>
                                <th class="py-3 px-4 text-center">إجراء (تحديد لمرة واحدة)</th>
                            </tr>
                        </thead>
                        <tbody>{teacher_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </body></html>
    """

@app.route('/director/update-workload', methods=['POST'])
def update_workload():
    if session.get('role') != 'director': return redirect(url_for('home'))
    t_uname = request.form.get('teacher_username')
    try:
        new_exp = float(request.form.get('expected_hours'))
    except:
        new_exp = 18.0
        
    wl = TeacherWorkload.query.filter_by(teacher_username=t_uname).first()
    if wl:
        wl.expected_hours = new_exp
    else:
        t_user = User.query.filter_by(username=t_uname).first()
        t_name = t_user.fullname if t_user else 'أستاذ'
        db.session.add(TeacherWorkload(teacher_username=t_uname, teacher_fullname=t_name, expected_hours=new_exp))
    db.session.commit()
    return redirect(url_for('director_dashboard_view'))

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
