import json
import os
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from config.config import Config
from utils.logger import app_logger

class AuthManager:
    """X.com認証管理クラス"""
    
    def __init__(self):
        self.cookie_file = Config.COOKIE_FILE_PATH
        self.encryption_key = self._get_or_create_key()
        self.cipher = Fernet(self.encryption_key)
        self.session_valid_until = None
    
    def _get_or_create_key(self):
        """暗号化キーを取得または作成"""
        key_file = os.path.join(os.path.dirname(self.cookie_file), 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
    
    def save_cookies(self, cookies):
        """Cookieを暗号化して保存"""
        try:
            cookie_data = {
                'cookies': cookies,
                'timestamp': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            # JSON文字列に変換
            json_data = json.dumps(cookie_data)
            
            # 暗号化
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            # ファイルに保存
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            with open(self.cookie_file, 'wb') as f:
                f.write(encrypted_data)
            
            # ファイル権限を制限
            os.chmod(self.cookie_file, 0o600)
            
            app_logger.info("Cookies saved successfully")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to save cookies: {e}")
            return False
    
    def load_cookies(self):
        """暗号化されたCookieを読み込み"""
        try:
            if not os.path.exists(self.cookie_file):
                app_logger.warning("Cookie file not found")
                return None
            
            # ファイルから読み込み
            with open(self.cookie_file, 'rb') as f:
                encrypted_data = f.read()
            
            # 復号化
            decrypted_data = self.cipher.decrypt(encrypted_data)
            cookie_data = json.loads(decrypted_data.decode())
            
            # 有効期限チェック
            expires_at = datetime.fromisoformat(cookie_data['expires_at'])
            if datetime.utcnow() > expires_at:
                app_logger.warning("Cookies have expired")
                return None
            
            app_logger.info("Cookies loaded successfully")
            return cookie_data['cookies']
            
        except Exception as e:
            app_logger.error(f"Failed to load cookies: {e}")
            return None
    
    def is_session_valid(self):
        """セッションの有効性をチェック"""
        try:
            # セッション有効期限ファイルをチェック
            session_file = os.path.join(os.path.dirname(self.cookie_file), 'session_validity.json')
            
            if not os.path.exists(session_file):
                return False
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            last_valid = datetime.fromisoformat(session_data.get('last_valid', '2000-01-01T00:00:00'))
            validity_hours = session_data.get('validity_hours', 24)
            
            # 有効期限をチェック（デフォルト24時間）
            if datetime.utcnow() - last_valid > timedelta(hours=validity_hours):
                app_logger.info("Session expired, automatic re-login required")
                return False
            
            # Cookieファイルの存在確認
            if not os.path.exists(self.cookie_file):
                return False
            
            # Cookieファイルの更新時間をチェック
            cookie_mtime = datetime.fromtimestamp(os.path.getmtime(self.cookie_file))
            if datetime.utcnow() - cookie_mtime > timedelta(hours=validity_hours):
                app_logger.info("Cookie file too old, re-login required")
                return False
            
            return True
            
        except Exception as e:
            app_logger.error(f"Error checking session validity: {e}")
            return False
    
    def update_session_validity(self, valid_duration_hours=24):
        """セッション有効期限を更新"""
        try:
            session_file = os.path.join(os.path.dirname(self.cookie_file), 'session_validity.json')
            
            session_data = {
                'last_valid': datetime.utcnow().isoformat(),
                'validity_hours': valid_duration_hours,
                'auto_login_enabled': getattr(Config, 'AUTO_LOGIN_ENABLED', True),
                'last_login_method': 'automatic' if getattr(Config, 'AUTO_LOGIN_ENABLED', True) else 'manual'
            }
            
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # ファイル権限を制限
            os.chmod(session_file, 0o600)
            
            # 従来の方法も維持
            self.session_valid_until = datetime.utcnow() + timedelta(hours=valid_duration_hours)
            
            app_logger.info(f"Session validity updated until {self.session_valid_until}")
            
        except Exception as e:
            app_logger.error(f"Error updating session validity: {e}")
            # フォールバック
            self.session_valid_until = datetime.utcnow() + timedelta(hours=valid_duration_hours)
    
    def invalidate_session(self):
        """セッションを無効化"""
        self.session_valid_until = None
        
        # セッション有効性ファイルも削除
        try:
            session_file = os.path.join(os.path.dirname(self.cookie_file), 'session_validity.json')
            if os.path.exists(session_file):
                os.remove(session_file)
        except Exception as e:
            app_logger.error(f"Error removing session file: {e}")
        
        app_logger.info("Session invalidated")
    
    def force_session_refresh(self):
        """セッションの強制更新"""
        try:
            session_file = os.path.join(os.path.dirname(self.cookie_file), 'session_validity.json')
            
            if os.path.exists(session_file):
                os.remove(session_file)
            
            if os.path.exists(self.cookie_file):
                os.remove(self.cookie_file)
            
            self.session_valid_until = None
            
            app_logger.info("Session forcefully refreshed - re-login required")
            
        except Exception as e:
            app_logger.error(f"Error forcing session refresh: {e}")
    
    def get_session_info(self):
        """セッション情報を取得"""
        try:
            session_file = os.path.join(os.path.dirname(self.cookie_file), 'session_validity.json')
            
            if not os.path.exists(session_file):
                return {
                    'valid': False,
                    'reason': 'No session file found'
                }
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            last_valid = datetime.fromisoformat(session_data.get('last_valid', '2000-01-01T00:00:00'))
            validity_hours = session_data.get('validity_hours', 24)
            expires_at = last_valid + timedelta(hours=validity_hours)
            
            return {
                'valid': self.is_session_valid(),
                'last_valid': session_data.get('last_valid'),
                'expires_at': expires_at.isoformat(),
                'validity_hours': validity_hours,
                'auto_login_enabled': session_data.get('auto_login_enabled', False),
                'last_login_method': session_data.get('last_login_method', 'unknown'),
                'time_remaining': str(expires_at - datetime.utcnow()) if expires_at > datetime.utcnow() else '0:00:00'
            }
            
        except Exception as e:
            app_logger.error(f"Error getting session info: {e}")
            return {
                'valid': False,
                'reason': f'Error: {str(e)}'
            }
    
    def cleanup_expired_cookies(self):
        """期限切れのCookieファイルを削除"""
        try:
            cookies = self.load_cookies()
            if cookies is None and os.path.exists(self.cookie_file):
                os.remove(self.cookie_file)
                app_logger.info("Expired cookie file removed")
        except Exception as e:
            app_logger.error(f"Failed to cleanup cookies: {e}")

class APIKeyManager:
    """APIキー管理クラス"""
    
    def __init__(self):
        self.valid_keys = self._load_api_keys()
    
    def _load_api_keys(self):
        """APIキーを読み込み"""
        # 環境変数から読み込み
        api_keys = [Config.API_KEY]
        
        # ファイルから追加のキーを読み込み（オプション）
        key_file = os.path.join(os.path.dirname(Config.COOKIE_FILE_PATH), 'api_keys.txt')
        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    additional_keys = [line.strip() for line in f if line.strip()]
                    api_keys.extend(additional_keys)
            except Exception as e:
                app_logger.error(f"Failed to load additional API keys: {e}")
        
        return set(api_keys)
    
    def is_valid_key(self, api_key):
        """APIキーの有効性をチェック"""
        return api_key in self.valid_keys
    
    def add_key(self, api_key):
        """新しいAPIキーを追加"""
        self.valid_keys.add(api_key)
    
    def remove_key(self, api_key):
        """APIキーを削除"""
        self.valid_keys.discard(api_key)

# グローバルインスタンス
auth_manager = AuthManager()
api_key_manager = APIKeyManager()

def require_api_key(func):
    """APIキー認証デコレータ"""
    def wrapper(*args, **kwargs):
        from flask import request, jsonify
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_API_KEY',
                    'message': 'API key is required'
                }
            }), 401
        
        if not api_key_manager.is_valid_key(api_key):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_API_KEY',
                    'message': 'Invalid API key'
                }
            }), 401
        
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    return wrapper

