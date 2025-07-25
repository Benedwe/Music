"""
Configuration file for the web application
Contains additional security vulnerabilities
"""

import os

class Config:
    # Bug 1: Hardcoded secrets and sensitive information
    SECRET_KEY = 'super_secret_key_12345'
    DATABASE_URL = 'sqlite:///users.db'
    
    # Bug 1: Hardcoded API keys and credentials
    API_KEY = 'sk-1234567890abcdef'
    ADMIN_PASSWORD = 'admin123'
    
    # Bug 1: Debug mode enabled
    DEBUG = True
    TESTING = False
    
    # Bug 2: Insecure default configurations
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    WTF_CSRF_ENABLED = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    # Bug 1: Using weak database in production
    DATABASE_URL = 'sqlite:///dev.db'

class ProductionConfig(Config):
    # Bug 1: Still using hardcoded secrets in production
    SECRET_KEY = 'production_secret_key_67890'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Fixed: Safe logging configuration with error handling
        import logging
        import os
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.join(os.getcwd(), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'app.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.WARNING)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Fallback to console logging if file logging fails
            app.logger.warning(f"Could not set up file logging: {e}")
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            app.logger.addHandler(console_handler)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}