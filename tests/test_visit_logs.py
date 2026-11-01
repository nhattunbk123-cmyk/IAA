import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import get_db, init_db

import tempfile
import uuid

@pytest.fixture
def app():
    test_db_path = os.path.join(tempfile.gettempdir(), f'test_visit_{uuid.uuid4().hex}.db')
    app = create_app({
        'TESTING': True,
        'DATABASE': test_db_path,
        'SECRET_KEY': 'test-secret-key-visit-logs',
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

def test_guest_visit_logging(client, app):
    """Kiểm tra lượt truy cập của khách vãng lai được tự động ghi nhận vào database."""
    response = client.get('/')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        log = db.execute("SELECT * FROM visit_logs WHERE path = '/' ORDER BY id DESC LIMIT 1").fetchone()
        assert log is not None
        assert log['username'] == 'Khách vãng lai'
        assert log['role'] == 'guest'
        assert log['method'] == 'GET'
        assert log['created_at'] is not None

def test_logged_in_user_visit_logging(client, app):
    """Kiểm tra lượt truy cập của thành viên đã đăng nhập được ghi nhận đúng danh tính."""
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = 'user1'
        sess['full_name'] = 'Nguyễn Văn An'
        sess['role'] = 'user'

    response = client.get('/cart')
    assert response.status_code == 200

    with app.app_context():
        db = get_db()
        log = db.execute("SELECT * FROM visit_logs WHERE path = '/cart' ORDER BY id DESC LIMIT 1").fetchone()
        assert log is not None
        assert log['user_id'] == 2
        assert log['username'] == 'user1'
        assert log['full_name'] == 'Nguyễn Văn An'
        assert log['role'] == 'user'

def test_admin_access_logs_protection(client):
    """Chỉ tài khoản admin mới được xem trang /admin/access-logs."""
    # Khách vãng lai bị chuyển hướng đăng nhập
    resp_guest = client.get('/admin/access-logs')
    assert resp_guest.status_code in [302, 403]

    # User thường bị từ chối 403
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = 'user1'
        sess['role'] = 'user'
    resp_user = client.get('/admin/access-logs')
    assert resp_user.status_code == 403

def test_admin_can_view_and_clear_logs(client, app):
    """Admin có thể xem và dọn dẹp lịch sử truy cập."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'hoangnhatdan123'
        sess['full_name'] = 'Hoàng Nhật Đan (Admin)'
        sess['role'] = 'admin'

    # Admin truy cập trang access-logs
    resp = client.get('/admin/access-logs')
    assert resp.status_code == 200
    assert 'Nhật Ký Truy Cập' in resp.get_data(as_text=True)

    # Admin truy cập dashboard
    resp_dash = client.get('/admin')
    assert resp_dash.status_code == 200
    assert 'Ai Đang Vào Web' in resp_dash.get_data(as_text=True)

    # Admin dọn dẹp nhật ký
    resp_clear = client.post('/admin/access-logs/clear', data={'action': 'all'}, follow_redirects=True)
    assert resp_clear.status_code == 200
