import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'arch-realty-super-secret-key-2026-ahmedabad-erp')
    _db_url = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'arch_realty.db')}"
    )
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configurations (protected storage outside public static)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'instance', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
    
    # Timezone & Localization
    TIMEZONE = 'Asia/Kolkata'
    CURRENCY_SYMBOL = '₹'
    
    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # WTForms CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'instance', 'test_uploads')
