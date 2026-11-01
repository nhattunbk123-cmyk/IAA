# TÀI LIỆU HƯỚNG DẪN BẢO MẬT & CẤU HÌNH HỆ THỐNG LAPTOP52H.VN

> **Ngày cập nhật:** 01/11/2026  
> **Trạng thái:** Đã triển khai và kiểm thử 100% thành công (10/10 automated tests passed).

---

## 1. THÔNG TIN CẤU HÌNH GMAIL SMTP THỰC TẾ

Hệ thống đã được tích hợp giao thức **Gmail SMTP** chính thức để tự động gửi mã OTP xác thực tới hộp thư Gmail của người dùng.

- **Tệp lưu cấu hình:** `.env` (thư mục gốc dự án)
- **Tài khoản Gmail gửi thư:** `testhieu652@gmail.com`
- **Mật khẩu ứng dụng (Google App Password):** `anisjbxkpobxvrlk`
- **Máy chủ SMTP:** `smtp.gmail.com`
- **Cổng kết nối:** `587`
- **Giao thức mã hóa:** `STARTTLS`
- **Tên người gửi:** `Laptop52h.vn Security`

---

## 2. CÁC TÍNH NĂNG BẢO MẬT ĐÃ HOÀN TẤT

### 2.1. Đăng ký tài khoản mới (`/register`)
1. **Kiểm tra mật khẩu mạnh:**
   - Độ dài tối thiểu: từ 8 ký tự trở lên.
   - Bắt buộc chứa: Chữ in hoa (`A-Z`), chữ in thường (`a-z`), chữ số (`0-9`), ký tự đặc biệt (`!@#$%^&*...`).
   - Có thanh đo độ mạnh mật khẩu và danh sách tích xanh 5 tiêu chuẩn theo thời gian thực.
2. **Xác thực qua Gmail:**
   - Sinh mã OTP 6 số ngẫu nhiên chuẩn an toàn mật mã.
   - Gửi thư trực tiếp tới địa chỉ Gmail người dùng nhập khi đăng ký.
   - Chuyển hướng tới trang xác thực (`/verify-register-otp`).
   - **Tuyệt đối không hiển thị mã trên giao diện web** (mã chỉ nằm trong hộp thư Gmail).
   - Có đếm ngược hiệu lực 5 phút và nút **Gửi lại mã OTP**.
   - Nhập đúng mã 6 số mới chính thức tạo tài khoản và tự động đăng nhập.

### 2.2. Đăng nhập hệ thống (`/login`)
1. **Chống Brute-force & Khóa tài khoản:**
   - Hệ thống theo dõi số lần đăng nhập sai liên tiếp.
   - **Nhập sai 5 lần liên tiếp sẽ tự động khóa tài khoản trong 5 phút**.
   - Trong thời gian bị khóa, dù nhập đúng mật khẩu hệ thống vẫn từ chối và báo rõ thời gian còn lại.
2. **Bảo mật 2 lớp (2FA qua Gmail):**
   - Khi nhập đúng mật khẩu, hệ thống sinh mã OTP 6 số mới và gửi về Gmail của tài khoản đó.
   - Chuyển hướng tới trang `/verify-login-otp`.
   - Nhập đúng mã 6 số từ Gmail để hoàn tất đăng nhập.

### 2.3. Quên mật khẩu & Đặt lại mật khẩu (`/forgot-password`)
1. **Yêu cầu bằng Gmail:**
   - Người dùng bấm vào nút **"Quên mật khẩu?"** trên form đăng nhập.
   - Nhập địa chỉ Gmail đăng ký (ví dụ: `phanhieu03022005@gmail.com` hoặc `testhieu652@gmail.com`).
   - Hệ thống tự động gửi mã OTP 6 số về Gmail đó.
2. **Bắt buộc xác thực OTP mới được đổi:**
   - Chỉ khi nhập chính xác mã OTP 6 số từ Gmail thì hệ thống mới cho phép mở trang `/reset-password`.
   - Cố tình truy cập thẳng vào trang đổi mật khẩu sẽ bị hệ thống phát hiện và chặn lại.
3. **Mật khẩu mới bắt buộc phải mạnh:**
   - Kiểm tra đầy đủ 5 tiêu chuẩn bảo mật mật khẩu mạnh.
   - Kiểm tra mật khẩu xác nhận trùng khớp.
   - Sau khi đổi thành công: Tự động mở khóa tài khoản (nếu trước đó bị khóa 5 phút) và chuyển về trang đăng nhập.

### 2.4. Google Authenticator (TOTP RFC 6238)
- Người dùng có thể quét mã QR Code trên trang Hồ sơ cá nhân (`/profile`) để liên kết với ứng dụng **Google Authenticator** trên điện thoại.
- Mã biến đổi mỗi 30 giây theo chuẩn thời gian thực.

---

## 3. DANH SÁCH TÀI KHOẢN MẪU & THỬ NGHIỆM

| Tên đăng nhập | Mật khẩu | Email nhận OTP | Vai trò |
| :--- | :--- | :--- | :--- |
| `hieu` | *(Đặt lại qua Quên MK)* | `phanhieu03022005@gmail.com` | Khách hàng |
| `hoangnhatdan123` | `12345678` | `testhieu652@gmail.com` | Quản trị viên (Admin) |
| `user1` | `User@123` | `testhieu652@gmail.com` | Khách hàng |

---

## 4. HƯỚNG DẪN KHỞI CHẠY & KIỂM THỬ

### 4.1. Khởi chạy bằng Docker (Khuyên dùng)
Dự án đã được đóng gói hoàn chỉnh bằng Dockerfile và Docker Compose:

1. **Khởi chạy container ngầm (Background):**
   ```bash
   docker compose up -d --build
   ```
2. **Kiểm tra trạng thái container:**
   ```bash
   docker compose ps
   ```
3. **Xem nhật ký hoạt động (Logs):**
   ```bash
   docker compose logs -f
   ```
4. **Dừng container khi không sử dụng:**
   ```bash
   docker compose down
   ```
5. **Chạy bộ kiểm thử tự động ngay trong Docker:**
   ```bash
   docker compose exec vulnshop python -m pytest tests/test_auth_security.py -v
   ```

Máy chủ Docker sẽ tự động ánh xạ vào: **`http://127.0.0.1:5000`**

---

### 4.2. Khởi chạy cục bộ (Không dùng Docker)
Nếu không dùng Docker, bạn có thể chạy trực tiếp bằng Python:
```bash
python run.py
```
Máy chủ sẽ hoạt động tại: **`http://127.0.0.1:5000`**

### Kiểm thử tự động trên máy cục bộ:
```bash
python -m pytest tests/test_auth_security.py -v
```
*(Kết quả: 10/10 test cases passed).*

---

## 5. TỆP MẪU PHP CHO DỰ ÁN KHÁC
Đã lưu sẵn tệp [`send_otp_example.php`](file:///a:/web%20laptop52h.vn/send_otp_example.php) ở thư mục gốc để bạn sử dụng cho các dự án PHP & PHPMailer.
