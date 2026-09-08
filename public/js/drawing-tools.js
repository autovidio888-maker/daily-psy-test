// public/js/drawing-tools.js
// Lightweight Charts overlay drawing engine.
class DrawingTools {
  constructor({ chart, series, canvas, container, storageKey }) {
    this.chart = chart;
    this.series = series;
    this.canvas = canvas;
    this.container = container;
    this.ctx = canvas.getContext("2d");
    this.storageKey = storageKey || "kline_drawings_v1";
    this.tool = "cursor";
    this.drawings = [];
    this.preview = null;
    this.startPoint = null;
    this.history = [];
    this.redoStack = [];
    this.dpr = window.devicePixelRatio || 1;
    this.enabled = false;
    this.load();
    this.bindEvents();
    this.resize();
  }

  setSeries(series) {
    this.series = series;
    this.redraw();
  }

  setStorageKey(key) {
    this.storageKey = key;
    this.load();
    this.redraw();
  }

  enable(enabled) {
    this.enabled = !!enabled;
    this.container.classList.toggle("drawing-disabled", !this.enabled);
  }

  setTool(tool) {
    this.tool = tool;
    this.enable(tool !== "cursor");
    this.preview = null;
    this.startPoint = null;
    this.redraw();
  }

  snapshot() {
    this.history.push(JSON.stringify(this.drawings));
    if (this.history.length > 80) this.history.shift();
    this.redoStack = [];
  }

  undo() {
    if (!this.history.length) return;
    this.redoStack.push(JSON.stringify(this.drawings));
    this.drawings = JSON.parse(this.history.pop() || "[]");
    this.save();
    this.redraw();
  }

  redo() {
    if (!this.redoStack.length) return;
    this.history.push(JSON.stringify(this.drawings));
    this.drawings = JSON.parse(this.redoStack.pop() || "[]");
    this.save();
    this.redraw();
  }

  clear() {
    if (!confirm("確定清空目前這檔的所有畫線嗎？")) return;
    this.snapshot();
    this.drawings = [];
    this.save();
    this.redraw();
  }

  exportJson() {
    return JSON.stringify(this.drawings, null, 2);
  }

  importJson(text) {
    const parsed = JSON.parse(text);
    if (!Array.isArray(parsed)) throw new Error("畫線 JSON 必須是陣列");
    this.snapshot();
    this.drawings = parsed;
    this.save();
    this.redraw();
  }

  load() {
    try {
      this.drawings = JSON.parse(localStorage.getItem(this.storageKey) || "[]");
      if (!Array.isArray(this.drawings)) this.drawings = [];
    } catch (_) {
      this.drawings = [];
    }
  }

  save() {
    try { localStorage.setItem(this.storageKey, JSON.stringify(this.drawings)); } catch (_) {}
  }

  resize() {
    const r = this.container.getBoundingClientRect();
    const w = Math.max(1, Math.floor(r.width));
    const h = Math.max(1, Math.floor(r.height));
    this.dpr = window.devicePixelRatio || 1;
    this.canvas.style.width = `${w}px`;
    this.canvas.style.height = `${h}px`;
    this.canvas.width = Math.floor(w * this.dpr);
    this.canvas.height = Math.floor(h * this.dpr);
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    this.redraw();
  }

  bindEvents() {
    window.addEventListener("resize", () => this.resize());
    this.chart.timeScale().subscribeVisibleTimeRangeChange(() => this.redraw());
    this.canvas.addEventListener("mousedown", e => this.onDown(e));
    this.canvas.addEventListener("mousemove", e => this.onMove(e));
    window.addEventListener("mouseup", e => this.onUp(e));
    this.canvas.addEventListener("dblclick", e => this.onDoubleClick(e));
  }

  mouse(ev) {
    const rect = this.canvas.getBoundingClientRect();
    return { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
  }

  normalizeTime(t) {
    if (!t) return null;
    if (typeof t === "string") return t;
    if (typeof t === "number") return t;
    if (typeof t === "object" && t.year && t.month && t.day) {
      const mm = String(t.month).padStart(2, "0");
      const dd = String(t.day).padStart(2, "0");
      return `${t.year}-${mm}-${dd}`;
    }
    return null;
  }

  pointFromEvent(ev) {
    const m = this.mouse(ev);
    const time = this.normalizeTime(this.chart.timeScale().coordinateToTime(m.x));
    const price = this.series.coordinateToPrice(m.y);
    if (time === null || price === null || Number.isNaN(price)) return { ...m, time: null, price: null };
    return { ...m, time, price: Number(price) };
  }

  coord(p) {
    if (!p) return null;
    const x = this.chart.timeScale().timeToCoordinate(p.time);
    const y = this.series.priceToCoordinate(p.price);
    if (x === null || y === null || Number.isNaN(x) || Number.isNaN(y)) return null;
    return { x, y };
  }

  onDown(ev) {
    if (!this.enabled) return;
    ev.preventDefault();
    ev.stopPropagation();
    const p = this.pointFromEvent(ev);
    if (p.time === null || p.price === null) return;

    if (this.tool === "delete") {
      const idx = this.hitTest(p.x, p.y);
      if (idx >= 0) {
        this.snapshot();
        this.drawings.splice(idx, 1);
        this.save();
        this.redraw();
      }
      return;
    }

    if (this.tool === "hline") {
      this.addDrawing({ type: "hline", price: p.price });
      return;
    }

    if (this.tool === "vline") {
      this.addDrawing({ type: "vline", time: p.time });
      return;
    }

    if (this.tool === "text") {
      const text = prompt("輸入文字標註：", "觀察點");
      if (text && text.trim()) this.addDrawing({ type: "text", point: { time: p.time, price: p.price }, text: text.trim().slice(0, 40) });
      return;
    }

    this.startPoint = { time: p.time, price: p.price };
    this.preview = null;
  }

  onMove(ev) {
    if (!this.enabled || !this.startPoint) return;
    const p = this.pointFromEvent(ev);
    if (p.time === null || p.price === null) return;
    const p2 = { time: p.time, price: p.price };
    if (["trend", "ray", "rect", "fib"].includes(this.tool)) {
      this.preview = { type: this.tool, p1: this.startPoint, p2 };
      this.redraw();
    }
  }

  onUp(ev) {
    if (!this.enabled || !this.startPoint || !this.preview) return;
    const p = this.pointFromEvent(ev);
    if (p.time === null || p.price === null) return;
    const c1 = this.coord(this.startPoint);
    const c2 = this.coord({ time: p.time, price: p.price });
    if (!c1 || !c2) return;
    const dist = Math.hypot(c2.x - c1.x, c2.y - c1.y);
    if (dist > 8) this.addDrawing(this.preview);
    this.startPoint = null;
    this.preview = null;
    this.redraw();
  }

  onDoubleClick(ev) {
    if (this.tool !== "delete") return;
    const m = this.mouse(ev);
    const idx = this.hitTest(m.x, m.y);
    if (idx >= 0) {
      this.snapshot();
      this.drawings.splice(idx, 1);
      this.save();
      this.redraw();
    }
  }

  addDrawing(d) {
    this.snapshot();
    d.id = `${Date.now()}_${Math.random().toString(16).slice(2)}`;
    this.drawings.push(d);
    this.save();
    this.redraw();
  }

  redraw() {
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    this.ctx.clearRect(0, 0, w, h);
    for (const d of this.drawings) this.drawOne(d, false);
    if (this.preview) this.drawOne(this.preview, true);
  }

  lineStyle(preview=false) {
    const ctx = this.ctx;
    ctx.lineWidth = preview ? 1.5 : 2;
    ctx.strokeStyle = preview ? "rgba(147,197,253,.72)" : "rgba(96,165,250,.95)";
    ctx.fillStyle = "rgba(96,165,250,.95)";
    ctx.setLineDash(preview ? [6, 5] : []);
    ctx.font = "12px system-ui, -apple-system, BlinkMacSystemFont, Segoe UI";
  }

  drawOne(d, preview=false) {
    const ctx = this.ctx;
    this.lineStyle(preview);

    if (d.type === "hline") {
      const y = this.series.priceToCoordinate(d.price);
      if (y === null) return;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(this.canvas.clientWidth, y); ctx.stroke();
      ctx.fillText(Number(d.price).toFixed(2), 8, y - 5);
      return;
    }

    if (d.type === "vline") {
      const x = this.chart.timeScale().timeToCoordinate(d.time);
      if (x === null) return;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, this.canvas.clientHeight); ctx.stroke();
      return;
    }

    if (d.type === "text") {
      const c = this.coord(d.point);
      if (!c) return;
      ctx.fillStyle = "rgba(226,232,240,.98)";
      ctx.strokeStyle = "rgba(15,23,42,.9)";
      ctx.lineWidth = 4;
      ctx.strokeText(d.text, c.x + 6, c.y - 6);
      ctx.fillText(d.text, c.x + 6, c.y - 6);
      return;
    }

    const c1 = this.coord(d.p1);
    const c2 = this.coord(d.p2);
    if (!c1 || !c2) return;

    if (d.type === "trend") {
      ctx.beginPath(); ctx.moveTo(c1.x, c1.y); ctx.lineTo(c2.x, c2.y); ctx.stroke();
      this.drawHandle(c1); this.drawHandle(c2);
      return;
    }

    if (d.type === "ray") {
      const dx = c2.x - c1.x;
      const dy = c2.y - c1.y;
      const endX = this.canvas.clientWidth;
      const endY = Math.abs(dx) < 1 ? c2.y : c1.y + dy * ((endX - c1.x) / dx);
      ctx.beginPath(); ctx.moveTo(c1.x, c1.y); ctx.lineTo(endX, endY); ctx.stroke();
      this.drawHandle(c1); this.drawHandle(c2);
      return;
    }

    if (d.type === "rect") {
      const x = Math.min(c1.x, c2.x), y = Math.min(c1.y, c2.y);
      const rw = Math.abs(c2.x - c1.x), rh = Math.abs(c2.y - c1.y);
      ctx.fillStyle = preview ? "rgba(96,165,250,.08)" : "rgba(96,165,250,.12)";
      ctx.strokeRect(x, y, rw, rh);
      ctx.fillRect(x, y, rw, rh);
      return;
    }

    if (d.type === "fib") {
      const x1 = Math.min(c1.x, c2.x), x2 = Math.max(c1.x, c2.x);
      const levels = [0, .236, .382, .5, .618, .786, 1];
      levels.forEach(level => {
        const y = c1.y + (c2.y - c1.y) * level;
        ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y); ctx.stroke();
        ctx.fillText(`${(level * 100).toFixed(1)}%`, x1 + 5, y - 4);
      });
    }
  }

  drawHandle(c) {
    const ctx = this.ctx;
    ctx.setLineDash([]);
    ctx.fillStyle = "rgba(191,219,254,.95)";
    ctx.beginPath(); ctx.arc(c.x, c.y, 4, 0, Math.PI * 2); ctx.fill();
  }

  hitTest(x, y) {
    for (let i = this.drawings.length - 1; i >= 0; i--) {
      if (this.isHit(this.drawings[i], x, y)) return i;
    }
    return -1;
  }

  isHit(d, x, y) {
    if (d.type === "hline") {
      const yy = this.series.priceToCoordinate(d.price);
      return yy !== null && Math.abs(y - yy) < 9;
    }
    if (d.type === "vline") {
      const xx = this.chart.timeScale().timeToCoordinate(d.time);
      return xx !== null && Math.abs(x - xx) < 9;
    }
    if (d.type === "text") {
      const c = this.coord(d.point);
      if (!c) return false;
      return x >= c.x && x <= c.x + Math.max(60, String(d.text).length * 13) && y >= c.y - 28 && y <= c.y + 8;
    }
    const c1 = this.coord(d.p1), c2 = this.coord(d.p2);
    if (!c1 || !c2) return false;
    if (d.type === "rect") {
      const minX = Math.min(c1.x, c2.x), maxX = Math.max(c1.x, c2.x);
      const minY = Math.min(c1.y, c2.y), maxY = Math.max(c1.y, c2.y);
      const nearBorder = Math.abs(x - minX) < 9 || Math.abs(x - maxX) < 9 || Math.abs(y - minY) < 9 || Math.abs(y - maxY) < 9;
      return x >= minX - 9 && x <= maxX + 9 && y >= minY - 9 && y <= maxY + 9 && nearBorder;
    }
    if (d.type === "fib") {
      const minX = Math.min(c1.x, c2.x), maxX = Math.max(c1.x, c2.x);
      if (x < minX - 8 || x > maxX + 8) return false;
      return [0, .236, .382, .5, .618, .786, 1].some(level => Math.abs(y - (c1.y + (c2.y - c1.y) * level)) < 8);
    }
    if (d.type === "ray") {
      const endX = this.canvas.clientWidth;
      const dx = c2.x - c1.x;
      const endY = Math.abs(dx) < 1 ? c2.y : c1.y + (c2.y - c1.y) * ((endX - c1.x) / dx);
      return this.pointToSegmentDistance(x, y, c1.x, c1.y, endX, endY) < 8;
    }
    return this.pointToSegmentDistance(x, y, c1.x, c1.y, c2.x, c2.y) < 8;
  }

  pointToSegmentDistance(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1, dy = y2 - y1;
    if (dx === 0 && dy === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
  }
}

window.DrawingTools = DrawingTools;
