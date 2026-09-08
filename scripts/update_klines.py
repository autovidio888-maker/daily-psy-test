# scripts/update_klines.py
# Yahoo/yfinance 抓取日K、週K、月K，計算常用技術指標，輸出成 GitHub Pages 可讀取的 JSON。

import json
import math
import os
import random
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

TAIWAN_TZ = timezone(timedelta(hours=8))
OUTPUT_DIR = "public/data"
KLINE_DIR = os.path.join(OUTPUT_DIR, "klines")
DAILY_CHALLENGE_PATH = os.path.join(OUTPUT_DIR, "daily_challenge.json")

TICKERS = [
    "2330.TW", "2317.TW", "2454.TW", "2303.TW", "0050.TW",
    "NVDA", "AAPL", "MSFT", "SPY", "QQQ", "BTC-USD",
]

INTERVALS = {
    "1d": {"period": "5y", "visible_bars": 240, "reveal_bars": 20, "range_threshold_pct": 1.2},
    "1wk": {"period": "10y", "visible_bars": 240, "reveal_bars": 12, "range_threshold_pct": 3.0},
    "1mo": {"period": "max", "visible_bars": 180, "reveal_bars": 8, "range_threshold_pct": 6.0},
}


def safe_float(value):
    if value is None:
        return None
    try:
        value = float(value)
    except Exception:
        return None
    if not math.isfinite(value):
        return None
    return round(value, 6)


def sanitize_file_name(ticker: str, interval: str) -> str:
    safe_ticker = ticker.replace(".", "_").replace("-", "_")
    return f"{safe_ticker}_{interval}.json"


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"]
    df["MA5"] = close.rolling(5).mean()
    df["MA20"] = close.rolling(20).mean()
    df["MA60"] = close.rolling(60).mean()
    df["EMA20"] = close.ewm(span=20, adjust=False).mean()
    df["EMA60"] = close.ewm(span=60, adjust=False).mean()
    df["RSI14"] = compute_rsi(close, 14)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df["BB_MID"] = bb_mid
    df["BB_UPPER"] = bb_mid + 2 * bb_std
    df["BB_LOWER"] = bb_mid - 2 * bb_std
    df["ATR14"] = compute_atr(df, 14)
    df["VOL_MA20"] = df["Volume"].rolling(20).mean()
    return df


def normalize_downloaded_frame(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if data is None or data.empty:
        return pd.DataFrame()
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex):
        try:
            if ticker in df.columns.get_level_values(0):
                df = df[ticker].copy()
            elif ticker in df.columns.get_level_values(1):
                df = df.xs(ticker, axis=1, level=1).copy()
        except Exception:
            pass
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()
    df = df[required].copy()
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    df = df[df["Close"] > 0]
    return df


def download_one(ticker: str, interval: str, period: str) -> pd.DataFrame:
    print(f"[INFO] Download {ticker} {interval} {period}")
    data = yf.download(
        tickers=ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
        group_by="column",
    )
    df = normalize_downloaded_frame(data, ticker)
    if df.empty:
        print(f"[WARN] Empty data: {ticker} {interval}")
        return df
    return add_indicators(df)


def df_to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for idx, row in df.iterrows():
        time_text = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
        item = {
            "time": time_text,
            "open": safe_float(row.get("Open")),
            "high": safe_float(row.get("High")),
            "low": safe_float(row.get("Low")),
            "close": safe_float(row.get("Close")),
            "volume": safe_float(row.get("Volume")),
            "ma5": safe_float(row.get("MA5")),
            "ma20": safe_float(row.get("MA20")),
            "ma60": safe_float(row.get("MA60")),
            "ema20": safe_float(row.get("EMA20")),
            "ema60": safe_float(row.get("EMA60")),
            "rsi14": safe_float(row.get("RSI14")),
            "macd": safe_float(row.get("MACD")),
            "macd_signal": safe_float(row.get("MACD_SIGNAL")),
            "macd_hist": safe_float(row.get("MACD_HIST")),
            "bb_upper": safe_float(row.get("BB_UPPER")),
            "bb_mid": safe_float(row.get("BB_MID")),
            "bb_lower": safe_float(row.get("BB_LOWER")),
            "atr14": safe_float(row.get("ATR14")),
            "vol_ma20": safe_float(row.get("VOL_MA20")),
        }
        if all(item[k] is not None for k in ["open", "high", "low", "close"]):
            records.append(item)
    return sorted(records, key=lambda x: x["time"])


def save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_daily_challenge(available_files: list[dict]) -> dict:
    today = datetime.now(TAIWAN_TZ).strftime("%Y-%m-%d")
    rng = random.Random(today)
    candidates = []
    for item in available_files:
        setting = INTERVALS[item["interval"]]
        required = setting["visible_bars"] + setting["reveal_bars"] + 80
        if item["count"] >= required:
            candidates.append(item)
    if not candidates:
        raise RuntimeError("No enough kline data to build daily challenge.")
    questions = []
    for q_no in range(1, 6):
        item = rng.choice(candidates)
        setting = INTERVALS[item["interval"]]
        visible = setting["visible_bars"]
        reveal = setting["reveal_bars"]
        max_start = item["count"] - visible - reveal - 1
        min_start = min(80, max_start)
        start_idx = rng.randint(min_start, max_start)
        questions.append({
            "question_no": q_no,
            "ticker": item["ticker"],
            "interval": item["interval"],
            "data_path": item["path"],
            "start_idx": start_idx,
            "visible_bars": visible,
            "reveal_bars": reveal,
            "threshold_pct": setting["range_threshold_pct"],
        })
    return {
        "date": today,
        "title": "今日裸 K 五連戰",
        "description": "每日自動產生 5 題 K 線方向練習。股票名稱先隱藏，作答後揭曉。",
        "questions": questions,
        "updated_at": datetime.now(TAIWAN_TZ).isoformat(),
    }


def main() -> None:
    os.makedirs(KLINE_DIR, exist_ok=True)
    available_files = []
    for ticker in TICKERS:
        for interval, setting in INTERVALS.items():
            try:
                df = download_one(ticker, interval, setting["period"])
                if df.empty:
                    continue
                records = df_to_records(df)
                if len(records) < 80:
                    print(f"[WARN] Too few records: {ticker} {interval} {len(records)}")
                    continue
                filename = sanitize_file_name(ticker, interval)
                path = os.path.join(KLINE_DIR, filename)
                public_path = f"public/data/klines/{filename}"
                save_json(path, records)
                available_files.append({"ticker": ticker, "interval": interval, "path": public_path, "count": len(records)})
                print(f"[OK] Saved {public_path}, rows={len(records)}")
            except Exception as e:
                print(f"[ERROR] {ticker} {interval}: {e}")
    if not available_files:
        raise RuntimeError("No kline files generated.")
    challenge = build_daily_challenge(available_files)
    save_json(DAILY_CHALLENGE_PATH, challenge)
    print(f"[OK] Saved {DAILY_CHALLENGE_PATH}")
    print(json.dumps(challenge, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
