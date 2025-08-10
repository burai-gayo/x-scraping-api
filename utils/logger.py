import logging
import logging.handlers
import os
import json
from datetime import datetime
from config.config import Config

class CustomFormatter(logging.Formatter):
    """カスタムログフォーマッター"""
    
    def format(self, record):
        # 個人情報をマスキング
        if hasattr(record, 'user_info'):
            record.user_info = self.mask_sensitive_data(record.user_info)
        
        return super().format(record)
    
    def mask_sensitive_data(self, data):
        """個人情報のマスキング"""
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if key.lower() in ['username', 'email', 'user_id']:
                    masked[key] = self.mask_string(str(value))
                else:
                    masked[key] = value
            return masked
        elif isinstance(data, str):
            return self.mask_string(data)
        return data
    
    def mask_string(self, text):
        """文字列のマスキング"""
        if len(text) <= 3:
            return '*' * len(text)
        return text[:2] + '*' * (len(text) - 4) + text[-2:]

def setup_logger():
    """ログ設定のセットアップ"""
    logger = logging.getLogger('x_scraping_api')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # ログディレクトリの作成
    log_dir = os.path.dirname(Config.LOG_FILE_PATH)
    os.makedirs(log_dir, exist_ok=True)
    
    # ファイルハンドラー（ローテーション付き）
    file_handler = logging.handlers.RotatingFileHandler(
        Config.LOG_FILE_PATH,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    
    # フォーマッター
    formatter = CustomFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_request(logger, request_id, action, target, start_time=None):
    """リクエストログの記録"""
    log_data = {
        'request_id': request_id,
        'action': action,
        'target': target,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if start_time:
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        log_data['processing_time'] = processing_time
    
    logger.info(f"Request processed: {json.dumps(log_data)}")

def log_error(logger, request_id, error, action=None):
    """エラーログの記録"""
    log_data = {
        'request_id': request_id,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if action:
        log_data['action'] = action
    
    logger.error(f"Error occurred: {json.dumps(log_data)}")

def log_metrics(logger, metrics):
    """メトリクスログの記録"""
    logger.info(f"Metrics: {json.dumps(metrics)}")

# グローバルロガーインスタンス
app_logger = setup_logger()

