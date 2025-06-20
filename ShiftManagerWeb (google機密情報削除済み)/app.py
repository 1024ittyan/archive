#!/usr/bin/env python3
"""
ShiftManagerWeb - シフト表PDFからGoogleカレンダーにイベントを登録するアプリケーション
"""
import os
import re
import logging
import json
import tempfile
from datetime import datetime, timedelta
from functools import wraps
import secrets

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.auth.transport.requests
from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash, send_from_directory
from flask_session import Session
from werkzeug.utils import secure_filename

# 自作モジュールのインポート
from pdf_parser import PdfParser
from config import Config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 開発環境用: HTTP でも OAuth を許可
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Flaskアプリケーションの初期化
app = Flask(__name__)
app.config.from_object(Config)

# セッション管理の初期化
Config.init_app(app)  # 必要なディレクトリを作成
Session(app)

# セッション設定の改善
def configure_session():
    app.config.update(
        SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1),
        SESSION_REFRESH_EACH_REQUEST=True
    )

# アプリケーション初期化時に呼び出し
configure_session()

# セッション初期化処理の追加
def init_session():
    if 'state' not in session:
        session['state'] = secrets.token_urlsafe(32)
    session.permanent = True

# 現在の年をすべてのテンプレートに渡す
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# OAuth 2.0 クライアントシークレットファイルのパス
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")

# 認証に必要なスコープと API の設定
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# アップロードされたPDFの一時保存先
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 許可するファイル拡張子
ALLOWED_EXTENSIONS = {'pdf'}

# REDIRECT_URIをグローバル変数として定義
REDIRECT_URI = 'http://localhost:5000/oauth2callback'  # 開発環境用
# 本番環境では環境変数から取得
# REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://your-domain.com/oauth2callback')

# プロダクション環境用の設定を追加
if os.getenv('VERCEL_ENV') == 'production':
    # Vercel環境用の設定
    REDIRECT_URI = os.getenv('REDIRECT_URI')
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = '/tmp/flask_session'  # Vercelの一時ディレクトリを使用

def allowed_file(filename):
    """アップロードされたファイルが許可された拡張子かチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Google認証が必要なルートに適用するデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return redirect(url_for('authorize'))
        return f(*args, **kwargs)
    return decorated_function

def get_calendar_service():
    """Google Calendar APIサービスを取得"""
    credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    
    # トークンの有効期限をチェックし、必要に応じて更新
    request_obj = google.auth.transport.requests.Request()
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(request_obj)
            session['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        except Exception as e:
            logger.error(f"トークン更新エラー: {e}")
            raise
    
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def get_user_settings():
    """ユーザー設定を取得（デフォルト値付き）"""
    default_settings = {
        'target_name': '瓜田',
        'event_title': '図書館バイト📚',
        'event_location': '図書館',
        'color_id': '8',  # グレー（'9'から'8'に変更）
        'reminder_minutes': 10,
        'calendar_id': 'primary',
        'additional_reminder': False,
        'additional_reminder_minutes': 60,
        'event_description_template': 'シフト時間: {time}'
    }
    
    return session.get('settings', default_settings)

def create_calendar_event_from_shift(schedule_item, year, month, settings):
    """シフト情報を基に、Google カレンダーに登録するためのイベント辞書を作成"""
    date = schedule_item['date']
    time_str = schedule_item['time']
    
    # 時間範囲を解析
    time_match = re.search(
        r'(\d{1,2}):(\d{2})\s*[‐\-~〜～]\s*(\d{1,2}):(\d{2})',
        time_str
    )
    
    if time_match:
        start_hour = int(time_match.group(1))
        start_min = int(time_match.group(2))
        end_hour = int(time_match.group(3))
        end_min = int(time_match.group(4))
        
        # 24時間表記に変換（必要に応じて）
        if end_hour < start_hour:
            end_hour += 24
        
        start_time = f"{year}-{month}-{int(date):02d}T{start_hour:02d}:{start_min:02d}:00+09:00"
        end_time = f"{year}-{month}-{int(date):02d}T{end_hour:02d}:{end_min:02d}:00+09:00"
    else:
        # 時間形式が合わない場合のフォールバック
        start_time = f"{year}-{month}-{int(date):02d}T10:00:00+09:00"
        end_time = f"{year}-{month}-{int(date):02d}T12:00:00+09:00"
    
    # リマインダー設定
    reminders = {
        "useDefault": False,
        "overrides": [
            {"method": "popup", "minutes": int(settings.get('reminder_minutes', 10))}
        ]
    }
    
    # 追加リマインダーが有効な場合
    if settings.get('additional_reminder', False):
        reminders["overrides"].append(
            {"method": "popup", "minutes": int(settings.get('additional_reminder_minutes', 60))}
        )
    
    # 説明文のテンプレート処理
    description_template = settings.get('event_description_template', 'シフト時間: {time}')
    description = description_template.format(time=time_str)
    
    event = {
        "summary": settings.get('event_title', '図書館バイト'),
        "location": settings.get('event_location', '図書館'),
        "description": description,
        "start": {
            "dateTime": start_time,
            "timeZone": "Asia/Tokyo"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Asia/Tokyo"
        },
        "colorId": settings.get('color_id', '9'),
        "reminders": reminders
    }
    return event

####################################
# ルート定義
####################################

@app.route('/')
def index():
    """トップページ"""
    if 'credentials' not in session:
        return render_template('index.html')
    return redirect(url_for('upload_pdf'))

@app.route('/authorize')
def authorize():
    """Google認証開始"""
    try:
        # すでに認証済みの場合はアップロード画面へリダイレクト
        if 'credentials' in session:
            return redirect(url_for('upload_pdf'))
            
        init_session()  # セッション初期化
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URI
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            # 'prompt'パラメータを削除して、毎回の同意画面表示を防ぐ
            state=session['state']
        )
        
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"認証エラー: {e}")
        flash('認証プロセスでエラーが発生しました', 'error')
        return redirect(url_for('index'))

@app.route('/oauth2callback')
def oauth2callback():
    """Google認証コールバック"""
    try:
        # すでに認証済みの場合はアップロード画面へリダイレクト
        if 'credentials' in session:
            return redirect(url_for('upload_pdf'))
            
        # stateの取得前にセッションチェック
        if not session:
            logger.error("セッションが無効です")
            return redirect(url_for('authorize'))
            
        state = session.get('state')
        if not state:
            state = request.args.get('state')
            if not state:
                raise ValueError("認証状態が見つかりません")
        
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state)
        flow.redirect_uri = REDIRECT_URI
        
        try:
            flow.fetch_token(authorization_response=request.url)
        except Exception as e:
            logger.error(f"トークン取得エラー: {e}")
            raise
            
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        session.modified = True
        
        # トークンの有効期限をログに記録
        logger.info(f"認証成功: トークン有効期限 {credentials.expiry}")
        
        return redirect(url_for('upload_pdf'))
        
    except Exception as e:
        logger.error(f"認証エラー: {e}")
        flash('認証に失敗しました。もう一度お試しください。', 'error')
        return redirect(url_for('index'))

@app.route('/calendar/events')
@login_required
def list_events():
    """カレンダーイベント一覧表示"""
    try:
        service = get_calendar_service()
        settings = get_user_settings()
        calendar_id = settings.get('calendar_id', 'primary')
        
        # 現在の日付から1ヶ月分のイベントを取得
        now = datetime.utcnow().isoformat() + 'Z'
        one_month_later = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=one_month_later,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return render_template('events.html', events=events, settings=settings)
    
    except Exception as e:
        logger.error(f"イベント取得エラー: {e}")
        flash('カレンダーイベントの取得に失敗しました', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """ログアウト処理"""
    session.clear()
    flash('ログアウトしました', 'info')
    return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """設定画面"""
    current_settings = get_user_settings()
    
    if request.method == 'POST':
        # フォームから設定を更新
        new_settings = {
            'target_name': request.form.get('target_name', current_settings['target_name']),
            'event_title': request.form.get('event_title', current_settings['event_title']),
            'event_location': request.form.get('event_location', current_settings['event_location']),
            'color_id': request.form.get('color_id', current_settings['color_id']),
            'reminder_minutes': request.form.get('reminder_minutes', current_settings['reminder_minutes']),
            'calendar_id': request.form.get('calendar_id', current_settings['calendar_id']),
            'additional_reminder': 'additional_reminder' in request.form,
            'additional_reminder_minutes': request.form.get('additional_reminder_minutes', current_settings['additional_reminder_minutes']),
            'event_description_template': request.form.get('event_description_template', current_settings['event_description_template'])
        }
        session['settings'] = new_settings
        flash('設定を保存しました', 'success')
        return redirect(url_for('settings'))
    
    # カレンダーの色一覧
    calendar_colors = [
        ("赤紫", "1", "#7986cb"),
        ("緑", "2", "#33b679"),
        ("紫", "3", "#8e24aa"),
        ("ピンク", "4", "#e67c73"),
        ("黄", "5", "#f6c026"),
        ("オレンジ", "6", "#f5511d"),
        ("水色", "7", "#039be5"),
        ("グレー", "8", "#616161"),
        ("青", "9", "#3f51b5"),
        ("深緑", "10", "#0b8043"),
        ("赤", "11", "#d60000")
    ]
    
    # 利用可能なカレンダー一覧を取得
    calendars = []
    try:
        service = get_calendar_service()
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
    except Exception as e:
        logger.error(f"カレンダー一覧取得エラー: {e}")
        flash('カレンダー一覧の取得に失敗しました', 'warning')
    
    return render_template('settings.html', 
                          settings=current_settings, 
                          colors=calendar_colors,
                          calendars=calendars)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    """PDFアップロード画面"""
    settings = get_user_settings()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('ファイルが選択されていません', 'error')
            return render_template('upload.html', settings=settings)
        
        file = request.files['file']
        if file.filename == '':
            flash('ファイルが選択されていません', 'error')
            return render_template('upload.html', settings=settings)
        
        if not allowed_file(file.filename):
            flash('PDFファイルを選択してください', 'error')
            return render_template('upload.html', settings=settings)
        
        try:
            # ファイルを安全に保存
            filepath = handle_pdf_upload(file)
            
            # PDFを解析
            parser = PdfParser(settings['target_name'])
            
            # まずファイル名から年月を抽出
            year, month = parser.extract_year_month_from_filename(file.filename)
            if year and month:
                logger.info(f"ファイル名から年月を抽出: {year}年{month}月 (ファイル名: {file.filename})")
            
            # シフト情報を解析
            shifts = parser.parse_pdf(filepath)
            
            if not shifts:
                flash(f"シフト情報が見つかりませんでした。名前「{settings['target_name']}」が正しいか確認してください。", 'warning')
                return render_template('upload.html', settings=settings)
            
            # 年月が取得できなかった場合はPDFの内容から抽出
            if year is None or month is None:
                year, month = parser.extract_year_month(filepath)
                if year is None or month is None:
                    flash('ファイル名またはPDFの内容から年月を特定できませんでした。', 'warning')
                    return render_template('upload.html', settings=settings)
            
            # セッションに保存
            session['shifts'] = shifts
            session['year'] = year
            session['month'] = month
            session['pdf_path'] = filepath
            
            # 確認画面で年月を表示
            flash(f'{year}年{month}月のシフト情報を読み込みました', 'info')
            
            return redirect(url_for('confirm_shifts'))
            
        except Exception as e:
            logger.error(f"PDFアップロードエラー: {e}")
            flash('PDFの処理中にエラーが発生しました', 'error')
            return render_template('upload.html', settings=settings)
    
    return render_template('upload.html', settings=settings)

@app.route('/confirm', methods=['GET', 'POST'])
@login_required
def confirm_shifts():
    """抽出したシフト情報の確認画面"""
    if 'shifts' not in session or 'year' not in session or 'month' not in session:
        flash('シフト情報がありません。PDFをアップロードしてください。', 'warning')
        return redirect(url_for('upload_pdf'))
    
    shifts = session['shifts']
    year = session['year']
    month = session['month']
    settings = get_user_settings()
    
    if request.method == 'POST':
        # 選択されたシフトのみを処理
        selected_shifts = []
        for i, shift in enumerate(shifts):
            if request.form.get(f'shift_{i}', '') == 'on':
                selected_shifts.append(shift)
        
        if not selected_shifts:
            flash('登録するシフトが選択されていません', 'warning')
            return render_template('confirm.html', shifts=shifts, year=year, month=month, settings=settings)
        
        # 選択されたシフトをセッションに保存
        session['selected_shifts'] = selected_shifts
        return redirect(url_for('register_events'))
    
    return render_template('confirm.html', shifts=shifts, year=year, month=month, settings=settings)

@app.route('/register', methods=['GET'])
@login_required
def register_events():
    """選択したシフトをカレンダーに登録"""
    if 'selected_shifts' not in session or 'year' not in session or 'month' not in session:
        flash('シフト情報がありません', 'warning')
        return redirect(url_for('upload_pdf'))
    
    shifts = session['selected_shifts']
    year = session['year']
    month = session['month']
    settings = get_user_settings()
    
    try:
        service = get_calendar_service()
        calendar_id = settings.get('calendar_id', 'primary')
        
        results = []
        for shift in shifts:
            event = create_calendar_event_from_shift(shift, year, month, settings)
            created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            
            results.append({
                'date': shift['date'],
                'time': shift['time'],
                'event_id': created_event['id'],
                'html_link': created_event['htmlLink']
            })
        
        # 結果をセッションに保存
        session['register_results'] = results
        flash(f'{len(results)}件のシフトをカレンダーに登録しました', 'success')
        
        # 一時ファイルを削除
        if 'pdf_path' in session and os.path.exists(session['pdf_path']):
            os.remove(session['pdf_path'])
            del session['pdf_path']
        
        return render_template('result.html', results=results, settings=settings)
        
    except Exception as e:
        logger.error(f"カレンダー登録エラー: {e}")
        flash('カレンダーへの登録中にエラーが発生しました', 'error')
        return redirect(url_for('confirm_shifts'))

@app.route('/favicon.ico')
def favicon():
    """ファビコン"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                              'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.errorhandler(404)
def page_not_found(e):
    """404エラーハンドラ"""
    return render_template('error.html', error_code=404, message="ページが見つかりません"), 404

@app.errorhandler(Exception)
def handle_exception(e):
    """グローバルエラーハンドラ"""
    logger.error(f"予期せぬエラー: {e}")
    return render_template('error.html', 
                         error_code=500,
                         message="予期せぬエラーが発生しました"), 500

def safe_remove_file(file_path):
    """安全にファイルを削除"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"ファイル削除エラー: {e}")

def handle_pdf_upload(file):
    """PDFファイルの処理（Vercel環境対応）"""
    if os.getenv('VERCEL_ENV') == 'production':
        # 一時ディレクトリを使用
        temp_dir = '/tmp'
        filename = secure_filename(file.filename)
        filepath = os.path.join(temp_dir, filename)
    else:
        # 通常の環境
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    file.save(filepath)
    return filepath

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
