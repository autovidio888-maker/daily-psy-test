import os
import json
import google.generativeai as genai

# 取得環境變數中的金鑰
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("找不到 GEMINI_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

prompt = """
你是一個爆款社群心理測驗設計師。請設計一個適合在 Threads / IG 引發轉發的趣味心理測驗。
主題可以是職場、社交、MBTI變體、戀愛風格或生活日常。

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
    "A": { "title": "稱號A", "quote": "金句", "traits": ["特徵1", "特徵2", "特徵3"], "bestMatch": "B", "worstMatch": "D" },
    "B": { "title": "稱號B", "quote": "金句", "traits": ["特徵1", "特徵2", "特徵3"], "bestMatch": "A", "worstMatch": "C" },
    "C": { "title": "稱號C", "quote": "金句", "traits": ["特徵1", "特徵2", "特徵3"], "bestMatch": "D", "worstMatch": "B" },
    "D": { "title": "稱號D", "quote": "金句", "traits": ["特徵1", "特徵2", "特徵3"], "bestMatch": "C", "worstMatch": "A" }
  }
}
請確保 questions 剛好有 6 題。
"""

response = model.generate_content(prompt)
raw_text = response.text.strip()

if raw_text.startswith("```json"):
    raw_text = raw_text[7:]
if raw_text.startswith("```"):
    raw_text = raw_text[3:]
if raw_text.endswith("```"):
    raw_text = raw_text[:-3]

quiz_data = json.loads(raw_text.strip())

# 寫入 public/data 資料夾
os.makedirs("public/data", exist_ok=True)
with open("public/data/daily_quiz.json", "w", encoding="utf-8") as f:
    json.dump(quiz_data, f, ensure_ascii=False, indent=2)

print("今日心理測驗生成成功！")
