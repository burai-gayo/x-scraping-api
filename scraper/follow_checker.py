import time
from scraper.base_scraper import BaseScraper, ScrapingError, ElementNotFoundError
from utils.logger import app_logger
from config.config import Config

class FollowChecker(BaseScraper):
    """フォロー確認クラス"""
    
    def check_follow_status(self, target_username):
        """フォロー状態をチェック"""
        try:
            if not self.is_logged_in:
                if not self.login_to_x():
                    raise ScrapingError("Login required but failed")
            
            # ユーザー名の正規化
            if target_username.startswith('@'):
                target_username = target_username[1:]
            
            # プロフィールページのURL構築
            profile_url = f"{Config.X_BASE_URL}/{target_username}"
            
            # プロフィールページに移動
            if not self.navigate_to_url(profile_url):
                raise ScrapingError(f"Failed to navigate to profile: {profile_url}")
            
            # ページ読み込み完了を待機
            self.wait_for_page_load()
            self.random_delay(2, 4)
            
            # フォロー状態を確認
            follow_status = self._check_follow_button_status()
            
            app_logger.info(f"Follow check completed for @{target_username}: {follow_status}")
            
            return {
                'is_following': follow_status['is_following'],
                'button_text': follow_status['button_text'],
                'button_state': follow_status['button_state']
            }
            
        except Exception as e:
            app_logger.error(f"Follow check failed for @{target_username}: {e}")
            raise ScrapingError(f"Follow check failed: {e}")
    
    def _check_follow_button_status(self):
        """フォローボタンの状態をチェック"""
        try:
            # フォローボタンの候補セレクタ
            follow_button_selectors = [
                '[data-testid="follow"]',
                '[data-testid="unfollow"]',
                '[aria-label*="Follow"]',
                '[aria-label*="Following"]',
                '[aria-label*="Unfollow"]',
                'div[role="button"]:has-text("Follow")',
                'div[role="button"]:has-text("Following")',
                'div[role="button"]:has-text("フォロー")',
                'div[role="button"]:has-text("フォロー中")'
            ]
            
            button_element = None
            button_text = ""
            
            # ボタン要素を検索
            for selector in follow_button_selectors:
                try:
                    element = self.page.ele(selector, timeout=3)
                    if element:
                        button_element = element
                        button_text = element.text.strip()
                        break
                except:
                    continue
            
            if not button_element:
                # プロフィールが存在しない可能性をチェック
                if self._is_profile_not_found():
                    raise ElementNotFoundError("Profile not found or private")
                
                # 自分自身のプロフィールかチェック
                if self._is_own_profile():
                    return {
                        'is_following': None,
                        'button_text': 'Own Profile',
                        'button_state': 'own_profile'
                    }
                
                raise ElementNotFoundError("Follow button not found")
            
            # ボタンの状態を判定
            is_following = self._determine_follow_status(button_element, button_text)
            
            return {
                'is_following': is_following,
                'button_text': button_text,
                'button_state': 'following' if is_following else 'not_following'
            }
            
        except Exception as e:
            app_logger.error(f"Failed to check follow button status: {e}")
            raise
    
    def _determine_follow_status(self, button_element, button_text):
        """ボタンの状態からフォロー状態を判定"""
        try:
            # テキストベースの判定
            following_indicators = [
                'Following', 'フォロー中', 'Unfollow', 'フォロー解除'
            ]
            
            not_following_indicators = [
                'Follow', 'フォロー', 'Follow Back', 'フォローバック'
            ]
            
            button_text_lower = button_text.lower()
            
            for indicator in following_indicators:
                if indicator.lower() in button_text_lower:
                    return True
            
            for indicator in not_following_indicators:
                if indicator.lower() in button_text_lower:
                    return False
            
            # data-testid属性での判定
            testid = button_element.attr('data-testid')
            if testid:
                if testid == 'unfollow':
                    return True
                elif testid == 'follow':
                    return False
            
            # aria-label属性での判定
            aria_label = button_element.attr('aria-label')
            if aria_label:
                aria_label_lower = aria_label.lower()
                if 'unfollow' in aria_label_lower or 'following' in aria_label_lower:
                    return True
                elif 'follow' in aria_label_lower:
                    return False
            
            # CSSクラスでの判定
            class_names = button_element.attr('class') or ''
            if 'following' in class_names.lower():
                return True
            
            # デフォルトは未フォロー状態
            app_logger.warning(f"Could not determine follow status from button: {button_text}")
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to determine follow status: {e}")
            return False
    
    def _is_profile_not_found(self):
        """プロフィールが見つからないかチェック"""
        try:
            not_found_indicators = [
                'This account doesn\'t exist',
                'アカウントが存在しません',
                'Something went wrong',
                'Try again'
            ]
            
            page_text = self.page.html
            for indicator in not_found_indicators:
                if indicator in page_text:
                    return True
            
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to check if profile not found: {e}")
            return False
    
    def _is_own_profile(self):
        """自分自身のプロフィールかチェック"""
        try:
            # "Edit profile" ボタンの存在をチェック
            edit_profile_selectors = [
                '[data-testid="editProfileButton"]',
                'a[href="/settings/profile"]',
                ':has-text("Edit profile")',
                ':has-text("プロフィールを編集")'
            ]
            
            for selector in edit_profile_selectors:
                if self.page.ele(selector, timeout=2):
                    return True
            
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to check if own profile: {e}")
            return False
    
    def get_profile_info(self, target_username):
        """プロフィール情報を取得（オプション機能）"""
        try:
            if target_username.startswith('@'):
                target_username = target_username[1:]
            
            profile_url = f"{Config.X_BASE_URL}/{target_username}"
            
            if not self.navigate_to_url(profile_url):
                return None
            
            self.wait_for_page_load()
            
            # プロフィール情報を取得
            profile_info = {}
            
            # 表示名
            display_name_element = self.page.ele('[data-testid="UserName"]', timeout=3)
            if display_name_element:
                profile_info['display_name'] = display_name_element.text.strip()
            
            # フォロワー数
            followers_element = self.page.ele('a[href$="/followers"] span', timeout=3)
            if followers_element:
                profile_info['followers_count'] = followers_element.text.strip()
            
            # フォロー数
            following_element = self.page.ele('a[href$="/following"] span', timeout=3)
            if following_element:
                profile_info['following_count'] = following_element.text.strip()
            
            # プロフィール画像
            avatar_element = self.page.ele('[data-testid="UserAvatar-Container-unknown"] img', timeout=3)
            if avatar_element:
                profile_info['avatar_url'] = avatar_element.attr('src')
            
            return profile_info
            
        except Exception as e:
            app_logger.error(f"Failed to get profile info for @{target_username}: {e}")
            return None

