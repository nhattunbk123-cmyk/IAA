import os
import sys

# Đảm bảo mã hóa UTF-8 trên Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Mặc định chỉ bind vào 127.0.0.1 nhằm đảm bảo an toàn cho môi trường lab cục bộ
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    
    print(f"[*] VulnShop Lab đang chạy tại: http://{host}:{port}")
    print(f"[*] Truy cập Trung tâm Thực hành Lab tại: http://{host}:{port}/labs")
    app.run(host=host, port=port, debug=debug)
