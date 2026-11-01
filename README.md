# 🛡️ VulnShop Lab - Ứng Dụng Web Bán Hàng Có Chủ Đích Chứa Lỗ Hổng Bảo Mật

**VulnShop Lab** là một ứng dụng thương mại điện tử hoàn chỉnh viết bằng **Python Flask** và **SQLite**, được thiết kế có chủ đích chứa 9 bài thực hành an toàn thông tin theo chuẩn **OWASP Top 10**. Ứng dụng được tối ưu hóa đặc biệt để chạy trong môi trường lab cục bộ trên **Kali Linux** hoặc bất kỳ hệ điều hành nào thông qua **Docker Compose**, với cấu hình bảo mật nghiêm ngặt **chỉ bind vào `127.0.0.1`**.

---

## 📑 MỤC LỤC
1. [Tính Năng Chính](#1-tính-năng-chính)
2. [Danh Sách 9 Bài Lab Bảo Mật](#2-danh-sách-9-bài-lab-bảo-mật)
3. [Tài Khoản Mẫu Trắc Nghiệm](#3-tài-khoản-mẫu-trắc-nghiệm)
4. [Hướng Dẫn Cài Đặt & Khởi Chạy Trên Kali Linux](#4-hướng-dẫn-cài-đặt--khởi-chạy-trên-kali-linux)
   - [Phương án 1: Sử dụng Docker Compose (Khuyến nghị)](#phương-án-1-chạy-bằng-docker-compose)
   - [Phương án 2: Chạy trực tiếp bằng Python 3](#phương-án-2-chạy-trực-tiếp-bằng-python-3)
5. [Cấu Trúc Thư Mục Dự Án](#5-cấu-trúc-thư-mục-dự-án)
6. [Trung Tâm Điều Khiển Lab (Lab Hub)](#6-trung-tâm-điều-khiển-lab-lab-hub)
7. [Báo Cáo Kiểm Thử Thực Tế](#7-báo-cáo-kiểm-thử-thực-tế)

---

## 1. TÍNH NĂNG CHÍNH

### 🛍️ Chức năng thương mại điện tử:
- **Xác thực:** Đăng ký tài khoản mới, đăng nhập, đăng xuất, lưu phiên làm việc an toàn.
- **Danh mục & Tìm kiếm:** Danh sách sản phẩm, lọc theo danh mục, tìm kiếm theo từ khóa.
- **Chi tiết & Đánh giá:** Xem chi tiết sản phẩm, hệ thống bình luận và chấm điểm sao.
- **Giỏ hàng & Đặt hàng:** Thêm sản phẩm, cập nhật số lượng, xóa sản phẩm, đặt hàng thanh toán giả lập (COD, Chuyển khoản, Ví điện tử). *Không tích hợp cổng thanh toán thật hay gửi email thật.*
- **Hồ sơ cá nhân:** Xem thông tin cá nhân, cập nhật địa chỉ giao hàng, lịch sử đơn hàng.
- **Quản trị hệ thống (Admin Dashboard):** Thống kê doanh thu, số lượng đơn hàng, CRUD sản phẩm, quản lý tài khoản người dùng, đổi trạng thái đơn hàng.

### 🔬 Chức năng hỗ trợ thực hành an ninh mạng:
- **Chế độ kép độc lập (Vulnerable / Fixed):** Mỗi bài lab có công tắc riêng biệt có thể bật hoặc tắt tức thì từ giao diện Web UI hoặc qua API.
- **Không xung đột:** Lỗ hổng ở bài lab này được cô lập hoàn toàn, không làm ảnh hưởng đến tính đúng đắn của các bài lab khác.
- **Khôi phục dữ liệu mẫu (1-Click Reset Database):** Xóa sạch mọi thay đổi trong quá trình kiểm thử và nạp lại dữ liệu chuẩn ban đầu.
- **Tài liệu & Gợi ý tích hợp:** Mỗi bài lab đều có mục tiêu, gợi ý (ẩn mặc định), phân tích nguyên nhân và so sánh mã nguồn trực quan (Code Diff).

---

## 2. DANH SÁCH 12 BÀI LAB BẢO MẬT

| STT | Bài Lab | Danh Mục | Độ Khó | Endpoint Liên Quan | Phương Thức |
|:---:|:---|:---|:---:|:---|:---:|
| **1** | **Reflected XSS** | Web Security | Dễ | `/search?q=...` | `GET` |
| **2** | **Stored XSS** | Web Security | Trung bình | `/product/<id>/comment` | `POST` |
| **3** | **DOM-based XSS** | Client Security | Trung bình | `/product/<id>#promo=...` | `GET` |
| **4** | **SQL Injection** | Database Security | Dễ | `/products/filter` | `GET` |
| **5** | **IDOR** | Access Control | Dễ | `/orders/<id>` & `/api/orders/<id>` | `GET` |
| **6** | **Broken Access Control** | Access Control | Trung bình | `/api/admin/orders/<id>/status` | `POST` |
| **7** | **CSRF** | Session Security | Trung bình | `/profile/update-address` | `POST` |
| **8** | **Business Logic Flaw** | Business Logic | Dễ | `/cart/checkout` | `POST` |
| **9** | **Security Misconfiguration** | Server Security | Dễ | `/api/system/debug-info` | `GET` |
| **10** | **OS Command Injection** | Command Injection | Trung bình | `/tools/ping` | `POST` |
| **11** | **Insecure File Upload & WebShell** | Core Language & RCE | Khó | `/tools/upload-file` | `POST` |
| **12** | **Denial of Service (ReDoS)** | Denial of Service | Trung bình | `/tools/validate-coupon` | `POST` |

> 📖 *Xem hướng dẫn chi tiết từng bài lab, cơ chế khai thác và phòng thủ tại tệp:* [`docs/SECURITY_LABS.md`](docs/SECURITY_LABS.md)

---

## 3. TÀI KHOẢN MẪU TRẮC NGHIỆM

Hệ thống được khởi tạo sẵn 3 tài khoản mẫu phục vụ các kịch bản kiểm thử phân quyền và leo thang đặc quyền:

| Tên Đăng Nhập | Mật Khẩu | Vai Trò (Role) | Mô Tả & Mục Đích Lab |
|:---|:---|:---:|:---|
| `admin` | `Admin@123` | **admin** | Quản trị viên hệ thống (truy cập Dashboard, quản lý sản phẩm, đơn hàng). |
| `user1` | `User@123` | **user** | Khách hàng mẫu 1 (sở hữu đơn hàng #1, #2; dùng để kiểm thử IDOR, BAC, CSRF). |
| `user2` | `User@123` | **user** | Khách hàng mẫu 2 (sở hữu đơn hàng #3; mục tiêu kiểm thử xem trộm đơn hàng IDOR). |

*(Trên giao diện trang Đăng nhập có sẵn các nút bấm điền nhanh để tiện thao tác trên trình duyệt Kali Linux).*

---

## 4. HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY TRÊN KALI LINUX

### Phương án 1: Chạy bằng Docker Compose (Khuyến nghị)

Ứng dụng cấu hình chỉ mở cổng tại địa chỉ loopback cục bộ: `127.0.0.1:5000:5000`.

1. **Mở Terminal trên Kali Linux và di chuyển vào thư mục dự án:**
   ```bash
   cd "d:/code app và lỗ hổng" # Hoặc đường dẫn thư mục bạn đặt mã nguồn
   ```

2. **Khởi chạy bằng Docker Compose:**
   ```bash
   docker compose up -d --build
   ```

3. **Kiểm tra trạng thái container:**
   ```bash
   docker compose ps
   ```

4. **Truy cập ứng dụng trên trình duyệt của Kali Linux (Firefox):**
   - Trang chủ cửa hàng: [http://127.0.0.1:5000](http://127.0.0.1:5000)
   - Trung tâm Quản lý Lab: [http://127.0.0.1:5000/labs](http://127.0.0.1:5000/labs)

5. **Dừng hệ thống khi kết thúc buổi thực hành:**
   ```bash
   docker compose down
   ```

---

### Phương án 2: Chạy trực tiếp bằng Python 3

Nếu không muốn dùng Docker, bạn có thể chạy trực tiếp bằng Python:

1. **Tạo và kích hoạt môi trường ảo (Virtualenv):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Cài đặt các gói phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Khởi tạo cơ sở dữ liệu mẫu:**
   ```bash
   python scripts/init_db.py
   ```

4. **Khởi chạy ứng dụng:**
   ```bash
   python run.py
   ```
   *(Mặc định `run.py` chỉ bind vào `127.0.0.1:5000`).*

---

## 5. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
.
├── app/
│   ├── __init__.py            # Flask application factory, error handlers, Jinja processors
│   ├── config.py              # Cấu hình hệ thống và mock parameters
│   ├── database.py            # SQLite connection, schema definition, seed/reset logic
│   ├── decorators.py          # @login_required, @admin_required, verify_csrf_token
│   ├── lab_data.py            # Cơ sở tri thức 9 bài lab, gợi ý, lời giải, code diff
│   ├── routes/
│   │   ├── main.py            # Trang chủ, tìm kiếm (Reflected XSS), lọc nâng cao (SQLi)
│   │   ├── auth.py            # Đăng ký, đăng nhập, logout, profile (CSRF)
│   │   ├── product.py         # Chi tiết sản phẩm, bình luận (Stored XSS), banner (DOM XSS)
│   │   ├── cart.py            # Giỏ hàng, đặt hàng (Business Logic), xem hóa đơn (IDOR)
│   │   ├── admin.py           # Quản trị sản phẩm, người dùng, API quản trị (BAC)
│   │   ├── lab.py             # Lab Center hub, toggle API, reset database API
│   │   └── debug.py           # Endpoint debug thông tin hệ thống (Security Misconfiguration)
│   ├── static/
│   │   ├── css/style.css      # Giao diện hiện đại, responsive, dark-mode, lab switches
│   │   └── js/
│   │       ├── main.js        # DOM XSS handler, quick login, toast notifications
│   │       └── lab.js         # Real-time AJAX toggle switch, accordions, reset modal
│   └── templates/             # Toàn bộ template Jinja2 giao diện tiếng Việt
├── docs/
│   └── SECURITY_LABS.md       # Tài liệu chi tiết 9 bài lab bảo mật và hướng dẫn khắc phục
├── scripts/
│   ├── init_db.py             # Script tạo bảng và nạp dữ liệu mẫu ban đầu
│   └── reset_db.py            # Script độc lập reset cơ sở dữ liệu về ban đầu
├── tests/
│   └── test_labs.py           # Bộ kiểm thử tự động so sánh chế độ Vulnerable vs Fixed
├── compose.yaml               # Docker Compose cấu hình bind 127.0.0.1:5000
├── Dockerfile                 # Dockerfile tối ưu trên nền python:3.11-slim
├── requirements.txt           # Danh mục thư viện Python
├── run.py                     # Entrypoint khởi chạy ứng dụng
└── README.md                  # Hướng dẫn sử dụng và báo cáo kiểm thử
```

---

## 6. TRUNG TÂM ĐIỀU KHIỂN LAB (LAB HUB)

Truy cập đường dẫn: **`http://127.0.0.1:5000/labs`**

- **Công tắc Toggle:** Bấm công tắc bên cạnh từng bài để chuyển tức thời giữa chế độ `🔴 Vulnerable` (có lỗ hổng) và `🟢 Fixed` (đã vá lỗi). Trạng thái được lưu trong bảng `lab_settings` của CSDL SQLite.
- **Nút "Khôi phục dữ liệu mẫu":** Bấm nút trên thanh công cụ để đưa cơ sở dữ liệu về nguyên bản ban đầu chỉ với 1 cú click.
- **Accordion thông minh:** Các phần *Gợi ý phân tích* và *Hướng dẫn xác thực cơ chế* được ẩn mặc định để người học tự suy nghĩ trước khi xem đáp án.

---

## 7. BÁO CÁO KIỂM THỬ THỰC TẾ

> ⚠️ **Cam kết trung thực:** Toàn bộ kết quả dưới đây đều được chạy thực tế trên máy thử nghiệm thông qua bộ test `tests/test_labs.py` và môi trường Python 3.11.

### Kết quả chạy kiểm thử tự động (Pytest):
```bash
python -m pytest tests/test_labs.py -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: d:\code app và lỗ hổng
collected 9 items

tests/test_labs.py::test_reflected_xss PASSED                            [ 11%]
tests/test_labs.py::test_stored_xss PASSED                               [ 22%]
tests/test_labs.py::test_dom_xss PASSED                                  [ 33%]
tests/test_labs.py::test_sql_injection PASSED                            [ 44%]
tests/test_labs.py::test_idor PASSED                                     [ 55%]
tests/test_labs.py::test_broken_access_control PASSED                    [ 66%]
tests/test_labs.py::test_csrf PASSED                                     [ 77%]
tests/test_labs.py::test_business_logic PASSED                           [ 88%]
tests/test_labs.py::test_security_misconfiguration PASSED                [100%]

============================== 9 passed in 6.53s ==============================
```

### Chi tiết các chức năng đã kiểm thử thực tế:
1. **Khởi tạo và khôi phục CSDL (`init_db.py`, `reset_db.py`):** Đã chạy thực tế, khởi tạo bảng thành công, nạp tài khoản mẫu, sản phẩm và đơn hàng giả lập.
2. **Reflected XSS:** Đã kiểm thử thực tế qua test client: chuỗi `<script>alert(1)</script>` được phản chiếu nguyên bản khi bật Vulnerable và được chuyển đổi thành `&lt;script&gt;` khi chuyển sang Fixed.
3. **Stored XSS:** Đã kiểm thử thực tế: nội dung bình luận chứa thẻ HTML được render trực tiếp khi Vulnerable và được auto-escape an toàn khi Fixed.
4. **DOM-based XSS:** Đã kiểm thử thực tế cờ `data-dom-vuln` chuyển đổi chính xác giữa `true` và `false`.
5. **SQL Injection:** Đã kiểm thử thực tế: chuỗi `' OR '1'='1` can thiệp vào câu lệnh SQL nối chuỗi thô khi Vulnerable và được xử lý an toàn bằng Parameterized Query (`?`) khi Fixed.
6. **IDOR:** Đã kiểm thử thực tế: `user1` xem được đơn hàng của `user2` khi Vulnerable (200 OK) và bị máy chủ chặn với mã `403 Forbidden` khi Fixed.
7. **Broken Access Control:** Đã kiểm thử thực tế: người dùng thường gọi được API quản trị khi Vulnerable (200 OK) và bị máy chủ từ chối với mã `403 Forbidden` khi Fixed.
8. **CSRF:** Đã kiểm thử thực tế: yêu cầu cập nhật địa chỉ thiếu token được chấp nhận khi Vulnerable (302 Redirect) và bị từ chối với mã `403 Forbidden` khi Fixed.
9. **Business Logic:** Đã kiểm thử thực tế: đặt sản phẩm Laptop 21.500.000 đ với giá 1.000 đ được chấp nhận khi Vulnerable (tổng tiền 1.000 đ) và bị ghi đè chuẩn xác về giá gốc 21.500.000 đ khi Fixed.
10. **Security Misconfiguration:** Đã kiểm thử thực tế: lộ `MOCK_PAYMENT_SECRET_KEY` khi Vulnerable và trả về `status: healthy` an toàn khi Fixed.
