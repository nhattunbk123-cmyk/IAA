import os
import re
import time
import uuid
import platform
import subprocess
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from app.database import is_lab_vulnerable

tools_bp = Blueprint('tools', __name__, url_prefix='/tools')

def get_upload_dir():
    """Lấy hoặc tạo thư mục lưu trữ file upload."""
    upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_path, exist_ok=True)
    return upload_path

# ==============================================================================
# TRANG TỔNG HỢP CÁC CÔNG CỤ LAB
# ==============================================================================
@tools_bp.route('/')
def index():
    """Trang chủ danh sách các công cụ tiện ích mở rộng."""
    return render_template('tools/index.html')

# ==============================================================================
# LAB 10: OS COMMAND INJECTION
# ==============================================================================
@tools_bp.route('/ping', methods=['GET', 'POST'])
def ping():
    """
    Công cụ kiểm tra kết nối mạng máy chủ (Server Diagnostics Ping Tool).
    Phục vụ bài Lab: OS Command Injection.
    """
    is_vuln = is_lab_vulnerable('command_injection')
    output = None
    target = ""
    error = None
    executed_command = None

    if request.method == 'POST':
        target = request.form.get('target', '').strip()
        
        if not target:
            error = "Vui lòng nhập địa chỉ IP hoặc tên miền cần kiểm tra!"
        else:
            is_windows = (platform.system().lower() == 'windows')
            count_flag = '-n' if is_windows else '-c'

            if is_vuln:
                # [CHẾ ĐỘ CÓ LỖ HỔNG]: Nối chuỗi trực tiếp và chạy với shell=True
                executed_command = f"ping {count_flag} 2 {target}"
                try:
                    res = subprocess.check_output(
                        executed_command,
                        shell=True,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=8
                    )
                    output = res
                except subprocess.CalledProcessError as e:
                    output = e.output if e.output else str(e)
                except subprocess.TimeoutExpired:
                    error = "Lệnh đã chạy quá thời gian cho phép (Timeout 8s)."
                except Exception as e:
                    error = f"Lỗi thực thi lệnh: {str(e)}"
            else:
                # [CHẾ ĐỘ ĐÃ SỬA]: Kiểm tra Whitelist Regex nghiêm ngặt & shell=False
                valid_pattern = r'^(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}|(?:\d{1,3}\.){3}\d{1,3}|localhost)$'
                if not re.match(valid_pattern, target):
                    error = "Phát hiện ký tự không hợp lệ! Chế độ an toàn chỉ chấp nhận địa chỉ IP hoặc Hostname thuần túy (không chứa ký tự điều khiển shell: ;, &, |, $, `)."
                else:
                    executed_command = f"ping {count_flag} 2 {target} (Chế độ an toàn: shell=False)"
                    try:
                        args = ["ping", count_flag, "2", target]
                        res = subprocess.check_output(
                            args,
                            shell=False,
                            stderr=subprocess.STDOUT,
                            text=True,
                            timeout=8
                        )
                        output = res
                    except subprocess.CalledProcessError as e:
                        output = e.output if e.output else str(e)
                    except subprocess.TimeoutExpired:
                        error = "Lệnh đã chạy quá thời gian cho phép (Timeout 8s)."
                    except Exception as e:
                        error = f"Lỗi thực thi lệnh: {str(e)}"

    return render_template(
        'tools/ping.html',
        target=target,
        output=output,
        error=error,
        executed_command=executed_command,
        is_vuln=is_vuln
    )

# ==============================================================================
# LAB 11: INSECURE FILE UPLOAD & WEBSHELL (PHP2SHELL / PYTHON SHELL)
# ==============================================================================
@tools_bp.route('/upload-file', methods=['GET', 'POST'])
def upload_file():
    """
    Trung tâm tải lên tệp tin và chứng từ.
    Phục vụ bài Lab: Insecure File Upload to Web Shell (Lỗ hổng ngôn ngữ cốt lõi).
    """
    is_vuln = is_lab_vulnerable('file_upload_shell')
    upload_dir = get_upload_dir()
    file_info = None
    error = None

    if request.method == 'POST':
        if 'file' not in request.files:
            error = "Vui lòng chọn tệp tin cần tải lên!"
        else:
            uploaded_file = request.files['file']
            raw_filename = uploaded_file.filename

            if not raw_filename:
                error = "Tên tệp không hợp lệ!"
            else:
                ext = os.path.splitext(raw_filename)[1].lower()
                
                if is_vuln:
                    # [CHẾ ĐỘ CÓ LỖ HỔNG]: Lưu trực tiếp mọi định dạng (.php, .py, .sh, .html)
                    safe_original_name = secure_filename(raw_filename) or f"upload_{int(time.time())}{ext}"
                    save_path = os.path.join(upload_dir, safe_original_name)
                    uploaded_file.save(save_path)
                    
                    file_info = {
                        'filename': safe_original_name,
                        'size': os.path.getsize(save_path),
                        'url': url_for('static', filename=f'uploads/{safe_original_name}'),
                        'is_script': ext in ['.php', '.py', '.sh', '.bash', '.cgi', '.pl'],
                        'shell_url': url_for('tools.webshell_console', filename=safe_original_name)
                    }
                    flash(f"Tải lên tệp thành công: {safe_original_name}", "success")
                else:
                    # [CHẾ ĐỘ ĐÃ SỬA]: Whitelist định dạng an toàn & đổi tên UUID ngẫu nhiên
                    ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.pdf'}
                    if ext not in ALLOWED_EXTENSIONS:
                        error = f"Lỗi bảo mật: Định dạng tệp '{ext}' bị từ chối! Hệ thống chỉ cho phép tải lên ảnh ({', '.join(ALLOWED_EXTENSIONS)})."
                    else:
                        safe_uuid_name = f"{uuid.uuid4().hex}{ext}"
                        save_path = os.path.join(upload_dir, safe_uuid_name)
                        uploaded_file.save(save_path)
                        
                        file_info = {
                            'filename': safe_uuid_name,
                            'original_name': raw_filename,
                            'size': os.path.getsize(save_path),
                            'url': url_for('static', filename=f'uploads/{safe_uuid_name}'),
                            'is_script': False
                        }
                        flash(f"Tải lên tệp an toàn thành công (Đã mã hóa tên tệp: {safe_uuid_name})", "success")

    # Liệt kê các tệp đã upload sẵn
    existing_files = []
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            fp = os.path.join(upload_dir, f)
            if os.path.isfile(fp):
                ext = os.path.splitext(f)[1].lower()
                existing_files.append({
                    'name': f,
                    'size': os.path.getsize(fp),
                    'url': url_for('static', filename=f'uploads/{f}'),
                    'is_script': ext in ['.php', '.py', '.sh', '.bash']
                })

    return render_template(
        'tools/file_upload.html',
        file_info=file_info,
        error=error,
        existing_files=existing_files,
        is_vuln=is_vuln
    )

@tools_bp.route('/webshell/<filename>', methods=['GET', 'POST'])
def webshell_console(filename):
    """
    Giao diện điều khiển Web Shell tương tác trực tiếp mô phỏng kịch bản PHP2Shell.
    """
    is_vuln = is_lab_vulnerable('file_upload_shell')
    if not is_vuln:
        return render_template('errors/403.html'), 403

    upload_dir = get_upload_dir()
    file_path = os.path.join(upload_dir, secure_filename(filename))
    
    if not os.path.exists(file_path):
        flash("Tệp WebShell không tồn tại trên máy chủ!", "warning")
        return redirect(url_for('tools.upload_file'))

    # Lấy lệnh thực thi từ query parameter hoặc POST form
    cmd = request.values.get('cmd', 'whoami').strip()
    cmd_output = ""
    error = None

    if cmd:
        try:
            cmd_output = subprocess.check_output(
                cmd,
                shell=True,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=5
            )
        except subprocess.CalledProcessError as e:
            cmd_output = e.output if e.output else str(e)
        except subprocess.TimeoutExpired:
            error = "Lệnh thực thi bị Timeout (5s)."
        except Exception as e:
            error = f"Lỗi chạy Web Shell: {str(e)}"

    return render_template(
        'tools/webshell.html',
        filename=filename,
        cmd=cmd,
        cmd_output=cmd_output,
        error=error
    )

# ==============================================================================
# LAB 12: DENIAL OF SERVICE (DoS - ReDoS)
# ==============================================================================
@tools_bp.route('/validate-coupon', methods=['GET', 'POST'])
def validate_coupon():
    """
    Công cụ xác thực mã giảm giá (Coupon Validator).
    Phục vụ bài Lab: Denial of Service (ReDoS - Catastrophic Backtracking).
    """
    is_vuln = is_lab_vulnerable('dos_redos')
    coupon_code = ""
    result = None
    execution_time_ms = 0.0
    error = None

    if request.method == 'POST':
        coupon_code = request.form.get('coupon_code', '')
        
        if not coupon_code:
            error = "Vui lòng nhập mã giảm giá cần kiểm tra!"
        else:
            # Giới hạn an toàn chiều dài tối đa của payload trong bài lab để tránh khóa server vĩnh viễn
            if len(coupon_code) > 30:
                coupon_code = coupon_code[:30]

            t_start = time.perf_counter()

            if is_vuln:
                # [CHẾ ĐỘ CÓ LỖ HỔNG]: Regex lồng lặp lỏng lẻo gây Catastrophic Backtracking
                # Khi chuỗi có dạng 'aaaaaaaaaaaaaaaa!' -> NFA quay lui 2^n nhánh
                vuln_regex = re.compile(r'^(([a-zA-Z0-9]+)+)+$')
                match = vuln_regex.match(coupon_code)
                t_end = time.perf_counter()
                execution_time_ms = round((t_end - t_start) * 1000, 2)

                if match:
                    result = {
                        'valid': True,
                        'discount': '15%',
                        'message': f"Mã hợp lệ! Bạn được giảm giá 15%."
                    }
                else:
                    result = {
                        'valid': False,
                        'message': "Mã không hợp lệ hoặc sai định dạng quy định."
                    }
            else:
                # [CHẾ ĐỘ ĐÃ SỬA]: Kiểm tra độ dài trước & Regex tuyến tính an toàn O(N)
                if len(coupon_code) > 16:
                    t_end = time.perf_counter()
                    execution_time_ms = round((t_end - t_start) * 1000, 2)
                    result = {
                        'valid': False,
                        'message': "Mã không hợp lệ (Độ dài vượt quá giới hạn 16 ký tự)."
                    }
                else:
                    safe_regex = re.compile(r'^[a-zA-Z0-9]{4,16}$')
                    match = safe_regex.match(coupon_code)
                    t_end = time.perf_counter()
                    execution_time_ms = round((t_end - t_start) * 1000, 2)

                    if match:
                        result = {
                            'valid': True,
                            'discount': '15%',
                            'message': f"Mã hợp lệ! Bạn được giảm giá 15%."
                        }
                    else:
                        result = {
                            'valid': False,
                            'message': "Mã không hợp lệ hoặc sai định dạng quy định."
                        }

    return render_template(
        'tools/coupon.html',
        coupon_code=coupon_code,
        result=result,
        execution_time_ms=execution_time_ms,
        error=error,
        is_vuln=is_vuln
    )
