import os
from flask import Flask, render_template, session, g, request
from app.config import Config
from app.database import close_db, init_db, get_db
from app.decorators import get_or_create_csrf_token

def parse_device_info(ua_string):
    """Phân tích chuỗi User-Agent thành icon, trình duyệt và hệ điều hành trực quan."""
    if not ua_string:
        return {'display': '🌐 Khách Web', 'browser': 'Trình duyệt', 'os': 'Khác', 'icon': '🌐'}
    ua = ua_string.lower()
    
    # Thiết bị & Hệ điều hành
    if 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
        icon = '📱'
    elif 'android' in ua:
        os_name = 'Android'
        icon = '📱'
    elif 'windows' in ua:
        os_name = 'Windows'
        icon = '💻'
    elif 'macintosh' in ua or 'mac os' in ua:
        os_name = 'macOS'
        icon = '💻'
    elif 'linux' in ua:
        os_name = 'Linux'
        icon = '🐧'
    else:
        os_name = 'Khác'
        icon = '🌐'

    # Trình duyệt
    if 'edg' in ua:
        browser = 'Edge'
    elif 'coccoc' in ua:
        browser = 'Cốc Cốc'
    elif 'chrome' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua:
        browser = 'Safari'
    elif 'opera' in ua or 'opr' in ua:
        browser = 'Opera'
    elif 'curl' in ua or 'python' in ua or 'postman' in ua:
        browser = 'API/Bot'
        icon = '🤖'
    else:
        browser = 'Trình duyệt'

    return {
        'display': f"{icon} {browser} ({os_name})",
        'browser': browser,
        'os': os_name,
        'icon': icon
    }

def create_app(test_config=None):
    """Application factory cho ứng dụng VulnShop."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Nạp cấu hình mặc định
    app.config.from_object(Config)
    
    if test_config:
        app.config.update(test_config)

    # Đảm bảo thư mục instance tồn tại
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Đăng ký đóng kết nối database khi request kết thúc
    app.teardown_appcontext(close_db)

    # Đăng ký bộ lọc Jinja
    app.jinja_env.filters['parse_device'] = parse_device_info

    # Đăng ký các context processor để truyền biến toàn cục vào Jinja template
    @app.context_processor
    def inject_global_data():
        cart = session.get('cart', {})
        total_items = sum(cart.values()) if isinstance(cart, dict) else 0
        return {
            'current_user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'role': session.get('role', 'guest')
            },
            'cart_count': total_items,
            'csrf_token': get_or_create_csrf_token()
        }

    # Đăng ký Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.product import product_bp
    from app.routes.cart import cart_bp
    from app.routes.admin import admin_bp
    from app.routes.lab import lab_bp
    from app.routes.debug import debug_bp
    from app.routes.tools import tools_bp
    from app.routes.shipping import shipping_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(shipping_bp)

    # Tự động ghi nhận lịch sử truy cập (Ai vào web & thời gian)
    @app.after_request
    def log_visit(response):
        # Bỏ qua tài nguyên tĩnh (css, js, images), icon, và endpoint healthcheck
        path = request.path
        if (
            path.startswith('/static/')
            or path == '/favicon.ico'
            or path.startswith('/api/system/debug-info')
        ):
            return response

        try:
            from datetime import datetime
            user_id = session.get('user_id')
            username = session.get('username')
            full_name = session.get('full_name')
            role = session.get('role', 'guest')

            if not username:
                username = 'Khách vãng lai'
                full_name = 'Khách truy cập'
                role = 'guest'

            ip_address = request.headers.get('X-Forwarded-For')
            if ip_address:
                ip_address = ip_address.split(',')[0].strip()
            else:
                ip_address = request.remote_addr or '127.0.0.1'

            user_agent = request.user_agent.string if request.user_agent else ''
            if len(user_agent) > 300:
                user_agent = user_agent[:300]

            full_path = request.full_path.rstrip('?') if request.query_string else request.path
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            db = get_db()
            db.execute("""
                INSERT INTO visit_logs (user_id, username, full_name, role, ip_address, path, method, user_agent, status_code, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, role, ip_address, full_path, request.method, user_agent, response.status_code, current_time))
            db.commit()
        except Exception:
            pass

        return response

    # Xử lý các trang mã lỗi HTTP
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Tự động khởi tạo database hoặc đảm bảo bảng visit_logs tồn tại
    db_path = app.config['DATABASE']
    with app.app_context():
        if not os.path.exists(db_path):
            init_db()
        else:
            from app.database import ensure_visit_logs_table, ensure_user_security_columns
            ensure_visit_logs_table()
            ensure_user_security_columns()

    return app

