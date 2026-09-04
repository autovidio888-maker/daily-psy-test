import os
import json
import time
import requests

THREADS_USER_ID = os.environ.get("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.environ.get("THREADS_ACCESS_TOKEN")

def post_to_threads():
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        print("未偵測到 THREADS_USER_ID 或 THREADS_ACCESS_TOKEN，跳過 Threads 發文步驟。")
        return

    quiz_file = "public/data/daily_quiz.json"
    if not os.path.exists(quiz_file):
        print("找不到 daily_quiz.json 檔案。")
        return

    with open(quiz_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    post_text = data.get("threads_post")
    if not post_text:
        theme = data.get("theme", "今日心理測驗")
        post_text = f"笑死，今天這個測驗根本是在裝監視器吧\n今日主題【{theme}】\n\n測驗連結在這邊 👉 https://daydayquiz.com\n測完留言說你是哪隻，看我們是不是相剋雷區🙂\n\n#心理測驗 #今日限定"

    print("即將發布至 Threads 的內容：\n", post_text)

    # 步驟 1: 建立貼文容器 (Container)
    create_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    payload = {
        "media_type": "TEXT",
        "text": post_text,
        "access_token": THREADS_ACCESS_TOKEN
    }
    
    try:
        res1 = requests.post(create_url, data=payload, timeout=20)
        res1_data = res1.json()
        creation_id = res1_data.get("id")

        if not creation_id:
            print("建立 Threads Container 失敗：", res1_data)
            return

        # 緩衝 5 秒等待 Meta 伺服器同步
        time.sleep(5)

        # 步驟 2: 發布貼文
        publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
        pub_payload = {
            "creation_id": creation_id,
            "access_token": THREADS_ACCESS_TOKEN
        }

        res2 = requests.post(publish_url, data=pub_payload, timeout=20)
        res2_data = res2.json()

        if "id" in res2_data:
            print(f"🎉 成功發布到 Threads！Post ID: {res2_data['id']}")
        else:
            print("Threads 發布失敗：", res2_data)

    except Exception as e:
        print(f"執行發布 Threads 時發生異常: {e}")

if __name__ == "__main__":
    post_to_threads()
