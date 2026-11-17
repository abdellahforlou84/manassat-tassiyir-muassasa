from flask import Flask, request, render_template, render_template_string, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# قاعدة بيانات افتراضية في الذاكرة للتجربة الفورية
USERS_DB = {
    'director': {'password': '123456', 'role': 'director', 'name': 'السيد مدير المؤسسة'},
    'deputy': {'password': '123456', 'role': 'inspector_deputy', 'name': 'السيد ناظر المؤسسة'},
    'counselor': {'password': '123456', 'role': 'counselor', 'name': 'السيد مستشار التربية'},
    'teacher': {'password': '123456', 'role': 'teacher', 'name': 'الأستاذ الفاضل'}
}

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

        {% if error %}
        <div class="mb-4 p-3 rounded-lg text-xs font-semibold bg-red-50 text-red-800 border border-red-300 text-center">
            {{ error }}
        </div>
        {% endif %}

        {% if success %}
        <div class="mb-4 p-3 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300 text-center">
            {{ success }}
        </div>
        {% endif %}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" placeholder="مثال: director أو teacher" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
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

        <div class="mt-5 p-3 bg-slate-100 rounded-lg text-xs text-slate-600">
            <p class="font-bold mb-1 text-slate-700">حسابات التجربة السريعة (كلمة المرور: 123456):</p>
            <div class="grid grid-cols-2 gap-1">
                <span>• مدير: <b>director</b></span>
                <span>• ناظر: <b>deputy</b></span>
                <span>• مستشار: <b>counselor</b></span>
                <span>• أستاذ: <b>teacher</b></span>
            </div>
        </div>

        <div class="flex justify-between items-center mt-5 text-sm">
            <a href="/register" class="text-blue-600 hover:underline font-medium">إنشاء حساب جديد</a>
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
    <title>منصة تسيير المؤسسة - تسجيل حساب جديد</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-gray-800">إنشاء حساب جديد</h1>
            <p class="text-sm text-gray-500 mt-2">تسجيل عضوية جديدة وتفعيلها مباشرة</p>
        </div>

        <form action="/register-action" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الاسم واللقب</label>
                <input type="text" name="fullname" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم (للدخول)</label>
                <input type="text" name="username" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
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
                إنشاء الحساب والدخول
            </button>
        </form>
        <div class="text-center mt-5">
            <a href="/" class="text-sm text-blue-600 hover:underline font-medium">العودة إلى تسجيل الدخول</a>
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
            <a href="/" class="text-sm text-blue-600 hover:underline font-medium">العودة إلى تسجيل الدخول</a>
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
    username = request.form.get('username').strip()
    password = request.form.get('password')
    role = request.form.get('role')
    
    USERS_DB[username] = {'password': password, 'role': role, 'name': fullname}
    return render_template_string(LOGIN_TEMPLATE, success=f"تم إنشاء حساب ({username}) بنجاح! يمكنك الدخول الآن.")

@app.route('/forgot-action', methods=['POST'])
def forgot_action():
    username = request.form.get('username').strip()
    new_password = request.form.get('new_password')
    
    if username in USERS_DB:
        USERS_DB[username]['password'] = new_password
        return render_template_string(LOGIN_TEMPLATE, success="تم تغيير كلمة المرور بنجاح! سجل دخولك الآن.")
    else:
        return render_template_string(LOGIN_TEMPLATE, error="اسم المستخدم غير موجود في النظام.")

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', '')

    user = USERS_DB.get(username)
    
    if not user or user['password'] != password:
        return render_template_string(LOGIN_TEMPLATE, error="اسم المستخدم أو كلمة المرور غير صحيحة!")
        
    if user['role'] != role:
        return render_template_string(LOGIN_TEMPLATE, error="الصفة التربوية المختارة لا تتطابق مع هذا الحساب!")

    session['username'] = username
    session['role'] = role
    display_name = user['name']

    # محاولة عرض القوالب الموجودة في مجلد templates، وفي حال وجود أي خلل فيها يتم عرض لوحة بديلة أنيقة تلقائياً
    template_map = {
        'director': 'dashboard_director.html',
        'inspector_deputy': 'dashboard_deputy.html',
        'counselor': 'dashboard_counselor.html',
        'teacher': 'dashboard_teacher.html'
    }
    
    try:
        return render_template(template_map[role], username=display_name)
    except Exception:
        return f"""
        <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
            <div class="bg-white rounded-2xl shadow-xl p-8 max-w-lg w-full text-center border-t-8 border-blue-600">
                <h1 class="text-2xl font-bold text-gray-800 mb-2">أهلاً بك، {display_name}</h1>
                <p class="text-blue-600 font-semibold mb-6">تم الدخول بنجاح بصفتك: {role}</p>
                <a href="/" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800">تسجيل الخروج</a>
            </div>
        </body></html>
        """
# ==================== الميزة الأولى: إدارة الغيابات اليومية ====================

# إنشاء جدول الغيابات في قاعدة البيانات تلقائياً إن لمש يكن موجوداً
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='غائب')

with app.app_context():
    db.create_all()

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
            teacher_name=session.get('username', 'أستاذ'),
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
            <p class="text-emerald-600 font-semibold mb-6">تم تحويل بيانات الغياب إلى مصلحة الاستشارة التربوية (الحارس العام).</p>
            <a href="/" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800">العودة للوحة التحكم</a>
        </div>
    </body></html>
    """
# ==================== الميزة الثانية: دفتر النصوص الرقمي ====================

# إنشاء جدول دفتر النصوص في قاعدة البيانات تلقائياً
class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()

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
            teacher_name=session.get('username', 'أستاذ'),
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
            <p class="text-indigo-600 font-semibold mb-6">تم حفظ محتوى الدرس في دفتر النصوص الرقمي وإرساله لمتابعة السيد الناظر.</p>
            <a href="/" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800">العودة للوحة التحكم</a>
        </div>
    </body></html>
    """



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
