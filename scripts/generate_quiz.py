import os
import json
import re
import google.generativeai as genai

# 取得環境變數中的金鑰
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("找不到 GEMINI_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

prompt = """
你是一個爆款社群心理測驗與視覺設計師。請設計一個適合在 Threads / IG 引發轉發的趣味心理測驗。
主題可以多樣化（例如：職場社畜生物、咖啡靈魂風味、奇幻冒險職業、貓狗社交人格、夜市小吃屬性等）。

除了題目外，請為 A, B, C, D 四種測驗結果分別設計一個專屬的「可愛治癒系代表吉祥物」。
為了讓卡片視覺極致精緻，請為每個結果提供：
1. "emoji": 一個代表性的可愛 Emoji（例如 🐱, ☕, 🧙, 🦦, 🥑 等）。
2. "tagline": 一句超有梗的副標題（例如「躺平系摸魚王」）。
3. "color": 專屬漸層主色（例如 "from-amber-400 to-orange-500" 或 "from-pink-400 to-rose-500"）。
4. "svg_icon": 一段乾淨、可愛的 SVG 向量圖標（viewBox="0 0 100 100"，寬高均為 100，使用簡約可愛的圓弧、幾何圖形拼湊出該角色或物品的呆萌外觀，包含眼睛、微笑嘴巴或專屬特徵）。

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
      "color": "from-amber-400 to-orange-500",
      "svg_icon": "<svg viewBox='0 0 100 100' class='w-20 h-20'><circle cx='50' cy='50' r='40' fill='#FBBF24'/><circle cx='38' cy='46' r='4' fill='#1F2937'/><circle cx='62' cy='46' r='4' fill='#1F2937'/><circle cx='39' cy='44' r='1.5' fill='#FFFFFF'/><circle cx='63' cy='44' r='1.5' fill='#FFFFFF'/><ellipse cx='50' cy='54' rx='4' ry='3' fill='#F43F5E'/><path d='M44 60 Q50 66 56 60' stroke='#1F2937' stroke-width='2.5' fill='none' stroke-linecap='round'/></svg>",
      "quote": "金句",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號B",
      "worstMatch": "稱號D"
    },
    "B": {
      "title": "稱號B",
      "tagline": "短梗副稱號",
      "emoji": "🐼",
      "color": "from-teal-400 to-emerald-500",
      "svg_icon": "<svg viewBox='0 0 100 100' class='w-20 h-20'><circle cx='50' cy='50' r='40' fill='#34D399'/><circle cx='38' cy='46' r='4' fill='#111827'/><circle cx='62' cy='46' r='4' fill='#111827'/><circle cx='39' cy='44' r='1.5' fill='#FFFFFF'/><circle cx='63' cy='44' r='1.5' fill='#FFFFFF'/><ellipse cx='50' cy='53' rx='3' ry='2' fill='#111827'/><path d='M45 58 Q50 63 55 58' stroke='#111827' stroke-width='2' fill='none' stroke-linecap='round'/></svg>",
      "quote": "金句",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號A",
      "worstMatch": "稱號C"
    },
    "C": {
      "title": "稱號C",
      "tagline": "短梗副稱號",
      "emoji": "🐱",
      "color": "from-indigo-400 to-purple-500",
      "svg_icon": "<svg viewBox='0 0 100 100' class='w-20 h-20'><circle cx='50' cy='50' r='40' fill='#A78BFA'/><circle cx='38' cy='46' r='4' fill='#1F2937'/><circle cx='62' cy='46' r='4' fill='#1F2937'/><circle cx='39' cy='44' r='1.5' fill='#FFFFFF'/><circle cx='63' cy='44' r='1.5' fill='#FFFFFF'/><ellipse cx='50' cy='53' rx='3' ry='2.5' fill='#EC4899'/><path d='M44 59 Q50 64 56 59' stroke='#1F2937' stroke-width='2' fill='none' stroke-linecap='round'/></svg>",
      "quote": "金句",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號D",
      "worstMatch": "稱號B"
    },
    "D": {
      "title": "稱號D",
      "tagline": "短梗副稱號",
      "emoji": "🐰",
      "color": "from-rose-400 to-pink-500",
      "svg_icon": "<svg viewBox='0 0 100 100' class='w-20 h-20'><circle cx='50' cy='50' r='40' fill='#FB7185'/><circle cx='38' cy='46' r='4' fill='#1F2937'/><circle cx='62' cy='46' r='4' fill='#1F2937'/><circle cx='39' cy='44' r='1.5' fill='#FFFFFF'/><circle cx='63' cy='44' r='1.5' fill='#FFFFFF'/><ellipse cx='50' cy='52' rx='3' ry='2' fill='#BE185D'/><path d='M45 58 Q50 63 55 58' stroke='#1F2937' stroke-width='2' fill='none' stroke-linecap='round'/></svg>",
      "quote": "金句",
      "traits": ["特徵1", "特徵2", "特徵3"],
      "bestMatch": "稱號C",
      "worstMatch": "稱號A"
    }
  }
}
請確保 questions 剛好有 6 題，內容風趣有洞察力。
"""

response = model.generate_content(prompt)
raw_text = response.text.strip()

# 清理 Markdown 標記
raw_text = re.sub(r"^```json\s*", "", raw_text, flags=re.MULTILINE)
raw_text = re.sub(r"^```\s*", "", raw_text, flags=re.MULTILINE)
raw_text = re.sub(r"```$", "", raw_text, flags=re.MULTILINE)

quiz_data = json.loads(raw_text.strip())

# 寫入 public/data 資料夾
os.makedirs("public/data", exist_ok=True)
with open("public/data/daily_quiz.json", "w", encoding="utf-8") as f:
    json.dump(quiz_data, f, ensure_ascii=False, indent=2)

print("今日心理測驗及專屬可愛角色生成成功！")
