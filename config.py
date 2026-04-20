"""
Nice PlayLand - Configuration Loader
Load settings dari environment variables
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / 'static'
TEMPLATE_DIR = BASE_DIR / 'templates'

# Load environment variables dari .env file
def load_env():
    """Load .env file jika ada"""
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

load_env()

# ================= APP CONFIG =================
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('FLASK_ENV', 'production') != 'production'

# ================= DATABASE =================
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///database.db')

# ================= MIDTRANS =================
MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY', 'Mid-server-DjT7AfkW_SfXsNK-jA60AVFe')
MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY', 'Mid-client-yVM7aqXrYZ2yuMiT')
MIDTRANS_IS_PRODUCTION = os.environ.get('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'

# ================= TICKET =================
TICKET_PRICE = int(os.environ.get('TICKET_PRICE', '35000'))

# ================= OFFICE GPS (Nice PlayLand Location) =================
# Lokasi: Nice PlayLand - Indramayu, Jawa Barat
OFFICE_LAT = float(os.environ.get('OFFICE_LAT', '-6.353323445991585'))
OFFICE_LNG = float(os.environ.get('OFFICE_LNG', '108.32058969370127'))
OFFICE_RADIUS = int(os.environ.get('OFFICE_RADIUS_METERS', '150'))

# ================= PARK INFO =================
PARK_NAME = "Nice PlayLand Indramayu"
PARK_ADDRESS = "Jl. Soekarno Hatta No.14a, Pekandangan Jaya, Kec. Indramayu, Kab. Indramayu, Jawa Barat 45211"
PARK_GMAPS = "https://maps.app.goo.gl/J8WC+M7"
PARK_PHONE = os.environ.get('PARK_PHONE', '+62821-9999-0000')
PARK_WA = os.environ.get('PARK_WA', '+62821-9999-0000')
PARK_EMAIL = os.environ.get('PARK_EMAIL', 'info@niceplayland.com')
PARK_INSTAGRAM = os.environ.get('PARK_INSTAGRAM', '@niceplayland_id')
PARK_FACEBOOK = os.environ.get('PARK_FACEBOOK', 'NicePlayLandIndramayu')
PARK_OPEN_HOUR = "08.00"
PARK_CLOSE_HOUR = "18.00"

# ================= URLs =================
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')

# ================= PROMO CODES =================
PROMO_CODES = {
    'PLAYLAND20': 20,
    'INDRAMAYU25': 25,
    'LIBURAN15': 15,
    'HEMAT50': 50,
    'MEI2024': 20,
    'WELCOME10': 10,
    'WONGASLI': 30,
}

# ================= ADMIN ACCOUNTS =================
DEFAULT_USERS = {
    'admin': {'password': '123', 'role': 'admin'},
    'admin2': {'password': '123', 'role': 'admin'},
    'admin3': {'password': '123', 'role': 'admin'},
    'karyawan1': {'password': '123', 'role': 'employee'},
    'karyawan2': {'password': '123', 'role': 'employee'},
    'karyawan3': {'password': '123', 'role': 'employee'},
    'karyawan4': {'password': '123', 'role': 'employee'},
    'karyawan5': {'password': '123', 'role': 'employee'},
    'karyawan6': {'password': '123', 'role': 'employee'},
    'karyawan7': {'password': '123', 'role': 'employee'},
    'karyawan8': {'password': '123', 'role': 'employee'},
    'karyawan9': {'password': '123', 'role': 'employee'},
    'karyawan10': {'password': '123', 'role': 'employee'},
}