import os
import json
import re
import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("找不到 GEMINI_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

prompt = """
你是一個專門打造社群瘋傳心理測驗的心理學專家與視覺設計師。請設計一個適合在 Threads / IG 引發病毒式轉發的趣味心理測驗。
主題可以多樣化（例如：職場摸魚生物、咖啡靈魂圖鑑、奇幻冒險職業、深夜消夜人格、貓狗社交屬性等）。

【核心規範 1：巴納姆效應深度剖析 (Barnum Effect)】
在每個結果的 "analysis" 中，必須深度運用巴納姆效應（結合矛盾但普遍共鳴的人性特質，例如：外表獨立但渴望被理解、平時隨和但對特定細節極度執著、社交電量看似滿格其實回家只想放空等），寫出一段約 80-120 字、直擊心靈讓人驚呼「這根本就是我本人！」的精準解析。

【核心規範 2：Threads 爆款引流文案（嚴禁 AI 味）】
請以一個「每天在 Threads 上衝浪、講話微厭世自嘲但幽默的 20 幾歲脆友」口吻，寫一篇發在 Threads 的推廣貼文（填入 "threads_post" 欄位）：
- 嚴禁出現「親愛的朋友」、「快來測測看」、「歡迎留言分享」、「今天為大家帶來」等八股公版機器人語氣。
- 開頭直接用一句大實話、社畜吐槽或自嘲破題（例如：「笑死，測完直接被看穿...」、「到底誰上班不摸魚...」）。
- 帶出今天的測驗主題與其中一隻搞笑/扎心的角色稱號。
- 引導大家點進測驗，並留言報上自己的角色（例如：「連結放下面，測完跟我說你是哪隻，看看我們今天是不合還是命定」）。
- 附帶網址 https://daydayquiz.com 與標籤 #心理測驗 #今日限定。
- 善用自然斷句與換行，總字數 150 字以內。

請嚴格只輸出合法的 JSON 格式（不要有 markdown 標記、不要用 ```json 包裹），格式規範如下：
{
  "theme": "測驗主題名稱",
  "threads_post": "Threads 專屬爆款自然文案...",
  "questions": [
    {
      "id": 1,
      "title": "題目敘述",
      "options": [
        { "text": "選項A", "type": "A" },
        { "text": "選項B", "type": "B" },
        { "text": "選項C", "type": "C" },
        { "text": "選項D", "type": "D" }
      ]
    }
  ],
  "results": {
    "A": {
      "title": "稱號A",
      "tagline": "短梗副稱號",
      "emoji": "🦊",
      "avatar_seed": "fox",
      "color": "from-amber-400 to-orange-500",
      "quote": "金句",
      "analysis": "巴納姆效應深度解析內容...",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號B",
      "worstMatch": "稱號D"
    },
    "B": {
      "title": "稱號B",
      "tagline": "短梗副稱號",
      "emoji": "🐼",
      "avatar_seed": "panda",
      "color": "from-teal-400 to-emerald-500",
      "quote": "金句",
      "analysis": "巴納姆效應深度解析內容...",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號A",
      "worstMatch": "稱號C"
    },
    "C": {
      "title": "稱號C",
      "tagline": "短梗副稱號",
      "emoji": "🐱",
      "avatar_seed": "cat",
      "color": "from-indigo-400 to-purple-500",
      "quote": "金句",
      "analysis": "巴納姆效應深度解析內容...",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號D",
      "worstMatch": "稱號B"
    },
    "D": {
      "title": "稱號D",
      "tagline": "短梗副稱號",
      "emoji": "🐰",
      "avatar_seed": "rabbit",
      "color": "from-rose-400 to-pink-500",
      "quote": "金句",
      "analysis": "巴納姆效應深度解析內容...",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號C",
      "worstMatch": "稱號A"
    }
  }
}
請確保 questions 剛好有 6 題。
"""

response = model.generate_content(prompt)
raw_text = response.text.strip()

raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
raw_text = re.sub(r"^```\s*", "", raw_text, flags=re.MULTILINE)
raw_text = re.sub(r"```$", "", raw_text, flags=re.MULTILINE)

quiz_data = json.loads(raw_text.strip())

os.makedirs("public/data", exist_ok=True)
with open("public/data/daily_quiz.json", "w", encoding="utf-8") as f:
    json.dump(quiz_data, f, ensure_ascii=False, indent=2)

print("今日心理測驗及 Threads 文案生成成功！")
