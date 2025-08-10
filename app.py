import os
import sys
import uuid
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from utils import (
    app_logger, log_request, log_error, log_metrics,
    rate_limiter, rate_limit_decorator,
    auth_manager, api_key_manager, require_api_key
)
from scraper import (
    FollowChecker, LikeChecker, RepostChecker, CommentChecker,
    ScrapingError, LoginRequiredError, ElementNotFoundError, RateLimitError
)

# Flaskアプリケーションの作成
app = Flask(__name__)
app.config.from_object(Config)

# CORSの設定
CORS(app, origins="*")

# グローバル変数
active_scrapers = {}

def get_client_identifier():
    """クライアント識別子を取得"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        return f"api_key:{api_key}"
    return request.remote_addr

def create_response(success=True, action=None, result=None, details=None, error=None):
    """標準レスポンス形式を作成"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if action:
        response['action'] = action
    if result is not None:
        response['result'] = result
    if details:
        response['details'] = details
    if error:
        response['error'] = error
    
    return response

def handle_scraping_error(e, request_id, action):
    """スクレイピングエラーのハンドリング"""
    log_error(app_logger, request_id, e, action)
    
    if isinstance(e, LoginRequiredError):
        return create_response(
            success=False,
            action=action,
            error={
                'code': 'LOGIN_REQUIRED',
                'message': 'X.com login is required. Please update cookies.',
                'retry_after': 300
            }
        ), 401
    
    elif isinstance(e, ElementNotFoundError):
        return create_response(
            success=False,
            action=action,
            error={
                'code': 'ELEMENT_NOT_FOUND',
                'message': str(e),
                'retry_after': 60
            }
        ), 404
    
    elif isinstance(e, RateLimitError):
        return create_response(
            success=False,
            action=action,
            error={
                'code': 'RATE_LIMITED',
                'message': str(e),
                'retry_after': 300
            }
        ), 429
    
    else:
        return create_response(
            success=False,
            action=action,
            error={
                'code': 'SCRAPING_ERROR',
                'message': str(e),
                'retry_after': 60
            }
        ), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェックエンドポイント"""
    try:
        stats = rate_limiter.get_stats('health_check')
        
        return jsonify(create_response(
            success=True,
            result={
                'status': 'healthy',
                'version': '1.0.0',
                'rate_limit_stats': stats
            },
            details='API is running normally'
        ))
    
    except Exception as e:
        app_logger.error(f"Health check failed: {e}")
        return jsonify(create_response(
            success=False,
            error={
                'code': 'HEALTH_CHECK_FAILED',
                'message': str(e)
            }
        )), 500

@app.route('/api/check/follow', methods=['POST'])
@require_api_key
@rate_limit_decorator(get_client_identifier)
def check_follow():
    """フォロー確認エンドポイント"""
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(
                success=False,
                action='follow',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'JSON data is required'
                }
            )), 400
        
        target_user = data.get('target_user')
        if not target_user:
            return jsonify(create_response(
                success=False,
                action='follow',
                error={
                    'code': 'MISSING_PARAMETER',
                    'message': 'target_user is required'
                }
            )), 400
        
        # フォロー確認を実行
        with FollowChecker() as checker:
            result = checker.check_follow_status(target_user)
        
        log_request(app_logger, request_id, 'follow', target_user, start_time)
        
        return jsonify(create_response(
            success=True,
            action='follow',
            result=result,
            details=f"Follow status checked for {target_user}"
        ))
    
    except ScrapingError as e:
        return handle_scraping_error(e, request_id, 'follow')
    
    except Exception as e:
        log_error(app_logger, request_id, e, 'follow')
        return jsonify(create_response(
            success=False,
            action='follow',
            error={
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        )), 500

@app.route('/api/check/like', methods=['POST'])
@require_api_key
@rate_limit_decorator(get_client_identifier)
def check_like():
    """いいね確認エンドポイント"""
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(
                success=False,
                action='like',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'JSON data is required'
                }
            )), 400
        
        tweet_url = data.get('tweet_url')
        if not tweet_url:
            return jsonify(create_response(
                success=False,
                action='like',
                error={
                    'code': 'MISSING_PARAMETER',
                    'message': 'tweet_url is required'
                }
            )), 400
        
        # いいね確認を実行
        with LikeChecker() as checker:
            result = checker.check_like_status(tweet_url)
        
        log_request(app_logger, request_id, 'like', tweet_url, start_time)
        
        return jsonify(create_response(
            success=True,
            action='like',
            result=result,
            details=f"Like status checked for tweet"
        ))
    
    except ScrapingError as e:
        return handle_scraping_error(e, request_id, 'like')
    
    except Exception as e:
        log_error(app_logger, request_id, e, 'like')
        return jsonify(create_response(
            success=False,
            action='like',
            error={
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        )), 500

@app.route('/api/check/repost', methods=['POST'])
@require_api_key
@rate_limit_decorator(get_client_identifier)
def check_repost():
    """リポスト確認エンドポイント"""
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(
                success=False,
                action='repost',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'JSON data is required'
                }
            )), 400
        
        tweet_url = data.get('tweet_url')
        if not tweet_url:
            return jsonify(create_response(
                success=False,
                action='repost',
                error={
                    'code': 'MISSING_PARAMETER',
                    'message': 'tweet_url is required'
                }
            )), 400
        
        # リポスト確認を実行
        with RepostChecker() as checker:
            result = checker.check_repost_status(tweet_url)
        
        log_request(app_logger, request_id, 'repost', tweet_url, start_time)
        
        return jsonify(create_response(
            success=True,
            action='repost',
            result=result,
            details=f"Repost status checked for tweet"
        ))
    
    except ScrapingError as e:
        return handle_scraping_error(e, request_id, 'repost')
    
    except Exception as e:
        log_error(app_logger, request_id, e, 'repost')
        return jsonify(create_response(
            success=False,
            action='repost',
            error={
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        )), 500

@app.route('/api/check/comment', methods=['POST'])
@require_api_key
@rate_limit_decorator(get_client_identifier)
def check_comment():
    """コメント確認エンドポイント"""
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify(create_response(
                success=False,
                action='comment',
                error={
                    'code': 'INVALID_REQUEST',
                    'message': 'JSON data is required'
                }
            )), 400
        
        tweet_url = data.get('tweet_url')
        checking_user = data.get('checking_user')
        
        if not tweet_url or not checking_user:
            return jsonify(create_response(
                success=False,
                action='comment',
                error={
                    'code': 'MISSING_PARAMETER',
                    'message': 'tweet_url and checking_user are required'
                }
            )), 400
        
        # コメント確認を実行
        with CommentChecker() as checker:
            result = checker.check_comment_status(tweet_url, checking_user)
        
        log_request(app_logger, request_id, 'comment', f"{tweet_url}:{checking_user}", start_time)
        
        return jsonify(create_response(
            success=True,
            action='comment',
            result=result,
            details=f"Comment status checked for {checking_user}"
        ))
    
    except ScrapingError as e:
        return handle_scraping_error(e, request_id, 'comment')
    
    except Exception as e:
        log_error(app_logger, request_id, e, 'comment')
        return jsonify(create_response(
            success=False,
            action='comment',
            error={
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }
        )), 500

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    """統計情報取得エンドポイント"""
    try:
        client_id = get_client_identifier()
        stats = rate_limiter.get_stats(client_id)
        
        return jsonify(create_response(
            success=True,
            result=stats,
            details='Statistics retrieved successfully'
        ))
    
    except Exception as e:
        app_logger.error(f"Stats retrieval failed: {e}")
        return jsonify(create_response(
            success=False,
            error={
                'code': 'STATS_ERROR',
                'message': str(e)
            }
        )), 500

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラー"""
    return jsonify(create_response(
        success=False,
        error={
            'code': 'NOT_FOUND',
            'message': 'Endpoint not found'
        }
    )), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """405エラーハンドラー"""
    return jsonify(create_response(
        success=False,
        error={
            'code': 'METHOD_NOT_ALLOWED',
            'message': 'Method not allowed'
        }
    )), 405

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    app_logger.error(f"Internal server error: {error}")
    return jsonify(create_response(
        success=False,
        error={
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'Internal server error occurred'
        }
    )), 500

if __name__ == '__main__':
    # 開発環境での実行
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )

