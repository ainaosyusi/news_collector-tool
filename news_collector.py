import feedparser
import pandas as pd
from datetime import datetime
from pathlib import Path

# ---- 1. 収集するRSSフィードの一覧 ----
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
    # TODO: あとでここにサイトをどんどん追加していく
]

# ---- 2. 既存のCSVを読み込み、既に登録済みのURLをセットで保持 ----
CSV_PATH = Path("news_log.csv")

if CSV_PATH.exists():
    df_existing = pd.read_csv(CSV_PATH)
    known_urls = set(df_existing["link"].astype(str))
else:
    df_existing = pd.DataFrame()
    known_urls = set()

new_rows = []

# ---- 3. 各RSSフィードを読み込んで、記事を取得 ----
for feed_info in FEEDS:
    print(f"Fetching: {feed_info['site']} - {feed_info['category']}")
    d = feedparser.parse(feed_info["url"])

    for entry in d.entries:
        link = entry.get("link", "")

        # すでに登録済みならスキップ
        if link in known_urls:
            continue

        title = entry.get("title", "")
        summary = entry.get("summary", "")

        # 公開日時を文字列に整形（無ければ今の時刻）
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
        else:
            dt = datetime.now()

        published = dt.strftime("%Y-%m-%d %H:%M:%S")

        row = {
            "datetime": published,
            "site": feed_info["site"],
            "category": feed_info["category"],
            "title": title,
            "summary": summary,
            "link": link,
        }
        new_rows.append(row)
        known_urls.add(link)

# ---- 4. CSVに書き出し ----
if new_rows:
    df_new = pd.DataFrame(new_rows)

    # 既存データがあれば結合してソート（新しい順）
    if not df_existing.empty:
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all = df_all.sort_values("datetime", ascending=False)

    df_all.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"Added {len(new_rows)} new articles. Total: {len(df_all)}")
else:
    print("No new articles.")
