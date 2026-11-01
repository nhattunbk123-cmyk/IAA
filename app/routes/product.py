from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from markupsafe import Markup, escape
from app.database import get_db, is_lab_vulnerable

product_bp = Blueprint('product', __name__)

@product_bp.route('/product/<int:product_id>')
def detail(product_id):
    """
    Chi tiết sản phẩm, hiển thị bình luận và khu vực mã ưu đãi (DOM XSS).
    - Phục vụ Lab: Stored XSS (khu vực hiển thị bình luận).
    - Phục vụ Lab: DOM-based XSS (khu vực xử lý mã giới thiệu từ URL hash/query).
    """
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        abort(404)
        
    comments = db.execute(
        "SELECT * FROM comments WHERE product_id = ? ORDER BY created_at DESC",
        (product_id,)
    ).fetchall()
    
    is_stored_xss_vuln = is_lab_vulnerable('xss')
    is_dom_xss_vuln = is_lab_vulnerable('xss')

    return render_template(
        'product_detail.html',
        product=product,
        comments=comments,
        is_stored_xss_vuln=is_stored_xss_vuln,
        is_dom_xss_vuln=is_dom_xss_vuln
    )

@product_bp.route('/product/<int:product_id>/comment', methods=['POST'])
def add_comment(product_id):
    """
    Thêm bình luận mới cho sản phẩm.
    Phục vụ bài Lab: Stored XSS.
    Lưu nội dung bình luận vào CSDL.
    - Ở chế độ Vulnerable: Template dùng | safe để render HTML thô.
    - Ở chế độ Fixed: Template dùng auto-escape mặc định an toàn của Jinja2.
    """
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        abort(404)

    content = request.form.get('content', '').strip()
    rating = int(request.form.get('rating', 5))
    
    if not content:
        flash('Nội dung bình luận không được để trống.', 'warning')
        return redirect(url_for('product.detail', product_id=product_id))

    user_id = session.get('user_id', 2) # Mặc định là user1 nếu chưa đăng nhập
    author_name = session.get('full_name', 'Khách hàng ẩn danh')

    db.execute("""
        INSERT INTO comments (product_id, user_id, author_name, content, rating)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, user_id, author_name, content, rating))
    db.commit()

    flash('Bình luận của bạn đã được đăng tải thành công!', 'success')
    return redirect(url_for('product.detail', product_id=product_id))
