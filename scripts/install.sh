#!/bin/bash

# X.com スクレイピングAPI 自動インストールスクリプト
# 作成者: Manus AI
# 最終更新: 2025-01-08

set -e  # エラー時に停止

# 色付きメッセージ用の関数
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# 設定変数
INSTALL_DIR="/opt/x_scraping_api"
SERVICE_NAME="x-scraping-api"
PYTHON_VERSION="3.9"

print_info "X.com スクレイピングAPI インストールを開始します..."

# 1. システム要件チェック
print_info "システム要件をチェックしています..."

# OSチェック
if [[ ! -f /etc/os-release ]]; then
    print_error "サポートされていないOSです"
    exit 1
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]]; then
    print_warning "Ubuntu/Debian以外のOSが検出されました。互換性に問題がある可能性があります。"
fi

# Pythonバージョンチェック
if ! command -v python3.9 &> /dev/null; then
    print_info "Python 3.9をインストールしています..."
    sudo apt update
    sudo apt install -y python3.9 python3.9-pip python3.9-venv python3.9-dev
fi

# 2. システムパッケージのインストール
print_info "システムパッケージをインストールしています..."

sudo apt update
sudo apt install -y \
    curl \
    wget \
    git \
    build-essential \
    chromium-browser \
    chromium-chromedriver \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    nginx \
    redis-server

# 3. インストールディレクトリの作成
print_info "インストールディレクトリを作成しています..."

if [[ -d "$INSTALL_DIR" ]]; then
    print_warning "既存のインストールディレクトリが見つかりました。バックアップを作成します..."
    sudo mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown $USER:$USER "$INSTALL_DIR"

# 4. アプリケーションファイルのコピー
print_info "アプリケーションファイルをコピーしています..."

# 現在のディレクトリからファイルをコピー
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cp -r "$PROJECT_DIR"/* "$INSTALL_DIR/"

# 5. Python仮想環境の作成
print_info "Python仮想環境を作成しています..."

cd "$INSTALL_DIR"
python3.9 -m venv venv
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# 依存関係のインストール
pip install -r requirements.txt

# 6. 設定ファイルの作成
print_info "設定ファイルを作成しています..."

if [[ ! -f .env ]]; then
    cp .env.example .env
    
    # ランダムキーの生成
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # .envファイルの更新
    sed -i "s/your-secret-key-here-change-this-in-production/$SECRET_KEY/" .env
    sed -i "s/your-api-key-here/$API_KEY/" .env
    sed -i "s/your-encryption-key-here/$ENCRYPTION_KEY/" .env
    
    print_success "設定ファイルが作成されました"
    print_info "生成されたAPIキー: $API_KEY"
fi

# 7. ディレクトリ権限の設定
print_info "ディレクトリ権限を設定しています..."

mkdir -p logs config/cookies
chmod 755 logs
chmod 700 config/cookies
chmod 600 .env

# 8. systemdサービスの作成
print_info "systemdサービスを作成しています..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=X Scraping API Server
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -c gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 9. サービスの有効化と開始
print_info "サービスを有効化しています..."

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# 10. Nginxリバースプロキシの設定
print_info "Nginxリバースプロキシを設定しています..."

sudo tee /etc/nginx/sites-available/x-scraping-api > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # タイムアウト設定
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF

# Nginxサイトの有効化
sudo ln -sf /etc/nginx/sites-available/x-scraping-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 11. ファイアウォール設定
print_info "ファイアウォールを設定しています..."

if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 'Nginx Full'
    print_success "ファイアウォールが設定されました"
fi

# 12. サービス開始
print_info "サービスを開始しています..."

sudo systemctl start $SERVICE_NAME

# 13. インストール確認
print_info "インストールを確認しています..."

sleep 5

if sudo systemctl is-active --quiet $SERVICE_NAME; then
    print_success "サービスが正常に起動しました"
else
    print_error "サービスの起動に失敗しました"
    sudo systemctl status $SERVICE_NAME
    exit 1
fi

# ヘルスチェック
API_KEY=$(grep "^API_KEY=" .env | cut -d'=' -f2)
if curl -s -H "X-API-Key: $API_KEY" http://localhost:5000/api/health > /dev/null; then
    print_success "APIが正常に動作しています"
else
    print_warning "APIの動作確認に失敗しました。ログを確認してください。"
fi

# 14. インストール完了メッセージ
print_success "インストールが完了しました！"
echo
echo "=== インストール情報 ==="
echo "インストールディレクトリ: $INSTALL_DIR"
echo "サービス名: $SERVICE_NAME"
echo "APIキー: $API_KEY"
echo "API URL: http://localhost:5000"
echo
echo "=== 次のステップ ==="
echo "1. X.comにログインしてCookieを保存してください:"
echo "   cd $INSTALL_DIR && source venv/bin/activate"
echo "   python3 -c \"from scraper.follow_checker import FollowChecker; ..."
echo
echo "2. サービス状態の確認:"
echo "   sudo systemctl status $SERVICE_NAME"
echo
echo "3. ログの確認:"
echo "   tail -f $INSTALL_DIR/logs/app.log"
echo
echo "4. APIテスト:"
echo "   curl -H \"X-API-Key: $API_KEY\" http://localhost:5000/api/health"
echo
print_success "セットアップガイドについては README.md を参照してください"

