from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# مفتاح الأمان للجلسات
app.secret_key = 'philo_school_manager_secret_key_2026'

# ربط قاعدة بيانات Supabase (يمكنك ترك هذا الرابط أو ضبطه عبر متغيرات البيئة في Render)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# نموذج جدول المستخدمين في قاعدة البيانات
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(30), nullable=False) # director, inspector_deputy, counselor, teacher

# إنشاء الجداول تلقائياً عند التشغيل الأول
with app.app_context():
    db.create_all()

# الصفحة الرئيسية (توجه مباشرة نحو صفحة المصادقة/تسجيل الدخول)
@app.route('/')
def home():
    return render_template('auth.html')

# مسار معالجة تسجيل الدخول حسب الدور
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    # التوجيه الذكي حسب الدور التربوي المختار
    if role == 'director':
        return "مرحباً بك في لوحة تحكم المدير (التسيير الشامل للمؤسسة)"
    elif role == 'inspector_deputy':
        return "مرحباً بك في لوحة تحكم الناظر (التنسيق البيداغوجي ومتابعة الأقسام)"
    elif role == 'counselor':
        return "مرحباً بك في لوحة مستشار التربية (متابعة الغيابات والانضباط اليومي)"
    elif role == 'teacher':
        return "مرحباً بك في ورقة بيانات الأساتذة (تسجيل الحضور والغياب للقسم)"
    else:
        return "الرجاء تحديد الصفة بدقة للمتابعة", 400

if __name__ == '__main__':
    app.run(debug=True)
