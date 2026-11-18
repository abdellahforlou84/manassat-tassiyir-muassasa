# ==============================================================================
# منصة تسيير المؤسسة - ثانوية الشهيد قوديد أحمد (سيدي الشحمي)
# الكود المتكامل والمحمي بالكامل (تلاميذ وأقسام مدمجة داخل الكود)
# ==============================================================================

from flask import Flask, render_template_string, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# إعداد قاعدة البيانات
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'philo_school_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==============================================================================
# نماذج قواعد البيانات (Models)
# ==============================================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    teacher_username = db.Column(db.String(80), nullable=True)

class TeacherSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(80), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='غائب')

class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(100), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

# القائمة الرسمية للأقسام
OFFICIAL_SECTIONS = [
    "3أف1", "3أف2", "3لغ", "3ع ت1", "3ع ت2", "3ريا", "3ت ر",
    "2أف1", "2أف2", "2ع ت1", "2ع ت2", "2لغ", "2ريا", "2تق", "2تر",
    "1ج م ع01", "1ج م ع02", "1ج م ع03", "1ج م ع04", "1ج م ع05",
    "1ج م أ01", "1ج م أ02", "1ج م أ03", "1أ1"
]

# قوائم التلاميذ المستخرجة من الصور بالترتيب المطلوب
DEFAULT_STUDENTS = [
    # --- قسم 1أ1 ---
    {"fullname": "المراربي أمينة", "section_name": "1أ1"},
    {"fullname": "بدة ملاك", "section_name": "1أ1"},
    {"fullname": "بران محمد", "section_name": "1أ1"},
    {"fullname": "بلعباس بن قرعة كوثر", "section_name": "1أ1"},
    {"fullname": "بلميلود أدم", "section_name": "1أ1"},
    {"fullname": "بلميلود هاجر", "section_name": "1أ1"},
    {"fullname": "بلهادف بدرة سلسبيل", "section_name": "1أ1"},
    {"fullname": "بلولو سندس", "section_name": "1أ1"},
    {"fullname": "بن حمادي إسلام", "section_name": "1أ1"},
    {"fullname": "بن حمدود سندس", "section_name": "1أ1"},
    {"fullname": "بن حصالي ألاء", "section_name": "1أ1"},
    {"fullname": "بن دوخة عبد الرحمان", "section_name": "1أ1"},
    {"fullname": "بن سعيد مروى", "section_name": "1أ1"},
    {"fullname": "بن عبد المومن آية", "section_name": "1أ1"},
    {"fullname": "بن علال هبة خيرة", "section_name": "1أ1"},
    {"fullname": "بن ناصر رتاج", "section_name": "1أ1"},
    {"fullname": "بنوار مريم", "section_name": "1أ1"},
    {"fullname": "بوخرص محمد صهيب", "section_name": "1أ1"},
    {"fullname": "بوري توفيق", "section_name": "1أ1"},
    {"fullname": "بورياح ايوب", "section_name": "1أ1"},
    {"fullname": "بوزيان محمد الأمين", "section_name": "1أ1"},
    {"fullname": "حمودي فاطمة", "section_name": "1أ1"},
    {"fullname": "داودي فاطمة الزهراء", "section_name": "1أ1"},
    {"fullname": "دحماني أمين", "section_name": "1أ1"},
    {"fullname": "دراديز اسلام الدين", "section_name": "1أ1"},
    {"fullname": "رابح نوال", "section_name": "1أ1"},
    {"fullname": "رفاسي ياسمين", "section_name": "1أ1"},
    {"fullname": "سريك رزان عائشة", "section_name": "1أ1"},
    {"fullname": "سعدو اسراء", "section_name": "1أ1"},
    {"fullname": "شتوكي آية", "section_name": "1أ1"},
    {"fullname": "شفار حبيب", "section_name": "1أ1"},
    {"fullname": "شفار بشرى", "section_name": "1أ1"},
    {"fullname": "عايد وصال نور الهدى", "section_name": "1أ1"},
    {"fullname": "عبيد نور الدين", "section_name": "1أ1"},
    {"fullname": "كاتب الهاشمي هاجر", "section_name": "1أ1"},
    {"fullname": "كرتالی محمد ايهاب", "section_name": "1أ1"},
    {"fullname": "كيري أية اناس", "section_name": "1أ1"},
    {"fullname": "محبوب فراح", "section_name": "1أ1"},
    {"fullname": "مرين رؤية", "section_name": "1أ1"},
    {"fullname": "مرين عمر", "section_name": "1أ1"},
    {"fullname": "مكاب ياسين محمد سالم", "section_name": "1أ1"},
    {"fullname": "مناع حمزة", "section_name": "1أ1"},
    {"fullname": "مهدي أسماء", "section_name": "1أ1"},
    {"fullname": "ناصر شرقي حسن حسين", "section_name": "1أ1"},

    # --- قسم 1أ2 ---
    {"fullname": "بخدة إسراء", "section_name": "1أ2"},
    {"fullname": "برحمون سناء", "section_name": "1أ2"},
    {"fullname": "بلغربي إسراء", "section_name": "1أ2"},
    {"fullname": "بن دادة ملاك", "section_name": "1أ2"},
    {"fullname": "بن عطية فاطمة", "section_name": "1أ2"},
    {"fullname": "بن علال عبد الله اسلام", "section_name": "1أ2"},
    {"fullname": "بن عودة شحط شهيناز", "section_name": "1أ2"},
    {"fullname": "بنافلة فاروق", "section_name": "1أ2"},
    {"fullname": "بوخلوة محمد عز الدين", "section_name": "1أ2"},
    {"fullname": "بوزار أمينة", "section_name": "1أ2"},
    {"fullname": "بوزيان آية ملاك", "section_name": "1أ2"},
    {"fullname": "بوعلام مليكة", "section_name": "1أ2"},
    {"fullname": "بوقفة عبد الكريم", "section_name": "1أ2"},
    {"fullname": "بوليلة عثمان", "section_name": "1أ2"},
    {"fullname": "ثابت حفصة", "section_name": "1أ2"},
    {"fullname": "ثابت سندس", "section_name": "1أ2"},
    {"fullname": "جيد هديل", "section_name": "1أ2"},
    {"fullname": "حداد زهرة", "section_name": "1أ2"},
    {"fullname": "حنيفي أمال", "section_name": "1أ2"},
    {"fullname": "روام سريك عائشة", "section_name": "1أ2"},
    {"fullname": "روماري محمد عادل", "section_name": "1أ2"},
    {"fullname": "زوج ملاك", "section_name": "1أ2"},
    {"fullname": "زوانب هواري", "section_name": "1أ2"},
    {"fullname": "سجلوماسى هند", "section_name": "1أ2"},
    {"fullname": "شايب الدور آية الرحمان", "section_name": "1أ2"},
    {"fullname": "شريفي فريال", "section_name": "1أ2"},
    {"fullname": "صابر معزوز بتينة", "section_name": "1أ2"},
    {"fullname": "عمارة فراح", "section_name": "1أ2"},
    {"fullname": "عواد إيمان", "section_name": "1أ2"},
    {"fullname": "عياد إكرام", "section_name": "1أ2"},
    {"fullname": "فايدة ريهام أميمة", "section_name": "1أ2"},
    {"fullname": "فرحاوي فراح غزلان", "section_name": "1أ2"},
    {"fullname": "قبايلى محمد مروان", "section_name": "1أ2"},
    {"fullname": "قطاف رحيل", "section_name": "1أ2"},
    {"fullname": "قورين اسيا", "section_name": "1أ2"},
    {"fullname": "كرتالي لجين", "section_name": "1أ2"},
    {"fullname": "مرين عبد الباسط عبد الصمد", "section_name": "1أ2"},
    {"fullname": "مرين يمينة", "section_name": "1أ2"},
    {"fullname": "موزاع دلين", "section_name": "1أ2"},
    {"fullname": "ناصر الشرقي مصطفى", "section_name": "1أ2"},
    {"fullname": "ناصر شرقي ميلود", "section_name": "1أ2"},
    {"fullname": "نباتي شرقي شيماء", "section_name": "1أ2"},
    {"fullname": "وانس مشكور سرين", "section_name": "1أ2"},

    # --- قسم 1أ3 ---
    {"fullname": "بداوي أسيا", "section_name": "1أ3"},
    {"fullname": "بركليت رحيل", "section_name": "1أ3"},
    {"fullname": "بلبية أمال", "section_name": "1أ3"},
    {"fullname": "بلعابد بشرى", "section_name": "1أ3"},
    {"fullname": "بلعربي كوثر", "section_name": "1أ3"},
    {"fullname": "بلكحلة أحمد", "section_name": "1أ3"},
    {"fullname": "بلميلود دعاء", "section_name": "1أ3"},
    {"fullname": "بن عطية فدوى نضال", "section_name": "1أ3"},
    {"fullname": "بنوار ياسين عبد الرحمان", "section_name": "1أ3"},
    {"fullname": "بوخلفة احلام", "section_name": "1أ3"},
    {"fullname": "بورشاش عبد الحكيم", "section_name": "1أ3"},
    {"fullname": "بوطيبة معمر عبد الغنى", "section_name": "1أ3"},
    {"fullname": "تقية محمد الأمين", "section_name": "1أ3"},
    {"fullname": "تويلي صفاء", "section_name": "1أ3"},
    {"fullname": "جبلى نريمان", "section_name": "1أ3"},
    {"fullname": "جديد خيرة", "section_name": "1أ3"},
    {"fullname": "حمادي دنيا", "section_name": "1أ3"},
    {"fullname": "رزيق يوسف", "section_name": "1أ3"},
    {"fullname": "رفاس هواري إسحاق", "section_name": "1أ3"},
    {"fullname": "سافر محمد", "section_name": "1أ3"},
    {"fullname": "شلابي محمد ياسر", "section_name": "1أ3"},
    {"fullname": "صالح هلال محمد أمين", "section_name": "1أ3"},
    {"fullname": "طويل رقية ملاك", "section_name": "1أ3"},
    {"fullname": "عبيد شيراز نسرين", "section_name": "1أ3"},
    {"fullname": "عتو نور الدين عبد الصمد", "section_name": "1أ3"},
    {"fullname": "عزة فريال", "section_name": "1أ3"},
    {"fullname": "علاوي فريال عائشة", "section_name": "1أ3"},
    {"fullname": "عمارة دعاء", "section_name": "1أ3"},
    {"fullname": "عيسى جميلة", "section_name": "1أ3"},
    {"fullname": "غراس بهجة ايناس", "section_name": "1أ3"},
    {"fullname": "قرميط رتاج سهيلة", "section_name": "1أ3"},
    {"fullname": "قنيش فاطمة", "section_name": "1أ3"},
    {"fullname": "قنيش أيوب", "section_name": "1أ3"},
    {"fullname": "كروش أسيا", "section_name": "1أ3"},
    {"fullname": "كيري محمد انس", "section_name": "1أ3"},
    {"fullname": "كيلالي ملحة", "section_name": "1أ3"},
    {"fullname": "مبارك إخلاص", "section_name": "1أ3"},
    {"fullname": "مختاري اميمة", "section_name": "1أ3"},
    {"fullname": "مزيود انس", "section_name": "1أ3"},
    {"fullname": "معيطى رتاج", "section_name": "1أ3"},
    {"fullname": "مملوك ربيعة", "section_name": "1أ3"},
    {"fullname": "مواز دعاء", "section_name": "1أ3"},
    {"fullname": "نباتى شرقى شيراز", "section_name": "1أ3"},

    # --- قسم 1ع1 ---
    {"fullname": "ابراهيم مفلاح اسلام", "section_name": "1ع1"},
    {"fullname": "اليوبي هبة الرحمان", "section_name": "1ع1"},
    {"fullname": "بحوصي محمد العدنان", "section_name": "1ع1"},
    {"fullname": "برفاس وصال", "section_name": "1ع1"},
    {"fullname": "بلحبيب بشري", "section_name": "1ع1"},
    {"fullname": "بلعباس مصطفى عبد الرحمان", "section_name": "1ع1"},
    {"fullname": "بلعباس اميرة", "section_name": "1ع1"},
    {"fullname": "بلقاسم رفيدة", "section_name": "1ع1"},
    {"fullname": "بن زيادي عماد الدين", "section_name": "1ع1"},
    {"fullname": "بن عائشة احمد حسام", "section_name": "1ع1"},
    {"fullname": "بن قانة نورهان", "section_name": "1ع1"},
    {"fullname": "بنوار اسامة", "section_name": "1ع1"},
    {"fullname": "بوخلوة عيسى", "section_name": "1ع1"},
    {"fullname": "بورداش عبد الرحمان", "section_name": "1ع1"},
    {"fullname": "بوزرادة جميلة", "section_name": "1ع1"},
    {"fullname": "بوسيف شيخ", "section_name": "1ع1"},
    {"fullname": "بولحليب عبد الحق", "section_name": "1ع1"},
    {"fullname": "حمزة شهد انصاف", "section_name": "1ع1"},
    {"fullname": "خนنو ملاك", "section_name": "1ع1"},
    {"fullname": "خيشان ابراهيم", "section_name": "1ع1"},
    {"fullname": "رفاس نور الهدى خيرة", "section_name": "1ع1"},
    {"fullname": "رقيق يسعد بشرى", "section_name": "1ع1"},
    {"fullname": "زياني سولاف", "section_name": "1ع1"},
    {"fullname": "شارف إسماعيل", "section_name": "1ع1"},
    {"fullname": "شحمي رتاج", "section_name": "1ع1"},
    {"fullname": "غمري أماني", "section_name": "1ع1"},
    {"fullname": "قيروان دعاء", "section_name": "1ع1"},
    {"fullname": "كروم محمد علال", "section_name": "1ع1"},
    {"fullname": "مصالح انس", "section_name": "1ع1"},
    {"fullname": "مغربي نور الهدى", "section_name": "1ع1"},
    {"fullname": "نباتى شرقى ملاك", "section_name": "1ع1"},
    {"fullname": "هبري إسمهان رميسة", "section_name": "1ع1"}
]

# تهيئة قاعدة البيانات والتلاميذ الافتراضيين
with app.app_context():
    db.create_all()
    if not User.query.first():
        db.session.add_all([
            User(username='director', password='123456', role='director', fullname='السيد المدير'),
            User(username='deputy', password='123456', role='inspector_deputy', fullname='السيد الناظر'),
            User(username='counselor', password='123456', role='counselor', fullname='السيد مستشار التربية'),
            User(username='teacher', password='123456', role='teacher', fullname='الأستاذ فغلو عبد الله')
        ])
        db.session.commit()
    
    if not Student.query.first():
        for s in DEFAULT_STUDENTS:
            db.session.add(Student(fullname=s["fullname"], section_name=s["section_name"], teacher_username='system'))
        db.session.commit()

# ==============================================================================
# واجهات HTML والمسارات
# ==============================================================================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - ثانوية الشهيد قوديد أحمد</title>
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
                <input type="text" name="username" placeholder="مثال: teacher" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" placeholder="123456" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الصفة التربوية (الدور)</label>
                <select name="role" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white focus:ring-2 focus:ring-blue-600 focus:outline-none">
                    <option value="" disabled selected>-- اختر صفتك في المؤسسة --</option>
                    <option value="director">المدير</option>
                    <option value="inspector_deputy">الناظر</option>
                    <option value="counselor">مستشار التربية</option>
                    <option value="teacher">أستاذ</option>
                </select>
            </div>
            <button type="submit" class="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-3 rounded-lg shadow-lg transition">
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
# لوحة تحكم الأستاذ (اختيار الأقسام + المناداة + تسجيل الغيابات)
# ==============================================================================

@app.route('/teacher/dashboard-view')
def teacher_dashboard_view():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    teacher_uname = session.get('username')
    today_date = datetime.now().strftime('%Y-%m-%d')

    assigned_sections = TeacherSection.query.filter_by(teacher_username=teacher_uname).all()
    assigned_section_names = [ts.section_name for ts in assigned_sections]

    selected_section = request.args.get('section', assigned_section_names[0] if assigned_section_names else '')
    students_in_section = Student.query.filter_by(section_name=selected_section).all() if selected_section else []

    my_sections_options = "".join([f'<option value="{sec}" {"selected" if sec == selected_section else ""}>{sec}</option>' for sec in assigned_section_names])
    all_sections_options = "".join([f'<option value="{sec}">{sec}</option>' for sec in OFFICIAL_SECTIONS if sec not in assigned_section_names])

    attendance_rows = "".join([f"""
    <tr class="border-b hover:bg-gray-50">
        <td class="py-2.5 px-3 text-sm font-semibold text-gray-800">{s.fullname}</td>
        <td class="py-2.5 px-3 text-sm text-gray-600">{s.section_name}</td>
        <td class="py-2.5 px-3 text-center">
            <form action="/teacher/mark-absence" method="POST" class="inline">
                <input type="hidden" name="student_name" value="{s.fullname}">
                <input type="hidden" name="section_name" value="{s.section_name}">
                <input type="hidden" name="date" value="{today_date}">
                <input type="hidden" name="selected_section" value="{selected_section}">
                <button type="submit" class="bg-red-50 text-red-600 border border-red-200 hover:bg-red-600 hover:text-white px-3 py-1 rounded text-xs font-bold transition">تسجيل غياب اليوم</button>
            </form>
        </td>
    </tr>
    """ for s in students_in_section]) or f"<tr><td colspan='3' class='text-center py-4 text-gray-400 text-xs'>لا توجد تلاميذ في القسم {selected_section} أو لم تختار قسماً بعد. اختر قسماً من القائمة أعلاه.</td></tr>"

    my_sections_list_html = "".join([f"""
    <div class="flex justify-between items-center bg-gray-50 px-3 py-2 rounded-lg border text-xs">
        <span class="font-bold text-blue-900">{ts.section_name}</span>
        <a href="/teacher/remove-section/{ts.id}" class="text-red-600 hover:underline">حذف</a>
    </div>
    """ for ts in assigned_sections]) or "<p class='text-xs text-gray-400'>لم تضف أي قسم بعد.</p>"

    return f"""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-4 md:p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 text-center border-b-4 border-blue-800 space-y-1">
                <p class="text-xs font-bold text-gray-600">الجمهورية الجزائرية الديمقراطية الشعبية | وزارة التربية الوطنية</p>
                <h2 class="text-lg font-extrabold text-blue-900 mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</h2>
                <div class="pt-2 flex justify-between items-center border-t mt-4 text-sm">
                    <span class="font-bold text-gray-700">الأستاذ: {session.get('fullname')} | التاريخ: {today_date}</span>
                    <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-red-100">تسجيل الخروج</a>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- إدارة الأقسام الخاصة بالأستاذ -->
                <div class="bg-white rounded-2xl shadow-md p-5 space-y-4">
                    <h3 class="text-md font-bold text-gray-800 border-b pb-2">إدارة أقسامي المسندة</h3>
                    <form action="/teacher/add-section" method="POST" class="space-y-3">
                        <select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white">
                            <option value="" disabled selected>-- اختر قسماً لإضافته --</option>
                            {all_sections_options}
                        </select>
                        <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-lg text-xs transition">إضافة إلى أقسامي</button>
                    </form>
                    <div class="space-y-2 mt-3 max-h-48 overflow-y-auto border-t pt-2">
                        {my_sections_list_html}
                    </div>
                </div>

                <!-- قائمة المناداة والغيابات للقسم المختار -->
                <div class="bg-white rounded-2xl shadow-md p-5 md:col-span-2 space-y-4">
                    <div class="flex justify-between items-center border-b pb-2">
                        <h3 class="text-md font-bold text-gray-800">قائمة المناداة للقسم المختار</h3>
                        <form method="GET" action="/teacher/dashboard-view" class="flex gap-2">
                            <select name="section" onchange="this.form.submit()" class="px-3 py-1.5 rounded-lg border text-xs bg-white font-bold text-blue-800">
                                <option value="" disabled selected>-- اختر القسم للمناداة --</option>
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

            <!-- دفتر النصوص الرقمي -->
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h3 class="text-md font-bold text-gray-800 mb-3">دفتر النصوص الرقمي (تسجيل الدرس المنجز)</h3>
                <form action="/teacher/submit-lesson" method="POST" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div><select name="section_name" required class="w-full px-3 py-2 rounded-lg border text-xs bg-white"><option value="" disabled selected>-- اختر القسم --</option>{my_sections_options}</select></div>
                    <div><input type="text" name="lesson_title" placeholder="عنوان الدرس..." required class="w-full px-3 py-2 rounded-lg border text-xs"></div>
                    <div><input type="text" name="content" placeholder="الملخص..." required class="w-full px-3 py-2 rounded-lg border text-xs"></div>
                    <div class="flex gap-2">
                        <input type="date" name="date" value="{today_date}" required class="w-full px-3 py-2 rounded-lg border text-xs">
                        <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-lg text-xs">حفظ</button>
                    </div>
                </form>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/teacher/add-section', methods=['POST'])
def add_section():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    sec = request.form.get('section_name')
    uname = session.get('username')
    if sec and not TeacherSection.query.filter_by(teacher_username=uname, section_name=sec).first():
        db.session.add(TeacherSection(teacher_username=uname, section_name=sec))
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view', section=sec))

@app.route('/teacher/remove-section/<int:sid>')
def remove_section(sid):
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    ts = TeacherSection.query.get(sid)
    if ts and ts.teacher_username == session.get('username'):
        db.session.delete(ts)
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view'))

@app.route('/teacher/mark-absence', methods=['POST'])
def mark_absence():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    student_name = request.form.get('student_name')
    section_name = request.form.get('section_name')
    date = request.form.get('date')
    selected_section = request.form.get('selected_section')
    if student_name and section_name and date:
        if not Attendance.query.filter_by(student_name=student_name, date=date).first():
            db.session.add(Attendance(student_name=student_name, section_name=section_name, teacher_name=session.get('fullname'), date=date, status='غائب'))
            db.session.commit()
    return redirect(url_for('teacher_dashboard_view', section=selected_section))

@app.route('/teacher/submit-lesson', methods=['POST'])
def submit_lesson():
    if session.get('role') != 'teacher': return redirect(url_for('home'))
    sec = request.form.get('section_name')
    title = request.form.get('lesson_title')
    content = request.form.get('content')
    date = request.form.get('date')
    if sec and title and content and date:
        db.session.add(LessonLog(teacher_name=session.get('fullname'), section_name=sec, lesson_title=title, content=content, date=date))
        db.session.commit()
    return redirect(url_for('teacher_dashboard_view', section=sec))

# ==============================================================================
# لوحات الإدارة الأخرى
# ==============================================================================

@app.route('/counselor/dashboard-view')
def counselor_dashboard_view():
    if session.get('role') != 'counselor': return redirect(url_for('home'))
    attendances = Attendance.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{a.student_name}</td><td class='py-3 px-4'>{a.section_name}</td><td class='py-3 px-4'>{a.teacher_name}</td><td class='py-3 px-4'>{a.date}</td><td class='py-3 px-4'><span class='bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold'>{a.status}</span></td></tr>" for a in attendances]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد غيابات مسجلة.</td></tr>"
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-amber-600">
                <div><h1 class="text-xl font-bold text-gray-800">مكتب الاستشارة التربوية - الحارس العام</h1><p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد</p></div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <h2 class="text-md font-bold text-gray-800 mb-4">ورقة الغيابات اليومية الواردة من الأساتذة</h2>
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
    if session.get('role') != 'inspector_deputy': return redirect(url_for('home'))
    logs = LessonLog.query.all()
    rows = "".join([f"<tr class='border-b'><td class='py-3 px-4'>{l.teacher_name}</td><td class='py-3 px-4'>{l.section_name}</td><td class='py-3 px-4 font-bold'>{l.lesson_title}</td><td class='py-3 px-4'>{l.content}</td><td class='py-3 px-4'>{l.date}</td></tr>" for l in logs]) or "<tr><td colspan='5' class='text-center py-4 text-gray-400'>لا توجد دروس مسجلة.</td></tr>"
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-indigo-600">
                <div><h1 class="text-xl font-bold text-gray-800">التنسيق البيداغوجي - السيد الناظر</h1><p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد</p></div>
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
    if session.get('role') != 'director': return redirect(url_for('home'))
    return f"""
    <html lang="ar" dir="rtl"><head><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet"><style>body{{font-family:'Cairo',sans-serif;}}</style></head>
    <body class="bg-slate-100 min-h-screen p-6">
        <div class="max-w-5xl mx-auto space-y-6">
            <div class="bg-white rounded-2xl shadow-md p-6 flex justify-between items-center border-r-8 border-blue-800">
                <div><h1 class="text-xl font-bold text-gray-800">لوحة القيادة الشاملة - السيد المدير</h1><p class="text-xs text-gray-500 mt-1">ثانوية الشهيد قوديد أحمد</p></div>
                <a href="/logout" class="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm font-semibold">تسجيل الخروج</a>
            </div>
            <div class="bg-white rounded-2xl shadow-md p-6">
                <p class="text-sm text-gray-700">مرحباً بك سيادة المدير. إشراف شامل ومتابعة لحظية لسيرورة الانضباط والغيابات ودفاتر النصوص.</p>
            </div>
        </div>
    </body></html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
