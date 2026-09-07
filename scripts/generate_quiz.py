import os
import json
import random
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

QUIZ_TYPES = ["workplace_quiz", "tarot_quiz", "love_quiz", "personality_quiz"]
selected_type = random.choice(QUIZ_TYPES)

prompt = f"""
你是一個精通社群病毒式行銷與心理學的測驗設計師。請生成一個今日限定測驗，類型為：{selected_type}。
嚴格遵守以下 JSON 格式輸出，不要包含任何 markdown 標記（如 ```json），只輸出純 JSON 字串：

{{
  "quiz_type": "{selected_type}",
  "theme": "吸睛主題標題（15字內，例如：職場甩鍋防禦率檢測）",
  "subtitle": "一句扎心有共鳴的引言（例如：上班最累的不是做事，而是演情緒穩定）",
  "questions": [
    {{
      "id": 1,
      "label": "狀態偵測",
      "title": "題目內容（情境化、社畜或生活感強烈）",
      "options": [
        {{"text": "選項 A 描述", "type": "A"}},
        {{"text": "選項 B 描述", "type": "B"}},
        {{"text": "選項 C 描述", "type": "C"}},
        {{"text": "選項 D 描述", "type": "D"}}
      ]
    }}
  ],
  "results": {{
    "A": {{
      "title": "角色名稱",
      "emoji": "🎭",
      "tagline": "短標籤",
      "quote": "一句代表角色的金句",
      "rarity": "SSR",
      "energy": "45%",
      "social": "30%",
      "analysis": "角色深入解析，100字左右",
      "tip": "今日生存建議",
      "bestMatch": "契合角色名",
      "worstMatch": "相剋角色名"
    }},
    "B": {{ ... }},
    "C": {{ ... }},
    "D": {{ ... }}
  }}
}}

注意：
1. questions 必須剛好 6 題。
2. results 必須包含 A, B, C, D 四種。
3. 嚴格輸出純 JSON，禁止包含任何外層解釋文字。
"""

response = model.generate_content(prompt)
raw_text = response.text.strip()

if raw_text.startswith("```json"):
    raw_text = raw_text[7:]
if raw_text.startswith("```"):
    raw_text = raw_text[3:]
if raw_text.endswith("```"):
    raw_text = raw_text[:-3]

data = json.loads(raw_text.strip())

os.makedirs("public/data", exist_ok=True)
with open("public/data/daily_quiz.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Daily quiz generated successfully.")
