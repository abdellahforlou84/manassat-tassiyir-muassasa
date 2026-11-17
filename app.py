from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# إعداد قاعدة البيانات المحلية الدائمة (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== هندسة جداول قاعدة البيانات ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False) # director, inspector_deputy, counselor, teacher
    fullname = db.Column(db.String(120), nullable=False)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # مثال: 1 ج م ع 1
    level = db.Column(db.String(50), nullable=False) # مثال: الأولى ثانوي

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    teacher_name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='غائب') # غائب أو مبرر

class LessonLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_name = db.Column(db.String(120), nullable=False)
    section_name = db.Column(db.String(50), nullable=False)
    lesson_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

# إنشاء الجداول تلقائياً عند أول تشغيل
with app.app_context():
    db.create_all()
    # إضافة حسابات افتراضية إذا كانت الجداول فارغة
    if not User.query.first():
        default_users = [
            User(username='director', password='123456', role='director', fullname='السيد المدير'),
            User(username='deputy', password='123456', role='inspector_deputy', fullname='السيد الناظر'),
            User(username='counselor', password='123456', role='counselor', fullname='السيد مستشار التربية'),
            User(username='teacher', password='123456', role='teacher', fullname='الأستاذ الفاضل')
        ]
        db.session.add_all(default_users)
        db.session.commit()

# ==================== المسارات والتحكم (Routes) ====================

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

    # التوجيه حسب الدور
    if role == 'director':
        return render_template('dashboard_director.html', username=user.fullname, attendances=Attendance.query.all())
    elif role == 'inspector_deputy':
        return render_template('dashboard_deputy.html', username=user.fullname, logs=LessonLog.query.all())
    elif role == 'counselor':
        return render_template('dashboard_counselor.html', username=user.fullname, attendances=Attendance.query.all())
    elif role == 'teacher':
        return render_template('dashboard_teacher.html', username=user.fullname)
    else:
        return redirect(url_for('home'))

@app.route('/teacher/submit-attendance', methods=['POST'])
def submit_attendance():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
    
    student_name = request.form.get('student_name')
    section_name = request.form.get('section_name')
    date = request.form.get('date')
    
    new_att = Attendance(
        student_name=student_name,
        section_name=section_name,
        teacher_name=session.get('fullname'),
        date=date,
        status='غائب'
    )
    db.session.add(new_att)
    db.session.commit()
    flash('تم إرسال ورقة الغيابات الرقمية بنجاح إلى مصلحة الاستشارة!', 'success')
    return redirect(url_for('login'))

@app.route('/teacher/submit-lesson', methods=['POST'])
def submit_lesson():
    if session.get('role') != 'teacher':
        return redirect(url_for('home'))
        
    section_name = request.form.get('section_name')
    lesson_title = request.form.get('lesson_title')
    content = request.form.get('content')
    date = request.form.get('date')
    
    new_log = LessonLog(
        teacher_name=session.get('fullname'),
        section_name=section_name,
        lesson_title=lesson_title,
        content=content,
        date=date
    )
    db.session.add(new_log)
    db.session.commit()
    flash('تم تسجيل الدرس في دفتر النصوص الرقمي بنجاح!', 'success')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
