import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from config.config import Config

class RateLimiter:
    """レート制限管理クラス"""
    
    def __init__(self):
        self.requests_per_minute = defaultdict(deque)
        self.requests_per_hour = defaultdict(deque)
        self.concurrent_requests = defaultdict(int)
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier, request_type='api'):
        """リクエストが許可されるかチェック"""
        with self.lock:
            now = datetime.utcnow()
            
            # 古いリクエスト記録を削除
            self._cleanup_old_requests(identifier, now)
            
            # 同時リクエスト数チェック
            if self.concurrent_requests[identifier] >= Config.MAX_CONCURRENT_REQUESTS:
                return False, "Too many concurrent requests"
            
            # 分間制限チェック
            if len(self.requests_per_minute[identifier]) >= Config.RATE_LIMIT_PER_MINUTE:
                oldest_request = self.requests_per_minute[identifier][0]
                wait_time = 60 - (now - oldest_request).total_seconds()
                return False, f"Rate limit exceeded. Try again in {wait_time:.0f} seconds"
            
            # 時間制限チェック
            if len(self.requests_per_hour[identifier]) >= Config.RATE_LIMIT_PER_HOUR:
                oldest_request = self.requests_per_hour[identifier][0]
                wait_time = 3600 - (now - oldest_request).total_seconds()
                return False, f"Hourly rate limit exceeded. Try again in {wait_time:.0f} seconds"
            
            return True, "Request allowed"
    
    def record_request(self, identifier):
        """リクエストを記録"""
        with self.lock:
            now = datetime.utcnow()
            self.requests_per_minute[identifier].append(now)
            self.requests_per_hour[identifier].append(now)
            self.concurrent_requests[identifier] += 1
    
    def release_request(self, identifier):
        """リクエスト完了を記録"""
        with self.lock:
            if self.concurrent_requests[identifier] > 0:
                self.concurrent_requests[identifier] -= 1
    
    def _cleanup_old_requests(self, identifier, now):
        """古いリクエスト記録を削除"""
        # 1分以上古い記録を削除
        minute_ago = now - timedelta(minutes=1)
        while (self.requests_per_minute[identifier] and 
               self.requests_per_minute[identifier][0] < minute_ago):
            self.requests_per_minute[identifier].popleft()
        
        # 1時間以上古い記録を削除
        hour_ago = now - timedelta(hours=1)
        while (self.requests_per_hour[identifier] and 
               self.requests_per_hour[identifier][0] < hour_ago):
            self.requests_per_hour[identifier].popleft()
    
    def get_stats(self, identifier):
        """統計情報を取得"""
        with self.lock:
            now = datetime.utcnow()
            self._cleanup_old_requests(identifier, now)
            
            return {
                'requests_per_minute': len(self.requests_per_minute[identifier]),
                'requests_per_hour': len(self.requests_per_hour[identifier]),
                'concurrent_requests': self.concurrent_requests[identifier],
                'limits': {
                    'per_minute': Config.RATE_LIMIT_PER_MINUTE,
                    'per_hour': Config.RATE_LIMIT_PER_HOUR,
                    'concurrent': Config.MAX_CONCURRENT_REQUESTS
                }
            }

# グローバルレート制限インスタンス
rate_limiter = RateLimiter()

def rate_limit_decorator(identifier_func=None):
    """レート制限デコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 識別子を取得（デフォルトはIPアドレス）
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                from flask import request
                identifier = request.remote_addr
            
            # レート制限チェック
            allowed, message = rate_limiter.is_allowed(identifier)
            if not allowed:
                from flask import jsonify
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': message
                    }
                }), 429
            
            # リクエストを記録
            rate_limiter.record_request(identifier)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # リクエスト完了を記録
                rate_limiter.release_request(identifier)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

