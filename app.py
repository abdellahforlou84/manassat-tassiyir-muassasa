# ==============================================================================
# البداية: استيراد المكتبات وإعداد التطبيق وقاعدة البيانات الأساسية
# ==============================================================================

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# إعداد قاعدة البيانات المحلية SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تعريف الكائن db أولاً وقبل أي جدول
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
    except Exception as e:
        print(f"Database error: {e}")

# ==============================================================================
# النهاية: إعداد القاعدة الأساسية وجداول النظام
# ==============================================================================


# ==============================================================================
# البداية: مسارات المصادقة وتسجيل الدخول والخروج
# ==============================================================================

@app.route('/')
def home():
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '')

    user = User.query.filter_by(username=username).first()
    
    if not user or user.password != password:
        flash('اسم المستخدم أو كلمة المرور غير صحيحة!', 'danger')
        return redirect(url_for('home'))
        
    if user.role != role:
        flash('الصفة التربوية المختارة لا تتطابق مع هذا الحساب!', 'danger')
        return redirect(url_for('home'))

    session['username'] = user.username
    session['fullname'] = user.fullname
    session['role'] = user.role

    if role == 'teacher':
        return redirect(url_for('teacher_dashboard_view'))
    elif role == 'counselor':
        return redirect(url_for('counselor_dashboard_view'))
    else:
        return f"""
        <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
            <div class="bg-white rounded-2xl shadow-xl p-8 max-w-lg w-full text-center border-t-8 border-blue-600">
                <h1 class="text-2xl font-bold text-gray-800 mb-2">أهلاً بك، {user.fullname}</h1>
                <p class="text-blue-600 font-semibold mb-6">تم الدخول بنجاح بصفتك: {role}</p>
                <a href="/logout" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800">تسجيل الخروج</a>
            </div>
        </body></html>
        """

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ==============================================================================
# النهاية: مسارات المصادقة وتسجيل الدخول والخروج
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
# البداية: تشغيل السيرفر
# ==============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# ==============================================================================
# النهاية: تشغيل السيرفر
# ==============================================================================
