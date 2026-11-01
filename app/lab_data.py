# Dữ liệu chi tiết về 3 bài Lab An Toàn Thông Tin Cốt Lõi: XSS, SQLi, Command Injection

LAB_DETAILS = {
    'xss': {
        'id': 'xss',
        'name': 'Cross-Site Scripting (XSS - Reflected & Stored)',
        'category': 'Lỗ hổng Ứng dụng Web',
        'difficulty': 'Trung bình',
        'endpoint': '/search?q=... và /product/<id>/comment',
        'method': 'GET / POST',
        'objective': 'Phân tích cơ chế tiêm mã kịch bản độc hại phía máy khách (Client-Side Script Injection) gồm cả Reflected XSS (qua thanh tìm kiếm) và Stored XSS (lưu trữ trong bình luận sản phẩm).',
        'root_cause': 'Ứng dụng nhận dữ liệu từ người dùng (tham số URL "q" hoặc nội dung bình luận "content") và hiển thị trực tiếp lên trình duyệt mà không qua mã hóa thực thể HTML (sử dụng Markup() hoặc bộ lọc | safe của Jinja2). Trình duyệt diễn giải các thẻ HTML/JavaScript nhập vào như mã thực thi hợp lệ.',
        'impact': 'Kẻ tấn công có thể chèn mã JavaScript tùy ý để đánh cắp phiên làm việc (Session Hijacking), đọc dữ liệu nhạy cảm trên trang, chuyển hướng người dùng đến trang độc hại hoặc mạo danh thao tác của người dùng.',
        'hints': [
            'Thử nghiệm Reflected XSS: Trên thanh tìm kiếm (/search), nhập thẻ HTML định dạng: `<u style="color:red">Test_XSS</u>` hoặc `<script>alert("XSS")</script>`.',
            'Thử nghiệm Stored XSS: Mở trang chi tiết bất kỳ sản phẩm laptop nào (/product/1), gửi bình luận chứa: `<b>Bình luận in đậm</b>`.',
            'Bật/tắt công tắc Lab và quan sát sự khác biệt khi thẻ được phân tích cú pháp (Vulnerable) so với khi được escape thành văn bản thô (Fixed).'
        ],
        'solution_overview': 'Ở chế độ Vulnerable, ứng dụng sử dụng Markup() trong tìm kiếm và bộ lọc `| safe` trong hiển thị bình luận, cho phép thẻ HTML kích hoạt trực tiếp. Ở chế độ Fixed, toàn bộ dữ liệu đầu vào đều được mã hóa thực thể HTML an toàn (ví dụ: `<` thành `&lt;`, `>` thành `&gt;`), vô hiệu hóa hoàn toàn mã độc.',
        'remediation': '1. Luôn sử dụng cơ chế Context-aware HTML Entity Encoding.\\n2. Tận dụng tính năng Auto-escaping mặc định của template engine và tuyệt đối không dùng bộ lọc `| safe` hoặc `Markup()` với dữ liệu từ người dùng.\\n3. Thiết lập chính sách bảo mật nội dung (Content Security Policy - CSP) để ngăn chặn thực thi inline script.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG XSS]
# 1. Reflected XSS (routes/main.py)
query = request.args.get('q', '')
rendered_query = Markup(query)  # Vô hiệu hóa auto-escape
return render_template('search.html', rendered_query=rendered_query)

# 2. Stored XSS (templates/product_detail.html)
{% for comment in comments %}
    <div class="comment-body">{{ comment.content | safe }}</div>
{% endfor %}''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA AN TOÀN]
# 1. Reflected XSS (routes/main.py)
query = request.args.get('q', '')
rendered_query = str(escape(query))  # Mã hóa thực thể HTML
return render_template('search.html', rendered_query=rendered_query)

# 2. Stored XSS (templates/product_detail.html)
{% for comment in comments %}
    <!-- Auto-escape mặc định của Jinja2 bảo vệ an toàn -->
    <div class="comment-body">{{ comment.content }}</div>
{% endfor %}'''
    },

    'sqli': {
        'id': 'sqli',
        'name': 'SQL Injection (Tiêm mã truy vấn CSDL)',
        'category': 'An toàn Cơ sở Dữ liệu',
        'difficulty': 'Dễ',
        'endpoint': '/products/filter?keyword=...&category=...&max_price=...',
        'method': 'GET',
        'objective': 'Phân tích cơ chế tấn công SQL Injection khi ứng dụng ghép chuỗi trực tiếp tham số đầu vào vào câu lệnh SQL thay vì dùng Parameterized Query.',
        'root_cause': 'Ứng dụng nối trực tiếp chuỗi từ biến `keyword`, `category` hoặc `sort` vào câu lệnh `SELECT * FROM products WHERE ...`. Kẻ tấn công có thể chèn các ký tự điều khiển cú pháp SQL như dấu nháy đơn (\'), mệnh đề OR, UNION hoặc dấu chấm phẩy (;).',
        'impact': 'Vượt qua logic xác thực, trích xuất toàn bộ dữ liệu nhạy cảm trong CSDL (thông tin người dùng, mật khẩu hash, thông tin giao dịch), hoặc sửa đổi, xóa dữ liệu quan trọng.',
        'hints': [
            'Truy cập trang danh sách sản phẩm và sử dụng bộ lọc tìm kiếm (/products/filter).',
            'Nhập payload SQLi kinh điển: `Acer\' OR \'1\'=\'1` vào ô tìm kiếm.',
            'Quan sát kết quả: Tất cả sản phẩm trong cơ sở dữ liệu sẽ hiển thị ra bất kể điều kiện lọc ban đầu.'
        ],
        'solution_overview': 'Ở chế độ Vulnerable, câu lệnh SQL được ghép chuỗi: `f"SELECT * FROM products WHERE (name LIKE \'%{keyword}%\')"` dẫn đến bị chèn điều kiện OR \'1\'=\'1. Ở chế độ Fixed, ứng dụng sử dụng Prepared Statement với dấu hỏi chấm (`?`) tham số hóa: `db.execute("SELECT * FROM products WHERE name LIKE ?", (\'%\' + keyword + \'%\',))` biến toàn bộ dữ liệu độc hại thành chuỗi tìm kiếm thông thường.',
        'remediation': '1. Bắt buộc sử dụng Tham số hóa Truy vấn (Parameterized Queries / Prepared Statements) cho 100% câu lệnh SQL.\\n2. Sử dụng thư viện ORM uy tín (như SQLAlchemy).\\n3. Áp dụng nguyên tắc đặc quyền tối thiểu (Least Privilege) cho tài khoản kết nối CSDL của ứng dụng.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG SQL INJECTION]
keyword = request.args.get('keyword', '')
# LỖ HỔNG NGUY HIỂM: Nối chuỗi trực tiếp vào câu lệnh SQL
query = f"SELECT * FROM products WHERE (name LIKE '%{keyword}%' OR description LIKE '%{keyword}%')"
cursor = db.execute(query)  # Kẻ tấn công chèn: ' OR '1'='1
products = cursor.fetchall()''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA AN TOÀN]
keyword = request.args.get('keyword', '')
# AN TOÀN TUYỆT ĐỐI: Sử dụng Parameterized Query với tham số (?)
query = "SELECT * FROM products WHERE (name LIKE ? OR description LIKE ?)"
param = f"%{keyword}%"
cursor = db.execute(query, (param, param))  # Database driver tự động escape
products = cursor.fetchall()'''
    },

    'command_injection': {
        'id': 'command_injection',
        'name': 'OS Command Injection (Tiêm lệnh hệ điều hành)',
        'category': 'An toàn Hệ thống & Máy chủ',
        'difficulty': 'Trung bình',
        'endpoint': '/tools/ping',
        'method': 'POST',
        'objective': 'Phân tích cách kẻ tấn công thực thi lệnh hệ điều hành tùy ý thông qua việc nối lệnh độc hại vào tham số ping mạng mà không được kiểm tra an toàn.',
        'root_cause': 'Ứng dụng nhận tham số địa chỉ mạng `target` từ người dùng, ghép vào chuỗi lệnh `ping {target}` và chuyển cho hàm `subprocess.check_output(..., shell=True)`. Trình shell hệ thống diễn giải các ký tự phân tách lệnh (`;`, `&&`, `|`, `&`) và thực thi chuỗi lệnh kèm theo.',
        'impact': 'Thực thi mã từ xa (RCE), cho phép kẻ tấn công kiểm soát toàn bộ máy chủ lưu trữ web, trích xuất tệp nhạy cảm (như /etc/passwd, .env), thiết lập reverse shell hoặc chiếm quyền điều khiển hạ tầng mạng.',
        'hints': [
            'Truy cập công cụ Chẩn đoán mạng tại `/tools/ping`.',
            'Nhập một địa chỉ IP hợp lệ như `127.0.0.1` để xem kết quả ping bình thường.',
            'Thử nghiệm nối thêm lệnh khác bằng các ký tự phân tách lệnh: `127.0.0.1; whoami` hoặc `127.0.0.1 && whoami` (trên Windows có thể dùng `127.0.0.1 & whoami`).'
        ],
        'solution_overview': 'Ở chế độ Vulnerable, khi nhập `127.0.0.1; whoami`, hệ thống sẽ thực hiện lệnh ping rồi lập tức thực thi tiếp lệnh `whoami`, in ra tên người dùng của hệ điều hành. Ở chế độ Fixed, ứng dụng kiểm tra Regex Whitelist chỉ cho phép định dạng IPv4/Hostname hợp lệ và gọi subprocess dưới dạng danh sách đối số độc lập với `shell=False`.',
        'remediation': '1. Tránh hoàn toàn việc sử dụng `shell=True` trong các hàm gọi hệ thống của Python.\\n2. Truyền tham số dưới dạng danh sách đối số phân tách: `subprocess.run(["ping", count_flag, "2", target], shell=False)`.\\n3. Xác thực đầu vào nghiêm ngặt bằng biểu thức chính quy (Regex Whitelist) chỉ cho phép định dạng IPv4 hoặc Hostname hợp lệ.',
        'vulnerable_code': '''# [MÃ CÓ LỖ HỔNG COMMAND INJECTION]
target = request.form.get('target', '')
# LỖ HỔNG: Ghép chuỗi và gọi với shell=True
cmd = f"ping -c 2 {target}"
output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)''',
        'fixed_code': '''# [MÃ ĐÃ SỬA CHỮA AN TOÀN]
target = request.form.get('target', '')
# 1. Kiểm tra regex whitelist (chỉ cho phép IPv4 hoặc hostname hợp lệ)
if not re.match(r'^(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,6}$|^(?:\\d{1,3}\\.){3}\\d{1,3}$', target):
    return "Địa chỉ IP/Hostname không hợp lệ!", 400

# 2. Truyền danh sách đối số độc lập, shell=False ngăn chặn tiêm lệnh 100%
output = subprocess.check_output(["ping", "-c", "2", target], shell=False, stderr=subprocess.STDOUT, text=True)'''
    }
}

# Ánh xạ tương thích ngược cho các route/link cũ
LAB_DETAILS['reflected_xss'] = LAB_DETAILS['xss']
LAB_DETAILS['stored_xss'] = LAB_DETAILS['xss']
LAB_DETAILS['dom_xss'] = LAB_DETAILS['xss']
