from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "smart_ombor_pro_v4_2026"

# 1. МАЪЛУМОТЛАР БАЗАСИ
def get_db_connection():
    conn = sqlite3.connect('smart_ombor_v4.db')
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS Mahsulotlar (id INTEGER PRIMARY KEY AUTOINCREMENT, nomi TEXT UNIQUE, miqdori INTEGER, narhi INTEGER)')
    conn.execute('CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
    if not conn.execute('SELECT * FROM Users WHERE username = ?', ('admin',)).fetchone():
        conn.execute('INSERT INTO Users (username, password) VALUES (?, ?)', ('admin', generate_password_hash('1')))
    conn.commit()
    conn.close()

# 2. ЯНГИЛАНГАН PRO ДИЗАЙН (HTML + CSS)
PRO_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f0f4f8; margin: 0; padding: 10px; }
        .app-card { width: 100%; max-width: 480px; background: white; border-radius: 25px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin: auto; }
        
        /* Юқори қисм ва Чиқиш тугмаси */
        .top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .title { color: #1a73e8; font-size: 22px; font-weight: bold; margin: 0; }
        .logout-link { color: #d93025; text-decoration: none; font-weight: bold; font-size: 14px; padding: 5px 10px; border: 1px solid #fad2cf; border-radius: 8px; background: #fff1f1; }

        /* Статистика */
        .stats { display: flex; gap: 10px; margin-bottom: 20px; }
        .stat-box { flex: 1; background: #eef5ff; padding: 12px; border-radius: 15px; text-align: center; border: 1px solid #d0e3ff; }
        .stat-label { font-size: 10px; color: #777; text-transform: uppercase; }
        .stat-val { font-size: 15px; font-weight: bold; color: #1a73e8; display: block; margin-top: 4px; }

        /* Маълумот киритиш */
        .input-group { background: #f8f9fa; padding: 15px; border-radius: 18px; margin-bottom: 20px; }
        input { width: 100%; padding: 12px; margin-bottom: 8px; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; outline: none; }
        .btn-add { width: 100%; padding: 14px; background: #28a745; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; }

        /* Жадвал */
        table { width: 100%; border-collapse: collapse; }
        th { background: #1a73e8; color: white; padding: 10px; font-size: 13px; text-align: center; }
        th:first-child { border-radius: 10px 0 0 0; }
        th:last-child { border-radius: 0 10px 0 0; }
        td { padding: 12px 8px; text-align: center; border-bottom: 1px solid #eee; font-size: 14px; }
        
        /* Тугмачалар */
        .action-btns { display: flex; gap: 5px; justify-content: center; }
        .btn-sell { background: #ff9800; color: white; border: none; padding: 8px; border-radius: 8px; cursor: pointer; }
        .btn-del { background: #f44336; color: white; border: none; padding: 8px; border-radius: 8px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="app-card">
        <div class="top-bar">
            <h1 class="title">📦 Smart Ombor PRO</h1>
            <a href="/logout" class="logout-link">🚪 Чиқиш</a>
        </div>

        <div class="stats">
            <div class="stat-box"><span class="stat-label">Жами товар</span><span id="st-qty" class="stat-val">0 та</span></div>
            <div class="stat-box"><span class="stat-label">Умумий қиймат</span><span id="st-sum" class="stat-val">0 сўм</span></div>
        </div>

        <div class="input-group">
            <input type="text" id="m-nomi" placeholder="Маҳсулот номи">
            <input type="number" id="m-soni" placeholder="Миқдори">
            <input type="number" id="m-narhi" placeholder="Нарҳи (сўм)">
            <button class="btn-add" onclick="qoshish()">➕ ОМБОРГА ҚЎШИШ</button>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Номи</th>
                    <th>Қолдиқ</th>
                    <th>Нарх</th>
                    <th>Амал</th>
                </tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
    </div>

    <script>
        async function yuklash() {
            let res = await fetch('/api/mahsulotlar');
            let data = await res.json();
            let h = ""; let q = 0; let s = 0;
            data.forEach(m => {
                h += `<tr>
                    <td><b>${m.nomi}</b></td>
                    <td>${m.miqdori} та</td>
                    <td>${Number(m.narhi).toLocaleString()}</td>
                    <td class="action-btns">
                        <button class="btn-sell" onclick="sotish(${m.id})" title="Сотиш">🛒</button>
                        <button class="btn-del" onclick="uchirish(${m.id})" title="Ўчириш">🗑️</button>
                    </td>
                </tr>`;
                q += Number(m.miqdori);
                s += (Number(m.miqdori) * Number(m.narhi));
            });
            document.getElementById('table-body').innerHTML = h;
            document.getElementById('st-qty').innerText = q + " та";
            document.getElementById('st-sum').innerText = s.toLocaleString() + " сўм";
        }

        async function qoshish() {
            let n = document.getElementById('m-nomi').value.trim();
            let s = document.getElementById('m-soni').value;
            let p = document.getElementById('m-narhi').value;
            if(!n || s <= 0 || p <= 0) return alert("Тўғри тўлдиринг!");
            await fetch('/api/qoshish', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({nomi: n, miqdori: s, narhi: p})
            });
            yuklash(); document.querySelectorAll('input').forEach(i => i.value='');
        }

        async function sotish(id) {
            let s = prompt("Қанча сотмоқчисиз?");
            if(!s || s <= 0) return;
            let res = await fetch('/api/sotish', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id, miqdori: s})
            });
            let data = await res.json();
            if(!data.ok) alert(data.msg);
            yuklash();
        }

        async function uchirish(id) {
            if(confirm("Ўчирилсинми?")) { await fetch('/api/uchirish/'+id, {method:'POST'}); yuklash(); }
        }
        window.onload = yuklash;
    </script>
</body>
</html>
"""

# 3. BACKEND (ЛОГИКА)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u', '').strip(), request.form.get('p', '').strip()
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ?', (u,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], p):
            session['auth'] = True
            return redirect(url_for('index'))
        flash("Хато!")
    return render_template_string("""
        <div style="max-width:300px; margin:100px auto; text-align:center;">
            <h2>📦 Smart Ombor</h2>
            <form method="POST">
                <input name="u" placeholder="Логин" style="width:100%; padding:10px; margin:5px 0;">
                <input type="password" name="p" placeholder="Пароль" style="width:100%; padding:10px; margin:5px 0;">
                <button type="submit" style="width:100%; padding:10px; background:#1a73e8; color:white; border:none;">КИРИШ</button>
            </form>
        </div>
    """)

@app.route('/')
def index():
    if not session.get('auth'): return redirect(url_for('login'))
    return render_template_string(PRO_HTML)

@app.route('/api/mahsulotlar')
def get_m():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM Mahsulotlar").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/qoshish', methods=['POST'])
def qosh():
    d = request.json
    conn = get_db_connection()
    check = conn.execute("SELECT id FROM Mahsulotlar WHERE nomi = ?", (d['nomi'],)).fetchone()
    if check:
        conn.execute("UPDATE Mahsulotlar SET miqdori = miqdori + ? WHERE id = ?", (d['miqdori'], check['id']))
    else:
        conn.execute("INSERT INTO Mahsulotlar (nomi, miqdori, narhi) VALUES (?, ?, ?)", (d['nomi'], d['miqdori'], d['narhi']))
    conn.commit(); conn.close(); return jsonify({"ok": True})

@app.route('/api/sotish', methods=['POST'])
def sotish():
    d = request.json
    conn = get_db_connection()
    m = conn.execute("SELECT miqdori FROM Mahsulotlar WHERE id = ?", (d['id'],)).fetchone()
    if m and m['miqdori'] >= int(d['miqdori']):
        conn.execute("UPDATE Mahsulotlar SET miqdori = miqdori - ? WHERE id = ?", (d['miqdori'], d['id']))
        conn.commit(); conn.close(); return jsonify({"ok": True})
    conn.close(); return jsonify({"ok": False, "msg": "Омборда етарли товар йўқ!"})

@app.route('/api/uchirish/<int:m_id>', methods=['POST'])
def uchirish(m_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Mahsulotlar WHERE id = ?", (m_id,)); conn.commit(); conn.close(); return jsonify({"ok": True})

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

if __name__ == '__main__':
    db_init()
    app.run(host='0.0.0.0', port=5000)
    
