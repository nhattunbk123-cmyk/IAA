<?php
/**
 * File mẫu gửi mã OTP qua Gmail SMTP bằng PHP và PHPMailer
 * Đã cấu hình sẵn tài khoản: testhieu652@gmail.com
 */

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

// Nạp thư viện PHPMailer (nếu dùng composer)
if (!file_exists(__DIR__ . '/vendor/autoload.php')) {
    echo "⚠️ CHÚ Ý: Chưa tìm thấy thư mục vendor của PHPMailer!\n";
    echo "Hãy chạy lệnh sau trong terminal để cài đặt thư viện:\n";
    echo "    composer require phpmailer/phpmailer\n\n";
    exit(1);
}

require_once __DIR__ . '/vendor/autoload.php';

function sendOtpViaGmail(string $toEmail, string $toName, string $otpCode): bool
{
    $mail = new PHPMailer(true);

    try {
        // Cấu hình máy chủ SMTP Gmail
        $mail->isSMTP();
        $mail->Host       = 'smtp.gmail.com';
        $mail->SMTPAuth   = true;
        $mail->Username   = 'testhieu652@gmail.com'; // Tài khoản Gmail gửi
        $mail->Password   = 'anisjbxkpobxvrlk';      // Mật khẩu ứng dụng 16 ký tự
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port       = 587;
        $mail->CharSet    = 'UTF-8';

        // Người gửi & Người nhận
        $mail->setFrom('testhieu652@gmail.com', 'Laptop52h.vn Security');
        $mail->addAddress($toEmail, $toName);

        // Nội dung Email
        $mail->isHTML(true);
        $mail->Subject = "[Laptop52h.vn] Mã xác thực OTP: [{$otpCode}]";
        $mail->Body    = "
            <div style='max-width: 500px; margin: auto; padding: 20px; font-family: Arial, sans-serif; border: 1px solid #e2e8f0; border-radius: 10px;'>
                <h2 style='color: #1d4ed8; text-align: center;'>Laptop52h.vn</h2>
                <p>Xin chào <strong>{$toName}</strong>,</p>
                <p>Mã xác thực OTP gồm 6 chữ số của bạn là:</p>
                <div style='text-align: center; margin: 20px 0;'>
                    <span style='font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #1d4ed8; background: #eff6ff; padding: 10px 24px; border-radius: 8px; border: 2px dashed #3b82f6;'>
                        {$otpCode}
                    </span>
                </div>
                <p style='color: #ef4444; font-size: 13px;'>⏱️ Mã này có hiệu lực trong vòng 5 phút. Tuyệt đối không chia sẻ mã cho bất kỳ ai!</p>
            </div>
        ";
        $mail->AltBody = "Mã xác thực OTP của bạn là: {$otpCode}. Có hiệu lực trong 5 phút.";

        $mail->send();
        echo "✅ ĐÃ GỬI THÀNH CÔNG mã OTP [{$otpCode}] tới email: {$toEmail}\n";
        return true;
    } catch (Exception $e) {
        echo "❌ GỬI THẤT BẠI: {$mail->ErrorInfo}\n";
        return false;
    }
}

// Thử nghiệm sinh mã 6 số và gửi
$testOtp = (string)random_int(100000, 999999);
echo "Đang thử gửi mã OTP [{$testOtp}] tới: testhieu652@gmail.com...\n";
sendOtpViaGmail('testhieu652@gmail.com', 'Phan Hiếu', $testOtp);
