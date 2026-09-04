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
你是一個爆款社群心理測驗與視覺設計師。請設計一個適合在 Threads / IG 引發轉發的趣味心理測驗。
主題可以多樣化（例如：職場摸魚生物、咖啡性格圖鑑、奇幻冒險職業、貓狗社交屬性、消夜靈魂人格等）。

除了題目外，請為 A, B, C, D 四種測驗結果分別設計一個專屬的「超可愛治癒系代表角色」。
為了生成專屬的可愛插圖，請為每個結果提供：
1. "emoji": 一個代表性的可愛 Emoji。
2. "tagline": 一句超有梗的副標題（例如「躺平系摸魚王」）。
3. "avatar_seed": 一個能代表該角色的簡短英文單字（用於生成專屬可愛頭像，例如 "cat", "wizard", "fox", "bear", "coffee", "sparkle"）。
4. "color": 專屬漸層顏色（例如 "from-amber-400 to-orange-500", "from-pink-400 to-rose-500", "from-teal-400 to-emerald-500", "from-indigo-400 to-purple-500"）。

請嚴格只輸出合法的 JSON 格式（不要有 markdown 標記、不要用 ```json 包裹），格式規範如下：
{
  "theme": "測驗主題名稱",
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
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號D",
      "worstMatch": "稱號B"
    },
    "D": {
      "title": "稱號D",
      "tagline": "短梗副稱號",
      "emoji": "🐰",
      "avatar_seed": "bunny",
      "color": "from-rose-400 to-pink-500",
      "quote": "金句",
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

print("今日心理測驗生成成功！")
