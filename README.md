# 裸 K 訓練場 KLine Replay Arena

這是一個可以部署在 GitHub Pages 的裸 K 練習網站。

功能：

- 每日裸 K 五題挑戰
- 隱藏股票名稱與日期，先判斷後續走勢
- 揭曉後 10 根 K 線
- 看漲 / 看跌 / 盤整計分
- 回測練習：手動買進、賣出、下一根
- 畫線工具：趨勢線、射線、水平線、垂直線、區間框、斐波、文字、刪除、復原、重做
- Supabase 即時對戰房間與排行榜
- GitHub Actions 每日更新 K 線資料

## 部署方式

1. 將本資料夾所有檔案放到 GitHub repo 根目錄。
2. 到 GitHub Pages 設定使用 main branch / root。
3. 如果要使用自訂網域，保留 `CNAME`。
4. 到 Actions 頁面手動執行 `Update Kline Data` 一次。
5. 等 `public/data/daily_challenge.json` 與 `public/data/klines/*.json` 更新完成。

## 即時對戰設定

1. 到 Supabase 建立 project。
2. 到 SQL Editor 執行 `supabase_schema.sql`。
3. 將 Supabase URL 與 anon key 填入 `public/js/config.js`：

```js
window.KLINE_CONFIG = {
  siteUrl: "https://daydayquiz.com",
  supabaseUrl: "你的 Supabase URL",
  supabaseAnonKey: "你的 Supabase anon key",
  dailyChallengePath: "public/data/daily_challenge.json"
};
```

## 注意

本網站僅供 K 線閱讀練習與教育用途，不提供任何投資建議，也不構成買賣推薦。
