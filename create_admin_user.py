#!/usr/bin/env python3
"""
Script tạo user admin đầu tiên cho production
Script to create first admin user for production
"""

import os
import sys
import getpass
from pathlib import Path

# Thêm thư mục ứng dụng vào Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Load environment variables
from production_config import load_environment_variables
load_environment_variables()

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Tạo user admin đầu tiên"""
    
    with app.app_context():
        # Kiểm tra xem đã có admin user chưa
        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            print(f"❌ Admin user đã tồn tại: {existing_admin.username}")
            return
        
        print("🔧 Tạo user admin đầu tiên cho hệ thống")
        print("=" * 50)
        
        # Nhập thông tin admin
        username = input("Nhập username admin: ").strip()
        if not username:
            username = "admin"
            
        email = input("Nhập email admin: ").strip()
        if not email:
            email = "admin@example.com"
            
        # Nhập mật khẩu an toàn
        while True:
            password = getpass.getpass("Nhập mật khẩu admin: ")
            password_confirm = getpass.getpass("Xác nhận mật khẩu: ")
            
            if password == password_confirm:
                if len(password) >= 8:
                    break
                else:
                    print("❌ Mật khẩu phải có ít nhất 8 ký tự!")
            else:
                print("❌ Mật khẩu xác nhận không khớp!")
        
        try:
            # Tạo admin user
            admin_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=True,
                can_delete_patients=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Tạo admin user thành công!")
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Quyền: Admin (có thể xóa bệnh nhân)")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Lỗi tạo admin user: {str(e)}")

def verify_database_connection():
    """Kiểm tra kết nối database"""
    
    with app.app_context():
        try:
            # Test database connection
            with db.engine.connect() as connection:
                connection.execute(db.text('SELECT 1'))
            print("✅ Kết nối database thành công")
            
            # Tạo tables nếu chưa có
            db.create_all()
            print("✅ Database tables đã sẵn sàng")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {str(e)}")
            print("   Kiểm tra lại DATABASE_URL trong .env file")
            return False

if __name__ == "__main__":
    print("🏥 Prostate Cancer Management System - Admin Setup")
    print("=" * 60)
    
    # Kiểm tra database connection
    if verify_database_connection():
        # Tạo admin user
        create_admin_user()
    else:
        print("❌ Không thể kết nối database. Vui lòng kiểm tra cấu hình.")