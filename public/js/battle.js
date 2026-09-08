// public/js/battle.js
// Optional Supabase realtime battle. Leave config empty to disable battle mode safely.
const Battle = {
  app: null,
  client: null,
  roomCode: "",
  playerId: "",
  playerName: "",
  channel: null,

  init(app) {
    this.app = app;
    const cfg = window.KLINE_CONFIG || {};
    this.playerId = localStorage.getItem("kline_player_id") || crypto.randomUUID();
    localStorage.setItem("kline_player_id", this.playerId);

    if (cfg.supabaseUrl && cfg.supabaseAnonKey && window.supabase) {
      this.client = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
      this.status("Supabase 已就緒，可以建立或加入房間。");
    } else {
      this.status("尚未設定 Supabase。單人練習可用，即時對戰需填 public/js/config.js。");
    }

    const createBtn = document.getElementById("battle-create");
    const joinBtn = document.getElementById("battle-join");
    if (createBtn) createBtn.onclick = () => this.createRoom();
    if (joinBtn) joinBtn.onclick = () => this.joinRoom();
  },

  status(msg) {
    const el = document.getElementById("battle-status");
    if (el) el.innerText = msg;
  },

  readInputs() {
    this.playerName = (document.getElementById("battle-name")?.value || "").trim().slice(0, 24);
    this.roomCode = (document.getElementById("battle-room")?.value || "ROOM001").trim().toUpperCase().replace(/[^A-Z0-9_-]/g, "") || "ROOM001";
    if (!this.playerName) throw new Error("請先輸入玩家名稱");
  },

  async createRoom() {
    try {
      if (!this.client) return this.status("尚未設定 Supabase，不能使用即時對戰。");
      this.readInputs();
      const { error } = await this.client.from("battle_rooms").insert({
        room_code: this.roomCode,
        owner_id: this.playerId,
        date: this.app.challenge?.date || new Date().toISOString().slice(0, 10),
        challenge: this.app.challenge,
        status: "playing"
      });
      if (error && !String(error.message).includes("duplicate")) throw error;
      await this.upsertPlayer();
      this.subscribeRoom();
      this.status(`已建立並加入房間 ${this.roomCode}。把房號給朋友即可對戰。`);
      await this.renderLeaderboard();
    } catch (e) {
      this.status(e.message || "建立房間失敗");
    }
  },

  async joinRoom() {
    try {
      if (!this.client) return this.status("尚未設定 Supabase，不能使用即時對戰。");
      this.readInputs();
      const { data, error } = await this.client.from("battle_rooms").select("*").eq("room_code", this.roomCode).maybeSingle();
      if (error) throw error;
      if (!data) throw new Error(`找不到房間 ${this.roomCode}`);
      await this.upsertPlayer();
      this.subscribeRoom();
      this.status(`已加入房間 ${this.roomCode}。雙方完成題目後會同步分數。`);
      await this.renderLeaderboard();
    } catch (e) {
      this.status(e.message || "加入房間失敗");
    }
  },

  async upsertPlayer(score = 0, hits = 0, answers = []) {
    const { error } = await this.client.from("battle_players").upsert({
      room_code: this.roomCode,
      player_id: this.playerId,
      player_name: this.playerName,
      score,
      hits,
      answers,
      updated_at: new Date().toISOString()
    }, { onConflict: "room_code,player_id" });
    if (error) throw error;
  },

  async submitCurrentScore(score, hits, answers) {
    try {
      if (!this.client || !this.roomCode || !this.playerName) return;
      await this.upsertPlayer(score, hits, answers);
      await this.renderLeaderboard();
    } catch (e) {
      this.status(e.message || "分數同步失敗");
    }
  },

  subscribeRoom() {
    if (this.channel) this.client.removeChannel(this.channel);
    this.channel = this.client
      .channel(`battle_${this.roomCode}`)
      .on("postgres_changes", { event: "*", schema: "public", table: "battle_players", filter: `room_code=eq.${this.roomCode}` }, () => this.renderLeaderboard())
      .subscribe();
  },

  async renderLeaderboard() {
    if (!this.client || !this.roomCode) return;
    const { data, error } = await this.client
      .from("battle_players")
      .select("player_name,score,hits,updated_at")
      .eq("room_code", this.roomCode)
      .order("score", { ascending: false })
      .order("hits", { ascending: false });
    if (error) return this.status(error.message);

    const box = document.getElementById("battle-leaderboard");
    if (!box) return;
    if (!data || !data.length) {
      box.innerHTML = `<p class="text-xs text-slate-500">目前還沒有玩家。</p>`;
      return;
    }
    box.innerHTML = data.map((p, idx) => `
      <div class="flex items-center justify-between bg-slate-900 border border-slate-700 rounded-xl px-3 py-2">
        <div class="font-black">${idx + 1}. ${escapeHtml(p.player_name || "玩家")}</div>
        <div class="text-right text-xs"><div class="text-blue-300 font-black">${p.score || 0} 分</div><div class="text-slate-500">命中 ${p.hits || 0}</div></div>
      </div>
    `).join("");
  }
};

function escapeHtml(str) {
  return String(str).replace(/[&<>'"]/g, t => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[t] || t));
}

window.Battle = Battle;
