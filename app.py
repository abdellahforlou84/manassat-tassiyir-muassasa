from flask import Flask, render_template, request, redirect, url_for, flash, session
import os

app = Flask(__name__)
# مفتاح التشفير ضروري جداً لعمل رسائل التنبيه (Flash Messages) والجلسات
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

@app.route('/')
def home():
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    # التحقق من إدخال البيانات
    if not username or not password or not role:
        flash('الرجاء ملء جميع الحقول واختيار الصفة التربوية!', 'warning')
        return redirect(url_for('home'))
    
    # حفظ بيانات الجلسة
    session['username'] = username
    session['role'] = role
    flash(f'مرحباً بك {username}، تم تسجيل الدخول بنجاح!', 'success')
    
    # التوجيه الذكي نحو لوحة التحكم المناسبة
    if role == 'director':
        return render_template('dashboard_director.html', username=username)
    elif role == 'inspector_deputy':
        return render_template('dashboard_deputy.html', username=username)
    elif role == 'counselor':
        return render_template('dashboard_counselor.html', username=username)
    elif role == 'teacher':
        return render_template('dashboard_teacher.html', username=username)
    else:
        flash('الصفة التربوية المختارة غير صالحة.', 'danger')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
