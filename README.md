# Nice PlayLand - Deployment Guide

## Production Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy dan edit configuration
cp .env.example .env

# Edit .env dengan value yang benar:
# - SECRET_KEY: generate dengan python -c "import secrets; print(secrets.token_hex(32))"
# - MIDTRANS_SERVER_KEY: dari Midtrans Dashboard
# - MIDTRANS_CLIENT_KEY: dari Midtrans Dashboard
# - BASE_URL: URL production Anda
```

### 3. Database

```bash
# Database automatically dibuat saat app start
# Untuk production, gunakan PostgreSQL dengan mengubah config.py
```

### 4. Running

#### Development:
```bash
python app.py
# Buka http://127.0.0.1:5000
```

#### Production:
```bash
# Menggunakan Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 5. Deployment ke Cloud

#### Render.com:
1. Push ke GitHub
2. Buat Web Service
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`

#### Railway:
1. Connect GitHub repo
2. Environment variables: Set di Railway dashboard
3. Deploy

#### VPS (DigitalOcean/AWS/Cloud":
```bash
# Install requirements
pip install -r requirements.txt

# Run dengan systemd atau supervisor
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### 6. HTTPS/SSL

- Render.com: auto HTTPS
- Railway: auto HTTPS  
- VPS: Gunakan Nginx dengan Let's Encrypt

## Demo Credentials

```
Admin: admin / 123
Karyawan: karyawan / 123
```

## Features

- ✅ Pembelian Tiket Online
- ✅ QR Code Digital
- ✅ Promo Codes
- ✅ Admin Dashboard dengan Charts
- ✅ Kelola Tiket
- ✅ Kelola Wahana
- ✅ Absensi GPS Employee
- ✅ Monitoring Absensi
- ✅ User Registration
- ✅ My Tickets History
- ✅ Dark Mode
- ✅ Responsive Design
- ✅ CS Chat Widget

## Technologies

- Flask (Python)
- SQLite (dev) / PostgreSQL (prod)
- Midtrans (Payment)
- QR Code
- Chart.js

## License

MIT