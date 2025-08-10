import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API設定
    API_KEY = os.getenv('API_KEY', 'default-api-key')
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '30'))
    RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
    
    # X.com設定
    X_LOGIN_URL = 'https://x.com/i/flow/login'
    X_BASE_URL = 'https://x.com'
    COOKIE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'cookies', 'x_cookies.json')
    
    # スクレイピング設定
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
    PAGE_LOAD_TIMEOUT = int(os.getenv('PAGE_LOAD_TIMEOUT', '15'))
    RETRY_COUNT = int(os.getenv('RETRY_COUNT', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '2'))
    
    # ログ設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # セキュリティ設定
    ALLOWED_IPS = os.getenv('ALLOWED_IPS', '').split(',') if os.getenv('ALLOWED_IPS') else []
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-encryption-key-here')
    
    # Redis設定（レート制限用）
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'False').lower() == 'true'

