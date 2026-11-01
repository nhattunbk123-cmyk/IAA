from flask import Blueprint, render_template, request, g, jsonify
from markupsafe import Markup, escape
from app.database import get_db, is_lab_vulnerable

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Trang chủ hiển thị danh sách sản phẩm nổi bật và các danh mục."""
    db = get_db()
    featured_products = db.execute("SELECT * FROM products ORDER BY id ASC LIMIT 8").fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products").fetchall()

    # Lấy banner URLs từ site_settings (cho phép admin thay đổi)
    banner_main_row = db.execute("SELECT setting_value FROM site_settings WHERE setting_key = 'banner_main'").fetchone()
    banner_side_row = db.execute("SELECT setting_value FROM site_settings WHERE setting_key = 'banner_side'").fetchone()
    banner_main = banner_main_row['setting_value'] if banner_main_row else '/static/images/nitro_v15_real.jpg'
    banner_side = banner_side_row['setting_value'] if banner_side_row else '/static/images/banner_delivery.svg'

    return render_template('index.html',
        products=featured_products,
        categories=[c['category'] for c in categories],
        banner_main=banner_main,
        banner_side=banner_side
    )

@main_bp.route('/search')
def search():
    """
    Chức năng tìm kiếm sản phẩm.
    Phục vụ bài Lab: Reflected XSS.
    - Khi Vulnerable: Chuỗi tìm kiếm người dùng nhập vào được phản chiếu trực tiếp vào HTML mà không qua escape.
    - Khi Fixed: Chuỗi tìm kiếm được escape thành các thực thể HTML an toàn.
    """
    query = request.args.get('q', '').strip()
    db = get_db()
    
    # Tìm kiếm sản phẩm an toàn bằng câu lệnh tham số hóa
    products = []
    if query:
        products = db.execute(
            "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?",
            (f"%{query}%", f"%{query}%")
        ).fetchall()
        
    is_vuln = is_lab_vulnerable('xss')
    
    # Xử lý phản chiếu XSS theo trạng thái lab
    if is_vuln:
        # Ở chế độ lỗ hổng: Sử dụng Markup() để vô hiệu hóa auto-escape của Jinja2
        rendered_query = Markup(query)
    else:
        # Ở chế độ an toàn: Ép kiểu chuỗi chuẩn và qua bộ lọc escape
        rendered_query = str(escape(query))

    return render_template(
        'search.html',
        query=query,
        rendered_query=rendered_query,
        products=products,
        is_vuln=is_vuln
    )

@main_bp.route('/products')
def product_list():
    """Trang danh mục toàn bộ sản phẩm."""
    db = get_db()
    category = request.args.get('category', '')
    categories = db.execute("SELECT DISTINCT category FROM products").fetchall()
    
    if category:
        products = db.execute("SELECT * FROM products WHERE category = ?", (category,)).fetchall()
    else:
        products = db.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
        
    return render_template('products.html', products=products, categories=[c['category'] for c in categories], current_category=category)

@main_bp.route('/products/filter')
def filter_products():
    """
    Endpoint lọc sản phẩm nâng cao theo danh mục và từ khóa.
    Phục vụ bài Lab: SQL Injection.
    - Khi Vulnerable: Nối chuỗi trực tiếp tham số đầu vào vào truy vấn SQLite.
    - Khi Fixed: Sử dụng truy vấn tham số hóa (Parameterized Query với dấu ?).
    """
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()
    db = get_db()
    
    is_vuln = is_lab_vulnerable('sqli')
    executed_sql = ""
    error_msg = None
    products = []

    try:
        if is_vuln:
            # CHẾ ĐỘ CÓ LỖ HỔNG (Vulnerable Mode): Nối chuỗi trực tiếp
            # Cho phép kiểm thử SQL Injection như: ' OR 1=1 --
            conditions = []
            if keyword:
                conditions.append(f"(name LIKE '%{keyword}%' OR description LIKE '%{keyword}%')")
            if category:
                conditions.append(f"category = '{category}'")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            executed_sql = f"SELECT * FROM products WHERE {where_clause} ORDER BY id ASC"
            
            # Thực thi câu lệnh nối chuỗi trực tiếp
            cursor = db.cursor()
            products = cursor.execute(executed_sql).fetchall()
        else:
            # CHẾ ĐỘ ĐÃ SỬA (Fixed Mode): Sử dụng Parameterized Queries an toàn
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            if keyword:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY id ASC"
            executed_sql = f"{query} | Tham số: {params}"
            products = db.execute(query, params).fetchall()

    except Exception as e:
        error_msg = str(e)

    # Nếu gọi qua AJAX hoặc API JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('format') == 'json':
        product_list_data = [
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description'],
                'price': p['price'],
                'category': p['category'],
                'image_url': p['image_url'],
                'stock': p['stock']
            } for p in products
        ]
        return jsonify({
            'success': error_msg is None,
            'products': product_list_data,
            'executed_sql': executed_sql if is_vuln else "[ĐÃ BẢO VỆ BẰNG PARAMETERIZED QUERY]",
            'error': error_msg,
            'is_vuln': is_vuln
        })

    categories = db.execute("SELECT DISTINCT category FROM products").fetchall()
    return render_template(
        'products_filter.html',
        products=products,
        categories=[c['category'] for c in categories],
        keyword=keyword,
        category=category,
        executed_sql=executed_sql,
        error_msg=error_msg,
        is_vuln=is_vuln
    )
