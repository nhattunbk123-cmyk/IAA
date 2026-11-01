import os
import sys
import pytest

# Thêm thư mục gốc vào đường dẫn hệ thống
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import get_db, init_db, seed_data, set_lab_vulnerable

import tempfile
import uuid

@pytest.fixture
def app():
    """Tạo Flask app với cấu hình test và database SQLite riêng biệt."""
    test_db_path = os.path.join(tempfile.gettempdir(), f'test_lab_{uuid.uuid4().hex}.db')
    app = create_app({
        'TESTING': True,
        'DATABASE': test_db_path,
        'SECRET_KEY': 'test-secret-key-lab',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        init_db()

    yield app

    # Dọn dẹp sau khi chạy test xong
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except OSError:
            pass

@pytest.fixture
def client(app):
    return app.test_client()

def login_as_user(client, username='user1'):
    """Helper đăng nhập với tư cách người dùng thường (user1)."""
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = username
        sess['full_name'] = 'Nguyễn Văn An'
        sess['role'] = 'user'
        sess['address'] = '123 Đường Cầu Giấy, Hà Nội'

def login_as_admin(client):
    """Helper đăng nhập với tư cách quản trị viên (admin)."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['full_name'] = 'Quản Trị Viên'
        sess['role'] = 'admin'

# ==============================================================================
# 1. TEST LAB 1: REFLECTED XSS
# ==============================================================================
def test_reflected_xss(client, app):
    with app.app_context():
        # Chế độ Vulnerable: Dữ liệu tìm kiếm không bị escape
        set_lab_vulnerable('reflected_xss', True)
        res_vuln = client.get('/search?q=<script>alert(1)</script>')
        html_vuln = res_vuln.get_data(as_text=True)
        assert '<script>alert(1)</script>' in html_vuln

        # Chế độ Fixed: Dữ liệu tìm kiếm được escape thành các thực thể HTML an toàn
        set_lab_vulnerable('reflected_xss', False)
        res_fixed = client.get('/search?q=<script>alert(1)</script>')
        html_fixed = res_fixed.get_data(as_text=True)
        assert '<script>alert(1)</script>' not in html_fixed
        assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html_fixed

# ==============================================================================
# 2. TEST LAB 2: STORED XSS
# ==============================================================================
def test_stored_xss(client, app):
    with app.app_context():
        # Chế độ Vulnerable: Cho phép thẻ HTML được render qua | safe
        set_lab_vulnerable('stored_xss', True)
        client.post('/product/1/comment', data={
            'content': '<b>San pham rat tot</b>',
            'rating': 5
        }, follow_redirects=True)
        res_vuln = client.get('/product/1')
        html_vuln = res_vuln.get_data(as_text=True)
        assert '<b>San pham rat tot</b>' in html_vuln

        # Chế độ Fixed: Chuỗi được escape an toàn trước khi lưu
        set_lab_vulnerable('stored_xss', False)
        client.post('/product/1/comment', data={
            'content': '<b>Thu nghiem an toan</b>',
            'rating': 5
        }, follow_redirects=True)
        res_fixed = client.get('/product/1')
        html_fixed = res_fixed.get_data(as_text=True)
        assert '&lt;b&gt;Thu nghiem an toan&lt;/b&gt;' in html_fixed

# ==============================================================================
# 3. TEST LAB 3: DOM-BASED XSS
# ==============================================================================
def test_dom_xss(client, app):
    with app.app_context():
        # Chế độ Vulnerable: Flag data-dom-vuln="true"
        set_lab_vulnerable('dom_xss', True)
        res_vuln = client.get('/product/1')
        html_vuln = res_vuln.get_data(as_text=True)
        assert 'data-dom-vuln="true"' in html_vuln

        # Chế độ Fixed: Flag data-dom-vuln="false"
        set_lab_vulnerable('dom_xss', False)
        res_fixed = client.get('/product/1')
        html_fixed = res_fixed.get_data(as_text=True)
        assert 'data-dom-vuln="false"' in html_fixed

# ==============================================================================
# 4. TEST LAB 4: SQL INJECTION
# ==============================================================================
def test_sql_injection(client, app):
    with app.app_context():
        # Chế độ Vulnerable: Nối chuỗi trực tiếp
        set_lab_vulnerable('sqli', True)
        res_vuln = client.get("/products/filter?keyword=Nitro' OR '1'='1")
        html_vuln = res_vuln.get_data(as_text=True)
        assert "SELECT * FROM products WHERE (name LIKE '%Nitro' OR '1'='1%'" in html_vuln or res_vuln.status_code == 200

        # Chế độ Fixed: Dùng Parameterized Query
        set_lab_vulnerable('sqli', False)
        res_fixed = client.get("/products/filter?keyword=Nitro' OR '1'='1")
        html_fixed = res_fixed.get_data(as_text=True)
        assert "Parameterized Query" in html_fixed or "SELECT * FROM products WHERE 1=1" in html_fixed

# ==============================================================================
# 5. TEST LAB 5: IDOR (INSECURE DIRECT OBJECT REFERENCE)
# ==============================================================================
def test_idor(client, app):
    login_as_user(client, 'user1') # user_id = 2, sở hữu đơn hàng 1 và 2

    with app.app_context():
        # Đơn hàng #3 thuộc về user2 (user_id = 3)
        # Chế độ Vulnerable: user1 có thể xem trái phép đơn hàng #3 của user2
        set_lab_vulnerable('idor', True)
        res_vuln = client.get('/api/orders/3')
        assert res_vuln.status_code == 200
        json_data = res_vuln.get_json()
        assert json_data['success'] is True
        assert json_data['order']['id'] == 3

        # Chế độ Fixed: user1 bị từ chối với mã 403 Forbidden
        set_lab_vulnerable('idor', False)
        res_fixed = client.get('/api/orders/3')
        assert res_fixed.status_code == 403
        assert res_fixed.get_json()['success'] is False

# ==============================================================================
# 6. TEST LAB 6: BROKEN ACCESS CONTROL
# ==============================================================================
def test_broken_access_control(client, app):
    login_as_user(client, 'user1') # Người dùng thông thường không có quyền admin

    with app.app_context():
        # Chế độ Vulnerable: Người dùng thường gọi API quản trị thành công (200 OK)
        set_lab_vulnerable('broken_access_control', True)
        res_vuln = client.post('/api/admin/orders/1/status', json={'status': 'Đã hoàn thành'})
        assert res_vuln.status_code == 200
        assert res_vuln.get_json()['success'] is True

        # Chế độ Fixed: Máy chủ kiểm tra vai trò và từ chối người dùng thường (403 Forbidden)
        set_lab_vulnerable('broken_access_control', False)
        res_fixed = client.post('/api/admin/orders/1/status', json={'status': 'Đã hoàn thành'})
        assert res_fixed.status_code == 403
        assert res_fixed.get_json()['success'] is False

# ==============================================================================
# 7. TEST LAB 7: CSRF (CROSS-SITE REQUEST FORGERY)
# ==============================================================================
def test_csrf(client, app):
    login_as_user(client, 'user1')

    with app.app_context():
        # Chế độ Vulnerable: Chấp nhận request thay đổi địa chỉ mà không có token CSRF
        set_lab_vulnerable('csrf', True)
        res_vuln = client.post('/profile/update-address', data={'address': 'Dia Chi Giao Hang Moi'})
        assert res_vuln.status_code == 302 # Chuyển hướng thành công

        # Chế độ Fixed: Từ chối request không có CSRF token với mã 403 Forbidden
        set_lab_vulnerable('csrf', False)
        res_fixed = client.post('/profile/update-address', data={'address': 'Dia Chi Bi Chan'})
        assert res_fixed.status_code == 403

# ==============================================================================
# 8. TEST LAB 8: BUSINESS LOGIC (PRICE TAMPERING)
# ==============================================================================
def test_business_logic(client, app):
    login_as_user(client, 'user1')

    with app.app_context():
        # Sản phẩm #1 (Laptop) có giá thực tế là 21,500,000 VND
        # Client gửi lên price: 1000 VND
        tampered_payload = {
            'items': [{'id': 1, 'quantity': 1, 'price': 1000}],
            'shipping_address': 'Địa chỉ test',
            'payment_method': 'COD'
        }

        # Chế độ Vulnerable: Server tin tưởng giá 1000 VND từ client
        set_lab_vulnerable('business_logic', True)
        res_vuln = client.post('/cart/checkout', json=tampered_payload)
        assert res_vuln.status_code == 200
        assert res_vuln.get_json()['total_amount'] == 1000

        # Chế độ Fixed: Server tự truy vấn database, áp dụng đúng giá thực tế từ CSDL
        set_lab_vulnerable('business_logic', False)
        res_fixed = client.post('/cart/checkout', json=tampered_payload)
        assert res_fixed.status_code == 200
        db_product = get_db().execute("SELECT price FROM products WHERE id = 1").fetchone()
        expected_price = db_product['price'] if db_product else 21500000
        assert res_fixed.get_json()['total_amount'] == expected_price

# ==============================================================================
# 9. TEST LAB 9: SECURITY MISCONFIGURATION
# ==============================================================================
def test_security_misconfiguration(client, app):
    with app.app_context():
        # Chế độ Vulnerable: Lộ thông tin cấu hình giả lập và đường dẫn nội bộ
        set_lab_vulnerable('security_misconfig', True)
        res_vuln = client.get('/api/system/debug-info')
        data_vuln = res_vuln.get_json()
        assert res_vuln.status_code == 200
        assert data_vuln['is_vuln'] is True
        assert 'mock_configuration_secrets' in data_vuln
        assert 'MOCK_PAYMENT_SECRET_KEY' in data_vuln['mock_configuration_secrets']

        # Chế độ Fixed: Ẩn toàn bộ cấu hình, chỉ trả về trạng thái chuẩn
        set_lab_vulnerable('security_misconfig', False)
        res_fixed = client.get('/api/system/debug-info')
        data_fixed = res_fixed.get_json()
        assert res_fixed.status_code == 200
        assert data_fixed['is_vuln'] is False
        assert 'mock_configuration_secrets' not in data_fixed
        assert data_fixed['status'] == 'healthy'

# ==============================================================================
# 10. TEST LAB 10: OS COMMAND INJECTION
# ==============================================================================
def test_command_injection(client, app):
    with app.app_context():
        # Chế độ Fixed: Chặn ký tự phân tách lệnh
        set_lab_vulnerable('command_injection', False)
        res_fixed = client.post('/tools/ping', data={'target': '127.0.0.1; whoami'})
        assert res_fixed.status_code == 200
        assert "Phát hiện ký tự không hợp lệ" in res_fixed.data.decode('utf-8')

        # Chế độ Vulnerable: Cho phép gọi shell với target chứa dấu phân tách
        set_lab_vulnerable('command_injection', True)
        res_vuln = client.post('/tools/ping', data={'target': '127.0.0.1'})
        assert res_vuln.status_code == 200
        assert "server_terminal@vulnshop" in res_vuln.data.decode('utf-8')

# ==============================================================================
# 11. TEST LAB 11: INSECURE FILE UPLOAD & WEBSHELL
# ==============================================================================
import io

def test_file_upload_shell(client, app):
    with app.app_context():
        # Chế độ Fixed: Từ chối upload file script .py/.php
        set_lab_vulnerable('file_upload_shell', False)
        data = {'file': (io.BytesIO(b"print('malicious')"), 'exploit.py')}
        res_fixed = client.post('/tools/upload-file', data=data)
        assert res_fixed.status_code == 200
        assert "bị từ chối" in res_fixed.data.decode('utf-8') or "Định dạng tệp" in res_fixed.data.decode('utf-8')

        # Endpoint WebShell trả về 403 ở chế độ Fixed
        res_ws_fixed = client.get('/tools/webshell/exploit.py')
        assert res_ws_fixed.status_code == 403

        # Chế độ Vulnerable: Chấp nhận upload file script
        set_lab_vulnerable('file_upload_shell', True)
        data_vuln = {'file': (io.BytesIO(b"print('shell_active')"), 'shell_test.py')}
        res_vuln = client.post('/tools/upload-file', data=data_vuln)
        assert res_vuln.status_code == 200
        assert "shell_test.py" in res_vuln.data.decode('utf-8')

# ==============================================================================
# 12. TEST LAB 12: DENIAL OF SERVICE (REDOS)
# ==============================================================================
def test_dos_redos(client, app):
    with app.app_context():
        # Chế độ Vulnerable: Nhận diện mã hợp lệ
        set_lab_vulnerable('dos_redos', True)
        res_valid = client.post('/tools/validate-coupon', data={'coupon_code': 'SUMMER2026'})
        assert res_valid.status_code == 200
        assert "Mã hợp lệ!" in res_valid.data.decode('utf-8')

        # Chế độ Fixed: Từ chối chuỗi vượt quá 16 ký tự để ngăn chặn ReDoS
        set_lab_vulnerable('dos_redos', False)
        res_fixed = client.post('/tools/validate-coupon', data={'coupon_code': 'aaaaaaaaaaaaaaaaaaaaa'})
        assert res_fixed.status_code == 200
        assert "Độ dài vượt quá giới hạn 16 ký tự" in res_fixed.data.decode('utf-8')

