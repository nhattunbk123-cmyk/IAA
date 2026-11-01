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
from app.database import init_db

if __name__ == '__main__':
    print("[*] Đang khởi tạo cơ sở dữ liệu VulnShop Lab...")
    app = create_app()
    with app.app_context():
        init_db()
    print("[+] Khởi tạo cơ sở dữ liệu và nạp dữ liệu mẫu thành công!")
    print("[+] Tài khoản hệ thống:")
    print("    - Admin:   hoangnhatdan123 / 12345678 (Quyền Quản Trị Viên)")
    print("    - User 1:  user1 / User@123 (Khách hàng 1)")
    print("    - User 2:  user2 / User@123 (Khách hàng 2)")
    print("    - Admin 2: admin / Admin@123 (Tương thích ngược)")
