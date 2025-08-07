# 🔧 Troubleshooting Guide - cPanel 122.0.16 Terminal

## Các lỗi thường gặp và cách sử dụng Terminal để fix

---

## 1. Lỗi 500 Internal Server Error

### Triệu chứng:
- Website hiển thị "Internal Server Error"
- Không load được trang chính

### Cách debug qua Terminal:

```bash
# Bước 1: Kiểm tra error log
cd ~/public_html
tail -f ~/logs/$(hostname).error.log

# Bước 2: Kiểm tra file permissions
ls -la app.cgi
# Phải hiển thị: -rwxr-xr-x (755)

# Nếu sai, fix permission:
chmod 755 app.cgi

# Bước 3: Test CGI script trực tiếp
python3 app.cgi
# Nếu có lỗi, sẽ hiển thị chi tiết

# Bước 4: Kiểm tra shebang line
head -1 app.cgi
# Phải là: #!/usr/bin/python3 hoặc #!/usr/bin/env python3

# Bước 5: Test import modules
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from main import app
    print('✅ App import successful')
except Exception as e:
    print('❌ Import error:', e)
    import traceback
    traceback.print_exc()
"
```

### Fix thường thấy:
```bash
# Fix permission
chmod 755 app.cgi
chmod 644 .htaccess
chmod 600 .env

# Fix shebang nếu cần
which python3  # Kiểm tra đường dẫn Python
# Cập nhật dòng đầu app.cgi nếu cần
```

---

## 2. Lỗi Database Connection

### Triệu chứng:
- "Database connection failed"
- "SQLALCHEMY_DATABASE_URI not found"

### Debug qua Terminal:

```bash
# Bước 1: Kiểm tra .env file
cat .env | grep DATABASE_URL
# Format phải đúng: postgresql://user:pass@host/dbname

# Bước 2: Test kết nối trực tiếp
python3 -c "
import os
import psycopg2

# Load .env
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

db_url = os.environ.get('DATABASE_URL')
print(f'Database URL: {db_url}')

try:
    # Parse URL
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],  # Remove leading /
        user=parsed.username,
        password=parsed.password,
        port=parsed.port or 5432
    )
    print('✅ Database connection successful')
    
    cursor = conn.cursor()
    cursor.execute('SELECT version()')
    version = cursor.fetchone()[0]
    print(f'PostgreSQL version: {version}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Database error: {e}')
    print('Check your database credentials in cPanel')
"

# Bước 3: Kiểm tra database tồn tại
# Vào cPanel → PostgreSQL Databases
# Verify database name, user, và permissions
```

### Fix database issues:
```bash
# 1. Kiểm tra database URL format
echo $DATABASE_URL

# 2. Test với psql nếu có
psql -h localhost -U username_dbuser -d username_prostate_cancer_db -c "SELECT 1;"

# 3. Recreate .env nếu cần
cp .env.example .env
nano .env  # Edit với thông tin đúng
```

---

## 3. Lỗi Missing Python Modules

### Triệu chứng:
- "No module named 'Flask'"
- "ModuleNotFoundError"

### Debug và fix:

```bash
# Bước 1: Kiểm tra Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Bước 2: Kiểm tra installed packages
pip3 list | grep -i flask
pip3 list | grep -i sqlalchemy

# Bước 3: Install missing packages
pip3 install --user Flask==3.0.0
pip3 install --user Flask-SQLAlchemy==3.1.1
pip3 install --user Flask-WTF==1.2.1

# Hoặc install tất cả từ requirements
pip3 install --user -r requirements_cpanel.txt

# Bước 4: Test import
python3 -c "
import Flask
import flask_sqlalchemy
import flask_wtf
print('✅ All core modules imported successfully')
"

# Bước 5: Nếu vẫn lỗi, check user installation
ls -la ~/.local/lib/python*/site-packages/ | grep -i flask
```

---

## 4. Lỗi Font/PDF Generation

### Triệu chứng:
- PDF không tạo được
- "Font not found" error
- Vietnamese text không hiển thị

### Debug PDF qua Terminal:

```bash
# Test PDF generation
python3 -c "
import sys
sys.path.insert(0, '.')

# Load environment
import os
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

from app import app, db
from models import Patient
from pdf_generator import generate_patient_report

with app.app_context():
    # Get a test patient
    patient = Patient.query.first()
    if patient:
        try:
            pdf_path = generate_patient_report(patient, [])
            print(f'✅ PDF generated: {pdf_path}')
            
            import os
            size = os.path.getsize(pdf_path)
            print(f'File size: {size} bytes')
            os.unlink(pdf_path)  # Cleanup
            
        except Exception as e:
            print(f'❌ PDF error: {e}')
            import traceback
            traceback.print_exc()
    else:
        print('No patient data for testing')
"

# Kiểm tra font files
find ~/.local/lib/python*/site-packages/ -name "*font*" -type d
```

---

## 5. Lỗi Permission Denied

### Triệu chứng:
- "Permission denied" khi truy cập files
- "Cannot write to directory"

### Fix permissions:

```bash
# Kiểm tra ownership
ls -la ~/public_html/

# Fix ownership nếu cần (thay 'username' bằng username thực)
chown -R username:username ~/public_html/

# Set correct permissions
find ~/public_html -type d -exec chmod 755 {} \;
find ~/public_html -type f -name "*.py" -exec chmod 644 {} \;
chmod 755 ~/public_html/app.cgi
chmod 755 ~/public_html/create_admin_user.py
chmod 600 ~/public_html/.env
chmod 644 ~/public_html/.htaccess

# Tạo thư mục logs nếu chưa có
mkdir -p ~/public_html/logs
chmod 755 ~/public_html/logs

# Tạo thư mục images nếu chưa có
mkdir -p ~/public_html/images
chmod 755 ~/public_html/images
```

---

## 6. Lỗi Memory/Resource Limits

### Triệu chứng:
- "MemoryError"
- "Resource temporarily unavailable"
- App chạy chậm

### Monitor và optimize:

```bash
# Kiểm tra memory usage
ps aux | grep python
top -u $(whoami)

# Kiểm tra disk usage
du -sh ~/public_html
df -h

# Clean up temporary files
find ~/public_html -name "*.pyc" -delete
find ~/public_html -name "__pycache__" -type d -exec rm -rf {} +

# Kiểm tra log file sizes
ls -lh ~/logs/
find ~/logs -name "*.log" -size +10M -ls

# Rotate logs nếu quá lớn
mv ~/logs/error.log ~/logs/error.log.old
touch ~/logs/error.log
```

---

## 7. SSL/HTTPS Issues

### Triệu chứng:
- "Mixed content" warnings
- SSL certificate errors

### Debug SSL:

```bash
# Test SSL connection
curl -I https://yourdomain.com

# Kiểm tra certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Force HTTPS trong .htaccess (đã có sẵn)
cat .htaccess | grep -i "https\|ssl"
```

---

## 8. Slow Performance Issues

### Debug performance:

```bash
# Kiểm tra slow queries
python3 -c "
import sys, os, time
sys.path.insert(0, '.')

# Load environment
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

from app import app, db
from sqlalchemy import text

with app.app_context():
    start_time = time.time()
    
    # Test simple query
    result = db.session.execute(text('SELECT COUNT(*) FROM users'))
    count = result.scalar()
    
    end_time = time.time()
    print(f'Query time: {end_time - start_time:.3f}s')
    print(f'User count: {count}')
"

# Optimize database
python3 -c "
import sys, os
sys.path.insert(0, '.')

with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

from app import app, db
from sqlalchemy import text

with app.app_context():
    # Run VACUUM ANALYZE (PostgreSQL)
    try:
        db.session.execute(text('VACUUM ANALYZE'))
        print('✅ Database optimized')
    except Exception as e:
        print(f'Note: {e}')
"
```

---

## 9. AI/Gemini API Issues

### Debug AI functionality:

```bash
# Test API key
python3 -c "
import os
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

api_key = os.environ.get('GEMINI_API_KEY')
if api_key:
    print(f'API Key present: {api_key[:10]}...{api_key[-5:]}')
    
    # Test API call
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Test message'
        )
        print('✅ Gemini API working')
        
    except Exception as e:
        print(f'❌ API Error: {e}')
else:
    print('❌ No API key found')
"
```

---

## 10. Emergency Recovery

### Quick recovery procedures:

```bash
# 1. Backup current state
cd ~/public_html
tar -czf emergency_backup_$(date +%Y%m%d_%H%M%S).tar.gz .

# 2. Reset file permissions
chmod 755 app.cgi
chmod 644 .htaccess
chmod 600 .env
chmod 644 *.py

# 3. Restart "application" (CGI restarts automatically)
touch app.cgi

# 4. Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 5. Test basic functionality
python3 -c "from main import app; print('✅ App loads')"

# 6. Check database
python3 -c "
import sys, os
sys.path.insert(0, '.')
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database OK')
"
```

---

## Advanced Debugging Tools

### Detailed error logging:

```bash
# Tạo debug script
cat > debug_app.py << 'EOF'
#!/usr/bin/env python3
import sys, os, traceback, logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, '.')

# Load environment
try:
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    print("✅ Environment loaded")
except Exception as e:
    print(f"❌ Environment error: {e}")

# Test imports
try:
    from app import app, db
    print("✅ App imported")
except Exception as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()

# Test database
try:
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")
except Exception as e:
    print(f"❌ Database error: {e}")
    traceback.print_exc()

print("Debug complete")
EOF

chmod +x debug_app.py
python3 debug_app.py
```

---

**Lưu ý quan trọng:** Luôn backup trước khi thực hiện troubleshooting. Sử dụng Terminal cẩn thận và test từng bước một.

**Liên hệ support:** Nếu vấn đề vẫn không được giải quyết, liên hệ hosting provider với error logs cụ thể.