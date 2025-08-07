#!/usr/bin/env python3
"""
Cấu hình production cho cPanel deployment
Production configuration for cPanel deployment
"""

import os
import sys
from pathlib import Path

# Thiết lập đường dẫn cho cPanel shared hosting
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

class ProductionConfig:
    """Cấu hình production cho ứng dụng Flask"""
    
    # Cấu hình cơ bản
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'production-secret-key-change-this'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///prostate_cancer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
        'echo': False  # Tắt SQL logging trong production
    }
    
    # Flask configuration
    DEBUG = False
    TESTING = False
    
    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(current_dir, 'images')
    
    # Security configuration
    SESSION_COOKIE_SECURE = True  # Yêu cầu HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # WTF CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Mail configuration (optional)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    @staticmethod
    def init_app(app):
        """Khởi tạo cấu hình cho ứng dụng"""
        
        # Tạo thư mục upload nếu chưa có
        upload_folder = ProductionConfig.UPLOAD_FOLDER
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, mode=0o755)
            
        # Thiết lập logging cho production
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            # Tạo thư mục logs
            if not os.path.exists('logs'):
                os.mkdir('logs')
                
            # Thiết lập rotating file handler
            file_handler = RotatingFileHandler(
                'logs/prostate_cancer.log',
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Prostate Cancer Management System startup')

def load_environment_variables():
    """Load environment variables từ .env file"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Load environment variables khi import module
load_environment_variables()