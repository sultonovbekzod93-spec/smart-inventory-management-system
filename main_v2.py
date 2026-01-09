from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'bank_maxfiy_kalit_999' 

# 1. МАЪЛУМОТЛАР БАЗАСИНИ СОЗЛАШ
def get_db_connection():
    conn = sqlite3.connect('test_employees.db')
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS Employees 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT NOT NULL, 
                     department TEXT NOT NULL, 
                     salary INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

# 2. ВАЛИДАЦИЯ (МАЪЛУМОТЛАРНИ ТЕКШИРИШ)
def validate_employee_data(name, dept, salary_str):
    messages = []
    if not name or not dept:
        messages.append("Исм ва Бўлим мажбурий майдонлардир.")
    try:
        salary = int(salary_str)
        if salary <= 0:
            messages.append("Ойлик мусбат сон бўлиши керак.")
    except (ValueError, TypeError):
        messages.append("Ойлик фақат сон бўлиши керак.")
        salary = None 
    return messages, salary

# 3. ЛОГИН САҲИФАСИ (HTML)
login_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Кириш - Банк Тизими</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 300px; text-align: center; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .err { color: #e74c3c; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🏦 Банк Тизими</h2>
        {% for category, message in get_flashed_messages(with_categories=true) %}
            <p class="err">{{ message }}</p>
        {% endfor %}
        <form method="POST">
            <input type="text" name="u" placeholder="Логин (1)" required>
            <input type="password" name="p" placeholder="Пароль (1)" required>
            <button type="submit">КИРИШ</button>
        </form>
    </div>
</body>
</html>
"""

# 4. АСОСИЙ САҲИФА (HTML)
main_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Банк Бошқаруви</title>
    <style>
        body { font-family: sans-serif; background: #f4f7f6; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .form-section { display: flex; gap: 20px; margin: 20px 0; }
        .box { flex: 1; padding: 15px; border-radius: 8px; border: 1px solid #ddd; }
        input { padding: 8px; margin: 5px 0; width: 90%; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px; border: none; border-radius: 4px; cursor: pointer; color: white; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
        th { background: #3498db; color: white; }
        .flash-error { color: red; } .flash-success { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🏦 Банк Ходимлари</h2>
            <a href="/logout" style="color: red; text-decoration: none;">🚪 Чиқиш</a>
        </div>

        {% for category, message in get_flashed_messages(with_categories=true) %}
            <p class="flash-{{ category }}">{{ message }}</p>
        {% endfor %}

        <div class="form-section">
            <div class="box" style="background: #e8ecef;">
                <h4>➕ Қўшиш</h4>
                <form method="POST">
                    <input type="text" name="name" placeholder="Исм" required>
                    <input type="text" name="dept" placeholder="Бўлим" required>
                    <input type="number" name="salary" placeholder="Ойлик" required>
                    <button type="submit" style="background: #27ae60; width: 100%;">Сақлаш</button>
                </form>
            </div>
            <div class="box" style="background: #d1ecf1;">
                <h4>🔍 Қидириш</h4>
                <form method="GET">
                    <input type="text" name="search" placeholder="Исм ёки бўлим..." value="{{ sq }}">
                    <button type="submit" style="background: #17a2b8; width: 100%;">Қидириш</button>
                    <a href="/" style="display:block; text-align:center; margin-top:5px; color:#666; font-size:12px;">Тозалаш</a>
                </form>
            </div>
        </div>

        <table>
            <tr><th>ID</th><th>Исм</th><th>Бўлим</th><th>Ойлик</th><th>Амаллар</th></tr>
            {% for row in employees %}
            <tr>
                <td>{{ row['id'] }}</td>
                <td><b>{{ row['name'] }}</b></td>
                <td>{{ row['department'] }}</td>
                <td>{{ "{:,.0f}".format(row['salary']) }} сўм</td>
                <td>
                    <a href="{{ url_for('edit', eid=row['id']) }}">✍️</a> | 
                    <a href="{{ url_for('delete', eid=row['id']) }}" onclick="return confirm('Ўчирилсинми?')">❌</a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# 5. ЙЎНАЛИШЛАР (BACKEND)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # .strip().lower() - хатоликни олдини олади
        u = request.form.get('u').strip().lower()
        p = request.form.get('p').strip().lower()
        if u == '1' and p == '1':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Логин ёки пароль хато!', 'error')
    return render_template_string(login_html)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    sq = request.args.get('search', '')

    if request.method == 'POST':
        name, dept, sal_s = request.form['name'], request.form['dept'], request.form['salary']
        errs, salary = validate_employee_data(name, dept, sal_s)
        if errs:
            for e in errs: flash(e, 'error')
        else:
            conn.execute('INSERT INTO Employees (name, department, salary) VALUES (?,?,?)', (name, dept, salary))
            conn.commit()
            flash(f"{name} қўшилди!", 'success')
        conn.close()
        return redirect('/')

    if sq:
        emps = conn.execute("SELECT * FROM Employees WHERE name LIKE ? OR department LIKE ?", ('%'+sq+'%', '%'+sq+'%')).fetchall()
    else:
        emps = conn.execute("SELECT * FROM Employees").fetchall()
    conn.close()
    return render_template_string(main_html, employees=emps, sq=sq)

@app.route('/delete/<int:eid>')
def delete(eid):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM Employees WHERE id = ?', (eid,))
    conn.commit(); conn.close()
    flash("Ўчирилди!", "success")
    return redirect('/')

@app.route('/edit/<int:eid>', methods=['GET', 'POST'])
def edit(eid):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    emp = conn.execute('SELECT * FROM Employees WHERE id = ?', (eid,)).fetchone()
    if request.method == 'POST':
        n, d, s_s = request.form['name'], request.form['dept'], request.form['salary']
        errs, salary = validate_employee_data(n, d, s_s)
        if not errs:
            conn.execute('UPDATE Employees SET name=?, department=?, salary=? WHERE id=?', (n, d, salary, eid))
            conn.commit(); conn.close()
            return redirect('/')
    conn.close()
    return render_template_string("<h3>Таҳрирлаш</h3><form method='POST'><input name='name' value='{{e.name}}'><br><input name='dept' value='{{e.department}}'><br><input name='salary' value='{{e.salary}}'><br><button>Янгилаш</button></form>", e=emp)

if __name__ == '__main__':
    db_init()
    app.run(host='0.0.0.0', port=5000, debug=True)
    
