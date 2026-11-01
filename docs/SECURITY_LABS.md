# TÀI LIỆU CHI TIẾT 12 BÀI LAB BẢO MẬT ỨNG DỤNG WEB (VULNSHOP LAB)

Tài liệu này cung cấp hướng dẫn chuyên sâu, phân tích mã nguồn, cách kiểm chứng an toàn trong môi trường lab cục bộ và giải pháp khắc phục cho toàn bộ 12 bài thực hành an toàn thông tin theo chuẩn OWASP.

---

## MỤC LỤC
1. [Lab 1: Reflected XSS (Cross-Site Scripting Phản Chiếu)](#lab-1-reflected-xss)
2. [Lab 2: Stored XSS (Cross-Site Scripting Lưu Trữ)](#lab-2-stored-xss)
3. [Lab 3: DOM-based XSS (XSS Trên Cấu Trúc DOM)](#lab-3-dom-based-xss)
4. [Lab 4: SQL Injection (Tiêm Lệnh SQL Trực Tiếp)](#lab-4-sql-injection)
5. [Lab 5: Insecure Direct Object References (IDOR)](#lab-5-idor)
6. [Lab 6: Broken Access Control (Thiếu Kiểm Tra Vai Trò Phía Máy Chủ)](#lab-6-broken-access-control)
7. [Lab 7: Cross-Site Request Forgery (CSRF)](#lab-7-csrf)
8. [Lab 8: Business Logic Flaw (Thao Túng Giá Sản Phẩm Phía Client)](#lab-8-business-logic)
9. [Lab 9: Security Misconfiguration (Lộ Thông Tin Cấu Hình & Gỡ Lỗi)](#lab-9-security-misconfiguration)
10. [Lab 10: OS Command Injection (Tiêm Lệnh Hệ Điều Hành)](#lab-10-os-command-injection)
11. [Lab 11: Insecure File Upload & Web Shell (Lỗ Hổng Ngôn Ngữ Cốt Lõi - PHP2Shell)](#lab-11-insecure-file-upload--web-shell)
12. [Lab 12: Denial of Service (ReDoS - Catastrophic Backtracking)](#lab-12-denial-of-service-redos)

---

### LAB 1: REFLECTED XSS
- **Mức độ khó:** Dễ
- **Phân loại:** Web Application Security / Injection
- **Trang & Endpoint:** Trang tìm kiếm (`GET /search?q=...`)
- **Tập tin liên quan:** `app/routes/main.py`, `app/templates/search.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Dữ liệu người dùng gửi lên qua tham số URL `q` được backend đưa vào đối tượng `Markup(query)` hoặc tắt cơ chế auto-escape của Jinja2 (`| safe`), khiến trình duyệt thông dịch trực tiếp các thẻ HTML thay vì đối xử như văn bản thô.
- **Tác động:** Kẻ tấn công có thể lừa người dùng bấm vào liên kết độc hại để thực thi JavaScript trong phiên của họ, đọc thông tin phiên làm việc hoặc giả mạo giao diện trang (Defacement).

#### 2. Cách kiểm chứng an toàn trong Lab
- Truy cập vào: `http://127.0.0.1:5000/search?q=<u style="color:red">Kiem_Thu_Lab</u>`
- **Kết quả khi có lỗ hổng (Vulnerable):** Chữ `Kiem_Thu_Lab` được gạch chân màu đỏ hiển thị trên trang, chứng tỏ thẻ HTML đã được trình duyệt phân tích cú pháp.
- **Kết quả khi đã vá (Fixed):** Trình duyệt hiển thị nguyên bản chuỗi `<u style="color:red">Kiem_Thu_Lab</u>`. Khi xem mã nguồn HTML (View Source), chuỗi đã được mã hóa thành `&lt;u style=...&gt;`.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Sử dụng tính năng Context-aware HTML Encoding mặc định của Jinja2 (`{{ query }}`) hoặc gọi hàm `escape(query)` trong module `markupsafe`.

```python
# [VULNERABLE]
rendered_query = Markup(query)
return render_template('search.html', rendered_query=rendered_query)

# [FIXED]
rendered_query = str(escape(query))
return render_template('search.html', rendered_query=rendered_query)
```

---

### LAB 2: STORED XSS
- **Mức độ khó:** Trung bình
- **Phân loại:** Persistent Injection
- **Trang & Endpoint:** Trang chi tiết sản phẩm (`POST /product/<id>/comment` & `GET /product/<id>`)
- **Tập tin liên quan:** `app/routes/product.py`, `app/templates/product_detail.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Nội dung đánh giá của khách hàng được lưu thô vào cơ sở dữ liệu SQLite bảng `comments`. Khi hiển thị, template sử dụng cú pháp `{{ comment.content | safe }}` vô hiệu hóa cơ chế phòng vệ của Jinja2.
- **Tác động:** Bất kỳ người dùng hoặc quản trị viên nào truy cập vào trang chi tiết sản phẩm đó đều bị mã độc trong bình luận tác động mà không cần phải bấm vào một link cụ thể nào.

#### 2. Cách kiểm chứng an toàn trong Lab
- Truy cập vào sản phẩm bất kỳ (ví dụ ID = 1).
- Trong khung "Bình luận và Đánh giá", nhập nội dung: `<b>Bình luận in đậm thử nghiệm</b>` và bấm "Gửi Đánh Giá".
- **Kết quả khi có lỗ hổng (Vulnerable):** Nội dung hiển thị dạng chữ in đậm.
- **Kết quả khi đã vá (Fixed):** Nội dung hiển thị nguyên trạng chuỗi `<b>Bình luận in đậm thử nghiệm</b>`. Thẻ `<b>` đã được escape thành `&lt;b&gt;`.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Bỏ hoàn toàn bộ lọc `| safe` trên các trường dữ liệu do người dùng tạo ra; áp dụng thư viện sanitize nếu cần cho phép một tập thẻ HTML an toàn.

```html
<!-- [VULNERABLE] -->
<div class="comment-body">{{ comment.content | safe }}</div>

<!-- [FIXED] -->
<div class="comment-body">{{ comment.content }}</div>
```

---

### LAB 3: DOM-BASED XSS
- **Mức độ khó:** Trung bình
- **Phân loại:** Client-side Security
- **Trang & Endpoint:** Trang chi tiết sản phẩm (`GET /product/<id>#promo=...` hoặc `?promo=...`)
- **Tập tin liên quan:** `app/static/js/main.js`, `app/templates/product_detail.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Mã JavaScript client đọc dữ liệu từ `window.location.hash` (Source) và gán trực tiếp vào thuộc tính `.innerHTML` (Sink nguy hiểm) của phần tử `#promo-banner` mà không qua kiểm tra.
- **Tác động:** Lỗ hổng xảy ra hoàn toàn trên trình duyệt; máy chủ backend và WAF không nhận được phần fragment sau dấu `#` nên không thể phát hiện hay ngăn chặn.

#### 2. Cách kiểm chứng an toàn trong Lab
- Mở trình duyệt và truy cập: `http://127.0.0.1:5000/product/1#promo=<b>Ưu_Đãi_Vàng</b>`
- **Kết quả khi có lỗ hổng (Vulnerable):** Banner khuyến mãi hiển thị chữ in đậm do `innerHTML` phân tích cú pháp HTML.
- **Kết quả khi đã vá (Fixed):** Banner sử dụng thuộc tính `textContent`, hiển thị nguyên bản dạng text thuần: `Ưu đãi đặc biệt: Áp dụng mã: <b>Ưu_Đãi_Vàng</b>`.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Thay thế các Sink nguy hiểm (`innerHTML`, `document.write`) bằng các thuộc tính an toàn chỉ xử lý văn bản như `textContent`.

```javascript
// [VULNERABLE]
banner.innerHTML = `<span>Mã ưu đãi: ${promoCode}</span>`;

// [FIXED]
banner.textContent = `Mã ưu đãi: ${promoCode}`;
```

---

### LAB 4: SQL INJECTION
- **Mức độ khó:** Dễ
- **Phân loại:** Database Security / Injection
- **Trang & Endpoint:** Lọc nâng cao (`GET /products/filter?category=...&keyword=...`)
- **Tập tin liên quan:** `app/routes/main.py`, `app/templates/products_filter.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Lập trình viên sử dụng kỹ thuật định dạng chuỗi (`f-string`) để ghép các tham số `keyword` và `category` trực tiếp vào câu lệnh SQL. Ký tự nháy đơn `'` của người dùng làm đóng sớm chuỗi ký tự trong cú pháp SQL.
- **Tác động:** Kẻ tấn công có thể can thiệp cấu trúc logic của truy vấn, vượt qua điều kiện lọc hoặc trích xuất dữ liệu trái phép từ các bảng khác.

#### 2. Cách kiểm chứng an toàn trong Lab
- Truy cập vào trang Lọc Nâng Cao (`/products/filter`).
- Tại ô Keyword, nhập: `Nitro' OR '1'='1`
- **Kết quả khi có lỗ hổng (Vulnerable):** Câu lệnh SQL được hiển thị là: `SELECT * FROM products WHERE (name LIKE '%Nitro' OR '1'='1%')` hoặc phát sinh lỗi cú pháp SQLite khi nhập ký tự `'` đơn lẻ.
- **Kết quả khi đã vá (Fixed):** Backend sử dụng dấu `?` trong truy vấn `SELECT * FROM products WHERE (name LIKE ? OR description LIKE ?)`. Toàn bộ chuỗi nhập vào được truyền dưới dạng dữ liệu tham số, không can thiệp vào cú pháp thực thi.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Luôn sử dụng Parameterized Queries (Prepared Statements) cho mọi truy vấn cơ sở dữ liệu.

```python
# [VULNERABLE]
sql = f"SELECT * FROM products WHERE name LIKE '%{keyword}%' AND category = '{category}'"
cursor.execute(sql)

# [FIXED]
sql = "SELECT * FROM products WHERE name LIKE ? AND category = ?"
cursor.execute(sql, (f"%{keyword}%", category))
```

---

### LAB 5: IDOR (INSECURE DIRECT OBJECT REFERENCES)
- **Mức độ khó:** Dễ
- **Phân loại:** Broken Object Level Authorization (BOLA)
- **Trang & Endpoint:** Chi tiết đơn hàng (`GET /orders/<id>` hoặc `GET /api/orders/<id>`)
- **Tập tin liên quan:** `app/routes/cart.py`, `app/templates/order_detail.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Backend truy vấn đơn hàng chỉ dựa trên ID truyền vào từ URL: `SELECT * FROM orders WHERE id = ?`. Máy chủ không kiểm tra xem trường `order.user_id` có trùng với `session['user_id']` của người dùng đang đăng nhập hay không.
- **Tác động:** Người dùng này có thể xem trái phép toàn bộ lịch sử đơn hàng, địa chỉ nhà riêng và thông tin mua sắm của người dùng khác.

#### 2. Cách kiểm chứng an toàn trong Lab
- Đăng nhập bằng tài khoản `user1` (user_id = 2).
- Truy cập vào: `http://127.0.0.1:5000/orders/3` (Đơn hàng #3 thuộc về `user2`).
- **Kết quả khi có lỗ hổng (Vulnerable):** Toàn bộ hóa đơn của `Trần Thị Bình` (user2) cùng địa chỉ tại TP. Hồ Chí Minh hiển thị đầy đủ.
- **Kết quả khi đã vá (Fixed):** Máy chủ từ chối với trang lỗi `403 Forbidden: Bạn không có quyền truy cập vào đơn hàng của khách hàng khác`.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Thực hiện kiểm tra quyền sở hữu đối tượng ở tầng máy chủ (Server-side Object Authorization).

```python
# [VULNERABLE]
order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
return render_template('order_detail.html', order=order)

# [FIXED]
order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
if order['user_id'] != session['user_id'] and session.get('role') != 'admin':
    abort(403)
return render_template('order_detail.html', order=order)
```

---

### LAB 6: BROKEN ACCESS CONTROL
- **Mức độ khó:** Trung bình
- **Phân loại:** Function Level Access Control
- **Trang & Endpoint:** API quản trị đơn hàng (`POST /api/admin/orders/<id>/status`)
- **Tập tin liên quan:** `app/routes/admin.py`, `app/templates/admin/orders.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Endpoint API quản trị chỉ kiểm tra xem người dùng đã đăng nhập chưa (`@login_required`), nhưng bỏ quên bước kiểm tra vai trò `session.get('role') == 'admin'`.
- **Tác động:** Khách hàng thông thường có thể gọi trực tiếp API này qua công cụ HTTP client (curl, Burp Suite, DevTools) để thay đổi trạng thái đơn hàng (ví dụ chuyển thành "Đã hoàn thành" hoặc "Đã hủy").

#### 2. Cách kiểm chứng an toàn trong Lab
- Đăng nhập bằng tài khoản thường `user1`.
- Mở tab Console trong trình duyệt hoặc sử dụng hộp test trên trang `/admin/orders`, gửi request POST:
```javascript
fetch('/api/admin/orders/1/status', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'Đã hoàn thành' })
}).then(r => r.json()).then(console.log);
```
- **Kết quả khi có lỗ hổng (Vulnerable):** Trả về HTTP 200 OK: `{"success": true, "message": "Đã cập nhật trạng thái..."}`.
- **Kết quả khi đã vá (Fixed):** Trả về HTTP 403 Forbidden: `{"success": false, "message": "Lỗi phân quyền: Bắt buộc quyền Quản trị viên"}`.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Kiểm tra vai trò người dùng chặt chẽ trên mọi endpoint nhạy cảm (Role-Based Access Control).

```python
# [VULNERABLE]
@admin_bp.route('/api/admin/orders/<id>/status', methods=['POST'])
@login_required # Chỉ kiểm tra đăng nhập
def api_update_order_status(order_id):
    ...

# [FIXED]
@admin_bp.route('/api/admin/orders/<id>/status', methods=['POST'])
@login_required
def api_update_order_status(order_id):
    if session.get('role') != 'admin': # Bắt buộc kiểm tra quyền admin
        return jsonify({'success': False, 'message': 'Từ chối truy cập'}), 403
    ...
```

---

### LAB 7: CSRF (CROSS-SITE REQUEST FORGERY)
- **Mức độ khó:** Trung bình
- **Phân loại:** Session Security
- **Trang & Endpoint:** Cập nhật địa chỉ nhận hàng (`POST /profile/update-address`)
- **Tập tin liên quan:** `app/routes/auth.py`, `app/decorators.py`, `app/templates/profile.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Endpoint thay đổi địa chỉ của tài khoản không yêu cầu mã thông báo bí mật (Anti-CSRF Token). Trình duyệt tự động gửi cookie phiên khi người dùng gửi request.
- **Tác động:** Nếu nạn nhân đang đăng nhập và mở một liên kết độc hại do kẻ tấn công chuẩn bị, trang độc hại đó có thể ngầm gửi yêu cầu đổi địa chỉ nhận hàng của nạn nhân thành địa chỉ của kẻ tấn công.

#### 2. Điều kiện tái hiện trong trình duyệt
1. Nạn nhân đã đăng nhập vào hệ thống và phiên làm việc còn hiệu lực.
2. Trình duyệt cho phép gửi cookie phiên trong ngữ cảnh cross-site (Cookie cấu hình không có thuộc tính `SameSite=Strict`, hoặc cùng domain lab).
3. Yêu cầu POST không có token xác thực.

#### 3. Cách kiểm chứng an toàn trong Lab
- Đăng nhập bằng `user1`.
- Gửi yêu cầu cập nhật địa chỉ mà không kèm `csrf_token`:
- **Kết quả khi có lỗ hổng (Vulnerable):** Địa chỉ được cập nhật ngay lập tức.
- **Kết quả khi đã vá (Fixed):** Server từ chối xử lý và trả về HTTP 403 Forbidden: `Lỗi bảo mật CSRF: Token xác thực không hợp lệ hoặc bị thiếu`.

#### 4. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Sử dụng Anti-CSRF Token ngẫu nhiên cho mỗi phiên làm việc; thiết lập cookie với `SameSite=Lax` hoặc `Strict`.

```python
# [VULNERABLE]
@auth_bp.route('/profile/update-address', methods=['POST'])
@login_required
def update_address():
    new_address = request.form.get('address')
    db.execute("UPDATE users SET address = ? WHERE id = ?", (new_address, session['user_id']))

# [FIXED]
@auth_bp.route('/profile/update-address', methods=['POST'])
@login_required
def update_address():
    if not verify_csrf_token():
        abort(403)
    new_address = request.form.get('address')
    db.execute("UPDATE users SET address = ? WHERE id = ?", (new_address, session['user_id']))
```

---

### LAB 8: BUSINESS LOGIC FLAW
- **Mức độ khó:** Dễ
- **Phân loại:** Business Logic Flaw / Price Tampering
- **Trang & Endpoint:** Đặt hàng & thanh toán (`POST /cart/checkout`)
- **Tập tin liên quan:** `app/routes/cart.py`, `app/templates/cart.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Máy chủ tin tưởng vào giá trị `price` nằm trong payload do trình duyệt gửi lên thay vì tự truy xuất giá từ bảng `products` trong CSDL.
- **Tác động:** Khách hàng có thể can thiệp vào request để mua món hàng trị giá 21.500.000 VND với mức giá chỉ 1.000 VND.

#### 2. Cách kiểm chứng an toàn trong Lab
- Thêm sản phẩm Laptop (21.500.000 đ) vào giỏ hàng.
- Trong trang giỏ hàng, sử dụng khung "Kiểm Thử Thao Túng Giá" hoặc gửi request API với body:
```json
{
  "items": [{"id": 1, "quantity": 1, "price": 1000}],
  "shipping_address": "Hà Nội",
  "payment_method": "COD"
}
```
- **Kết quả khi có lỗ hổng (Vulnerable):** Đơn hàng được tạo thành công với tổng tiền chỉ 1.000 VND.
- **Kết quả khi đã vá (Fixed):** Máy chủ hoàn toàn bỏ qua giá phía client gửi, tự truy vấn CSDL và tạo đơn với giá chuẩn 21.500.000 VND.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Toàn bộ phép tính tài chính phải được thực hiện 100% tại phía máy chủ (Server-side calculation) dựa trên dữ liệu chuẩn trong cơ sở dữ liệu.

```python
# [VULNERABLE]
for item in items:
    price = item['price'] # Nhận giá trực tiếp từ client
    total += price * item['quantity']

# [FIXED]
for item in items:
    row = db.execute("SELECT price FROM products WHERE id = ?", (item['id'],)).fetchone()
    total += row['price'] * item['quantity'] # Luôn lấy giá từ Database
```

---

### LAB 9: SECURITY MISCONFIGURATION
- **Mức độ khó:** Dễ
- **Phân loại:** Server & Framework Configuration
- **Trang & Endpoint:** Kiểm tra trạng thái hệ thống (`GET /api/system/debug-info`) và trang gây lỗi (`GET /debug/trigger-error`)
- **Tập tin liên quan:** `app/routes/debug.py`, `app/templates/errors/500.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Kích hoạt chế độ gỡ lỗi (Debug mode) trên môi trường hoạt động hoặc để lộ các endpoint nội bộ cung cấp thông tin chi tiết về biến môi trường giả lập (mock secrets, token, đường dẫn file).
- **Tác động:** Kẻ tấn công dễ dàng thu thập thông tin trinh sát (Information Disclosure), xác định phiên bản phần mềm để tìm kiếm lỗ hổng đã biết.

#### 2. Cách kiểm chứng an toàn trong Lab
- Truy cập vào: `http://127.0.0.1:5000/api/system/debug-info`
- **Kết quả khi có lỗ hổng (Vulnerable):** JSON trả về chứa `MOCK_PAYMENT_SECRET_KEY`, `internal_paths`, và phiên bản chi tiết.
- **Kết quả khi đã vá (Fixed):** JSON chỉ trả về trạng thái chuẩn an toàn `{"status": "healthy", "service": "VulnShop Public API"}` và ẩn toàn bộ thông số nội bộ.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Tắt chế độ debug trong môi trường triển khai thực tế; xây dựng trang báo lỗi tùy biến (custom error handler 500) và không để lộ endpoint kiểm thử nội bộ.

```python
# [VULNERABLE]
return jsonify({
    'debug_enabled': True,
    'mock_secrets': current_app.config['MOCK_PAYMENT_SECRET_KEY'],
    'internal_paths': ['/app/instance/vulnshop.db']
})

# [FIXED]
return jsonify({
    'status': 'healthy',
    'service': 'VulnShop Public API Gateway',
    'message': 'Hệ thống hoạt động bình thường.'
})
```

---

### LAB 10: OS COMMAND INJECTION
- **Mức độ khó:** Trung bình
- **Phân loại:** Command Injection / Server-side Injection
- **Trang & Endpoint:** Tiện ích kiểm tra mạng (`POST /tools/ping`)
- **Tập tin liên quan:** `app/routes/tools.py`, `app/templates/tools/ping.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Ứng dụng nhận tham số địa chỉ IP hoặc Hostname từ người dùng và nối trực tiếp vào chuỗi lệnh hệ điều hành: `f"ping -c 2 {target}"`, sau đó thực thi qua `subprocess.check_output(..., shell=True)`. Cờ `shell=True` cho phép trình thông dịch shell xử lý các toán tử phân tách lệnh như `;`, `&`, `|`, `&&`.
- **Tác động:** Kẻ tấn công có thể chèn các câu lệnh bổ sung để thực thi tùy ý với quyền hạn của tiến trình web (đọc `/etc/passwd`, cài cắm backdoor, đánh cắp thông tin nhạy cảm).

#### 2. Cách kiểm chứng an toàn trong Lab
- Mở trang `http://127.0.0.1:5000/tools/ping`.
- Nhập payload: `127.0.0.1; whoami` hoặc `127.0.0.1; id`.
- **Kết quả khi có lỗ hổng (Vulnerable):** Bên dưới thông tin phản hồi ping sẽ hiển thị kết quả của lệnh được tiêm (ví dụ: `root` hoặc `uid=0(root) gid=0(root)...`).
- **Kết quả khi đã vá (Fixed):** Hệ thống kiểm tra Regex Whitelist và hiển thị cảnh báo `Phát hiện ký tự không hợp lệ!`, đồng thời chạy lệnh với `shell=False` và danh sách đối số độc lập.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Tuyệt đối không bật `shell=True`; dùng danh sách đối số riêng biệt và kiểm tra định dạng IP/Hostname bằng Regex Whitelist.

```python
# [VULNERABLE]
cmd = f"ping -c 2 {target}"
output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)

# [FIXED]
if not re.match(r'^(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}|(?:\d{1,3}\.){3}\d{1,3}|localhost)$', target):
    return "Phát hiện ký tự không hợp lệ!", 400
output = subprocess.check_output(["ping", "-c", "2", target], shell=False, stderr=subprocess.STDOUT, text=True)
```

---

### LAB 11: INSECURE FILE UPLOAD & WEB SHELL (PHP2SHELL)
- **Mức độ khó:** Khó
- **Phân loại:** Language Core & Arbitrary Code Execution (RCE)
- **Trang & Endpoint:** Tải lên chứng từ (`POST /tools/upload-file`) & Web Shell Console (`GET/POST /tools/webshell/<filename>`)
- **Tập tin liên quan:** `app/routes/tools.py`, `app/templates/tools/file_upload.html`, `app/templates/tools/webshell.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Chức năng tải lên tệp tin không kiểm tra danh sách đuôi mở rộng (Extension Whitelist), không xác thực MIME-type, và lưu nguyên tên tệp mở rộng do người dùng đặt vào thư mục truy cập công khai.
- **Tác động:** Kẻ tấn công tải lên tệp tin kịch bản mã nguồn (.php, .py, .sh), sau đó kích hoạt thực thi để chiếm quyền kiểm soát máy chủ từ xa (Remote Code Execution - RCE).

#### 2. Cách kiểm chứng an toàn trong Lab
- Truy cập `http://127.0.0.1:5000/tools/upload-file`.
- Nhấp nút `📋 Tạo & Chọn file mẫu: lab_shell.py` và nhấn `📤 Tiến Hành Tải Lên Máy Chủ`.
- **Kết quả khi có lỗ hổng (Vulnerable):** Tệp được tải lên thành công kèm nút `🚀 Mở Web Shell Interactive Console`. Người dùng có thể chạy bất kỳ lệnh nào như `whoami`, `id`, `ls -la /app` trực tiếp trên trình duyệt.
- **Kết quả khi đã vá (Fixed):** Hệ thống phát hiện đuôi `.py` không nằm trong Whitelist ảnh (`.png, .jpg, .jpeg, .webp, .pdf`) và từ chối tải lên. Endpoint WebShell trả về mã lỗi 403 Forbidden.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Chỉ cho phép các đuôi tệp an toàn (Whitelist), đổi tên tệp ngẫu nhiên bằng UUID hash để ngăn chặn truy cập trực tiếp bằng tên tệp độc hại.

```python
# [VULNERABLE]
uploaded_file.save(os.path.join(upload_dir, raw_filename))

# [FIXED]
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.pdf'}
ext = os.path.splitext(raw_filename)[1].lower()
if ext not in ALLOWED_EXTENSIONS:
    return "Định dạng tệp không được phép!", 400
safe_name = f"{uuid.uuid4().hex}{ext}"
uploaded_file.save(os.path.join(upload_dir, safe_name))
```

---

### LAB 12: DENIAL OF SERVICE (REDOS)
- **Mức độ khó:** Trung bình
- **Phân loại:** Denial of Service (DoS) / Regular Expression Catastrophic Backtracking
- **Trang & Endpoint:** Xác thực mã giảm giá (`POST /tools/validate-coupon`)
- **Tập tin liên quan:** `app/routes/tools.py`, `app/templates/tools/coupon.html`

#### 1. Nguyên nhân & Tác động
- **Nguyên nhân:** Biểu thức chính quy kiểm tra định dạng chứa các nhóm lặp lồng nhau: `^(([a-zA-Z0-9]+)+)+$`. Khi chuỗi đầu vào dài và có ký tự kết thúc không khớp, thuật toán NFA duyệt qua $2^n$ hoán vị quay lui (Catastrophic Backtracking).
- **Tác động:** Chiếm dụng 100% tài nguyên CPU của một luồng xử lý, làm đóng băng máy chủ và khiến toàn bộ người dùng khác bị ngắt kết nối hoặc timeout (Từ chối dịch vụ - DoS).

#### 2. Cách kiểm chứng an toàn trong Lab
- Mở trang `http://127.0.0.1:5000/tools/validate-coupon`.
- Thử mã hợp lệ: `SUMMER2026` -> Thời gian xử lý: `< 0.1 ms`.
- Thử nút `🔴 ReDoS Test 1: aaaaaaaaaaaaaaaa!` -> Ở chế độ Vulnerable, thời gian phân tích tăng vọt lên `~1.700 ms` (1.7 giây). Với 18 ký tự `a`, thời gian tăng lên `~6.800 ms`.
- Chuyển sang chế độ Fixed và thử lại -> Hệ thống kiểm tra giới hạn độ dài trước và dùng Regex tuyến tính `^[a-zA-Z0-9]{4,16}$`, thời gian phản hồi giảm xuống ngay lập tức `< 0.1 ms`.

#### 3. Biện pháp khắc phục & Mã nguồn so sánh
- **Khắc phục:** Luôn kiểm tra độ dài chuỗi tối đa (`len <= 16`) trước khi phân tích; loại bỏ các nhóm lặp lồng nhau trong Regular Expression.

```python
# [VULNERABLE]
vuln_regex = re.compile(r'^(([a-zA-Z0-9]+)+)+$')
match = vuln_regex.match(coupon_code)

# [FIXED]
if len(coupon_code) > 16:
    return "Mã không được vượt quá 16 ký tự", 400
safe_regex = re.compile(r'^[a-zA-Z0-9]{4,16}$')
match = safe_regex.match(coupon_code)
```

