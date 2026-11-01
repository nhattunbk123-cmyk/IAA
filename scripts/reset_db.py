import os
import sys

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import get_db, seed_data

if __name__ == '__main__':
    print("[*] Đang khôi phục toàn bộ cơ sở dữ liệu về trạng thái sạch ban đầu...")
    app = create_app()
    with app.app_context():
        db = get_db()
        seed_data(db)
    print("[+] Hoàn tất! Cơ sở dữ liệu đã được làm sạch và nạp lại toàn bộ dữ liệu mẫu ban đầu.")
