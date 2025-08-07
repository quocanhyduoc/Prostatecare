# 🚀 Hướng dẫn Deploy Flask App trên cPanel 122.0.16 (Terminal)

## Tổng quan
Hướng dẫn này dành cho việc deploy ứng dụng Prostate Cancer Management System lên shared hosting sử dụng cPanel 122.0.16 thông qua Terminal tích hợp (không cần SSH).

---

## Phần 1: Chuẩn bị trước khi deploy

### 1.1 Kiểm tra hosting requirements
- ✅ Python 3.8+ (khuyến nghị 3.11+)
- ✅ PostgreSQL hoặc MySQL database
- ✅ SSL certificate (Let's Encrypt miễn phí)
- ✅ Ít nhất 1GB RAM, 5GB disk space

### 1.2 Tạo package deployment
```bash
# Chạy trên máy local hoặc Replit
./quick_deploy_script.sh
```

Sẽ tạo file `prostate_cancer_app.zip` chứa:
```
├── app.cgi (executable)
├── .htaccess 
├── .env.example
├── main.py
├── app.py
├── models.py
├── routes.py
├── forms.py
├── pdf_generator.py
├── ai_prediction.py
├── gemini_ai.py
├── translations.py
├── production_config.py
├── wsgi.py
├── create_admin_user.py
├── requirements_cpanel.txt
├── templates/ (folder)
├── static/ (folder)
└── images/ (folder)
```

---

## Phần 2: Setup Database trên cPanel

### 2.1 Tạo PostgreSQL Database
1. **Đăng nhập cPanel** → Tìm "PostgreSQL Databases"
2. **Tạo Database mới:**
   - Database Name: `prostate_cancer_db`
   - Hệ thống sẽ tự thêm prefix: `username_prostate_cancer_db`

3. **Tạo Database User:**
   - Username: `dbuser` 
   - Password: Tạo password mạnh (ít nhất 12 ký tự)
   - Hệ thống sẽ tạo: `username_dbuser`

4. **Gán quyền User:**
   - Chọn user vừa tạo
   - Chọn database vừa tạo  
   - Check "ALL PRIVILEGES"
   - Click "Add"

5. **Ghi nhớ thông tin kết nối:**
   ```
   Host: localhost
   Database: username_prostate_cancer_db
   Username: username_dbuser
   Password: [password bạn vừa tạo]
   Port: 5432 (PostgreSQL) / 3306 (MySQL)
   ```

---

## Phần 3: Upload và Extract Files

### 3.1 Upload qua File Manager
1. **Mở File Manager** từ cPanel
2. **Điều hướng** đến thư mục `public_html`
3. **Upload file** `prostate_cancer_app.zip`
4. **Extract:** Click chuột phải → "Extract"
5. **Xóa file zip** sau khi extract xong

### 3.2 Cấu hình file .env
1. **Copy template:**
   - Rename `.env.example` thành `.env`
   
2. **Edit file .env:**
   ```env
   # Database - Thay thế với thông tin thực tế
   DATABASE_URL=postgresql://username_dbuser:your_password@localhost/username_prostate_cancer_db
   
   # Session Security - Tạo random string 32+ ký tự
   SESSION_SECRET=your-very-secure-random-session-secret-key-here
   
   # AI Integration (tùy chọn)
   GEMINI_API_KEY=your-google-gemini-api-key
   
   # SMS (tùy chọn)
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   TWILIO_PHONE_NUMBER=+1234567890
   
   # Production settings
   FLASK_ENV=production
   FLASK_DEBUG=false
   ```

### 3.3 Set File Permissions
**Thông qua File Manager:**
1. Click chuột phải vào file → "Permissions"
2. Set như sau:
   - `app.cgi`: **755** (rwxr-xr-x)
   - `.env`: **600** (rw-------)  
   - `.htaccess`: **644** (rw-r--r--)
   - `create_admin_user.py`: **755** (rwxr-xr-x)
   - Các file `.py` khác: **644**
   - Thư mục: **755**

---

## Phần 4: Sử dụng Terminal trong cPanel

### 4.1 Mở Terminal
1. **Trong cPanel** → Tìm "Terminal" (có thể trong mục "Advanced")
2. **Click Terminal** → Cửa sổ terminal sẽ mở
3. **Điều hướng** đến thư mục web:
   ```bash
   cd ~/public_html
   pwd  # Kiểm tra đường dẫn hiện tại
   ls -la  # List files
   ```

### 4.2 Kiểm tra Python version
```bash
# Kiểm tra Python có sẵn
python3 --version
which python3

# Kiểm tra pip
pip3 --version
which pip3

# Nếu không có pip3, có thể dùng:
python3 -m pip --version
```

### 4.3 Cài đặt Python dependencies
```bash
# Cài đặt packages với user flag
pip3 install --user -r requirements_cpanel.txt

# Hoặc từng package nếu gặp lỗi:
pip3 install --user Flask==3.0.0
pip3 install --user Flask-SQLAlchemy==3.1.1
pip3 install --user Flask-WTF==1.2.1
pip3 install --user psycopg2-binary==2.9.9
pip3 install --user reportlab==4.0.7
pip3 install --user matplotlib==3.8.2
pip3 install --user google-genai==0.5.4

# Kiểm tra cài đặt
pip3 list | grep Flask
```

### 4.4 Test database connection
```bash
# Test kết nối database
python3 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://username_dbuser:password@localhost/username_prostate_cancer_db'
from sqlalchemy import create_engine
try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        result = conn.execute('SELECT version()')
        print('✅ Database connection successful!')
        print('Version:', result.fetchone()[0])
except Exception as e:
    print('❌ Database error:', str(e))
"
```

### 4.5 Load environment variables và test app
```bash
# Load .env file
export $(cat .env | grep -v '^#' | xargs)

# Kiểm tra variables
echo $DATABASE_URL
echo $SESSION_SECRET

# Test import app
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app import app, db
    print('✅ App import successful')
    
    with app.app_context():
        db.create_all()
        print('✅ Database tables created')
except Exception as e:
    print('❌ Error:', str(e))
    import traceback
    traceback.print_exc()
"
```

---

## Phần 5: Tạo Admin User và Test

### 5.1 Tạo admin user đầu tiên
```bash
# Chạy script tạo admin
python3 create_admin_user.py

# Script sẽ hỏi:
# - Username (mặc định: admin)
# - Email 
# - Password (ít nhất 8 ký tự)
# - Confirm password
```

### 5.2 Test ứng dụng web
```bash
# Test CGI script
python3 app.cgi

# Kiểm tra syntax
python3 -m py_compile app.cgi
python3 -m py_compile main.py
```

### 5.3 Truy cập website
1. **Mở browser** → `https://yourdomain.com`
2. **Kiểm tra:**
   - Trang login hiển thị đúng
   - CSS/JS load properly
   - Đăng nhập với admin account

---

## Phần 6: Troubleshooting thông qua Terminal

### 6.1 Kiểm tra error logs
```bash
# Xem error log của Apache
tail -f ~/logs/yourdomain.com.error.log

# Hoặc tạo custom error log
touch ~/public_html/error.log
chmod 644 ~/public_html/error.log
```

### 6.2 Debug common issues

**❌ Lỗi 500 Internal Server Error:**
```bash
# Kiểm tra file permissions
ls -la app.cgi
chmod 755 app.cgi

# Kiểm tra shebang
head -1 app.cgi

# Test CGI manually
python3 app.cgi
```

**❌ Lỗi "No module named 'xxx'":**
```bash
# Kiểm tra installed packages
pip3 list

# Cài đặt missing package
pip3 install --user package_name

# Kiểm tra Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

**❌ Lỗi database connection:**
```bash
# Test database với psql (nếu có)
psql -h localhost -U username_dbuser -d username_prostate_cancer_db

# Hoặc test với Python
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        database='username_prostate_cancer_db', 
        user='username_dbuser',
        password='your_password'
    )
    print('✅ Direct database connection OK')
    conn.close()
except Exception as e:
    print('❌ Database error:', e)
"
```

### 6.3 Performance monitoring
```bash
# Kiểm tra disk usage
du -sh ~/public_html

# Kiểm tra memory usage của processes
ps aux | grep python

# Kiểm tra file logs size
ls -lh ~/logs/
```

---

## Phần 7: Production Optimization

### 7.1 Cấu hình SSL/HTTPS
1. **Trong cPanel** → "SSL/TLS"
2. **Let's Encrypt:** Kích hoạt free SSL
3. **Force HTTPS Redirect:** Enable
4. **Test:** https://yourdomain.com

### 7.2 Setup backup tự động
```bash
# Tạo script backup database
cat > ~/backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U username_dbuser username_prostate_cancer_db > ~/backups/db_backup_$DATE.sql
# Xóa backup cũ hơn 7 ngày
find ~/backups/ -name "*.sql" -mtime +7 -delete
EOF

chmod +x ~/backup_db.sh

# Tạo thư mục backup
mkdir -p ~/backups

# Test backup
./backup_db.sh
ls -la ~/backups/
```

### 7.3 Monitor logs
```bash
# Tạo script monitor errors
cat > ~/monitor_errors.sh << 'EOF'
#!/bin/bash
ERROR_LOG="$HOME/logs/$(hostname).error.log"
if [ -f "$ERROR_LOG" ]; then
    tail -n 50 "$ERROR_LOG" | grep -i error
fi
EOF

chmod +x ~/monitor_errors.sh

# Chạy monitor
./monitor_errors.sh
```

---

## Phần 8: Advanced Configuration

### 8.1 Cấu hình Python App (nếu hosting hỗ trợ)
1. **cPanel** → "Python App"
2. **Create Application:**
   - Python version: 3.11 (hoặc cao nhất có sẵn)
   - Application root: `public_html`
   - Application URL: `/` (root domain)
   - Application startup file: `wsgi.py`
   - Application Entry point: `application`

3. **Configuration:**
   - Upload `requirements_cpanel.txt`
   - Install packages qua giao diện

### 8.2 Environment variables trong Python App
1. **Trong Python App settings** → "Environment Variables"
2. **Thêm variables:**
   ```
   DATABASE_URL=postgresql://username_dbuser:password@localhost/username_prostate_cancer_db
   SESSION_SECRET=your-secure-key
   FLASK_ENV=production
   ```

---

## Phần 9: Testing và Validation

### 9.1 Functional testing qua Terminal
```bash
# Test các chức năng chính
python3 -c "
import sys, os
sys.path.insert(0, '.')
os.environ.update(dict(line.strip().split('=', 1) for line in open('.env') if '=' in line and not line.startswith('#')))

from app import app, db
from models import User, Patient

with app.app_context():
    # Test user creation
    admin = User.query.filter_by(username='admin').first()
    print(f'✅ Admin user exists: {admin is not None}')
    
    # Test database tables
    print(f'✅ User table: {User.query.count()} users')
    print(f'✅ Patient table: {Patient.query.count()} patients')
    
    print('✅ All tests passed!')
"
```

### 9.2 Load testing (basic)
```bash
# Test concurrent requests (nếu có curl)
for i in {1..5}; do
    curl -s -o /dev/null -w "%{http_code} " https://yourdomain.com &
done
wait
echo "Done"
```

---

## Phần 10: Maintenance và Support

### 10.1 Regular maintenance tasks
```bash
# Weekly maintenance script
cat > ~/weekly_maintenance.sh << 'EOF'
#!/bin/bash
echo "=== Weekly Maintenance $(date) ==="

# Backup database
./backup_db.sh

# Clean old logs
find ~/logs/ -name "*.log" -mtime +30 -delete

# Check disk space
echo "Disk usage:"
du -sh ~/public_html
du -sh ~/logs

# Update packages (careful with this)
# pip3 install --user --upgrade pip

echo "=== Maintenance complete ==="
EOF

chmod +x ~/weekly_maintenance.sh
```

### 10.2 Emergency procedures
```bash
# Quick app restart (CGI tự restart mỗi request)
touch app.cgi

# Database backup ngay lập tức
pg_dump -h localhost -U username_dbuser username_prostate_cancer_db > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# Rollback code (nếu có backup)
# cp -r ~/backups/app_backup_date/* ~/public_html/
```

---

## Phần 11: Security Best Practices

### 11.1 File permissions audit
```bash
# Kiểm tra permissions
find ~/public_html -type f -name "*.py" ! -perm 644 -ls
find ~/public_html -type f -name "app.cgi" ! -perm 755 -ls
find ~/public_html -type f -name ".env" ! -perm 600 -ls

# Fix permissions nếu cần
find ~/public_html -type f -name "*.py" -exec chmod 644 {} \;
chmod 755 ~/public_html/app.cgi
chmod 600 ~/public_html/.env
```

### 11.2 Log monitoring
```bash
# Check for suspicious activity
grep -i "error\|fail\|attack" ~/logs/*.log | tail -20

# Monitor large files
find ~/public_html -type f -size +10M -ls
```

---

## Kết luận

Với hướng dẫn này, bạn có thể hoàn toàn deploy ứng dụng Flask trên cPanel 122.0.16 chỉ sử dụng Terminal tích hợp, không cần SSH.

### Checklist cuối cùng:
- ✅ Database được tạo và kết nối thành công
- ✅ All Python packages được cài đặt  
- ✅ File permissions được set đúng
- ✅ Admin user được tạo
- ✅ Website hoạt động tại https://yourdomain.com
- ✅ SSL được kích hoạt
- ✅ Backup system được thiết lập

### Hỗ trợ:
- **Error logs:** `~/logs/yourdomain.com.error.log`
- **App logs:** `~/public_html/error.log` 
- **Database logs:** Xem trong cPanel PostgreSQL section
- **Support ticket:** Liên hệ hosting provider nếu cần

---
*Tài liệu này được tạo cho Prostate Cancer Management System v1.0*  
*cPanel version: 122.0.16 | Python 3.11+ | PostgreSQL/MySQL*  
*Cập nhật: August 3, 2025*