import io
import re
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def validate_password_strength(password: str):
    """
    Kiểm tra độ mạnh của mật khẩu theo chuẩn bảo mật:
    - Độ dài tối thiểu 8 ký tự
    - Chứa ít nhất một chữ in hoa (A-Z)
    - Chứa ít nhất một chữ in thường (a-z)
    - Chứa ít nhất một chữ số (0-9)
    - Chứa ít nhất một ký tự đặc biệt (!@#$%^&*...)
    
    Trả về: (is_valid: bool, error_message: str)
    """
    if not password or len(password) < 8:
        return False, "Mật khẩu phải có độ dài tối thiểu từ 8 ký tự trở lên."
    
    if not re.search(r"[A-Z]", password):
        return False, "Mật khẩu phải chứa ít nhất một chữ cái in hoa (A-Z)."
        
    if not re.search(r"[a-z]", password):
        return False, "Mật khẩu phải chứa ít nhất một chữ cái in thường (a-z)."
        
    if not re.search(r"\d", password):
        return False, "Mật khẩu phải chứa ít nhất một chữ số (0-9)."
        
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]", password):
        return False, "Mật khẩu phải chứa ít nhất một ký tự đặc biệt (ví dụ: !@#$%^&*...)."
        
    return True, ""

def check_account_lockout(user):
    """
    Kiểm tra xem tài khoản có đang bị khóa do nhập sai mật khẩu 5 lần hay không.
    Trả về: (is_locked: bool, message: str, remaining_seconds: int)
    """
    locked_until_str = user['locked_until'] if 'locked_until' in user.keys() else None
    if not locked_until_str:
        return False, "", 0
        
    try:
        locked_until = datetime.strptime(locked_until_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        
        if now < locked_until:
            diff = int((locked_until - now).total_seconds())
            minutes = diff // 60
            seconds = diff % 60
            time_str = f"{minutes} phút {seconds} giây" if minutes > 0 else f"{seconds} giây"
            msg = f"Tài khoản của bạn tạm thời bị khóa do nhập sai mật khẩu 5 lần liên tiếp. Vui lòng thử lại sau {time_str}."
            return True, msg, diff
    except Exception:
        pass
        
    return False, "", 0

def record_failed_login(db, user):
    """
    Ghi nhận một lần đăng nhập thất bại.
    Nếu đạt 5 lần liên tiếp -> Khóa tài khoản trong 5 phút.
    Trả về: (is_locked: bool, error_msg: str)
    """
    current_attempts = (user['failed_attempts'] if 'failed_attempts' in user.keys() and user['failed_attempts'] else 0) + 1
    now = datetime.now()
    
    if current_attempts >= 5:
        # Khóa tài khoản 5 phút
        locked_until = (now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        db.execute("""
            UPDATE users 
            SET failed_attempts = ?, locked_until = ?
            WHERE id = ?
        """, (current_attempts, locked_until, user['id']))
        db.commit()
        return True, "Bạn đã nhập sai mật khẩu 5 lần liên tiếp! Tài khoản đã bị tạm khóa trong 5 phút để bảo vệ an toàn."
    else:
        db.execute("""
            UPDATE users 
            SET failed_attempts = ?
            WHERE id = ?
        """, (current_attempts, user['id']))
        db.commit()
        remaining = 5 - current_attempts
        return False, f"Tên đăng nhập hoặc mật khẩu không chính xác. (Bạn còn {remaining} lần thử trước khi tài khoản bị khóa 5 phút)"

def reset_failed_login(db, user_id):
    """Đặt lại số lần đăng nhập sai về 0 và gỡ khóa khi đăng nhập thành công."""
    try:
        db.execute("""
            UPDATE users 
            SET failed_attempts = 0, locked_until = NULL
            WHERE id = ?
        """, (user_id,))
        db.commit()
    except Exception:
        pass

# ==============================================================================
# HÀM XỬ LÝ MÃ OTP GỬI QUA GMAIL THẬT (GMAIL SMTP)
# ==============================================================================

def generate_otp_code(length: int = 6) -> str:
    """Sinh mã OTP 6 chữ số ngẫu nhiên chuẩn an toàn mật mã."""
    return "".join(secrets.choice("0123456789") for _ in range(length))

def mask_email(email: str) -> str:
    """Ẩn một phần email để hiển thị an toàn trên giao diện (ví dụ ph***@gmail.com)."""
    if not email or '@' not in email:
        return email or ''
    parts = email.split('@', 1)
    user_part = parts[0]
    domain_part = parts[1]
    if len(user_part) <= 2:
        masked = user_part[0] + "***"
    else:
        masked = user_part[:2] + "***"
    return f"{masked}@{domain_part}"

def send_otp_email(recipient_email: str, recipient_name: str, otp_code: str, purpose: str = "xác thực tài khoản") -> tuple[bool, str]:
    """
    Gửi mã xác thực OTP 6 số tới hòm thư Gmail của người dùng qua giao thức Gmail SMTP.
    Sử dụng tài khoản testhieu652@gmail.com và Google App Password.
    
    Trả về: (thành_công: bool, thông_báo_lỗi: str)
    """
    try:
        # Lấy thông tin cấu hình từ Flask config hoặc biến môi trường
        mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port = int(os.environ.get('MAIL_PORT', 587))
        mail_user = os.environ.get('MAIL_USERNAME', 'testhieu652@gmail.com')
        mail_pass = os.environ.get('MAIL_PASSWORD', 'anisjbxkpobxvrlk')
        sender_name = "Laptop52h.vn Security"

        # Nếu email người nhận là email mẫu (mock / lab / example), tự động chuyển tiếp tới mail_user để người test nhận được ngay
        target_email = recipient_email
        if (
            not target_email 
            or target_email.endswith('.lab') 
            or target_email.endswith('.example.com') 
            or target_email.endswith('@example.com')
            or target_email.endswith('@laptopaz.vn')
            or target_email.endswith('@laptop52h.vn')
        ):
            print(f"[GMAIL SMTP] Tài khoản mẫu ({recipient_email}), chuyển tiếp OTP về hòm thư test: {mail_user}")
            target_email = mail_user

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Laptop52h.vn] Mã OTP xác thực {purpose}: [{otp_code}]"
        msg['From'] = f"{sender_name} <{mail_user}>"
        msg['To'] = target_email

        # Bản HTML với giao diện chuẩn doanh nghiệp
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f1f5f9; padding: 30px 10px;">
                <tr>
                    <td align="center">
                        <table width="100%" max-width="520" border="0" cellspacing="0" cellpadding="0" style="max-width: 520px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #1d4ed8, #0284c7); padding: 24px 20px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: 0.5px;">💻 Laptop52h.vn</h1>
                                    <p style="color: #bfdbfe; margin: 6px 0 0 0; font-size: 13px;">Hệ Thống Bán Lẻ Laptop & Công Nghệ Hàng Đầu</p>
                                </td>
                            </tr>
                            <!-- Body -->
                            <tr>
                                <td style="padding: 28px 24px; color: #334155;">
                                    <h2 style="color: #0f172a; margin: 0 0 12px 0; font-size: 18px; font-weight: 700;">Xác thực mã bảo mật (OTP)</h2>
                                    <p style="font-size: 14px; line-height: 1.6; margin: 0 0 16px 0;">
                                        Xin chào <strong>{recipient_name}</strong>,<br>
                                        Bạn đang thực hiện thao tác <strong>{purpose}</strong> trên hệ thống Laptop52h.vn.
                                    </p>
                                    <p style="font-size: 14px; line-height: 1.6; margin: 0 0 20px 0;">
                                        Vui lòng sử dụng mã xác thực gồm 6 chữ số dưới đây để hoàn tất:
                                    </p>
                                    
                                    <!-- Khung hiển thị OTP nổi bật -->
                                    <div style="text-align: center; margin: 24px 0;">
                                        <div style="display: inline-block; background-color: #eff6ff; border: 2px dashed #3b82f6; border-radius: 10px; padding: 14px 32px;">
                                            <span style="font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: monospace;">{otp_code}</span>
                                        </div>
                                    </div>

                                    <div style="background-color: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; padding: 12px 16px; margin: 20px 0; font-size: 13px; color: #b91c1c; line-height: 1.5;">
                                        ⏱️ Mã OTP này có hiệu lực trong vòng <strong>5 phút</strong>.<br>
                                        🔒 <strong>Cảnh báo an toàn:</strong> Tuyệt đối không chia sẻ mã này cho bất kỳ ai, kể cả nhân viên hỗ trợ của Laptop52h.vn.
                                    </div>

                                    <p style="font-size: 12px; color: #64748b; margin: 20px 0 0 0; line-height: 1.5;">
                                        Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email hoặc đổi ngay mật khẩu để bảo vệ tài khoản.
                                    </p>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8fafc; padding: 16px 20px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
                                    © 2026 Laptop52h.vn • Hotline: 0825.233.233 • Số 18 ngõ 121 Thái Hà, Hà Nội
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Bản text thuần cho mail client cũ
        text_content = f"""Laptop52h.vn - Mã xác thực OTP
Xin chào {recipient_name},

Mã xác thực {purpose} của bạn là: {otp_code}
Mã này có hiệu lực trong vòng 5 phút.

Tuyệt đối không chia sẻ mã OTP này cho bất kỳ ai!
Hotline hỗ trợ: 0825.233.233
"""

        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # Kết nối tới máy chủ Google SMTP và gửi thư
        print(f"[GMAIL SMTP] Đang gửi mã OTP {otp_code} tới: {target_email}...", flush=True)
        with smtplib.SMTP(mail_server, mail_port, timeout=12) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_user, target_email, msg.as_string())

        print(f"[GMAIL SMTP] ✅ ĐÃ GỬI THÀNH CÔNG mã OTP {otp_code} tới {target_email}!", flush=True)
        return True, ""
    except Exception as e:
        err = str(e)
        print(f"[ERROR] ❌ Không thể gửi Gmail OTP tới {target_email}: {err}", flush=True)
        return False, err

# ==============================================================================
# HỖ TRỢ GOOGLE AUTHENTICATOR (TOTP)
# ==============================================================================
import base64
import pyotp
import qrcode

def generate_totp_secret() -> str:
    """Sinh chuỗi khóa bí mật Base32 ngẫu nhiên cho Google Authenticator."""
    return pyotp.random_base32()

def get_totp_uri(secret: str, username: str) -> str:
    """Tạo URI chuẩn otpauth:// để đồng bộ với Google Authenticator."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name="Laptop52h.vn")

def get_totp_qr_base64(secret: str, username: str) -> str:
    """Tạo ảnh QR Code định dạng PNG Base64 để hiển thị trực tiếp cho camera quét."""
    uri = get_totp_uri(secret, username)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def verify_totp_code(secret: str, code: str) -> bool:
    """Xác thực mã OTP 6 chữ số từ ứng dụng Google Authenticator."""
    if not secret or not code:
        return False
    clean_code = str(code).strip().replace(" ", "").replace("-", "")
    if len(clean_code) != 6 or not clean_code.isdigit():
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(clean_code, valid_window=1))
