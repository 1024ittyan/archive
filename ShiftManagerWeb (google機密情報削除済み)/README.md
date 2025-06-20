# ShiftManagerWeb

PDFフォーマットのシフト表からシフト情報を抽出し、Googleカレンダーに自動登録するウェブアプリケーションです。

## 機能

- PDFシフト表からの自動シフト情報抽出
- Googleカレンダーへの簡単登録
- 複数のPDFフォーマットに対応
- カスタマイズ可能なイベント設定
- モバイルフレンドリーなUI

## 必要条件

- Python 3.7以上
- Google APIクライアントID（OAuth 2.0）

## インストール

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/ShiftManagerWeb.git
cd ShiftManagerWeb
```

2. 仮想環境を作成して有効化
```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
venv\Scripts\activate     # Windowsの場合
```

3. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

4. Google API認証情報を設定
   - [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
   - OAuth 2.0クライアントIDを作成
   - 認証情報をダウンロードし、`client_secret.json`として保存

## 使い方

1. アプリケーションを起動
```bash
python app.py
```

2. ブラウザで http://localhost:5000 にアクセス

3. Googleアカウントでログイン

4. シフト表のPDFをアップロード

5. 抽出されたシフト情報を確認

6. カレンダーに登録

## 設定

アプリケーション内の設定ページから以下の項目をカスタマイズできます：

- 検索対象の名前
- イベントタイトル
- イベントの場所
- カレンダーの色
- リマインダー設定
- 使用するカレンダー

## 対応しているPDFフォーマット

- テーブル形式のシフト表
- テキスト形式のシフト表
- 日付と時間が含まれているPDF

## 開発者向け情報

### プロジェクト構造

```
ShiftManagerWeb/
├── app.py              # メインアプリケーション
├── pdf_parser.py       # PDFパーサー
├── config.py           # 設定
├── requirements.txt    # 依存パッケージ
├── static/             # 静的ファイル
│   ├── css/            # スタイルシート
│   ├── js/             # JavaScript
│   └── images/         # 画像
├── templates/          # HTMLテンプレート
└── uploads/            # アップロードされたファイル（一時）
```

### 依存パッケージ

- Flask: ウェブフレームワーク
- pdfplumber: PDF解析
- google-auth, google-auth-oauthlib, google-api-python-client: Google API

## ライセンス

MIT

## 作者

Soichiro Urita

## 謝辞

- [Flask](https://flask.palletsprojects.com/)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [Google Calendar API](https://developers.google.com/calendar)
- [Bootstrap](https://getbootstrap.com/) 
