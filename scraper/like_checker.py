import time
import re
from scraper.base_scraper import BaseScraper, ScrapingError, ElementNotFoundError
from utils.logger import app_logger
from config.config import Config

class LikeChecker(BaseScraper):
    """いいね確認クラス"""
    
    def check_like_status(self, tweet_url):
        """いいね状態をチェック"""
        try:
            if not self.is_logged_in:
                if not self.login_to_x():
                    raise ScrapingError("Login required but failed")
            
            # ツイートURLの正規化
            normalized_url = self._normalize_tweet_url(tweet_url)
            if not normalized_url:
                raise ScrapingError(f"Invalid tweet URL: {tweet_url}")
            
            # ツイートページに移動
            if not self.navigate_to_url(normalized_url):
                raise ScrapingError(f"Failed to navigate to tweet: {normalized_url}")
            
            # ページ読み込み完了を待機
            self.wait_for_page_load()
            self.random_delay(2, 4)
            
            # いいね状態を確認
            like_status = self._check_like_button_status()
            
            app_logger.info(f"Like check completed for tweet: {like_status}")
            
            return {
                'is_liked': like_status['is_liked'],
                'like_count': like_status['like_count'],
                'button_state': like_status['button_state']
            }
            
        except Exception as e:
            app_logger.error(f"Like check failed for {tweet_url}: {e}")
            raise ScrapingError(f"Like check failed: {e}")
    
    def _normalize_tweet_url(self, tweet_url):
        """ツイートURLを正規化"""
        try:
            # URLパターンのマッチング
            patterns = [
                r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)',
                r'https?://(?:www\.)?(?:twitter\.com|x\.com)/i/web/status/(\d+)',
                r'(\d{15,20})'  # ツイートIDのみ
            ]
            
            for pattern in patterns:
                match = re.search(pattern, tweet_url)
                if match:
                    tweet_id = match.group(1)
                    return f"{Config.X_BASE_URL}/i/web/status/{tweet_id}"
            
            return None
            
        except Exception as e:
            app_logger.error(f"Failed to normalize tweet URL: {e}")
            return None
    
    def _check_like_button_status(self):
        """いいねボタンの状態をチェック"""
        try:
            # いいねボタンの候補セレクタ
            like_button_selectors = [
                '[data-testid="like"]',
                '[data-testid="unlike"]',
                '[aria-label*="Like"]',
                '[aria-label*="Liked"]',
                '[aria-label*="いいね"]',
                'div[role="button"][aria-label*="like" i]',
                'button[aria-label*="like" i]'
            ]
            
            like_button = None
            
            # いいねボタンを検索
            for selector in like_button_selectors:
                try:
                    element = self.page.ele(selector, timeout=3)
                    if element:
                        like_button = element
                        break
                except:
                    continue
            
            if not like_button:
                # ツイートが存在しない可能性をチェック
                if self._is_tweet_not_found():
                    raise ElementNotFoundError("Tweet not found or deleted")
                
                raise ElementNotFoundError("Like button not found")
            
            # いいね状態を判定
            is_liked = self._determine_like_status(like_button)
            
            # いいね数を取得
            like_count = self._get_like_count(like_button)
            
            return {
                'is_liked': is_liked,
                'like_count': like_count,
                'button_state': 'liked' if is_liked else 'not_liked'
            }
            
        except Exception as e:
            app_logger.error(f"Failed to check like button status: {e}")
            raise
    
    def _determine_like_status(self, like_button):
        """いいねボタンの状態からいいね状態を判定"""
        try:
            # data-testid属性での判定
            testid = like_button.attr('data-testid')
            if testid:
                if testid == 'unlike':
                    return True
                elif testid == 'like':
                    return False
            
            # aria-pressed属性での判定
            aria_pressed = like_button.attr('aria-pressed')
            if aria_pressed:
                return aria_pressed.lower() == 'true'
            
            # aria-label属性での判定
            aria_label = like_button.attr('aria-label')
            if aria_label:
                aria_label_lower = aria_label.lower()
                if 'liked' in aria_label_lower or 'いいねしました' in aria_label_lower:
                    return True
                elif 'like' in aria_label_lower or 'いいね' in aria_label_lower:
                    return False
            
            # SVGアイコンの色での判定
            svg_element = like_button.ele('svg', timeout=1)
            if svg_element:
                # いいね済みの場合、通常赤色のハートアイコン
                fill_color = svg_element.attr('fill')
                if fill_color and ('red' in fill_color.lower() or '#f91880' in fill_color.lower()):
                    return True
                
                # パスの色をチェック
                path_elements = svg_element.eles('path')
                for path in path_elements:
                    fill = path.attr('fill')
                    if fill and ('red' in fill.lower() or '#f91880' in fill.lower()):
                        return True
            
            # CSSクラスでの判定
            class_names = like_button.attr('class') or ''
            if 'liked' in class_names.lower() or 'active' in class_names.lower():
                return True
            
            # デフォルトは未いいね状態
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to determine like status: {e}")
            return False
    
    def _get_like_count(self, like_button):
        """いいね数を取得"""
        try:
            # いいね数の候補セレクタ
            count_selectors = [
                'span[data-testid="app-text-transition-container"]',
                'span.css-901oao',
                'span[dir="ltr"]'
            ]
            
            # ボタンの親要素からいいね数を検索
            parent_element = like_button.parent()
            if parent_element:
                for selector in count_selectors:
                    count_element = parent_element.ele(selector, timeout=1)
                    if count_element:
                        count_text = count_element.text.strip()
                        if count_text and count_text.isdigit():
                            return int(count_text)
                        elif count_text:
                            # "1.2K" のような表記を数値に変換
                            return self._parse_count_text(count_text)
            
            # ボタン内のテキストからいいね数を取得
            button_text = like_button.text.strip()
            if button_text and button_text.isdigit():
                return int(button_text)
            elif button_text:
                return self._parse_count_text(button_text)
            
            return 0
            
        except Exception as e:
            app_logger.error(f"Failed to get like count: {e}")
            return 0
    
    def _parse_count_text(self, count_text):
        """カウントテキストを数値に変換"""
        try:
            count_text = count_text.replace(',', '').strip()
            
            if count_text.endswith('K'):
                return int(float(count_text[:-1]) * 1000)
            elif count_text.endswith('M'):
                return int(float(count_text[:-1]) * 1000000)
            elif count_text.isdigit():
                return int(count_text)
            
            return 0
            
        except Exception as e:
            app_logger.error(f"Failed to parse count text: {count_text}")
            return 0
    
    def _is_tweet_not_found(self):
        """ツイートが見つからないかチェック"""
        try:
            not_found_indicators = [
                'This Tweet was deleted',
                'このツイートは削除されました',
                'Tweet not available',
                'Something went wrong',
                'Try again',
                'Hmm...this page doesn\'t exist'
            ]
            
            page_text = self.page.html
            for indicator in not_found_indicators:
                if indicator in page_text:
                    return True
            
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to check if tweet not found: {e}")
            return False
    
    def get_tweet_info(self, tweet_url):
        """ツイート情報を取得（オプション機能）"""
        try:
            normalized_url = self._normalize_tweet_url(tweet_url)
            if not normalized_url:
                return None
            
            if not self.navigate_to_url(normalized_url):
                return None
            
            self.wait_for_page_load()
            
            # ツイート情報を取得
            tweet_info = {}
            
            # ツイート本文
            tweet_text_element = self.page.ele('[data-testid="tweetText"]', timeout=3)
            if tweet_text_element:
                tweet_info['text'] = tweet_text_element.text.strip()
            
            # 投稿者情報
            author_element = self.page.ele('[data-testid="User-Names"]', timeout=3)
            if author_element:
                tweet_info['author'] = author_element.text.strip()
            
            # 投稿時刻
            time_element = self.page.ele('time', timeout=3)
            if time_element:
                tweet_info['timestamp'] = time_element.attr('datetime')
            
            # リツイート数
            retweet_element = self.page.ele('[data-testid="retweet"]', timeout=3)
            if retweet_element:
                retweet_count_element = retweet_element.parent().ele('span[data-testid="app-text-transition-container"]')
                if retweet_count_element:
                    tweet_info['retweet_count'] = self._parse_count_text(retweet_count_element.text)
            
            return tweet_info
            
        except Exception as e:
            app_logger.error(f"Failed to get tweet info: {e}")
            return None

