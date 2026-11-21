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

# الأقسام الرسمية والتخصصات المعتمدة
OFFICIAL_SECTIONS = [
    "1أ1", "1أ2", "1أ3", "1ع1", "1ع2", "1ع3", "1ع4", "1ع5", "1ع6",
    "2أف1", "2أف2", "2لغ", "2ع ت1", "2ع ت2", 
    "2تق", "2ريا", "2تر (هـ ط)", "2تر (هـ ك)", "2تر (هـ م)",
    "3أف1", "3أف2", "3لغ (إسبانية)", "3لغ (ألمانية)", "3ع ت1", "3ع ت2", 
    "3تق", "3ريا", "3تر (هـ ك)", "3تر (هـ م)"
]

# قائمة التلاميذ الشاملة والمصنفة حسب الأقسام والتخصصات
DEFAULT_STUDENTS = [
    # --- قسم 1أ1 ---
    {"fullname": "المراربي أمينة", "section_name": "1أ1"}, {"fullname": "بدة ملاك", "section_name": "1أ1"},
    {"fullname": "بران محمد", "section_name": "1أ1"}, {"fullname": "بلعباس بن قرعة كوثر", "section_name": "1أ1"},
    {"fullname": "بلميلود أدم", "section_name": "1أ1"}, {"fullname": "بلميلود هاجر", "section_name": "1أ1"},
    {"fullname": "بلهادف بدرة سلسبيل", "section_name": "1أ1"}, {"fullname": "بلولو سندس", "section_name": "1أ1"},
    {"fullname": "بن حمادي إسلام", "section_name": "1أ1"}, {"fullname": "بن حمدود سندس", "section_name": "1أ1"},
    {"fullname": "بن حصالي ألاء", "section_name": "1أ1"}, {"fullname": "بن دوخة عبد الرحمان", "section_name": "1أ1"},
    {"fullname": "بن سعيد مروى", "section_name": "1أ1"}, {"fullname": "بن عبد المومن آية", "section_name": "1أ1"},
    {"fullname": "بن علال هبة خيرة", "section_name": "1أ1"}, {"fullname": "بن ناصر رتاج", "section_name": "1أ1"},
    {"fullname": "بنوار مريم", "section_name": "1أ1"}, {"fullname": "بوخرص محمد صهيب", "section_name": "1أ1"},
    {"fullname": "بوري توفيق", "section_name": "1أ1"}, {"fullname": "بورياح ايوب", "section_name": "1أ1"},
    {"fullname": "بوزيان محمد الأمين", "section_name": "1أ1"}, {"fullname": "حمودي فاطمة", "section_name": "1أ1"},
    {"fullname": "داودي فاطمة الزهراء", "section_name": "1أ1"}, {"fullname": "دحماني أمين", "section_name": "1أ1"},
    {"fullname": "دراديز اسلام الدين", "section_name": "1أ1"}, {"fullname": "رابح نوال", "section_name": "1أ1"},
    {"fullname": "رفاسي ياسمين", "section_name": "1أ1"}, {"fullname": "سريك رزان عائشة", "section_name": "1أ1"},
    {"fullname": "سعدو اسراء", "section_name": "1أ1"}, {"fullname": "شتوكي آية", "section_name": "1أ1"},
    {"fullname": "شفار حبيب", "section_name": "1أ1"}, {"fullname": "شفار بشرى", "section_name": "1أ1"},
    {"fullname": "عايد وصال نور الهدى", "section_name": "1أ1"}, {"fullname": "عبيد نور الدين", "section_name": "1أ1"},
    {"fullname": "كاتب الهاشمي هاجر", "section_name": "1أ1"}, {"fullname": "كرتالی محمد ايهاب", "section_name": "1أ1"},
    {"fullname": "كيري أية اناس", "section_name": "1أ1"}, {"fullname": "محبوب فراح", "section_name": "1أ1"},
    {"fullname": "مرين رؤية", "section_name": "1أ1"}, {"fullname": "مرين عمر", "section_name": "1أ1"},
    {"fullname": "مكاب ياسين محمد سالم", "section_name": "1أ1"}, {"fullname": "مناع حمزة", "section_name": "1أ1"},
    {"fullname": "مهدي أسماء", "section_name": "1أ1"}, {"fullname": "ناصر شرقي حسن حسين", "section_name": "1أ1"},

    # --- قسم 1أ2 ---
    {"fullname": "بخدة إسراء", "section_name": "1أ2"}, {"fullname": "برحمون سناء", "section_name": "1أ2"},
    {"fullname": "بلغربي إسراء", "section_name": "1أ2"}, {"fullname": "بن دادة ملاك", "section_name": "1أ2"},
    {"fullname": "بن عطية فاطمة", "section_name": "1أ2"}, {"fullname": "بن علال عبد الله اسلام", "section_name": "1أ2"},
    {"fullname": "بن عودة شحط شهيناز", "section_name": "1أ2"}, {"fullname": "بنافلة فاروق", "section_name": "1أ2"},
    {"fullname": "بوخلوة محمد عز الدين", "section_name": "1أ2"}, {"fullname": "بوزار أمينة", "section_name": "1أ2"},
    {"fullname": "بوزيان آية ملاك", "section_name": "1أ2"}, {"fullname": "بوعلام مليكة", "section_name": "1أ2"},
    {"fullname": "بوقفة عبد الكريم", "section_name": "1أ2"}, {"fullname": "بوليلة عثمان", "section_name": "1أ2"},
    {"fullname": "ثابت حفصة", "section_name": "1أ2"}, {"fullname": "ثابت سندس", "section_name": "1أ2"},
    {"fullname": "جيد هديل", "section_name": "1أ2"}, {"fullname": "حداد زهرة", "section_name": "1أ2"},
    {"fullname": "حنيفي أمال", "section_name": "1أ2"}, {"fullname": "روام سريك عائشة", "section_name": "1أ2"},
    {"fullname": "روماري محمد عادل", "section_name": "1أ2"}, {"fullname": "زوج ملاك", "section_name": "1أ2"},
    {"fullname": "زوانب هواري", "section_name": "1أ2"}, {"fullname": "سجلوماسى هند", "section_name": "1أ2"},
    {"fullname": "شايب الدور آية الرحمان", "section_name": "1أ2"}, {"fullname": "شريفي فريال", "section_name": "1أ2"},
    {"fullname": "صابر معزوز بتينة", "section_name": "1أ2"}, {"fullname": "عمارة فراح", "section_name": "1أ2"},
    {"fullname": "عواد إيمان", "section_name": "1أ2"}, {"fullname": "عياد إكرام", "section_name": "1أ2"},
    {"fullname": "فايدة ريهام أميمة", "section_name": "1أ2"}, {"fullname": "فرحاوي فراح غزلان", "section_name": "1أ2"},
    {"fullname": "قبايلى محمد مروان", "section_name": "1أ2"}, {"fullname": "قطاف رحيل", "section_name": "1أ2"},
    {"fullname": "قورين اسيا", "section_name": "1أ2"}, {"fullname": "كرتالي لجين", "section_name": "1أ2"},
    {"fullname": "مرين عبد الباسط عبد الصمد", "section_name": "1أ2"}, {"fullname": "مرين يمينة", "section_name": "1أ2"},
    {"fullname": "موزاع دلين", "section_name": "1أ2"}, {"fullname": "ناصر الشرقي مصطفى", "section_name": "1أ2"},
    {"fullname": "ناصر شرقي ميلود", "section_name": "1أ2"}, {"fullname": "نباتي شرقي شيماء", "section_name": "1أ2"},
    {"fullname": "وانس مشكور سرين", "section_name": "1أ2"},

    # --- قسم 1أ3 ---
    {"fullname": "بداوي أسيا", "section_name": "1أ3"}, {"fullname": "بركليت رحيل", "section_name": "1أ3"},
    {"fullname": "بلبية أمال", "section_name": "1أ3"}, {"fullname": "بلعابد بشرى", "section_name": "1أ3"},
    {"fullname": "بلعربي كوثر", "section_name": "1أ3"}, {"fullname": "بلكحلة أحمد", "section_name": "1أ3"},
    {"fullname": "بلميلود دعاء", "section_name": "1أ3"}, {"fullname": "بن عطية فدوى نضال", "section_name": "1أ3"},
    {"fullname": "بنوار ياسين عبد الرحمان", "section_name": "1أ3"}, {"fullname": "بوخلفة احلام", "section_name": "1أ3"},
    {"fullname": "بورشاش عبد الحكيم", "section_name": "1أ3"}, {"fullname": "بوطيبة معمر عبد الغنى", "section_name": "1أ3"},
    {"fullname": "تقية محمد الأمين", "section_name": "1أ3"}, {"fullname": "تويلي صفاء", "section_name": "1أ3"},
    {"fullname": "جبلى نريمان", "section_name": "1أ3"}, {"fullname": "جديد خيرة", "section_name": "1أ3"},
    {"fullname": "حمادي دنيا", "section_name": "1أ3"}, {"fullname": "رزيق يوسف", "section_name": "1أ3"},
    {"fullname": "رفاس هواري إسحاق", "section_name": "1أ3"}, {"fullname": "سافر محمد", "section_name": "1أ3"},
    {"fullname": "شلابي محمد ياسر", "section_name": "1أ3"}, {"fullname": "صالح هلال محمد أمين", "section_name": "1أ3"},
    {"fullname": "طويل رقية ملاك", "section_name": "1أ3"}, {"fullname": "عبيد شيراز نسرين", "section_name": "1أ3"},
    {"fullname": "عتو نور الدين عبد الصمد", "section_name": "1أ3"}, {"fullname": "عزة فريال", "section_name": "1أ3"},
    {"fullname": "علاوي فريال عائشة", "section_name": "1أ3"}, {"fullname": "عمارة دعاء", "section_name": "1أ3"},
    {"fullname": "عيسى جميلة", "section_name": "1أ3"}, {"fullname": "غراس بهجة ايناس", "section_name": "1أ3"},
    {"fullname": "قرميط رتاج سهيلة", "section_name": "1أ3"}, {"fullname": "قنيش فاطمة", "section_name": "1أ3"},
    {"fullname": "قنيش أيوب", "section_name": "1أ3"}, {"fullname": "كروش أسيا", "section_name": "1أ3"},
    {"fullname": "كيري محمد انس", "section_name": "1أ3"}, {"fullname": "كيلالي ملحة", "section_name": "1أ3"},
    {"fullname": "مبارك إخلاص", "section_name": "1أ3"}, {"fullname": "مختاري اميمة", "section_name": "1أ3"},
    {"fullname": "مزيود انس", "section_name": "1أ3"}, {"fullname": "معيطى رتاج", "section_name": "1أ3"},
    {"fullname": "مملوك ربيعة", "section_name": "1أ3"}, {"fullname": "مواز دعاء", "section_name": "1أ3"},
    {"fullname": "نباتى شرقى شيراز", "section_name": "1أ3"},

    # --- قسم 1ع1 ---
    {"fullname": "ابراهيم مفلاح اسلام", "section_name": "1ع1"}, {"fullname": "اليوبي هبة الرحمان", "section_name": "1ع1"},
    {"fullname": "بحوصي محمد العدنان", "section_name": "1ع1"}, {"fullname": "برفاس وصال", "section_name": "1ع1"},
    {"fullname": "بلحبيب بشري", "section_name": "1ع1"}, {"fullname": "بلعباس مصطفى عبد الرحمان", "section_name": "1ع1"},
    {"fullname": "بلعباس اميرة", "section_name": "1ع1"}, {"fullname": "بلقاسم رفيدة", "section_name": "1ع1"},
    {"fullname": "بن زيادي عماد الدين", "section_name": "1ع1"}, {"fullname": "بن عائشة احمد حسام", "section_name": "1ع1"},
    {"fullname": "بن قانة نورهان", "section_name": "1ع1"}, {"fullname": "بنوار اسامة", "section_name": "1ع1"},
    {"fullname": "بوخلوة عيسى", "section_name": "1ع1"}, {"fullname": "بورداش عبد الرحمان", "section_name": "1ع1"},
    {"fullname": "بوزرادة جميلة", "section_name": "1ع1"}, {"fullname": "بوسيف شيخ", "section_name": "1ع1"},
    {"fullname": "بولحليب عبد الحق", "section_name": "1ع1"}, {"fullname": "حمزة شهد انصاف", "section_name": "1ع1"},
    {"fullname": "خنو ملاك", "section_name": "1ع1"}, {"fullname": "خيشان ابراهيم", "section_name": "1ع1"},
    {"fullname": "رفاس نور الهدى خيرة", "section_name": "1ع1"}, {"fullname": "رقيق يسعد بشرى", "section_name": "1ع1"},
    {"fullname": "زياني سولاف", "section_name": "1ع1"}, {"fullname": "شارف إسماعيل", "section_name": "1ع1"},
    {"fullname": "شحمي رتاج", "section_name": "1ع1"}, {"fullname": "غمري أماني", "section_name": "1ع1"},
    {"fullname": "قيروان دعاء", "section_name": "1ع1"}, {"fullname": "كروم محمد علال", "section_name": "1ع1"},
    {"fullname": "مصالح انس", "section_name": "1ع1"}, {"fullname": "مغربي نور الهدى", "section_name": "1ع1"},
    {"fullname": "نباتى شرقى ملاك", "section_name": "1ع1"}, {"fullname": "هبري إسمهان رميسة", "section_name": "1ع1"},

    # --- قسم 1ع2 ---
    {"fullname": "اوجيت ملاك", "section_name": "1ع2"}, {"fullname": "أوراغى عبد الجليل", "section_name": "1ع2"},
    {"fullname": "بلهاشمي كوثر", "section_name": "1ع2"}, {"fullname": "بن دحو آية", "section_name": "1ع2"},
    {"fullname": "بن عبد الله عبد المالك خالد", "section_name": "1ع2"}, {"fullname": "بن عيشوش ياسين", "section_name": "1ع2"},
    {"fullname": "بن يوسف قادة", "section_name": "1ع2"}, {"fullname": "بودومي الحسن", "section_name": "1ع2"},
    {"fullname": "بودية سارة", "section_name": "1ع2"}, {"fullname": "بوسيف عبد الرحمن سعيد", "section_name": "1ع2"},
    {"fullname": "خنو رجاء", "section_name": "1ع2"}, {"fullname": "رفاسي مريم", "section_name": "1ع2"},
    {"fullname": "روام سريك يوسف عبد المالك", "section_name": "1ع2"}, {"fullname": "روام سريك أميمة", "section_name": "1ع2"},
    {"fullname": "زوبة الهواري", "section_name": "1ع2"}, {"fullname": "زوبير علي", "section_name": "1ع2"},
    {"fullname": "سعادي عمر الفاروق", "section_name": "1ع2"}, {"fullname": "سمون دعاء", "section_name": "1ع2"},
    {"fullname": "شاقور هنادي", "section_name": "1ع2"}, {"fullname": "طاهري نور الدين", "section_name": "1ع2"},
    {"fullname": "عبيد ريان", "section_name": "1ع2"}, {"fullname": "فرطاس سعاد", "section_name": "1ع2"},
    {"fullname": "فرعون ريان رياض", "section_name": "1ع2"}, {"fullname": "فریوی حنان عائشة", "section_name": "1ع2"},
    {"fullname": "قادري عماد", "section_name": "1ع2"}, {"fullname": "كرتالي هبة جنان", "section_name": "1ع2"},
    {"fullname": "لكحل خيرالدين", "section_name": "1ع2"}, {"fullname": "مرحوم ياسين", "section_name": "1ع2"},
    {"fullname": "مصابيح ادم علی", "section_name": "1ع2"}, {"fullname": "معطى الله شمس الضحى", "section_name": "1ع2"},
    {"fullname": "نصر الدين منال", "section_name": "1ع2"}, {"fullname": "هادف حفصة", "section_name": "1ع2"},
    {"fullname": "يرو رانيا", "section_name": "1ع2"},

    # --- قسم 1ع3 ---
    {"fullname": "الشرقى ذكرى فاطمة", "section_name": "1ع3"}, {"fullname": "بعلة ألاء سندس", "section_name": "1ع3"},
    {"fullname": "بقدور عبد الكافي مروان", "section_name": "1ع3"}, {"fullname": "بلعزيز عبد الرحمان", "section_name": "1ع3"},
    {"fullname": "بلميلود أمال فاطمة", "section_name": "1ع3"}, {"fullname": "بلهاشمى رضوان", "section_name": "1ع3"},
    {"fullname": "بن رابح محمد", "section_name": "1ع3"}, {"fullname": "بن زايد هديل", "section_name": "1ع3"},
    {"fullname": "بن عودة شحط يسرى", "section_name": "1ع3"}, {"fullname": "بن مسعود أكرم", "section_name": "1ع3"},
    {"fullname": "بنوار بشرى", "section_name": "1ع3"}, {"fullname": "بوخرص أسماء", "section_name": "1ع3"},
    {"fullname": "بوعرارة هديل", "section_name": "1ع3"}, {"fullname": "بوعقل مريم رميسة", "section_name": "1ع3"},
    {"fullname": "توبة أمينة", "section_name": "1ع3"}, {"fullname": "جديد محمد أمين", "section_name": "1ع3"},
    {"fullname": "جلواط احمد ياسين", "section_name": "1ع3"}, {"fullname": "حساني عبد الرحمان", "section_name": "1ع3"},
    {"fullname": "ربوحى بن بربار محمد الامين", "section_name": "1ع3"}, {"fullname": "رصانی جميلة", "section_name": "1ع3"},
    {"fullname": "رقيق يسعد دينا أسيل", "section_name": "1ع3"}, {"fullname": "زياني مروان", "section_name": "1ع3"},
    {"fullname": "سرحان ملاك رهف", "section_name": "1ع3"}, {"fullname": "صرصار أية", "section_name": "1ع3"},
    {"fullname": "عراب سعيد مليسا", "section_name": "1ع3"}, {"fullname": "عروسی رحيل", "section_name": "1ع3"},
    {"fullname": "عمارة عمارة فارس", "section_name": "1ع3"}, {"fullname": "عمارة محمد أمين", "section_name": "1ع3"},
    {"fullname": "لقام عائشة", "section_name": "1ع3"}, {"fullname": "لوشنی خديجة", "section_name": "1ع3"},
    {"fullname": "مشري بوبكر", "section_name": "1ع3"}, {"fullname": "مصابيح فاطمة الزهراء", "section_name": "1ع3"},
    {"fullname": "مغربي عائشة", "section_name": "1ع3"}, {"fullname": "موفق ملاك", "section_name": "1ع3"},
    {"fullname": "ناجي كوثر اسراء", "section_name": "1ع3"}, {"fullname": "نباتى شرقى حاجة فاطمة", "section_name": "1ع3"},

    # --- قسم 1ع4 ---
    {"fullname": "احمد بلاحة احمد", "section_name": "1ع4"}, {"fullname": "اوشعبان ملاك", "section_name": "1ع4"},
    {"fullname": "برداية صافية", "section_name": "1ع4"}, {"fullname": "بشير هناء", "section_name": "1ع4"},
    {"fullname": "بكييري عبد القادر", "section_name": "1ع4"}, {"fullname": "بلعباس أيوب", "section_name": "1ع4"},
    {"fullname": "بلعتروس ملاك", "section_name": "1ع4"}, {"fullname": "بلعقون عمر", "section_name": "1ع4"},
    {"fullname": "بلعيدي خديجة", "section_name": "1ع4"}, {"fullname": "بلميلود زينب", "section_name": "1ع4"},
    {"fullname": "بن صاولة محمد طه ياسين", "section_name": "1ع4"}, {"fullname": "بوخلوة يحي", "section_name": "1ع4"},
    {"fullname": "بونعجة مريم", "section_name": "1ع4"}, {"fullname": "حري ألاء شهد", "section_name": "1ع4"},
    {"fullname": "حمانی مروان", "section_name": "1ع4"}, {"fullname": "حميداش نشوى نورة", "section_name": "1ع4"},
    {"fullname": "حنيفي مروان محمد امين", "section_name": "1ع4"}, {"fullname": "دويلة ابراهيم خليل عمر", "section_name": "1ع4"},
    {"fullname": "سبع عبد الحق لزرق", "section_name": "1ع4"}, {"fullname": "سحنون مريم الاء", "section_name": "1ع4"},
    {"fullname": "سنينة زكرياء", "section_name": "1ع4"}, {"fullname": "سيد احمد سولاف", "section_name": "1ع4"},
    {"fullname": "شريف محمد عبد الجليل", "section_name": "1ع4"}, {"fullname": "شلابي آية", "section_name": "1ع4"},
    {"fullname": "صابر أحلام", "section_name": "1ع4"}, {"fullname": "عاشور آية", "section_name": "1ع4"},
    {"fullname": "عالم جبار صفية", "section_name": "1ع4"}, {"fullname": "عشوري دعاء شيماء", "section_name": "1ع4"},
    {"fullname": "عماري جلال الدين", "section_name": "1ع4"}, {"fullname": "غفاري أنس عبد الرحمان", "section_name": "1ع4"},
    {"fullname": "فلاح ياسر", "section_name": "1ع4"}, {"fullname": "فلاح أيمن", "section_name": "1ع4"},
    {"fullname": "فيدوح سارة", "section_name": "1ع4"}, {"fullname": "قادة بن عثمان هبة الرحمان", "section_name": "1ع4"},
    {"fullname": "لژغم محمد أمين", "section_name": "1ع4"}, {"fullname": "ميمون عامر", "section_name": "1ع4"},
    {"fullname": "يحي صفوان", "section_name": "1ع4"},

    # --- قسم 1ع5 ---
    {"fullname": "بلحبيب نسرين", "section_name": "1ع5"}, {"fullname": "بلخير إلياس", "section_name": "1ع5"},
    {"fullname": "بلعباس فاطمة الزهراء", "section_name": "1ع5"}, {"fullname": "بلقاضى عبد النور", "section_name": "1ع5"},
    {"fullname": "بلهوان محمد عبد الغانی", "section_name": "1ع5"}, {"fullname": "بن طالب شيماء", "section_name": "1ع5"},
    {"fullname": "بن عالية عربية ريان", "section_name": "1ع5"}, {"fullname": "بن عثمان سيف الدين", "section_name": "1ع5"},
    {"fullname": "بن كواشى آدم", "section_name": "1ع5"}, {"fullname": "بن يعقوب بدرة", "section_name": "1ع5"},
    {"fullname": "بوعلام عثمان", "section_name": "1ع5"}, {"fullname": "جپور خلود", "section_name": "1ع5"},
    {"fullname": "جلواط أنفال رحيل", "section_name": "1ع5"}, {"fullname": "رجوح شمس الدين ريان", "section_name": "1ع5"},
    {"fullname": "رجوح سلينا", "section_name": "1ع5"}, {"fullname": "رَقيبة ياسمين", "section_name": "1ع5"},
    {"fullname": "روان سريك هواري", "section_name": "1ع5"}, {"fullname": "ريزوقة الياس", "section_name": "1ع5"},
    {"fullname": "زقاق اللاء", "section_name": "1ع5"}, {"fullname": "سى سهلى عبد الرحمان", "section_name": "1ع5"},
    {"fullname": "شحمی مفيد بدر الدين", "section_name": "1ع5"}, {"fullname": "شيخ غالم إبتسام", "section_name": "1ع5"},
    {"fullname": "صالحي تقوى الإيمان", "section_name": "1ع5"}, {"fullname": "صحراوي مروى", "section_name": "1ع5"},
    {"fullname": "طاوي دنيا", "section_name": "1ع5"}, {"fullname": "عالم جبار محمد أيوب", "section_name": "1ع5"},
    {"fullname": "عبدلى عبد الإله", "section_name": "1ع5"}, {"fullname": "عز الدين مختار الناصر", "section_name": "1ع5"},
    {"fullname": "فايدة ياسين", "section_name": "1ع5"}, {"fullname": "قريش رضا عبد الإله", "section_name": "1ع5"},
    {"fullname": "قنيش مختار", "section_name": "1ع5"}, {"fullname": "مدانی فواتيح عتيقة", "section_name": "1ع5"},
    {"fullname": "مغربی محمد صديق", "section_name": "1ع5"}, {"fullname": "منصور دعاء", "section_name": "1ع5"},
    {"fullname": "مهنى محمد عبد الرحمان", "section_name": "1ع5"}, {"fullname": "نباتى شرقي عبد الوهاب", "section_name": "1ع5"},

    # --- قسم 1ع6 ---
    {"fullname": "ابراهيم فواتيح على نصر الله", "section_name": "1ع6"}, {"fullname": "الغريسي مليكة", "section_name": "1ع6"},
    {"fullname": "أوجالی فارس", "section_name": "1ع6"}, {"fullname": "أوسيف أشرف محمد الأمين", "section_name": "1ع6"},
    {"fullname": "بدة رانية", "section_name": "1ع6"}, {"fullname": "بشير نور الهدى", "section_name": "1ع6"},
    {"fullname": "بشيري محمد ياسين", "section_name": "1ع6"}, {"fullname": "بلعربي عبد اللطيف", "section_name": "1ع6"},
    {"fullname": "بلميلود سيف الاسلام", "section_name": "1ع6"}, {"fullname": "بن خلف الله أنس", "section_name": "1ع6"},
    {"fullname": "بن دوخة بشرى", "section_name": "1ع6"}, {"fullname": "بن رابح رحيل", "section_name": "1ع6"},
    {"fullname": "بن صباح ندى امال", "section_name": "1ع6"}, {"fullname": "بن عبد الرحمان اسراء", "section_name": "1ع6"},
    {"fullname": "بن ميرة ملاك", "section_name": "1ع6"}, {"fullname": "بوسلهام نور هند رشيدة", "section_name": "1ع6"},
    {"fullname": "بوعبدالله تامر", "section_name": "1ع6"}, {"fullname": "بوكراس عبد الرحمان", "section_name": "1ع6"},
    {"fullname": "جلواط محمد", "section_name": "1ع6"}, {"fullname": "حداد ياسر", "section_name": "1ع6"},
    {"fullname": "رقيق يسعد سارة", "section_name": "1ع6"}, {"fullname": "سايح دعاء", "section_name": "1ع6"},
    {"fullname": "سحنون رغدة", "section_name": "1ع6"}, {"fullname": "شافع خودة", "section_name": "1ع6"},
    {"fullname": "صغير عبد الإله سفيان", "section_name": "1ع6"}, {"fullname": "عبادية يوسف", "section_name": "1ع6"},
    {"fullname": "عرابة ملك نور", "section_name": "1ع6"}, {"fullname": "عليان رميساء", "section_name": "1ع6"},
    {"fullname": "قبايلي زهير", "section_name": "1ع6"}, {"fullname": "قدار عبد القادر", "section_name": "1ع6"},
    {"fullname": "مبارك اسحاق", "section_name": "1ع6"}, {"fullname": "مطرانی لليا", "section_name": "1ع6"},
    {"fullname": "مقدم جلال", "section_name": "1ع6"}, {"fullname": "مكى اكرام فاطمة", "section_name": "1ع6"},
    {"fullname": "موساوي وجدان", "section_name": "1ع6"}, {"fullname": "ميموني ألاء", "section_name": "1ع6"},
    {"fullname": "نباتى شرقى زهرة حليمة", "section_name": "1ع6"}, {"fullname": "يخو عبد القادر سيف الدين", "section_name": "1ع6"},

    # --- قسم 2أف1 ---
    {"fullname": "بخدة محمد ريان", "section_name": "2أف1"}, {"fullname": "بريشي عبد الاله", "section_name": "2أف1"},
    {"fullname": "بلهوان رميساء", "section_name": "2أف1"}, {"fullname": "بلولو ميلود", "section_name": "2أف1"},
    {"fullname": "بن زايد عبدالجليل", "section_name": "2أف1"}, {"fullname": "بن شراير أميمة", "section_name": "2أف1"},
    {"fullname": "بن قانة مريم", "section_name": "2أف1"}, {"fullname": "بن ميرة ادم", "section_name": "2أف1"},
    {"fullname": "بودالي مروى", "section_name": "2أف1"}, {"fullname": "بودية محمد رضوان", "section_name": "2أف1"},
    {"fullname": "بورحلة ميمونة دعاء", "section_name": "2أف1"}, {"fullname": "بوسيف محمد", "section_name": "2أف1"},
    {"fullname": "بوسيف هناء مريم", "section_name": "2أف1"}, {"fullname": "جرى مروى", "section_name": "2أف1"},
    {"fullname": "رحماني عبد الله هواري", "section_name": "2أف1"}, {"fullname": "رزقى امينة", "section_name": "2أف1"},
    {"fullname": "رصانی محمد ندير", "section_name": "2أف1"}, {"fullname": "رفاس هاجر", "section_name": "2أف1"},
    {"fullname": "روام سريك إيمان إسراء", "section_name": "2أف1"}, {"fullname": "سلهامي مصطفى", "section_name": "2أف1"},
    {"fullname": "شافع اسراء", "section_name": "2أف1"}, {"fullname": "صابري محمد رحيم", "section_name": "2أف1"},
    {"fullname": "صبار يسرى", "section_name": "2أف1"}, {"fullname": "صرصار ايوب", "section_name": "2أف1"},
    {"fullname": "طباق فاطمة", "section_name": "2أف1"}, {"fullname": "عرابی لميس", "section_name": "2أف1"},
    {"fullname": "غنومات عبد الرحمان", "section_name": "2أف1"}, {"fullname": "فقيرة غفران", "section_name": "2أف1"},
    {"fullname": "قاضى فضيلة", "section_name": "2أف1"}, {"fullname": "قرنة لينا حنين", "section_name": "2أف1"},
    {"fullname": "كرايي فاطمة", "section_name": "2أف1"}, {"fullname": "لبيض مختارية", "section_name": "2أف1"},
    {"fullname": "مزاري إسماعيل", "section_name": "2أف1"}, {"fullname": "معروف يحياوي زهرة", "section_name": "2أف1"},

    # --- قسم 2أف2 ---
    {"fullname": "بلجيلالى مختارية", "section_name": "2أف2"}, {"fullname": "بلغربي سرين سعدية", "section_name": "2أف2"},
    {"fullname": "بلهاشمى رياض", "section_name": "2أف2"}, {"fullname": "بن عبيد منور", "section_name": "2أف2"},
    {"fullname": "بن عمر كوثر", "section_name": "2أف2"}, {"fullname": "بو لنوار مصطفى عبد الرزاق", "section_name": "2أف2"},
    {"fullname": "بو مدين اسماء رحمة", "section_name": "2أف2"}, {"fullname": "بوترعة مصطفى", "section_name": "2أف2"},
    {"fullname": "بوسيف عبير فاطمة", "section_name": "2أف2"}, {"fullname": "بونعجة رميساء", "section_name": "2أف2"},
    {"fullname": "حداد هواري", "section_name": "2أف2"}, {"fullname": "خيئر فاطمة", "section_name": "2أف2"},
    {"fullname": "روام سريك يونس اسماعيل", "section_name": "2أف2"}, {"fullname": "ريزوقة أية", "section_name": "2أف2"},
    {"fullname": "زازوة سندس", "section_name": "2أف2"}, {"fullname": "شنوفي حورية", "section_name": "2أف2"},
    {"fullname": "عياشى صورية", "section_name": "2أف2"}, {"fullname": "غرناطى ألاء", "section_name": "2أف2"},
    {"fullname": "فريفر فاطمة", "section_name": "2أف2"}, {"fullname": "قانة يونس", "section_name": "2أف2"},
    {"fullname": "قرير روفيدة", "section_name": "2أف2"}, {"fullname": "قليليل راضية", "section_name": "2أف2"},
    {"fullname": "كرتالي مروى", "section_name": "2أف2"}, {"fullname": "كرغلى ايناس", "section_name": "2أف2"},
    {"fullname": "كيري هيثم وسيم", "section_name": "2أف2"}, {"fullname": "لحمر خيرة", "section_name": "2أف2"},
    {"fullname": "لزرق سلابي محمد", "section_name": "2أف2"}, {"fullname": "لوراد سندس فاطمة", "section_name": "2أف2"},
    {"fullname": "محنداحمد سرين", "section_name": "2أف2"}, {"fullname": "مرين كوثر", "section_name": "2أف2"},
    {"fullname": "مصاحب سيد أحمد", "section_name": "2أف2"}, {"fullname": "ملاح العيد", "section_name": "2أف2"},
    {"fullname": "مونسی صابرين", "section_name": "2أف2"}, {"fullname": "ميلوى فتيحة", "section_name": "2أف2"},
    {"fullname": "نايري جميلة", "section_name": "2أف2"},

    # --- قسم 2لغ ---
    {"fullname": "اوعيل نصيرة", "section_name": "2لغ"}, {"fullname": "بلعباس هبة", "section_name": "2لغ"},
    {"fullname": "بن حمر العين فراح مريم", "section_name": "2لغ"}, {"fullname": "بن عياد فاطمة الزهراء", "section_name": "2لغ"},
    {"fullname": "بوترعة فراح", "section_name": "2لغ"}, {"fullname": "بوحريرة محمد عثمان", "section_name": "2لغ"},
    {"fullname": "بوخيبة أيمن", "section_name": "2لغ"}, {"fullname": "بوهالي عماد", "section_name": "2لغ"},
    {"fullname": "حمادي فاطمة الزهراء", "section_name": "2لغ"}, {"fullname": "خفافة فاطمة الزهراء", "section_name": "2لغ"},
    {"fullname": "روام سريك رجاء", "section_name": "2لغ"}, {"fullname": "روام سريك ميلود", "section_name": "2لغ"},
    {"fullname": "زمايش بلاحة عبد الصمد", "section_name": "2لغ"}, {"fullname": "سايح شيماء", "section_name": "2لغ"},
    {"fullname": "سليمانى عبد الرحمان", "section_name": "2لغ"}, {"fullname": "سوالمية نورهان هدى", "section_name": "2لغ"},
    {"fullname": "شريف حضرية فاطمة الزهراء", "section_name": "2لغ"}, {"fullname": "صحراوي ولاء شريفة", "section_name": "2لغ"},
    {"fullname": "عقى دعاء", "section_name": "2لغ"}, {"fullname": "علمى سيرين هناء", "section_name": "2لغ"},
    {"fullname": "فايدة مروى", "section_name": "2لغ"}, {"fullname": "قدور بن قادة سماح", "section_name": "2لغ"},
    {"fullname": "كوار نور الهدى", "section_name": "2لغ"}, {"fullname": "لزرق شلابي سندس", "section_name": "2لغ"},
    {"fullname": "لليبي وفية", "section_name": "2لغ"}, {"fullname": "محلى صهيب", "section_name": "2لغ"},
    {"fullname": "مصابيح ريتاج", "section_name": "2لغ"}, {"fullname": "أزرو غزلان أماني", "section_name": "2لغ"},
    {"fullname": "اوسيف مروى", "section_name": "2لغ"}, {"fullname": "بكاي أميرة", "section_name": "2لغ"},
    {"fullname": "راشم شيماء", "section_name": "2لغ"}, {"fullname": "روام سريك فاطمة الزهراء", "section_name": "2لغ"},
    {"fullname": "زلاط ياسمين", "section_name": "2لغ"}, {"fullname": "فغول أدم", "section_name": "2لغ"},
    {"fullname": "فقيرة سلسبيل", "section_name": "2لغ"}, {"fullname": "مراح محمد عادل", "section_name": "2لغ"},

    # --- قسم 2ع ت1 ---
    {"fullname": "أوجيت شهيناز", "section_name": "2ع ت1"}, {"fullname": "بلغوتي ملاك", "section_name": "2ع ت1"},
    {"fullname": "بلميلود مروة", "section_name": "2ع ت1"}, {"fullname": "بن زهرة شهيناز", "section_name": "2ع ت1"},
    {"fullname": "بن زهرة محمد الامين", "section_name": "2ع ت1"}, {"fullname": "بوسيف وسام", "section_name": "2ع ت1"},
    {"fullname": "بوسيف شيماء", "section_name": "2ع ت1"}, {"fullname": "بوشيخي لجين", "section_name": "2ع ت1"},
    {"fullname": "بوقفحة اسلام عبد الحميد نذير", "section_name": "2ع ت1"}, {"fullname": "حساين محمد رمزي", "section_name": "2ع ت1"},
    {"fullname": "حمادي هاجر", "section_name": "2ع ت1"}, {"fullname": "حواش عبد الرحيم", "section_name": "2ع ت1"},
    {"fullname": "خيئر نجوى", "section_name": "2ع ت1"}, {"fullname": "دركى عبد الحق", "section_name": "2ع ت1"},
    {"fullname": "دركى رباب كوثر", "section_name": "2ع ت1"}, {"fullname": "درنى علي عبد المجيد", "section_name": "2ع ت1"},
    {"fullname": "دلة فاطمة الزهراء", "section_name": "2ع ت1"}, {"fullname": "رامى ميلود", "section_name": "2ع ت1"},
    {"fullname": "رميشى أكرم عماد الدين", "section_name": "2ع ت1"}, {"fullname": "زمايش منال", "section_name": "2ع ت1"},
    {"fullname": "زوبير فاطمة زهرة", "section_name": "2ع ت1"}, {"fullname": "سدي عدة محمد", "section_name": "2ع ت1"},
    {"fullname": "سريج فاطمة الزهراء", "section_name": "2ع ت1"}, {"fullname": "سليمانى غازي", "section_name": "2ع ت1"},
    {"fullname": "صبار كوثر", "section_name": "2ع ت1"}, {"fullname": "صديق رياض", "section_name": "2ع ت1"},
    {"fullname": "عامري إيمان", "section_name": "2ع ت1"}, {"fullname": "عراب رفيق", "section_name": "2ع ت1"},
    {"fullname": "عمارة إبتسام", "section_name": "2ع ت1"}, {"fullname": "غنومات خديجة", "section_name": "2ع ت1"},
    {"fullname": "فریوي يحي مختار علي عصام", "section_name": "2ع ت1"}, {"fullname": "قعنون فضيلة", "section_name": "2ع ت1"},
    {"fullname": "كاملي رحيل", "section_name": "2ع ت1"}, {"fullname": "لبيض مروة", "section_name": "2ع ت1"},
    {"fullname": "لحدير عبد الرحمان", "section_name": "2ع ت1"}, {"fullname": "لرجم إكرام كوثر", "section_name": "2ع ت1"},
    {"fullname": "مصطفى عبد الرحيم", "section_name": "2ع ت1"}, {"fullname": "معروف يحياوي خديجة", "section_name": "2ع ت1"},
    {"fullname": "مغوفل فاطمة الزهراء", "section_name": "2ع ت1"},

    # --- قسم 2ع ت2 ---
    {"fullname": "بلبح سارة", "section_name": "2ع ت2"}, {"fullname": "بلعيدي عبد الإله", "section_name": "2ع ت2"},
    {"fullname": "بن بلال عبد الجليل", "section_name": "2ع ت2"}, {"fullname": "بن زايد محمد أمين", "section_name": "2ع ت2"},
    {"fullname": "بن عودة شحط مهدي", "section_name": "2ع ت2"}, {"fullname": "بن نوار عبد العزيز", "section_name": "2ع ت2"},
    {"fullname": "بوسيف علاء الدين", "section_name": "2ع ت2"}, {"fullname": "حاج أحمد مريم", "section_name": "2ع ت2"},
    {"fullname": "حريدي عبد الحق لخضر", "section_name": "2ع ت2"}, {"fullname": "خالدي إبتهال", "section_name": "2ع ت2"},
    {"fullname": "خليف دنيا", "section_name": "2ع ت2"}, {"fullname": "دلهوم محمد", "section_name": "2ع ت2"},
    {"fullname": "رفاسي محمد الامين", "section_name": "2ع ت2"}, {"fullname": "رقراق فردوس خيرة", "section_name": "2ع ت2"},
    {"fullname": "زدام مايا", "section_name": "2ع ت2"}, {"fullname": "سهالة عبد الله فارس الدين", "section_name": "2ع ت2"},
    {"fullname": "سى مرابط فريال", "section_name": "2ع ت2"}, {"fullname": "شاوش محمد باديس", "section_name": "2ع ت2"},
    {"fullname": "شرقي فاطمة", "section_name": "2ع ت2"}, {"fullname": "شعيب رحاب سارة", "section_name": "2ع ت2"},
    {"fullname": "شيخ ابراهيم", "section_name": "2ع ت2"}, {"fullname": "شيكر جاوتی عبد المجيد", "section_name": "2ع ت2"},
    {"fullname": "صغيري وليد", "section_name": "2ع ت2"}, {"fullname": "عالم جبار ناجی", "section_name": "2ع ت2"},
    {"fullname": "عثمانى شيماء", "section_name": "2ع ت2"}, {"fullname": "عرابة لميس", "section_name": "2ع ت2"},
    {"fullname": "عنصر الاء", "section_name": "2ع ت2"}, {"fullname": "غيلاس فارس إسلام", "section_name": "2ع ت2"},
    {"fullname": "فغلو خير الدين", "section_name": "2ع ت2"}, {"fullname": "قرمى رانيا", "section_name": "2ع ت2"},
    {"fullname": "كرايی فايزة منال", "section_name": "2ع ت2"}, {"fullname": "لزرق شلابي سولا ف", "section_name": "2ع ت2"},
    {"fullname": "ماموني نور الهدى", "section_name": "2ع ت2"}, {"fullname": "مبارك ابتسام", "section_name": "2ع ت2"},
    {"fullname": "مسلم مروى", "section_name": "2ع ت2"}, {"fullname": "نومية عبد الله", "section_name": "2ع ت2"},
    {"fullname": "هواري الياس", "section_name": "2ع ت2"}, {"fullname": "واحمانی عصام الدين", "section_name": "2ع ت2"},
    {"fullname": "وليد جميلة", "section_name": "2ع ت2"}, {"fullname": "يطو دعاء", "section_name": "2ع ت2"},

    # --- قسم 2تق ---
    {"fullname": "بختى ايمن", "section_name": "2تق"}, {"fullname": "بركليت حنان", "section_name": "2تق"},
    {"fullname": "بشير عبد الإله", "section_name": "2تق"}, {"fullname": "بلعباس آية", "section_name": "2تق"},
    {"fullname": "بلهواري بشرى", "section_name": "2تق"}, {"fullname": "بوتنزار عبدالقادر", "section_name": "2تق"},
    {"fullname": "بودية بشرى", "section_name": "2تق"}, {"fullname": "بوشعالة ريتاج الاء", "section_name": "2تق"},
    {"fullname": "بوقويلبة خديجة", "section_name": "2تق"}, {"fullname": "بوكبدة علاء الدين", "section_name": "2تق"},
    {"fullname": "بولحية فاطمة الزهراء", "section_name": "2تق"}, {"fullname": "تهامى محمد الصديق", "section_name": "2تق"},
    {"fullname": "خننو نهاد", "section_name": "2تق"}, {"fullname": "دحمانى محمد ندير", "section_name": "2تق"},
    {"fullname": "دلباز حنان", "section_name": "2تق"}, {"fullname": "دلباز عبد الجليل", "section_name": "2تق"},
    {"fullname": "رصانى خديجة", "section_name": "2تق"}, {"fullname": "رصانى عبد الهادي", "section_name": "2تق"},
    {"fullname": "عشوري عبد الكريم", "section_name": "2تق"}, {"fullname": "عليلات أيهم عبد الرحمان", "section_name": "2تق"},
    {"fullname": "غربي يوسف", "section_name": "2تق"}, {"fullname": "غمري دعاء منى", "section_name": "2تق"},
    {"fullname": "قدورة حفصة", "section_name": "2تق"}, {"fullname": "قيري صابرين", "section_name": "2تق"},
    {"fullname": "كرطالى ياسين", "section_name": "2تق"}, {"fullname": "لوشنى سندس", "section_name": "2تق"},
    {"fullname": "مزغرانى عادل", "section_name": "2تق"}, {"fullname": "موساوي محمد صهيب", "section_name": "2تق"},
    {"fullname": "يطو ايمان", "section_name": "2تق"},

    # --- قسم 2ريا ---
    {"fullname": "بكة ريتاج", "section_name": "2ريا"}, {"fullname": "بن عبورة جنة الايمان", "section_name": "2ريا"},
    {"fullname": "بوتين نرجس جوهر", "section_name": "2ريا"}, {"fullname": "سعد هواري ياسين", "section_name": "2ريا"},
    {"fullname": "صحراوي صفاء", "section_name": "2ريا"}, {"fullname": "كاعوش عائشة", "section_name": "2ريا"},
    {"fullname": "لحمر ايناس اميرة سندس", "section_name": "2ريا"}, {"fullname": "مقداد إكرام", "section_name": "2ريا"},

    # --- قسم 2تر (هـ ط) ---
    {"fullname": "بن زهرة عبد المعز", "section_name": "2تر (هـ ط)"}, {"fullname": "سنحين إكرام", "section_name": "2تر (هـ ط)"},
    {"fullname": "عرابي بسملة", "section_name": "2تر (هـ ط)"}, {"fullname": "لعموري عائشة", "section_name": "2تر (هـ ط)"},
    {"fullname": "مشتی اسراء", "section_name": "2تر (هـ ط)"}, {"fullname": "مهون عبد الاله", "section_name": "2تر (هـ ط)"},

    # --- قسم 2تر (هـ ك) ---
    {"fullname": "باوية محمدإحسان", "section_name": "2تر (هـ ك)"}, {"fullname": "بن زينب محمد", "section_name": "2تر (هـ ك)"},
    {"fullname": "بن عائشة فاطمة الزهراء", "section_name": "2تر (هـ ك)"}, {"fullname": "بن علو محمد رياض", "section_name": "2تر (هـ ك)"},
    {"fullname": "بوسيف منال سعدية", "section_name": "2تر (هـ ك)"}, {"fullname": "حسين سارة", "section_name": "2تر (هـ ك)"},
    {"fullname": "زيري رحاب", "section_name": "2تر (هـ ك)"}, {"fullname": "سعادي أنس عبد الرحمان", "section_name": "2تر (هـ ك)"},
    {"fullname": "سعادي ميساء", "section_name": "2تر (هـ ك)"}, {"fullname": "طيفور عزيزة", "section_name": "2تر (هـ ك)"},
    {"fullname": "كرطالى هند", "section_name": "2تر (هـ ك)"},

    # --- قسم 2تر (هـ م) ---
    {"fullname": "بن سعادة ماريا", "section_name": "2تر (هـ م)"}, {"fullname": "بن عائشة هاجر", "section_name": "2تر (هـ م)"},
    {"fullname": "بوزيدي نور الهدى ليليا", "section_name": "2تر (هـ م)"}, {"fullname": "بوسيف عبد الله", "section_name": "2تر (هـ م)"},
    {"fullname": "تلى آية", "section_name": "2تر (هـ م)"}, {"fullname": "خير الدين عبد الهادي يحيى", "section_name": "2تر (هـ م)"},
    {"fullname": "سى فضيل عبد النور", "section_name": "2تر (هـ م)"}, {"fullname": "قرشى هديل", "section_name": "2تر (هـ م)"},
    {"fullname": "مداح بشرى", "section_name": "2تر (هـ م)"}, {"fullname": "نوال ريهام سندس", "section_name": "2تر (هـ م)"},
    
    # --- قسم 3أف1 ---
    {"fullname": "بلهزيل نور الهدى", "section_name": "3أف2"}, {"fullname": "بن زهرة آية", "section_name": "3أف2"},
    {"fullname": "بن عودة ياسين", "section_name": "3أف2"}, {"fullname": "بن يعقوب مريم", "section_name": "3أف2"},
    {"fullname": "بن يوس عومرية", "section_name": "3أف2"}, {"fullname": "بوخاري خضرة فدوى", "section_name": "3أف2"},
    {"fullname": "بوشنتوف أحمد إسلام", "section_name": "3أف2"}, {"fullname": "بونعجة عائشة", "section_name": "3أف2"},
    {"fullname": "تركي كوثر", "section_name": "3أف2"}, {"fullname": "تقار اخلاص", "section_name": "3أف2"},
    {"fullname": "جعلاب ليندة", "section_name": "3أف2"}, {"fullname": "حروس آية", "section_name": "3أف2"},
    {"fullname": "رصانی غزلان حسنية", "section_name": "3أف2"}, {"fullname": "رصانی خديجة وردية", "section_name": "3أف2"},
    {"fullname": "سلام عبدالقادر محمد امين", "section_name": "3أف2"}, {"fullname": "سواحلية صالحية اسراء", "section_name": "3أف2"},
    {"fullname": "شحمی نادية", "section_name": "3أف2"}, {"fullname": "شيخ عادل", "section_name": "3أف2"},
    {"fullname": "عبادية مروى", "section_name": "3أف2"}, {"fullname": "عدة امينة", "section_name": "3أف2"},
    {"fullname": "عمري زهرة آية", "section_name": "3أف2"}, {"fullname": "عيساوي يوسف", "section_name": "3أف2"},
    {"fullname": "فايدة دعاء خديجة", "section_name": "3أف2"}, {"fullname": "فركان ياسمين", "section_name": "3أف2"},
    {"fullname": "قرنة صورية", "section_name": "3أف2"}, {"fullname": "لحسن محمد امين", "section_name": "3أف2"},
    {"fullname": "مختاري فضيلة", "section_name": "3أف2"}, {"fullname": "مداح روبة", "section_name": "3أف2"},
    {"fullname": "مزيان نور الإيمان", "section_name": "3أف2"}, {"fullname": "مسعودي يوسف رزق الله", "section_name": "3أف2"},

    # --- قسم 3أف2 ---
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
    
    # --- قسم 3لغ (إسبانية) ---
    {"fullname": "أحمد بلاحة زينب", "section_name": "3لغ (إسبانية)"}, {"fullname": "الشرقى محمد عماد الدين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بختاوي ريمة", "section_name": "3لغ (إسبانية)"}, {"fullname": "بن مقداد سولاف", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بو عبد الله نسرين", "section_name": "3لغ (إسبانية)"}, {"fullname": "بوجراف مروى", "section_name": "3لغ (إسبانية)"},
    {"fullname": "بوخرطة حمزة", "section_name": "3لغ (إسبانية)"}, {"fullname": "بولحية مهدي", "section_name": "3لغ (إسبانية)"},
    {"fullname": "جفال مهدي سايح", "section_name": "3لغ (إسبانية)"}, {"fullname": "حمو ابراهيم", "section_name": "3لغ (إسبانية)"},
    {"fullname": "دودوح مريم دعاء", "section_name": "3لغ (إسبانية)"}, {"fullname": "رحماني اسلام", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عبد السلام سندس رتاج صورية", "section_name": "3لغ (إسبانية)"}, {"fullname": "عراب سعيد جوهرة ملاك", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عكرمى رميساء", "section_name": "3لغ (إسبانية)"}, {"fullname": "علواش محمد الامين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "عمایم حفصة", "section_name": "3لغ (إسبانية)"}, {"fullname": "غريبي أروة سرين", "section_name": "3لغ (إسبانية)"},
    {"fullname": "فايدة مارية", "section_name": "3لغ (إسبانية)"}, {"fullname": "فريفر إبتسام", "section_name": "3لغ (إسبانية)"},
    {"fullname": "فيدوح دعاء", "section_name": "3لغ (إسبانية)"}, {"fullname": "كبداني سندس", "section_name": "3لغ (إسبانية)"},
    {"fullname": "كتاب شيماء", "section_name": "3لغ (إسبانية)"}, {"fullname": "مشري مختارية", "section_name": "3لغ (إسبانية)"},
    {"fullname": "مصابيح إسراء", "section_name": "3لغ (إسبانية)"}, {"fullname": "مقدم بحوص فاروق", "section_name": "3لغ (إسبانية)"},
    {"fullname": "نباتى شرقي فريال", "section_name": "3لغ (إسبانية)"}, {"fullname": "يوكلف يسرى", "section_name": "3لغ (إسبانية)"},

    # --- قسم 3لغ (ألمانية) ---
    {"fullname": "بخدة هبة الرحمن", "section_name": "3لغ (ألمانية)"}, {"fullname": "بن سالم دعاء", "section_name": "3لغ (ألمانية)"},
    {"fullname": "بوشنتوف نسرين بدرة", "section_name": "3لغ (ألمانية)"}, {"fullname": "جعييد يمينة ملاك", "section_name": "3لغ (ألمانية)"},
    {"fullname": "راشم آدم", "section_name": "3لغ (ألمانية)"}, {"fullname": "سريج سارة", "section_name": "3لغ (ألمانية)"},
    {"fullname": "صور رودينة جيداء", "section_name": "3لغ (ألمانية)"}, {"fullname": "طويل مروى", "section_name": "3لغ (ألمانية)"},
    {"fullname": "عبو عبد المالك", "section_name": "3لغ (ألمانية)"},

    # --- قسم 3ع ت1 ---
    {"fullname": "العربي اخلاص", "section_name": "3ع ت1"}, {"fullname": "اليوبي إسراء إلهام", "section_name": "3ع ت1"},
    {"fullname": "بركاني عبد المالك", "section_name": "3ع ت1"}, {"fullname": "بلحميدي خولة", "section_name": "3ع ت1"},
    {"fullname": "بلمختار سناء", "section_name": "3ع ت1"}, {"fullname": "بلميلود أية", "section_name": "3ع ت1"},
    {"fullname": "بن طاطة أميرة", "section_name": "3ع ت1"}, {"fullname": "بن فغول أية", "section_name": "3ع ت1"},
    {"fullname": "بن قانة سكينة", "section_name": "3ع ت1"}, {"fullname": "بن ناجي سلسبيل", "section_name": "3ع ت1"},
    {"fullname": "بن يمينة لميس", "section_name": "3ع ت1"}, {"fullname": "بوتشيش عبد الصمد", "section_name": "3ع ت1"},
    {"fullname": "بوتنزاز محمد يحي", "section_name": "3ع ت1"}, {"fullname": "بوسيف شيماء", "section_name": "3ع ت1"},
    {"fullname": "تشمون محمد", "section_name": "3ع ت1"}, {"fullname": "جبور نادية", "section_name": "3ع ت1"},
    {"fullname": "حاسي عبدالقادر صلاح الدين", "section_name": "3ع ت1"}, {"fullname": "حتو مروى", "section_name": "3ع ت1"},
    {"fullname": "حمزة آية سيرين", "section_name": "3ع ت1"}, {"fullname": "خلق الله حبيب", "section_name": "3ع ت1"},
    {"fullname": "داني معاد بن جبل", "section_name": "3ع ت1"}, {"fullname": "درواش هبة الرحمان غزلان", "section_name": "3ع ت1"},
    {"fullname": "روام سريك هدى", "section_name": "3ع ت1"}, {"fullname": "ريزوقة كوثر", "section_name": "3ع ت1"},
    {"fullname": "شباح وفاء", "section_name": "3ع ت1"}, {"fullname": "شحمی حفصة", "section_name": "3ع ت1"},
    {"fullname": "شنوفي وداد وردة", "section_name": "3ع ت1"}, {"fullname": "شوايل شايلة غالم ريان", "section_name": "3ع ت1"},
    {"fullname": "صويلح منال", "section_name": "3ع ت1"}, {"fullname": "عبادية نجوى سارة", "section_name": "3ع ت1"},
    {"fullname": "غربي أيوب", "section_name": "3ع ت1"}, {"fullname": "قطاف جهينة", "section_name": "3ع ت1"},
    {"fullname": "كاشة محمد", "section_name": "3ع ت1"}, {"fullname": "كرطالي سناء", "section_name": "3ع ت1"},
    {"fullname": "كرطالي عبد الباسط براء", "section_name": "3ع ت1"}, {"fullname": "كرطالي عبد القادر", "section_name": "3ع ت1"},
    {"fullname": "لزغم عبد النور", "section_name": "3ع ت1"}, {"fullname": "لمقدم هبة الرحمان غزلان", "section_name": "3ع ت1"},
    {"fullname": "لمقدم اسراء", "section_name": "3ع ت1"}, {"fullname": "مولوج دحو محمد", "section_name": "3ع ت1"},
    {"fullname": "ناصر شرقي آدم محمد", "section_name": "3ع ت1"}, {"fullname": "ولد سليمان مروان", "section_name": "3ع ت1"},
    {"fullname": "يطو ياسين", "section_name": "3ع ت1"},

    # --- قسم 3ع ت2 ---
    {"fullname": "بطيشة محمد", "section_name": "3ع ت2"}, {"fullname": "بلعاطى مختارية", "section_name": "3ع ت2"},
    {"fullname": "بلعيدي فاطمة", "section_name": "3ع ت2"}, {"fullname": "بلميلود دعاء", "section_name": "3ع ت2"},
    {"fullname": "بن سعيد نور الهدى", "section_name": "3ع ت2"}, {"fullname": "بن يوب نجاة", "section_name": "3ع ت2"},
    {"fullname": "بوعزة سندس", "section_name": "3ع ت2"}, {"fullname": "تامدة شيماء", "section_name": "3ع ت2"},
    {"fullname": "تقار دعاء", "section_name": "3ع ت2"}, {"fullname": "تومی إسحاق مسعود أحمد", "section_name": "3ع ت2"},
    {"fullname": "جعفري ملاك", "section_name": "3ع ت2"}, {"fullname": "جلول عبد الاله اسلام", "section_name": "3ع ت2"},
    {"fullname": "حرطال عاشورية دعاء", "section_name": "3ع ت2"}, {"fullname": "رابح سمية", "section_name": "3ع ت2"},
    {"fullname": "زيان يونس اسلام", "section_name": "3ع ت2"}, {"fullname": "زيري نسرين", "section_name": "3ع ت2"},
    {"fullname": "سايح كوثر", "section_name": "3ع ت2"}, {"fullname": "سعود محمد علاء الدين", "section_name": "3ع ت2"},
    {"fullname": "سى مرابط أمال", "section_name": "3ع ت2"}, {"fullname": "شكور يوسف", "section_name": "3ع ت2"},
    {"fullname": "صرصار أحمد مجيب الرحمان", "section_name": "3ع ت2"}, {"fullname": "عبوشي لخضر", "section_name": "3ع ت2"},
    {"fullname": "عتو ميلود ياسين", "section_name": "3ع ت2"}, {"fullname": "عرابة محمد ربيع", "section_name": "3ع ت2"},
    {"fullname": "عطا الله مريم", "section_name": "3ع ت2"}, {"fullname": "فريح إسماعيل", "section_name": "3ع ت2"},
    {"fullname": "قادري يوسف", "section_name": "3ع ت2"}, {"fullname": "قليل مروى", "section_name": "3ع ت2"},
    {"fullname": "قليل حسام الدين", "section_name": "3ع ت2"}, {"fullname": "مصابيح ياسر", "section_name": "3ع ت2"},
    {"fullname": "مقداد يوسف", "section_name": "3ع ت2"}, {"fullname": "يحي لقمان", "section_name": "3ع ت2"},

   # --- قسم 3تق ---
    {"fullname": "بطيشة محمد", "section_name": "3تق"},
    {"fullname": "بلعاطى مختارية", "section_name": "3تق"},
    {"fullname": "بلعيدي فاطمة", "section_name": "3تق"},
    {"fullname": "بلميلود دعاء", "section_name": "3تق"},
    {"fullname": "بن سعيد نور الهدى", "section_name": "3تق"},
    {"fullname": "بن يوب نجاة", "section_name": "3تق"},
    {"fullname": "بوعزة سندس", "section_name": "3تق"},
    {"fullname": "تامدة شيماء", "section_name": "3تق"},
    {"fullname": "تقار دعاء", "section_name": "3تق"},
    {"fullname": "تومی إسحاق مسعود أحمد", "section_name": "3تق"},
    {"fullname": "جعفري ملاك", "section_name": "3تق"},
    {"fullname": "جلول عبد الاله اسلام", "section_name": "3تق"},
    {"fullname": "حرتال عاشورية دعاء", "section_name": "3تق"},
    {"fullname": "رابح سمية", "section_name": "3تق"},
    {"fullname": "زيان يونس اسلام", "section_name": "3تق"},
    {"fullname": "زيري نسرين", "section_name": "3تق"},
    {"fullname": "سايح كوثر", "section_name": "3تق"},
    {"fullname": "سعود محمد علاء الدين", "section_name": "3تق"},
    {"fullname": "سى مرابط أمال", "section_name": "3تق"},
    {"fullname": "شكور يوسف", "section_name": "3تق"},
    {"fullname": "صرصار أحمد مجيب الرحمان", "section_name": "3تق"},
    {"fullname": "عبوشي لخضر", "section_name": "3تق"},
    {"fullname": "عتو ميلود ياسين", "section_name": "3تق"},
    {"fullname": "عرابة محمد ربيع", "section_name": "3تق"},
    {"fullname": "عطا الله مريم", "section_name": "3تق"},
    {"fullname": "فريح إسماعيل", "section_name": "3تق"},
    {"fullname": "قادري يوسف", "section_name": "3تق"},
    {"fullname": "قليل مروى", "section_name": "3تق"},
    {"fullname": "قليل حسام الدين", "section_name": "3تق"},
    {"fullname": "مصابيح ياسر", "section_name": "3تق"},
    {"fullname": "مقداد يوسف", "section_name": "3تق"},
    {"fullname": "يحي لقمان", "section_name": "3تق"},

# --- قسم 3ريا ---
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

# --- قسم 3تر (هـ ك) ---
    {"fullname": "بغداد تسنيم", "section_name": "3تر (هـ ك)"},
    {"fullname": "بلزرق إياد محمد أمين", "section_name": "3تر (هـ ك)"},
    {"fullname": "بلعوينات عبد الرزاق", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوجمعة محمد ياسين", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوزيدي محمد", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوشتة وهيبة", "section_name": "3تر (هـ ك)"},
    {"fullname": "بوعقل عبد المجيد", "section_name": "3تر (هـ ك)"},
    {"fullname": "مصالح محمد صهيب", "section_name": "3تر (هـ ك)"},
    {"fullname": "نجادي امينة نور الهدى", "section_name": "3تر (هـ ك)"},

    # --- قسم 3تر (هـ م) ---
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

        <div class="mt-4 pt-3 border-t flex justify-between items-center text-xs font-semibold">
            <a href="{{ url_for('register_account') }}" class="text-blue-700 hover:underline">تسجيل حساب جديد</a>
            <a href="{{ url_for('recover_account') }}" class="text-amber-700 hover:underline">استعادة الحساب</a>
        </div>
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

# ==============================================================================
# مسارات التسجيل الجديد واستعادة الحساب (مرتبطة بجدول User و SQLAlchemy)
# ==============================================================================

REGISTER_PAGE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل حساب جديد - ثانوية الشهيد قوديد أحمد</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-xl font-bold text-gray-800">إنشاء حساب جديد</h1>
            <p class="text-xs text-blue-600 font-semibold mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="space-y-2 mb-4">
              {% for category, message in messages %}
                <div class="p-3 rounded-lg text-xs font-bold text-center border {% if category == 'success' %}bg-emerald-50 text-emerald-700 border-emerald-200{% else %}bg-red-50 text-red-700 border-red-200{% endif %}">
                  {{ message }}
                </div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}

        <form method="POST" action="{{ url_for('register_account') }}" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الاسم الكامل</label>
                <input type="text" name="fullname" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الصفة التربوية (الدور)</label>
                <select name="role" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white focus:ring-2 focus:ring-blue-600 focus:outline-none">
                    <option value="teacher">أستاذ</option>
                    <option value="counselor">مستشار التربية</option>
                    <option value="inspector_deputy">الناظر</option>
                    <option value="director">المدير</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" required minlength="4" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-3 rounded-lg shadow-lg transition">
                تسجيل الحساب
            </button>
        </form>

        <div class="mt-5 pt-4 border-t flex justify-between items-center text-xs font-semibold">
            <a href="{{ url_for('home') }}" class="text-blue-700 hover:underline">العودة لتسجيل الدخول</a>
            <a href="{{ url_for('recover_account') }}" class="text-amber-700 hover:underline">استعادة الحساب</a>
        </div>
    </div>
</body>
</html>
"""

RECOVER_PAGE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>استعادة الحساب - ثانوية الشهيد قوديد أحمد</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Cairo', sans-serif; }</style>
</head>
<body class="bg-gradient-to-br from-blue-900 via-indigo-900 to-slate-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl w-full max-w-md p-8 border border-white/20">
        <div class="text-center mb-6">
            <h1 class="text-xl font-bold text-gray-800">استعادة الحساب وتعيين كلمة مرور جديدة</h1>
            <p class="text-xs text-blue-600 font-semibold mt-1">ثانوية الشهيد قوديد أحمد ـ سيدي الشحمي</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="space-y-2 mb-4">
              {% for category, message in messages %}
                <div class="p-3 rounded-lg text-xs font-bold text-center border {% if category == 'success' %}bg-emerald-50 text-emerald-700 border-emerald-200{% else %}bg-red-50 text-red-700 border-red-200{% endif %}">
                  {{ message }}
                </div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}

        <form method="POST" action="{{ url_for('recover_account') }}" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">اسم المستخدم المسجل</label>
                <input type="text" name="username" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">الاسم الكامل المطابق للحساب</label>
                <input type="text" name="fullname" required class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">كلمة المرور الجديدة</label>
                <input type="password" name="new_password" required minlength="4" class="w-full px-4 py-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-lg shadow-lg transition">
                تحديث كلمة المرور
            </button>
        </form>

        <div class="mt-5 pt-4 border-t flex justify-between items-center text-xs font-semibold">
            <a href="{{ url_for('home') }}" class="text-blue-700 hover:underline">العودة لتسجيل الدخول</a>
            <a href="{{ url_for('register_account') }}" class="text-indigo-700 hover:underline">إنشاء حساب جديد</a>
        </div>
    </div>
</body>
</html>
"""

@app.route("/register", methods=["GET", "POST"], endpoint="register_account")
def register_account():
    if request.method == "POST":
        fullname = (request.form.get("fullname") or "").strip()
        username = (request.form.get("username") or "").strip()
        role = (request.form.get("role") or "teacher").strip()
        password = request.form.get("password") or ""

        if not fullname or not username or not password:
            flash("يرجى ملء جميع الحقول المطلوبة.", "danger")
            return redirect(url_for("register_account"))

        if User.query.filter_by(username=username).first():
            flash("اسم المستخدم مستعمل مسبقاً، يرجى اختيار اسم آخر.", "danger")
            return redirect(url_for("register_account"))

        new_user = User(
            username=username,
            password=password,
            role=role,
            fullname=fullname
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f"تم إنشاء الحساب ({username}) بنجاح. يمكنك الآن تسجيل الدخول.", "success")
        return redirect(url_for("register_account"))

    return render_template_string(REGISTER_PAGE_HTML)

@app.route("/recover-account", methods=["GET", "POST"], endpoint="recover_account")
def recover_account():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
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

    return render_template_string(RECOVER_PAGE_HTML)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
