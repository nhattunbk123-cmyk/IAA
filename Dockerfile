# Sử dụng hình ảnh Python 3.11-slim tối ưu kích thước và bảo mật
FROM python:3.11-slim

# Thiết lập các biến môi trường cho Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các gói phụ thuộc hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Sao chép và cài đặt các dependencies Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn dự án vào container
COPY . .

# Khởi tạo thư mục instance cho SQLite database và khởi tạo dữ liệu mẫu
RUN mkdir -p /app/instance && python scripts/init_db.py

# Mở cổng 5000 nội bộ trong container
EXPOSE 5000

# Chạy ứng dụng web bằng python run.py
CMD ["python", "run.py"]
