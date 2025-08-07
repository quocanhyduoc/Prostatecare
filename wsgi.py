#!/usr/bin/env python3
"""
WSGI entry point for production deployment
Điểm vào WSGI cho việc deploy production
"""

import os
import sys
from pathlib import Path

# Thêm thư mục ứng dụng vào Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# Load environment variables
def load_dotenv():
    """Load environment variables từ .env file"""
    env_file = current_dir / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Load environment variables
load_dotenv()

# Thiết lập môi trường production
os.environ['FLASK_ENV'] = 'production'

# Import Flask application
from app import app

# Application object cho WSGI server
application = app

if __name__ == "__main__":
    application.run()