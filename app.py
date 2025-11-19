from flask import Flask, render_template_string, request
from news_to_sheet import main as run_news_collection

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>ニュース収集ツール</title>
</head>
<body>
  <h1>ニュース収集ツール</h1>
  <p>スプレッドシートに最新のニュースを追加します。</p>

  <form method="post">
    <button type="submit">今すぐニュースを収集する</button>
  </form>

  {% if message %}
    <p style="margin-top:20px;">{{ message }}</p>
  {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
  message = ""
  if request.method == "POST":
    try:
      run_news_collection()  # news_to_sheet.main() を実行
      message = "ニュース収集が完了しました。"
    except Exception as e:
      message = f"エラーが発生しました: {e}"

  return render_template_string(HTML, message=message)


if __name__ == "__main__":
  # ローカル開発用サーバ（自分のPCからだけアクセス）
  app.run(host="127.0.0.1", port=5000, debug=True)
