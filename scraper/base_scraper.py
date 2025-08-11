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
            
            # 自動ログインが有効な場合は実行
            if Config.AUTO_LOGIN_ENABLED and Config.X_USERNAME and Config.X_PASSWORD:
                app_logger.info("Attempting automatic login")
                if self._perform_automatic_login():
                    self.is_logged_in = True
                    auth_manager.update_session_validity()
                    # 新しいCookieを保存
                    self.save_current_cookies()
                    app_logger.info("Automatic login successful")
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
    
    def _perform_automatic_login(self):
        """自動ログインを実行"""
        try:
            app_logger.info("Starting automatic login process")
            
            # ログインページに移動
            self.page.get(Config.X_LOGIN_URL)
            self.wait_for_page_load()
            time.sleep(3)
            
            # ログインフォームの検出と入力
            for attempt in range(Config.LOGIN_RETRY_COUNT):
                try:
                    app_logger.info(f"Login attempt {attempt + 1}/{Config.LOGIN_RETRY_COUNT}")
                    
                    # ユーザー名/メール入力フィールドを検索
                    username_selectors = [
                        'input[name="text"]',
                        'input[autocomplete="username"]',
                        'input[data-testid="ocfEnterTextTextInput"]',
                        'input[placeholder*="phone" i]',
                        'input[placeholder*="email" i]',
                        'input[placeholder*="username" i]'
                    ]
                    
                    username_field = None
                    for selector in username_selectors:
                        try:
                            field = self.page.ele(selector, timeout=5)
                            if field and field.is_enabled():
                                username_field = field
                                break
                        except:
                            continue
                    
                    if not username_field:
                        app_logger.error("Username field not found")
                        time.sleep(5)
                        continue
                    
                    # ユーザー名またはメールアドレスを入力
                    login_identifier = Config.X_EMAIL if Config.X_EMAIL else Config.X_USERNAME
                    username_field.clear()
                    username_field.input(login_identifier)
                    app_logger.info(f"Entered username/email: {login_identifier[:3]}***")
                    
                    time.sleep(2)
                    
                    # 次へボタンをクリック
                    next_button_selectors = [
                        'div[role="button"]:has-text("Next")',
                        'div[role="button"]:has-text("次へ")',
                        'button:has-text("Next")',
                        'button:has-text("次へ")',
                        '[data-testid="ocfEnterTextNextButton"]'
                    ]
                    
                    next_button = None
                    for selector in next_button_selectors:
                        try:
                            button = self.page.ele(selector, timeout=3)
                            if button and button.is_enabled():
                                next_button = button
                                break
                        except:
                            continue
                    
                    if next_button:
                        next_button.click()
                        time.sleep(3)
                    
                    # パスワード入力フィールドを検索
                    password_selectors = [
                        'input[name="password"]',
                        'input[type="password"]',
                        'input[autocomplete="current-password"]',
                        'input[data-testid="ocfEnterTextTextInput"]'
                    ]
                    
                    password_field = None
                    for selector in password_selectors:
                        try:
                            field = self.page.ele(selector, timeout=10)
                            if field and field.is_enabled():
                                password_field = field
                                break
                        except:
                            continue
                    
                    if not password_field:
                        app_logger.error("Password field not found")
                        time.sleep(5)
                        continue
                    
                    # パスワードを入力
                    password_field.clear()
                    password_field.input(Config.X_PASSWORD)
                    app_logger.info("Password entered")
                    
                    time.sleep(2)
                    
                    # ログインボタンをクリック
                    login_button_selectors = [
                        'div[role="button"]:has-text("Log in")',
                        'div[role="button"]:has-text("ログイン")',
                        'button:has-text("Log in")',
                        'button:has-text("ログイン")',
                        '[data-testid="LoginForm_Login_Button"]'
                    ]
                    
                    login_button = None
                    for selector in login_button_selectors:
                        try:
                            button = self.page.ele(selector, timeout=3)
                            if button and button.is_enabled():
                                login_button = button
                                break
                        except:
                            continue
                    
                    if not login_button:
                        app_logger.error("Login button not found")
                        time.sleep(5)
                        continue
                    
                    login_button.click()
                    app_logger.info("Login button clicked")
                    
                    # ログイン完了を待機
                    time.sleep(10)
                    
                    # 2FA認証やその他の認証ステップをチェック
                    if self._handle_additional_auth_steps():
                        time.sleep(5)
                    
                    # ログイン成功を確認
                    if self._check_login_status():
                        app_logger.info("Automatic login successful")
                        return True
                    
                    app_logger.warning(f"Login attempt {attempt + 1} failed, retrying...")
                    time.sleep(5)
                    
                except Exception as e:
                    app_logger.error(f"Login attempt {attempt + 1} error: {e}")
                    time.sleep(5)
                    continue
            
            app_logger.error("All automatic login attempts failed")
            return False
            
        except Exception as e:
            app_logger.error(f"Automatic login failed: {e}")
            return False
    
    def _handle_additional_auth_steps(self):
        """追加の認証ステップを処理"""
        try:
            # 2FA認証の検出
            auth_code_selectors = [
                'input[name="verfication_code"]',
                'input[placeholder*="code" i]',
                'input[data-testid="ocfEnterTextTextInput"]'
            ]
            
            for selector in auth_code_selectors:
                try:
                    field = self.page.ele(selector, timeout=3)
                    if field:
                        app_logger.warning("2FA authentication detected - manual intervention required")
                        # 2FA認証は手動で処理する必要がある
                        return True
                except:
                    continue
            
            # 電話番号確認の検出
            phone_selectors = [
                'input[name="phone_number"]',
                'input[placeholder*="phone" i]'
            ]
            
            for selector in phone_selectors:
                try:
                    field = self.page.ele(selector, timeout=3)
                    if field:
                        app_logger.warning("Phone verification detected - manual intervention required")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            app_logger.error(f"Error handling additional auth steps: {e}")
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

