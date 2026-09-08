// public/js/app.js
const App = {
  mode: "practice",
  challenge: null,
  questionIndex: 0,
  currentData: [],
  currentQuestion: null,
  chart: null,
  candleSeries: null,
  volumeSeries: null,
  drawingTools: null,
  revealed: false,
  score: 0,
  hits: 0,
  answers: [],
  backtest: null,
  autoplayTimer: null
};

const $ = id => document.getElementById(id);
const cfg = window.KLINE_CONFIG || {};

function money(n) {
  return Number(n || 0).toLocaleString("zh-TW", { maximumFractionDigits: 0 });
}

function pct(n) {
  const v = Number(n || 0);
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function setMode(mode) {
  App.mode = mode;

  ["practice", "backtest", "battle"].forEach(m => {
    const btn = $(`mode-${m}`);
    if (!btn) return;

    btn.className = m === mode
      ? "btn px-4 py-2 bg-blue-600 text-white"
      : "btn px-4 py-2 bg-slate-800 border border-slate-700 text-slate-200";
  });

  $("answer-area").classList.toggle("hidden", mode !== "practice" && mode !== "battle");
  $("backtest-area").classList.toggle("hidden", mode !== "backtest");
  $("battle-panel").classList.toggle("hidden", mode !== "battle");

  renderQuestion();
}

async function init() {
  bindUi();
  createChart();
  await loadChallenge();
  renderQuestion();
  updateStats();

  if (window.Battle) {
    window.Battle.init(App);
  }
}

function bindUi() {
  $("mode-practice").onclick = () => setMode("practice");
  $("mode-backtest").onclick = () => setMode("backtest");
  $("mode-battle").onclick = () => setMode("battle");

  $("restart-btn").onclick = restart;
  $("next-question").onclick = nextQuestion;
  $("copy-share").onclick = copyShareText;

  document.querySelectorAll(".answer-btn").forEach(btn => {
    btn.onclick = () => submitAnswer(btn.dataset.answer);
  });

  document.querySelectorAll(".tool-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".tool-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      if (App.drawingTools) {
        App.drawingTools.setTool(btn.dataset.tool);
      }
    };
  });

  $("undo-btn").onclick = () => App.drawingTools && App.drawingTools.undo();
  $("redo-btn").onclick = () => App.drawingTools && App.drawingTools.redo();
  $("clear-draw-btn").onclick = () => App.drawingTools && App.drawingTools.clear();

  $("bt-buy").onclick = () => backtestBuy();
  $("bt-sell").onclick = () => backtestSell();
  $("bt-next").onclick = () => backtestNext();
  $("bt-auto").onclick = () => toggleAutoplay();
  $("bt-reset").onclick = () => setupBacktest(true);
}

function addCandlestickSeriesCompat(chart, options) {
  // Lightweight Charts v4
  if (typeof chart.addCandlestickSeries === "function") {
    return chart.addCandlestickSeries(options);
  }

  // Lightweight Charts v5
  if (typeof chart.addSeries === "function" && LightweightCharts.CandlestickSeries) {
    return chart.addSeries(LightweightCharts.CandlestickSeries, options);
  }

  throw new Error("Lightweight Charts CandlestickSeries API 載入失敗，請檢查 CDN 版本。");
}

function addHistogramSeriesCompat(chart, options) {
  // Lightweight Charts v4
  if (typeof chart.addHistogramSeries === "function") {
    return chart.addHistogramSeries(options);
  }

  // Lightweight Charts v5
  if (typeof chart.addSeries === "function" && LightweightCharts.HistogramSeries) {
    return chart.addSeries(LightweightCharts.HistogramSeries, options);
  }

  throw new Error("Lightweight Charts HistogramSeries API 載入失敗，請檢查 CDN 版本。");
}

function createChart() {
  const chartEl = $("chart");
  const rect = chartEl.getBoundingClientRect();

  App.chart = LightweightCharts.createChart(chartEl, {
    width: Math.max(320, Math.floor(rect.width || chartEl.clientWidth || 900)),
    height: Math.max(420, Math.floor(rect.height || chartEl.clientHeight || 680)),
    layout: {
      background: { type: "solid", color: "#020617" },
      textColor: "#cbd5e1"
    },
    grid: {
      vertLines: { color: "rgba(51,65,85,.35)" },
      horzLines: { color: "rgba(51,65,85,.35)" }
    },
    rightPriceScale: {
      borderColor: "rgba(148,163,184,.25)"
    },
    timeScale: {
      borderColor: "rgba(148,163,184,.25)",
      timeVisible: false
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal
    },
    localization: {
      locale: "zh-TW"
    }
  });

  App.candleSeries = addCandlestickSeriesCompat(App.chart, {
    upColor: "#22c55e",
    downColor: "#ef4444",
    borderUpColor: "#22c55e",
    borderDownColor: "#ef4444",
    wickUpColor: "#22c55e",
    wickDownColor: "#ef4444"
  });

  App.volumeSeries = addHistogramSeriesCompat(App.chart, {
    priceFormat: {
      type: "volume"
    },
    priceScaleId: "volume",
    color: "rgba(148,163,184,.35)"
  });

  App.chart.priceScale("volume").applyOptions({
    scaleMargins: {
      top: 0.82,
      bottom: 0
    }
  });

  const canvas = $("draw-canvas");
  const wrap = $("chart-wrap");

  if (window.DrawingTools && canvas && wrap) {
    App.drawingTools = new DrawingTools({
      chart: App.chart,
      series: App.candleSeries,
      canvas,
      container: wrap
    });

    App.drawingTools.enable(false);
  }

  new ResizeObserver(() => {
    const r = chartEl.getBoundingClientRect();

    App.chart.applyOptions({
      width: Math.floor(r.width),
      height: Math.floor(r.height)
    });

    if (App.drawingTools) {
      App.drawingTools.resize();
    }
  }).observe(chartEl);
}

async function loadChallenge() {
  const path = cfg.dailyChallengePath || "public/data/daily_challenge.json";
  const res = await fetch(`${path}?t=${Date.now()}`);

  if (!res.ok) {
    throw new Error("daily_challenge.json 載入失敗");
  }

  App.challenge = await res.json();
  $("challenge-title").innerText = App.challenge.title || "今日裸 K 五連戰";
}

async function loadKlines(path) {
  const res = await fetch(`${path}?t=${Date.now()}`);

  if (!res.ok) {
    throw new Error(`K 線資料載入失敗：${path}`);
  }

  const raw = await res.json();

  return raw
    .map(x => ({
      time: x.time,
      open: Number(x.open),
      high: Number(x.high),
      low: Number(x.low),
      close: Number(x.close),
      volume: Number(x.volume || 0)
    }))
    .filter(x =>
      x.time &&
      Number.isFinite(x.open) &&
      Number.isFinite(x.high) &&
      Number.isFinite(x.low) &&
      Number.isFinite(x.close)
    );
}

async function renderQuestion() {
  if (!App.challenge) return;

  clearInterval(App.autoplayTimer);
  App.autoplayTimer = null;

  $("bt-auto").innerText = "自動播放";
  App.revealed = false;
  $("result-box").classList.add("hidden");
  $("next-question").classList.add("hidden");
  setAnswerButtonsDisabled(false);

  const q = App.challenge.questions[App.questionIndex];
  App.currentQuestion = q;
  App.currentData = await loadKlines(q.data_path);

  const start = q.start_idx;
  const visibleBars = q.visible_bars || 60;
  const revealBars = q.reveal_bars || 10;

  const visibleEnd = Math.min(
    start + visibleBars,
    App.currentData.length - revealBars - 1
  );

  const revealEnd = Math.min(
    visibleEnd + revealBars,
    App.currentData.length - 1
  );

  q._visibleEnd = visibleEnd;
  q._revealEnd = revealEnd;

  const visible = App.currentData.slice(start, visibleEnd + 1);

  setChartData(visible);
  App.chart.timeScale().fitContent();

  $("question-title").innerText =
    `第 ${App.questionIndex + 1} / ${App.challenge.questions.length} 題：判斷後 ${revealBars} 根 K`;

  $("symbol-badge").innerText = "代號隱藏";
  $("blind-badge").innerText = "BLIND MODE";

  if (App.drawingTools) {
    App.drawingTools.setStorageKey(`drawings_${q.ticker || "unknown"}_${q.interval || "1d"}`);
  }

  if (App.mode === "backtest") {
    setupBacktest(false);
  }

  updateStats();
}

function setChartData(candles) {
  App.candleSeries.setData(
    candles.map(x => ({
      time: x.time,
      open: x.open,
      high: x.high,
      low: x.low,
      close: x.close
    }))
  );

  App.volumeSeries.setData(
    candles.map(x => ({
      time: x.time,
      value: x.volume || 0,
      color: x.close >= x.open
        ? "rgba(34,197,94,.32)"
        : "rgba(239,68,68,.32)"
    }))
  );

  requestAnimationFrame(() => {
    if (App.drawingTools) {
      App.drawingTools.resize();
    }
  });
}

function computeOutcome() {
  const q = App.currentQuestion;
  const base = App.currentData[q._visibleEnd];
  const future = App.currentData.slice(q._visibleEnd + 1, q._revealEnd + 1);
  const last = App.currentData[q._revealEnd];

  const ret = ((last.close - base.close) / base.close) * 100;
  const maxHigh = Math.max(...future.map(x => x.high));
  const minLow = Math.min(...future.map(x => x.low));
  const maxUp = ((maxHigh - base.close) / base.close) * 100;
  const maxDown = ((minLow - base.close) / base.close) * 100;

  const threshold = Number(App.challenge.range_threshold_pct || 1.2);

  let direction = "range";

  if (ret > threshold) {
    direction = "up";
  } else if (ret < -threshold) {
    direction = "down";
  }

  return {
    direction,
    ret,
    maxUp,
    maxDown,
    baseClose: base.close,
    lastClose: last.close
  };
}

function labelDirection(d) {
  if (d === "up") return "看漲";
  if (d === "down") return "看跌";
  return "盤整";
}

function submitAnswer(answer) {
  if (App.revealed) return;

  App.revealed = true;
  setAnswerButtonsDisabled(true);

  const q = App.currentQuestion;
  const reveal = App.currentData.slice(q.start_idx, q._revealEnd + 1);

  setChartData(reveal);
  App.chart.timeScale().fitContent();

  const out = computeOutcome();
  const correct = answer === out.direction;
  const gained = correct ? (out.direction === "range" ? 25 : 20) : 0;

  App.score += gained;

  if (correct) {
    App.hits += 1;
  }

  App.answers.push({
    question: App.questionIndex + 1,
    answer,
    correct: out.direction,
    gained,
    ticker: q.ticker,
    ret: out.ret
  });

  $("symbol-badge").innerText = `${q.ticker || "UNKNOWN"} · ${q.interval || "1d"}`;
  $("blind-badge").innerText = correct ? "命中" : "失誤";

  showResult(correct, answer, out, gained);
  updateStats();

  if (App.mode === "battle" && window.Battle) {
    window.Battle.submitCurrentScore(App.score, App.hits, App.answers);
  }
}

function showResult(correct, answer, out, gained) {
  const box = $("result-box");
  box.classList.remove("hidden");

  box.innerHTML = `
    <div class="flex items-center justify-between gap-2 mb-2">
      <h3 class="font-black text-lg ${correct ? "text-emerald-300" : "text-rose-300"}">
        ${correct ? "判斷正確" : "判斷失誤"}
      </h3>
      <span class="text-xs px-3 py-1 rounded-full bg-slate-800 border border-slate-700">
        +${gained} 分
      </span>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-bold">
      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">你的答案</div>
        <div class="mt-1">${labelDirection(answer)}</div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">實際方向</div>
        <div class="mt-1">${labelDirection(out.direction)}</div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">收盤變化</div>
        <div class="mt-1 ${out.ret >= 0 ? "text-emerald-300" : "text-rose-300"}">
          ${pct(out.ret)}
        </div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">區間振幅</div>
        <div class="mt-1">上 ${pct(out.maxUp)} / 下 ${pct(out.maxDown)}</div>
      </div>
    </div>

    <p class="text-sm text-slate-400 mt-3">
      ${feedbackText(correct, answer, out)}
    </p>
  `;

  if (App.questionIndex < App.challenge.questions.length - 1) {
    $("next-question").classList.remove("hidden");
  } else {
    finishChallenge();
  }
}

function feedbackText(correct, answer, out) {
  if (correct) {
    return "這題你抓到主要方向。重點不是猜對一次，而是累積大量樣本後檢查自己的誤判類型。";
  }

  if (answer === "up" && out.direction === "down") {
    return "你偏向追強，但後段收盤轉弱。下次注意突破後是否能守住關鍵低點。";
  }

  if (answer === "down" && out.direction === "up") {
    return "你被前面的壓力感影響，但後段買盤延續。下次注意低點是否沒有再破。";
  }

  if (out.direction === "range") {
    return "這段主要是盤整，方向感不強。裸 K 練習也要學會承認沒有明確方向。";
  }

  return "這題的方向判斷和後續收盤結果不同，建議回看你畫的支撐壓力是否太主觀。";
}

function setAnswerButtonsDisabled(disabled) {
  document.querySelectorAll(".answer-btn").forEach(btn => {
    btn.disabled = disabled;
    btn.classList.toggle("opacity-50", disabled);
  });
}

function nextQuestion() {
  if (App.questionIndex < App.challenge.questions.length - 1) {
    App.questionIndex += 1;
    renderQuestion();
  }
}

function updateStats() {
  const total = App.challenge?.questions?.length || 5;

  $("stat-progress").innerText = `${Math.min(App.answers.length, total)}/${total}`;
  $("stat-hit").innerText = App.hits;
  $("stat-score").innerText = App.score;
  $("score-badge").innerText = `分數 ${App.score}`;
}

function finishChallenge() {
  let title = "被洗出去的人";

  if (App.score >= 90) {
    title = "裸 K 老狐狸";
  } else if (App.score >= 70) {
    title = "不追高戰士";
  } else if (App.score >= 45) {
    title = "盤感修煉中";
  }

  const box = $("result-box");

  box.innerHTML += `
    <div class="mt-4 rounded-2xl border border-blue-500/30 bg-blue-500/10 p-4">
      <h3 class="text-xl font-black text-blue-200">
        今日挑戰完成：${title}
      </h3>
      <p class="text-sm text-slate-300 mt-1">
        命中 ${App.hits}/${App.challenge.questions.length}，總分 ${App.score}。
      </p>
    </div>
  `;

  saveDailyResult();
}

function saveDailyResult() {
  const key = `kline_result_${App.challenge.date || new Date().toISOString().slice(0, 10)}`;

  localStorage.setItem(
    key,
    JSON.stringify({
      score: App.score,
      hits: App.hits,
      answers: App.answers,
      saved_at: new Date().toISOString()
    })
  );
}

function restart() {
  App.questionIndex = 0;
  App.score = 0;
  App.hits = 0;
  App.answers = [];

  renderQuestion();
  updateStats();
}

function copyShareText() {
  const total = App.challenge?.questions?.length || 5;

  const text =
`我剛完成今日裸 K 五連戰
命中：${App.hits}/${total}
分數：${App.score}

不看消息、不看指標，只看 K 線。
${cfg.siteUrl || "https://daydayquiz.com"}`;

  navigator.clipboard.writeText(text).then(() => {
    alert("戰績文已複製");
  });
}

function setupBacktest(resetOnly) {
  const q = App.currentQuestion;
  if (!q) return;

  App.backtest = {
    idx: q._visibleEnd,
    end: q._revealEnd,
    cash: 1000000,
    shares: 0,
    avgCost: 0,
    realized: 0,
    trades: []
  };

  setChartData(App.currentData.slice(q.start_idx, q._visibleEnd + 1));
  App.chart.timeScale().fitContent();

  showBacktestStatus("回測已重置。你可以按買進、賣出或下一根。");

  if (resetOnly) return;
}

function currentBacktestPrice() {
  const bt = App.backtest;
  return App.currentData[bt.idx].close;
}

function backtestBuy() {
  const bt = App.backtest;
  if (!bt) return;

  const price = currentBacktestPrice();
  const qty = Math.floor(bt.cash / price);

  if (qty <= 0) {
    return showBacktestStatus("現金不足，無法買進。");
  }

  bt.cash -= qty * price;
  bt.avgCost = bt.shares > 0
    ? ((bt.avgCost * bt.shares) + (price * qty)) / (bt.shares + qty)
    : price;

  bt.shares += qty;

  bt.trades.push({
    type: "buy",
    idx: bt.idx,
    price,
    qty
  });

  showBacktestStatus(`買進 ${qty} 股，價格 ${price.toFixed(2)}。`);
}

function backtestSell() {
  const bt = App.backtest;
  if (!bt) return;

  const price = currentBacktestPrice();

  if (bt.shares <= 0) {
    return showBacktestStatus("目前沒有持股可賣出。");
  }

  const qty = bt.shares;

  bt.cash += qty * price;
  bt.realized += (price - bt.avgCost) * qty;

  bt.trades.push({
    type: "sell",
    idx: bt.idx,
    price,
    qty
  });

  bt.shares = 0;
  bt.avgCost = 0;

  showBacktestStatus(`賣出 ${qty} 股，價格 ${price.toFixed(2)}。`);
}

function backtestNext() {
  const bt = App.backtest;
  if (!bt) return;

  if (bt.idx >= bt.end) {
    return finishBacktest();
  }

  bt.idx += 1;

  setChartData(App.currentData.slice(App.currentQuestion.start_idx, bt.idx + 1));
  App.chart.timeScale().fitContent();

  if (bt.idx >= bt.end) {
    finishBacktest();
  } else {
    showBacktestStatus("已前進一根 K。", false);
  }
}

function toggleAutoplay() {
  if (App.autoplayTimer) {
    clearInterval(App.autoplayTimer);
    App.autoplayTimer = null;
    $("bt-auto").innerText = "自動播放";
    return;
  }

  $("bt-auto").innerText = "停止播放";

  App.autoplayTimer = setInterval(() => {
    const bt = App.backtest;

    if (!bt || bt.idx >= bt.end) {
      clearInterval(App.autoplayTimer);
      App.autoplayTimer = null;
      $("bt-auto").innerText = "自動播放";
      finishBacktest();
      return;
    }

    backtestNext();
  }, 700);
}

function showBacktestStatus(message) {
  const bt = App.backtest;
  if (!bt) return;

  const price = currentBacktestPrice();
  const equity = bt.cash + bt.shares * price;
  const ret = ((equity - 1000000) / 1000000) * 100;

  const box = $("result-box");
  box.classList.remove("hidden");

  box.innerHTML = `
    <h3 class="font-black text-lg mb-2">回測練習</h3>

    <p class="text-sm text-slate-400 mb-3">
      ${message}
    </p>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-bold">
      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">目前價格</div>
        <div>${price.toFixed(2)}</div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">現金</div>
        <div>${money(bt.cash)}</div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">持股</div>
        <div>${money(bt.shares)}</div>
      </div>

      <div class="bg-slate-900 border border-slate-700 rounded-xl p-3">
        <div class="text-slate-500">權益變化</div>
        <div class="${ret >= 0 ? "text-emerald-300" : "text-rose-300"}">
          ${pct(ret)}
        </div>
      </div>
    </div>
  `;
}

function finishBacktest() {
  const bt = App.backtest;
  if (!bt) return;

  const price = currentBacktestPrice();
  const equity = bt.cash + bt.shares * price;
  const ret = ((equity - 1000000) / 1000000) * 100;

  showBacktestStatus(
    `回測結束。交易次數 ${bt.trades.length}，最後權益 ${money(equity)}，報酬 ${pct(ret)}。`
  );
}

window.addEventListener("DOMContentLoaded", () => {
  init().catch(err => {
    console.error(err);

    $("challenge-title").innerText = "載入失敗";
    $("question-title").innerText = err.message || "請檢查 daily_challenge.json";
  });
});
