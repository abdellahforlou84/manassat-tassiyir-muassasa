from flask import Flask, request, render_template_string, session, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'manassat_tassiyir_muassasa_secret_key_2026'

# واجهة تسجيل الدخول المصممة خصيصاً لمنصة تسيير المؤسسة (مدمجة بالكامل لضمان الظهور الفوري)
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
        <div class="text-center mb-8">
            <h1 class="text-2xl font-bold text-gray-800">منصة تسيير المؤسسة</h1>
            <p class="text-sm text-gray-500 mt-2">الرجاء إدخال بيانات الدخول واختيار الصفة التربوية</p>
        </div>

        <form action="/login" method="POST" class="space-y-5">
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">اسم المستخدم</label>
                <input type="text" name="username" required class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">كلمة المرور</label>
                <input type="password" name="password" required class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition">
            </div>

            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">الصفة التربوية (الدور)</label>
                <select name="role" required class="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:outline-none transition bg-white">
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
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    role = request.form.get('role')
    
    # واجهة لوحة التحكم المؤقتة والمنظمة لكل دور تربوي
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Cairo', sans-serif; }}</style>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center p-6">
        <div class="bg-white rounded-2xl shadow-xl p-8 max-w-lg w-full text-center border-t-8 border-blue-600">
            <h1 class="text-2xl font-bold text-gray-800 mb-2">أهلاً بك، {username}</h1>
            <p class="text-blue-600 font-semibold mb-6">تم تسجيل الدخول بنجاح بصفتك: <span class="underline">{role}</span></p>
            <div class="bg-blue-50 p-4 rounded-lg text-gray-600 mb-6 text-sm">
                لوحة التحكم الخاصة بك جاهزة تماماً لإدارة شؤون المؤسسة التربوية.
            </div>
            <a href="/" class="inline-block bg-slate-900 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-slate-800 transition">العودة لتسجيل الخروج</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
