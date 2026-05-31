# app.py（完成版）

from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import unicodedata

app = Flask(__name__)

# ----------------------------
# Selenium設定
# ----------------------------
options = Options()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")


# ----------------------------
# HTML
# ----------------------------
def render_form():
  return """
    <div style="text-align:center;">
        <h2>東京マルイ検索システム</h2>

        <form action="/" method="POST">
            <input type="text" name="searchWord" placeholder="検索ワード"><br><br>

            <input type="radio" name="sort" value="1" checked>
            発売日順

            <input type="radio" name="sort" value="2">
            価格（降順）

            <input type="radio" name="sort" value="3">
            価格（昇順）

            <br><br>
            <input type="submit" value="検索">
        </form>
    </div>
    """


# ----------------------------
# 全角文字幅
# ----------------------------
def get_east_asian_width(text):
  total_width = 0

  for char in text:
    status = unicodedata.east_asian_width(char)

    if status in ("W", "F", "A"):
      total_width += 1.4
    else:
      total_width += 1

  return int(total_width + 0.5)


# ----------------------------
# メイン処理
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def searching():

  if request.method == "GET":
    return render_form()

  search_word = request.form.get("searchWord", "").strip()
  sort_option = request.form.get("sort", "1")

  if not search_word:
    return render_form() + "<p>検索ワードを入力してください</p>"

  driver = None

  try:
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.get("https://www.tokyo-marui.co.jp/")

    # 検索ワード入力
    script = """
        var keyword = arguments[0];
        var targets = document.getElementsByName('productname');

        for (var i = 0; i < targets.length; i++) {
            targets[i].value = keyword;

            var form = targets[i].closest('form');

            if (form) {
                form.submit();
                break;
            }
        }
        """

    driver.execute_script(script, search_word)

    # 並び替え
    if sort_option in ["1", "2", "3"]:
      wait = WebDriverWait(driver, 10)

      select_element = wait.until(
          EC.presence_of_element_located(
              (By.CSS_SELECTOR, "dl dd select")
          )
      )

      Select(select_element).select_by_value(sort_option)

    # 商品待機
    wait = WebDriverWait(driver, 10)

    wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR,
             "li.sw-Card_Products-Type1_Item")
        )
    )

    items = driver.find_elements(
        By.CSS_SELECTOR,
        "li.sw-Card_Products-Type1_Item"
    )

    products_data = []
    len_max = 0

    # 最大文字幅
    for item in items:
      try:
        name = item.find_element(
            By.CSS_SELECTOR,
            "h3 a"
        ).text.strip()

        length = get_east_asian_width(name)

        len_max = max(len_max, length)

      except:
        continue

    count = 1

    for item in items:
      try:
        sells = item.find_element(
            By.CSS_SELECTOR,
            "span, .category, .type"
        ).text.strip()

        name = item.find_element(
            By.CSS_SELECTOR,
            "h3 a"
        ).text.strip()

        price = item.find_element(
            By.CSS_SELECTOR,
            "div p strong"
        ).text.strip()

        url = item.find_element(
            By.CSS_SELECTOR,
            "a"
        ).get_attribute("href")

        category = url.split("/")[-3]

        category_map = {
            "electric": "電動ガン",
            "gas": "ガスガン",
            "aircocking": "エアコキ"
        }

        category = category_map.get(
            category,
            "その他"
        )

        if search_word.lower() in name.lower():

          padding = (
              "⠀" *
              (
                  len_max
                  - get_east_asian_width(name)
                  + 2
              )
          )

          products_data.append(
              f"""
                        {count}.
                        【{sells}】
                        [{category}]
                        {name}
                        {padding}
                        |
                        {price}
                        <a href="{url}" target="_blank">
                        製品リンク
                        </a>
                        """
          )

          count += 1

      except Exception as e:
        print(e)

    result_text = (
        "<br>".join(products_data)
        if products_data
        else "該当なし"
    )

    return f"""
        {render_form()}
        <hr>

        <div style="padding:20px;">
            <h3>「{search_word}」の検索結果</h3>
            <p>{result_text}</p>
        </div>
        """

  except Exception as e:
    return f"""
        {render_form()}
        <p>エラーが発生しました</p>
        <pre>{str(e)}</pre>
        """

  finally:
    if driver:
      driver.quit()


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
