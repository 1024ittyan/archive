#!/usr/bin/env python3
"""
Configuration Module - アプリケーション設定
"""
import os
import secrets
from datetime import timedelta

class Config:
    """アプリケーション設定クラス"""
    
    # Flask設定
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    
    # アップロード設定
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # ログ設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # デフォルト設定
    DEFAULT_SETTINGS = {
        'target_name': '瓜田',
        'event_title': '図書館バイト📚',
        'event_location': '図書館',
        'color_id': '9',  # 青
        'reminder_minutes': 10,
        'calendar_id': 'primary',
        'additional_reminder': False,
        'additional_reminder_minutes': 60,
        'event_description_template': 'シフト時間: {time}'
    }
    
    # セキュリティ設定の追加
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True  # HTTPS環境では必須
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('CSRF_SECRET_KEY', secrets.token_hex(16))
    
    # 初期化時にディレクトリを作成
    @classmethod
    def init_app(cls, app):
        """アプリケーション初期化時の設定"""
        # セッションディレクトリの作成
        if not os.path.exists(cls.SESSION_FILE_DIR):
            os.makedirs(cls.SESSION_FILE_DIR)
        
        # アップロードディレクトリの作成
        if not os.path.exists(cls.UPLOAD_FOLDER):
            os.makedirs(cls.UPLOAD_FOLDER)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Vercel環境用の設定
    if os.getenv('VERCEL_ENV') == 'production':
        SESSION_FILE_DIR = '/tmp/flask_session'
        UPLOAD_FOLDER = '/tmp/uploads' 