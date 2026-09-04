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
你是一個專門打造爆款社群心理測驗的心理學專家與視覺設計師。
請設計一個適合在 Threads / IG 引發病毒式轉發的趣味心理測驗。
主題可以多樣化（例如：職場摸魚生物、咖啡靈魂圖鑑、奇幻冒險職業、貓狗社交人格、深夜消夜屬性等）。

【核心要求：深度巴納姆效應（Barnum Effect）】
在每個結果的 "analysis" 中，必須深度運用巴納姆效應（結合看似矛盾但普遍共鳴的心理特質，例如：外表獨立但渴望被理解、平時隨和但對某些細節極度固執、看起來很能社交其實電量消耗極快等），寫出一段約 80-120 字、直擊靈魂讓人直呼「這完全就是我！」的精準解析。

請為每個結果提供：
1. "emoji": 一個代表性的可愛 Emoji。
2. "tagline": 一句超有梗的副標題（例如「躺平系摸魚王」）。
3. "avatar_seed": 一個能代表該角色的簡短英文單字（用於生成專屬可愛頭像，例如 "cat", "fox", "panda", "rabbit", "owl" 等）。
4. "color": 專屬漸層顏色（例如 "from-amber-400 to-orange-500", "from-pink-400 to-rose-500", "from-teal-400 to-emerald-500", "from-indigo-400 to-purple-500"）。
5. "quote": 扎心又好笑的一句話金句。
6. "analysis": 運用巴納姆效應的深度特質剖析（80~120 字）。
7. "traits": 3~4 個特質關鍵字標籤。
8. "bestMatch": 契合拍檔（直接填寫對應結果的稱號，如「摸魚貓頭鷹」）。
9. "worstMatch": 相剋雷區（直接填寫對應結果的稱號，如「八卦鸚鵡」）。

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

print("今日心理測驗生成成功！")
