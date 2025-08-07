#!/usr/bin/python3
"""
CGI script for cPanel deployment
Script CGI cho việc deploy trên cPanel
"""

import sys
import os
import cgitb

# Enable CGI error reporting
cgitb.enable()

# Lấy đường dẫn thư mục hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Thêm thư mục ứng dụng vào Python path
sys.path.insert(0, current_dir)

try:
    # Load environment variables
    from production_config import load_environment_variables
    load_environment_variables()
    
    # Import Flask app
    from main import app
    
    # Thiết lập môi trường production
    os.environ['FLASK_ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Chạy ứng dụng qua CGI
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)
    
except Exception as e:
    # In lỗi ra browser để debug
    print("Content-Type: text/html\n")
    print(f"<h1>Application Error</h1>")
    print(f"<p>Error: {str(e)}</p>")
    print(f"<p>Python path: {sys.path}</p>")
    print(f"<p>Current directory: {current_dir}</p>")
    
    # Ghi lỗi vào log file
    import traceback
    error_log = os.path.join(current_dir, 'error.log')
    with open(error_log, 'a') as f:
        f.write(f"CGI Error: {str(e)}\n")
        f.write(traceback.format_exc())
        f.write("\n" + "="*50 + "\n")