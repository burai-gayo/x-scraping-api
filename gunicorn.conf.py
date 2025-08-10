# Gunicorn設定ファイル

import os
import multiprocessing

# サーバー設定
bind = "0.0.0.0:5000"
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # 最大4ワーカー
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# タイムアウト設定
timeout = 30
keepalive = 2
graceful_timeout = 30

# ログ設定
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# プロセス設定
preload_app = True
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# セキュリティ設定
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# パフォーマンス設定
worker_tmp_dir = "/dev/shm"  # メモリ上の一時ディレクトリを使用

def when_ready(server):
    """サーバー起動時の処理"""
    server.log.info("X Scraping API Server is ready. Listening on: %s", server.address)

def worker_int(worker):
    """ワーカー中断時の処理"""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """ワーカーフォーク前の処理"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """ワーカーフォーク後の処理"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """ワーカー異常終了時の処理"""
    worker.log.info("Worker received SIGABRT signal")

