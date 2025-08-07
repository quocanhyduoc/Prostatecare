# Hướng dẫn Upload Ứng dụng Flask lên cPanel

## Tổng quan
Hướng dẫn này sẽ giúp bạn upload và deploy ứng dụng Prostate Cancer Patient Management System lên shared hosting sử dụng cPanel.

## Yêu cầu hệ thống
- cPanel hosting hỗ trợ Python 3.11+
- PostgreSQL hoặc MySQL database
- SSL certificate (khuyến nghị)
- Ít nhất 1GB RAM
- Ít nhất 5GB disk space

## Bước 1: Chuẩn bị File Upload

### 1.1 Tạo file requirements.txt
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.1
Flask-Login==0.6.3
WTForms==3.1.0
Werkzeug==3.0.1
email-validator==2.1.0
google-genai==0.5.4
matplotlib==3.8.2
numpy==1.25.2
pandas==2.1.4
Pillow==10.1.0
psycopg2-binary==2.9.9
PyJWT==2.8.0
reportlab==4.0.7
requests==2.31.0
scipy==1.11.4
SQLAlchemy==2.0.23
Twilio==8.10.0
openpyxl==3.1.2
xlsxwriter==3.1.9
gunicorn==21.2.0
```

### 1.2 Tạo file .htaccess cho Apache
```apache
RewriteEngine On
RewriteRule ^(.*)$ /cgi-bin/app.cgi/$1 [QSA,L]

# Bảo mật file cấu hình
<Files "*.py">
    Order allow,deny
    Deny from all
</Files>

<Files "app.cgi">
    Order allow,deny
    Allow from all
</Files>

# Bảo vệ thư mục nhạy cảm
RedirectMatch 404 /\.git
RedirectMatch 404 /\.env
RedirectMatch 404 /config\.py
```

### 1.3 Tạo file app.cgi cho CGI execution
```python
#!/usr/bin/python3

import sys
import os

# Thêm thư mục ứng dụng vào Python path
sys.path.insert(0, '/home/yourusername/public_html/')

# Import ứng dụng Flask
from main import app

# Thiết lập môi trường production
os.environ['FLASK_ENV'] = 'production'

if __name__ == '__main__':
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)
```

## Bước 2: Cấu hình Database

### 2.1 Tạo Database PostgreSQL/MySQL trên cPanel
1. Đăng nhập cPanel
2. Tìm "PostgreSQL Databases" hoặc "MySQL Databases"
3. Tạo database mới: `prostate_cancer_db`
4. Tạo user database với full privileges
5. Ghi nhớ thông tin kết nối:
   - Database Name: `username_prostate_cancer_db`
   - Database User: `username_dbuser`
   - Database Password: `your_secure_password`
   - Database Host: `localhost`

### 2.2 Cập nhật file môi trường
Tạo file `.env` với thông tin database:
```
DATABASE_URL=postgresql://username_dbuser:your_secure_password@localhost/username_prostate_cancer_db
SESSION_SECRET=your_very_secure_session_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone
```

## Bước 3: Chuẩn bị Code cho Production

### 3.1 Cập nhật app.py cho production
```python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Tạo Flask app
app = Flask(__name__)

# Cấu hình cho production
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'your-fallback-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Proxy fix cho shared hosting
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Khởi tạo database
db.init_app(app)

# Import routes và models
with app.app_context():
    import models
    import routes
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
```

### 3.2 Cập nhật main.py
```python
#!/usr/bin/env python3
import os
import sys

# Thêm thư mục hiện tại vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app import app

# Load environment variables từ .env file
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

if __name__ == '__main__':
    app.run(debug=False)
```

## Bước 4: Upload File lên cPanel

### 4.1 Sử dụng File Manager
1. Đăng nhập cPanel
2. Mở "File Manager"
3. Điều hướng đến `public_html`
4. Upload tất cả file ứng dụng:
   ```
   public_html/
   ├── .htaccess
   ├── .env
   ├── app.cgi (chmod 755)
   ├── app.py
   ├── main.py
   ├── models.py
   ├── routes.py
   ├── forms.py
   ├── pdf_generator.py
   ├── ai_prediction.py
   ├── gemini_ai.py
   ├── translations.py
   ├── requirements.txt
   ├── templates/
   ├── static/
   └── images/
   ```

### 4.2 Thiết lập quyền file
- `app.cgi`: 755 (executable)
- `.htaccess`: 644
- `.env`: 600 (bảo mật)
- Các file Python: 644
- Thư mục: 755

## Bước 5: Cài đặt Python Dependencies

### 5.1 Sử dụng SSH (nếu có)
```bash
cd ~/public_html
pip3 install --user -r requirements.txt
```

### 5.2 Sử dụng Python App trong cPanel
1. Tìm "Python App" trong cPanel
2. Tạo Python App mới:
   - Python version: 3.11
   - Application root: public_html
   - Application URL: yourdomain.com
3. Vào "Packages" và install từ requirements.txt

## Bước 6: Cấu hình SSL và Domain

### 6.1 Kích hoạt SSL
1. Tìm "SSL/TLS" trong cPanel
2. Kích hoạt "Force HTTPS Redirect"
3. Cài đặt Let's Encrypt certificate (miễn phí)

### 6.2 Cập nhật DNS (nếu cần)
- Trỏ domain về IP server hosting
- Chờ DNS propagation (24-48 giờ)

## Bước 7: Test và Troubleshooting

### 7.1 Kiểm tra log lỗi
```bash
tail -f ~/logs/yourdomain.com.error.log
```

### 7.2 Các lỗi thường gặp và cách fix

#### Lỗi 500 Internal Server Error
- Kiểm tra quyền file app.cgi (phải là 755)
- Kiểm tra shebang line trong app.cgi
- Xem error log để biết chi tiết

#### Lỗi kết nối database
- Kiểm tra DATABASE_URL trong .env
- Đảm bảo database user có đủ quyền
- Test kết nối database bằng cPanel

#### Lỗi import module
- Kiểm tra đường dẫn Python trong sys.path
- Đảm bảo tất cả dependencies đã được cài
- Kiểm tra Python version compatibility

### 7.3 Tạo user admin đầu tiên
Tạo script `create_admin.py`:
```python
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/home/yourusername/public_html/')

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Tạo admin user
    admin = User(
        username='admin',
        email='admin@yourdomain.com',
        password_hash=generate_password_hash('your_secure_admin_password'),
        is_admin=True,
        can_delete_patients=True
    )
    
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully!")
```

Chạy script:
```bash
cd ~/public_html
python3 create_admin.py
```

## Bước 8: Bảo mật Production

### 8.1 Cấu hình bảo mật .htaccess
```apache
# Bảo vệ file nhạy cảm
<Files ".env">
    Order allow,deny
    Deny from all
</Files>

<Files "*.py">
    Order allow,deny
    Deny from all
</Files>

# Chỉ cho phép app.cgi chạy
<Files "app.cgi">
    Order allow,deny
    Allow from all
</Files>

# Chặn truy cập thư mục hệ thống
RedirectMatch 404 /\.
RedirectMatch 404 /__pycache__
```

### 8.2 Backup định kỳ
- Thiết lập backup database hàng ngày
- Backup file ứng dụng hàng tuần
- Lưu trữ backup ở vị trí an toàn

## Bước 9: Monitoring và Maintenance

### 9.1 Giám sát hiệu năng
- Theo dõi usage CPU/Memory
- Monitor database connections
- Kiểm tra disk space định kỳ

### 9.2 Cập nhật bảo mật
- Cập nhật dependencies định kỳ
- Monitor security advisories
- Thay đổi password định kỳ

## Liên hệ hỗ trợ
- Email: support@yourdomain.com
- Documentation: https://yourdomain.com/docs
- Emergency: +84-xxx-xxx-xxxx

---
*Hướng dẫn này được tạo cho Prostate Cancer Patient Management System v1.0*
*Cập nhật lần cuối: August 1, 2025*