# 🚀 Hướng dẫn Deploy lên cPanel - Prostate Cancer Management System

## 📦 File đã tạo sẵn cho deployment

### File cấu hình chính:
- ✅ **`app.cgi`** - CGI script chạy ứng dụng Flask (chmod 755)
- ✅ **`.htaccess`** - Cấu hình Apache với bảo mật và rewrite rules  
- ✅ **`wsgi.py`** - WSGI entry point cho production
- ✅ **`production_config.py`** - Cấu hình production với logging và bảo mật
- ✅ **`.env.example`** - Template file môi trường (copy thành `.env`)
- ✅ **`requirements_cpanel.txt`** - Dependencies cho shared hosting

### Script hỗ trợ:
- ✅ **`create_admin_user.py`** - Tạo admin user đầu tiên (chmod 755)
- ✅ **`quick_deploy_script.sh`** - Script chuẩn bị deployment tự động

### Tài liệu:
- ✅ **`cpanel_deployment_guide.md`** - Hướng dẫn chi tiết từng bước
- ✅ **`deployment_checklist.md`** - Checklist kiểm tra deployment
- ✅ **`DEPLOY_README.md`** - File này (tóm tắt nhanh)

## 🎯 Các bước deploy nhanh

### Bước 1: Chuẩn bị
```bash
# Chạy script chuẩn bị tự động
chmod +x quick_deploy_script.sh
./quick_deploy_script.sh
```

### Bước 2: Cấu hình database
1. Vào cPanel → PostgreSQL/MySQL Databases
2. Tạo database: `username_prostate_cancer_db`
3. Tạo user với full privileges
4. Ghi nhớ: host, database, username, password

### Bước 3: Cấu hình .env
```bash
# Copy template và edit
cp .env.example .env
nano .env  # Hoặc edit qua File Manager
```

Cập nhật:
```
DATABASE_URL=postgresql://user:pass@localhost/dbname
SESSION_SECRET=your-secure-random-key-here
GEMINI_API_KEY=your-gemini-key  # Tùy chọn cho AI
```

### Bước 4: Upload lên cPanel
1. Zip tất cả file: `prostate_cancer_app.zip` 
2. Upload qua File Manager → public_html
3. Extract zip file
4. Set permissions:
   - `app.cgi`: 755
   - `.env`: 600
   - `.htaccess`: 644

### Bước 5: Cài đặt dependencies
**Nếu có SSH:**
```bash
cd ~/public_html  
pip3 install --user -r requirements_cpanel.txt
```

**Hoặc dùng Python App trong cPanel:**
- Tạo Python App mới (Python 3.11+)
- Upload requirements_cpanel.txt
- Install packages qua giao diện

### Bước 6: Tạo admin user
```bash
cd ~/public_html
python3 create_admin_user.py
```

### Bước 7: Test application
- Truy cập: https://yourdomain.com
- Đăng nhập với admin account
- Test các chức năng chính

## 🔧 Troubleshooting nhanh

### Lỗi 500 Internal Server Error
```bash
# Kiểm tra permissions
chmod 755 app.cgi
ls -la app.cgi

# Kiểm tra error log
tail ~/logs/yourdomain.com.error.log
```

### Lỗi database connection
```bash
# Test kết nối
python3 -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ.get('DATABASE_URL'))
with engine.connect() as conn:
    print('✅ Database OK')
"
```

### Lỗi missing modules
```bash
# Kiểm tra installed packages
pip3 list | grep Flask
pip3 install --user Flask
```

## 📱 Features hoạt động sau deploy

- ✅ **Quản lý bệnh nhân** - Thêm, sửa, xóa, tìm kiếm
- ✅ **Xét nghiệm máu** - Nhập kết quả, theo dõi PSA
- ✅ **Báo cáo PDF** - Xuất báo cáo tiếng Việt hoàn chỉnh
- ✅ **AI Risk Assessment** - Phân tích nguy cơ (cần GEMINI_API_KEY)
- ✅ **Import/Export Excel** - Bulk data management
- ✅ **Multi-user system** - Admin và user roles
- ✅ **SMS Notifications** - Nhắc hẹn (cần Twilio)
- ✅ **Responsive UI** - Tương thích mobile

## 🔒 Bảo mật production

File `.htaccess` đã cấu hình:
- Bảo vệ file `.py`, `.env`
- Security headers (XSS, CSRF protection)
- SSL/HTTPS redirect
- File compression và caching

## 📞 Hỗ trợ

**Nếu gặp vấn đề:**
1. Kiểm tra `deployment_checklist.md`
2. Xem `cpanel_deployment_guide.md` 
3. Check error logs: `~/logs/`
4. Liên hệ hosting provider nếu cần

**Thông tin kỹ thuật:**
- Framework: Flask 3.0.0
- Database: PostgreSQL/MySQL
- Python: 3.11+
- UI: Bootstrap 5 + Vietnamese language
- PDF: ReportLab với font Unicode
- Charts: matplotlib + Chart.js

---
*Package deployment được tạo ngày August 1, 2025*
*Phiên bản: Prostate Cancer Management System v1.0*