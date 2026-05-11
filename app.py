from flask import Flask, render_template, request, session, redirect, jsonify, flash
import qrcode
import os
import uuid
import sqlite3
import midtransclient
import math
from datetime import datetime
from functools import wraps
import logging

# Import configuration
from config import (
    SECRET_KEY, DEBUG, TICKET_PRICE, OFFICE_LAT, OFFICE_LNG, OFFICE_RADIUS,
    MIDTRANS_SERVER_KEY, MIDTRANS_CLIENT_KEY, MIDTRANS_IS_PRODUCTION,
    BASE_URL, PROMO_CODES, DEFAULT_USERS, PARK_NAME, PARK_ADDRESS, PARK_PHONE
)

# Setup Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.debug = DEBUG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Midtrans
try:
    snap = midtransclient.Snap(
        is_production=MIDTRANS_IS_PRODUCTION,
        server_key=MIDTRANS_SERVER_KEY
    )
    logger.info("Midtrans configured successfully")
except Exception as e:
    logger.warning(f"Midtrans not configured: {e}")
    snap = None

# ================= DATABASE =================

def get_db():
    # Use /tmp for Vercel serverless (ephemeral but writable)
    # Use local file for development
    import sys
    if 'vercel' in sys.executable.lower() or os.environ.get('VERCEL'):
        db_path = '/tmp/database.db'
    else:
        db_path = 'database.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            nama TEXT,
            jumlah INTEGER,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            nama_lengkap TEXT,
            email TEXT,
            no_hp TEXT,
            created_at TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS absensi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            tanggal TEXT,
            jam TEXT,
            jarak REAL,
            status TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wahana (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            deskripsi TEXT,
            emoji TEXT,
            kategori TEXT,
            status TEXT,
            wait_time INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def migrate_db():
    conn = get_db()
    columns = ['nama_lengkap', 'email', 'no_hp', 'created_at']
    for col in columns:
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except:
            pass
    try:
        conn.execute("ALTER TABLE tickets ADD COLUMN created_at TEXT")
    except:
        pass
    conn.commit()
    conn.close()

def create_default_users():
    conn = get_db()
    for username, data in DEFAULT_USERS.items():
        existing = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, data['password'], data['role'])
            )
    conn.commit()
    conn.close()

def create_wahana():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) FROM wahana").fetchone()[0]
    if existing == 0:
        wahana_data = [
            ('Roller Coaster', 'Sensasi多人terbang yang mendancurkan', '🎢', 'dry', 'available', 15),
            ('Carousel', 'Wahana klasik favorit keluarga', '🎠', 'dry', 'available', 5),
            ('Ferris Wheel', 'Pemandangan kota dari atas', '🎡', 'dry', 'available', 20),
            ('Boat Ride', 'Petualangan danau dengan boat', '🛶', 'dry', 'available', 10),
            ('House of Horror', 'Rumah horor dengan efek especial', '🎪', 'indoor', 'available', 30),
            ('Fun House', 'Playground dalam ruangan', '🏰', 'indoor', 'available', 0),
            ('Arcade Zone', 'Game center dengan berbagai mesin', '🎯', 'indoor', 'available', 5),
            ('Water Boom', 'Kolam air dengan seluncur', '🌊', 'water', 'maintenance', 25),
        ]
        for nama, deskripsi, emoji, kategori, status, wait_time in wahana_data:
            conn.execute(
                "INSERT INTO wahana (nama, deskripsi, emoji, kategori, status, wait_time) VALUES (?, ?, ?, ?, ?, ?)",
                (nama, deskripsi, emoji, kategori, status, wait_time)
            )
        conn.commit()
    conn.close()

init_db()
migrate_db()
create_default_users()
create_wahana()

# ================= HELPER FUNCTIONS =================

def hitung_jarak(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ================= ROUTES: PUBLIC =================

@app.route('/')
def home():
    return render_template('public/index.html')

@app.route('/explore')
def explore():
    conn = get_db()
    wahana = conn.execute("SELECT * FROM wahana").fetchall()
    conn.close()
    return render_template('public/explore.html', wahana=wahana)

@app.route('/gallery')
def gallery():
    return render_template('public/gallery.html')

# ================= ROUTES: AUTH =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('auth/login.html', error="Mohon isi semua Field!")
        
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()
        
        if user:
            session['user'] = user['username']
            session['role'] = user['role']
            
            # Set welcome message based on role
            if user['role'] == 'admin':
                session['welcome'] = f"Halo Admin {user['username']}! 👑"
            elif user['role'] == 'employee':
                session['welcome'] = f"Halo {user['username']}! 👨‍💼"
            else:
                session['welcome'] = f"Halo {user['username']}! 🎡"
            
            # Redirect based on role
            if user['role'] == 'admin':
                return redirect('/admin')
            elif user['role'] == 'employee':
                return redirect('/absensi')
            else:
                return redirect('/ticket')
        
        return render_template('auth/login.html', error="Username atau password salah!")
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        email = request.form.get('email', '').strip()
        no_hp = request.form.get('no_hp', '').strip()
        
        if not username or not password or not nama_lengkap:
            return render_template('auth/register.html', error="Mohon isi semua Field wajib!")
        
        conn = get_db()
        existing = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        
        if existing:
            conn.close()
            return render_template('auth/register.html', error="Username sudah digunakan!")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute(
            "INSERT INTO users (username, password, role, nama_lengkap, email, no_hp, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, password, 'user', nama_lengkap, email, no_hp, now)
        )
        conn.commit()
        conn.close()
        
        session['user'] = username
        session['role'] = 'user'
        
        return redirect('/ticket')
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= ROUTES: TICKET (USER ONLY) =================

@app.route('/ticket', methods=['GET', 'POST'])
def ticket():
    # ONLY for regular users
    if session.get('role') == 'admin':
        return redirect('/admin')
    if session.get('role') == 'employee':
        return redirect('/absensi')
    if not session.get('user'):
        return redirect('/login?next=/ticket')
    
    if request.method == 'POST':
        nama = session.get('user')
        jumlah = int(request.form.get('jumlah', 1))
        kode_promo = request.form.get('kode_promo', '').upper()
        
        if not nama or jumlah < 1:
            return render_template('public/ticket.html', error="Mohon isi data dengan benar!")
        
        # Calculate price with promo
        diskon = PROMO_CODES.get(kode_promo, 0)
        total_harga = jumlah * TICKET_PRICE
        if diskon > 0:
            total_harga = int(total_harga * (100 - diskon) / 100)
        
        ticket_id = str(uuid.uuid4())
        
        session['nama'] = nama
        session['jumlah'] = jumlah
        session['ticket_id'] = ticket_id
        
        # Try Midtrans payment
        if snap:
            try:
                transaction = {
                    "transaction_details": {
                        "order_id": ticket_id,
                        "gross_amount": total_harga
                    },
                    "customer_details": {
                        "first_name": nama
                    },
                    "callbacks": {
                        "finish": f"{BASE_URL}/success"
                    }
                }
                snap_token = snap.create_transaction(transaction)
                return render_template('public/payment.html', snap_token=snap_token['token'])
            except Exception as e:
                logger.error(f"Midtrans error: {e}")
                return render_template('public/ticket.html', error="Payment unavailable. Coba lagi!")
        
        return render_template('public/ticket.html', error="Payment system unavailable!")
    
    return render_template('public/ticket.html')

@app.route('/success')
def success():
    # ONLY for regular users
    if session.get('role') in ['admin', 'employee']:
        return redirect('/')
    
    username = session.get('user', '')
    jumlah = session.get('jumlah', 1)
    ticket_id = session.get('ticket_id') or str(uuid.uuid4())
    
    conn = get_db()
    user = conn.execute("SELECT nama_lengkap FROM users WHERE username=?", (username,)).fetchone()
    
    if user and user['nama_lengkap']:
        nama = user['nama_lengkap']
    else:
        nama = username
    
    # Save ticket to database
    existing = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO tickets (id, nama, jumlah, status) VALUES (?, ?, ?, ?)",
            (ticket_id, username, jumlah, 'valid')
        )
        conn.commit()
    
    # Generate QR as base64 (no file write needed)
    import io
    import base64
    qr_data = f"{BASE_URL}/verify/{ticket_id}"
    qr = qrcode.make(qr_data)
    
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    # Clear session
    session.pop('ticket_id', None)
    session.pop('nama', None)
    
    return render_template(
        'public/qr_result.html',
        nama=nama,
        jumlah=jumlah,
        qr_image=f"data:image/png;base64,{qr_base64}",
        username=username
    )

@app.route('/verify/<ticket_id>')
def verify(ticket_id):
    conn = get_db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    
    if not ticket:
        return render_template('public/verify_fail.html', message="Tiket tidak ditemukan!")
    
    if ticket['status'] == 'used':
        return render_template('public/verify_fail.html', message="Tiket sudah digunakan!")
    
    conn.execute("UPDATE tickets SET status='used' WHERE id=?", (ticket_id,))
    conn.commit()
    
    user = conn.execute("SELECT nama_lengkap FROM users WHERE username=?", (ticket['nama'],)).fetchone()
    nama = user['nama_lengkap'] if user and user['nama_lengkap'] else ticket['nama']
    
    conn.close()
    
    return render_template('public/verify_success.html', nama=nama)

@app.route('/my-tickets')
def my_tickets():
    if not session.get('user'):
        return redirect('/login?next=/my-tickets')
    
    if session.get('role') in ['admin', 'employee']:
        return redirect('/')
    
    username = session.get('user')
    
    conn = get_db()
    tickets = conn.execute(
        "SELECT * FROM tickets WHERE nama=? ORDER BY ROWID DESC LIMIT 50",
        (username,)
    ).fetchall()
    conn.close()
    
    return render_template('public/my_tickets.html', tickets=tickets, username=username)

# ================= ROUTES: ADMIN =================

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    used = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='used'").fetchone()[0]
    valid = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='valid'").fetchone()[0]
    tickets = conn.execute("SELECT * FROM tickets ORDER BY ROWID DESC LIMIT 50").fetchall()
    total_tiket = conn.execute("SELECT SUM(jumlah) FROM tickets").fetchone()[0] or 0
    total_pendapatan_raw = total_tiket * TICKET_PRICE
    total_pendapatan = f"{total_pendapatan_raw:,}".replace(",", ".")
    conn.close()
    
    return render_template(
        'admin/dashboard.html',
        total=total, used=used, valid=valid,
        tickets=tickets, total_pendapatan=total_pendapatan
    )

@app.route('/manage_ticket')
def manage_ticket():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    tickets = conn.execute("SELECT * FROM tickets ORDER BY ROWID DESC").fetchall()
    conn.close()
    
    return render_template('admin/manage_ticket.html', tickets=tickets)

@app.route('/manage_wahana', methods=['GET', 'POST'])
def manage_wahana():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        emoji = request.form.get('emoji', '🎢')
        kategori = request.form.get('kategori', 'dry')
        status = request.form.get('status', 'available')
        wait_time = int(request.form.get('wait_time', 0))
        
        if nama:
            conn.execute(
                "INSERT INTO wahana (nama, deskripsi, emoji, kategori, status, wait_time) VALUES (?, ?, ?, ?, ?, ?)",
                (nama, deskripsi, emoji, kategori, status, wait_time)
            )
            conn.commit()
    
    wahana = conn.execute("SELECT * FROM wahana").fetchall()
    conn.close()
    
    return render_template('admin/manage_wahana.html', wahana=wahana)

@app.route('/delete_wahana/<int:wahana_id>')
def delete_wahana(wahana_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    conn.execute("DELETE FROM wahana WHERE id=?", (wahana_id,))
    conn.commit()
    conn.close()
    
    return redirect('/manage_wahana')

@app.route('/scan')
def scan():
    if session.get('role') not in ['admin', 'employee']:
        return redirect('/login')
    
    return render_template('admin/scan.html')

@app.route('/admin_absensi')
def admin_absensi():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    absensi = conn.execute("SELECT * FROM absensi ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    
    return render_template('admin/absensi.html', absensi=absensi)

@app.route('/users')
def users():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY role, username").fetchall()
    conn.close()
    
    return render_template('admin/users.html', users=users)

@app.route('/create_user', methods=['POST'])
def create_user():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    nama_lengkap = request.form.get('nama_lengkap', '').strip()
    role = request.form.get('role', 'user')
    
    if not username or not password:
        return redirect('/users')
    
    conn = get_db()
    existing = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not existing:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute(
            "INSERT INTO users (username, password, role, nama_lengkap, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, password, role, nama_lengkap, now)
        )
        conn.commit()
    conn.close()
    
    return redirect('/users')

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if user and user['username'] != 'admin':
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    conn.close()
    
    return redirect('/users')

# ================= ROUTES: EMPLOYEE =================

@app.route('/absensi', methods=['GET', 'POST'])
def absensi():
    if session.get('role') not in ['employee', 'admin']:
        return redirect('/login')
    
    if request.method == 'POST':
        lat = float(request.form.get('lat', 0))
        lng = float(request.form.get('lng', 0))
        
        jarak = hitung_jarak(lat, lng, OFFICE_LAT, OFFICE_LNG)
        
        if jarak > OFFICE_RADIUS:
            return render_template(
                'employee/absensi.html',
                error=f"Gagal! Di luar area ({int(jarak)}m). Harus dalam radius {OFFICE_RADIUS}m."
            )
        
        now = datetime.now()
        tanggal = now.strftime("%Y-%m-%d")
        jam = now.strftime("%H:%M:%S")
        
        conn = get_db()
        conn.execute(
            "INSERT INTO absensi (nama, tanggal, jam, jarak, status) VALUES (?, ?, ?, ?, ?)",
            (session['user'], tanggal, jam, jarak, "Dalam Area")
        )
        conn.commit()
        conn.close()
        
        return render_template(
            'employee/absensi.html',
            success=f"Berhasil! Absen masuk pada {jam}"
        )
    
    return render_template('employee/absensi.html')

@app.route('/history')
def history():
    if session.get('role') not in ['employee', 'admin']:
        return redirect('/login')
    
    conn = get_db()
    data = conn.execute(
        "SELECT * FROM absensi WHERE nama=? ORDER BY id DESC",
        (session['user'],)
    ).fetchall()
    conn.close()
    
    return render_template('employee/history.html', data=data)

# ================= ROUTES: TICKET MANAGEMENT =================

@app.route('/reset/<ticket_id>')
def reset(ticket_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    conn.execute("UPDATE tickets SET status='valid' WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    return redirect('/manage_ticket')

@app.route('/delete/<ticket_id>')
def delete(ticket_id):
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db()
    conn.execute("DELETE FROM tickets WHERE id=?", (ticket_id,))
    conn.commit()
    conn.close()
    return redirect('/manage_ticket')

# ================= RUN =================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)