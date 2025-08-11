# X.com スクレイピングAPI

X APIの有料プラン制限を回避し、リポスト、いいね、コメント、フォロー状態を確認するためのPython APIサーバーです。DrissionPageライブラリを使用したスクレイピングにより、X.comから直接情報を取得します。

## 目次

1. [概要](#概要)
2. [機能](#機能)
3. [システム要件](#システム要件)
4. [インストール](#インストール)
5. [設定](#設定)
6. [使用方法](#使用方法)
7. [API仕様](#api仕様)
8. [PHP連携](#php連携)
9. [運用・監視](#運用監視)
10. [トラブルシューティング](#トラブルシューティング)
11. [セキュリティ](#セキュリティ)
12. [ライセンス](#ライセンス)

## 概要

このAPIサーバーは、X.com（旧Twitter）のソーシャルアクション（フォロー、いいね、リポスト、コメント）の確認を自動化するためのソリューションです。X APIの制限や料金を回避し、既存のPHPアプリケーションと連携して動作します。

### 主な特徴

- **X APIの制限回避**: 有料プランを使用せずにソーシャルアクション確認が可能
- **高い精度**: DrissionPageによる実ブラウザベースのスクレイピング
- **RESTful API**: 標準的なHTTP APIとして提供
- **レート制限**: 適切な制限により安定した動作を保証
- **セキュリティ**: APIキー認証、Cookie暗号化、ログマスキング
- **監視機能**: 詳細なログ出力と統計情報の提供
- **PHP連携**: 既存のPHPアプリケーションとの簡単な統合

## 機能

### 対応アクション

1. **フォロー確認** (`/api/check/follow`)
   - 指定ユーザーをフォローしているかの判定
   - プロフィール情報の取得（オプション）
   - 自分自身のプロフィール検出

2. **いいね確認** (`/api/check/like`)
   - 指定ツイートにいいねしているかの判定
   - いいね数の取得
   - ツイート情報の取得（オプション）

3. **リポスト確認** (`/api/check/repost`)
   - 指定ツイートをリポストしているかの判定
   - リポスト数の取得
   - 引用リポストの確認（オプション）

4. **コメント確認** (`/api/check/comment`)
   - 指定ツイートにコメントしているかの判定
   - コメント内容の検索（オプション）

### 認証・セキュリティ機能

1. **自動ログイン機能**
   - 環境変数に設定したユーザー名・パスワードによる自動ログイン
   - クッキー有効期限切れ時の自動再ログイン
   - 2FA認証の検出と手動介入の通知
   - ログイン失敗時のリトライ機能

2. **セッション管理**
   - 24時間有効期限での自動セッション管理
   - セッション状態の確認API (`/api/session/info`)
   - セッション強制更新API (`/api/session/refresh`)
   - セッション有効性の自動チェック

3. **セキュリティ機能**
   - APIキー認証による安全なアクセス制御
   - Fernet暗号化によるCookie保護
   - ログ内の個人情報自動マスキング
   - ファイル権限の適切な設定

### API機能

1. **RESTful API**
   - 標準的なHTTP APIインターフェース
   - JSON形式でのリクエスト・レスポンス
   - 詳細なエラーコードとメッセージ

2. **レート制限**
   - 分単位・時間単位でのリクエスト制限
   - クライアント別の制限管理
   - 制限超過時の適切なエラーレスポンス
3. **監視・統計**
   - 詳細なログ出力とローテーション
   - API使用統計の取得 (`/api/stats`)
   - ヘルスチェック機能 (`/api/health`)

## システム要件

- **ヘルスチェック** (`/api/health`): サーバー状態の確認
- **統計情報** (`/api/stats`): レート制限状況の確認
- **自動ログイン**: Cookie管理による認証状態の維持
- **エラーハンドリング**: 詳細なエラー情報とリトライ指示

## システム要件

### 必須要件

- **OS**: Ubuntu 20.04+ / CentOS 8+ / Amazon Linux 2+
- **Python**: 3.9以上
- **メモリ**: 最低2GB、推奨4GB以上
- **ディスク**: 最低5GB、推奨10GB以上
- **ネットワーク**: X.comへのHTTPS接続が可能

### 推奨要件

- **CPU**: 2コア以上
- **メモリ**: 8GB以上
- **SSD**: 高速ディスクアクセス
- **Redis**: レート制限の高速化（オプション）

### ブラウザ要件

DrissionPageが使用するChromiumブラウザが動作する環境が必要です。ヘッドレスモードで動作するため、GUI環境は不要です。

## インストール

### 1. システムの準備

```bash
# システムパッケージの更新
sudo apt update && sudo apt upgrade -y

# 必要なシステムパッケージのインストール
sudo apt install -y python3.9 python3.9-pip python3.9-venv git curl wget

# Chromiumブラウザの依存関係をインストール
sudo apt install -y chromium-browser chromium-chromedriver
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

### 2. プロジェクトのダウンロード

```bash
# プロジェクトディレクトリの作成
sudo mkdir -p /opt/x_scraping_api
sudo chown $USER:$USER /opt/x_scraping_api
cd /opt/x_scraping_api

# ファイルのコピー（提供されたファイルを配置）
# または、Gitリポジトリからクローン
# git clone https://github.com/your-repo/x_scraping_api.git .
```

### 3. Python仮想環境の作成

```bash
# 仮想環境の作成
python3.9 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip
```

### 4. 依存関係のインストール

```bash
# 必要なPythonパッケージのインストール
pip install -r requirements.txt

# DrissionPageの追加設定（必要に応じて）
python -c "from DrissionPage import ChromiumOptions; print('DrissionPage installation verified')"
```

### 5. ディレクトリ権限の設定

```bash
# ログディレクトリの作成と権限設定
mkdir -p logs
chmod 755 logs

# Cookieディレクトリの権限設定
chmod 700 config/cookies

# 設定ファイルの権限設定
chmod 600 .env
```

## 設定

### 1. 環境変数の設定

```bash
# .envファイルの作成
cp .env.example .env

# .envファイルの編集
nano .env
```

重要な設定項目：

```bash
# セキュリティ設定（必須変更）
SECRET_KEY=your-unique-secret-key-here
API_KEY=your-secure-api-key-here
ENCRYPTION_KEY=your-encryption-key-here

# X.com自動ログイン設定
X_USERNAME=your-x-username-here
X_PASSWORD=your-x-password-here
X_EMAIL=your-x-email-here
AUTO_LOGIN_ENABLED=True
LOGIN_RETRY_COUNT=3
LOGIN_TIMEOUT=30

# レート制限設定
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=1000
MAX_CONCURRENT_REQUESTS=5

# ログレベル設定
LOG_LEVEL=INFO
```

### 2. X.com自動ログイン設定

自動ログイン機能を使用するには、以下の設定が必要です：

#### 2.1 ログイン情報の設定

```bash
# .envファイルに以下を設定
X_USERNAME=your_twitter_username    # @マークなしのユーザー名
X_PASSWORD=your_twitter_password    # パスワード
X_EMAIL=your_twitter_email         # メールアドレス（必要に応じて）
AUTO_LOGIN_ENABLED=True            # 自動ログインを有効化
```

#### 2.2 セキュリティ注意事項

- **パスワードの保護**: .envファイルの権限を600に設定
- **2FA認証**: 2FA有効時は手動介入が必要
- **ログイン失敗**: 3回失敗後は手動ログインが必要

```bash
# .envファイルの権限設定
chmod 600 .env
```

#### 2.3 自動ログイン動作

1. **初回起動時**: 設定された認証情報で自動ログイン
2. **Cookie期限切れ**: 自動的に再ログインを実行
3. **ログイン失敗**: エラーログに記録し、手動介入を要求
4. **2FA検出**: 手動認証が必要な旨をログに出力

### 3. APIキーの生成

セキュアなAPIキーを生成します：

```bash
# ランダムなAPIキーの生成
python3 -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"

# 暗号化キーの生成
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### 3. X.comログイン設定

初回のみ手動でX.comにログインし、Cookieを保存する必要があります：

```bash
# テスト用スクリプトの実行
python3 -c "
from scraper.follow_checker import FollowChecker
with FollowChecker() as checker:
    print('ブラウザが起動します。手動でX.comにログインしてください。')
    input('ログイン完了後、Enterキーを押してください...')
    checker.save_current_cookies()
    print('Cookieが保存されました。')
"
```

### 4. システムサービスの設定

systemdサービスとして登録：

```bash
# サービスファイルの作成
sudo tee /etc/systemd/system/x-scraping-api.service > /dev/null <<EOF
[Unit]
Description=X Scraping API Server
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=/opt/x_scraping_api
Environment=PATH=/opt/x_scraping_api/venv/bin
ExecStart=/opt/x_scraping_api/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# サービスの有効化と開始
sudo systemctl daemon-reload
sudo systemctl enable x-scraping-api
sudo systemctl start x-scraping-api
```


## 使用方法

### 1. サーバーの起動確認

```bash
# サービス状態の確認
sudo systemctl status x-scraping-api

# ログの確認
sudo journalctl -u x-scraping-api -f

# ヘルスチェック
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/health
```

### 2. 基本的なAPI呼び出し

#### フォロー確認

```bash
curl -X POST http://localhost:5000/api/check/follow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"target_user": "@elonmusk"}'
```

#### いいね確認

```bash
curl -X POST http://localhost:5000/api/check/like \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"tweet_url": "https://x.com/user/status/1234567890"}'
```

#### リポスト確認

```bash
curl -X POST http://localhost:5000/api/check/repost \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"tweet_url": "https://x.com/user/status/1234567890"}'
```

#### コメント確認

```bash
curl -X POST http://localhost:5000/api/check/comment \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"tweet_url": "https://x.com/user/status/1234567890", "checking_user": "@username"}'
```

### 3. レスポンス形式

成功時のレスポンス例：

```json
{
  "success": true,
  "action": "follow",
  "result": {
    "is_following": true,
    "button_text": "Following",
    "button_state": "following"
  },
  "details": "Follow status checked for @elonmusk",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

エラー時のレスポンス例：

```json
{
  "success": false,
  "action": "follow",
  "result": null,
  "details": null,
  "timestamp": "2025-01-08T10:30:00Z",
  "error": {
    "code": "LOGIN_REQUIRED",
    "message": "X.com login is required. Please update cookies.",
    "retry_after": 300
  }
}
```

## API仕様

### 認証

すべてのAPIエンドポイントは認証が必要です。以下のいずれかの方法でAPIキーを提供してください：

- **HTTPヘッダー**: `X-API-Key: your-api-key`
- **クエリパラメータ**: `?api_key=your-api-key`

### エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/api/health` | GET | ヘルスチェック |
| `/api/check/follow` | POST | フォロー確認 |
| `/api/check/like` | POST | いいね確認 |
| `/api/check/repost` | POST | リポスト確認 |
| `/api/check/comment` | POST | コメント確認 |
| `/api/stats` | GET | 統計情報取得 |

### 詳細仕様

#### GET /api/health

サーバーの状態を確認します。

**レスポンス**:
```json
{
  "success": true,
  "result": {
    "status": "healthy",
    "version": "1.0.0",
    "rate_limit_stats": {
      "requests_per_minute": 5,
      "requests_per_hour": 120,
      "concurrent_requests": 1,
      "limits": {
        "per_minute": 30,
        "per_hour": 1000,
        "concurrent": 5
      }
    }
  },
  "details": "API is running normally",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

#### POST /api/check/follow

指定ユーザーのフォロー状態を確認します。

**リクエストボディ**:
```json
{
  "target_user": "@username"
}
```

**レスポンス**:
```json
{
  "success": true,
  "action": "follow",
  "result": {
    "is_following": true,
    "button_text": "Following",
    "button_state": "following"
  },
  "details": "Follow status checked for @username",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

#### POST /api/check/like

指定ツイートのいいね状態を確認します。

**リクエストボディ**:
```json
{
  "tweet_url": "https://x.com/user/status/1234567890"
}
```

**レスポンス**:
```json
{
  "success": true,
  "action": "like",
  "result": {
    "is_liked": true,
    "like_count": 1250,
    "button_state": "liked"
  },
  "details": "Like status checked for tweet",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

#### POST /api/check/repost

指定ツイートのリポスト状態を確認します。

**リクエストボディ**:
```json
{
  "tweet_url": "https://x.com/user/status/1234567890"
}
```

**レスポンス**:
```json
{
  "success": true,
  "action": "repost",
  "result": {
    "is_reposted": false,
    "repost_count": 89,
    "button_state": "not_reposted"
  },
  "details": "Repost status checked for tweet",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

#### POST /api/check/comment

指定ツイートのコメント状態を確認します。

**リクエストボディ**:
```json
{
  "tweet_url": "https://x.com/user/status/1234567890",
  "checking_user": "@username"
}
```

**レスポンス**:
```json
{
  "success": true,
  "action": "comment",
  "result": {
    "has_commented": true,
    "comment_count": 2,
    "comments": [
      {
        "username": "username",
        "text": "Great post!",
        "timestamp": "2025-01-08T09:15:00Z",
        "comment_id": "1234567891"
      }
    ]
  },
  "details": "Comment status checked for @username",
  "timestamp": "2025-01-08T10:30:00Z"
}
```

### エラーコード

| コード | 説明 | HTTPステータス |
|---|---|---|
| `INVALID_REQUEST` | リクエスト形式が不正 | 400 |
| `MISSING_PARAMETER` | 必須パラメータが不足 | 400 |
| `MISSING_API_KEY` | APIキーが未提供 | 401 |
| `INVALID_API_KEY` | APIキーが無効 | 401 |
| `LOGIN_REQUIRED` | X.comログインが必要 | 401 |
| `ELEMENT_NOT_FOUND` | 対象要素が見つからない | 404 |
| `RATE_LIMIT_EXCEEDED` | レート制限に達した | 429 |
| `SCRAPING_ERROR` | スクレイピングエラー | 500 |
| `INTERNAL_ERROR` | 内部エラー | 500 |

### 6. セッション管理API

#### 6.1 セッション情報取得

**エンドポイント**: `GET /api/session/info`

**説明**: 現在のセッション状態と有効期限を取得します。

**リクエスト例**:
```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:5000/api/session/info
```

**レスポンス例**:
```json
{
  "success": true,
  "result": {
    "valid": true,
    "last_valid": "2025-01-08T10:30:00.000000",
    "expires_at": "2025-01-09T10:30:00.000000",
    "validity_hours": 24,
    "auto_login_enabled": true,
    "last_login_method": "automatic",
    "time_remaining": "23:45:30"
  },
  "details": "Session information retrieved successfully",
  "timestamp": "2025-01-08T10:45:00.000000"
}
```

#### 6.2 セッション強制更新

**エンドポイント**: `POST /api/session/refresh`

**説明**: セッションを強制的に無効化し、次回API呼び出し時に再ログインを実行します。

**リクエスト例**:
```bash
curl -X POST \
     -H "X-API-Key: your-api-key" \
     http://localhost:5000/api/session/refresh
```

**レスポンス例**:
```json
{
  "success": true,
  "result": {
    "message": "Session refreshed successfully",
    "next_action": "Re-login required for next API call"
  },
  "details": "Session has been forcefully refreshed",
  "timestamp": "2025-01-08T10:45:00.000000"
}
```

#### 6.3 セッション管理の活用

**自動ログイン状態の確認**:
```bash
# セッション情報を確認
response=$(curl -s -H "X-API-Key: $API_KEY" http://localhost:5000/api/session/info)
valid=$(echo $response | jq -r '.result.valid')

if [ "$valid" = "false" ]; then
    echo "Session expired - automatic re-login will occur on next API call"
fi
```

**手動セッション更新**:
```bash
# 問題が発生した場合の強制更新
curl -X POST -H "X-API-Key: $API_KEY" http://localhost:5000/api/session/refresh
```

## PHP連携

既存のPHPアプリケーションとの連携方法を説明します。

### 1. 基本的な連携コード

```php
<?php
class XScrapingAPIClient {
    private $baseUrl;
    private $apiKey;
    
    public function __construct($baseUrl, $apiKey) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->apiKey = $apiKey;
    }
    
    private function makeRequest($endpoint, $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $headers = [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->apiKey
        ];
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_CONNECTTIMEOUT => 10
        ]);
        
        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($response === false) {
            throw new Exception('API request failed');
        }
        
        $result = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid JSON response');
        }
        
        return [
            'http_code' => $httpCode,
            'data' => $result
        ];
    }
    
    public function checkFollow($targetUser) {
        return $this->makeRequest('/api/check/follow', [
            'target_user' => $targetUser
        ]);
    }
    
    public function checkLike($tweetUrl) {
        return $this->makeRequest('/api/check/like', [
            'tweet_url' => $tweetUrl
        ]);
    }
    
    public function checkRepost($tweetUrl) {
        return $this->makeRequest('/api/check/repost', [
            'tweet_url' => $tweetUrl
        ]);
    }
    
    public function checkComment($tweetUrl, $checkingUser) {
        return $this->makeRequest('/api/check/comment', [
            'tweet_url' => $tweetUrl,
            'checking_user' => $checkingUser
        ]);
    }
    
    public function getHealth() {
        return $this->makeRequest('/api/health');
    }
}
?>
```

### 2. 使用例

```php
<?php
// APIクライアントの初期化
$apiClient = new XScrapingAPIClient('http://localhost:5000', 'your-api-key');

try {
    // フォロー確認
    $followResult = $apiClient->checkFollow('@elonmusk');
    
    if ($followResult['data']['success']) {
        $isFollowing = $followResult['data']['result']['is_following'];
        echo "フォロー状態: " . ($isFollowing ? 'フォロー中' : '未フォロー') . "\n";
        
        // データベース更新
        updateUserCampaignAction($userId, $campaignId, 'follow', $isFollowing);
    } else {
        echo "エラー: " . $followResult['data']['error']['message'] . "\n";
    }
    
    // いいね確認
    $likeResult = $apiClient->checkLike('https://x.com/user/status/1234567890');
    
    if ($likeResult['data']['success']) {
        $isLiked = $likeResult['data']['result']['is_liked'];
        echo "いいね状態: " . ($isLiked ? 'いいね済み' : '未いいね') . "\n";
        
        // データベース更新
        updateUserCampaignAction($userId, $campaignId, 'like', $isLiked);
    }
    
} catch (Exception $e) {
    echo "API呼び出しエラー: " . $e->getMessage() . "\n";
}

function updateUserCampaignAction($userId, $campaignId, $action, $completed) {
    // データベース更新処理
    $pdo = new PDO($dsn, $username, $password);
    
    $sql = "INSERT INTO user_campaign_actions (user_id, campaign_id, action_type, completed, checked_at) 
            VALUES (?, ?, ?, ?, NOW()) 
            ON DUPLICATE KEY UPDATE completed = ?, checked_at = NOW()";
    
    $stmt = $pdo->prepare($sql);
    $stmt->execute([$userId, $campaignId, $action, $completed, $completed]);
}
?>
```

### 3. エラーハンドリング

```php
<?php
function handleAPIResponse($response) {
    if ($response['http_code'] !== 200) {
        switch ($response['http_code']) {
            case 401:
                throw new Exception('認証エラー: APIキーを確認してください');
            case 429:
                $retryAfter = $response['data']['error']['retry_after'] ?? 60;
                throw new Exception("レート制限: {$retryAfter}秒後に再試行してください");
            case 500:
                throw new Exception('サーバーエラー: しばらく時間をおいて再試行してください');
            default:
                throw new Exception('API呼び出しに失敗しました');
        }
    }
    
    if (!$response['data']['success']) {
        $errorCode = $response['data']['error']['code'] ?? 'UNKNOWN';
        $errorMessage = $response['data']['error']['message'] ?? 'Unknown error';
        throw new Exception("API エラー [{$errorCode}]: {$errorMessage}");
    }
    
    return $response['data']['result'];
}
?>
```

### 4. 非同期処理

大量のチェックを行う場合は、非同期処理を使用することを推奨します：

```php
<?php
// Guzzle HTTPを使用した非同期処理例
use GuzzleHttp\Client;
use GuzzleHttp\Promise;

function checkMultipleActionsAsync($actions) {
    $client = new Client([
        'base_uri' => 'http://localhost:5000',
        'timeout' => 30,
        'headers' => [
            'Content-Type' => 'application/json',
            'X-API-Key' => 'your-api-key'
        ]
    ]);
    
    $promises = [];
    
    foreach ($actions as $key => $action) {
        $promises[$key] = $client->postAsync('/api/check/' . $action['type'], [
            'json' => $action['data']
        ]);
    }
    
    $responses = Promise\settle($promises)->wait();
    
    $results = [];
    foreach ($responses as $key => $response) {
        if ($response['state'] === 'fulfilled') {
            $results[$key] = json_decode($response['value']->getBody(), true);
        } else {
            $results[$key] = ['success' => false, 'error' => $response['reason']->getMessage()];
        }
    }
    
    return $results;
}
?>
```


## 運用・監視

### 1. ログ監視

#### ログファイルの場所

- **アプリケーションログ**: `logs/app.log`
- **アクセスログ**: `logs/access.log`
- **エラーログ**: `logs/error.log`
- **システムログ**: `journalctl -u x-scraping-api`

#### ログレベル

- **DEBUG**: 詳細なデバッグ情報
- **INFO**: 正常な処理の記録
- **WARNING**: 警告レベルの問題
- **ERROR**: エラー発生時の記録
- **CRITICAL**: システム停止レベルの問題

#### ログ監視コマンド

```bash
# リアルタイムログ監視
tail -f logs/app.log

# エラーログのみ表示
grep "ERROR\|CRITICAL" logs/app.log

# 特定期間のログ表示
journalctl -u x-scraping-api --since "2025-01-08 10:00:00" --until "2025-01-08 11:00:00"

# ログローテーション確認
ls -la logs/app.log*
```

### 2. パフォーマンス監視

#### システムリソース監視

```bash
# CPU・メモリ使用量確認
top -p $(pgrep -f "gunicorn.*app:app")

# ディスク使用量確認
df -h
du -sh /opt/x_scraping_api/logs/

# ネットワーク接続確認
netstat -tlnp | grep :5000
```

#### API統計情報の取得

```bash
# 統計情報API呼び出し
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/stats

# レスポンス時間測定
time curl -H "X-API-Key: your-api-key" http://localhost:5000/api/health
```

### 3. 自動監視スクリプト

#### ヘルスチェックスクリプト

```bash
#!/bin/bash
# health_check.sh

API_KEY="your-api-key"
API_URL="http://localhost:5000/api/health"
LOG_FILE="/var/log/x-scraping-api-health.log"

response=$(curl -s -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL")
http_code="${response: -3}"
body="${response%???}"

timestamp=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$http_code" -eq 200 ]; then
    echo "[$timestamp] OK: API is healthy" >> "$LOG_FILE"
else
    echo "[$timestamp] ERROR: API health check failed (HTTP $http_code)" >> "$LOG_FILE"
    # アラート送信処理をここに追加
    # send_alert "X Scraping API is down"
fi
```

#### Cronジョブ設定

```bash
# crontabに追加
crontab -e

# 5分ごとにヘルスチェック実行
*/5 * * * * /opt/x_scraping_api/scripts/health_check.sh

# 日次でログローテーション
0 2 * * * find /opt/x_scraping_api/logs -name "*.log" -mtime +7 -delete
```

### 4. アラート設定

#### Slack通知スクリプト

```bash
#!/bin/bash
# slack_alert.sh

SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
MESSAGE="$1"

curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"🚨 X Scraping API Alert: $MESSAGE\"}" \
    "$SLACK_WEBHOOK_URL"
```

#### メール通知設定

```bash
# mailutilsのインストール
sudo apt install mailutils

# メール送信テスト
echo "Test message" | mail -s "X Scraping API Test" admin@example.com
```

## トラブルシューティング

### 1. よくある問題と解決方法

#### 問題: APIが起動しない

**症状**: サービス起動時にエラーが発生する

**確認方法**:
```bash
sudo systemctl status x-scraping-api
sudo journalctl -u x-scraping-api -n 50
```

**解決方法**:
1. 依存関係の確認
```bash
source /opt/x_scraping_api/venv/bin/activate
pip install -r requirements.txt
```

2. 権限の確認
```bash
sudo chown -R $USER:$USER /opt/x_scraping_api
chmod +x /opt/x_scraping_api/venv/bin/gunicorn
```

3. ポートの確認
```bash
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000
```

#### 問題: ログイン認証エラー

**症状**: `LOGIN_REQUIRED` エラーが頻発する

**確認方法**:
```bash
# Cookieファイルの確認
ls -la /opt/x_scraping_api/config/cookies/
cat /opt/x_scraping_api/logs/app.log | grep "LOGIN_REQUIRED"
```

**解決方法**:
1. 手動ログインの実行
```bash
cd /opt/x_scraping_api
source venv/bin/activate
python3 -c "
from scraper.follow_checker import FollowChecker
with FollowChecker() as checker:
    print('手動ログインを実行してください')
    input('完了後Enterを押してください...')
    checker.save_current_cookies()
"
```

2. Cookie有効期限の確認
```bash
python3 -c "
from utils.auth_manager import auth_manager
cookies = auth_manager.load_cookies()
print('Cookies loaded:', cookies is not None)
"
```

#### 問題: レート制限エラー

**症状**: `RATE_LIMIT_EXCEEDED` エラーが発生する

**確認方法**:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/stats
```

**解決方法**:
1. レート制限設定の調整
```bash
# .envファイルの編集
nano .env

# 以下の値を調整
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=2000
```

2. Redis使用の検討
```bash
# Redisのインストール
sudo apt install redis-server

# .envファイルでRedis有効化
REDIS_ENABLED=True
REDIS_URL=redis://localhost:6379/0
```

#### 問題: スクレイピングエラー

**症状**: `ELEMENT_NOT_FOUND` エラーが発生する

**確認方法**:
```bash
# スクリーンショット機能でページ状態を確認
python3 -c "
from scraper.follow_checker import FollowChecker
with FollowChecker() as checker:
    checker.navigate_to_url('https://x.com')
    screenshot_path = checker.take_screenshot()
    print(f'Screenshot saved: {screenshot_path}')
"
```

**解決方法**:
1. X.comのページ構造変更への対応
2. セレクタの更新
3. 待機時間の調整

### 2. デバッグモード

#### デバッグモードの有効化

```bash
# .envファイルでデバッグモード有効化
DEBUG=True
LOG_LEVEL=DEBUG

# サービス再起動
sudo systemctl restart x-scraping-api
```

#### 詳細ログの確認

```bash
# デバッグログの表示
tail -f logs/app.log | grep DEBUG

# 特定のリクエストIDでフィルタ
grep "request_id_here" logs/app.log
```

### 3. パフォーマンス問題

#### メモリ使用量の最適化

```bash
# メモリ使用量確認
ps aux | grep gunicorn
free -h

# ワーカー数の調整
nano gunicorn.conf.py
# workers = 2  # CPUコア数に応じて調整
```

#### ディスク容量の管理

```bash
# ログファイルサイズ確認
du -sh logs/

# 古いログファイルの削除
find logs/ -name "*.log.*" -mtime +30 -delete

# ログローテーション設定
sudo nano /etc/logrotate.d/x-scraping-api
```

### 4. セキュリティ問題

#### 不正アクセスの検出

```bash
# アクセスログの分析
grep "401\|403" logs/access.log
grep "INVALID_API_KEY" logs/app.log

# 異常なリクエスト数の検出
awk '{print $1}' logs/access.log | sort | uniq -c | sort -nr | head -10
```

#### APIキーの更新

```bash
# 新しいAPIキーの生成
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# .envファイルの更新
nano .env

# サービス再起動
sudo systemctl restart x-scraping-api
```

## セキュリティ

### 1. 認証・認可

#### APIキー管理

- **強力なAPIキー**: 32文字以上のランダム文字列を使用
- **定期的な更新**: 3ヶ月ごとにAPIキーを更新
- **アクセス制限**: 必要最小限のIPアドレスからのみアクセス許可

#### Cookie暗号化

- **暗号化キー**: Fernet暗号化による強力な暗号化
- **ファイル権限**: Cookieファイルは600権限で保護
- **有効期限**: 30日間の自動有効期限設定

### 2. ネットワークセキュリティ

#### ファイアウォール設定

```bash
# UFWファイアウォールの設定
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24 to any port 5000  # 内部ネットワークのみ許可
sudo ufw status
```

#### リバースプロキシ設定

Nginxを使用したリバースプロキシ設定：

```nginx
# /etc/nginx/sites-available/x-scraping-api
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # レート制限
        limit_req zone=api burst=10 nodelay;
    }
}

# レート制限設定
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
}
```

### 3. ログセキュリティ

#### 個人情報のマスキング

ログ出力時に自動的に個人情報をマスキング：

- ユーザー名: `@username` → `@us****me`
- メールアドレス: `user@example.com` → `us**@ex******.com`
- APIキー: 最初の4文字のみ表示

#### ログアクセス制限

```bash
# ログファイルの権限設定
chmod 640 logs/*.log
chown root:adm logs/*.log

# ログディレクトリの権限
chmod 750 logs/
```

### 4. 定期的なセキュリティチェック

#### セキュリティ監査スクリプト

```bash
#!/bin/bash
# security_audit.sh

echo "=== X Scraping API Security Audit ==="
echo "Date: $(date)"
echo

# ファイル権限チェック
echo "1. File Permissions:"
ls -la /opt/x_scraping_api/.env
ls -la /opt/x_scraping_api/config/cookies/

# プロセス確認
echo "2. Running Processes:"
ps aux | grep gunicorn

# ネットワーク接続確認
echo "3. Network Connections:"
netstat -tlnp | grep :5000

# ログファイルサイズ確認
echo "4. Log File Sizes:"
du -sh /opt/x_scraping_api/logs/*

# 最近のエラー確認
echo "5. Recent Errors:"
tail -n 20 /opt/x_scraping_api/logs/app.log | grep ERROR

echo "=== Audit Complete ==="
```

### 5. バックアップとリカバリ

#### 設定ファイルのバックアップ

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/x-scraping-api/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 設定ファイルのバックアップ
cp /opt/x_scraping_api/.env "$BACKUP_DIR/"
cp -r /opt/x_scraping_api/config/ "$BACKUP_DIR/"

# ログファイルのアーカイブ
tar -czf "$BACKUP_DIR/logs.tar.gz" /opt/x_scraping_api/logs/

echo "Backup completed: $BACKUP_DIR"
```

#### リストア手順

```bash
# サービス停止
sudo systemctl stop x-scraping-api

# 設定ファイルのリストア
cp /backup/x-scraping-api/20250108/.env /opt/x_scraping_api/
cp -r /backup/x-scraping-api/20250108/config/ /opt/x_scraping_api/

# 権限の修正
chmod 600 /opt/x_scraping_api/.env
chmod 700 /opt/x_scraping_api/config/cookies/

# サービス再開
sudo systemctl start x-scraping-api
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

```
MIT License

Copyright (c) 2025 Manus AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## サポート

### 技術サポート

- **ドキュメント**: このREADMEファイルを参照
- **ログ確認**: 問題発生時は必ずログファイルを確認
- **GitHub Issues**: バグ報告や機能要望はGitHubのIssuesで管理

### 免責事項

- このソフトウェアはX.com（旧Twitter）の利用規約に準拠して使用してください
- スクレイピング行為による法的リスクは使用者の責任となります
- サービスの可用性や精度について保証はありません
- X.comの仕様変更により動作しなくなる可能性があります

### 更新履歴

- **v1.0.0** (2025-01-08): 初回リリース
  - フォロー、いいね、リポスト、コメント確認機能
  - Flask API サーバー
  - レート制限機能
  - Cookie暗号化
  - 詳細ログ出力

---

**作成者**: Manus AI  
**最終更新**: 2025年1月8日

