# News Collector Tool

RSSフィードから最新のニュースを自動収集し、Google スプレッドシートへ集約・翻訳・整形成形するツールです。
Pythonによるバックエンド収集と、Google Apps Script (GAS) によるスプレッドシート上での操作の両方に対応しています。

## 特徴

- **マルチソース収集**: ITmedia、TechCrunch、東洋経済、NHKなどの主要なRSSフィードからニュースを取得。
- **Google Sheets 連携**: 収集したデータをGoogleスプレッドシートに自動的に書き込みます。
- **自動翻訳**: GASを利用して、英語記事のタイトルや概要を日本語に自動翻訳します。
- **UI/UX**: GASによるカスタムメニューから、スプレッドシート上で直接ニュース更新や整形が可能です。
- **Flask Web UI**: PythonスクリプトをWebブラウザから実行するためのシンプルなインターフェースを搭載。

## システム構成

- **Python**: RSSのパース、スプレッドシートへのデータ送信 (`gspread`)。
- **Flask**: ローカル環境での実行用Web UI。
- **Google Apps Script (GAS)**: スプレッドシート内での自動翻訳、UI操作。
- **Google Sheets API**: プログラムからのスプレッドシート操作。

## セットアップ

### 1. リポジトリのクローン
```bash
git clone https://github.com/YourUsername/news_collector-tool.git
cd news_collector-tool
```

### 2. Python環境の設定
```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env を編集し、Google Cloud のサービスアカウントキーとスプレッドシートIDを設定してください。
```

### 3. Google Apps Script の設定
1. Google スプレッドシートを作成し、IDをコピーします。
2. 「拡張機能」 > 「Apps Script」を選択します。
3. `google_script_news_.js` の内容をコピー＆ペーストして保存します。
4. スプレッドシートをリロードすると、「ニュース更新」メニューが表示されます。

## 使い方

### Python (Flask) から実行
```bash
python app.py
```
ブラウザで `http://127.0.0.1:5000` にアクセスし、「今すぐニュースを収集する」ボタンを押すとスプレッドシートに最新ニュースが追加されます。

### スプレッドシートから実行
スプレッドシート上部の「ニュース更新」メニューから「最新ニュースを取得」をクリックします。

## ライセンス

[MIT License](LICENSE)
