from flask import Flask, jsonify, render_template_string, request
import pandas as pd
import sqlite3
import os

app = Flask(__name__)

DB_NAME = 'philo_school_manager.db'
EXCEL_FILE = 'قوائم التلاميذ.xlsx'

# --- 1. إعداد قاعدة البيانات والجداول ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول الأقسام
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # جدول الأساتذة
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # جدول إسناد الأقسام للأساتذة (العلاقة بين الأستاذ وأقسامه)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teacher_classes (
        teacher_id INTEGER,
        class_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES teachers (id),
        FOREIGN KEY (class_id) REFERENCES classes (id),
        PRIMARY KEY (teacher_id, class_id)
    )
    ''')
    
    # جدول التلاميذ
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        class_id INTEGER,
        FOREIGN KEY (class_id) REFERENCES classes (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# --- 2. استيراد البيانات من ملف الإكسل إلى قاعدة البيانات ---
def import_excel_to_db(filepath):
    if not os.path.exists(filepath):
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    xls = pd.ExcelFile(filepath)
    for sheet in xls.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet)
        if df.empty:
            continue
        
        current_class = None
        for idx, row in df.iterrows():
            row_str = str(row.values[0])
            
            # التقاط اسم القسم
            if 'القسم:' in row_str or 'القسم' in row_str:
                parts = row_str.split('القسم')
                if len(parts) > 1:
                    current_class = parts[-1].replace(':', '').strip()
                    if current_class:
                        cursor.execute('INSERT OR IGNORE INTO classes (class_name) VALUES (?)', (current_class,))
            
            # التقاط بيانات التلاميذ وإضافتهم للقسم
            val_no = row.values[0]
            try:
                if pd.notna(val_no) and str(val_no).strip().isdigit() and current_class:
                    last_name = str(row.values[1]).strip() if pd.notna(row.values[1]) else ""
                    first_name = str(row.values[2]).strip() if pd.notna(row.values[2]) else ""
                    if last_name or first_name:
                        full_name = f"{last_name} {first_name}".strip()
                        
                        # جلب معرف القسم
                        cursor.execute('SELECT id FROM classes WHERE class_name = ?', (current_class,))
                        cls_row = cursor.fetchone()
                        if cls_row:
                            cls_id = cls_row[0]
                            cursor.execute('''
                                INSERT INTO students (student_name, class_id) 
                                SELECT ?, ? WHERE NOT EXISTS 
                                (SELECT 1 FROM students WHERE student_name = ? AND class_id = ?)
                            ''', (full_name, cls_id, full_name, cls_id))
            except:
                pass
                
    conn.commit()
    conn.close()

# --- 3. الواجهة الأمامية المتكاملة (HTML + JavaScript) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Philo School Manager - تسيير الأقسام والتلاميذ</title>
    <style>
        body { font-family: Tahoma, Arial, sans-serif; margin: 30px; background: #f4f7f6; color: #333; }
        .container { max-width: 750px; margin: auto; }
        .card { background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 20px; }
        h2 { color: #2c3e50; text-align: center; margin-bottom: 25px; }
        label { font-weight: bold; display: block; margin-bottom: 10px; color: #2c3e50; }
        select, input[type="text"] { width: 100%; padding: 12px; font-size: 16px; border-radius: 6px; border: 1px solid #ccc; margin-bottom: 15px; background: #fff; }
        .checkbox-container { display: flex; flex-wrap: wrap; gap: 10px; max-height: 180px; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 6px; background: #fafafa; margin-bottom: 15px; }
        .checkbox-label { background: #eef2f7; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 14px; display: flex; align-items: center; gap: 5px; }
        .btn { background: #3498db; color: white; border: none; padding: 10px 20px; font-size: 15px; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .student-count { color: #555; font-size: 14px; font-weight: bold; margin-top: 10px; }
    </style>
</head>
<body>

<div class="container">
    <h2>منصة تسيير الأقسام والنتائج - أستاذ الفلسفة</h2>

    <!-- بيانات الأستاذ -->
    <div class="card">
        <label for="teacherName">اسم الأستاذ:</label>
        <input type="text" id="teacherName" placeholder="أدخل اسمك الكريم (مثال: أستاذ الفلسفة)" value="أستاذ الفلسفة">
        
        <label>حدد أقسامك المُسندة إليك (من إجمالي الأقسام):</label>
        <div id="allClassesCheckboxes" class="checkbox-container">
            جاري تحميل الأقسام...
        </div>
        <button class="btn" onclick="saveTeacherAssignments()">حفظ إسناد الأقسام</button>
    </div>

    <!-- استعراض الأقسام والتلاميذ -->
    <div class="card">
        <label for="teacherClassSelect">اختر القسم المطلوب استعراضه (أقسامك المسندة فقط):</label>
        <select id="teacherClassSelect" onchange="loadStudentsForClass()">
            <option value="">-- اختر القسم --</option>
        </select>

        <label for="studentsSelect">قائمة تلاميذ القسم المختار:</label>
        <select id="studentsSelect">
            <option value="">-- اختر التلميذ --</option>
        </select>
        <div id="studentCount" class="student-count"></div>
    </div>
</div>

<script>
    let allSchoolClasses = [];

    // تحميل جميع أقسام المدرسة عند فتح الصفحة
    window.onload = function() {
        fetch('/api/classes')
            .then(res => res.json())
            .then(classes => {
                allSchoolClasses = classes;
                const container = document.getElementById('allClassesCheckboxes');
                container.innerHTML = '';
                classes.forEach(cls => {
                    const wrapper = document.createElement('label');
                    wrapper.className = 'checkbox-label';
                    wrapper.innerHTML = `<input type="checkbox" value="${cls}" class="class-chk"> ${cls}`;
                    container.appendChild(wrapper);
                });
                loadTeacherAssignedClasses();
            });
    };

    // حفظ إسناد الأقسام للأستاذ في قاعدة البيانات
    function saveTeacherAssignments() {
        const teacherName = document.getElementById('teacherName').value.trim();
        const checkedBoxes = document.querySelectorAll('.class-chk:checked');
        const selectedClasses = Array.from(checkedBoxes).map(cb => cb.value);

        if (!teacherName) {
            alert('الرجاء إدخال اسم الأستاذ');
            return;
        }

        fetch('/api/save-assignment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ teacher_name: teacherName, classes: selectedClasses })
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            loadTeacherAssignedClasses();
        });
    }

    // جلب الأقسام المسندة للأستاذ الحالي لتعبئة القائمة المنسدلة
    function loadTeacherAssignedClasses() {
        const teacherName = document.getElementById('teacherName').value.trim();
        fetch(`/api/teacher-classes?teacher_name=${encodeURIComponent(teacherName)}`)
            .then(res => res.json())
            .then(assignedClasses => {
                const classSelect = document.getElementById('teacherClassSelect');
                classSelect.innerHTML = '<option value="">-- اختر القسم --</option>';
                
                assignedClasses.forEach(cls => {
                    const opt = document.createElement('option');
                    opt.value = cls;
                    opt.textContent = `قسم: ${cls}`;
                    classSelect.appendChild(opt);
                });
            });
    }

    // جلب تلاميذ القسم المختار حصراً
    function loadStudentsForClass() {
        const className = document.getElementById('teacherClassSelect').value;
        const studentsSelect = document.getElementById('studentsSelect');
        studentsSelect.innerHTML = '<option value="">-- اختر التلميذ --</option>';
        document.getElementById('studentCount').textContent = '';

        if (!className) return;

        fetch(`/api/students?class_name=${encodeURIComponent(className)}`)
            .then(res => res.json())
            .then(students => {
                students.forEach(st => {
                    const opt = document.createElement('option');
                    opt.value = st;
                    opt.textContent = st;
                    studentsSelect.appendChild(opt);
                });
                document.getElementById('studentCount').textContent = `إجمالي عدد التلاميذ في هذا القسم: ${students.length} تلميذ`;
            });
    }
</script>

</body>
</html>
"""

# --- 4. مسارات الـ API الخاصة بـ Flask ---
@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/classes', methods=['GET'])
def get_classes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT class_name FROM classes')
    rows = cursor.fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])

@app.route('/api/save-assignment', methods=['POST'])
def save_assignment():
    data = request.json
    teacher_name = data.get('teacher_name')
    classes = data.get('classes', [])
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # إضافة أو جلب الأستاذ
    cursor.execute('INSERT OR IGNORE INTO teachers (teacher_name) VALUES (?)', (teacher_name,))
    cursor.execute('SELECT id FROM teachers WHERE teacher_name = ?', (teacher_name,))
    teacher_id = cursor.fetchone()[0]
    
    # حذف الإسنادات القديمة لهذا الأستاذ لتحديثها
    cursor.execute('DELETE FROM teacher_classes WHERE teacher_id = ?', (teacher_id,))
    
    # إضافة الإسنادات الجديدة
    for cls_name in classes:
        cursor.execute('SELECT id FROM classes WHERE class_name = ?', (cls_name,))
        cls_row = cursor.fetchone()
        if cls_row:
            cls_id = cls_row[0]
            cursor.execute('INSERT INTO teacher_classes (teacher_id, class_id) VALUES (?, ?)', (teacher_id, cls_id))
            
    conn.commit()
    conn.close()
    return jsonify({'message': 'تم حفظ الإسناد بنجاح!'})

@app.route('/api/teacher-classes', methods=['GET'])
def get_teacher_classes():
    teacher_name = request.args.get('teacher_name', '')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.class_name FROM classes c
        JOIN teacher_classes tc ON c.id = tc.class_id
        JOIN teachers t ON tc.teacher_id = t.id
        WHERE t.teacher_name = ?
    ''', (teacher_name,))
    
    rows = cursor.fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])

@app.route('/api/students', methods=['GET'])
def get_students():
    class_name = request.args.get('class_name', '')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.student_name FROM students s
        JOIN classes c ON s.class_id = c.id
        WHERE c.class_name = ?
    ''', (class_name,))
    
    rows = cursor.fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])

if __name__ == '__main__':
    # تهيئة قاعدة البيانات واستيراد ملف الإكسل تلقائياً عند التشغيل الأول
    init_db()
    import_excel_to_db(EXCEL_FILE)
    app.run(debug=True, port=5000)
