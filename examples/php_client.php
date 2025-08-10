<?php
/**
 * X.com スクレイピングAPI PHPクライアント
 * 
 * 使用例:
 * $client = new XScrapingAPIClient('http://localhost:5000', 'your-api-key');
 * $result = $client->checkFollow('@elonmusk');
 * 
 * @author Manus AI
 * @version 1.0.0
 * @since 2025-01-08
 */

class XScrapingAPIClient {
    private $baseUrl;
    private $apiKey;
    private $timeout;
    private $connectTimeout;
    
    /**
     * コンストラクタ
     * 
     * @param string $baseUrl APIサーバーのベースURL
     * @param string $apiKey APIキー
     * @param int $timeout リクエストタイムアウト（秒）
     * @param int $connectTimeout 接続タイムアウト（秒）
     */
    public function __construct($baseUrl, $apiKey, $timeout = 30, $connectTimeout = 10) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->apiKey = $apiKey;
        $this->timeout = $timeout;
        $this->connectTimeout = $connectTimeout;
    }
    
    /**
     * APIリクエストを実行
     * 
     * @param string $endpoint エンドポイント
     * @param array|null $data リクエストデータ
     * @param string $method HTTPメソッド
     * @return array レスポンス配列
     * @throws Exception API呼び出しエラー
     */
    private function makeRequest($endpoint, $data = null, $method = 'POST') {
        $url = $this->baseUrl . $endpoint;
        
        $headers = [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->apiKey,
            'User-Agent: XScrapingAPI-PHP-Client/1.0.0'
        ];
        
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_CONNECTTIMEOUT => $this->connectTimeout,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_MAXREDIRS => 3,
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_SSL_VERIFYHOST => 2
        ]);
        
        if ($method === 'POST' && $data !== null) {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        } elseif ($method === 'GET' && $data !== null) {
            $url .= '?' . http_build_query($data);
            curl_setopt($ch, CURLOPT_URL, $url);
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($response === false) {
            throw new Exception('cURL Error: ' . $error);
        }
        
        $result = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('Invalid JSON response: ' . json_last_error_msg());
        }
        
        return [
            'http_code' => $httpCode,
            'data' => $result
        ];
    }
    
    /**
     * レスポンスを処理してエラーハンドリング
     * 
     * @param array $response APIレスポンス
     * @return array 処理結果
     * @throws Exception APIエラー
     */
    private function handleResponse($response) {
        if ($response['http_code'] !== 200) {
            $errorMessage = 'HTTP Error ' . $response['http_code'];
            
            switch ($response['http_code']) {
                case 400:
                    $errorMessage = 'Bad Request: リクエスト形式が不正です';
                    break;
                case 401:
                    $errorMessage = 'Unauthorized: APIキーが無効または認証が必要です';
                    break;
                case 404:
                    $errorMessage = 'Not Found: 対象が見つかりません';
                    break;
                case 429:
                    $retryAfter = $response['data']['error']['retry_after'] ?? 60;
                    $errorMessage = "Rate Limited: {$retryAfter}秒後に再試行してください";
                    break;
                case 500:
                    $errorMessage = 'Internal Server Error: サーバーエラーが発生しました';
                    break;
            }
            
            throw new Exception($errorMessage);
        }
        
        if (!$response['data']['success']) {
            $errorCode = $response['data']['error']['code'] ?? 'UNKNOWN';
            $errorMessage = $response['data']['error']['message'] ?? 'Unknown error';
            throw new Exception("API Error [{$errorCode}]: {$errorMessage}");
        }
        
        return $response['data'];
    }
    
    /**
     * ヘルスチェック
     * 
     * @return array ヘルスチェック結果
     */
    public function getHealth() {
        $response = $this->makeRequest('/api/health', null, 'GET');
        return $this->handleResponse($response);
    }
    
    /**
     * フォロー状態確認
     * 
     * @param string $targetUser 対象ユーザー名（@付きまたはなし）
     * @return array フォロー確認結果
     */
    public function checkFollow($targetUser) {
        $response = $this->makeRequest('/api/check/follow', [
            'target_user' => $targetUser
        ]);
        return $this->handleResponse($response);
    }
    
    /**
     * いいね状態確認
     * 
     * @param string $tweetUrl ツイートURL
     * @return array いいね確認結果
     */
    public function checkLike($tweetUrl) {
        $response = $this->makeRequest('/api/check/like', [
            'tweet_url' => $tweetUrl
        ]);
        return $this->handleResponse($response);
    }
    
    /**
     * リポスト状態確認
     * 
     * @param string $tweetUrl ツイートURL
     * @return array リポスト確認結果
     */
    public function checkRepost($tweetUrl) {
        $response = $this->makeRequest('/api/check/repost', [
            'tweet_url' => $tweetUrl
        ]);
        return $this->handleResponse($response);
    }
    
    /**
     * コメント状態確認
     * 
     * @param string $tweetUrl ツイートURL
     * @param string $checkingUser 確認対象ユーザー名
     * @return array コメント確認結果
     */
    public function checkComment($tweetUrl, $checkingUser) {
        $response = $this->makeRequest('/api/check/comment', [
            'tweet_url' => $tweetUrl,
            'checking_user' => $checkingUser
        ]);
        return $this->handleResponse($response);
    }
    
    /**
     * 統計情報取得
     * 
     * @return array 統計情報
     */
    public function getStats() {
        $response = $this->makeRequest('/api/stats', null, 'GET');
        return $this->handleResponse($response);
    }
    
    /**
     * 複数のアクションを一括確認
     * 
     * @param array $actions アクション配列
     * @return array 確認結果配列
     */
    public function checkMultipleActions($actions) {
        $results = [];
        
        foreach ($actions as $key => $action) {
            try {
                switch ($action['type']) {
                    case 'follow':
                        $result = $this->checkFollow($action['target_user']);
                        break;
                    case 'like':
                        $result = $this->checkLike($action['tweet_url']);
                        break;
                    case 'repost':
                        $result = $this->checkRepost($action['tweet_url']);
                        break;
                    case 'comment':
                        $result = $this->checkComment($action['tweet_url'], $action['checking_user']);
                        break;
                    default:
                        throw new Exception('Unknown action type: ' . $action['type']);
                }
                
                $results[$key] = [
                    'success' => true,
                    'data' => $result
                ];
                
            } catch (Exception $e) {
                $results[$key] = [
                    'success' => false,
                    'error' => $e->getMessage()
                ];
            }
            
            // レート制限を考慮した待機
            if (count($actions) > 1) {
                sleep(2);
            }
        }
        
        return $results;
    }
}

/**
 * データベース連携用のヘルパークラス
 */
class XScrapingDBHelper {
    private $pdo;
    private $apiClient;
    
    public function __construct($pdo, $apiClient) {
        $this->pdo = $pdo;
        $this->apiClient = $apiClient;
    }
    
    /**
     * ユーザーのキャンペーンアクションを確認・更新
     * 
     * @param int $userId ユーザーID
     * @param int $campaignId キャンペーンID
     * @param array $requiredActions 必要なアクション配列
     * @return array 確認結果
     */
    public function checkAndUpdateUserActions($userId, $campaignId, $requiredActions) {
        $results = [];
        
        foreach ($requiredActions as $action) {
            try {
                // APIで確認
                $apiResult = null;
                switch ($action['type']) {
                    case 'follow':
                        $apiResult = $this->apiClient->checkFollow($action['target_user']);
                        $completed = $apiResult['result']['is_following'];
                        break;
                    case 'like':
                        $apiResult = $this->apiClient->checkLike($action['tweet_url']);
                        $completed = $apiResult['result']['is_liked'];
                        break;
                    case 'repost':
                        $apiResult = $this->apiClient->checkRepost($action['tweet_url']);
                        $completed = $apiResult['result']['is_reposted'];
                        break;
                    case 'comment':
                        $apiResult = $this->apiClient->checkComment($action['tweet_url'], $action['checking_user']);
                        $completed = $apiResult['result']['has_commented'];
                        break;
                }
                
                // データベース更新
                $this->updateUserCampaignAction($userId, $campaignId, $action['type'], $completed);
                
                $results[$action['type']] = [
                    'success' => true,
                    'completed' => $completed,
                    'api_result' => $apiResult
                ];
                
            } catch (Exception $e) {
                $results[$action['type']] = [
                    'success' => false,
                    'error' => $e->getMessage()
                ];
            }
        }
        
        return $results;
    }
    
    /**
     * ユーザーキャンペーンアクションをデータベースに記録
     * 
     * @param int $userId ユーザーID
     * @param int $campaignId キャンペーンID
     * @param string $actionType アクションタイプ
     * @param bool $completed 完了状態
     */
    private function updateUserCampaignAction($userId, $campaignId, $actionType, $completed) {
        $sql = "INSERT INTO user_campaign_actions (user_id, campaign_id, action_type, completed, checked_at) 
                VALUES (?, ?, ?, ?, NOW()) 
                ON DUPLICATE KEY UPDATE completed = ?, checked_at = NOW()";
        
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$userId, $campaignId, $actionType, $completed, $completed]);
    }
}

// 使用例
if (basename(__FILE__) === basename($_SERVER['SCRIPT_NAME'])) {
    try {
        // APIクライアントの初期化
        $apiClient = new XScrapingAPIClient('http://localhost:5000', 'your-api-key-here');
        
        // ヘルスチェック
        echo "=== ヘルスチェック ===\n";
        $health = $apiClient->getHealth();
        echo "Status: " . $health['result']['status'] . "\n";
        echo "Version: " . $health['result']['version'] . "\n\n";
        
        // フォロー確認
        echo "=== フォロー確認 ===\n";
        $followResult = $apiClient->checkFollow('@elonmusk');
        echo "Following: " . ($followResult['result']['is_following'] ? 'Yes' : 'No') . "\n";
        echo "Button State: " . $followResult['result']['button_state'] . "\n\n";
        
        // いいね確認
        echo "=== いいね確認 ===\n";
        $likeResult = $apiClient->checkLike('https://x.com/elonmusk/status/1234567890');
        echo "Liked: " . ($likeResult['result']['is_liked'] ? 'Yes' : 'No') . "\n";
        echo "Like Count: " . $likeResult['result']['like_count'] . "\n\n";
        
        // 複数アクション確認
        echo "=== 複数アクション確認 ===\n";
        $actions = [
            'follow_check' => [
                'type' => 'follow',
                'target_user' => '@elonmusk'
            ],
            'like_check' => [
                'type' => 'like',
                'tweet_url' => 'https://x.com/elonmusk/status/1234567890'
            ]
        ];
        
        $multiResults = $apiClient->checkMultipleActions($actions);
        foreach ($multiResults as $key => $result) {
            echo "$key: " . ($result['success'] ? 'Success' : 'Failed - ' . $result['error']) . "\n";
        }
        
    } catch (Exception $e) {
        echo "Error: " . $e->getMessage() . "\n";
    }
}
?>

