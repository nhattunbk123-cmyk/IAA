from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
from app.database import get_db, is_lab_vulnerable
from app.decorators import login_required, admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_required
def dashboard():
    """Trang chủ quản trị viên hiển thị thống kê tổng quan."""
    db = get_db()
    from datetime import datetime
    total_users = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    total_products = db.execute("SELECT COUNT(*) as count FROM products").fetchone()['count']
    total_orders = db.execute("SELECT COUNT(*) as count FROM orders").fetchone()['count']
    total_revenue = db.execute("SELECT SUM(total_amount) as sum FROM orders WHERE status = 'Đã hoàn thành'").fetchone()['sum'] or 0
    
    # Thống kê lượt truy cập (Ai vào web & thời gian)
    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
        total_visits = db.execute("SELECT COUNT(*) as count FROM visit_logs").fetchone()['count']
        today_visits = db.execute("SELECT COUNT(*) as count FROM visit_logs WHERE created_at LIKE ?", (f"{today_str}%",)).fetchone()['count']
        recent_visits = db.execute("""
            SELECT * FROM visit_logs 
            ORDER BY created_at DESC, id DESC 
            LIMIT 10
        """).fetchall()
    except Exception:
        total_visits = 0
        today_visits = 0
        recent_visits = []

    recent_orders = db.execute("""
        SELECT o.*, u.full_name as customer_name
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 5
    """).fetchall()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_visits=total_visits,
        today_visits=today_visits,
        recent_orders=recent_orders,
        recent_visits=recent_visits
    )

@admin_bp.route('/admin/products')
@admin_required
def products():
    """Quản lý danh sách sản phẩm."""
    db = get_db()
    products_list = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template('admin/products.html', products=products_list)

@admin_bp.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Thêm sản phẩm mới."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = int(request.form.get('price', 0))
        original_price = int(request.form.get('original_price', price))
        category = request.form.get('category', 'Phụ kiện').strip()
        image_url = request.form.get('image_url', '/static/images/placeholder.png').strip()
        stock = int(request.form.get('stock', 50))

        if not name or price <= 0:
            flash('Tên sản phẩm và giá hợp lệ là bắt buộc.', 'danger')
            return render_template('admin/product_form.html', action='add')

        db = get_db()
        db.execute("""
            INSERT INTO products (name, description, price, original_price, category, image_url, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price, original_price, category, image_url, stock))
        db.commit()

        flash('Đã thêm sản phẩm mới thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', action='add', product=None)

@admin_bp.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Chỉnh sửa thông tin sản phẩm."""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = int(request.form.get('price', 0))
        original_price = int(request.form.get('original_price', price))
        category = request.form.get('category', '').strip()
        image_url = request.form.get('image_url', '').strip()
        stock = int(request.form.get('stock', 0))

        db.execute("""
            UPDATE products
            SET name = ?, description = ?, price = ?, original_price = ?, category = ?, image_url = ?, stock = ?
            WHERE id = ?
        """, (name, description, price, original_price, category, image_url, stock, product_id))
        db.commit()

        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', action='edit', product=product)

@admin_bp.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Xóa sản phẩm khỏi hệ thống."""
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': 'Đã xóa sản phẩm thành công.'})
    flash('Đã xóa sản phẩm thành công.', 'info')
    return redirect(request.referrer or url_for('admin.products'))

# ==============================================================================
# CÁC TÍNH NĂNG QUẢN TRỊ TRỰC TIẾP TRÊN GIAO DIỆN CỬA HÀNG (QUICK ACTIONS)
# ==============================================================================

@admin_bp.route('/admin/products/<int:product_id>/quick-price', methods=['POST'])
@admin_required
def quick_edit_price(product_id):
    """Admin sửa giá trực tiếp trên thẻ sản phẩm."""
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm.'}), 404
        flash('Không tìm thấy sản phẩm.', 'danger')
        return redirect(url_for('main.index'))

    data = request.get_json(silent=True) or request.form
    try:
        new_price = int(data.get('price', 0))
        original_price = int(data.get('original_price', product['original_price'] or new_price))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Giá không hợp lệ.'}), 400

    if new_price <= 0:
        return jsonify({'success': False, 'message': 'Giá bán phải lớn hơn 0.'}), 400

    db.execute("""
        UPDATE products
        SET price = ?, original_price = ?
        WHERE id = ?
    """, (new_price, original_price, product_id))
    db.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': 'Đã cập nhật giá bán thành công!',
            'product_id': product_id,
            'price': new_price,
            'original_price': original_price,
            'formatted_price': f"{new_price:,.0f} đ".replace(',', '.')
        })

    flash(f"Đã cập nhật giá cho {product['name']} thành công!", 'success')
    return redirect(request.referrer or url_for('main.index'))

@admin_bp.route('/admin/products/<int:product_id>/quick-image', methods=['POST'])
@admin_required
def quick_edit_image(product_id):
    """Admin đổi ảnh / thêm ảnh sản phẩm trực tiếp từ giao diện."""
    import os, uuid
    from flask import current_app
    from werkzeug.utils import secure_filename

    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        return jsonify({'success': False, 'message': 'Không tìm thấy sản phẩm.'}), 404

    image_url = None

    # Kiểm tra xem có file tải lên hay không
    if 'image_file' in request.files and request.files['image_file'].filename:
        file = request.files['image_file']
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"prod_{product_id}_{uuid.uuid4().hex[:6]}_{secure_filename(file.filename)}"
        file.save(os.path.join(upload_dir, filename))
        image_url = url_for('static', filename=f'uploads/products/{filename}')
    elif request.form.get('image_url'):
        image_url = request.form.get('image_url').strip()

    if not image_url:
        return jsonify({'success': False, 'message': 'Vui lòng chọn file ảnh hoặc nhập đường link ảnh.'}), 400

    db.execute("UPDATE products SET image_url = ? WHERE id = ?", (image_url, product_id))
    db.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': 'Đã cập nhật ảnh sản phẩm thành công!',
            'product_id': product_id,
            'image_url': image_url
        })

    flash(f"Đã cập nhật ảnh cho {product['name']} thành công!", 'success')
    return redirect(request.referrer or url_for('main.index'))

@admin_bp.route('/admin/products/quick-add', methods=['POST'])
@admin_required
def quick_add_product():
    """Admin thêm nhanh Laptop mới ngay trên trang chủ."""
    import os, uuid
    from flask import current_app
    from werkzeug.utils import secure_filename

    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Laptop Gaming').strip()
    description = request.form.get('description', '').strip()
    
    try:
        price = int(request.form.get('price', 0))
        original_price = int(request.form.get('original_price', price))
        stock = int(request.form.get('stock', 20))
    except (ValueError, TypeError):
        flash('Giá hoặc số lượng không hợp lệ.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    if not name or price <= 0:
        flash('Tên laptop và giá bán hợp lệ là bắt buộc.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    image_url = '/static/images/laptop_acer_v15.svg'
    if 'image_file' in request.files and request.files['image_file'].filename:
        file = request.files['image_file']
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"prod_new_{uuid.uuid4().hex[:6]}_{secure_filename(file.filename)}"
        file.save(os.path.join(upload_dir, filename))
        image_url = url_for('static', filename=f'uploads/products/{filename}')
    elif request.form.get('image_url'):
        image_url = request.form.get('image_url').strip()

    db = get_db()
    db.execute("""
        INSERT INTO products (name, description, price, original_price, category, image_url, stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, description, price, original_price, category, image_url, stock))
    db.commit()

    flash(f'Đã thêm thành công sản phẩm mới: {name}!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@admin_bp.route('/admin/banners/<banner_key>/update', methods=['POST'])
@admin_required
def update_banner(banner_key):
    """Admin đổi ảnh banner trực tiếp trên trang chủ (banner_main hoặc banner_side)."""
    import os, uuid
    from flask import current_app
    from werkzeug.utils import secure_filename

    valid_keys = ['banner_main', 'banner_side']
    if banner_key not in valid_keys:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Key banner không hợp lệ.'}), 400
        flash('Key banner không hợp lệ.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    image_url = None

    # Kiểm tra xem có file tải lên hay không
    if 'banner_file' in request.files and request.files['banner_file'].filename:
        file = request.files['banner_file']
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'banners')
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{banner_key}_{uuid.uuid4().hex[:6]}_{secure_filename(file.filename)}"
        file.save(os.path.join(upload_dir, filename))
        image_url = url_for('static', filename=f'uploads/banners/{filename}')
    elif request.form.get('banner_url'):
        image_url = request.form.get('banner_url').strip()

    if not image_url:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'message': 'Vui lòng chọn file ảnh hoặc nhập đường link ảnh.'}), 400
        flash('Vui lòng chọn file ảnh hoặc nhập đường link ảnh.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    db = get_db()
    # Upsert: cập nhật nếu key đã tồn tại, thêm mới nếu chưa
    existing = db.execute("SELECT setting_key FROM site_settings WHERE setting_key = ?", (banner_key,)).fetchone()
    if existing:
        db.execute("UPDATE site_settings SET setting_value = ? WHERE setting_key = ?", (image_url, banner_key))
    else:
        db.execute("INSERT INTO site_settings (setting_key, setting_value) VALUES (?, ?)", (banner_key, image_url))
    db.commit()

    banner_label = 'Banner chính' if banner_key == 'banner_main' else 'Banner phụ'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': f'Đã cập nhật {banner_label} thành công!',
            'banner_key': banner_key,
            'image_url': image_url
        })

    flash(f'Đã cập nhật {banner_label} thành công!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@admin_bp.route('/admin/orders')
@admin_required
def orders():
    """Quản lý danh sách toàn bộ đơn hàng của khách."""
    db = get_db()
    orders_list = db.execute("""
        SELECT o.*, u.full_name, u.username
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """).fetchall()
    return render_template('admin/orders.html', orders=orders_list)

@admin_bp.route('/admin/users')
@admin_required
def users():
    """Quản lý danh sách người dùng và vai trò."""
    db = get_db()
    users_list = db.execute("SELECT id, username, full_name, email, address, role, created_at FROM users ORDER BY id ASC").fetchall()
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/admin/access-logs')
@admin_required
def access_logs():
    """Trang quản trị xem chi tiết ai vào web và thời gian."""
    db = get_db()
    from datetime import datetime
    import math

    role_filter = request.args.get('role', 'all').strip()
    search_q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 25
    if page < 1:
        page = 1

    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
        total_visits = db.execute("SELECT COUNT(*) as count FROM visit_logs").fetchone()['count']
        today_visits = db.execute("SELECT COUNT(*) as count FROM visit_logs WHERE created_at LIKE ?", (f"{today_str}%",)).fetchone()['count']
        user_visits = db.execute("SELECT COUNT(*) as count FROM visit_logs WHERE role IN ('user', 'admin')").fetchone()['count']
        guest_visits = db.execute("SELECT COUNT(*) as count FROM visit_logs WHERE role = 'guest'").fetchone()['count']
    except Exception:
        total_visits = today_visits = user_visits = guest_visits = 0

    where_clauses = []
    params = []

    if role_filter == 'guest':
        where_clauses.append("role = 'guest'")
    elif role_filter == 'user':
        where_clauses.append("role = 'user'")
    elif role_filter == 'admin':
        where_clauses.append("role = 'admin'")
    elif role_filter == 'member':
        where_clauses.append("role IN ('user', 'admin')")

    if search_q:
        where_clauses.append("(username LIKE ? OR full_name LIKE ? OR ip_address LIKE ? OR path LIKE ?)")
        search_pattern = f"%{search_q}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    try:
        count_sql = f"SELECT COUNT(*) as count FROM visit_logs {where_sql}"
        filtered_count = db.execute(count_sql, params).fetchone()['count']
        total_pages = max(1, math.ceil(filtered_count / per_page))
        if page > total_pages:
            page = total_pages

        offset = (page - 1) * per_page
        query_sql = f"""
            SELECT * FROM visit_logs
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
        """
        logs = db.execute(query_sql, params + [per_page, offset]).fetchall()
    except Exception:
        filtered_count = 0
        total_pages = 1
        logs = []

    return render_template(
        'admin/access_logs.html',
        logs=logs,
        total_visits=total_visits,
        today_visits=today_visits,
        user_visits=user_visits,
        guest_visits=guest_visits,
        filtered_count=filtered_count,
        current_page=page,
        total_pages=total_pages,
        role_filter=role_filter,
        search_q=search_q
    )

@admin_bp.route('/admin/access-logs/clear', methods=['POST'])
@admin_required
def clear_access_logs():
    """Xóa nhật ký truy cập theo yêu cầu của admin."""
    action = request.form.get('action', 'all')
    db = get_db()
    if action == 'older_7days':
        db.execute("DELETE FROM visit_logs WHERE created_at < datetime('now', '-7 days')")
        flash('Đã dọn dẹp các bản ghi truy cập cũ hơn 7 ngày.', 'info')
    else:
        db.execute("DELETE FROM visit_logs")
        flash('Đã làm sạch toàn bộ nhật ký truy cập thành công!', 'success')
    db.commit()
    return redirect(url_for('admin.access_logs'))

# ==============================================================================
# ENDPOINT PHỤC VỤ BÀI LAB: BROKEN ACCESS CONTROL (BAC)
# ==============================================================================

@admin_bp.route('/api/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def api_update_order_status(order_id):
    """
    API Quản trị cập nhật trạng thái đơn hàng.
    Phục vụ bài Lab: Broken Access Control.
    - Khi Vulnerable: Endpoint chỉ kiểm tra người dùng đã đăng nhập (@login_required)
      nhưng KHÔNG kiểm tra vai trò người dùng có phải là 'admin' hay không!
      Khách hàng thông thường (user1, user2) vẫn có thể gửi request để đổi trạng thái đơn hàng.
    - Khi Fixed: Kiểm tra nghiêm ngặt vai trò người dùng trong session: session.get('role') == 'admin'.
    """
    is_vuln = is_lab_vulnerable('broken_access_control')
    
    if not is_vuln:
        # CHẾ ĐỘ ĐÃ SỬA: Xác thực bắt buộc quyền Admin từ phía máy chủ
        if session.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Lỗi phân quyền Broken Access Control: Bắt buộc quyền Quản trị viên (Admin) để thao tác API này!',
                'is_vuln': False
            }), 403

    data = request.get_json(silent=True) or request.form
    new_status = data.get('status', '').strip()
    
    valid_statuses = ['Đang xử lý', 'Đang giao hàng', 'Đã hoàn thành', 'Đã hủy']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': f'Trạng thái không hợp lệ. Phải thuộc: {valid_statuses}'}), 400

    db = get_db()
    order = db.execute("SELECT id FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        return jsonify({'success': False, 'message': 'Không tìm thấy đơn hàng.'}), 404

    db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    db.commit()

    return jsonify({
        'success': True,
        'message': f'Đã cập nhật trạng thái đơn hàng #{order_id} thành: {new_status}',
        'order_id': order_id,
        'new_status': new_status,
        'is_vuln': is_vuln,
        'executed_by': session.get('username'),
        'user_role': session.get('role')
    })
