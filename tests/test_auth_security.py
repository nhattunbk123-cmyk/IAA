import os
import sys
import pytest
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import get_db, init_db
from app.security import (
    validate_password_strength,
    generate_otp_code,
    mask_email,
    send_otp_email
)

import tempfile
import uuid

@pytest.fixture
def app():
    test_db_path = os.path.join(tempfile.gettempdir(), f'test_sec_{uuid.uuid4().hex}.db')
    app = create_app({
        'TESTING': True,
        'DATABASE': test_db_path,
        'SECRET_KEY': 'test-secret-key-security',
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

# ==============================================================================
# 1. KIỂM THỬ CHÍNH SÁCH MẬT KHẨU MẠNH (STRONG PASSWORD POLICY)
# ==============================================================================
def test_password_strength_validator():
    """Kiểm tra logic hàm kiểm tra độ mạnh mật khẩu."""
    # Quá ngắn (< 8 ký tự)
    ok, msg = validate_password_strength("Ab1@")
    assert not ok
    assert "tối thiểu từ 8 ký tự" in msg

    # Thiếu chữ in hoa
    ok, msg = validate_password_strength("weakpass123@")
    assert not ok
    assert "chữ cái in hoa" in msg

    # Thiếu chữ in thường
    ok, msg = validate_password_strength("WEAKPASS123@")
    assert not ok
    assert "chữ cái in thường" in msg

    # Thiếu số
    ok, msg = validate_password_strength("WeakPassWord@")
    assert not ok
    assert "chữ số" in msg

    # Thiếu ký tự đặc biệt
    ok, msg = validate_password_strength("WeakPassword123")
    assert not ok
    assert "ký tự đặc biệt" in msg

    # Hợp lệ đầy đủ chuẩn
    ok, msg = validate_password_strength("Laptop52h@Secure2026")
    assert ok
    assert msg == ""

def test_register_weak_password_rejected(client):
    """Đăng ký tài khoản với mật khẩu yếu bị từ chối ngay lập tức."""
    resp = client.post('/register', data={
        'username': 'testweakuser',
        'password': '123',
        'full_name': 'Người Dùng Test',
        'email': 'testweak@example.com',
        'address': 'Hà Nội'
    })
    assert resp.status_code == 200
    assert "Mật khẩu phải có độ dài tối thiểu từ 8 ký tự" in resp.get_data(as_text=True)

# ==============================================================================
# 2. KIỂM THỬ KHÓA TÀI KHOẢN 5 PHÚT SAU 5 LẦN SAI LIÊN TIẾP
# ==============================================================================
def test_account_lockout_after_5_failed_attempts(client, app):
    """Nhập sai 5 lần liên tiếp sẽ khóa tài khoản trong 5 phút."""
    target_username = 'user1'

    # Nhập sai 4 lần đầu
    for i in range(1, 5):
        resp = client.post('/login', data={'username': target_username, 'password': 'WrongPassword'}, follow_redirects=True)
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        remaining = 5 - i
        assert f"Bạn còn {remaining} lần thử" in html

    # Lần thứ 5 sai -> Kích hoạt khóa tài khoản 5 phút
    resp_5 = client.post('/login', data={'username': target_username, 'password': 'WrongPassword'}, follow_redirects=True)
    html_5 = resp_5.get_data(as_text=True)
    assert "Tài khoản đã bị tạm khóa trong 5 phút" in html_5

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (target_username,)).fetchone()
        assert user['failed_attempts'] == 5
        assert user['locked_until'] is not None

    # Lần thứ 6: Dù nhập ĐÚNG mật khẩu cũng bị chặn do đang trong thời gian khóa
    resp_locked = client.post('/login', data={'username': target_username, 'password': 'User@123'}, follow_redirects=True)
    html_locked = resp_locked.get_data(as_text=True)
    assert "Tài khoản của bạn tạm thời bị khóa do nhập sai mật khẩu 5 lần" in html_locked

# ==============================================================================
# 3. KIỂM THỬ HÀM TIỆN ÍCH EMAIL & OTP
# ==============================================================================
def test_otp_generation_and_mask_email():
    """Kiểm tra sinh mã OTP 6 số và làm mờ email."""
    otp = generate_otp_code(6)
    assert len(otp) == 6
    assert otp.isdigit()

    masked1 = mask_email("phanhieu03022005@gmail.com")
    assert masked1 == "ph***@gmail.com"

    masked2 = mask_email("a@gmail.com")
    assert masked2 == "a***@gmail.com"

# ==============================================================================
# 4. KIỂM THỬ ĐĂNG KÝ VỚI GMAIL OTP
# ==============================================================================
def test_register_flow_with_gmail_otp(client, app):
    """Quy trình đăng ký gửi OTP về Gmail và xác thực thành công."""
    reg_data = {
        'username': 'newuser_gmail',
        'password': 'SecurePassword@2026',
        'full_name': 'Phan Hiếu Test',
        'email': 'testhieu652@gmail.com',
        'address': 'Hà Nội'
    }

    # Bước 1: Gửi form đăng ký
    resp = client.post('/register', data=reg_data, follow_redirects=False)
    assert resp.status_code == 302
    assert '/verify-register-otp' in resp.headers['Location']

    # Kiểm tra session lưu pending_register
    with client.session_transaction() as sess:
        assert 'pending_register' in sess
        otp = sess['pending_register']['otp']
        assert len(otp) == 6

    # Bước 2: Nhập OTP sai -> Bị từ chối
    resp_wrong = client.post('/verify-register-otp', data={'code': '000000'}, follow_redirects=True)
    assert resp_wrong.status_code == 200
    assert "Mã xác thực OTP không chính xác" in resp_wrong.get_data(as_text=True)

    # Bước 3: Nhập OTP đúng -> Tạo tài khoản và tự động đăng nhập
    resp_correct = client.post('/verify-register-otp', data={'code': otp}, follow_redirects=True)
    assert resp_correct.status_code == 200
    assert "kích hoạt tài khoản thành công" in resp_correct.get_data(as_text=True)

    # Kiểm tra user đã vào DB
    with app.app_context():
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE username = 'newuser_gmail'").fetchone()
        assert u is not None
        assert u['email'] == 'testhieu652@gmail.com'

# ==============================================================================
# 5. KIỂM THỬ ĐĂNG NHẬP VỚI GMAIL OTP
# ==============================================================================
def test_login_flow_with_gmail_otp(client, app):
    """Quy trình đăng nhập gửi OTP về Gmail và xác thực thành công."""
    # user1 có sẵn trong DB (pass: User@123, email: an.nguyen@example.com)
    resp = client.post('/login', data={'username': 'user1', 'password': 'User@123'}, follow_redirects=False)
    assert resp.status_code == 302
    assert '/verify-login-otp' in resp.headers['Location']

    with client.session_transaction() as sess:
        assert 'pending_login_otp' in sess
        otp = sess['pending_login_otp']['otp']
        assert len(otp) == 6

    # Nhập OTP sai
    resp_bad = client.post('/verify-login-otp', data={'code': '111111'}, follow_redirects=True)
    assert resp_bad.status_code == 200
    assert "Mã xác thực OTP không chính xác" in resp_bad.get_data(as_text=True)

    # Nhập OTP đúng
    resp_ok = client.post('/verify-login-otp', data={'code': otp}, follow_redirects=True)
    assert resp_ok.status_code == 200
    assert "Chào mừng Khách hàng: Nguyễn Văn An" in resp_ok.get_data(as_text=True)

    with client.session_transaction() as sess:
        assert sess['user_id'] == 2
        assert sess['username'] == 'user1'

# ==============================================================================
# 6. KIỂM THỬ GỬI LẠI MÃ OTP (RESEND)
# ==============================================================================
def test_resend_otp(client, app):
    """Kiểm tra chức năng gửi lại mã OTP."""
    client.post('/login', data={'username': 'user1', 'password': 'User@123'}, follow_redirects=False)

    with client.session_transaction() as sess:
        old_otp = sess['pending_login_otp']['otp']

    # Bấm gửi lại mã
    resp_resend = client.get('/resend-login-otp', follow_redirects=True)
    assert resp_resend.status_code == 200
    assert "Mã xác thực OTP mới đã được gửi lại" in resp_resend.get_data(as_text=True)

    with client.session_transaction() as sess:
        new_otp = sess['pending_login_otp']['otp']
        # Mã mới đã được sinh
        assert len(new_otp) == 6


# ==============================================================================
# 7. KIỂM THỬ QUÊN MẬT KHẨU & ĐẶT LẠI MẬT KHẨU MẠNH VỚI MÃ OTP
# ==============================================================================
def test_forgot_password_invalid_user(client):
    """Yêu cầu quên mật khẩu với tài khoản không tồn tại."""
    resp = client.post('/forgot-password', data={'identifier': 'nonexistent_user'}, follow_redirects=True)
    assert resp.status_code == 200
    assert "Không tìm thấy tài khoản" in resp.get_data(as_text=True)

def test_reset_password_requires_otp_verification(client):
    """Cố tình truy cập thẳng vào trang đổi mật khẩu khi chưa xác thực OTP sẽ bị chặn."""
    resp = client.get('/reset-password', follow_redirects=True)
    assert resp.status_code == 200
    assert "Bạn phải xác thực mã OTP trước khi đổi mật khẩu" in resp.get_data(as_text=True)

def test_forgot_password_full_flow_with_strong_password(client, app):
    """Quy trình quên mật khẩu hoàn chỉnh: Gửi OTP -> Xác thực OTP -> Kiểm tra mật khẩu mạnh -> Đổi thành công."""
    # Bước 1: Gửi yêu cầu quên mật khẩu bằng Gmail của user1
    resp_forgot = client.post('/forgot-password', data={'email': 'an.nguyen@example.com'}, follow_redirects=False)
    assert resp_forgot.status_code == 302
    assert '/verify-reset-password' in resp_forgot.headers['Location']

    with client.session_transaction() as sess:
        assert 'pending_reset_password' in sess
        otp = sess['pending_reset_password']['otp']
        assert len(otp) == 6
        assert not sess['pending_reset_password']['verified']

    # Bước 2: Nhập sai mã OTP -> Bị từ chối
    resp_bad_otp = client.post('/verify-reset-password', data={'code': '999999'}, follow_redirects=True)
    assert resp_bad_otp.status_code == 200
    assert "Mã xác thực OTP không chính xác" in resp_bad_otp.get_data(as_text=True)

    # Bước 3: Nhập đúng mã OTP -> Thành công và chuyển hướng tới /reset-password
    resp_good_otp = client.post('/verify-reset-password', data={'code': otp}, follow_redirects=False)
    assert resp_good_otp.status_code == 302
    assert '/reset-password' in resp_good_otp.headers['Location']

    with client.session_transaction() as sess:
        assert sess['pending_reset_password']['verified'] is True

    # Bước 4: Thử đặt mật khẩu mới YẾU (thiếu ký tự đặc biệt, hoa, v.v...) -> Bị từ chối
    resp_weak = client.post('/reset-password', data={
        'password': 'weakpassword123',
        'confirm_password': 'weakpassword123'
    }, follow_redirects=True)
    assert resp_weak.status_code == 200
    assert "Mật khẩu phải chứa ít nhất một chữ cái in hoa" in resp_weak.get_data(as_text=True)

    # Bước 5: Thử đặt mật khẩu mới xác nhận không khớp -> Bị từ chối
    resp_mismatch = client.post('/reset-password', data={
        'password': 'NewPassword@2026',
        'confirm_password': 'DifferentPassword@2026'
    }, follow_redirects=True)
    assert resp_mismatch.status_code == 200
    assert "Mật khẩu xác nhận không trùng khớp" in resp_mismatch.get_data(as_text=True)

    # Bước 6: Đặt mật khẩu mới MẠNH và ĐẠT CHUẨN -> Thành công
    resp_success = client.post('/reset-password', data={
        'password': 'NewSecurePassword@2026',
        'confirm_password': 'NewSecurePassword@2026'
    }, follow_redirects=True)
    assert resp_success.status_code == 200
    assert "Đặt lại mật khẩu thành công" in resp_success.get_data(as_text=True)

    # Bước 7: Thử đăng nhập bằng mật khẩu MỚI
    resp_new_login = client.post('/login', data={'username': 'user1', 'password': 'NewSecurePassword@2026'}, follow_redirects=False)
    assert resp_new_login.status_code == 302
    assert '/verify-login-otp' in resp_new_login.headers['Location']
