import time
import re
from scraper.base_scraper import BaseScraper, ScrapingError, ElementNotFoundError
from utils.logger import app_logger
from config.config import Config

class CommentChecker(BaseScraper):
    """コメント確認クラス"""
    
    def check_comment_status(self, tweet_url, checking_username):
        """コメント状態をチェック"""
        try:
            if not self.is_logged_in:
                if not self.login_to_x():
                    raise ScrapingError("Login required but failed")
            
            # ツイートURLの正規化
            normalized_url = self._normalize_tweet_url(tweet_url)
            if not normalized_url:
                raise ScrapingError(f"Invalid tweet URL: {tweet_url}")
            
            # ユーザー名の正規化
            if checking_username.startswith('@'):
                checking_username = checking_username[1:]
            
            # ツイートページに移動
            if not self.navigate_to_url(normalized_url):
                raise ScrapingError(f"Failed to navigate to tweet: {normalized_url}")
            
            # ページ読み込み完了を待機
            self.wait_for_page_load()
            self.random_delay(2, 4)
            
            # コメント状態を確認
            comment_status = self._check_user_comments(checking_username)
            
            app_logger.info(f"Comment check completed for @{checking_username}: {comment_status}")
            
            return {
                'has_commented': comment_status['has_commented'],
                'comment_count': comment_status['comment_count'],
                'comments': comment_status['comments']
            }
            
        except Exception as e:
            app_logger.error(f"Comment check failed for {tweet_url}: {e}")
            raise ScrapingError(f"Comment check failed: {e}")
    
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
    
    def _check_user_comments(self, username):
        """指定ユーザーのコメントをチェック"""
        try:
            comments_found = []
            max_scroll_attempts = 5
            scroll_attempts = 0
            
            while scroll_attempts < max_scroll_attempts:
                # 現在表示されているコメントを取得
                current_comments = self._get_visible_comments(username)
                
                # 新しいコメントがあれば追加
                for comment in current_comments:
                    if comment not in comments_found:
                        comments_found.append(comment)
                
                # さらにコメントを読み込むためにスクロール
                if not self._scroll_to_load_more_comments():
                    break
                
                scroll_attempts += 1
                self.random_delay(2, 3)
            
            return {
                'has_commented': len(comments_found) > 0,
                'comment_count': len(comments_found),
                'comments': comments_found
            }
            
        except Exception as e:
            app_logger.error(f"Failed to check user comments: {e}")
            return {
                'has_commented': False,
                'comment_count': 0,
                'comments': []
            }
    
    def _get_visible_comments(self, username):
        """現在表示されているコメントから指定ユーザーのものを取得"""
        try:
            comments = []
            
            # コメント要素の候補セレクタ
            comment_selectors = [
                '[data-testid="tweet"]',
                'article[data-testid="tweet"]',
                'div[data-testid="tweet"]'
            ]
            
            comment_elements = []
            for selector in comment_selectors:
                try:
                    elements = self.page.eles(selector, timeout=3)
                    if elements:
                        comment_elements.extend(elements)
                        break
                except:
                    continue
            
            if not comment_elements:
                return comments
            
            # 各コメント要素をチェック
            for element in comment_elements:
                try:
                    comment_info = self._extract_comment_info(element, username)
                    if comment_info:
                        comments.append(comment_info)
                except Exception as e:
                    app_logger.debug(f"Failed to extract comment info: {e}")
                    continue
            
            return comments
            
        except Exception as e:
            app_logger.error(f"Failed to get visible comments: {e}")
            return []
    
    def _extract_comment_info(self, comment_element, target_username):
        """コメント要素から情報を抽出"""
        try:
            # ユーザー名を取得
            username_selectors = [
                '[data-testid="User-Names"] a[href*="/"]',
                'a[role="link"][href*="/"]',
                '[data-testid="User-Names"] span'
            ]
            
            comment_username = None
            for selector in username_selectors:
                try:
                    username_element = comment_element.ele(selector, timeout=1)
                    if username_element:
                        href = username_element.attr('href')
                        if href:
                            # URLからユーザー名を抽出
                            username_match = re.search(r'/([^/]+)$', href)
                            if username_match:
                                comment_username = username_match.group(1)
                                break
                        else:
                            # テキストからユーザー名を取得
                            text = username_element.text.strip()
                            if text.startswith('@'):
                                comment_username = text[1:]
                            elif text:
                                comment_username = text
                            break
                except:
                    continue
            
            # 対象ユーザーでない場合はスキップ
            if not comment_username or comment_username.lower() != target_username.lower():
                return None
            
            # コメント本文を取得
            text_selectors = [
                '[data-testid="tweetText"]',
                'div[lang]',
                'span[lang]'
            ]
            
            comment_text = ""
            for selector in text_selectors:
                try:
                    text_element = comment_element.ele(selector, timeout=1)
                    if text_element:
                        comment_text = text_element.text.strip()
                        break
                except:
                    continue
            
            # 投稿時刻を取得
            time_element = comment_element.ele('time', timeout=1)
            timestamp = None
            if time_element:
                timestamp = time_element.attr('datetime')
            
            # コメントIDを取得（重複チェック用）
            comment_id = None
            link_elements = comment_element.eles('a[href*="/status/"]')
            for link in link_elements:
                href = link.attr('href')
                if href:
                    id_match = re.search(r'/status/(\d+)', href)
                    if id_match:
                        comment_id = id_match.group(1)
                        break
            
            return {
                'username': comment_username,
                'text': comment_text,
                'timestamp': timestamp,
                'comment_id': comment_id
            }
            
        except Exception as e:
            app_logger.debug(f"Failed to extract comment info: {e}")
            return None
    
    def _scroll_to_load_more_comments(self):
        """さらにコメントを読み込むためにスクロール"""
        try:
            # 現在のページの高さを取得
            initial_height = self.page.run_js('return document.body.scrollHeight')
            
            # ページの下部にスクロール
            self.page.scroll.to_bottom()
            time.sleep(2)
            
            # 新しいコンテンツが読み込まれたかチェック
            new_height = self.page.run_js('return document.body.scrollHeight')
            
            return new_height > initial_height
            
        except Exception as e:
            app_logger.debug(f"Failed to scroll for more comments: {e}")
            return False
    
    def get_total_comment_count(self, tweet_url):
        """ツイートの総コメント数を取得"""
        try:
            normalized_url = self._normalize_tweet_url(tweet_url)
            if not normalized_url:
                return 0
            
            if not self.navigate_to_url(normalized_url):
                return 0
            
            self.wait_for_page_load()
            
            # コメント数の候補セレクタ
            comment_count_selectors = [
                '[data-testid="reply"]',
                '[aria-label*="Reply"]',
                '[aria-label*="replies"]',
                '[aria-label*="返信"]'
            ]
            
            for selector in comment_count_selectors:
                try:
                    element = self.page.ele(selector, timeout=3)
                    if element:
                        # 親要素からカウントを取得
                        parent = element.parent()
                        if parent:
                            count_element = parent.ele('span[data-testid="app-text-transition-container"]', timeout=1)
                            if count_element:
                                count_text = count_element.text.strip()
                                return self._parse_count_text(count_text)
                except:
                    continue
            
            return 0
            
        except Exception as e:
            app_logger.error(f"Failed to get total comment count: {e}")
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
    
    def check_specific_comment_exists(self, tweet_url, comment_text, username):
        """特定のコメント内容が存在するかチェック"""
        try:
            comment_status = self.check_comment_status(tweet_url, username)
            
            if not comment_status['has_commented']:
                return False
            
            # コメント内容をチェック
            for comment in comment_status['comments']:
                if comment_text.lower() in comment['text'].lower():
                    return True
            
            return False
            
        except Exception as e:
            app_logger.error(f"Failed to check specific comment: {e}")
            return False

