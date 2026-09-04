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
你是一位專門設計社群爆款互動測驗的內容企劃、心理測驗設計師與視覺設計師。
請為 DayDayQuiz 產生一份「今日限定測驗」JSON。

【最重要規則：每天測驗類型必須有變化】
請先從以下測驗類型中挑選一種，並讓整份測驗符合該類型的玩法與語氣：

1. personality_quiz：生活化心理測驗，6 題 A/B/C/D 選項。
2. tarot_quiz：塔羅風格測驗，使用神秘、直覺、命運感語氣，但不得宣稱真實預言。
3. numerology_quiz：生命靈數風格測驗，可用生日、月份、數字直覺作為題目包裝，但不得要求使用者輸入個資。
4. zodiac_quiz：生肖或星座風格測驗，用日常情境包裝性格分析。
5. visual_choice_quiz：潛意識選圖測驗，用「選一扇門、一杯飲料、一種顏色、一隻動物」等視覺選擇。
6. workplace_quiz：職場人格測驗，語氣可厭世、自嘲、社畜共鳴。
7. love_quiz：戀愛人格測驗，圍繞聊天、曖昧、依附模式、戀愛反應。
8. fantasy_quiz：奇幻職業、魔法屬性、冒險角色測驗。

請避免連續使用常見老梗，例如「你是哪種動物」、「你是哪種咖啡」。
主題要有新鮮感、社群感、畫面感。

【輸出內容要求】
請輸出剛好 6 題，每題 4 個選項，選項分別對應 A/B/C/D。
每個選項必須有 emoji，且語氣要生活化、有梗、有畫面，不要像正式問卷。
每個結果 A/B/C/D 都要有明確角色稱號。

【結果卡片設計要求】
每個結果需要包含：
- title：結果稱號，短、好記、適合截圖分享。
- tagline：一句短副標，像社群梗。
- emoji：代表角色的 emoji。
- avatar_seed：英文 seed。
- color：Tailwind gradient class，例如 from-amber-400 to-orange-500。
- quote：一句金句。
- rarity：R / SR / SSR / UR 其中一種。
- energy：今日能量值，例如 73%。
- social：社交電量，例如 38%。
- analysis：80-120 字，使用巴納姆效應，但要自然，不要 AI 味。
- tip：今日建議，30-50 字。
- traits：3-4 個短特質。
- bestMatch：最契合角色稱號。
- worstMatch：最相剋角色稱號。

【巴納姆效應寫法】
analysis 要讓人覺得「這就是我」。
可以使用這類矛盾但普遍共鳴的人性描述：
- 看起來隨和，其實對某些細節很執著。
- 表面很獨立，其實也希望有人懂自己。
- 社交時可以很嗨，但回家後只想安靜。
- 平常懶得解釋，但心裡其實想很多。
- 很會替別人想，卻常忘記照顧自己。
請避免過度心理學術語。

【Threads 爆款文案】
請寫入 threads_post 欄位。
語氣要像每天在 Threads 上滑手機的 20 幾歲使用者，微厭世、自嘲、好笑。
禁止使用：
「親愛的朋友」、「快來測測看」、「歡迎留言分享」、「今天為大家帶來」。
必須包含：
- 一句吐槽或自嘲開頭
- 今日測驗主題
- 一個搞笑或扎心的結果稱號
- 網址：https://daydayquiz.com
- 標籤：#心理測驗 #今日限定
總字數 150 字以內。

【視覺要求】
請產生 visual_style 欄位，描述今天適合的網頁視覺風格。
例如：
- 神秘塔羅風：深紫、金色、星星、霧面卡片
- 職場摸魚風：便利貼、辦公桌、咖啡、灰藍色
- 深夜食堂風：霓虹、暖光、食物角色
- 生命靈數風：數字、星盤、漸層光暈
- 潛意識選圖風：夢境、柔和色塊、抽象插畫

【嚴格格式】
請只輸出合法 JSON。
不要 markdown。
不要 ```json。
不要解釋。

格式如下：
{
  "date": "YYYY-MM-DD",
  "quiz_type": "personality_quiz / tarot_quiz / numerology_quiz / zodiac_quiz / visual_choice_quiz / workplace_quiz / love_quiz / fantasy_quiz",
  "theme": "測驗主題名稱",
  "subtitle": "一句吸引人的副標",
  "visual_style": "今日視覺風格描述",
  "threads_post": "Threads 文案",
  "questions": [
    {
      "id": 1,
      "label": "短標籤",
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
      "rarity": "SR",
      "energy": "73%",
      "social": "42%",
      "analysis": "80-120 字解析",
      "tip": "今日建議",
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
      "rarity": "SSR",
      "energy": "88%",
      "social": "76%",
      "analysis": "80-120 字解析",
      "tip": "今日建議",
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
      "rarity": "R",
      "energy": "55%",
      "social": "31%",
      "analysis": "80-120 字解析",
      "tip": "今日建議",
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
      "rarity": "UR",
      "energy": "91%",
      "social": "64%",
      "analysis": "80-120 字解析",
      "tip": "今日建議",
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
