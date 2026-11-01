# Dữ liệu chi tiết về 9 bài Lab An Toàn Thông Tin

LAB_DETAILS = {
    'reflected_xss': {
        'id': 'reflected_xss',
        'name': 'Reflected XSS (Cross-Site Scripting Phản Chiếu)',
        'category': 'Lỗ hổng Ứng dụng Web',
        'difficulty': 'Dễ',
        'endpoint': '/search?q=...',
        'method': 'GET',
        'objective': 'Quan sát cách tham số tìm kiếm từ URL được phản chiếu trực tiếp vào cấu trúc HTML của trang mà không được mã hóa thực thể.',
        'root_cause': 'Ứng dụng lấy dữ liệu từ `request.args.get("q")` và truyền vào template hiển thị. Ở chế độ lỗi, ứng dụng vô hiệu hóa bộ lọc mã hóa (ví dụ sử dụng `Markup()` hoặc `| safe` trong Jinja2), khiến trình duyệt hiểu nhầm chuỗi nhập liệu là các thẻ HTML/JavaScript hợp lệ.',
        'impact': 'Nếu kẻ tấn công lừa nạn nhân truy cập vào một liên kết độc hại, mã script tùy biến có thể được thực thi trong ngữ cảnh phiên làm việc của nạn nhân trên trình duyệt (đọc cookie không có HttpOnly, điều hướng trang, mạo danh thao tác).',
        'hints': [
            'Quan sát tham số "q" trên thanh địa chỉ URL của trang tìm kiếm.',
            'Thử nghiệm nhập các thẻ HTML định dạng cơ bản như <u>, <b>, <i> để kiểm tra xem trình duyệt có render định dạng thay vì hiển thị ký tự thô hay không.',
            'Quan sát mã nguồn HTML (View Source) tại thẻ chứa kết quả thông báo tìm kiếm.'
        ],
        'solution_overview': 'Tại ô tìm kiếm, nhập thử thẻ đánh dấu HTML thông thường (ví dụ: `<u style="color:red">Kiểm_Thử_Lab</u>`). Nếu chế độ Vulnerable đang bật, thẻ sẽ được trình duyệt phân tích cú pháp và hiển thị dòng chữ gạch chân màu đỏ. Khi bật chế độ Fixed, chuỗi được chuyển thành `&lt;u style=...&gt;` và hiển thị dạng văn bản an toàn.',
        'remediation': 'Áp dụng cơ chế Context-aware HTML Entity Encoding. Tận dụng tính năng Auto-escaping mặc định của template engine (như Jinja2) và không bao giờ sử dụng filter `| safe` hoặc `Markup()` đối với bất kỳ dữ liệu nào đến từ người dùng.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
query = request.args.get('q', '')
# Đưa chuỗi vào Markup() làm mất đi cơ chế auto-escape của Jinja2
rendered_query = Markup(query)
return render_template('search.html', rendered_query=rendered_query)

<!-- Trong file template HTML -->
<p>Kết quả tìm kiếm cho: {{ rendered_query }}</p>''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
query = request.args.get('q', '')
# Ép kiểu và mã hóa thực thể HTML an toàn
rendered_query = str(escape(query))
return render_template('search.html', rendered_query=rendered_query)

<!-- Trong file template HTML (Jinja2 tự động escape) -->
<p>Kết quả tìm kiếm cho: {{ query }}</p>'''
    },

    'stored_xss': {
        'id': 'stored_xss',
        'name': 'Stored XSS (Cross-Site Scripting Lưu Trữ)',
        'category': 'Lỗ hổng Ứng dụng Web',
        'difficulty': 'Trung bình',
        'endpoint': '/product/<id>/comment',
        'method': 'POST',
        'objective': 'Phân tích cơ chế dữ liệu đầu vào người dùng được lưu trữ lâu dài trong cơ sở dữ liệu và hiển thị cho mọi người dùng khác mà không qua làm sạch (sanitization).',
        'root_cause': 'Ứng dụng nhận nội dung bình luận từ form POST và lưu nguyên bản vào bảng `comments`. Khi hiển thị danh sách bình luận trên trang chi tiết sản phẩm, template sử dụng cú pháp `{{ comment.content | safe }}`, cho phép trình duyệt diễn giải bất kỳ thẻ HTML nào có trong nội dung.',
        'impact': 'Mọi người dùng truy cập vào trang chi tiết sản phẩm đều sẽ bị thực thi mã trong nội dung bình luận. Tác động lan rộng hơn Reflected XSS vì không cần gửi link riêng lẻ cho từng nạn nhân.',
        'hints': [
            'Tìm đến phần "Bình luận và Đánh giá" ở cuối trang chi tiết sản phẩm bất kỳ.',
            'Thử gửi một bình luận có chứa các thẻ định dạng HTML như <b>Văn bản in đậm</b> hoặc <em>Chữ nghiêng</em>.',
            'Tải lại trang và quan sát xem nội dung bình luận hiển thị ra sao đối với người dùng khác.'
        ],
        'solution_overview': 'Gửi bình luận thử nghiệm với các thẻ HTML hợp lệ vào form đánh giá. Khi lab ở chế độ Vulnerable, nội dung hiển thị sẽ kích hoạt kiểu dáng của thẻ HTML. Sau khi chuyển sang chế độ Fixed, toàn bộ các ký tự đặc biệt như `<`, `>`, `"` đều được escape thành thực thể an toàn.',
        'remediation': '1. Sanitize dữ liệu trước khi lưu trữ hoặc khi hiển thị bằng các thư viện chuẩn (như Bleach trong Python).\\n2. Loại bỏ hoàn toàn bộ lọc `| safe` trong template engine.\\n3. Thiết lập chính sách bảo mật nội dung (Content Security Policy - CSP) để hạn chế thực thi script tùy biến.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
# Lưu trực tiếp nội dung người dùng nhập vào database
db.execute("INSERT INTO comments (content) VALUES (?)", (raw_content,))

<!-- Trong file template product_detail.html -->
{% for comment in comments %}
    <!-- Sử dụng bộ lọc safe vô hiệu hóa cơ chế bảo vệ -->
    <div class="comment-body">{{ comment.content | safe }}</div>
{% endfor %}''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
# Xử lý escape hoặc sanitize trước khi lưu hoặc hiển thị
clean_content = str(escape(raw_content))
db.execute("INSERT INTO comments (content) VALUES (?)", (clean_content,))

<!-- Trong file template product_detail.html -->
{% for comment in comments %}
    <!-- Auto-escape mặc định của Jinja2 bảo vệ ứng dụng -->
    <div class="comment-body">{{ comment.content }}</div>
{% endfor %}'''
    },

    'dom_xss': {
        'id': 'dom_xss',
        'name': 'DOM-based XSS (XSS Dựa Trên Cấu Trúc DOM)',
        'category': 'Bảo mật Phía Trình Duyệt',
        'difficulty': 'Trung bình',
        'endpoint': '/product/<id>#promo=... hoặc ?ref=...',
        'method': 'GET',
        'objective': 'Hiểu rõ lỗ hổng bắt nguồn từ phía client-side JavaScript khi đọc dữ liệu từ một Source (URL hash / location.search) và truyền vào một Sink nguy hiểm (innerHTML) mà không qua kiểm tra.',
        'root_cause': 'Mã JavaScript phía client sử dụng `window.location.hash` hoặc `window.location.search` để lấy mã ưu đãi hiển thị lên banner thông qua thuộc tính `.innerHTML`. Vì mã nguồn xử lý hoàn toàn trên trình duyệt mà không qua máy chủ, các WAF hay bộ lọc phía backend không thể can thiệp.',
        'impact': 'Mã độc được thực thi ngay trong môi trường trình duyệt của người dùng khi họ mở một đường dẫn có đoạn fragment hash hoặc query string độc hại.',
        'hints': [
            'Mở trang chi tiết sản phẩm và quan sát banner "Mã ưu đãi đang áp dụng".',
            'Kiểm tra thanh địa chỉ URL có gắn tham số fragment như `#promo=GIAMGIA10` hoặc `?promo=GIAMGIA10`.',
            'Mở tab Developer Tools (F12) -> Console hoặc Sources để đọc đoạn mã JavaScript xử lý banner.'
        ],
        'solution_overview': 'Trên trình duyệt, sửa URL thành `#promo=<b>GIAMGIA50%</b>`. Ở chế độ Vulnerable, mã JS gán trực tiếp vào `.innerHTML`, khiến chữ hiển thị in đậm. Ở chế độ Fixed, ứng dụng sử dụng `.textContent`, khiến toàn bộ nội dung xuất hiện nguyên bản dạng text an toàn.',
        'remediation': 'Tránh sử dụng các Sink không an toàn như `element.innerHTML`, `document.write()`, `eval()`. Hãy thay thế bằng các phương thức an toàn chỉ xử lý văn bản thuần như `element.textContent`, hoặc sử dụng DOMPurify để làm sạch trước khi chèn vào DOM.',
        'vulnerable_code': '''// [MÃ JAVASCRIPT CÓ LỖ HỔNG PHÍA CLIENT]
const hash = window.location.hash;
if (hash.includes('promo=')) {
    const promoCode = decodeURIComponent(hash.split('promo=')[1]);
    // LỖ HỔNG: Gán trực tiếp vào innerHTML (Sink nguy hiểm)
    document.getElementById('promo-banner').innerHTML = 
        '<span>Mã ưu đãi đang áp dụng: ' + promoCode + '</span>';
}''',
        'fixed_code': '''// [MÃ JAVASCRIPT ĐÃ SỬA CHỮA PHÍA CLIENT]
const hash = window.location.hash;
if (hash.includes('promo=')) {
    const promoCode = decodeURIComponent(hash.split('promo=')[1]);
    // SỬA: Sử dụng textContent để ngăn chặn việc phân tích cú pháp HTML
    const banner = document.getElementById('promo-banner');
    banner.textContent = 'Mã ưu đãi đang áp dụng: ' + promoCode;
}'''
    },

    'sqli': {
        'id': 'sqli',
        'name': 'SQL Injection (Nối Chuỗi Truy Vấn SQL Trực Tiếp)',
        'category': 'Bảo mật Cơ Sở Dữ Liệu',
        'difficulty': 'Dễ',
        'endpoint': '/products/filter?category=...&keyword=...',
        'method': 'GET',
        'objective': 'Quan sát hiện tượng cấu trúc cú pháp của câu lệnh truy vấn SQL bị thay đổi khi dữ liệu đầu vào người dùng được ghép chuỗi trực tiếp thay vì phân tách riêng biệt giữa mã lệnh và dữ liệu.',
        'root_cause': 'Trong hàm `filter_products()`, lập trình viên sử dụng f-string định dạng chuỗi: `f"SELECT * FROM products WHERE (name LIKE \'%{keyword}%\') AND category = \'{category}\'"`. Khi người dùng nhập các ký tự điều khiển cú pháp SQL như dấu nháy đơn (`\') hoặc dấu gạch nối đôi (`--`), cấu trúc logic của truy vấn bị biến đổi.',
        'impact': 'Kẻ tấn công có thể vượt qua bộ lọc logic, truy xuất trái phép dữ liệu ngoài phạm vi cho phép (như thông tin người dùng, mật khẩu), hoặc làm thay đổi logic nghiệp vụ của ứng dụng.',
        'hints': [
            'Truy cập trang Lọc Nâng Cao (/products/filter).',
            'Nhập một dấu nháy đơn (\') vào ô từ khóa hoặc danh mục và bấm Lọc.',
            'Quan sát xem ứng dụng có phát sinh thông báo lỗi cú pháp SQLite (ví dụ: unrecognized token, syntax error) hay không.'
        ],
        'solution_overview': 'Tại ô tìm kiếm nâng cao, khi nhập các ký tự đặc biệt như nháy đơn hoặc toán tử logic, ở chế độ Vulnerable hệ thống sẽ hiển thị câu SQL bị lỗi cú pháp hoặc trả về kết quả vượt ngoài logic ban đầu. Khi chuyển sang Fixed, ứng dụng dùng Parameterized Query và đối xử với mọi ký tự như một chuỗi giá trị thuần túy.',
        'remediation': 'Tuyệt đối không ghép chuỗi để tạo câu truy vấn SQL. Luôn sử dụng Parameterized Queries (Prepared Statements) với ký hiệu `?` trong SQLite hoặc `%s` trong PostgreSQL/MySQL. Parameterized queries phân tách hoàn toàn mã thực thi và dữ liệu đầu vào.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
# Ghép chuỗi trực tiếp từ request vào câu lệnh SQL
keyword = request.args.get('keyword', '')
category = request.args.get('category', '')
sql = f"SELECT * FROM products WHERE name LIKE '%{keyword}%' AND category = '{category}'"
cursor.execute(sql) # Dữ liệu làm thay đổi cú pháp thực thi''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
# Tách biệt hoàn toàn mã SQL và tham số dữ liệu
keyword = request.args.get('keyword', '')
category = request.args.get('category', '')
sql = "SELECT * FROM products WHERE name LIKE ? AND category = ?"
params = (f"%{keyword}%", category)
cursor.execute(sql, params) # SQLite xử lý tham số an toàn 100%'''
    },

    'idor': {
        'id': 'idor',
        'name': 'IDOR (Insecure Direct Object References - Tham Chiếu Đối Tượng Trực Tiếp)',
        'category': 'Kiểm Soát Quyền Truy Cập',
        'difficulty': 'Dễ',
        'endpoint': '/orders/<order_id> hoặc /api/orders/<order_id>',
        'method': 'GET',
        'objective': 'Phát hiện lỗ hổng ủy quyền mức đối tượng (Object-level Authorization) khi ứng dụng sử dụng định danh trực tiếp mà không xác thực mối quan hệ sở hữu giữa đối tượng và người dùng đang đăng nhập.',
        'root_cause': 'Endpoint hiển thị đơn hàng truy vấn dữ liệu theo ID: `SELECT * FROM orders WHERE id = ?`. Máy chủ chỉ kiểm tra xem người dùng đã đăng nhập chưa, nhưng quên không so sánh trường `order.user_id` với `session["user_id"]`.',
        'impact': 'Người dùng thông thường (ví dụ user1) có thể xem toàn bộ chi tiết đơn hàng, địa chỉ nhà riêng, số tiền thanh toán của các khách hàng khác (ví dụ user2) chỉ bằng cách đổi số ID trên thanh địa chỉ URL.',
        'hints': [
            'Đăng nhập bằng tài khoản `user1` (mật khẩu: `User@123`).',
            'Truy cập trang Lịch sử đơn hàng để xem một đơn hàng của chính mình (ví dụ ID là 1 hoặc 2).',
            'Thử thay đổi số ID trên thanh địa chỉ thành 3 (đơn hàng của `user2`).'
        ],
        'solution_overview': 'Khi đăng nhập với `user1`, truy cập đường dẫn `/orders/3`. Ở chế độ Vulnerable, hóa đơn mua hàng của `user2` (Trần Thị Bình) cùng địa chỉ nhà tại TP.HCM sẽ hiển thị đầy đủ. Khi chuyển sang chế độ Fixed, hệ thống sẽ phát hiện sai lệch quyền sở hữu và trả về trang lỗi 403 Forbidden.',
        'remediation': 'Luôn áp dụng nguyên tắc kiểm tra quyền sở hữu tại tầng máy chủ (Server-side Object Authorization Check): Kiểm tra xem đối tượng được yêu cầu có thuộc về người dùng hiện tại hoặc người dùng có vai trò quản trị viên hay không trước khi trả về dữ liệu.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
@login_required
def order_detail(order_id):
    # Chỉ lấy theo ID mà không kiểm tra quyền sở hữu!
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order: abort(404)
    return render_template('order_detail.html', order=order)''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
@login_required
def order_detail(order_id):
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order: abort(404)
    # BẮT BUỘC: Kiểm tra quyền sở hữu đối tượng
    if order['user_id'] != session['user_id'] and session.get('role') != 'admin':
        abort(403) # Chặn truy cập trái phép
    return render_template('order_detail.html', order=order)'''
    },

    'broken_access_control': {
        'id': 'broken_access_control',
        'name': 'Broken Access Control (Thiếu Kiểm Tra Vai Trò Phía Máy Chủ)',
        'category': 'Kiểm Soát Quyền Truy Cập',
        'difficulty': 'Trung bình',
        'endpoint': '/api/admin/orders/<order_id>/status',
        'method': 'POST',
        'objective': 'Minh họa lỗi bảo mật phân quyền theo chức năng (Function-level Access Control) khi API quản trị giả định rằng chỉ admin mới biết URL, nhưng thực tế không kiểm tra vai trò tại máy chủ.',
        'root_cause': 'Endpoint `/api/admin/orders/<order_id>/status` chỉ gắn decorator `@login_required` để kiểm tra phiên đăng nhập của người dùng, nhưng bỏ sót kiểm tra thuộc tính vai trò `session.get("role") == "admin"`.',
        'impact': 'Bất kỳ người dùng có tài khoản hợp lệ (kể cả khách hàng bình thường) đều có thể gửi HTTP POST request đến endpoint này để can thiệp trạng thái đơn hàng (chuyển sang "Đã hoàn thành" hoặc "Đã hủy").',
        'hints': [
            'Mở tab Network trong F12 Developer Tools.',
            'Đăng nhập với tài khoản `user1` (vai trò khách hàng).',
            'Thử gửi request POST đến `/api/admin/orders/1/status` với body JSON `{"status": "Đã hoàn thành"}`.'
        ],
        'solution_overview': 'Gửi request POST tới endpoint API admin bằng phiên của user1. Ở chế độ Vulnerable, trạng thái đơn hàng được cập nhật thành công với mã 200 OK. Khi chuyển sang Fixed, server lập tức từ chối và trả về mã lỗi 403 Forbidden kèm thông báo thiếu quyền Quản trị viên.',
        'remediation': 'Áp dụng cơ chế kiểm soát truy cập dựa trên vai trò (Role-Based Access Control - RBAC) tại mọi endpoint nhạy cảm. Xác thực chặt chẽ quyền hạn từ session hoặc token được ký bí mật từ phía máy chủ.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
@admin_bp.route('/api/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required # Chỉ kiểm tra đã đăng nhập, quên kiểm tra quyền Admin!
def api_update_order_status(order_id):
    new_status = request.json.get('status')
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    return jsonify({'success': True})''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
@admin_bp.route('/api/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def api_update_order_status(order_id):
    # BẮT BUỘC: Kiểm tra vai trò admin từ phía máy chủ
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Yêu cầu quyền Quản trị viên'}), 403
    
    new_status = request.json.get('status')
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    return jsonify({'success': True})'''
    },

    'csrf': {
        'id': 'csrf',
        'name': 'Cross-Site Request Forgery (CSRF - Mạo Danh Yêu Cầu)',
        'category': 'Bảo Mật Phiên Làm Việc',
        'difficulty': 'Trung bình',
        'endpoint': '/profile/update-address',
        'method': 'POST',
        'objective': 'Phân tích cơ chế kẻ tấn công lợi dụng việc trình duyệt tự động gửi kèm cookie phiên của người dùng trong các yêu cầu cross-origin để thực hiện hành động trái phép.',
        'root_cause': 'Endpoint `/profile/update-address` xử lý các yêu cầu thay đổi dữ liệu nhạy cảm nhưng không yêu cầu một mã thông báo bí mật, khó đoán (Anti-CSRF Token). Trình duyệt khi gửi form từ trang web bên ngoài vẫn tự động đính kèm cookie của trang lab nếu chính sách SameSite không được siết chặt.',
        'impact': 'Nếu người dùng đang đăng nhập trên hệ thống và vô tình mở một trang web độc hại do kẻ tấn công điều khiển, trang web đó có thể ngầm gửi một form POST để đổi địa chỉ nhận hàng của nạn nhân sang địa chỉ của kẻ tấn công.',
        'hints': [
            'Xem mã nguồn form đổi địa chỉ trong trang Thông tin cá nhân (/profile).',
            'Kiểm tra xem form có chứa thẻ input ẩn `<input type="hidden" name="csrf_token" ...>` hay không.',
            'Điều kiện để CSRF hoạt động trên trình duyệt: Nạn nhân đã đăng nhập vào lab, cookie được gửi kèm trong cross-site context.'
        ],
        'solution_overview': 'Thực hiện request POST thay đổi địa chỉ mà không kèm theo CSRF token. Ở chế độ Vulnerable, địa chỉ của người dùng bị đổi ngay lập tức. Ở chế độ Fixed, máy chủ kiểm tra `verify_csrf_token()` và từ chối xử lý với mã lỗi 403 Forbidden.',
        'remediation': '1. Triển khai Synchronizer Token Pattern (Anti-CSRF token) cho mọi request có tính chất làm thay đổi trạng thái (POST, PUT, DELETE).\\n2. Thiết lập thuộc tính `SameSite=Strict` hoặc `SameSite=Lax` cho cookie phiên làm việc.\\n3. Xác minh thêm tiêu đề `Origin` và `Referer` của request.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
@auth_bp.route('/profile/update-address', methods=['POST'])
@login_required
def update_address():
    # KHÔNG CÓ BẤT KỲ BỘ KIỂM TRA TOKEN CSRF NÀO!
    new_address = request.form.get('address')
    db.execute("UPDATE users SET address = ? WHERE id = ?", (new_address, session['user_id']))
    return redirect(url_for('auth.profile'))''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
@auth_bp.route('/profile/update-address', methods=['POST'])
@login_required
def update_address():
    # BẮT BUỘC: Kiểm tra tính hợp lệ của CSRF Token
    token = request.form.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        abort(403) # Chặn đứng cuộc tấn công mạo danh CSRF
        
    new_address = request.form.get('address')
    db.execute("UPDATE users SET address = ? WHERE id = ?", (new_address, session['user_id']))
    return redirect(url_for('auth.profile'))'''
    },

    'business_logic': {
        'id': 'business_logic',
        'name': 'Business Logic Flaw (Lỗi Logic Thao Túng Giá Sản Phẩm)',
        'category': 'Logic Nghiệp Vụ',
        'difficulty': 'Dễ',
        'endpoint': '/cart/checkout',
        'method': 'POST',
        'objective': 'Phát hiện sai lầm phổ biến khi nhà phát triển tin tưởng vào tính toàn vẹn của dữ liệu giá tiền do phía client truyền lên thay vì tự kiểm chứng tại máy chủ.',
        'root_cause': 'Chức năng thanh toán nhận payload chứa mảng các sản phẩm và giá: `[{"id": 1, "quantity": 1, "price": 1000}]`. Máy chủ ở chế độ lỗi tính tổng tiền: `total = sum(item["price"] * item["quantity"])` mà không đối chiếu lại giá gốc trong bảng `products`.',
        'impact': 'Người mua hàng có thể mua sản phẩm trị giá hàng chục triệu đồng với giá chỉ 1.000 VND hoặc thậm chí số âm để đảo ngược luồng thanh toán.',
        'hints': [
            'Thêm một sản phẩm có giá trị lớn (ví dụ Laptop 21.500.000 VND) vào giỏ hàng.',
            'Quan sát payload gửi lên trong request thanh toán.',
            'Thử nghiệm sửa đổi giá trị tham số `custom_price` hoặc trường `price` trong JSON payload thanh toán.'
        ],
        'solution_overview': 'Gửi yêu cầu đặt hàng với giá sản phẩm bị sửa thành 1000 VND. Ở chế độ Vulnerable, đơn hàng được tạo thành công với tổng thanh toán chỉ 1000 VND. Khi chuyển sang Fixed, backend tự động tra cứu lại giá từ CSDL (21.500.000 VND) và tính toán chính xác.',
        'remediation': 'Nguyên tắc bất di bất dịch: Tuyệt đối không bao giờ tin tưởng dữ liệu giá hoặc giảm giá do phía client gửi lên. Mọi phép tính toán giá trị tài chính phải được thực hiện hoàn toàn ở phía máy chủ (Server-side Calculation) dựa trên dữ liệu chuẩn trong CSDL.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
# Backend tin tưởng giá tiền do client gửi lên!
items = request.json.get('items')
total_amount = 0
for item in items:
    price = item['price'] # LỖ HỔNG: Lấy trực tiếp từ client
    total_amount += price * item['quantity']
db.execute("INSERT INTO orders (total_amount) VALUES (?)", (total_amount,))''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
# Backend tự tra cứu giá gốc từ cơ sở dữ liệu
items = request.json.get('items')
total_amount = 0
for item in items:
    # Tra cứu giá gốc từ CSDL, bỏ qua mọi dữ liệu giá client gửi
    row = db.execute("SELECT price FROM products WHERE id = ?", (item['id'],)).fetchone()
    total_amount += row['price'] * item['quantity']
db.execute("INSERT INTO orders (total_amount) VALUES (?)", (total_amount,))'''
    },

    'security_misconfig': {
        'id': 'security_misconfig',
        'name': 'Security Misconfiguration (Lộ Thông Tin Cấu Hình & Gỡ Lỗi)',
        'category': 'Cấu Hình Hệ Thống',
        'difficulty': 'Dễ',
        'endpoint': '/api/system/debug-info và /debug/trigger-error',
        'method': 'GET',
        'objective': 'Nhận thức được mức độ nguy hiểm khi để lộ các endpoint nội bộ, chế độ debug, hoặc dấu vết ngăn xếp lỗi (stack trace) trên môi trường ứng dụng.',
        'root_cause': 'Hệ thống kích hoạt chế độ gỡ lỗi (Debug Mode) hoặc duy trì các endpoint phục vụ mục đích kiểm thử nhưng không thu hồi khi triển khai. Khi có ngoại lệ phát sinh, ứng dụng trả về toàn bộ chi tiết mã nguồn và thông tin cấu hình giả lập.',
        'impact': 'Kẻ tấn công thu thập được thông tin tình báo (Fingerprinting) chính xác về phiên bản framework, đường dẫn lưu trữ cơ sở dữ liệu và các thông số kết nối, hỗ trợ tối đa cho các giai đoạn tấn công tiếp theo.',
        'hints': [
            'Truy cập endpoint `/api/system/debug-info` trên trình duyệt.',
            'Quan sát các trường dữ liệu JSON được trả về.',
            'Truy cập endpoint `/debug/trigger-error` để quan sát cách máy chủ xử lý khi gặp ngoại lệ nội bộ.'
        ],
        'solution_overview': 'Truy cập endpoint debug. Ở chế độ Vulnerable, toàn bộ các biến môi trường giả lập (MOCK_PAYMENT_SECRET_KEY, internal paths) sẽ hiện rõ. Ở chế độ Fixed, endpoint trả về phản hồi chung an toàn và ẩn toàn bộ thông số kỹ thuật nội bộ.',
        'remediation': '1. Luôn tắt chế độ Debug (`DEBUG = False`) khi triển khai thực tế.\\n2. Xây dựng trang thông báo lỗi tùy biến (Custom Error Pages) cho mã 404, 500 để không làm lộ stack trace.\\n3. Loại bỏ hoặc bảo vệ nghiêm ngặt các endpoint chuẩn đoán và giám sát nội bộ.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
@debug_bp.route('/api/system/debug-info')
def debug_info():
    # Trả về toàn bộ cấu hình nội bộ và biến môi trường
    return jsonify({
        'debug_mode': True,
        'mock_secret_key': current_app.config['MOCK_PAYMENT_SECRET_KEY'],
        'db_path': current_app.config['DATABASE']
    })''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
@debug_bp.route('/api/system/debug-info')
def debug_info():
    # Chỉ trả về thông tin trạng thái hoạt động tiêu chuẩn
    return jsonify({
        'status': 'healthy',
        'service': 'VulnShop Public API',
        'message': 'Hệ thống hoạt động bình thường.'
    })'''
    },

    'command_injection': {
        'id': 'command_injection',
        'name': 'OS Command Injection (Tiêm Lệnh Hệ Điều Hành)',
        'category': 'Lỗ Hổng Tiêm Lệnh (Injection)',
        'difficulty': 'Trung bình',
        'endpoint': '/tools/ping',
        'method': 'POST',
        'objective': 'Khai thác lỗ hổng tiêm lệnh hệ điều hành khi máy chủ thực thi lệnh shell hệ thống nối trực tiếp chuỗi nhập liệu từ người dùng.',
        'root_cause': 'Endpoint `/tools/ping` nhận tham số địa chỉ mạng (target host) và thực thi lệnh qua `subprocess.check_output(f"ping -c 2 {target}", shell=True)`. Việc bật `shell=True` cho phép trình thông dịch shell (sh/bash/cmd) xử lý các ký tự điều khiển lệnh đặc biệt như `;`, `&`, `|`, `&&`, `$()`.',
        'impact': 'Kẻ tấn công có thể thực thi bất kỳ lệnh hệ điều hành nào với đặc quyền của người dùng chạy ứng dụng (đọc tệp nhạy cảm `/etc/passwd`, cài đặt webshell, mở reverse shell chiếm toàn quyền kiểm soát máy chủ).',
        'hints': [
            'Truy cập trang Công Cụ Kiểm Tra Mạng (/tools/ping).',
            'Nhập một địa chỉ IP hợp lệ như `127.0.0.1` để xem kết quả ping bình thường.',
            'Thử nghiệm nối thêm lệnh khác bằng các ký tự phân tách lệnh: `127.0.0.1; whoami` hoặc `127.0.0.1; id` (hoặc `127.0.0.1 & whoami` trên Windows).'
        ],
        'solution_overview': 'Tại ô nhập địa chỉ, nhập chuỗi `127.0.0.1; whoami`. Ở chế độ Vulnerable, bên dưới kết quả ping sẽ xuất hiện tên người dùng hệ thống (`root` hoặc tài khoản hiện tại). Ở chế độ Fixed, hệ thống kiểm tra regex Whitelist chặn đứng các ký tự phân tách và chỉ chạy lệnh với danh sách đối số an toàn.',
        'remediation': '1. Tránh hoàn toàn việc sử dụng `shell=True` trong các hàm gọi hệ thống của Python.\\n2. Truyền tham số dưới dạng danh sách đối số phân tách: `subprocess.run(["ping", "-c", "2", target], shell=False)`.\\n3. Xác thực đầu vào nghiêm ngặt bằng biểu thức chính quy (Regex Whitelist) chỉ cho phép định dạng IPv4 hoặc Hostname hợp lệ.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
# Ghép chuỗi trực tiếp và sử dụng shell=True
target = request.form.get('target', '')
cmd = f"ping -c 2 {target}"
output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
# Kiểm tra regex whitelist và chạy với shell=False
target = request.form.get('target', '')
if not re.match(r'^(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,6}$|^(?:\\d{1,3}\\.){3}\\d{1,3}$', target):
    return "Địa chỉ IP/Hostname không hợp lệ!", 400

# Truyền mảng đối số độc lập, shell=False ngăn chặn tiêm lệnh 100%
output = subprocess.check_output(["ping", "-c", "2", target], shell=False, stderr=subprocess.STDOUT, text=True)'''
    },

    'file_upload_shell': {
        'id': 'file_upload_shell',
        'name': 'Insecure File Upload & Web Shell (Lỗ Hổng Ngôn Ngữ Cốt Lõi - PHP2Shell)',
        'category': 'Lỗ Hổng Ngôn Ngữ Cốt Lõi (Language Core & RCE)',
        'difficulty': 'Khó',
        'endpoint': '/tools/upload-file và /tools/webshell/<filename>',
        'method': 'POST',
        'objective': 'Mô phỏng chuỗi tấn công kinh điển PHP2Shell / Upload to Web Shell: Tải lên tệp mã nguồn độc hại lên máy chủ và kích hoạt Web Shell tương tác để kiểm soát hệ thống.',
        'root_cause': 'Chức năng tải lên tệp tin không kiểm tra danh sách đuôi mở rộng cho phép (Whitelist), không xác minh MIME type, và lưu tệp nguyên bản vào thư mục công khai có quyền truy cập hoặc thực thi script.',
        'impact': 'Kẻ tấn công tải lên một tệp webshell (.php, .py, .sh), sau đó truy cập hoặc kích hoạt tệp đó để thực thi mã tùy ý từ xa (Remote Code Execution - RCE), trích xuất mã nguồn và toàn bộ cơ sở dữ liệu.',
        'hints': [
            'Truy cập trang Trung Tâm Tải Lên Chứng Từ / Hóa Đơn (/tools/upload-file).',
            'Sử dụng nút bấm tiện ích "📋 Tải Payload WebShell Mẫu" hoặc chuẩn bị một file có đuôi `.py` hoặc `.php`.',
            'Tải tệp lên hệ thống và nhấp vào liên kết Web Shell Console để thực thi lệnh trực tuyến.'
        ],
        'solution_overview': 'Tải lên một tệp mã nguồn độc hại (ví dụ `shell.py` hoặc `cmd.php`). Ở chế độ Vulnerable, tệp được lưu thành công và liên kết kích hoạt Web Shell Console sẽ mở ra, cho phép bạn gõ các lệnh như `id`, `whoami`, `ls -la`. Ở chế độ Fixed, hệ thống kiểm tra Whitelist và từ chối tệp không phải ảnh/tài liệu hợp lệ, đồng thời vô hiệu hóa trình thông dịch shell.',
        'remediation': '1. Áp dụng Whitelist đuôi mở rộng nghiêm ngặt: chỉ cho phép các định dạng an toàn như `.png`, `.jpg`, `.pdf`.\\n2. Đổi tên tệp ngẫu nhiên bằng mã hash ngẫu nhiên (UUID) để ngăn chặn truy cập trực tiếp bằng tên tệp độc hại.\\n3. Lưu trữ tệp tải lên ở thư mục riêng biệt nằm ngoài Document Root và cấu hình máy chủ web vô hiệu hóa hoàn toàn quyền thực thi script trong thư mục upload.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
# Lưu trực tiếp tệp người dùng tải lên mà không kiểm tra định dạng
uploaded_file = request.files.get('file')
filename = secure_filename(uploaded_file.filename)
# Chấp nhận mọi đuôi tệp: .py, .php, .sh
uploaded_file.save(os.path.join(UPLOAD_FOLDER, filename))
# Cho phép kích hoạt và thực thi mã qua Web Shell Console''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
# Whitelist đuôi mở rộng an toàn và sinh tên tệp UUID ngẫu nhiên
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.pdf'}
ext = os.path.splitext(uploaded_file.filename)[1].lower()
if ext not in ALLOWED_EXTENSIONS:
    return "Định dạng tệp không được phép!", 400

# Đổi tên tệp an toàn bằng UUID
safe_name = f"{uuid.uuid4().hex}{ext}"
uploaded_file.save(os.path.join(UPLOAD_FOLDER, safe_name))'''
    },

    'dos_redos': {
        'id': 'dos_redos',
        'name': 'Denial of Service (DoS - ReDoS Phân Tích Cú Pháp Biểu Thức Chính Quy)',
        'category': 'Từ Chối Dịch Vụ (Denial of Service)',
        'difficulty': 'Trung bình',
        'endpoint': '/tools/validate-coupon',
        'method': 'POST',
        'objective': 'Khám phá lỗ hổng ReDoS (Regular Expression Denial of Service) khi máy chủ sử dụng biểu thức chính quy lồng nhau bị lỗi Catastrophic Backtracking làm cạn kiệt CPU của hệ thống.',
        'root_cause': 'Biểu thức kiểm tra định dạng mã giảm giá sử dụng cấu trúc lồng nhóm lặp: `^(([a-zA-Z0-9]+)+)+$`. Khi chuỗi đầu vào chứa nhiều ký tự hợp lệ nhưng kết thúc bằng ký tự không hợp lệ (ví dụ `aaaaaaaaaaaaaaaa!`), thuật toán NFA của Regex phải duyệt qua $2^n$ hoán vị, khiến luồng CPU bị khóa chặt trong nhiều giây.',
        'impact': 'Một hoặc vài yêu cầu kiểm tra mã giảm giá được gửi liên tục có thể chiếm dụng 100% CPU của máy chủ, khiến ứng dụng web bị treo cứng hoàn toàn, không thể phản hồi bất kỳ người dùng nào khác (Từ chối dịch vụ - DoS).',
        'hints': [
            'Mở trang Kiểm Tra Mã Giảm Giá (/tools/validate-coupon).',
            'Thử nhập một mã bình thường như `SUMMER2026` và quan sát thời gian phản hồi (~0.05ms).',
            'Nhấp vào nút "Thử nghiệm ReDoS Payload" với chuỗi `aaaaaaaaaaaaaaaa!` và quan sát CPU cùng thời gian phản hồi tăng vọt lên hàng nghìn mili-giây.'
        ],
        'solution_overview': 'Gửi payload ReDoS `aaaaaaaaaaaaaaaa!` vào form kiểm tra mã giảm giá. Ở chế độ Vulnerable, server mất từ 1.5 đến 15 giây để xử lý một request đơn lẻ. Ở chế độ Fixed, hệ thống sử dụng Regex tuyến tính an toàn `^[a-zA-Z0-9]{4,16}$` và kiểm tra độ dài trước, xử lý xong ngay lập tức trong 0.05ms.',
        'remediation': '1. Tuyệt đối không sử dụng các mẫu Regex có nhóm lặp lồng nhau như `(a+)+`, `([a-zA-Z]+)*` gây ra Catastrophic Backtracking.\\n2. Luôn kiểm tra giới hạn độ dài chuỗi tối đa trước khi đưa vào Regex.\\n3. Sử dụng các Regex Engine có thời gian chạy tuyến tính an toàn hoặc đặt Timeout cho quá trình so khớp chuỗi.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG]
# Regex lồng lặp lỏng lẻo gây Catastrophic Backtracking
VULN_REGEX = re.compile(r'^(([a-zA-Z0-9]+)+)+$')

# Không kiểm tra độ dài, duyệt qua 2^n nhánh quay lui
match = VULN_REGEX.match(coupon_code)''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA]
# Kiểm tra độ dài tối đa trước
if len(coupon_code) > 16:
    return "Mã giảm giá không được vượt quá 16 ký tự", 400

# Regex tuyến tính an toàn O(N), không có lồng lặp
SAFE_REGEX = re.compile(r'^[a-zA-Z0-9]{4,16}$')
match = SAFE_REGEX.match(coupon_code)'''
    }
}
