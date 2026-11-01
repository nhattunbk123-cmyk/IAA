from functools import wraps
from flask import session, redirect, url_for, request, jsonify, abort, render_template
import secrets
from app.database import is_lab_vulnerable

def login_required(f):
    """Bắt buộc người dùng phải đăng nhập trước khi truy cập."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập để thực hiện thao tác này.'}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Bắt buộc quyền quản trị viên (Admin) cho các trang quản trị chính thống."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        if session.get('role') != 'admin':
            return render_template('errors/403.html', message="Bạn không có quyền truy cập trang quản trị."), 403
        return f(*args, **kwargs)
    return decorated_function

def get_or_create_csrf_token():
    """Tạo hoặc lấy token CSRF của phiên hiện tại."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(24)
    return session['csrf_token']

def verify_csrf_token():
    """Kiểm tra CSRF token dựa trên trạng thái của bài lab CSRF."""
    # Nếu bài lab CSRF đang ở chế độ Vulnerable: bỏ qua kiểm tra hoàn toàn
    if is_lab_vulnerable('csrf'):
        return True
    
    # Nếu ở chế độ Fixed: bắt buộc kiểm tra token hợp lệ
    token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
    session_token = session.get('csrf_token')
    
    if not token or not session_token or token != session_token:
        return False
    return True
