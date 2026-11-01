import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, current_app, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db, is_lab_vulnerable
from app.decorators import login_required, get_or_create_csrf_token, verify_csrf_token
from app.security import (
    validate_password_strength,
    check_account_lockout,
    record_failed_login,
    reset_failed_login,
    generate_otp_code,
    mask_email,
    send_otp_email,
    generate_totp_secret,
    get_totp_uri,
    get_totp_qr_base64,
    verify_totp_code
)

auth_bp = Blueprint('auth', __name__)

# ==============================================================================
# 1. ĐĂNG KÝ TÀI KHOẢN VỚI MẬT KHẨU MẠNH & XÁC THỰC GMAIL OTP
# ==============================================================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Đăng ký tài khoản:
    1. Kiểm tra chính sách mật khẩu mạnh.
    2. Gửi mã xác thực OTP 6 số trực tiếp đến hòm thư Gmail đăng ký.
    3. Chuyển sang màn hình xác thực OTP.
    """
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()

        if not username or not password or not full_name or not email:
            flash('Vui lòng điền đầy đủ các thông tin bắt buộc.', 'danger')
            return render_template('auth/register.html')

        # 1. Kiểm tra chính sách mật khẩu mạnh
        is_strong, pass_err = validate_password_strength(password)
        if not is_strong:
            flash(pass_err, 'danger')
            return render_template('auth/register.html')

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
        if existing:
            flash('Tên đăng nhập hoặc địa chỉ email đã tồn tại trên hệ thống.', 'warning')
            return render_template('auth/register.html')

        # 2. Sinh mã OTP 6 số và lưu thông tin tạm vào session (thời hạn 5 phút)
        otp_code = generate_otp_code(6)
        session['pending_register'] = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'full_name': full_name,
            'email': email,
            'address': address,
            'otp': otp_code,
            'expires_at': time.time() + 300  # 5 phút
        }

        # 3. Gửi email OTP thực tế qua Google SMTP
        send_success, err_msg = send_otp_email(email, full_name, otp_code, purpose="đăng ký tài khoản")
        masked = mask_email(email)

        if send_success:
            flash(f'Mã xác thực OTP gồm 6 chữ số đã được gửi đến Gmail: {masked}. Vui lòng kiểm tra hộp thư (cả mục Hộp thư đến hoặc Thư rác/Spam)!', 'info')
        else:
            flash(f'Đã khởi tạo đăng ký cho email {masked}. Vui lòng nhập mã OTP để hoàn tất.', 'info')

        return redirect(url_for('auth.verify_register_otp'))

    return render_template('auth/register.html')


@auth_bp.route('/verify-register-otp', methods=['GET', 'POST'])
def verify_register_otp():
    """
    Trang nhập mã OTP 6 số để kích hoạt tài khoản đăng ký mới.
    Mã chỉ nằm trong hộp thư Gmail người dùng, tuyệt đối không hiển thị trên màn hình.
    """
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    pending = session.get('pending_register')
    if not pending:
        flash('Không tìm thấy phiên đăng ký chờ xác thực. Vui lòng đăng ký lại.', 'warning')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        user_code = request.form.get('code', '').strip().replace(" ", "").replace("-", "")

        # Kiểm tra thời hạn hiệu lực
        if time.time() > pending.get('expires_at', 0):
            flash('Mã xác thực OTP đã hết hạn (sau 5 phút). Vui lòng nhấn "Gửi lại mã OTP" bên dưới!', 'danger')
            return render_template('auth/verify_register_otp.html', masked_email=mask_email(pending['email']))

        # Kiểm tra mã OTP
        if user_code == pending.get('otp'):
            db = get_db()
            cur = db.execute("""
                INSERT INTO users (username, password_hash, full_name, email, address, role)
                VALUES (?, ?, ?, ?, ?, 'user')
            """, (
                pending['username'],
                pending['password_hash'],
                pending['full_name'],
                pending['email'],
                pending['address']
            ))
            db.commit()
            new_user_id = cur.lastrowid

            # Đăng nhập trực tiếp người dùng mới
            session['user_id'] = new_user_id
            session['username'] = pending['username']
            session['full_name'] = pending['full_name']
            session['role'] = 'user'
            session['email'] = pending['email']
            session['address'] = pending['address']
            get_or_create_csrf_token()

            session.pop('pending_register', None)
            flash(f'🎉 Chúc mừng {session["full_name"]}! Bạn đã kích hoạt tài khoản thành công qua Gmail.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Mã xác thực OTP không chính xác. Vui lòng kiểm tra lại trong Gmail!', 'danger')

    return render_template('auth/verify_register_otp.html', masked_email=mask_email(pending['email']))


@auth_bp.route('/resend-register-otp', methods=['GET', 'POST'])
def resend_register_otp():
    """Gửi lại mã xác thực OTP đăng ký vào Gmail."""
    pending = session.get('pending_register')
    if not pending:
        flash('Không tìm thấy phiên đăng ký chờ xác thực.', 'warning')
        return redirect(url_for('auth.register'))

    new_otp = generate_otp_code(6)
    pending['otp'] = new_otp
    pending['expires_at'] = time.time() + 300
    session['pending_register'] = pending

    send_otp_email(pending['email'], pending['full_name'], new_otp, purpose="đăng ký tài khoản")
    flash(f'Mã xác thực OTP mới đã được gửi lại vào Gmail: {mask_email(pending["email"])}.', 'success')
    return redirect(url_for('auth.verify_register_otp'))


# ==============================================================================
# 2. ĐĂNG NHẬP VỚI CHỐNG BRUTE-FORCE VÀ XÁC THỰC GMAIL OTP 2 LỚP
# ==============================================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Đăng nhập hệ thống:
    - Chống Brute-force: Khóa tài khoản 5 phút nếu nhập sai mật khẩu 5 lần.
    - Bảo mật 2 lớp: Gửi mã OTP 6 số về Gmail đã đăng ký của tài khoản.
    """
    if 'user_id' in session:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'redirect': url_for('main.index')})
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json

        if not username or not password:
            err_msg = 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.'
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg}), 400
            flash(err_msg, 'danger')
            return render_template('auth/login.html')

        db = get_db()

        # Đảm bảo tài khoản admin hoangnhatdan123 luôn tồn tại
        if username == 'hoangnhatdan123' and password == '12345678':
            admin_check = db.execute("SELECT * FROM users WHERE username = 'hoangnhatdan123'").fetchone()
            if not admin_check:
                db.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, address, role)
                    VALUES ('hoangnhatdan123', ?, 'Hoàng Nhật Đan (Admin)', 'hoangnhatdan@laptop52h.vn', 'Số 18, ngõ 121, Thái Hà, Đống Đa, Hà Nội', 'admin')
                """, (generate_password_hash('12345678'),))
                db.commit()

        # Tìm kiếm tài khoản qua username hoặc email
        user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()

        if not user:
            err_msg = 'Tên đăng nhập hoặc mật khẩu không chính xác.'
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg}), 401
            flash(err_msg, 'danger')
            return render_template('auth/login.html')

        # 1. BẢO MẬT: Kiểm tra xem tài khoản có đang bị khóa (Account Lockout 5 phút)
        is_locked, lock_msg, remaining_sec = check_account_lockout(user)
        if is_locked:
            if is_ajax:
                return jsonify({'success': False, 'message': lock_msg, 'is_locked': True}), 403
            flash(lock_msg, 'danger')
            return render_template('auth/login.html')

        # 2. Kiểm tra mật khẩu
        if check_password_hash(user['password_hash'], password):
            # Mật khẩu đúng -> Đặt lại số lần sai về 0
            reset_failed_login(db, user['id'])

            next_url = request.args.get('next') or request.form.get('next')
            if not next_url or not next_url.startswith('/'):
                next_url = url_for('main.index')

            # 3. GỬI MÃ XÁC THỰC OTP 6 SỐ VỀ GMAIL CỦA TÀI KHOẢN NÀY
            otp_code = generate_otp_code(6)
            session['pending_login_otp'] = {
                'user_id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role'],
                'email': user['email'],
                'address': user['address'],
                'otp': otp_code,
                'expires_at': time.time() + 300,  # 5 phút
                'next_url': next_url
            }

            # Gửi thư qua Gmail SMTP
            send_otp_email(user['email'], user['full_name'], otp_code, purpose="đăng nhập tài khoản")
            masked = mask_email(user['email'])

            if is_ajax:
                return jsonify({
                    'success': True,
                    'require_otp': True,
                    'message': f'Mã xác thực OTP đã được gửi đến Gmail: {masked}',
                    'redirect': url_for('auth.verify_login_otp')
                })

            flash(f'Mã xác thực OTP đã được gửi đến Gmail: {masked}. Vui lòng kiểm tra hòm thư để đăng nhập!', 'info')
            return redirect(url_for('auth.verify_login_otp'))
        else:
            # Mật khẩu sai -> Ghi nhận lần thử thất bại, nếu đủ 5 lần thì khóa 5 phút
            is_now_locked, err_msg = record_failed_login(db, user)
            status_code = 403 if is_now_locked else 401
            if is_ajax:
                return jsonify({'success': False, 'message': err_msg, 'is_locked': is_now_locked}), status_code
            flash(err_msg, 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/verify-login-otp', methods=['GET', 'POST'])
def verify_login_otp():
    """
    Trang xác thực mã OTP 6 số khi đăng nhập.
    Mã được gửi qua Gmail, không hiển thị trên màn hình.
    """
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    pending = session.get('pending_login_otp')
    if not pending:
        flash('Không tìm thấy phiên đăng nhập chờ xác thực OTP. Vui lòng đăng nhập lại.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user_code = request.form.get('code', '').strip().replace(" ", "").replace("-", "")

        # Kiểm tra thời hạn hiệu lực (5 phút)
        if time.time() > pending.get('expires_at', 0):
            flash('Mã xác thực OTP đã hết hạn hiệu lực (sau 5 phút). Vui lòng nhấn "Gửi lại mã OTP" bên dưới!', 'danger')
            return render_template('auth/verify_login_otp.html', masked_email=mask_email(pending['email']))

        # Kiểm tra mã OTP
        if user_code == pending.get('otp'):
            # Xác thực thành công -> Cấp quyền đăng nhập
            session['user_id'] = pending['user_id']
            session['username'] = pending['username']
            session['full_name'] = pending['full_name']
            session['role'] = pending['role']
            session['email'] = pending['email']
            session['address'] = pending['address']
            get_or_create_csrf_token()

            next_url = pending.get('next_url') or url_for('main.index')
            session.pop('pending_login_otp', None)

            role_title = "Quản trị viên" if session['role'] == 'admin' else "Khách hàng"
            flash(f'Chào mừng {role_title}: {session["full_name"]}! Bạn đã đăng nhập thành công.', 'success')
            return redirect(next_url)
        else:
            flash('Mã xác thực OTP không chính xác. Vui lòng kiểm tra lại trong Gmail!', 'danger')

    return render_template('auth/verify_login_otp.html', masked_email=mask_email(pending['email']))


@auth_bp.route('/resend-login-otp', methods=['GET', 'POST'])
def resend_login_otp():
    """Gửi lại mã xác thực OTP đăng nhập vào Gmail."""
    pending = session.get('pending_login_otp')
    if not pending:
        flash('Không tìm thấy phiên đăng nhập.', 'warning')
        return redirect(url_for('auth.login'))

    new_otp = generate_otp_code(6)
    pending['otp'] = new_otp
    pending['expires_at'] = time.time() + 300
    session['pending_login_otp'] = pending

    send_otp_email(pending['email'], pending['full_name'], new_otp, purpose="đăng nhập tài khoản")
    flash(f'Mã xác thực OTP mới đã được gửi lại vào Gmail: {mask_email(pending["email"])}.', 'success')
    return redirect(url_for('auth.verify_login_otp'))


# ==============================================================================
# 3. QUÊN MẬT KHẨU (GỬI MÃ OTP QUA GMAIL & ĐẶT LẠI MẬT KHẨU MẠNH)
# ==============================================================================
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Trang yêu cầu đặt lại mật khẩu: người dùng nhập Gmail."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = (request.form.get('email') or request.form.get('identifier', '')).strip().lower()
        if not email:
            flash('Vui lòng nhập địa chỉ Gmail của bạn.', 'danger')
            return render_template('auth/forgot_password.html')

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?", (email, email)).fetchone()
        if not user:
            flash(f'Không tìm thấy tài khoản nào gắn với địa chỉ Gmail: {email}. Vui lòng kiểm tra lại!', 'danger')
            return render_template('auth/forgot_password.html')

        otp_code = generate_otp_code(6)
        session['pending_reset_password'] = {
            'user_id': user['id'],
            'username': user['username'],
            'full_name': user['full_name'],
            'email': user['email'],
            'otp': otp_code,
            'expires_at': time.time() + 300,  # 5 phút
            'verified': False
        }

        send_otp_email(user['email'], user['full_name'], otp_code, purpose="đặt lại mật khẩu")
        masked = mask_email(user['email'])
        flash(f'Mã xác thực OTP gồm 6 chữ số đã được gửi đến Gmail: {masked}. Vui lòng mở hộp thư để lấy mã!', 'info')
        return redirect(url_for('auth.verify_reset_password'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/verify-reset-password', methods=['GET', 'POST'])
def verify_reset_password():
    """Xác thực mã OTP 6 số để được quyền đổi mật khẩu."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    pending = session.get('pending_reset_password')
    if not pending:
        flash('Không tìm thấy yêu cầu đặt lại mật khẩu. Vui lòng thử lại.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        user_code = request.form.get('code', '').strip().replace(" ", "").replace("-", "")

        if time.time() > pending.get('expires_at', 0):
            flash('Mã xác thực OTP đã hết hạn (sau 5 phút). Vui lòng nhấn "Gửi lại mã OTP" bên dưới!', 'danger')
            return render_template('auth/verify_reset_otp.html', masked_email=mask_email(pending['email']))

        if user_code == pending.get('otp'):
            pending['verified'] = True
            session['pending_reset_password'] = pending
            flash('Xác thực mã OTP thành công! Bây giờ bạn hãy tạo mật khẩu mới cho tài khoản.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('Mã xác thực OTP không chính xác. Vui lòng kiểm tra lại trong Gmail!', 'danger')

    return render_template('auth/verify_reset_otp.html', masked_email=mask_email(pending['email']))


@auth_bp.route('/resend-reset-otp', methods=['GET', 'POST'])
def resend_reset_otp():
    """Gửi lại mã OTP đặt lại mật khẩu."""
    pending = session.get('pending_reset_password')
    if not pending:
        flash('Không tìm thấy phiên làm việc.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    new_otp = generate_otp_code(6)
    pending['otp'] = new_otp
    pending['expires_at'] = time.time() + 300
    session['pending_reset_password'] = pending

    send_otp_email(pending['email'], pending['full_name'], new_otp, purpose="đặt lại mật khẩu")
    flash(f'Mã xác thực OTP mới đã được gửi lại vào Gmail: {mask_email(pending["email"])}.', 'success')
    return redirect(url_for('auth.verify_reset_password'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Trang thiết lập mật khẩu mới (bắt buộc kiểm tra độ mạnh của mật khẩu)."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    pending = session.get('pending_reset_password')
    if not pending or not pending.get('verified'):
        flash('Bạn phải xác thực mã OTP trước khi đổi mật khẩu mới!', 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not password or not confirm_password:
            flash('Vui lòng điền đầy đủ mật khẩu mới và xác nhận mật khẩu.', 'danger')
            return render_template('auth/reset_password.html', username=pending['username'])

        if password != confirm_password:
            flash('Mật khẩu xác nhận không trùng khớp. Vui lòng nhập lại!', 'danger')
            return render_template('auth/reset_password.html', username=pending['username'])

        # BẮT BUỘC KIỂM TRA MẬT KHẨU MẠNH
        is_strong, err_msg = validate_password_strength(password)
        if not is_strong:
            flash(err_msg, 'danger')
            return render_template('auth/reset_password.html', username=pending['username'])

        # Cập nhật mật khẩu mới vào database và mở khóa tài khoản nếu đang bị khóa
        db = get_db()
        hashed_pw = generate_password_hash(password)
        db.execute("""
            UPDATE users 
            SET password_hash = ?, failed_attempts = 0, locked_until = NULL 
            WHERE id = ?
        """, (hashed_pw, pending['user_id']))
        db.commit()

        session.pop('pending_reset_password', None)
        flash('🎉 Đặt lại mật khẩu thành công! Bạn có thể sử dụng mật khẩu mới để đăng nhập ngay.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', username=pending['username'])


# ==============================================================================
# 4. ĐĂNG XUẤT & QUẢN LÝ THÔNG TIN CÁ NHÂN
# ==============================================================================
@auth_bp.route('/logout')
def logout():
    """Đăng xuất phiên làm việc hiện tại."""
    session.clear()
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """Trang thông tin cá nhân và lịch sử đơn hàng."""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    orders = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    
    csrf_token = get_or_create_csrf_token()
    is_csrf_vuln = is_lab_vulnerable('csrf')

    return render_template(
        'profile.html',
        user=user,
        orders=orders,
        csrf_token=csrf_token,
        is_csrf_vuln=is_csrf_vuln
    )


@auth_bp.route('/profile/update-address', methods=['POST'])
@login_required
def update_address():
    """Cập nhật địa chỉ giao hàng cá nhân (CSRF Lab)."""
    is_vuln = is_lab_vulnerable('csrf')
    
    if not is_vuln:
        if not verify_csrf_token():
            return render_template('errors/403.html', message="Lỗi bảo mật CSRF: Token xác thực không hợp lệ hoặc bị thiếu! Yêu cầu bị chặn."), 403

    new_address = request.form.get('address', '').strip()
    if not new_address:
        flash('Địa chỉ không được để trống.', 'warning')
        return redirect(url_for('auth.profile'))

    db = get_db()
    db.execute("UPDATE users SET address = ? WHERE id = ?", (new_address, session['user_id']))
    db.commit()
    session['address'] = new_address

    flash('Cập nhật địa chỉ giao hàng thành công!', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/profile/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Cập nhật ảnh đại diện tài khoản."""
    import uuid
    from werkzeug.utils import secure_filename

    if 'avatar' not in request.files:
        flash('Vui lòng chọn tệp tin ảnh đại diện.', 'warning')
        return redirect(url_for('auth.profile'))

    file = request.files['avatar']
    if not file.filename:
        flash('Chưa có tệp nào được chọn.', 'warning')
        return redirect(url_for('auth.profile'))

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    raw_name = file.filename
    ext = os.path.splitext(raw_name)[1].lower()

    is_vuln = is_lab_vulnerable('file_upload_shell')
    if is_vuln:
        safe_name = f"avatar_{session['user_id']}_{secure_filename(raw_name)}"
        save_path = os.path.join(upload_dir, safe_name)
        file.save(save_path)
        avatar_url = url_for('static', filename=f'uploads/{safe_name}')
        flash(f'Tải lên ảnh đại diện thành công: {safe_name} (Đường dẫn: {avatar_url})', 'success')
    else:
        ALLOWED_EXT = {'.png', '.jpg', '.jpeg', '.webp'}
        if ext not in ALLOWED_EXT:
            flash(f'Lỗi bảo mật: Định dạng tệp {ext} không được phép! Chỉ chấp nhận ảnh ({", ".join(ALLOWED_EXT)}).', 'danger')
            return redirect(url_for('auth.profile'))

        safe_uuid = f"avatar_{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(upload_dir, safe_uuid)
        file.save(save_path)
        avatar_url = url_for('static', filename=f'uploads/{safe_uuid}')
        flash('Cập nhật ảnh đại diện thành công!', 'success')

    session['avatar_url'] = avatar_url
    return redirect(url_for('auth.profile'))
