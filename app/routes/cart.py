from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort
import random
import string
from app.database import get_db, is_lab_vulnerable
from app.decorators import login_required

cart_bp = Blueprint('cart', __name__)

def generate_order_code():
    """Tạo mã đơn hàng ngẫu nhiên định dạng ORD-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f"ORD-2026-{suffix}"

@cart_bp.route('/cart')
def view_cart():
    """Xem giỏ hàng hiện tại."""
    cart = session.get('cart', {})
    db = get_db()
    
    cart_items = []
    total_amount = 0
    
    for pid_str, quantity in cart.items():
        try:
            pid = int(pid_str)
            product = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
            if product:
                subtotal = product['price'] * quantity
                total_amount += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
        except ValueError:
            continue
            
    is_bl_vuln = is_lab_vulnerable('business_logic')
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount, is_bl_vuln=is_bl_vuln)

@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Thêm sản phẩm vào giỏ hàng session."""
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    if not product_id or quantity <= 0:
        flash('Dữ liệu sản phẩm không hợp lệ.', 'warning')
        return redirect(request.referrer or url_for('main.index'))
        
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    session.modified = True
    
    flash('Đã thêm sản phẩm vào giỏ hàng!', 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/update', methods=['POST'])
def update_cart():
    """Cập nhật số lượng sản phẩm trong giỏ."""
    cart = session.get('cart', {})
    for key in list(cart.keys()):
        field_name = f"quantity_{key}"
        if field_name in request.form:
            try:
                new_qty = int(request.form.get(field_name, 1))
                if new_qty > 0:
                    cart[key] = new_qty
                else:
                    cart.pop(key, None)
            except ValueError:
                pass
    session['cart'] = cart
    session.modified = True
    flash('Giỏ hàng đã được cập nhật.', 'info')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    """
    Áp dụng mã giảm giá / Voucher ưu đãi cho giỏ hàng.
    Tích hợp tự nhiên lỗ hổng Denial of Service (ReDoS - Catastrophic Backtracking).
    """
    import re, time
    coupon_code = request.form.get('coupon_code', '').strip()
    if not coupon_code:
        flash('Vui lòng nhập mã giảm giá.', 'warning')
        return redirect(url_for('cart.view_cart'))

    if len(coupon_code) > 30:
        coupon_code = coupon_code[:30]

    is_vuln = is_lab_vulnerable('dos_redos')
    t_start = time.perf_counter()

    if is_vuln:
        # [LỖ HỔNG REDOS]: Biểu thức chính quy lồng lặp gây Catastrophic Backtracking
        vuln_regex = re.compile(r'^(([a-zA-Z0-9]+)+)+$')
        match = vuln_regex.match(coupon_code)
    else:
        # [ĐÃ SỬA]: Kiểm tra độ dài trước và dùng Regex an toàn O(N)
        if len(coupon_code) > 16:
            match = None
        else:
            safe_regex = re.compile(r'^[a-zA-Z0-9]{4,16}$')
            match = safe_regex.match(coupon_code)

    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

    if match:
        session['discount_rate'] = 0.15
        session['applied_coupon'] = coupon_code
        flash(f'Áp dụng mã giảm giá {coupon_code} thành công! Bạn được giảm 15% (Xử lý trong {elapsed_ms}ms).', 'success')
    else:
        flash(f'Mã giảm giá không hợp lệ hoặc đã hết hạn (Xử lý trong {elapsed_ms}ms).', 'danger')

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Xóa một sản phẩm khỏi giỏ hàng."""
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    session.modified = True
    flash('Đã xóa sản phẩm khỏi giỏ hàng.', 'info')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    """
    Xử lý đặt hàng và thanh toán giả lập.
    Phục vụ bài Lab: Business Logic Flaw (Thao túng giá từ client).
    - Khi Vulnerable: Server đọc trực tiếp giá (price) từ payload gửi lên và tính tổng tiền dựa trên giá này.
    - Khi Fixed: Server hoàn toàn bỏ qua giá phía client, tra cứu giá từ CSDL và tính toán phía backend.
    """
    db = get_db()
    shipping_address = request.form.get('shipping_address') or session.get('address', 'Chưa có địa chỉ')
    payment_method = request.form.get('payment_method', 'COD (Thanh toán khi nhận)')
    
    # Payload kiểm thử thao túng giá (nếu có gửi qua form tùy biến hoặc JSON)
    custom_price = request.form.get('custom_price')
    tampered_product_id = request.form.get('tampered_product_id')
    
    is_vuln = is_lab_vulnerable('business_logic')
    cart = session.get('cart', {})
    
    # Hỗ trợ nhận cả JSON payload trực tiếp cho các kịch bản kiểm thử API
    json_data = request.get_json(silent=True)
    if json_data and 'items' in json_data:
        # Xử lý theo payload JSON
        items_payload = json_data.get('items', [])
        total_amount = 0
        order_items_to_save = []
        
        for item in items_payload:
            pid = int(item.get('id', 0))
            qty = int(item.get('quantity', 1))
            product = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
            if not product:
                continue
                
            if is_vuln:
                # CHẾ ĐỘ CÓ LỖ HỔNG: Lấy giá từ client gửi lên!
                price = int(item.get('price', product['price']))
            else:
                # CHẾ ĐỘ ĐÃ SỬA: Luôn lấy giá từ Database!
                price = product['price']
                
            total_amount += price * qty
            order_items_to_save.append((pid, product['name'], price, qty))
            
        order_code = generate_order_code()
        cur = db.execute("""
            INSERT INTO orders (order_code, user_id, total_amount, status, shipping_address, payment_method)
            VALUES (?, ?, ?, 'Đang xử lý', ?, ?)
        """, (order_code, session['user_id'], total_amount, shipping_address, payment_method))
        order_id = cur.lastrowid
        
        for item in order_items_to_save:
            db.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, item[0], item[1], item[2], item[3]))
        db.commit()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'order_code': order_code,
            'total_amount': total_amount,
            'is_vuln': is_vuln,
            'message': 'Đặt hàng thành công!'
        })

    # Xử lý luồng Web Form thông thường
    if not cart and not tampered_product_id:
        flash('Giỏ hàng của bạn đang trống.', 'warning')
        return redirect(url_for('cart.view_cart'))
        
    total_amount = 0
    order_items_to_save = []
    
    for pid_str, quantity in cart.items():
        pid = int(pid_str)
        product = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if not product:
            continue
            
        if is_vuln and custom_price and str(pid) == str(tampered_product_id):
            # Lỗ hổng: chấp nhận giá do client can thiệp gửi lên
            price = int(custom_price)
        else:
            price = product['price']
            
        total_amount += price * quantity
        order_items_to_save.append((pid, product['name'], price, quantity))
        
    order_code = generate_order_code()
    cur = db.execute("""
        INSERT INTO orders (order_code, user_id, total_amount, status, shipping_address, payment_method)
        VALUES (?, ?, ?, 'Đang xử lý', ?, ?)
    """, (order_code, session['user_id'], total_amount, shipping_address, payment_method))
    order_id = cur.lastrowid
    
    for item in order_items_to_save:
        db.execute("""
            INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, item[0], item[1], item[2], item[3]))
        
    db.commit()
    session['cart'] = {}
    session.modified = True
    
    flash(f'Đặt hàng thành công! Mã đơn: {order_code}', 'success')
    return redirect(url_for('cart.order_detail', order_id=order_id))

@cart_bp.route('/orders')
@login_required
def orders_list():
    """Xem danh sách đơn hàng của người dùng hiện tại."""
    db = get_db()
    orders = db.execute("""
        SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC
    """, (session['user_id'],)).fetchall()
    return render_template('orders.html', orders=orders)

@cart_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """
    Xem chi tiết hóa đơn đơn hàng.
    Phục vụ bài Lab: Insecure Direct Object References (IDOR).
    - Khi Vulnerable: Chỉ truy vấn theo order_id mà không kiểm tra quyền sở hữu user_id.
    - Khi Fixed: Kiểm tra nếu order['user_id'] != session['user_id'] và không phải admin thì trả về 403 Forbidden.
    """
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    
    if not order:
        abort(404)
        
    is_vuln = is_lab_vulnerable('idor')
    
    if not is_vuln:
        # CHẾ ĐỘ ĐÃ SỬA: Kiểm tra quyền sở hữu nghiêm ngặt
        if order['user_id'] != session['user_id'] and session.get('role') != 'admin':
            return render_template('errors/403.html', message="Lỗi phân quyền IDOR: Bạn không có quyền truy cập vào đơn hàng của khách hàng khác!"), 403

    owner = db.execute("SELECT id, username, full_name, email FROM users WHERE id = ?", (order['user_id'],)).fetchone()
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    
    return render_template(
        'order_detail.html',
        order=order,
        owner=owner,
        items=items,
        is_vuln=is_vuln
    )

@cart_bp.route('/api/orders/<int:order_id>')
@login_required
def api_order_detail(order_id):
    """API JSON xem chi tiết đơn hàng (hỗ trợ kiểm thử tự động IDOR)."""
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    
    if not order:
        return jsonify({'success': False, 'message': 'Không tìm thấy đơn hàng'}), 404
        
    is_vuln = is_lab_vulnerable('idor')
    
    if not is_vuln:
        if order['user_id'] != session['user_id'] and session.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Truy cập bị từ chối: Bạn không sở hữu đơn hàng này.',
                'is_vuln': False
            }), 403

    owner = db.execute("SELECT id, username, full_name, email FROM users WHERE id = ?", (order['user_id'],)).fetchone()
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    
    return jsonify({
        'success': True,
        'order': {
            'id': order['id'],
            'order_code': order['order_code'],
            'user_id': order['user_id'],
            'total_amount': order['total_amount'],
            'status': order['status'],
            'shipping_address': order['shipping_address'],
            'payment_method': order['payment_method'],
            'owner_name': owner['full_name'] if owner else 'Unknown',
            'items': [{'name': i['product_name'], 'price': i['price'], 'quantity': i['quantity']} for i in items]
        },
        'is_vuln': is_vuln
    })
