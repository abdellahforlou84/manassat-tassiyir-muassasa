from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

@app.route('/')
def home():
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    # توجيه ذكي حسب الدور التربوي المختار
    if role == 'director':
        return render_template('dashboard_director.html', username=username)
    elif role == 'inspector_deputy':
        return render_template('dashboard_deputy.html', username=username)
    elif role == 'counselor':
        return render_template('dashboard_counselor.html', username=username)
    elif role == 'teacher':
        return render_template('dashboard_teacher.html', username=username)
    else:
        return "الرجاء تحديد الصفة التربوية بدقة", 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
