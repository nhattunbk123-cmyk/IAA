import os
import re
import platform
import subprocess
from flask import Blueprint, render_template, request, flash, session
from app.database import is_lab_vulnerable

shipping_bp = Blueprint('shipping', __name__, url_prefix='/shipping')

@shipping_bp.route('/tracking', methods=['GET', 'POST'])
def tracking():
    """
    Chức năng Tra cứu hành trình vận chuyển & Kiểm tra kết nối trạm bưu cục.
    Tích hợp tự nhiên lỗ hổng OS Command Injection trong nghiệp vụ giao hàng.
    """
    order_code = request.values.get('order_code', 'VULN-88219').strip()
    partner_gateway = request.values.get('partner_gateway', '127.0.0.1').strip()
    ping_output = None
    error = None
    is_vuln = is_lab_vulnerable('command_injection')

    if request.method == 'POST':
        if not partner_gateway:
            error = "Vui lòng nhập địa chỉ máy chủ bưu cục hoặc đối tác vận chuyển!"
        else:
            is_windows = (platform.system().lower() == 'windows')
            count_flag = '-n' if is_windows else '-c'

            if is_vuln:
                # [LỖ HỔNG COMMAND INJECTION]: Nối trực tiếp tham số vào lệnh shell
                cmd = f"ping {count_flag} 2 {partner_gateway}"
                try:
                    ping_output = subprocess.check_output(
                        cmd,
                        shell=True,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=8
                    )
                except subprocess.CalledProcessError as e:
                    ping_output = e.output if e.output else str(e)
                except subprocess.TimeoutExpired:
                    error = "Kiểm tra kết nối trạm bưu cục quá thời gian (Timeout 8s)."
                except Exception as e:
                    error = f"Lỗi kết nối trạm bưu cục: {str(e)}"
            else:
                # [ĐÃ SỬA]: Kiểm tra Whitelist Regex an toàn & chạy với shell=False
                valid_pattern = r'^(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}|(?:\d{1,3}\.){3}\d{1,3}|localhost)$'
                if not re.match(valid_pattern, partner_gateway):
                    error = "Địa chỉ máy chủ đối tác không hợp lệ! Vui lòng chỉ nhập tên miền hoặc địa chỉ IP."
                else:
                    try:
                        args = ["ping", count_flag, "2", partner_gateway]
                        ping_output = subprocess.check_output(
                            args,
                            shell=False,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8
                        )
                    except subprocess.CalledProcessError as e:
                        ping_output = e.output if e.output else str(e)
                    except subprocess.TimeoutExpired:
                        error = "Kiểm tra kết nối trạm bưu cục quá thời gian (Timeout 8s)."
                    except Exception as e:
                        error = f"Lỗi kết nối trạm bưu cục: {str(e)}"

    return render_template(
        'shipping_track.html',
        order_code=order_code,
        partner_gateway=partner_gateway,
        ping_output=ping_output,
        error=error,
        is_vuln=is_vuln
    )
