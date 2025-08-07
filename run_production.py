#!/usr/bin/env python3
"""
Production startup script for Prostate Care AI
Optimized for Google Cloud deployment
"""
import os
import logging
from app import app

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

# Import routes to register them
import routes  # noqa: F401

if __name__ == '__main__':
    # Get port from environment (default for Cloud Run)
    port = int(os.environ.get('PORT', 8080))
    
    # Run in production mode
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )