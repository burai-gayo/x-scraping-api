import time
import random
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions
from config.config import Config
from utils.logger import app_logger
from utils.auth_manager import auth_manager

class BaseScraper:
    """ベーススクレイパークラス"""
    
    def __init__(self):
        self.page = None
        self.is_logged_in = False
        self.setup_browser()
    
    def setup_browser(self):
        """ブラウザの初期設定"""
        try:
            # Chromiumオプションの設定
            options = ChromiumOptions()
            options.headless(True)  # ヘッドレスモード
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')
            options.set_argument('--disable-gpu')
            options.set_argument('--disable-web-security')
            options.set_argument('--disable-features=VizDisplayCompositor')
            options.set_argument('--window-size=1920,1080')
            
            # User-Agentの設定
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            options.set_argument(f'--user-agent={random.choice(user_agents)}')
            
            # ページオブジェクトの作成
            self.page = ChromiumPage(addr_or_opts=options)
            self.page.set.timeouts(Config.PAGE_LOAD_TIMEOUT)
            
            app_logger.info("Browser setup completed")
            
        except Exception as e:
            app_logger.error(f"Failed to setup browser: {e}")
            raise
    
    def login_to_x(self):
        """X.comにログイン"""
        try:
            # 既存のCookieを読み込み
            cookies = auth_manager.load_cookies()
            
            if cookies and auth_manager.is_session_valid():
                # Cookieを使用してログイン状態を復元
                self.page.get(Config.X_BASE_URL)
                
                for cookie in cookies:
                    self.page.set.cookies(cookie)
                
                # ログイン状態を確認
                self.page.refresh()
                time.sleep(3)
                
                if self._check_login_status():
                    self.is_logged_in = True
                    auth_manager.update_session_validity()
                    app_logger.info("Login restored from cookies")
                    return True
            
            # 手動ログインが必要
            app_logger.warning("Manual login required - cookies not available or expired")
            return False
            
        except Exception as e:
            app_logger.error(f"Login failed: {e}")
            return False
    
    def _check_login_status(self):
        """ログイン状態をチェック"""
        try:
            # ログイン状態の確認要素をチェック
            login_indicators = [
                '[data-testid="SideNav_AccountSwitcher_Button"]',
                '[data-testid="AppTabBar_Profile_Link"]',
                '[aria-label="Profile"]'
            ]
            
            for indicator in login_indicators:
                if self.page.ele(indicator, timeout=2):
                    return True
            
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to check login status: {e}")
            return False
    
    def save_current_cookies(self):
        """現在のCookieを保存"""
        try:
            cookies = self.page.cookies()
            if cookies:
                auth_manager.save_cookies(cookies)
                app_logger.info("Cookies saved successfully")
                return True
            return False
        except Exception as e:
            app_logger.error(f"Failed to save cookies: {e}")
            return False
    
    def navigate_to_url(self, url, max_retries=3):
        """URLに移動（リトライ機能付き）"""
        for attempt in range(max_retries):
            try:
                app_logger.info(f"Navigating to: {url} (attempt {attempt + 1})")
                self.page.get(url)
                
                # ページ読み込み完了を待機
                self.wait_for_page_load()
                
                return True
                
            except Exception as e:
                app_logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(Config.RETRY_DELAY * (attempt + 1))
                else:
                    app_logger.error(f"Failed to navigate to {url} after {max_retries} attempts")
                    return False
        
        return False
    
    def wait_for_page_load(self, timeout=10):
        """ページ読み込み完了を待機"""
        try:
            # JavaScriptの実行完了を待機
            self.page.wait.load_start()
            time.sleep(2)  # 追加の待機時間
            
            # 基本的なページ要素の読み込みを確認
            self.page.wait.ele_loaded('body', timeout=timeout)
            
        except Exception as e:
            app_logger.warning(f"Page load wait timeout: {e}")
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """ランダムな遅延を追加"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def scroll_to_element(self, element):
        """要素までスクロール"""
        try:
            if element:
                element.scroll.to_see()
                time.sleep(1)
                return True
        except Exception as e:
            app_logger.warning(f"Failed to scroll to element: {e}")
        return False
    
    def take_screenshot(self, filename=None):
        """スクリーンショットを撮影"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = f"/tmp/{filename}"
            self.page.get_screenshot(path=screenshot_path)
            app_logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            app_logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def close(self):
        """ブラウザを閉じる"""
        try:
            if self.page:
                self.page.quit()
                app_logger.info("Browser closed")
        except Exception as e:
            app_logger.error(f"Failed to close browser: {e}")
    
    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        self.close()

class ScrapingError(Exception):
    """スクレイピング関連のエラー"""
    pass

class LoginRequiredError(ScrapingError):
    """ログインが必要なエラー"""
    pass

class ElementNotFoundError(ScrapingError):
    """要素が見つからないエラー"""
    pass

class RateLimitError(ScrapingError):
    """レート制限エラー"""
    pass

