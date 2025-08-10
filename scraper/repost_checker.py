import time
import re
from scraper.base_scraper import BaseScraper, ScrapingError, ElementNotFoundError
from utils.logger import app_logger
from config.config import Config

class RepostChecker(BaseScraper):
    """リポスト確認クラス"""
    
    def check_repost_status(self, tweet_url):
        """リポスト状態をチェック"""
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
            
            # リポスト状態を確認
            repost_status = self._check_repost_button_status()
            
            app_logger.info(f"Repost check completed for tweet: {repost_status}")
            
            return {
                'is_reposted': repost_status['is_reposted'],
                'repost_count': repost_status['repost_count'],
                'button_state': repost_status['button_state']
            }
            
        except Exception as e:
            app_logger.error(f"Repost check failed for {tweet_url}: {e}")
            raise ScrapingError(f"Repost check failed: {e}")
    
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
    
    def _check_repost_button_status(self):
        """リポストボタンの状態をチェック"""
        try:
            # リポストボタンの候補セレクタ
            repost_button_selectors = [
                '[data-testid="retweet"]',
                '[data-testid="unretweet"]',
                '[aria-label*="Repost"]',
                '[aria-label*="Reposted"]',
                '[aria-label*="Retweet"]',
                '[aria-label*="Retweeted"]',
                '[aria-label*="リポスト"]',
                'div[role="button"][aria-label*="retweet" i]',
                'button[aria-label*="retweet" i]'
            ]
            
            repost_button = None
            
            # リポストボタンを検索
            for selector in repost_button_selectors:
                try:
                    element = self.page.ele(selector, timeout=3)
                    if element:
                        repost_button = element
                        break
                except:
                    continue
            
            if not repost_button:
                # ツイートが存在しない可能性をチェック
                if self._is_tweet_not_found():
                    raise ElementNotFoundError("Tweet not found or deleted")
                
                raise ElementNotFoundError("Repost button not found")
            
            # リポスト状態を判定
            is_reposted = self._determine_repost_status(repost_button)
            
            # リポスト数を取得
            repost_count = self._get_repost_count(repost_button)
            
            return {
                'is_reposted': is_reposted,
                'repost_count': repost_count,
                'button_state': 'reposted' if is_reposted else 'not_reposted'
            }
            
        except Exception as e:
            app_logger.error(f"Failed to check repost button status: {e}")
            raise
    
    def _determine_repost_status(self, repost_button):
        """リポストボタンの状態からリポスト状態を判定"""
        try:
            # data-testid属性での判定
            testid = repost_button.attr('data-testid')
            if testid:
                if testid == 'unretweet':
                    return True
                elif testid == 'retweet':
                    return False
            
            # aria-pressed属性での判定
            aria_pressed = repost_button.attr('aria-pressed')
            if aria_pressed:
                return aria_pressed.lower() == 'true'
            
            # aria-label属性での判定
            aria_label = repost_button.attr('aria-label')
            if aria_label:
                aria_label_lower = aria_label.lower()
                if ('reposted' in aria_label_lower or 
                    'retweeted' in aria_label_lower or 
                    'リポストしました' in aria_label_lower):
                    return True
                elif ('repost' in aria_label_lower or 
                      'retweet' in aria_label_lower or 
                      'リポスト' in aria_label_lower):
                    return False
            
            # SVGアイコンの色での判定
            svg_element = repost_button.ele('svg', timeout=1)
            if svg_element:
                # リポスト済みの場合、通常緑色のアイコン
                fill_color = svg_element.attr('fill')
                if fill_color and ('green' in fill_color.lower() or '#00ba7c' in fill_color.lower()):
                    return True
                
                # パスの色をチェック
                path_elements = svg_element.eles('path')
                for path in path_elements:
                    fill = path.attr('fill')
                    if fill and ('green' in fill.lower() or '#00ba7c' in fill.lower()):
                        return True
                    
                    # strokeの色もチェック
                    stroke = path.attr('stroke')
                    if stroke and ('green' in stroke.lower() or '#00ba7c' in stroke.lower()):
                        return True
            
            # CSSクラスでの判定
            class_names = repost_button.attr('class') or ''
            if 'reposted' in class_names.lower() or 'retweeted' in class_names.lower():
                return True
            
            # デフォルトは未リポスト状態
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to determine repost status: {e}")
            return False
    
    def _get_repost_count(self, repost_button):
        """リポスト数を取得"""
        try:
            # リポスト数の候補セレクタ
            count_selectors = [
                'span[data-testid="app-text-transition-container"]',
                'span.css-901oao',
                'span[dir="ltr"]'
            ]
            
            # ボタンの親要素からリポスト数を検索
            parent_element = repost_button.parent()
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
            
            # ボタン内のテキストからリポスト数を取得
            button_text = repost_button.text.strip()
            if button_text and button_text.isdigit():
                return int(button_text)
            elif button_text:
                return self._parse_count_text(button_text)
            
            return 0
            
        except Exception as e:
            app_logger.error(f"Failed to get repost count: {e}")
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
    
    def check_quote_repost_status(self, tweet_url):
        """引用リポスト状態をチェック（オプション機能）"""
        try:
            if not self.is_logged_in:
                if not self.login_to_x():
                    raise ScrapingError("Login required but failed")
            
            normalized_url = self._normalize_tweet_url(tweet_url)
            if not normalized_url:
                raise ScrapingError(f"Invalid tweet URL: {tweet_url}")
            
            if not self.navigate_to_url(normalized_url):
                raise ScrapingError(f"Failed to navigate to tweet: {normalized_url}")
            
            self.wait_for_page_load()
            self.random_delay(2, 4)
            
            # 引用リポストボタンを検索
            quote_button_selectors = [
                '[data-testid="quoteTweet"]',
                '[aria-label*="Quote"]',
                '[aria-label*="引用"]'
            ]
            
            for selector in quote_button_selectors:
                try:
                    element = self.page.ele(selector, timeout=3)
                    if element:
                        # 引用リポスト数を取得
                        quote_count = self._get_repost_count(element)
                        return {
                            'has_quote_reposts': quote_count > 0,
                            'quote_count': quote_count
                        }
                except:
                    continue
            
            return {
                'has_quote_reposts': False,
                'quote_count': 0
            }
            
        except Exception as e:
            app_logger.error(f"Quote repost check failed: {e}")
            return {
                'has_quote_reposts': False,
                'quote_count': 0
            }

