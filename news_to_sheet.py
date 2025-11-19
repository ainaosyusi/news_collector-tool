import os
import feedparser
import pandas as pd
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# =========================
# 1. .env 読み込み
# =========================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "シート1")

if not SERVICE_ACCOUNT_FILE:
    raise RuntimeError("ERROR: GOOGLE_CREDENTIALS が .env に設定されていません")
if not SPREADSHEET_ID:
    raise RuntimeError("ERROR: SPREADSHEET_ID が .env に設定されていません")


# =========================
# 2. RSS フィード一覧
# =========================
FEEDS = [
    {
        "site": "NHK",
        "category": "主要ニュース",
        "url": "http://www3.nhk.or.jp/rss/news/cat0.xml",
    },
    {
        "site": "ITmedia",
        "category": "総合",
        "url": "https://rss.itmedia.co.jp/rss/2.0/itmedia_all.xml",
    },
    # 今後ここに追加していく
]


# =========================
# 3. Google 認証
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES,
)

gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)

# ワークシートを開く（無ければ作る）
try:
    ws = sh.worksheet(WORKSHEET_NAME)
except gspread.exceptions.WorksheetNotFound:
    ws = sh.add_worksheet(title=WORKSHEET_NAME, rows="2000", cols="10")


# =========================
# 4. 既存データ読み込み（重複防止）
# =========================
rows = ws.get_all_values()

if len(rows) == 0:
    header = ["datetime", "site", "category", "title", "summary", "link"]
    ws.append_row(header)
    known_urls = set()

else:
    header = rows[0]
    if "link" in header:
        link_col = header.index("link")
        known_urls = set(
            r[link_col] for r in rows[1:] if len(r) > link_col
        )
    else:
        header = ["datetime", "site", "category", "title", "summary", "link"]
        ws.update("A1:F1", [header])
        known_urls = set()


# =========================
# 5. RSS 新着取得
# =========================
new_rows = []

for feed_info in FEEDS:
    print(f"Fetching: {feed_info['site']} - {feed_info['category']}")

    feed = feedparser.parse(feed_info["url"])

    for entry in feed.entries:
        link = entry.get("link", "")

        # すでに登録済みはスキップ
        if link in known_urls:
            continue

        title = entry.get("title", "")
        summary = entry.get("summary", "")

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
        else:
            dt = datetime.now()

        row = [
            dt.strftime("%Y-%m-%d %H:%M:%S"),
            feed_info["site"],
            feed_info["category"],
            title,
            summary,
            link,
        ]

        new_rows.append(row)
        known_urls.add(link)

# =========================
# 6. スプレッドシートに追加
# =========================
if new_rows:
    ws.append_rows(new_rows)
    print(f"Added {len(new_rows)} new articles!")
else:
    print("No new articles.")
