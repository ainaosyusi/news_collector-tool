import os
import feedparser
from datetime import datetime

from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials


# =========================
# 1. .env 読み込み
# =========================
load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

if not SERVICE_ACCOUNT_FILE:
    raise RuntimeError("ERROR: GOOGLE_CREDENTIALS が .env に設定されていません")
if not SPREADSHEET_ID:
    raise RuntimeError("ERROR: SPREADSHEET_ID が .env に設定されていません")


# =========================
# 2. カテゴリとRSSフィード定義
# =========================

# カテゴリ -> シート名
CATEGORY_SHEETS = {
    "IT": "ITニュース",
    "ECONOMY": "経済ニュース",
    "GENERAL": "一般ニュース",
}

# RSSフィード一覧
FEEDS = [
    # IT 系
    {
        "site": "ITmedia",
        "top_category": "IT",
        "feed_category": "ITmedia 総合",
        "url": "https://rss.itmedia.co.jp/rss/2.0/itmedia_all.xml",
    },
    {
        "site": "TechCrunch",
        "top_category": "IT",
        "feed_category": "TechCrunch Global",
        "url": "https://techcrunch.com/feed/",
    },

    # 経済系
    {
        "site": "東洋経済オンライン",
        "top_category": "ECONOMY",
        "feed_category": "総合",
        "url": "http://toyokeizai.net/list/feed/rss",
    },
    {
        "site": "ダイヤモンド・オンライン",
        "top_category": "ECONOMY",
        "feed_category": "総合",
        "url": "https://diamond.jp/list/feed/rss",
    },

    # 一般ニュース（NHK主要）
    {
        "site": "NHK",
        "top_category": "GENERAL",
        "feed_category": "主要ニュース",
        "url": "http://www3.nhk.or.jp/rss/news/cat0.xml",
    },
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


def ensure_worksheet(sheet_title: str):
    """指定タイトルのワークシートを取得（無ければ作成）"""
    try:
        ws = sh.worksheet(sheet_title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_title, rows="2000", cols="10")
    return ws


def setup_header(ws):
    """
    ヘッダー行を整える。
    戻り値:
      header: ヘッダーリスト
      known_urls: 既存URLの set
    """
    rows = ws.get_all_values()
    header = [
        "datetime",      # 0
        "site",          # 1
        "feed_category", # 2
        "title",         # 3
        "summary",       # 4 (RSS summary)
        "link",          # 5
    ]

    if not rows:
        ws.append_row(header)
        return header, set()

    current_header = rows[0]
    # 列構成が違っていたら上書きして揃える
    if current_header != header:
        ws.update(range_name="A1:F1", values=[header])

    # 既存URL集合
    link_col_index = header.index("link")
    known_urls = set()
    for r in rows[1:]:
        if len(r) > link_col_index:
            known_urls.add(r[link_col_index])

    return header, known_urls


def collect_for_category(top_category: str):
    """
    カテゴリ単位でRSSを読んで、対応するシートに新着を書き込む
    """
    sheet_title = CATEGORY_SHEETS[top_category]
    ws = ensure_worksheet(sheet_title)
    header, known_urls = setup_header(ws)

    new_rows = []

    # 該当カテゴリのフィードだけ回す
    for feed_info in [f for f in FEEDS if f["top_category"] == top_category]:
        print(f"[{top_category}] Fetching: {feed_info['site']} - {feed_info['feed_category']}")
        feed = feedparser.parse(feed_info["url"])

        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in known_urls:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")

            if hasattr(entry, "published_parsed") and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6])
            else:
                dt = datetime.now()

            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")

            row = [
                dt_str,
                feed_info["site"],
                feed_info["feed_category"],
                title,
                summary,
                link,
            ]
            new_rows.append(row)
            known_urls.add(link)

    if new_rows:
        ws.append_rows(new_rows)
        print(f"[{top_category}] Added {len(new_rows)} new articles.")
    else:
        print(f"[{top_category}] No new articles.")


def main():
    for cat in CATEGORY_SHEETS.keys():
        collect_for_category(cat)


if __name__ == "__main__":
    main()
