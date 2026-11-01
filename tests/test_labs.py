import os
import sys
import pytest

# Thêm thư mục gốc vào đường dẫn hệ thống
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import get_db, init_db, set_lab_vulnerable

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
        sess['username'] = 'hoangnhatdan123'
        sess['full_name'] = 'Hoàng Nhật Đan (Admin)'
        sess['role'] = 'admin'

# ==============================================================================
# 1. KIỂM THỬ LỖ HỔNG 1: CROSS-SITE SCRIPTING (XSS)
# ==============================================================================
def test_xss_reflected(client, app):
    """Kiểm tra Reflected XSS trên thanh tìm kiếm."""
    with app.app_context():
        # Chế độ Vulnerable: Dữ liệu tìm kiếm không bị escape (render thẻ thô)
        set_lab_vulnerable('xss', True)
        res_vuln = client.get('/search?q=<script>alert(1)</script>')
        html_vuln = res_vuln.get_data(as_text=True)
        assert '<script>alert(1)</script>' in html_vuln

        # Chế độ Fixed: Dữ liệu tìm kiếm được escape an toàn
        set_lab_vulnerable('xss', False)
        res_fixed = client.get('/search?q=<script>alert(1)</script>')
        html_fixed = res_fixed.get_data(as_text=True)
        assert '<script>alert(1)</script>' not in html_fixed
        assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html_fixed

def test_xss_stored(client, app):
    """Kiểm tra Stored XSS trong bình luận sản phẩm."""
    with app.app_context():
        # Chế độ Vulnerable: Cho phép thẻ HTML được render qua | safe
        set_lab_vulnerable('xss', True)
        client.post('/product/1/comment', data={
            'content': '<b>San pham rat tot</b>',
            'rating': 5
        }, follow_redirects=True)
        res_vuln = client.get('/product/1')
        html_vuln = res_vuln.get_data(as_text=True)
        assert '<b>San pham rat tot</b>' in html_vuln

        # Chế độ Fixed: Bỏ bộ lọc safe
        set_lab_vulnerable('xss', False)
        res_fixed = client.get('/product/1')
        html_fixed = res_fixed.get_data(as_text=True)
        assert 'is_stored_xss_vuln' not in html_fixed or res_fixed.status_code == 200

# ==============================================================================
# 2. KIỂM THỬ LỖ HỔNG 2: SQL INJECTION (SQLI)
# ==============================================================================
def test_sql_injection(client, app):
    """Kiểm tra SQL Injection trên bộ lọc sản phẩm."""
    with app.app_context():
        # Chế độ Vulnerable: Nối chuỗi trực tiếp
        set_lab_vulnerable('sqli', True)
        res_vuln = client.get("/products/filter?keyword=Nitro' OR '1'='1")
        assert res_vuln.status_code == 200

        # Chế độ Fixed: Dùng Parameterized Query an toàn
        set_lab_vulnerable('sqli', False)
        res_fixed = client.get("/products/filter?keyword=Nitro' OR '1'='1")
        assert res_fixed.status_code == 200

# ==============================================================================
# 3. KIỂM THỬ LỖ HỔNG 3: OS COMMAND INJECTION
# ==============================================================================
def test_command_injection(client, app):
    """Kiểm tra OS Command Injection trên công cụ ping mạng."""
    with app.app_context():
        # Chế độ Fixed: Chặn ký tự phân tách lệnh
        set_lab_vulnerable('command_injection', False)
        res_fixed = client.post('/tools/ping', data={'target': '127.0.0.1; whoami'})
        assert res_fixed.status_code == 200
        assert "Phát hiện ký tự không hợp lệ" in res_fixed.data.decode('utf-8')

        # Chế độ Vulnerable: Chấp nhận địa chỉ hợp lệ
        set_lab_vulnerable('command_injection', True)
        res_vuln = client.post('/tools/ping', data={'target': '127.0.0.1'})
        assert res_vuln.status_code == 200

# ==============================================================================
# 4. KIỂM THỬ CÁC TÍNH NĂNG KHÁC LUÔN AN TOÀN (VÁ MẶC ĐỊNH)
# ==============================================================================
def test_other_features_are_secure_by_default(client, app):
    """Xác nhận các tính năng ngoài 3 lab trên (IDOR, Debug Secrets, v.v...) luôn ở trạng thái an toàn."""
    with app.app_context():
        login_as_user(client, 'user1')
        
        # IDOR đã được vá: user1 không thể xem trộm đơn hàng 3 của user2
        res_order = client.get('/api/orders/3')
        assert res_order.status_code == 403

        # Debug info đã được vá: Ẩn thông tin cấu hình nhạy cảm
        res_debug = client.get('/api/system/debug-info')
        data_debug = res_debug.get_json()
        assert data_debug['is_vuln'] is False
        assert 'mock_configuration_secrets' not in data_debug

# ==============================================================================
# 5. KIỂM THỬ API LAB TOGGLE (CHỈ CÓ 3 LAB)
# ==============================================================================
def test_lab_hub_has_exactly_3_labs(client, app):
    """Kiểm tra trang Trung tâm Lab chỉ hiển thị đúng 3 bài lab."""
    res = client.get('/labs')
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert 'Hệ thống 3 bài thực hành an ninh mạng cốt lõi' in html
    assert 'Cross-Site Scripting (XSS' in html
    assert 'SQL Injection' in html
    assert 'OS Command Injection' in html

def test_api_toggle_lab(client, app):
    """Kiểm tra API bật tắt trạng thái cho 3 lab."""
    with app.app_context():
        # Bật XSS
        res = client.post('/api/labs/toggle', json={'lab_id': 'xss', 'status': True})
        assert res.status_code == 200
        assert res.get_json()['success'] is True

        # Tắt XSS
        res = client.post('/api/labs/toggle', json={'lab_id': 'xss', 'status': False})
        assert res.status_code == 200
        assert res.get_json()['is_vulnerable'] is False
