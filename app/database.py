import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash

def get_db():
    """Lấy kết nối SQLite cho request hiện tại."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Kích hoạt Foreign Keys trong SQLite
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Đóng kết nối SQLite khi kết thúc request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Khởi tạo toàn bộ bảng và nạp dữ liệu mẫu ban đầu."""
    if app:
        with app.app_context():
            _execute_init()
    else:
        _execute_init()

def _execute_init():
    db = get_db()
    
    # 1. Tạo bảng Users
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        failed_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP DEFAULT NULL,
        two_factor_secret TEXT DEFAULT NULL,
        two_factor_enabled INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tạo bảng Products
    db.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price INTEGER NOT NULL,
        original_price INTEGER,
        category TEXT NOT NULL,
        image_url TEXT,
        stock INTEGER DEFAULT 50,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Tạo bảng Comments
    db.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        author_name TEXT NOT NULL,
        content TEXT NOT NULL,
        rating INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 4. Tạo bảng Orders
    db.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Đang xử lý',
        shipping_address TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 5. Tạo bảng Order Items
    db.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        price INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    );
    """)

    # 6. Tạo bảng Cài đặt Lab (Lab Settings)
    db.execute("""
    CREATE TABLE IF NOT EXISTS lab_settings (
        lab_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        is_vulnerable INTEGER NOT NULL DEFAULT 1,
        summary TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        method TEXT NOT NULL
    );
    """)

    # 7. Tạo bảng Cài đặt trang (Site Settings) – lưu banner, logo, v.v.
    db.execute("""
    CREATE TABLE IF NOT EXISTS site_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT NOT NULL
    );
    """)

    # 8. Tạo bảng Nhật ký truy cập (Visit Logs) - Theo dõi ai vào web và thời gian
    db.execute("""
    CREATE TABLE IF NOT EXISTS visit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        role TEXT DEFAULT 'guest',
        ip_address TEXT,
        path TEXT NOT NULL,
        method TEXT NOT NULL,
        user_agent TEXT,
        status_code INTEGER DEFAULT 200,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_visit_logs_created_at ON visit_logs(created_at DESC);")

    db.commit()
    seed_data(db)

def seed_data(db):
    """Nạp dữ liệu mẫu sạch cho ứng dụng và các bài lab."""
    # Tắt tạm thời kiểm tra foreign key trong quá trình làm sạch dữ liệu
    db.execute("PRAGMA foreign_keys = OFF;")
    
    # Xóa dữ liệu cũ
    db.execute("DELETE FROM order_items;")
    db.execute("DELETE FROM orders;")
    db.execute("DELETE FROM comments;")
    db.execute("DELETE FROM products;")
    db.execute("DELETE FROM users;")
    db.execute("DELETE FROM lab_settings;")
    db.execute("DELETE FROM site_settings;")
    db.execute("DELETE FROM visit_logs;")
    
    # Reset sequence của auto-increment nếu có
    try:
        db.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'products', 'comments', 'orders', 'order_items', 'visit_logs');")
    except Exception:
        pass

    db.execute("PRAGMA foreign_keys = ON;")

    # 1. Seed Users (Chỉ định rõ ID để liên kết dữ liệu ổn định tuyệt đối)
    # 1. Seed Users (Chỉ định rõ ID để liên kết dữ liệu ổn định tuyệt đối)
    # Tài khoản:
    # - id 1: hoangnhatdan123 / 12345678 (Tài khoản Admin quản trị viên theo yêu cầu)
    # - id 2: user1 / User@123 (Khách hàng mẫu 1)
    # - id 3: user2 / User@123 (Khách hàng mẫu 2)
    # - id 4: admin / Admin@123 (Quản trị viên hệ thống tương thích ngược)
    users_data = [
        (1, 'hoangnhatdan123', generate_password_hash('12345678'), 'Hoàng Nhật Đan (Admin)', 'hoangnhatdan@laptopaz.vn', 'Số 18, ngõ 121, Thái Hà, Đống Đa, Hà Nội', 'admin'),
        (2, 'user1', generate_password_hash('User@123'), 'Nguyễn Văn An', 'an.nguyen@example.com', '123 Đường Cầu Giấy, Q. Cầu Giấy, Hà Nội', 'user'),
        (3, 'user2', generate_password_hash('User@123'), 'Trần Thị Bình', 'binh.tran@example.com', '456 Đường Lê Lợi, Q. 1, TP. Hồ Chí Minh', 'user'),
        (4, 'admin', generate_password_hash('Admin@123'), 'Quản Trị Viên Hệ Thống', 'admin@vulnshop.lab', '01 Đường Độc Lập, Q. Hoàn Kiếm, Hà Nội', 'admin')
    ]
    db.executemany("""
        INSERT INTO users (id, username, password_hash, full_name, email, address, role)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, users_data)

    # 2. Seed Products (Laptop Gaming chính hãng chuẩn giao diện LaptopAZ.vn)
    products_data = [
        (1, '[Like New] Lecoo Fighter 7000P 2026 Nitro Edition | Core 7 245HX, 16GB, 512GB, RTX 5060 8GB, 16inch WQXGA 180Hz', 'Laptop Gaming Lecoo Fighter 7000P hiệu năng cực đỉnh, vi xử lý Intel Core 7 245HX thế hệ mới nhất, card đồ họa RTX 5060 8GB GDDR6, màn hình chuẩn màu 16 inch WQXGA 180Hz siêu nét.', 38990000, 45300000, 'Laptop Lenovo', '/static/images/laptop_lecoo_fighter.svg', 25),
        (2, 'Laptop Lenovo Lecoo GT16 N176DG | Core i5 205H, 16GB, 512GB, RTX 3050 4GB, 16inch WUXGA 165Hz', 'Thiết kế hiện đại, tản nhiệt buồng hơi công nghệ kép, CPU Core i5 205H đa nhiệm xuất sắc, màn hình tần số quét 165Hz cho trải nghiệm gaming mượt mà, viền mỏng ấn tượng.', 25890000, 28140000, 'Laptop Lenovo', '/static/images/laptop_lenovo_gt16.svg', 30),
        (3, '[Review] Laptop Acer Gaming Nitro ProPanel ANV15-52-50VA NH.QUBSV.002 | Core 5 210H, 16GB, RTX 4050', 'Acer Nitro ProPanel phiên bản nâng cấp màn hình siêu sáng, tản nhiệt cánh quạt thép kép, card đồ họa rời RTX 4050 chiến mượt mọi tựa game AAA và ứng dụng đồ họa.', 26990000, 29990000, 'Laptop Acer', '/static/images/laptop_nitro_pro.svg', 18),
        (4, 'Laptop ASUS TUF Gaming A15 FA506NCG-HN396W | AMD Ryzen 7 155, 8GB, 512GB, RTX 3050 4GB', 'Dòng laptop chuẩn độ bền quân đội Mỹ MIL-STD-810H, vi xử lý AMD Ryzen 7 tiết kiệm pin, phím số full-size có đèn nền RGB rực rỡ và loa vòm Dolby Atmos sống động.', 25590000, 26100000, 'Laptop Asus', '/static/images/laptop_asus_tuf.svg', 40),
        (5, 'Laptop Acer Nitro V 15 ANV15-51-57B2 | Core i5-13420H, RTX 4050 6GB, 16GB DDR5, 512GB SSD, 15.6" 144Hz', 'Laptop quốc dân Nitro V 15 siêu hot, tản nhiệt 2 quạt 4 hốc thoát gió, màn hình 144Hz chống chói IPS, thiết kế logo Nitro phát quang tương lai và bàn phím chuyên dụng game thủ.', 21500000, 23900000, 'Laptop Acer', '/static/images/nitro_v15_real.jpg', 35),
        (6, 'Laptop Dell Gaming G15 5530 | Core i7-13650HX, RTX 4060 8GB, 16GB RAM, 512GB SSD, 15.6" FHD 165Hz', 'Thiết kế đậm chất Alienware hầm hố, khung máy chắc chắn, trang bị phím G-key tăng tốc tản nhiệt tức thì chỉ với một chạm, bàn phím led cam đặc trưng phong cách Dell Gaming.', 28990000, 31170000, 'Laptop Dell', '/static/images/laptop_dell_g15.svg', 20),
        (7, 'Laptop HP Victus 16-r0129TX | Core i7-13700H, RTX 4060 8GB, 16GB DDR5, 1TB SSD, 16.1" FHD 144Hz', 'Màn hình lớn 16.1 inch tỷ lệ hiển thị rộng, loa B&O Audio cao cấp, cấu hình Core i7 14 nhân 20 luồng siêu mạnh cho đồ họa chuyên nghiệp và chiến game đỉnh cao.', 29490000, 31370000, 'Laptop HP', '/static/images/laptop_hp_victus.svg', 22),
        (8, 'Laptop Gigabyte G5 KF | Intel Core i5-12500H, RTX 4060 8GB, 16GB RAM, 512GB SSD, 15.6" FHD 144Hz', 'Trọng lượng siêu nhẹ chỉ 1.9kg trong phân khúc laptop gaming RTX 4060, kết nối đa cổng Thunderbolt 4 và Wi-Fi 6E siêu tốc, thiết kế tối giản tinh tế.', 22990000, 26120000, 'Laptop Gigabyte', '/static/images/laptop_gigabyte_g5.svg', 28)
    ]
    db.executemany("""
        INSERT INTO products (id, name, description, price, original_price, category, image_url, stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, products_data)

    # 3. Seed Comments
    comments_data = [
        (1, 2, 'Nguyễn Văn An', 'Laptop dùng rất mượt, màn hình 180Hz cực kỳ sắc nét, chơi CS2 và Valorant fps ổn định trên 300.', 5),
        (1, 3, 'Trần Thị Bình', 'Thiết kế đẹp, tản nhiệt mát mẻ khi render video và làm việc nặng nhiều giờ liền.', 5),
        (2, 2, 'Nguyễn Văn An', 'Máy nguyên seal chính hãng, shop hỗ trợ cài win và vệ sinh miễn phí rất nhiệt tình.', 5),
        (3, 3, 'Trần Thị Bình', 'Màn hình Nitro ProPanel màu rất đẹp, bàn phím gõ nảy, đóng gói cẩn thận 5 sao!', 5),
        (4, 2, 'Nguyễn Văn An', 'Dòng TUF này rất bền, build chắc chắn, pin dùng văn phòng được hơn 5 tiếng.', 5)
    ]
    db.executemany("""
        INSERT INTO comments (product_id, user_id, author_name, content, rating)
        VALUES (?, ?, ?, ?, ?);
    """, comments_data)

    # 4. Seed Orders (Đơn hàng của user1 và user2)
    orders_data = [
        (1, 'ORD-2026-001', 2, 38990000, 'Đã hoàn thành', '123 Đường Cầu Giấy, Q. Cầu Giấy, Hà Nội', 'Chuyển khoản giả lập'),
        (2, 'ORD-2026-002', 2, 52880000, 'Đang giao hàng', '123 Đường Cầu Giấy, Q. Cầu Giấy, Hà Nội', 'COD (Thanh toán khi nhận)'),
        (3, 'ORD-2026-003', 3, 25590000, 'Đã hoàn thành', '456 Đường Lê Lợi, Q. 1, TP. Hồ Chí Minh', 'Ví điện tử giả lập')
    ]
    db.executemany("""
        INSERT INTO orders (id, order_code, user_id, total_amount, status, shipping_address, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, orders_data)

    # 5. Seed Order Items
    order_items_data = [
        (1, 1, '[Like New] Lecoo Fighter 7000P 2026 Nitro Edition', 38990000, 1),
        (2, 2, 'Laptop Lenovo Lecoo GT16 N176DG', 25890000, 1),
        (2, 3, '[Review] Laptop Acer Gaming Nitro ProPanel ANV15-52-50VA', 26990000, 1),
        (3, 4, 'Laptop ASUS TUF Gaming A15 FA506NCG-HN396W', 25590000, 1)
    ]
    db.executemany("""
        INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
        VALUES (?, ?, ?, ?, ?);
    """, order_items_data)

    # 6. Seed Lab Settings (9 bài lab với trạng thái mặc định is_vulnerable = 1)
    labs_data = [
        (
            'reflected_xss',
            'Reflected XSS (Cross-Site Scripting phản chiếu)',
            'Web Security',
            'Dễ',
            1,
            'Tham số tìm kiếm trên URL được phản chiếu trực tiếp vào HTML mà không qua mã hóa thực thể HTML.',
            '/search',
            'GET'
        ),
        (
            'stored_xss',
            'Stored XSS (Cross-Site Scripting lưu trữ)',
            'Web Security',
            'Trung bình',
            1,
            'Bình luận sản phẩm được lưu thô vào cơ sở dữ liệu và hiển thị trực tiếp cho mọi người xem với bộ lọc tắt escape.',
            '/products/<id>/comments',
            'POST'
        ),
        (
            'dom_xss',
            'DOM-based XSS (XSS trên DOM phía trình duyệt)',
            'Client Security',
            'Trung bình',
            1,
            'Mã JavaScript client đọc dữ liệu từ URL hash hoặc query string rồi chèn trực tiếp vào innerHTML.',
            '/product/<id>#promo=...',
            'GET'
        ),
        (
            'sqli',
            'SQL Injection (Tiêm mã SQL qua tìm kiếm/lọc)',
            'Database Security',
            'Dễ',
            1,
            'Bộ lọc sản phẩm ghép chuỗi trực tiếp từ tham số người dùng vào câu lệnh SQL thay vì dùng tham số hóa (Parameterized Query).',
            '/products/filter',
            'GET'
        ),
        (
            'idor',
            'Insecure Direct Object References (IDOR)',
            'Access Control',
            'Dễ',
            1,
            'Endpoint xem chi tiết đơn hàng chỉ dựa trên ID truyền vào từ URL/API mà không kiểm tra quyền sở hữu của người dùng hiện tại.',
            '/orders/<id>',
            'GET'
        ),
        (
            'broken_access_control',
            'Broken Access Control (Leo thang đặc quyền API)',
            'Access Control',
            'Trung bình',
            1,
            'API quản trị cho phép thay đổi trạng thái đơn hàng hoặc vai trò người dùng nhưng chỉ kiểm tra đăng nhập mà quên kiểm tra quyền admin.',
            '/api/admin/orders/<id>/status',
            'POST'
        ),
        (
            'csrf',
            'Cross-Site Request Forgery (CSRF)',
            'Session Security',
            'Trung bình',
            1,
            'Chức năng cập nhật địa chỉ giao hàng không có token bảo vệ CSRF, chấp nhận request gửi kèm cookie phiên hợp lệ từ nguồn thứ ba.',
            '/profile/update-address',
            'POST'
        ),
        (
            'business_logic',
            'Business Logic Flaw (Thao túng giá sản phẩm)',
            'Business Logic',
            'Dễ',
            1,
            'Endpoint thanh toán đơn hàng tin tưởng hoàn toàn vào giá sản phẩm do phía client gửi lên thay vì truy xuất giá từ database.',
            '/cart/checkout',
            'POST'
        ),
        (
            'security_misconfig',
            'Security Misconfiguration (Lộ thông tin gỡ lỗi)',
            'Server Security',
            'Dễ',
            1,
            'Endpoint debug để lộ biến môi trường giả lập, thông tin phiên bản nội bộ và thông báo lỗi chi tiết khi gặp sự cố.',
            '/api/system/debug-info',
            'GET'
        ),
        (
            'command_injection',
            'OS Command Injection (Tiêm lệnh hệ điều hành)',
            'Command Injection',
            'Trung bình',
            1,
            'Công cụ kiểm tra mạng nối trực tiếp tham số người dùng vào lệnh shell hệ thống (ping) mà không qua làm sạch hay danh sách đối số an toàn.',
            '/tools/ping',
            'POST'
        ),
        (
            'file_upload_shell',
            'Insecure File Upload & Web Shell (Lỗ hổng ngôn ngữ cốt lõi - PHP2Shell)',
            'Core Language & RCE',
            'Khó',
            1,
            'Cho phép tải lên tệp mã nguồn độc hại (.php, .py, .sh) và thực thi Web Shell trực tiếp trên máy chủ do thiếu cơ chế kiểm tra đuôi mở rộng và phân quyền thư mục.',
            '/tools/upload-file',
            'POST'
        ),
        (
            'dos_redos',
            'Denial of Service (DoS - ReDoS qua biểu thức chính quy)',
            'Denial of Service',
            'Trung bình',
            1,
            'Kiểm tra mã giảm giá sử dụng biểu thức chính quy lồng lặp dễ bị Catastrophic Backtracking, gây treo CPU và từ chối dịch vụ toàn bộ hệ thống.',
            '/tools/validate-coupon',
            'POST'
        )
    ]
    db.executemany("""
        INSERT INTO lab_settings (lab_id, name, category, difficulty, is_vulnerable, summary, endpoint, method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, labs_data)

    # 7. Seed Site Settings (Banner mặc định)
    site_settings_data = [
        ('banner_main', '/static/images/nitro_v15_real.jpg'),
        ('banner_side', '/static/images/banner_delivery.svg'),
    ]
    db.executemany("""
        INSERT INTO site_settings (setting_key, setting_value)
        VALUES (?, ?);
    """, site_settings_data)

    # 8. Seed Visit Logs (Mẫu nhật ký người dùng ghé thăm web ban đầu)
    sample_visit_logs = [
        (1, 1, 'hoangnhatdan123', 'Hoàng Nhật Đan (Admin)', 'admin', '127.0.0.1', '/admin', 'GET', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/133.0.0.0', 200, '2026-11-01 14:15:30'),
        (2, 2, 'user1', 'Nguyễn Văn An', 'user', '118.70.182.45', '/product/1', 'GET', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/132.0.0.0', 200, '2026-11-01 14:28:12'),
        (3, None, 'Khách vãng lai', 'Khách truy cập', 'guest', '42.113.140.22', '/search?q=acer+nitro', 'GET', 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148', 200, '2026-11-01 15:02:44'),
        (4, 3, 'user2', 'Trần Thị Bình', 'user', '171.244.15.89', '/cart', 'GET', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15', 200, '2026-11-01 15:20:10'),
        (5, None, 'Khách vãng lai', 'Khách truy cập', 'guest', '113.161.72.10', '/', 'GET', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/133.0.0.0', 200, '2026-11-01 15:35:05')
    ]
    db.executemany("""
        INSERT INTO visit_logs (id, user_id, username, full_name, role, ip_address, path, method, user_agent, status_code, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_visit_logs)

    db.commit()

def is_lab_vulnerable(lab_id):
    """Kiểm tra xem một bài lab cụ thể đang ở chế độ Vulnerable (1) hay Fixed (0)."""
    try:
        db = get_db()
        row = db.execute("SELECT is_vulnerable FROM lab_settings WHERE lab_id = ?", (lab_id,)).fetchone()
        if row:
            return bool(row['is_vulnerable'])
    except Exception:
        pass
    return True

def set_lab_vulnerable(lab_id, status: bool):
    """Bật/tắt chế độ vulnerable cho một bài lab."""
    db = get_db()
    db.execute("UPDATE lab_settings SET is_vulnerable = ? WHERE lab_id = ?", (1 if status else 0, lab_id))
    db.commit()

def get_all_labs():
    """Lấy danh sách tất cả các bài lab cùng trạng thái hiện tại."""
    db = get_db()
    return db.execute("SELECT * FROM lab_settings ORDER BY rowid ASC").fetchall()

def ensure_visit_logs_table(db=None):
    """Đảm bảo bảng visit_logs luôn tồn tại kể cả với cơ sở dữ liệu cũ."""
    if db is None:
        db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS visit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        role TEXT DEFAULT 'guest',
        ip_address TEXT,
        path TEXT NOT NULL,
        method TEXT NOT NULL,
        user_agent TEXT,
        status_code INTEGER DEFAULT 200,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_visit_logs_created_at ON visit_logs(created_at DESC);")
    db.commit()

def ensure_user_security_columns(db=None):
    """Đảm bảo bảng users có các cột failed_attempts, locked_until, two_factor_secret, two_factor_enabled."""
    if db is None:
        db = get_db()
    try:
        columns = [row['name'] for row in db.execute("PRAGMA table_info(users);").fetchall()]
        if 'failed_attempts' not in columns:
            db.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0;")
        if 'locked_until' not in columns:
            db.execute("ALTER TABLE users ADD COLUMN locked_until TIMESTAMP DEFAULT NULL;")
        if 'two_factor_secret' not in columns:
            db.execute("ALTER TABLE users ADD COLUMN two_factor_secret TEXT DEFAULT NULL;")
        if 'two_factor_enabled' not in columns:
            db.execute("ALTER TABLE users ADD COLUMN two_factor_enabled INTEGER DEFAULT 0;")
        db.commit()
    except Exception:
        pass
