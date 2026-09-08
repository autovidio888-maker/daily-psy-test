# scripts/update_klines.py
# GitHub Actions 用：每日更新 K 線 JSON 與 daily_challenge.json。
# 注意：本程式只整理歷史資料，不產生投資建議。

from __future__ import annotations

import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
KLINE_DIR = ROOT / "public" / "data" / "klines"
CHALLENGE_PATH = ROOT / "public" / "data" / "daily_challenge.json"

# 先用高流動性標的，避免資料太少或冷門股造成挑戰無法生成。
TICKERS = [
    "2330.TW", "2317.TW", "2454.TW", "2303.TW", "2881.TW",
    "2882.TW", "2891.TW", "3711.TW", "2382.TW", "3037.TW",
    "0050.TW", "0056.TW", "00878.TW", "006208.TW",
    "AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ",
    "BTC-USD", "ETH-USD",
]

PERIOD = "3y"
INTERVAL = "1d"
VISIBLE_BARS = 60
REVEAL_BARS = 10
QUESTION_COUNT = 5
RANGE_THRESHOLD_PCT = 1.2

def taipei_today() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d")


def file_safe_ticker(ticker: str) -> str:
    return ticker.replace(".", "_").replace("-", "_").replace("/", "_")


def normalize_frame(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    required = ["Open", "High", "Low", "Close"]
    for col in required:
        if col not in df.columns:
            return []

    out = []
    clean = df.dropna(subset=required).copy()
    for idx, row in clean.iterrows():
        try:
            if hasattr(idx, "strftime"):
                time_value = idx.strftime("%Y-%m-%d")
            else:
                time_value = str(idx)[:10]
            item = {
                "time": time_value,
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
                "volume": int(float(row.get("Volume", 0) or 0)),
            }
            if item["high"] >= item["low"] > 0 and item["open"] > 0 and item["close"] > 0:
                out.append(item)
        except Exception:
            continue
    return out


def download_one(ticker: str) -> tuple[str, list[dict]]:
    print(f"[INFO] Download {ticker}")
    df = yf.download(
        ticker,
        period=PERIOD,
        interval=INTERVAL,
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    return ticker, normalize_frame(df)


def write_klines() -> list[dict]:
    KLINE_DIR.mkdir(parents=True, exist_ok=True)
    available = []

    for ticker in TICKERS:
        try:
            symbol, rows = download_one(ticker)
            if len(rows) < VISIBLE_BARS + REVEAL_BARS + 30:
                print(f"[WARN] Skip {symbol}: only {len(rows)} rows")
                continue
            filename = f"{file_safe_ticker(symbol)}_1d.json"
            path = KLINE_DIR / filename
            with path.open("w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            available.append({
                "ticker": symbol,
                "path": f"public/data/klines/{filename}",
                "rows": len(rows),
            })
            print(f"[OK] {symbol}: {len(rows)} rows -> {filename}")
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")

    if len(available) < QUESTION_COUNT:
        raise RuntimeError(f"可用 K 線資料不足：{len(available)}")

    return available


def build_daily_challenge(available: list[dict]) -> None:
    today = taipei_today()
    rng = random.Random(f"KLINE_DAILY_CHALLENGE|{today}")
    selected = rng.sample(available, QUESTION_COUNT)

    questions = []
    for i, item in enumerate(selected, start=1):
        # 避免抽到太靠近最前或最後的位置。
        min_start = 20
        max_start = item["rows"] - VISIBLE_BARS - REVEAL_BARS - 5
        start_idx = rng.randint(min_start, max_start)
        questions.append({
            "id": f"{today}-q{i}",
            "ticker": item["ticker"],
            "interval": "1d",
            "data_path": item["path"],
            "start_idx": start_idx,
            "visible_bars": VISIBLE_BARS,
            "reveal_bars": REVEAL_BARS,
        })

    challenge = {
        "date": today,
        "title": f"{today} 今日裸 K 五連戰",
        "description": "不看消息、不看指標，只看 K 線判斷後續走勢。",
        "range_threshold_pct": RANGE_THRESHOLD_PCT,
        "questions": questions,
        "disclaimer": "本網站僅供 K 線閱讀練習與教育用途，不提供任何投資建議，也不構成買賣推薦。",
    }

    CHALLENGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CHALLENGE_PATH.open("w", encoding="utf-8") as f:
        json.dump(challenge, f, ensure_ascii=False, indent=2)
    print(f"[OK] Write {CHALLENGE_PATH}")


def main() -> None:
    available = write_klines()
    build_daily_challenge(available)


if __name__ == "__main__":
    main()
