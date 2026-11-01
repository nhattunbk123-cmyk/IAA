from flask import Blueprint, jsonify, current_app, render_template, request
import traceback
from app.database import is_lab_vulnerable

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/api/system/debug-info')
def debug_info():
    """
    Endpoint cung cấp thông tin kiểm tra trạng thái hệ thống.
    Phục vụ bài Lab: Security Misconfiguration.
    - Khi Vulnerable: Để lộ phiên bản framework, cấu hình giả lập (mock secrets, mock keys),
      và đường dẫn tệp nội bộ hệ thống.
    - Khi Fixed: Chỉ trả về thông tin tối thiểu an toàn, không để lộ bất kỳ chi tiết kiến trúc nào.
    """
    is_vuln = is_lab_vulnerable('security_misconfig')
    
    if is_vuln:
        # CHẾ ĐỘ CÓ LỖ HỔNG: Lộ thông tin cấu hình giả lập (không dùng bí mật thật)
        return jsonify({
            'status': 'DEBUG_MODE_ACTIVE',
            'is_vuln': True,
            'warning': 'CẢNH BÁO BẢO MẬT: Chế độ Debug đang kích hoạt trên môi trường Production!',
            'system_info': {
                'framework': 'Flask 3.1.0 (Python 3.11.9)',
                'environment': 'development',
                'debug_enabled': True,
                'application_version': current_app.config.get('APP_VERSION', '2.4.1-lab-build'),
                'simulated_host': 'kali-lab-instance.local',
                'simulated_internal_ip': '10.0.0.15'
            },
            'mock_configuration_secrets': {
                'MOCK_PAYMENT_GATEWAY_API': current_app.config.get('MOCK_PAYMENT_GATEWAY_API'),
                'MOCK_PAYMENT_SECRET_KEY': current_app.config.get('MOCK_PAYMENT_SECRET_KEY'),
                'MOCK_INTERNAL_AUTH_SERVICE': current_app.config.get('MOCK_INTERNAL_AUTH_SERVICE'),
                'MOCK_DEBUG_FLAG': current_app.config.get('MOCK_INTERNAL_DEBUG_FLAG')
            },
            'internal_paths': [
                '/app/instance/vulnshop.db',
                '/app/config.py',
                '/etc/vulnshop/mock_ssl_cert.crt'
            ]
        })
    else:
        # CHẾ ĐỘ ĐÃ SỬA: Phản hồi tiêu chuẩn an toàn
        return jsonify({
            'status': 'healthy',
            'is_vuln': False,
            'service': 'VulnShop E-Commerce API Gateway',
            'message': 'Hệ thống đang hoạt động bình thường. Mọi thông số gỡ lỗi đã được bảo vệ.'
        })

@debug_bp.route('/debug/trigger-error')
def trigger_error():
    """Endpoint thử nghiệm phản ứng khi gặp lỗi máy chủ nội bộ (500)."""
    is_vuln = is_lab_vulnerable('security_misconfig')
    
    try:
        # Giả lập lỗi chia cho 0 trong logic xử lý
        result = 100 / 0
    except ZeroDivisionError as e:
        if is_vuln:
            # Lộ stack trace chi tiết ra màn hình
            return jsonify({
                'status': 'error',
                'exception_type': type(e).__name__,
                'exception_message': str(e),
                'stack_trace': traceback.format_exc(),
                'is_vuln': True,
                'note': 'Hệ thống đã làm rò rỉ toàn bộ Call Stack và vị trí file mã nguồn.'
            }), 500
        else:
            # Trả về thông báo lỗi chung an toàn
            return render_template('errors/500.html'), 500
