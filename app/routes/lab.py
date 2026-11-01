from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from app.database import get_db, is_lab_vulnerable, set_lab_vulnerable, get_all_labs, seed_data
from app.lab_data import LAB_DETAILS

lab_bp = Blueprint('lab', __name__)

@lab_bp.route('/labs')
def index():
    """
    Trang trung tâm điều khiển và hướng dẫn 9 bài Lab Bảo Mật.
    Hiển thị danh sách, độ khó, trạng thái kích hoạt (Vulnerable vs Fixed),
    và cho phép chuyển đổi trạng thái tức thì.
    """
    db_labs = get_all_labs()
    labs_combined = []
    
    # Kết hợp trạng thái từ DB với siêu dữ liệu chi tiết
    for db_lab in db_labs:
        lab_id = db_lab['lab_id']
        detail = LAB_DETAILS.get(lab_id, {})
        labs_combined.append({
            'id': lab_id,
            'name': db_lab['name'],
            'category': db_lab['category'],
            'difficulty': db_lab['difficulty'],
            'is_vulnerable': bool(db_lab['is_vulnerable']),
            'summary': db_lab['summary'],
            'endpoint': db_lab['endpoint'],
            'method': db_lab['method'],
            'objective': detail.get('objective', ''),
            'hints': detail.get('hints', []),
            'solution_overview': detail.get('solution_overview', ''),
            'vulnerable_code': detail.get('vulnerable_code', ''),
            'fixed_code': detail.get('fixed_code', '')
        })

    return render_template('lab/index.html', labs=labs_combined)

@lab_bp.route('/labs/<lab_id>')
def detail(lab_id):
    """Trang xem chi tiết một bài lab cụ thể với toàn bộ tài liệu và code so sánh."""
    if lab_id not in LAB_DETAILS:
        flash('Bài lab không tồn tại.', 'warning')
        return redirect(url_for('lab.index'))
        
    db = get_db()
    db_lab = db.execute("SELECT * FROM lab_settings WHERE lab_id = ?", (lab_id,)).fetchone()
    lab_info = LAB_DETAILS[lab_id].copy()
    lab_info['is_vulnerable'] = bool(db_lab['is_vulnerable']) if db_lab else True

    return render_template('lab/detail.html', lab=lab_info)

@lab_bp.route('/api/labs/toggle', methods=['POST'])
def toggle_lab():
    """
    API Bật/Tắt chế độ Vulnerable cho một bài lab cụ thể.
    Nhận JSON: {"lab_id": "reflected_xss", "status": true/false}
    """
    data = request.get_json(silent=True) or request.form
    lab_id = data.get('lab_id')
    status = data.get('status')
    
    if not lab_id or status is None:
        return jsonify({'success': False, 'message': 'Thiếu tham số lab_id hoặc status.'}), 400
        
    # Chuyển đổi status sang boolean
    if isinstance(status, str):
        status = status.lower() in ['true', '1', 'yes']
    else:
        status = bool(status)

    set_lab_vulnerable(lab_id, status)
    
    return jsonify({
        'success': True,
        'lab_id': lab_id,
        'is_vulnerable': status,
        'message': f'Đã chuyển bài lab [{lab_id}] sang chế độ: {"CÓ LỖ HỔNG (Vulnerable)" if status else "ĐÃ VÁ LỖI (Fixed)"}'
    })

@lab_bp.route('/api/labs/toggle-all', methods=['POST'])
def toggle_all_labs():
    """Bật hoặc tắt toàn bộ 9 bài lab cùng lúc."""
    data = request.get_json(silent=True) or request.form
    status = data.get('status', True)
    
    if isinstance(status, str):
        status = status.lower() in ['true', '1', 'yes']
    else:
        status = bool(status)

    db = get_db()
    db.execute("UPDATE lab_settings SET is_vulnerable = ?", (1 if status else 0,))
    db.commit()

    return jsonify({
        'success': True,
        'is_vulnerable_all': status,
        'message': f'Đã chuyển toàn bộ 9 bài lab sang chế độ: {"CÓ LỖ HỔNG" if status else "ĐÃ VÁ LỖI"}'
    })

@lab_bp.route('/api/labs/reset-db', methods=['POST'])
def reset_database():
    """
    Khôi phục cơ sở dữ liệu mẫu về trạng thái tinh khôi ban đầu.
    Xóa sạch mọi đơn hàng, bình luận hoặc thay đổi do người dùng thực hiện trong quá trình test.
    """
    try:
        db = get_db()
        seed_data(db)
        return jsonify({
            'success': True,
            'message': 'Đã khôi phục thành công toàn bộ cơ sở dữ liệu mẫu về trạng thái gốc!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi khi khôi phục cơ sở dữ liệu: {str(e)}'
        }), 500

@lab_bp.route('/api/labs/status')
def get_labs_status():
    """Lấy danh sách trạng thái hiện tại của tất cả các bài lab."""
    db_labs = get_all_labs()
    status_list = [
        {
            'lab_id': row['lab_id'],
            'name': row['name'],
            'is_vulnerable': bool(row['is_vulnerable']),
            'difficulty': row['difficulty']
        }
        for row in db_labs
    ]
    return jsonify({'success': True, 'labs': status_list})
