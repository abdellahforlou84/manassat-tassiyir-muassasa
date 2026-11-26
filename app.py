import os
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    render_template_string,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "qoudid-ahmed-management-secret-key-2026")

# ==============================================================================
# إعداد قاعدة البيانات (يدعم PostgreSQL الدائم أو SQLite محلياً)
# ==============================================================================

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL:
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    IS_PERSISTENT_DB = True
    DB_MODE_LABEL = "قاعدة بيانات دائمة مفعّلة (PostgreSQL)"
else:
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "school_management.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
    IS_PERSISTENT_DB = False
    DB_MODE_LABEL = "وضع قاعدة البيانات المحلية (SQLite)"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

ROLES = {
    "director": "المدير",
    "inspector_deputy": "الناظر",
    "counselor": "مستشار التربية",
    "teacher": "أستاذ",
}

OFFICIAL_SECTIONS = [
    "1ج م آ 1", "1ج م آ 2", "1ج م آ 3",
    "1ج م ع 1", "1ج م ع 2", "1ج م ع 3", "1ج م ع 4", "1ج م ع 5",
    "2آف1", "2آف2",
    "2لغ1", "2لغ2",
    "2ع ت1", "2ع ت2",
    "2تق", "2ريا",
    "2تر (هـ ط)", "2تر (هـ ك)", "2تر (هـ م)",
    "3أف1", "3أف2",
    "3لغ (إسبانية)", "3لغ (ألمانية)",
    "3ع ت1", "3ع ت2",
    "3تق", "3ريا",
    "3تر (هـ ك)", "3تر (هـ م)",
]


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    sections_json = db.Column(db.Text, default="[]")
    weekly_hours = db.Column(db.Float, nullable=True)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def verify_password(self, raw_password):
        if not raw_password or not self.password_hash:
            return False
        if self.password_hash.startswith(("scrypt:", "pbkdf2:")):
            return check_password_hash(self.password_hash, raw_password)
        return self.password_hash == raw_password

    @property
    def sections(self):
        try:
            data = json.loads(self.sections_json or "[]")
            return data if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @sections.setter
    def sections(self, value):
        self.sections_json = json.dumps(value or [], ensure_ascii=False)


class TeacherSection(db.Model):
    __tablename__ = "teacher_section"
    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(80), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)


class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)
    teacher_username = db.Column(db.String(80), default="system")


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(150), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)
    teacher_username = db.Column(db.String(80), nullable=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    hours = db.Column(db.Float, default=1.0)
    approval_status = db.Column(db.String(20), default="approved")
    approved_by = db.Column(db.String(120), nullable=True)


class LessonLog(db.Model):
    __tablename__ = "lesson_log"
    id = db.Column(db.Integer, primary_key=True)
    teacher_username = db.Column(db.String(80), nullable=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(80), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(30), nullable=False)
    hours = db.Column(db.Float, default=1.0)
    approval_status = db.Column(db.String(20), default="pending")
    approved_by = db.Column(db.String(120), nullable=True)


DEFAULT_STUDENTS = [
    {"fullname": "زدام مايا", "section_name": "2ع ت2"},
    {"fullname": "سهالة عبد الله فارس الدين", "section_name": "2ع ت2"},
    {"fullname": "سى مرابط فريال", "section_name": "2ع ت2"},
    {"fullname": "شاوش محمد باديس", "section_name": "2ع ت2"},
    {"fullname": "شرقي فاطمة", "section_name": "2ع ت2"},
    {"fullname": "شعيب رحاب سارة", "section_name": "2ع ت2"},
    {"fullname": "شيخ ابراهيم", "section_name": "2ع ت2"},
    {"fullname": "شيكر جاوتی عبد المجيد", "section_name": "2ع ت2"},
    {"fullname": "صغيري وليد", "section_name": "2ع ت2"},
    {"fullname": "عالم جبار ناجی", "section_name": "2ع ت2"},
    {"fullname": "عثمانى شيماء", "section_name": "2ع ت2"},
    {"fullname": "عرابة لميس", "section_name": "2ع ت2"},
    {"fullname": "عنصر الاء", "section_name": "2ع ت2"},
    {"fullname": "غيلاس فارس إسلام", "section_name": "2ع ت2"},
    {"fullname": "فغلو خير الدين", "section_name": "2ع ت2"},
    {"fullname": "قرمى رانيا", "section_name": "2ع ت2"},
    {"fullname": "كرايی فايزة منال", "section_name": "2ع ت2"},
    {"fullname": "لزرق شلابي سولا ف", "section_name": "2ع ت2"},
    {"fullname": "ماموني نور الهدى", "section_name": "2ع ت2"},
    {"fullname": "مبارك ابتسام", "section_name": "2ع ت2"},
    {"fullname": "مسلم مروى", "section_name": "2ع ت2"},
    {"fullname": "نومية عبد الله", "section_name": "2ع ت2"},
    {"fullname": "هواري الياس", "section_name": "2ع ت2"},
    {"fullname": "واحمانی عصام الدين", "section_name": "2ع ت2"},
    {"fullname": "وليد جميلة", "section_name": "2ع ت2"},
    {"fullname": "يطو دعاء", "section_name": "2ع ت2"},
    {"fullname": "بختى ايمن", "section_name": "2تق"},
    {"fullname": "بركليت حنان", "section_name": "2تق"},
    {"fullname": "بشير عبد الإله", "section_name": "2تق"},
    {"fullname": "بلعباس آية", "section_name": "2تق"},
    {"fullname": "بلهواري بشرى", "section_name": "2تق"},
    {"fullname": "بوتنزار عبدالقادر", "section_name": "2تق"},
    {"fullname": "بودية بشرى", "section_name": "2تق"},
    {"fullname": "بوشعالة ريتاج الاء", "section_name": "2تق"},
    {"fullname": "بوقويلبة خديجة", "section_name": "2تق"},
    {"fullname": "بوكبدة علاء الدين", "section_name": "2تق"},
    {"fullname": "بولحية فاطمة الزهراء", "section_name": "2تق"},
    {"fullname": "تهامى محمد الصديق", "section_name": "2تق"},
    {"fullname": "خننو نهاد", "section_name": "2تق"},
    {"fullname": "دحمانى محمد ندير", "section_name": "2تق"},
    {"fullname": "دلباز حنان", "section_name": "2تق"},
    {"fullname": "دلباز عبد الجليل", "section_name": "2تق"},
    {"fullname": "رصانى خديجة", "section_name": "2تق"},
    {"fullname": "رصانى عبد الهادي", "section_name": "2تق"},
    {"fullname": "عشوري عبد الكريم", "section_name": "2تق"},
    {"fullname": "عليلات أيهم عبد الرحمان", "section_name": "2تق"},
    {"fullname": "غربي يوسف", "section_name": "2تق"},
    {"fullname": "غمري دعاء منى", "section_name": "2تق"},
    {"fullname": "قدورة حفصة", "section_name": "2تق"},
    {"fullname": "قيري صابرين", "section_name": "2تق"},
    {"fullname": "كرطالى ياسين", "section_name": "2تق"},
    {"fullname": "لوشنى سندس", "section_name": "2تق"},
    {"fullname": "مزغرانى عادل", "section_name": "2تق"},
    {"fullname": "موساوي محمد صهيب", "section_name": "2تق"},
    {"fullname": "يطو ايمان", "section_name": "2تق"},
    {"fullname": "بكة ريتاج", "section_name": "2ريا"},
    {"fullname": "بن عبورة جنة الايمان", "section_name": "2ريا"},
    {"fullname": "بوتين نرجس جوهر", "section_name": "2ريا"},
    {"fullname": "سعد هواري ياسين", "section_name": "2ريا"},
    {"fullname": "صحراوي صفاء", "section_name": "2ريا"},
    {"fullname": "كاعوش عائشة", "section_name": "2ريا"},
    {"fullname": "لحمر ايناس اميرة سندس", "section_name": "2ريا"},
    {"fullname": "مقداد إكرام", "section_name": "2ريا"},
    {"fullname": "بن زهرة عبد المعز", "section_name": "2تر (هـ ط)"},
    {"fullname": "سنحين إكرام", "section_name": "2تر (هـ ط)"},
    {"fullname": "عرابي بسملة", "section_name": "2تر (هـ ط)"},
    {"fullname": "لعموري عائشة", "section_name": "2تر (هـ ط)"},
    {"fullname": "مشتی اسراء", "section_name": "2تر (هـ ط)"},
    {"fullname": "مهون عبد الاله", "section_name": "2تر (هـ ط)"},
    {"fullname": "باوية محمدإحسان", "section_name": "2تر (هـ ك)"},
    {"fullname": "بن زينب محمد", "section_name": "2تر (هـ ك)"},
    {"fullname": "بن عائشة فاطمة الزهراء", "section_name": "2تر (هـ ك)"},
    {"fullname": "بن علو محمد رياض", "section_name": "2تر (هـ ك)"},
    {"fullname": "بوسيف منال سعدية", "section_name": "2تر (هـ ك)"},
    {"fullname": "حسين سارة", "section_name": "2تر (هـ ك)"},
    {"fullname": "زيري رحاب", "section_name": "2تر (هـ ك)"},
    {"fullname": "سعادي أنس عبد الرحمان", "section_name": "2تر (هـ ك)"},
    {"fullname": "سعادي ميساء", "section_name": "2تر (هـ ك)"},
    {"fullname": "طيفور عزيزة", "section_name": "2تر (هـ ك)"},
    {"fullname": "كرطالى هند", "section_name": "2تر (هـ ك)"},
    {"fullname": "بن سعادة ماريا", "section_name": "2تر (هـ م)"},
    {"fullname": "بن عائشة هاجر", "section_name": "2تر (هـ م)"},
    {"fullname": "بوزيدي نور الهدى ليليا", "section_name": "2تر (هـ م)"},
    {"fullname": "بوسيف عبد الله", "section_name": "2تر (هـ م)"},
    {"fullname": "تلى آية", "section_name": "2تر (هـ م)"},
    {"fullname": "خير الدين عبد الهادي يحيى", "section_name": "2تر (هـ م)"},
    {"fullname": "سى فضيل عبد النور", "section_name": "2تر (هـ م)"},
    {"fullname": "قرشى هديل", "section_name": "2تر (هـ م)"},
    {"fullname": "مداح بشرى", "section_name": "2تر (هـ م)"},
    {"fullname": "نوال ريهام سندس", "section_name": "2تر (هـ م)"},
    {"fullname": "بلهزيل نور الهدى", "section_name": "3أف1"},
    {"fullname": "بن زهرة آية", "section_name": "3أف1"},
    {"fullname": "بن عودة ياسين", "section_name": "3أف1"},
    {"fullname": "بن يعقوب مريم", "section_name": "3أف1"},
    {"fullname": "بن يوس عومرية", "section_name": "3أف1"},
    {"fullname": "بوخاري خضرة فدوى", "section_name": "3أف1"},
    {"fullname": "بوشنتوف أحمد إسلام", "section_name": "3أف1"},
    {"fullname": "بونعجة عائشة", "section_name": "3أف1"},
    {"fullname": "تركي كوثر", "section_name": "3أف1"},
    {"fullname": "تقار اخلاص", "section_name": "3أف1"},
    {"fullname": "جعلاب ليندة", "section_name": "3أف1"},
    {"fullname": "حروس آية", "section_name": "3أف1"},
    {"fullname": "رصانی غزلان حسنية", "section_name": "3أف1"},
    {"fullname": "رصانی خديجة وردية", "section_name": "3أف1"},
    {"fullname": "سلام عبدالقادر محمد امين", "section_name": "3أف1"},
    {"fullname": "سواحلية صالحية اسراء", "section_name": "3أف1"},
    {"fullname": "شحمی نادية", "section_name": "3أف1"},
    {"fullname": "شيخ عادل", "section_name": "3أف1"},
    {"fullname": "عبادية مروى", "section_name": "3أف1"},
    {"fullname": "عدة امينة", "section_name": "3أف1"},
    {"fullname": "عمري زهرة آية", "section_name": "3أف1"},
    {"fullname": "عيساوي يوسف", "section_name": "3أف1"},
    {"fullname": "فايدة دعاء خديجة", "section_name": "3أف1"},
    {"fullname": "فركان ياسمين", "section_name": "3أف1"},
    {"fullname": "قرنة صورية", "section_name": "3أف1"},
    {"fullname": "لحسن محمد امين", "section_name": "3أف1"},
    {"fullname": "مختاري فضيلة", "section_name": "3أف1"},
    {"fullname": "مداح روبة", "section_name": "3أف1"},
    {"fullname": "مزيان نور الإيمان", "section_name": "3أف1"},
    {"fullname": "مسعودي يوسف رزق الله", "section_name": "3أف1"},
    {"fullname": "العقون حسناء", "section_name": "3أف2"},
    {"fullname": "براهيمي بسملة", "section_name": "3أف2"},
    {"fullname": "بلعوني ابتهال وداد", "section_name": "3أف2"},
    {"fullname": "بن عمر صليحة", "section_name": "3أف2"},
    {"fullname": "بودية الياس", "section_name": "3أف2"},
    {"fullname": "بوعجامة دعاء", "section_name": "3أف2"},
    {"fullname": "بولنوار بلقيس", "section_name": "3أف2"},
    {"fullname": "جلابت عبد الحق", "section_name": "3أف2"},
    {"fullname": "حري وليد", "section_name": "3أف2"},
    {"fullname": "حسيني أية", "section_name": "3أف2"},
    {"fullname": "حكو دنيا انفال", "section_name": "3أف2"},
    {"fullname": "داني أسماء", "section_name": "3أف2"},
    {"fullname": "روام سريك عبد الله", "section_name": "3أف2"},
    {"fullname": "روام سريك ملاك", "section_name": "3أف2"},
    {"fullname": "زكار سموم سارة", "section_name": "3أف2"},
    {"fullname": "زيانی أيمن", "section_name": "3أف2"},
    {"fullname": "شحمی تسنيم", "section_name": "3أف2"},
    {"fullname": "شيخ محمد الامين", "section_name": "3أف2"},
    {"fullname": "عويسات يمنى", "section_name": "3أف2"},
    {"fullname": "غرزولي زوليخة", "section_name": "3أف2"},
    {"fullname": "فريح آية", "section_name": "3أف2"},
    {"fullname": "قاسم بن علي أمين", "section_name": "3أف2"},
    {"fullname": "قداري يمينة ام الدنيا وسام", "section_name": "3أف2"},
    {"fullname": "كشاي هبة اخلاص", "section_name": "3أف2"},
    {"fullname": "لحسن مليكة", "section_name": "3أف2"},
    {"fullname": "لزرق عبد القادر", "section_name": "3أف2"},
    {"fullname": "منصوري محمد يوسف نزيم", "section_name": "3أف2"},
    {"fullname": "موساوي ريحانة", "section_name": "3أف2"},
    {"fullname": "ناصر الشرقي دنيا", "section_name": "3أف2"},
    {"fullname": "ناصر الشرقي امين", "section_name": "3أف2"},
    {"fullname": "ناصر الشرقي فاطمة", "section_name": "3أف2"},
    {"fullname": "نوقعة لميس", "section_name": "3أف2"},
    {"fullname": "وعمارة ريان", "section_name": "3أف2"},
    {"fullname": "أحمد بلاحة زينب", "section_name": "3لغ (إسبانية)"},
    {"fullname": "الشرقى محمد عماد الدين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بختاوي ريمة", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بن مقداد سولاف", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بو عبد الله نسرين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بوجراف مروى", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بوخرطة حمزة", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بولحية مهدي", "section_name": "3لغ (إسبانية)"},
    {"fullname": "جفال مهدي سايح", "section_name": "3لغ (إسبانية)"},
    {"fullname": "حمو ابراهيم", "section_name": "3لغ (إسبانية)"},
    {"fullname": "دودوح مريم دعاء", "section_name": "3لغ (إسبانية)"},
    {"fullname": "رحماني اسلام", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عبد السلام سندس رتاج صورية", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عراب سعيد جوهرة ملاك", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عكرمى رميساء", "section_name": "3لغ (إسبانية)"},
    {"fullname": "علواش محمد الامين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عمایم حفصة", "section_name": "3لغ (إسبانية)"},
    {"fullname": "غريبي أروة سرين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "فايدة مارية", "section_name": "3لغ (إسبانية)"},
    {"fullname": "فريفر إبتسام", "section_name": "3لغ (إسبانية)"},
    {"fullname": "فيدوح دعاء", "section_name": "3لغ (إسبانية)"},
    {"fullname": "كبداني سندس", "section_name": "3لغ (إسبانية)"},
    {"fullname": "كتاب شيماء", "section_name": "3لغ (إسبانية)"},
    {"fullname": "مشري مختارية", "section_name": "3لغ (إسبانية)"},
    {"fullname": "مصابيح إسراء", "section_name": "3لغ (إسبانية)"},
    {"fullname": "مقدم بحوص فاروق", "section_name": "3لغ (إسبانية)"},
    {"fullname": "نباتى شرقي فريال", "section_name": "3لغ (إسبانية)"},
    {"fullname": "يوكلف يسرى", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بخدة هبة الرحمن", "section_name": "3لغ (ألمانية)"},
    {"fullname": "بن سالم دعاء", "section_name": "3لغ (ألمانية)"},
    {"fullname": "بوشنتوف نسرين بدرة", "section_name": "3لغ (ألمانية)"},
    {"fullname": "جعييد يمينة ملاك", "section_name": "3لغ (ألمانية)"},
    {"fullname": "راشم آدم", "section_name": "3لغ (ألمانية)"},
    {"fullname": "سريج سارة", "section_name": "3لغ (ألمانية)"},
    {"fullname": "صور رودينة جيداء", "section_name": "3لغ (ألمانية)"},
    {"fullname": "طويل مروى", "section_name": "3لغ (ألمانية)"},
    {"fullname": "عبو عبد المالك", "section_name": "3لغ (ألمانية)"},
    {"fullname": "بحيرة اسراء تسنيم", "section_name": "3ع ت1"},
    {"fullname": "بشحط يسرى", "section_name": "3ع ت1"},
    {"fullname": "بلزرق رميساء", "section_name": "3ع ت1"},
    {"fullname": "بلعيدي آية", "section_name": "3ع ت1"},
    {"fullname": "بن سعيد تسنيم", "section_name": "3ع ت1"},
    {"fullname": "بن سعيد يوسف", "section_name": "3ع ت1"},
    {"fullname": "بن عبد الرحمان آدم", "section_name": "3ع ت1"},
    {"fullname": "بوجمعة عبد القادر", "section_name": "3ع ت1"},
    {"fullname": "بوشارب إكرام", "section_name": "3ع ت1"},
    {"fullname": "بوليلة بشرى", "section_name": "3ع ت1"},
    {"fullname": "تابت خديجة", "section_name": "3ع ت1"},
    {"fullname": "خننو مروان", "section_name": "3ع ت1"},
    {"fullname": "دهاص بشرى رهام", "section_name": "3ع ت1"},
    {"fullname": "رصاني على أبو الأنوار", "section_name": "3ع ت1"},
    {"fullname": "رقاب رؤية", "section_name": "3ع ت1"},
    {"fullname": "ريزوقة اكرام", "section_name": "3ع ت1"},
    {"fullname": "زهراوي نسرين", "section_name": "3ع ت1"},
    {"fullname": "زهير علاء الدين", "section_name": "3ع ت1"},
    {"fullname": "زيان وهيبة", "section_name": "3ع ت1"},
    {"fullname": "سايح فاطمة الزهراء", "section_name": "3ع ت1"},
    {"fullname": "سحنون دعاء", "section_name": "3ع ت1"},
    {"fullname": "سمون سندس", "section_name": "3ع ت1"},
    {"fullname": "سي زياني عبد الخالق", "section_name": "3ع ت1"},
    {"fullname": "شريفي حليمة خيرة", "section_name": "3ع ت1"},
    {"fullname": "شمالي ندى", "section_name": "3ع ت1"},
    {"fullname": "صابر مليكة", "section_name": "3ع ت1"},
    {"fullname": "صابر سمية", "section_name": "3ع ت1"},
    {"fullname": "عالم جبار نورهان", "section_name": "3ع ت1"},
    {"fullname": "عبيد خالد", "section_name": "3ع ت1"},
    {"fullname": "عدوش فتحي", "section_name": "3ع ت1"},
    {"fullname": "غمري ملاك الرحمان", "section_name": "3ع ت1"},
    {"fullname": "فارس عائشة", "section_name": "3ع ت1"},
    {"fullname": "كاتب الهاشمي مروى", "section_name": "3ع ت1"},
    {"fullname": "كرسيفان مهجية", "section_name": "3ع ت1"},
    {"fullname": "كرطالي عبد الرحمان", "section_name": "3ع ت1"},
    {"fullname": "كساني فاطمة الزهراء", "section_name": "3ع ت1"},
    {"fullname": "لزاج فاطمة الزهراء", "section_name": "3ع ت1"},
    {"fullname": "لعور نادية أمينة", "section_name": "3ع ت1"},
    {"fullname": "مخيسي حليمة", "section_name": "3ع ت1"},
    {"fullname": "مرحوم عبدالرحمان", "section_name": "3ع ت1"},
    {"fullname": "مقدم إكرام", "section_name": "3ع ت1"},
    {"fullname": "نباتي الشرقي ايمان", "section_name": "3ع ت1"},
    {"fullname": "نباتي شرقي شيماء", "section_name": "3ع ت1"},
    {"fullname": "نومية سهام حميدة", "section_name": "3ع ت1"},
    {"fullname": "العربي اخلاص", "section_name": "3ع ت2"},
    {"fullname": "اليوبي إسراء إلهام", "section_name": "3ع ت2"},
    {"fullname": "بركاني عبد المالك", "section_name": "3ع ت2"},
    {"fullname": "بلحميدي خولة", "section_name": "3ع ت2"},
    {"fullname": "بلمختار سناء", "section_name": "3ع ت2"},
    {"fullname": "بلميلود أية", "section_name": "3ع ت2"},
    {"fullname": "بن طاطة أميرة", "section_name": "3ع ت2"},
    {"fullname": "بن فغول أية", "section_name": "3ع ت2"},
    {"fullname": "بن قانة سكينة", "section_name": "3ع ت2"},
    {"fullname": "بن ناجي سلسبيل", "section_name": "3ع ت2"},
    {"fullname": "بن يمينة لميس", "section_name": "3ع ت2"},
    {"fullname": "بوتشيش عبد الصمد", "section_name": "3ع ت2"},
    {"fullname": "بوتنزاز محمد يحي", "section_name": "3ع ت2"},
    {"fullname": "بوسيف شيماء", "section_name": "3ع ت2"},
    {"fullname": "تشمون محمد", "section_name": "3ع ت2"},
    {"fullname": "جبور نادية", "section_name": "3ع ت2"},
    {"fullname": "حاسي عبدالقادر صلاح الدين", "section_name": "3ع ت2"},
    {"fullname": "حتو مروى", "section_name": "3ع ت2"},
    {"fullname": "حمزة آية سيرين", "section_name": "3ع ت2"},
    {"fullname": "خلق الله حبيب", "section_name": "3ع ت2"},
    {"fullname": "داني معاد بن جبل", "section_name": "3ع ت2"},
    {"fullname": "درواش هبة الرحمان غزلان", "section_name": "3ع ت2"},
    {"fullname": "روام سريك هدى", "section_name": "3ع ت2"},
    {"fullname": "ريزوقة كوثر", "section_name": "3ع ت2"},
    {"fullname": "شباح وفاء", "section_name": "3ع ت2"},
    {"fullname": "شحمي حفصة", "section_name": "3ع ت2"},
    {"fullname": "شنوفي وداد وردة", "section_name": "3ع ت2"},
    {"fullname": "شوايل شايلة غالم ريان", "section_name": "3ع ت2"},
    {"fullname": "صويلح منال", "section_name": "3ع ت2"},
    {"fullname": "عبادية نجوى سارة", "section_name": "3ع ت2"},
    {"fullname": "غربي أيوب", "section_name": "3ع ت2"},
    {"fullname": "قطاف جهينة", "section_name": "3ع ت2"},
    {"fullname": "كاشة محمد", "section_name": "3ع ت2"},
    {"fullname": "كرطالي سناء", "section_name": "3ع ت2"},
    {"fullname": "كرطالي عبد الباسط براء", "section_name": "3ع ت2"},
    {"fullname": "كرطالي عبد القادر", "section_name": "3ع ت2"},
    {"fullname": "لزغم عبد النور", "section_name": "3ع ت2"},
    {"fullname": "لمقدم هبة الرحمان غزلان", "section_name": "3ع ت2"},
    {"fullname": "لمقدم اسراء", "section_name": "3ع ت2"},
    {"fullname": "مولوج دحو محمد", "section_name": "3ع ت2"},
    {"fullname": "ناصر شرقي ادم محمد", "section_name": "3ع ت2"},
    {"fullname": "ولد سليمان مروان", "section_name": "3ع ت2"},
    {"fullname": "يطو ياسين", "section_name": "3ع ت2"},
    {"fullname": "بطيشة محمد", "section_name": "3تق"},
    {"fullname": "بلعاطى مختارية", "section_name": "3تق"},
    {"fullname": "بلعيدي فاطمة", "section_name": "3تق"},
    {"fullname": "بلميلود دعاء", "section_name": "3تق"},
    {"fullname": "بن سعيد نور الهدى", "section_name": "3تق"},
    {"fullname": "بن يوب نجاة", "section_name": "3تق"},
    {"fullname": "بوعزة سندس", "section_name": "3تق"},
    {"fullname": "تامدة شيماء", "section_name": "3تق"},
    {"fullname": "تقار دعاء", "section_name": "3تق"},
    {"fullname": "تومى إسحاق مسعود أحمد", "section_name": "3تق"},
    {"fullname": "جعفري ملاك", "section_name": "3تق"},
    {"fullname": "جلول عبد الاله اسلام", "section_name": "3تق"},
    {"fullname": "حرطال عاشورية دعاء", "section_name": "3تق"},
    {"fullname": "رابح سمية", "section_name": "3تق"},
    {"fullname": "زيان يونس اسلام", "section_name": "3تق"},
    {"fullname": "زيري نسرين", "section_name": "3تق"},
    {"fullname": "سايح كوثر", "section_name": "3تق"},
    {"fullname": "سعود محمد علاء الدين", "section_name": "3تق"},
    {"fullname": "سى مرابط أمال", "section_name": "3تق"},
    {"fullname": "شكور يوسف", "section_name": "3تق"},
    {"fullname": "صرصار أحمد مجيب الرحمان", "section_name": "3تق"},
    {"fullname": "عبوشى لخضر", "section_name": "3تق"},
    {"fullname": "عتو ميلود ياسين", "section_name": "3تق"},
    {"fullname": "عرابة محمد ربيع", "section_name": "3تق"},
    {"fullname": "عطا الله مريم", "section_name": "3تق"},
    {"fullname": "فريح إسماعيل", "section_name": "3تق"},
    {"fullname": "قادري يوسف", "section_name": "3تق"},
    {"fullname": "قليل مروى", "section_name": "3تق"},
    {"fullname": "قليل حسام الدين", "section_name": "3تق"},
    {"fullname": "مصابيح ياسر", "section_name": "3تق"},
    {"fullname": "مقداد يوسف", "section_name": "3تق"},
    {"fullname": "ياحي لقمان", "section_name": "3تق"},
    {"fullname": "بلميلود منال", "section_name": "3ريا"},
    {"fullname": "بوسيف أكرم سليمان", "section_name": "3ريا"},
    {"fullname": "حجار عبد الرحمن", "section_name": "3ريا"},
    {"fullname": "خليفي أميمة", "section_name": "3ريا"},
    {"fullname": "سبع شهيناز", "section_name": "3ريا"},
    {"fullname": "شبوب نسرين", "section_name": "3ريا"},
    {"fullname": "شلقوم أشواق ليلى", "section_name": "3ريا"},
    {"fullname": "صابر أسامة", "section_name": "3ريا"},
    {"fullname": "عامر محلى عثمان", "section_name": "3ريا"},
    {"fullname": "غريسى هاجر منال", "section_name": "3ريا"},
    {"fullname": "قليل عصام الدين", "section_name": "3ريا"},
    {"fullname": "منقور منال", "section_name": "3ريا"},
    {"fullname": "بغداد تسنيم", "section_name": "3تر (هـ ك)"},
    {"fullname": "بلزرق إياد محمد أمين", "section_name": "3تر (هـ ك)"},
    {"fullname": "بلعوينات عبد الرزاق", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوجمعة محمد ياسين", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوزيدي محمد", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوشتة وهيبة", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوعقل عبد المجيد", "section_name": "3تر (هـ ك)"},
    {"fullname": "مصالح محمد صهيب", "section_name": "3تر (هـ ك)"},
    {"fullname": "نجادي امينة نور الهدى", "section_name": "3تر (هـ ك)"},
    {"fullname": "بلعباس لينة", "section_name": "3تر (هـ م)"},
    {"fullname": "بلميلود أمال", "section_name": "3تر (هـ م)"},
    {"fullname": "بلهاشمي مصطفى", "section_name": "3تر (هـ م)"},
    {"fullname": "بن زينب يوسف", "section_name": "3تر (هـ م)"},
    {"fullname": "بوترعة اية الرحمان", "section_name": "3تر (هـ م)"},
    {"fullname": "حسين عبد الغنى", "section_name": "3تر (هـ م)"},
    {"fullname": "خليفة هديل", "section_name": "3تر (هـ م)"},
    {"fullname": "دلهوم عبد الكريم", "section_name": "3تر (هـ م)"},
    {"fullname": "ديهاج محمد", "section_name": "3تر (هـ م)"},
    {"fullname": "ربوحى بن بربار حبيب", "section_name": "3تر (هـ م)"},
    {"fullname": "روام سريك شيماء", "section_name": "3تر (هـ م)"},
    {"fullname": "سيد احمد أية نهاد", "section_name": "3تر (هـ م)"},
    {"fullname": "صابر محمد آمين", "section_name": "3تر (هـ م)"},
    {"fullname": "غوال رميساء", "section_name": "3تر (هـ م)"},
    {"fullname": "لزرق هبة", "section_name": "3تر (هـ م)"},
]


def _add_column_if_missing(conn, table_name, col_name, col_def):
    conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN {col_name} {col_def}'))


def ensure_schema_columns():
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())

    with db.engine.begin() as conn:
        if "user" in tables:
            cols = {c["name"] for c in inspector.get_columns("user")}
            if "password_hash" not in cols:
                _add_column_if_missing(conn, "user", "password_hash", "VARCHAR(255)")
                if "password" in cols:
                    conn.execute(text('UPDATE "user" SET password_hash = password WHERE password_hash IS NULL'))
            if "sections_json" not in cols:
                _add_column_if_missing(conn, "user", "sections_json", "TEXT DEFAULT '[]'")
            if "weekly_hours" not in cols:
                _add_column_if_missing(conn, "user", "weekly_hours", "FLOAT")

        if "attendance" in tables:
            cols = {c["name"] for c in inspector.get_columns("attendance")}
            if "teacher_username" not in cols:
                _add_column_if_missing(conn, "attendance", "teacher_username", "VARCHAR(80)")
            if "hours" not in cols:
                _add_column_if_missing(conn, "attendance", "hours", "FLOAT DEFAULT 1.0")
            if "approval_status" not in cols:
                _add_column_if_missing(conn, "attendance", "approval_status", "VARCHAR(20) DEFAULT 'approved'")
            if "approved_by" not in cols:
                _add_column_if_missing(conn, "attendance", "approved_by", "VARCHAR(120)")

        if "lesson_log" in tables:
            cols = {c["name"] for c in inspector.get_columns("lesson_log")}
            if "teacher_username" not in cols:
                _add_column_if_missing(conn, "lesson_log", "teacher_username", "VARCHAR(80)")
            if "hours" not in cols:
                _add_column_if_missing(conn, "lesson_log", "hours", "FLOAT DEFAULT 1.0")
            if "approval_status" not in cols:
                _add_column_if_missing(conn, "lesson_log", "approval_status", "VARCHAR(20) DEFAULT 'pending'")
            if "approved_by" not in cols:
                _add_column_if_missing(conn, "lesson_log", "approved_by", "VARCHAR(120)")


def init_database():
    db.create_all()
    ensure_schema_columns()

    if not User.query.first():
        db.session.add_all([
            User(username="director", password="123456", role="director", fullname="السيد المدير"),
            User(username="deputy", password="123456", role="inspector_deputy", fullname="السيد الناظر"),
            User(username="counselor", password="123456", role="counselor", fullname="السيد مستشار التربية"),
            User(username="teacher", password="123456", role="teacher", fullname="الأستاذ فغلو عبد الله"),
        ])
        db.session.commit()

    if not Student.query.first():
        for s in DEFAULT_STUDENTS:
            db.session.add(
                Student(
                    fullname=s["fullname"],
                    section_name=s["section_name"],
                    teacher_username="system",
                )
            )
        db.session.commit()


with app.app_context():
    init_database()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("يرجى تسجيل الدخول أولاً.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


def redirect_by_role(role):
    if role == "teacher":
        return redirect(url_for("teacher_dashboard_view"))
    if role == "counselor":
        return redirect(url_for("counselor_dashboard_view"))
    if role == "director":
        return redirect(url_for("director_dashboard_view"))
    if role == "inspector_deputy":
        return redirect(url_for("deputy_dashboard_view"))
    return redirect(url_for("home"))


def format_hours(val):
    try:
        num = float(val or 0)
        return f"{num:g}"
    except (ValueError, TypeError):
        return "0"


def get_declared_teachers():
    teachers = User.query.filter_by(role="teacher").all()
    return [t for t in teachers if t.weekly_hours is not None and float(t.weekly_hours) > 0]


# ==============================================================================
# واجهة موحّدة (Bootstrap 5 RTL + خط Cairo + ترويسة المؤسسة)
# ==============================================================================

ALIGNED_SHELL = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }} - ثانوية الشهيد قوديد أحمد</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', sans-serif; background-color: #f4f7f6; }
        @media print { .no-print { display: none !important; } }
        .official-header {
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
            color: #ffffff;
            background: linear-gradient(135deg, #0d3b66, #1d6fa5);
            padding: 20px 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.06); }
    </style>
</head>
<body class="bg-light d-flex flex-column min-vh-100">
    <div class="official-header">
        <div style="font-size: 13px; opacity: 0.92;">الجمهورية الجزائرية الديمقراطية الشعبية</div>
        <div style="font-size: 13px; opacity: 0.92;" class="my-1">وزارة التربية الوطنية - مديرية التربية لولاية وهران</div>
        <div style="font-size: 19px; color: #ffca3a;" class="fw-bold mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي (منصة التسيير)</div>
    </div>

    <div class="container py-2 flex-grow-1">
        {% if db_mode_label %}
        <div class="alert {% if is_persistent_db %}alert-success{% else %}alert-warning{% endif %} py-2 small text-center fw-bold no-print">
            {{ db_mode_label }}
        </div>
        {% endif %}

        {% if session.get('username') %}
        <div class="card p-3 shadow-sm mb-4 bg-white no-print">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                <div class="small fw-bold text-secondary">
                    <i class="fas fa-user-check text-success me-1"></i>
                    {{ session.get('fullname') }}
                    <span class="badge bg-primary ms-1">{{ session.get('role') }}</span>
                </div>
                <div class="d-flex gap-2 flex-wrap">
                    {% if session.get('role') == 'teacher' %}
                        <a href="{{ url_for('teacher_dashboard_view', section=selected_section or '') }}" class="btn btn-outline-success btn-sm fw-bold">
                            <i class="fas fa-chalkboard me-1"></i> الأقسام والغيابات ودفتر النصوص
                        </a>
                    {% elif session.get('role') == 'counselor' %}
                        <a href="{{ url_for('counselor_dashboard_view') }}" class="btn btn-outline-warning text-dark btn-sm fw-bold">
                            <i class="fas fa-user-shield me-1"></i> مكتب الاستشارة والغيابات
                        </a>
                    {% elif session.get('role') == 'inspector_deputy' %}
                        <a href="{{ url_for('deputy_dashboard_view') }}" class="btn btn-outline-primary btn-sm fw-bold">
                            <i class="fas fa-book-open me-1"></i> التنسيق البيداغوجي
                        </a>
                    {% elif session.get('role') == 'director' %}
                        <a href="{{ url_for('director_dashboard_view') }}" class="btn btn-outline-primary btn-sm fw-bold">
                            <i class="fas fa-tachometer-alt me-1"></i> لوحة القيادة
                        </a>
                    {% endif %}
                    <a href="{{ url_for('logout') }}" class="btn btn-outline-danger btn-sm fw-bold">
                        <i class="fas fa-sign-out-alt me-1"></i> تسجيل الخروج
                    </a>
                </div>
            </div>
        </div>
        {% endif %}

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="mb-3 no-print">
              {% for category, message in messages %}
                <div class="alert {% if category == 'success' %}alert-success{% else %}alert-danger{% endif %} py-2 small fw-bold text-center mb-2">
                  {{ message }}
                </div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}

        {% if message %}
        <div class="alert alert-danger py-2 small fw-bold text-center no-print">{{ message }}</div>
        {% endif %}

        {{ body_content|safe }}
    </div>

    <footer class="text-center py-3 bg-dark text-white mt-auto no-print">
        <p class="mb-0 small">منصة تسيير المؤسسة &copy; 2026 - ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
        <p class="mb-0 fw-bold text-warning small mt-1">جميع الحقوق محفوظة &copy; للأستاذ فغلو عبد الله آل بن علي السنوسي</p>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

LOGIN_BODY = """
<div class="row justify-content-center mt-2">
    <div class="col-md-6 col-lg-5">
        <div class="card p-4 bg-white">
            <h5 class="fw-bold text-center text-primary mb-3"><i class="fas fa-sign-in-alt me-1"></i> تسجيل الدخول</h5>
            <form action="/login" method="POST">
                <div class="mb-3">
                    <label class="form-label small fw-bold">اسم المستخدم</label>
                    <input type="text" name="username" placeholder="مثال: teacher" required class="form-control form-control-sm">
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">كلمة المرور</label>
                    <input type="password" name="password" placeholder="••••••••" required class="form-control form-control-sm">
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">الصفة التربوية (الدور)</label>
                    <select name="role" required class="form-select form-select-sm">
                        <option value="" disabled selected>-- اختر صفتك في المؤسسة --</option>
                        <option value="director">المدير</option>
                        <option value="inspector_deputy">الناظر</option>
                        <option value="counselor">مستشار التربية</option>
                        <option value="teacher">أستاذ</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-success btn-sm w-100 fw-bold py-2">
                    دخول إلى لوحة التحكم
                </button>
            </form>
            <hr class="my-3">
            <div class="d-flex justify-content-between small fw-bold">
                <a href="{{ url_for('register_account') }}" class="text-primary text-decoration-none">تسجيل حساب جديد</a>
                <a href="{{ url_for('recover_account') }}" class="text-warning text-dark text-decoration-none">استعادة الحساب</a>
            </div>
        </div>
    </div>
</div>
"""

REGISTER_BODY = """
<div class="row justify-content-center mt-2">
    <div class="col-md-8 col-lg-7">
        <div class="card p-4 bg-white">
            <h5 class="fw-bold text-center text-primary mb-3"><i class="fas fa-user-plus me-1"></i> إنشاء حساب جديد</h5>
            <form method="POST" action="{{ url_for('register_account') }}">
                <div class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">الاسم الكامل</label>
                        <input type="text" name="fullname" required class="form-control form-control-sm">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">اسم المستخدم</label>
                        <input type="text" name="username" required class="form-control form-control-sm">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">الصفة التربوية (الدور)</label>
                        <select name="role" required class="form-select form-select-sm">
                            <option value="teacher">أستاذ</option>
                            <option value="counselor">مستشار التربية</option>
                            <option value="inspector_deputy">الناظر</option>
                            <option value="director">المدير</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label small fw-bold">الحجم الساعي الفعلي الأسبوعي (اختياري)</label>
                        <input type="number" step="0.5" min="1" max="50" name="weekly_hours" placeholder="مثال: 13" class="form-control form-control-sm">
                    </div>
                    <div class="col-12">
                        <label class="form-label small fw-bold">كلمة المرور</label>
                        <input type="password" name="password" required minlength="4" class="form-control form-control-sm">
                    </div>
                    <div class="col-12">
                        <label class="form-label small fw-bold">الأقسام المسندة (اختياري)</label>
                        <div class="row g-2 p-2 bg-light rounded border" style="max-height: 190px; overflow-y: auto;">
                            {% for section in sections %}
                            <div class="col-6 col-sm-4">
                                <label class="form-check bg-white p-1.5 px-2 rounded border small fw-bold mb-0">
                                    <input type="checkbox" name="sections" value="{{ section }}" class="form-check-input ms-1">
                                    <span class="me-3">{{ section }}</span>
                                </label>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    <div class="col-12">
                        <button type="submit" class="btn btn-primary btn-sm w-100 fw-bold py-2">تسجيل الحساب</button>
                    </div>
                </div>
            </form>
            <hr class="my-3">
            <div class="d-flex justify-content-between small fw-bold">
                <a href="{{ url_for('home') }}" class="text-primary text-decoration-none">العودة لتسجيل الدخول</a>
                <a href="{{ url_for('recover_account') }}" class="text-warning text-dark text-decoration-none">استعادة الحساب</a>
            </div>
        </div>
    </div>
</div>
"""

RECOVER_BODY = """
<div class="row justify-content-center mt-2">
    <div class="col-md-6 col-lg-5">
        <div class="card p-4 bg-white">
            <h5 class="fw-bold text-center text-primary mb-3"><i class="fas fa-key me-1"></i> استعادة الحساب وتعيين كلمة مرور جديدة</h5>
            <form method="POST" action="{{ url_for('recover_account') }}">
                <div class="mb-3">
                    <label class="form-label small fw-bold">اسم المستخدم المسجل</label>
                    <input type="text" name="username" required class="form-control form-control-sm">
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">الاسم الكامل المطابق للحساب</label>
                    <input type="text" name="fullname" required class="form-control form-control-sm">
                </div>
                <div class="mb-3">
                    <label class="form-label small fw-bold">كلمة المرور الجديدة</label>
                    <input type="password" name="new_password" required minlength="4" class="form-control form-control-sm">
                </div>
                <button type="submit" class="btn btn-success btn-sm w-100 fw-bold py-2">تحديث كلمة المرور</button>
            </form>
            <hr class="my-3">
            <div class="d-flex justify-content-between small fw-bold">
                <a href="{{ url_for('home') }}" class="text-primary text-decoration-none">العودة لتسجيل الدخول</a>
                <a href="{{ url_for('register_account') }}" class="text-secondary text-decoration-none">إنشاء حساب جديد</a>
            </div>
        </div>
    </div>
</div>
"""


def render_aligned(page_title, body_content, message=None, selected_section=""):
    return render_template_string(
        ALIGNED_SHELL,
        page_title=page_title,
        body_content=body_content,
        message=message,
        selected_section=selected_section,
        db_mode_label=DB_MODE_LABEL,
        is_persistent_db=IS_PERSISTENT_DB,
    )


@app.route("/")
def home():
    if "username" in session and "role" in session:
        return redirect_by_role(session.get("role"))
    return render_aligned("تسجيل الدخول", LOGIN_BODY)


@app.route("/login", methods=["POST"])
def login():
    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    role = (request.form.get("role") or "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password) or user.role != role:
        return render_aligned("تسجيل الدخول", LOGIN_BODY, message="بيانات الدخول غير صحيحة!")

    session["username"] = user.username
    session["fullname"] = user.fullname
    session["role"] = user.role
    return redirect_by_role(user.role)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"], endpoint="register_account")
def register_account():
    if request.method == "POST":
        fullname = (request.form.get("fullname") or "").strip()
        username = (request.form.get("username") or "").strip().lower()
        role = (request.form.get("role") or "teacher").strip()
        password = request.form.get("password") or ""
        weekly_hours_raw = (request.form.get("weekly_hours") or "").strip()
        selected_sections = [
            s for s in request.form.getlist("sections") if s in OFFICIAL_SECTIONS
        ]

        if not fullname or not username or not password:
            flash("يرجى ملء جميع الحقول المطلوبة.", "danger")
            return redirect(url_for("register_account"))

        if role not in ROLES:
            role = "teacher"

        if User.query.filter_by(username=username).first():
            flash("اسم المستخدم مستعمل مسبقاً، يرجى اختيار اسم آخر.", "danger")
            return redirect(url_for("register_account"))

        parsed_hours = None
        if role == "teacher" and weekly_hours_raw:
            try:
                val = float(weekly_hours_raw)
                if val > 0:
                    parsed_hours = val
            except ValueError:
                parsed_hours = None

        try:
            new_user = User(
                username=username,
                password=password,
                role=role,
                fullname=fullname,
                weekly_hours=parsed_hours,
            )
            new_user.sections = selected_sections
            db.session.add(new_user)

            for sec in selected_sections:
                if not TeacherSection.query.filter_by(
                    teacher_username=username, section_name=sec
                ).first():
                    db.session.add(
                        TeacherSection(teacher_username=username, section_name=sec)
                    )

            db.session.commit()
            flash(f"تم إنشاء الحساب ({username}) وحفظه بنجاح. يمكنك الآن تسجيل الدخول.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"تعذر حفظ الحساب في قاعدة البيانات: {e}", "danger")

        return redirect(url_for("register_account"))

    rendered = render_template_string(REGISTER_BODY, sections=OFFICIAL_SECTIONS)
    return render_aligned("تسجيل حساب جديد", rendered)


@app.route("/recover-account", methods=["GET", "POST"], endpoint="recover_account")
def recover_account():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        fullname = (request.form.get("fullname") or "").strip()
        new_password = request.form.get("new_password") or ""

        if not username or not fullname or not new_password:
            flash("يرجى إدخال اسم المستخدم، الاسم الكامل، وكلمة المرور الجديدة.", "danger")
            return redirect(url_for("recover_account"))

        user = User.query.filter_by(username=username, fullname=fullname).first()
        if not user:
            flash("لم يتم العثور على حساب مطابق لاسم المستخدم والاسم الكامل المدخلين.", "danger")
            return redirect(url_for("recover_account"))

        user.password = new_password
        db.session.commit()
        flash("تم تحديث كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول بكلمة المرور الجديدة.", "success")
        return redirect(url_for("recover_account"))

    return render_aligned("استعادة الحساب", RECOVER_BODY)


# ==============================================================================
# مسارات الأستاذ المساعدة (الساعات، الأقسام، التلاميذ، والغيابات)
# ==============================================================================

@app.route("/teacher/set-hours", methods=["POST"])
@login_required
def set_teacher_hours():
    if session.get("role") != "teacher":
        return redirect(url_for("home"))
    raw_hours = (request.form.get("weekly_hours") or "").strip()
    try:
        val = float(raw_hours)
        if val <= 0:
            raise ValueError("Hours must be positive")
        user = User.query.filter_by(username=session.get("username")).first()
        if user:
            user.weekly_hours = val
            db.session.commit()
            flash("تم حفظ الحجم الساعي بنجاح.", "success")
    except ValueError:
        flash("يرجى إدخال حجم ساعي صحيح أكبر من الصفر.", "danger")
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
        flash(f"تمت إضافة القسم ({sec}) إلى أقسامك.", "success")
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
        flash(f"تم حذف القسم ({sec_name}) من قائمتك.", "success")
    return redirect(url_for("teacher_dashboard_view"))


@app.route("/teacher/add-student", methods=["POST"])
@login_required
def add_student():
    if session.get("role") != "teacher":
        return redirect(url_for("home"))
    fullname = (request.form.get("student_fullname") or "").strip()
    section_name = (request.form.get("section_name") or "").strip()
    if fullname and section_name:
        db.session.add(
            Student(
                fullname=fullname,
                section_name=section_name,
                teacher_username=session.get("username"),
            )
        )
        db.session.commit()
        flash(f"تمت إضافة التلميذ ({fullname}) إلى قسم {section_name}.", "success")
    return redirect(url_for("teacher_dashboard_view", section=section_name))


# ==============================================================================
# مسارات الحارس العام المساعدة (اعتماد/رفض الحصص والغيابات)
# ==============================================================================

@app.route("/counselor/approve-lesson/<int:lid>", methods=["POST"])
@login_required
def approve_lesson(lid):
    if session.get("role") != "counselor":
        return redirect(url_for("home"))
    lesson = LessonLog.query.get(lid)
    if lesson:
        try:
            hrs = float(request.form.get("hours") or lesson.hours or 1.0)
            if hrs > 0:
                lesson.hours = hrs
        except ValueError:
            pass
        lesson.approval_status = "approved"
        lesson.approved_by = session.get("fullname")
        db.session.commit()
    return redirect(url_for("counselor_dashboard_view"))


@app.route("/counselor/reject-lesson/<int:lid>", methods=["POST"])
@login_required
def reject_lesson(lid):
    if session.get("role") != "counselor":
        return redirect(url_for("home"))
    lesson = LessonLog.query.get(lid)
    if lesson:
        lesson.approval_status = "rejected"
        lesson.approved_by = session.get("fullname")
        db.session.commit()
    return redirect(url_for("counselor_dashboard_view"))


@app.route("/counselor/approve-attendance/<int:aid>", methods=["POST"])
@login_required
def approve_attendance(aid):
    if session.get("role") != "counselor":
        return redirect(url_for("home"))
    att = Attendance.query.get(aid)
    if att:
        try:
            hrs = float(request.form.get("hours") or att.hours or 1.0)
            if hrs > 0:
                att.hours = hrs
        except ValueError:
            pass
        att.approval_status = "approved"
        att.approved_by = session.get("fullname")
        db.session.commit()
    return redirect(url_for("counselor_dashboard_view"))


@app.route("/counselor/reject-attendance/<int:aid>", methods=["POST"])
@login_required
def reject_attendance(aid):
    if session.get("role") != "counselor":
        return redirect(url_for("home"))
    att = Attendance.query.get(aid)
    if att:
        att.approval_status = "rejected"
        att.approved_by = session.get("fullname")
        db.session.commit()
    return redirect(url_for("counselor_dashboard_view"))


# ==============================================================================
# لوحة السيد الناظر
# ==============================================================================

@app.route("/deputy/dashboard-view")
@login_required
def deputy_dashboard_view():
    if session.get("role") != "inspector_deputy":
        return redirect(url_for("home"))
    approved_logs = LessonLog.query.filter_by(approval_status="approved").all()
    total_hrs = sum(float(l.hours or 0) for l in approved_logs)
    rows = "".join([
        (
            "<tr>"
            f"<td>{l.teacher_name}</td>"
            f"<td>{l.section_name}</td>"
            f"<td class='fw-bold'>{l.lesson_title}</td>"
            f"<td>{l.content}</td>"
            f"<td class='fw-bold text-primary'>{format_hours(l.hours)} سا</td>"
            f"<td>{l.date}</td>"
            "</tr>"
        )
        for l in approved_logs
    ]) or "<tr><td colspan='6' class='text-center py-4 text-muted'>لا توجد دروس معتمدة بعد.</td></tr>"

    body = f"""
    <div class="card p-4 bg-white mb-4 border-end border-4 border-primary">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>
                <h5 class="fw-bold text-primary mb-1"><i class="fas fa-book-open me-1"></i> التنسيق البيداغوجي - السيد الناظر</h5>
                <div class="small text-muted">ثانوية الشهيد قوديد أحمد | إجمالي الساعات المعتمدة: <b>{format_hours(total_hrs)} سا</b></div>
            </div>
        </div>
    </div>
    <div class="card p-4 bg-white">
        <h6 class="fw-bold text-dark mb-3">متابعة دفاتر النصوص المعتمدة</h6>
        <div class="table-responsive">
            <table class="table table-bordered table-striped text-center align-middle small">
                <thead class="table-primary">
                    <tr><th>الأستاذ</th><th>القسم</th><th>الدرس</th><th>المحتوى</th><th>الساعات</th><th>التاريخ</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </div>
    """
    return render_aligned("التنسيق البيداغوجي - الناظر", body)


# ==============================================================================
# التسيير المباشر: الأقسام والغيابات + دفتر النصوص + الاستشارة والمدير
# ==============================================================================

COUNSELOR_ROLES = ("counselor", "advisor", "guidance_counselor")
DIRECTOR_ROLES = ("director", "principal")
TEACHER_ROLES = ("teacher",)


def _mod_bind_view(rule, endpoint_name, view_func, **options):
    app.view_functions[endpoint_name] = view_func
    existing_rule = None
    for r in app.url_map.iter_rules():
        if r.rule == rule:
            existing_rule = r
            break

    if existing_rule is not None:
        old_ep = existing_rule.endpoint
        if old_ep != endpoint_name and old_ep in app.url_map._rules_by_endpoint:
            app.url_map._rules_by_endpoint[old_ep] = [
                r for r in app.url_map._rules_by_endpoint[old_ep] if r != existing_rule
            ]
        existing_rule.endpoint = endpoint_name
        ep_rules = app.url_map._rules_by_endpoint.setdefault(endpoint_name, [])
        if existing_rule not in ep_rules:
            ep_rules.append(existing_rule)
    else:
        options["endpoint"] = endpoint_name
        app.add_url_rule(rule, view_func=view_func, **options)

    return view_func


def _mod_ensure_report_table():
    with db.engine.begin() as conn:
        conn.execute(text("""
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


with app.app_context():
    _mod_ensure_report_table()


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
        flash(f"تم إرسال الحصة ({lesson.lesson_title}) إلى السيد المدير.", "success")

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

    return redirect(url_for("teacher_dashboard_view", section=selected_section, att_date=date))


_mod_bind_view("/teacher/mark-absence", "mark_absence", mod_mark_absence, methods=["POST"])


@login_required
def mod_teacher_dashboard_view():
    if session.get("role") not in TEACHER_ROLES:
        return redirect(url_for("home"))

    teacher_uname = session.get("username")
    teacher_user = User.query.filter_by(username=teacher_uname).first()
    today_date = datetime.now().strftime("%Y-%m-%d")
    att_date = (request.args.get("att_date") or today_date).strip()

    assigned_sections = TeacherSection.query.filter_by(teacher_username=teacher_uname).all()
    assigned_section_names = [ts.section_name for ts in assigned_sections]
    selected_section = request.args.get("section", assigned_section_names[0] if assigned_section_names else "")
    students_in_section = (
        Student.query.filter_by(section_name=selected_section).order_by(Student.fullname.asc()).all()
        if selected_section
        else []
    )

    absent_names_on_date = {
        a.student_name
        for a in Attendance.query.filter_by(section_name=selected_section, date=att_date).all()
    } if selected_section else set()

    students_sorted = sorted(
        students_in_section,
        key=lambda st: (0 if st.fullname in absent_names_on_date else 1, st.fullname),
    )

    section_tabs_html = "".join([
        f'<a href="{url_for("teacher_dashboard_view", section=sec, att_date=att_date)}" '
        f'class="btn btn-sm fw-bold {"btn-success" if sec == selected_section else "btn-outline-success"}">{sec}</a>'
        for sec in assigned_section_names
    ]) or '<span class="text-muted small">لا توجد أقسام مسندة بعد — أضف قسماً من القائمة أدناه.</span>'

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

    attendance_rows = "".join([
        f"""
        <tr class="{'table-danger fw-bold' if s.fullname in absent_names_on_date else ''}">
            <td>{idx}</td>
            <td class="text-start px-3">{s.fullname}</td>
            <td>{s.section_name}</td>
            <td>
                {'<span class="badge bg-danger">غائب (' + att_date + ')</span>' if s.fullname in absent_names_on_date else '<span class="badge bg-light text-dark border">حاضر</span>'}
            </td>
            <td>
                <form action="/teacher/mark-absence" method="POST" class="d-inline-flex align-items-center gap-1">
                    <input type="hidden" name="student_name" value="{s.fullname}">
                    <input type="hidden" name="section_name" value="{s.section_name}">
                    <input type="hidden" name="date" value="{att_date}">
                    <input type="hidden" name="selected_section" value="{selected_section}">
                    <input type="number" step="0.5" min="0.5" max="12" name="hours" value="1" class="form-control form-control-sm text-center fw-bold" style="width: 68px;">
                    <button type="submit" class="btn btn-outline-danger btn-sm fw-bold">تسجيل غياب</button>
                </form>
            </td>
        </tr>
        """
        for idx, s in enumerate(students_sorted, 1)
    ]) or "<tr><td colspan='5' class='text-center py-4 text-muted small'>اختر قسماً لعرض قائمة المناداة وتسجيل الغيابات.</td></tr>"

    my_sections_list_html = "".join([
        f"""
        <div class="d-flex justify-content-between align-items-center bg-light px-3 py-2 rounded border small">
            <span class="fw-bold text-primary">{ts.section_name}</span>
            <a href="/teacher/remove-section/{ts.id}" class="text-danger text-decoration-none fw-bold">حذف</a>
        </div>
        """
        for ts in assigned_sections
    ]) or "<p class='text-muted small mb-0'>لم تضف أي قسم بعد.</p>"

    lessons_rows = "".join([
        f"""
        <tr class='small'>
            <td class='fw-bold'>{l.section_name}</td>
            <td class='text-start'>{l.lesson_title}</td>
            <td class='fw-bold text-primary'>{format_hours(l.hours)} سا</td>
            <td>{l.date}</td>
            <td>
                {"<span class='badge bg-primary'>مُرسلة للمدير</span>" if l.approved_by == "مرسل للمدير" else "<span class='badge bg-secondary'>محفوظة عند الأستاذ</span>"}
            </td>
            <td>
                {"<span class='text-success fw-bold'>تم الإرسال</span>" if l.approved_by == "مرسل للمدير" else f"<form action='/teacher/send-lesson-to-director/{l.id}' method='POST' class='d-inline'><button type='submit' class='btn btn-primary btn-sm py-0 px-2 fw-bold'>إرسال للمدير</button></form>"}
            </td>
        </tr>
        """
        for l in reversed(my_lessons)
    ]) or "<tr><td colspan='6' class='text-center py-4 text-muted small'>لا توجد حصص مسجلة في دفتر النصوص بعد.</td></tr>"

    body = f"""
    <div class="card p-4 bg-white mb-4">
        <div class="row g-3 text-center">
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">حجمي الساعي الفعلي</div>
                    <div class="fw-bold fs-6 text-primary mt-1">{hours_display}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">ساعات دفتر النصوص</div>
                    <div class="fw-bold fs-6 text-success mt-1">{format_hours(total_lesson_hours)} سا</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">حصص مرسلة للمدير</div>
                    <div class="fw-bold fs-6 text-info mt-1">{sent_to_director_count}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">غيابات مسجلة</div>
                    <div class="fw-bold fs-6 text-danger mt-1">{len(my_absences)}</div>
                </div>
            </div>
        </div>

        <form action="/teacher/set-hours" method="POST" class="row g-2 align-items-center bg-light p-3 rounded border mt-3">
            <div class="col-md-7 small fw-bold text-secondary">
                تحديد/تعديل الحجم الساعي الفعلي الأسبوعي (يظهر للحارس العام والمدير بعد الحفظ):
            </div>
            <div class="col-md-3">
                <input type="number" step="0.5" min="1" max="50" name="weekly_hours" value="{hours_input_val}" placeholder="مثال: 13" required class="form-control form-control-sm text-center fw-bold">
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-primary btn-sm w-100 fw-bold">حفظ الحجم الساعي</button>
            </div>
        </form>
    </div>

    <div class="row g-4 mb-4">
        <div class="col-lg-4">
            <div class="card p-4 bg-white h-100">
                <h6 class="fw-bold text-success border-bottom pb-2 mb-3">
                    <i class="fas fa-chalkboard me-1"></i> إدارة الأقسام المسندة
                </h6>
                <form action="/teacher/add-section" method="POST" class="mb-3">
                    <div class="input-group input-group-sm">
                        <select name="section_name" required class="form-select">
                            <option value="" disabled selected>-- اختر قسماً لإضافته --</option>
                            {all_sections_options}
                        </select>
                        <button type="submit" class="btn btn-success fw-bold">إضافة قسم</button>
                    </div>
                </form>
                <div class="d-flex flex-column gap-2" style="max-height: 200px; overflow-y: auto;">
                    {my_sections_list_html}
                </div>

                {% if selected_section %}
                <hr class="my-3">
                <h6 class="fw-bold text-primary small mb-2">
                    <i class="fas fa-user-plus me-1"></i> إضافة تلميذ إلى القسم ({selected_section})
                </h6>
                <form action="/teacher/add-student" method="POST">
                    <input type="hidden" name="section_name" value="{selected_section}">
                    <div class="input-group input-group-sm">
                        <input type="text" name="student_fullname" class="form-control" placeholder="الاسم واللقب..." required>
                        <button type="submit" class="btn btn-primary fw-bold">إضافة</button>
                    </div>
                </form>
                {% endif %}
            </div>
        </div>

        <div class="col-lg-8">
            <div class="card p-4 bg-white">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 border-bottom pb-2 mb-3">
                    <h6 class="fw-bold text-success mb-0">
                        <i class="fas fa-clipboard-list me-1"></i> الأقسام وقائمة المناداة وتسجيل الغيابات
                    </h6>
                    <form method="GET" action="/teacher/dashboard-view" class="d-flex align-items-center gap-2">
                        <select name="section" onchange="this.form.submit()" class="form-select form-select-sm fw-bold text-primary" style="width: auto;">
                            <option value="" disabled selected>-- اختر القسم --</option>
                            {my_sections_options}
                        </select>
                        <input type="date" name="att_date" value="{att_date}" onchange="this.form.submit()" class="form-control form-control-sm" style="width: auto;">
                    </form>
                </div>

                <div class="d-flex flex-wrap gap-2 mb-3">
                    {section_tabs_html}
                </div>

                <div class="table-responsive" style="max-height: 360px; overflow-y: auto;">
                    <table class="table table-bordered table-sm text-center align-middle small">
                        <thead class="table-success">
                            <tr><th style="width: 45px;">#</th><th class="text-start px-3">التلميذ</th><th>القسم</th><th>الحالة</th><th>تسجيل الغياب</th></tr>
                        </thead>
                        <tbody>{attendance_rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="card p-4 bg-white mb-4">
        <h6 class="fw-bold text-primary mb-3">
            <i class="fas fa-book me-1"></i> دفتر النصوص (تسجيل مباشر عند الأستاذ — يُرسل للمدير عند الطلب)
        </h6>
        <form action="/teacher/submit-lesson" method="POST" class="row g-2 mb-3 bg-light p-3 rounded border">
            <div class="col-md-2">
                <select name="section_name" required class="form-select form-select-sm">
                    <option value="" disabled selected>-- القسم --</option>
                    {my_sections_options}
                </select>
            </div>
            <div class="col-md-3">
                <input type="text" name="lesson_title" placeholder="عنوان الدرس..." required class="form-control form-control-sm">
            </div>
            <div class="col-md-3">
                <input type="text" name="content" placeholder="الملخص..." required class="form-control form-control-sm">
            </div>
            <div class="col-md-2">
                <input type="number" step="0.5" min="0.5" max="12" name="hours" value="1" placeholder="الساعات" required class="form-control form-control-sm text-center fw-bold">
            </div>
            <div class="col-md-2 d-flex gap-1">
                <input type="date" name="date" value="{today_date}" required class="form-control form-control-sm">
                <button type="submit" class="btn btn-primary btn-sm fw-bold">تسجيل</button>
            </div>
        </form>

        <div class="table-responsive">
            <table class="table table-bordered table-striped text-center align-middle small">
                <thead class="table-light">
                    <tr><th>القسم</th><th class="text-start">الدرس</th><th>الساعات</th><th>التاريخ</th><th>الحالة</th><th>إرسال للمدير</th></tr>
                </thead>
                <tbody>{lessons_rows}</tbody>
            </table>
        </div>
    </div>
    """
    return render_aligned("لوحة الأستاذ - الأقسام والغيابات", body, selected_section=selected_section)


_mod_bind_view("/teacher/dashboard-view", "teacher_dashboard_view", mod_teacher_dashboard_view, methods=["GET"])


@login_required
def mod_submit_report_to_director():
    if session.get("role") not in COUNSELOR_ROLES:
        return redirect(url_for("home"))

    _mod_ensure_report_table()
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
        f'<span class="badge bg-warning text-dark p-2">{m.fullname}</span>'
        for m in stats["counselor_members"]
    ]) or '<span class="text-muted small">لا يوجد أعضاء استشارة مسجلون حالياً.</span>'

    declared_teachers_cards = "".join([
        f"""
        <div class="col-md-4">
            <div class="p-2.5 bg-light rounded border d-flex justify-content-between align-items-center small">
                <span class="fw-bold">{t.fullname}</span>
                <span class="badge bg-primary">{format_hours(t.weekly_hours)} سا/أسبوع</span>
            </div>
        </div>
        """
        for t in declared_teachers
    ]) or '<p class="text-muted small mb-0">لم يحدد أي أستاذ حجمه الساعي بعد.</p>'

    att_rows = "".join([
        f"""
        <tr class='small'>
            <td class='fw-bold'>{a.student_name}</td>
            <td><span class='badge bg-secondary'>{a.section_name}</span></td>
            <td>{a.teacher_name}</td>
            <td>{a.date}</td>
            <td class='fw-bold text-danger'>{format_hours(a.hours)} سا</td>
        </tr>
        """
        for a in reversed(attendances)
    ]) or "<tr><td colspan='5' class='text-center py-4 text-muted small'>لا توجد غيابات مسجلة بعد.</td></tr>"

    body = f"""
    <div class="card p-4 bg-white mb-4 border-end border-4 border-warning">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
            <div>
                <h5 class="fw-bold text-dark mb-1"><i class="fas fa-user-shield text-warning me-1"></i> مكتب الاستشارة التربوية - الحارس العام</h5>
                <div class="small text-muted">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</div>
            </div>
            <form action="/counselor/submit-report-to-director" method="POST" class="d-inline">
                <button type="submit" class="btn btn-success btn-sm fw-bold">
                    <i class="fas fa-paper-plane me-1"></i> رفع تقرير الغيابات للمدير
                </button>
            </form>
        </div>

        <div class="row g-3 text-center mb-3">
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">غيابات التلاميذ</div>
                    <div class="fw-bold fs-6 text-danger mt-1">{stats['student_absence_count']} / {format_hours(stats['student_absence_hours'])} سا</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">غيابات الأساتذة</div>
                    <div class="fw-bold fs-6 text-warning mt-1">{stats['teacher_absence_count']} / {format_hours(stats['teacher_absence_hours'])} سا</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">أعضاء الاستشارة</div>
                    <div class="fw-bold fs-6 text-dark mt-1">{stats['counselor_members_count']}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">أساتذة حددوا الحجم الساعي</div>
                    <div class="fw-bold fs-6 text-primary mt-1">{len(declared_teachers)}</div>
                </div>
            </div>
        </div>

        <div class="border-top pt-3 mb-3">
            <div class="small fw-bold text-secondary mb-2">أعضاء الاستشارة التربوية:</div>
            <div class="d-flex flex-wrap gap-2">{counselor_members_html}</div>
        </div>

        <div class="border-top pt-3">
            <div class="small fw-bold text-secondary mb-2">الحجم الساعي الفعلي للأساتذة:</div>
            <div class="row g-2">{declared_teachers_cards}</div>
        </div>
    </div>

    <div class="card p-4 bg-white">
        <h6 class="fw-bold text-dark mb-3"><i class="fas fa-table me-1"></i> سجل غيابات التلاميذ والأقسام الواردة تلقائياً</h6>
        <div class="table-responsive">
            <table class="table table-bordered table-striped text-center align-middle small">
                <thead class="table-success">
                    <tr><th>التلميذ</th><th>القسم</th><th>الأستاذ</th><th>التاريخ</th><th>الساعات</th></tr>
                </thead>
                <tbody>{att_rows}</tbody>
            </table>
        </div>
    </div>
    """
    return render_aligned("مكتب الاستشارة التربوية", body)


_mod_bind_view("/counselor/dashboard-view", "counselor_dashboard_view", mod_counselor_dashboard_view, methods=["GET"])


@login_required
def mod_director_dashboard_view():
    if session.get("role") not in DIRECTOR_ROLES:
        return redirect(url_for("home"))

    _mod_ensure_report_table()
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
        f"""
        <div class="col-md-4">
            <div class="p-2.5 bg-light rounded border d-flex justify-content-between align-items-center small">
                <span class="fw-bold">{t.fullname}</span>
                <span class="badge bg-primary">{format_hours(t.weekly_hours)} سا/أسبوع</span>
            </div>
        </div>
        """
        for t in declared_teachers
    ]) or '<p class="text-muted small mb-0">لا توجد حجوم ساعية محددة من طرف الأساتذة بعد.</p>'

    sent_lessons_rows = "".join([
        f"""
        <tr class='small'>
            <td>{l.teacher_name}</td>
            <td><span class='badge bg-secondary'>{l.section_name}</span></td>
            <td class='fw-bold text-start'>{l.lesson_title}</td>
            <td class='fw-bold text-primary'>{format_hours(l.hours)} سا</td>
            <td>{l.date}</td>
        </tr>
        """
        for l in reversed(sent_lessons)
    ]) or "<tr><td colspan='5' class='text-center py-4 text-muted small'>لم يرسل أي أستاذ حصصاً للمدير بعد.</td></tr>"

    reports_rows = "".join([
        f"""
        <tr class='small'>
            <td class='fw-bold'>{r[1] or '-'}</td>
            <td>{r[2] or '-'}</td>
            <td>{r[3]} ({format_hours(r[4])} سا)</td>
            <td>{r[5]} ({format_hours(r[6])} سا)</td>
            <td class='fw-bold'>{r[7]}</td>
        </tr>
        """
        for r in reports
    ]) or "<tr><td colspan='5' class='text-center py-4 text-muted small'>لا توجد تقارير مرفوعة من الحارس العام بعد.</td></tr>"

    body = f"""
    <div class="card p-4 bg-white mb-4 border-end border-4 border-primary">
        <h5 class="fw-bold text-primary mb-3"><i class="fas fa-tachometer-alt me-1"></i> لوحة القيادة الشاملة - السيد المدير</h5>
        <div class="row g-3 text-center mb-3">
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">غيابات التلاميذ</div>
                    <div class="fw-bold fs-6 text-danger mt-1">{latest_student_abs}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">غيابات الأساتذة</div>
                    <div class="fw-bold fs-6 text-warning mt-1">{latest_teacher_abs}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">أعضاء الاستشارة</div>
                    <div class="fw-bold fs-6 text-dark mt-1">{latest_counselor_cnt}</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="p-3 bg-light rounded border">
                    <div class="small text-muted fw-bold">أساتذة حددوا الحجم الساعي</div>
                    <div class="fw-bold fs-6 text-primary mt-1">{len(declared_teachers)}</div>
                </div>
            </div>
        </div>
        <div class="border-top pt-3">
            <div class="small fw-bold text-secondary mb-2">الحجم الساعي الفعلي للأساتذة:</div>
            <div class="row g-2">{declared_teachers_html}</div>
        </div>
    </div>

    <div class="card p-4 bg-white mb-4">
        <h6 class="fw-bold text-dark mb-3">تقارير الغيابات المرفوعة من الحارس العام</h6>
        <div class="table-responsive">
            <table class="table table-bordered table-striped text-center align-middle small">
                <thead class="table-primary">
                    <tr><th>الحارس العام</th><th>تاريخ الرفع</th><th>غيابات التلاميذ</th><th>غيابات الأساتذة</th><th>أعضاء الاستشارة</th></tr>
                </thead>
                <tbody>{reports_rows}</tbody>
            </table>
        </div>
    </div>

    <div class="card p-4 bg-white">
        <h6 class="fw-bold text-dark mb-3">حصص دفتر النصوص المرسلة للمدير</h6>
        <div class="table-responsive">
            <table class="table table-bordered table-striped text-center align-middle small">
                <thead class="table-success">
                    <tr><th>الأستاذ</th><th>القسم</th><th class="text-start">الدرس</th><th>الساعات</th><th>التاريخ</th></tr>
                </thead>
                <tbody>{sent_lessons_rows}</tbody>
            </table>
        </div>
    </div>
    """
    return render_aligned("لوحة القيادة - المدير", body)


_mod_bind_view("/director/dashboard-view", "director_dashboard_view", mod_director_dashboard_view, methods=["GET"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
