"""
Tệp kiểm tra kết nối gửi Gmail SMTP trực tiếp (Python thuần, không cần cài đặt thêm thư viện)
Sử dụng tài khoản: testhieu652@gmail.com
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER = "testhieu652@gmail.com"
PASSWORD = "anisjbxkpobxvrlk"

print("=" * 60)
print("  KIỂM TRA GỬI MÃ OTP QUA GMAIL SMTP - LAPTOP52H.VN")
print("=" * 60)

# Nhập email người nhận
target_email = input("Nhập địa chỉ Gmail người nhận (mặc định: testhieu652@gmail.com): ").strip()
if not target_email:
    target_email = "testhieu652@gmail.com"

otp_code = "868686"

msg = MIMEMultipart('alternative')
msg['Subject'] = f"[Laptop52h.vn] Mã OTP kiểm tra kết nối: [{otp_code}]"
msg['From'] = f"Laptop52h.vn Security <{SENDER}>"
msg['To'] = target_email

body = f"""Laptop52h.vn - Xác thực kết nối SMTP
Xin chào,
Mã OTP thử nghiệm của bạn là: {otp_code}
Được gửi từ: {SENDER}
"""
msg.attach(MIMEText(body, 'plain', 'utf-8'))

print(f"\n[*] Đang kết nối tới máy chủ Google SMTP (smtp.gmail.com:587)...")
try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
        server.starttls()
        print(f"[*] Đang xác thực với tài khoản {SENDER}...")
        server.login(SENDER, PASSWORD)
        print(f"[*] Đang gửi email tới {target_email}...")
        server.sendmail(SENDER, target_email, msg.as_string())
    print(f"\n[+] THÀNH CÔNG! Đã gửi mã OTP [{otp_code}] tới hòm thư: {target_email}")
    print("[+] Hãy mở hộp thư (kiểm tra cả mục Hộp thư đến và Thư rác/Spam) để kiểm tra!")
except Exception as e:
    print(f"\n[-] THẤT BẠI: {e}")
    print("[-] Hướng dẫn khắc phục:")
    print("    1. Kiểm tra máy tính có kết nối mạng Internet hay không.")
    print("    2. Kiểm tra mạng Wi-Fi (trường học/công ty) có chặn cổng gửi thư 587 hay không.")
    print("    3. Kiểm tra thông tin tài khoản và mật khẩu ứng dụng Google.")
print("=" * 60)
