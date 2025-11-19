// =======================================================
// スプレッドシート用 ニュース収集 + 日本語訳 + 整形 完成版
// =======================================================

// ------- 設定 -------

// RSSフィード一覧
const FEEDS = [
    // IT
    { site: "ITmedia",    catCode: "IT",       url: "https://rss.itmedia.co.jp/rss/2.0/itmedia_all.xml" },
    { site: "TechCrunch", catCode: "IT",       url: "https://techcrunch.com/feed/" },
  
    // 経済
    { site: "東洋経済",     catCode: "ECONOMY", url: "http://toyokeizai.net/list/feed/rss" },
    { site: "ダイヤモンド", catCode: "ECONOMY", url: "https://diamond.jp/list/feed/rss" },
  
    // 一般
    { site: "NHK",         catCode: "GENERAL", url: "http://www3.nhk.or.jp/rss/news/cat0.xml" },
  ];
  
  // カテゴリコード → シート名
  const SHEET_MAP = {
    IT: "ITニュース",
    ECONOMY: "経済ニュース",
    GENERAL: "一般ニュース",
  };
  
  
  // =======================================================
  // 1. シートを開いた時にメニューを追加
  // =======================================================
  function onOpen() {
    const ui = SpreadsheetApp.getUi();
  
    ui.createMenu("ニュース更新")
      .addItem("最新ニュースを取得", "updateNews")
      .addItem("シート整形", "formatSheets")
      .addItem("既存データに翻訳を付与", "translateExistingRows")
      .addToUi();
  }
  
  
  // =======================================================
  // 2. RSS からニュース取得＋シート追記（日本語訳つき）
  // =======================================================
  function updateNews() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
  
    FEEDS.forEach(feed => {
      const sheetName = SHEET_MAP[feed.catCode];
      if (!sheetName) return;
  
      let sheet = ss.getSheetByName(sheetName);
      if (!sheet) {
        sheet = ss.insertSheet(sheetName);
      }
  
      // ヘッダーが無い場合は1行目に追加
      if (sheet.getLastRow() === 0) {
        sheet.appendRow([
          "datetime", "site", "feed_category", "title",
          "summary", "link", "translated"
        ]);
      }
  
      // 既存リンク（F列）を取得して重複チェック用セットに
      const lastRow = sheet.getLastRow();
      let existingLinks = new Set();
      if (lastRow >= 2) {
        const linkValues = sheet.getRange(2, 6, lastRow - 1, 1).getValues();
        linkValues.forEach(row => {
          const v = row[0];
          if (v) existingLinks.add(v);
        });
      }
  
      // RSS取得
      let xmlText;
      try {
        xmlText = UrlFetchApp.fetch(feed.url).getContentText("UTF-8");
      } catch (e) {
        Logger.log("Fetch error: " + feed.url + " / " + e);
        return;
      }
  
      // scriptタグを削除（XMLパーサ対策）
      xmlText = xmlText.replace(/<script[\s\S]*?<\/script>/gi, "");
  
      // XMLパース
      let doc;
      try {
        doc = XmlService.parse(xmlText);
      } catch (e) {
        Logger.log("XML parse error: " + feed.url + " / " + e);
        return;
      }
  
      const root = doc.getRootElement();
      const rootName = root.getName();
      const ns = root.getNamespace();
      let items = [];
  
      if (rootName === "rss") {
        const channel = root.getChild("channel");
        if (!channel) return;
        items = channel.getChildren("item");
      } else if (rootName === "feed") {
        // Atom形式
        items = root.getChildren("entry", ns);
      } else {
        Logger.log("Unknown feed root: " + rootName);
        return;
      }
  
      let added = 0;
  
      items.forEach(item => {
        let title = "", desc = "", link = "", dateStr = "";
  
        if (rootName === "rss") {
          title   = getChildText(item, "title");
          desc    = getChildText(item, "description");
          link    = getChildText(item, "link");
          dateStr = getChildText(item, "pubDate");
        } else {
          // Atom
          title = getChildTextNS(item, "title", ns);
          desc  = getChildTextNS(item, "summary", ns) ||
                  getChildTextNS(item, "content", ns);
  
          const linkElem = item.getChild("link", ns);
          if (linkElem && linkElem.getAttribute("href")) {
            link = linkElem.getAttribute("href").getValue();
          }
  
          dateStr = getChildTextNS(item, "updated", ns) ||
                    getChildTextNS(item, "published", ns);
        }
  
        if (!link) return;
        if (existingLinks.has(link)) return;  // すでに登録済み
  
        // 日付
        let pubDate = dateStr ? new Date(dateStr) : new Date();
        if (isNaN(pubDate.getTime())) pubDate = new Date();
  
        // 日本語訳（タイトル＋概要をまとめて翻訳）
        let translated = "";
        try {
          translated = LanguageApp.translate(
            (title || "") + "\n\n" + (desc || ""),
            "auto",
            "ja"
          );
        } catch (e) {
          translated = "";
        }
  
        // 1行分のデータ
        const row = [
          pubDate,
          feed.site,
          feed.catCode, // feed_category 列（IT / ECONOMY / GENERAL）
          title,
          desc,
          link,
          translated
        ];
  
        sheet.appendRow(row);
        existingLinks.add(link);
        added++;
      });
  
      Logger.log(sheetName + " に " + added + " 件追加");
    });
  
    SpreadsheetApp.getUi().alert("最新ニュースの取得が完了しました。");
  }
  
  
  // =======================================================
  // 3. シートの見た目を整える
  // =======================================================
  function formatSheets() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheets = ["ITニュース", "経済ニュース", "一般ニュース"];
  
    sheets.forEach(name => {
      const sheet = ss.getSheetByName(name);
      if (!sheet) return;
  
      // 既存の交互背景色を全部削除
      const bandings = sheet.getBandings();
      bandings.forEach(b => b.remove());
  
      // ヘッダー固定
      sheet.setFrozenRows(1);
  
      // ヘッダーのスタイル
      sheet.getRange("A1:G1")
        .setFontWeight("bold")
        .setBackground("#f5f5f5");  // 薄いグレー
  
      // 列幅自動調整
      sheet.autoResizeColumns(1, 7);
  
      // データ部分に交互の背景色
      const last = sheet.getLastRow();
      if (last > 1) {
        const dataRange = sheet.getRange(2, 1, last - 1, 7);
        dataRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY);
      }
  
      // タイトル・概要・翻訳を折り返し表示
      sheet.getRange("D:E").setWrap(true);
      sheet.getRange("G:G").setWrap(true);
    });
  
    SpreadsheetApp.getUi().alert("シートの整形が完了しました。");
  }
  
  
  // =======================================================
  // 4. 既存データにも翻訳をまとめて付与したいとき用
  //    （あとから導入したとき用の一括処理）
  // =======================================================
  function translateExistingRows() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getActiveSheet();  // 今開いているシートに対して実行
  
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return;
  
    const titles   = sheet.getRange(2, 4, lastRow - 1, 1).getValues(); // D列
    const summaries= sheet.getRange(2, 5, lastRow - 1, 1).getValues(); // E列
    const result   = [];
  
    for (let i = 0; i < titles.length; i++) {
      const title = titles[i][0] || "";
      const summary = summaries[i][0] || "";
      let translated = "";
  
      if (title || summary) {
        try {
          translated = LanguageApp.translate(
            title + "\n\n" + summary,
            "auto",
            "ja"
          );
        } catch (e) {
          translated = "";
        }
      }
      result.push([translated]);
    }
  
    sheet.getRange(2, 7, result.length, 1).setValues(result);
    SpreadsheetApp.getUi().alert("既存データへの翻訳付与が完了しました。");
  }
  
  
  // =======================================================
  // 5. XML ヘルパー
  // =======================================================
  function getChildText(elem, name) {
    const c = elem.getChild(name);
    return c ? c.getText() : "";
  }
  
  function getChildTextNS(elem, name, ns) {
    const c = elem.getChild(name, ns);
    return c ? c.getText() : "";
  }
  