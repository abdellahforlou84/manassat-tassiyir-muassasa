from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# مفتاح الأمان للجلسات (أمان التطبيق)
app.secret_key = 'philo_school_manager_secret_key_2026'

# الصفحة الرئيسية (توجه مباشرة نحو صفحة المصادقة/تسجيل الدخول)
@app.route('/')
def home():
    return render_template('auth.html')

# مسار معالجة تسجيل الدخول حسب الصلاحيات (مدير، ناظر، مستشار، أستاذ)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role') # اختيار الدور من الواجهة
    
    # نموذج توجيه أولي حسب الدور
    if role == 'director':
        return "مرحباً بك في لوحة تحكم المدير (التسيير الشامل)"
    elif role == 'inspector_deputy':
        return "مرحباً بك في لوحة تحكم الناظر (التنسيق البيداغوجي)"
    elif role == 'counselor':
        return "مرحباً بك في لوحة الاستشارة والغيابات اليومية"
    elif role == 'teacher':
        return "مرحباً بك في بوابة الأساتذة (ورقة الغيابات الرقمية)"
    else:
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
