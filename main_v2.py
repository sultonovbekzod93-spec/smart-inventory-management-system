from flask import Flask, render_template_string, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- 1. БАЗАНИ СОЗЛАШ ---
def db_init():
    conn = sqlite3.connect('shifo_pro.db')
    conn.execute('CREATE TABLE IF NOT EXISTS Doctors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, spec TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS Orders (id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER, p_name TEXT, p_surname TEXT, time TEXT, date TEXT)')
    conn.commit()
    conn.close()

# --- 2. ИНТЕРФЕЙС (Янгиланган Дизайн) ---
html_kod = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Shifo</title>
    <style>
        :root { --primary: #2563eb; --secondary: #10b981; --dark: #1e293b; --light: #f8fafc; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: var(--light); margin: 0; padding: 15px; color: var(--dark); }
        .container { max-width: 500px; margin: 0 auto; }
        
        /* Юқори навигация */
        .tabs { display: flex; background: #e2e8f0; padding: 5px; border-radius: 15px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 12px; border: none; border-radius: 12px; cursor: pointer; font-weight: 600; background: transparent; transition: 0.3s; }
        .tab.active { background: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); color: var(--primary); }

        .card { background: white; border-radius: 24px; padding: 25px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); }
        h2 { margin: 0 0 20px 0; font-size: 24px; text-align: center; }

        select, input { width: 100%; padding: 14px; margin: 10px 0; border: 1.5px solid #e2e8f0; border-radius: 12px; box-sizing: border-box; font-size: 16px; outline: none; }
        select:focus, input:focus { border-color: var(--primary); }
        
        .btn { width: 100%; padding: 15px; background: var(--primary); color: white; border: none; border-radius: 12px; cursor: pointer; font-weight: bold; font-size: 16px; transition: 0.2s; }
        .btn:active { transform: scale(0.98); }

        /* Вақт жадвали */
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
        .slot { padding: 12px; border: 1.5px solid var(--primary); border-radius: 10px; cursor: pointer; color: var(--primary); text-align: center; font-weight: 600; font-size: 14px; }
        .slot.busy { background: #f1f5f9; border-color: #cbd5e1; color: #94a3b8; cursor: not-allowed; }
        .slot.past { background: #fee2e2; border-color: #fecaca; color: #ef4444; cursor: not-allowed; opacity: 0.6; }
        .slot.selected { background: var(--primary) !important; color: white !important; }

        /* Жадвал */
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { text-align: left; padding: 12px; border-bottom: 2px solid #f1f5f9; font-size: 14px; color: #64748b; }
        td { padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 15px; }
        .cancel-btn { color: #ef4444; cursor: pointer; border: none; background: none; font-size: 18px; }
    </style>
</head>
<body onload="initApp()">

<div class="container">
    <div class="tabs">
        <button class="tab active" id="t-p" onclick="showPage('p')">Бемор</button>
        <button class="tab" id="t-d" onclick="showPage('d')">Шифокор</button>
        <button class="tab" id="t-a" onclick="showPage('a')">Админ</button>
    </div>

    <div id="p-page" class="card">
        <h2>🩺 Навбат олиш</h2>
        <select id="p-select" onchange="loadSlots()">
            <option value="">Шифокорни танланг...</option>
        </select>
        <div class="grid" id="slots-grid"></div>
        <div id="p-form" style="display:none">
            <input id="p-name" placeholder="Исмингиз">
            <input id="p-surname" placeholder="Фамилиянгиз">
            <button class="btn" style="background: var(--secondary)" onclick="bookOrder()">✅ Тасдиқлаш</button>
        </div>
    </div>

    <div id="d-page" class="card" style="display:none">
        <h2>👨‍⚕️ Иш жадвали</h2>
        <select id="d-select" onchange="loadDoctorOrders()">
            <option value="">Ўз исмингизни танланг...</option>
        </select>
        <div id="d-list-content">
            <table>
                <thead><tr><th>Вақт</th><th>Бемор</th><th></th></tr></thead>
                <tbody id="orders-table"></tbody>
            </table>
        </div>
    </div>

    <div id="a-page" class="card" style="display:none">
        <h2>⚙️ Бошқарув</h2>
        <input type="password" id="admin-pass" placeholder="Админ пароли">
        <div id="admin-content" style="display:none">
            <input id="new-doc" placeholder="Янги шифокор Ф.И.Ш.">
            <button class="btn" onclick="addDoctor()">➕ Қўшиш</button>
            <div id="admin-doc-list" style="margin-top:20px"></div>
        </div>
        <button class="btn" id="pass-btn" onclick="checkPass()">Кириш</button>
    </div>
</div>

<script>
    let selTime = "";
    const ADMIN_KEY = "1234"; // Профессионал пароль
    const times = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"];

    function showPage(p) {
        document.getElementById('p-page').style.display = p=='p'?'block':'none';
        document.getElementById('d-page').style.display = p=='d'?'block':'none';
        document.getElementById('a-page').style.display = p=='a'?'block':'none';
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.getElementById('t-'+p).classList.add('active');
    }

    function checkPass() {
        if(document.getElementById('admin-pass').value === ADMIN_KEY) {
            document.getElementById('admin-content').style.display = 'block';
            document.getElementById('admin-pass').style.display = 'none';
            document.getElementById('pass-btn').style.display = 'none';
        } else { alert("Пароль хато!"); }
    }

    async function initApp() {
        let res = await fetch('/api/get_docs');
        let docs = await res.json();
        let ps = document.getElementById('p-select'), ds = document.getElementById('d-select'), al = document.getElementById('admin-doc-list');
        ps.innerHTML = ds.innerHTML = '<option value="">Танланг...</option>';
        al.innerHTML = "<b>Шифокорлар:</b>";
        docs.forEach(d => {
            let opt = `<option value="${d[0]}">${d[1]}</option>`;
            ps.innerHTML += opt; ds.innerHTML += opt;
            al.innerHTML += `<div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #f1f5f9">
                <span>${d[1]}</span><button onclick="delDoc(${d[0]})" style="color:red; border:none; background:none; cursor:pointer">🗑️</button>
            </div>`;
        });
    }

    async function loadSlots() {
        let dId = document.getElementById('p-select').value;
        if(!dId) return;
        let busy = await (await fetch('/api/get_busy/'+dId)).json();
        let grid = document.getElementById('slots-grid');
        grid.innerHTML = "";
        
        let now = new Date();
        let curTime = now.getHours() + ":" + (now.getMinutes()<10?'0':'') + now.getMinutes();

        times.forEach(t => {
            let isBusy = busy.includes(t);
            let isPast = t < curTime; // Вақт чеклов (4-функция)
            let div = document.createElement('div');
            div.className = `slot ${isBusy?'busy':''} ${isPast?'past':''}`;
            div.innerText = t;
            if(!isBusy && !isPast) div.onclick = () => {
                selTime = t;
                document.querySelectorAll('.slot').forEach(s => s.classList.remove('selected'));
                div.classList.add('selected');
                document.getElementById('p-form').style.display = 'block';
            };
            grid.appendChild(div);
        });
    }

    async function loadDoctorOrders() {
        let dId = document.getElementById('d-select').value;
        if(!dId) return;
        let orders = await (await fetch('/api/get_orders/'+dId)).json();
        let table = document.getElementById('orders-table');
        table.innerHTML = orders.length ? "" : "<tr><td colspan='3'>Навбат йўқ</td></tr>";
        orders.forEach(o => {
            table.innerHTML += `<tr><td><b>${o[4]}</b></td><td>${o[2]} ${o[3]}</td>
            <td><button class="cancel-btn" onclick="cancelOrder(${o[0]})">🚫</button></td></tr>`;
        });
    }

    async function bookOrder() {
        let dId = document.getElementById('p-select').value;
        let n = document.getElementById('p-name').value, s = document.getElementById('p-surname').value;
        if(!n || !s) return alert("Маълумотни тўлдиринг!");
        await fetch('/api/book', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({doc_id:dId, name:n, surname:s, time:selTime})});
        alert("Навбат олинди!"); location.reload();
    }

    async function cancelOrder(id) {
        if(confirm("Бекор қилинсинми?")) {
            await fetch('/api/cancel/'+id);
            loadDoctorOrders();
        }
    }

    async function addDoctor() {
        let n = document.getElementById('new-doc').value;
        await fetch('/api/add_doc', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:n})});
        document.getElementById('new-doc').value = ""; initApp();
    }

    async function delDoc(id) { if(confirm("Ўчирилсинми?")) { await fetch('/api/del_doc/'+id); initApp(); } }
</script>
</body>
</html>
"""

# --- 3. BACKEND (PYTHON) ---
@app.route('/')
def index(): return render_template_string(html_kod)

@app.route('/api/add_doc', methods=['POST'])
def add_doc():
    conn = sqlite3.connect('shifo_pro.db')
    conn.execute("INSERT INTO Doctors (name) VALUES (?)", (request.json['name'],))
    conn.commit(); conn.close(); return jsonify(True)

@app.route('/api/get_docs')
def get_docs():
    conn = sqlite3.connect('shifo_pro.db')
    res = conn.execute("SELECT * FROM Doctors").fetchall()
    conn.close(); return jsonify(res)

@app.route('/api/get_busy/<int:d_id>')
def get_busy(d_id):
    conn = sqlite3.connect('shifo_pro.db')
    res = conn.execute("SELECT time FROM Orders WHERE doc_id = ?", (d_id,)).fetchall()
    conn.close(); return jsonify([r[0] for r in res])

@app.route('/api/get_orders/<int:d_id>')
def get_orders(d_id):
    conn = sqlite3.connect('shifo_pro.db')
    res = conn.execute("SELECT * FROM Orders WHERE doc_id = ? ORDER BY time ASC", (d_id,)).fetchall()
    conn.close(); return jsonify(res)

@app.route('/api/book', methods=['POST'])
def book():
    d = request.json
    conn = sqlite3.connect('shifo_pro.db')
    conn.execute("INSERT INTO Orders (doc_id, p_name, p_surname, time) VALUES (?,?,?,?)", (d['doc_id'], d['name'], d['surname'], d['time']))
    conn.commit(); conn.close(); return jsonify(True)

@app.route('/api/cancel/<int:id>')
def cancel(id):
    conn = sqlite3.connect('shifo_pro.db')
    conn.execute("DELETE FROM Orders WHERE id = ?", (id,))
    conn.commit(); conn.close(); return jsonify(True)

@app.route('/api/del_doc/<int:id>')
def del_doc(id):
    conn = sqlite3.connect('shifo_pro.db')
    conn.execute("DELETE FROM Doctors WHERE id = ?", (id,))
    conn.execute("DELETE FROM Orders WHERE doc_id = ?", (id,))
    conn.commit(); conn.close(); return jsonify(True)

if __name__ == '__main__':
    db_init()
    app.run(host='0.0.0.0', port=5000)
