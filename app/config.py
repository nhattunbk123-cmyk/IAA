import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Tự động nạp biến môi trường từ tệp .env nếu có
ENV_FILE = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_FILE):
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    except Exception:
        pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vulnshop-super-secret-key-for-lab-only')
    DATABASE = os.environ.get('DATABASE_PATH', os.path.join(INSTANCE_DIR, 'vulnshop.db'))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    TEMPLATES_AUTO_RELOAD = True
    
    # Cấu hình gửi Gmail SMTP thực tế
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'testhieu652@gmail.com')  # Địa chỉ Gmail người gửi mặc định
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'anisjbxkpobxvrlk')  # Mật khẩu ứng dụng Google 16 ký tự
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Laptop52h.vn <testhieu652@gmail.com>')

    # Dữ liệu cấu hình giả lập (Mock Secrets) phục vụ bài lab Security Misconfiguration
    # Không sử dụng thông tin thật của máy chủ
    MOCK_PAYMENT_GATEWAY_API = "https://mock-payment-sandbox.local/v1"
    MOCK_PAYMENT_SECRET_KEY = "mock_sec_key_sandbox_998877665544"
    MOCK_INTERNAL_AUTH_SERVICE = "http://10.0.0.15:8080/internal/auth"
    MOCK_INTERNAL_DEBUG_FLAG = True
    APP_VERSION = "2.4.1-lab-build"
