// Monitores secundarios: SIEM (izquierda) y panel de operación (derecha).
const SEV = {
  critical: "#ff2e4d", high: "#ff7a3d", medium: "#ffd23f", low: "#7fa3b8",
  info: "#3fe0ff", success: "#39ff7a", msg: "#c77dff",
};
const FONT = '"JetBrains Mono", monospace';

function base(ctx, W, H, tint) {
  ctx.fillStyle = "#03070a";
  ctx.fillRect(0, 0, W, H);
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, tint);
  g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

function crt(ctx, W, H) {
  ctx.fillStyle = "rgba(0,0,0,0.2)";
  for (let y = 0; y < H; y += 3) ctx.fillRect(0, y, W, 1);
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, W * 0.75);
  v.addColorStop(0, "rgba(0,0,0,0)");
  v.addColorStop(1, "rgba(0,0,0,0.6)");
  ctx.fillStyle = v;
  ctx.fillRect(0, 0, W, H);
}

function wrapText(ctx, text, maxW) {
  const words = String(text).split(" ");
  const lines = [];
  let cur = "";
  for (const w of words) {
    const test = cur ? cur + " " + w : w;
    if (ctx.measureText(test).width > maxW && cur) {
      lines.push(cur);
      cur = w;
    } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}

export class SiemScreen {
  constructor(w = 1024, h = 640) {
    this.canvas = document.createElement("canvas");
    this.canvas.width = w;
    this.canvas.height = h;
    this.ctx = this.canvas.getContext("2d");
    this.events = [];
    this.timers = [];
    this.traffic = Array.from({ length: 120 }, () => 0.3 + Math.random() * 0.2);
    this.spike = 0;
    this.last = 0;
  }

  push(ev) {
    this.events.unshift({ ...ev, at: new Date() });
    this.events = this.events.slice(0, 30);
    if (ev.severity === "critical" || ev.severity === "high") this.spike = 1;
  }

  reset() {
    this.events = [];
    this.timers = [];
  }

  update(t) {
    if (t - this.last < 130) return false;
    this.last = t;
    this.spike *= 0.96;
    this.traffic.shift();
    this.traffic.push(0.25 + Math.random() * 0.2 + this.spike * (0.4 + Math.random() * 0.3));
    this.draw(t);
    return true;
  }

  draw(t) {
    const { ctx, canvas } = this;
    const W = canvas.width, H = canvas.height;
    base(ctx, W, H, "rgba(255,46,77,0.08)");
    ctx.textBaseline = "top";
    ctx.font = `700 26px ${FONT}`;
    ctx.fillStyle = "#ff5a70";
    ctx.fillText("SIEM // EVENTOS EN VIVO", 30, 24);
    ctx.font = `16px ${FONT}`;
    ctx.fillStyle = "#6b8291";
    ctx.fillText(new Date().toLocaleTimeString("es-MX"), W - 130, 30);

    // gráfica de tráfico
    const gx = 30, gy = 70, gw = W - 60, gh = 110;
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    for (let i = 0; i <= 4; i++) {
      ctx.beginPath(); ctx.moveTo(gx, gy + (gh / 4) * i); ctx.lineTo(gx + gw, gy + (gh / 4) * i); ctx.stroke();
    }
    ctx.beginPath();
    this.traffic.forEach((v, i) => {
      const x = gx + (i / (this.traffic.length - 1)) * gw;
      const y = gy + gh - Math.min(1, v) * gh;
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.strokeStyle = this.spike > 0.2 ? "#ff2e4d" : "#3fe0ff";
    ctx.lineWidth = 2;
    ctx.shadowBlur = 10; ctx.shadowColor = ctx.strokeStyle;
    ctx.stroke();
    ctx.shadowBlur = 0; ctx.lineWidth = 1;
    ctx.font = `13px ${FONT}`;
    ctx.fillStyle = "#6b8291";
    ctx.fillText("tráfico de red (pps)", gx, gy + gh + 6);

    let y = 215;
    for (const tm of this.timers) {
      const blink = Math.floor(t / 400) % 2 === 0;
      ctx.fillStyle = blink ? "rgba(255,46,77,0.25)" : "rgba(255,46,77,0.12)";
      ctx.fillRect(30, y, W - 60, 40);
      ctx.strokeStyle = "#ff2e4d"; ctx.strokeRect(30.5, y + 0.5, W - 61, 39);
      ctx.font = `700 18px ${FONT}`; ctx.fillStyle = "#ffd6dc";
      ctx.fillText("⚠ " + tm.title, 44, y + 10);
      const mm = String(Math.floor(tm.remaining / 60)).padStart(2, "0");
      const ss = String(tm.remaining % 60).padStart(2, "0");
      ctx.fillStyle = "#ff2e4d"; ctx.fillText(`${mm}:${ss}`, W - 110, y + 10);
      y += 50;
    }

    ctx.font = `15px ${FONT}`;
    for (const ev of this.events) {
      if (y > H - 50) break;
      const col = SEV[ev.kind === "msg" ? "msg" : ev.severity] || SEV.info;
      ctx.fillStyle = col;
      ctx.fillRect(30, y + 4, 6, 34);
      ctx.font = `13px ${FONT}`;
      ctx.fillStyle = "#6b8291";
      const time = ev.at.toLocaleTimeString("es-MX", { hour12: false });
      ctx.fillText(`${time}  ${String(ev.sender || "").toUpperCase()}  ${String(ev.severity || "").toUpperCase()}`, 48, y + 2);
      ctx.font = `700 17px ${FONT}`;
      ctx.fillStyle = "#e8f2ee";
      const title = ev.title.length > 70 ? ev.title.slice(0, 68) + "…" : ev.title;
      ctx.fillText(title, 48, y + 20);
      y += 50;
    }
    if (!this.events.length && !this.timers.length) {
      ctx.font = `16px ${FONT}`;
      ctx.fillStyle = "#3d5262";
      ctx.fillText("sin eventos… por ahora.", 30, y);
    }
    crt(ctx, W, H);
  }
}

export class OpsScreen {
  constructor(w = 1024, h = 640) {
    this.canvas = document.createElement("canvas");
    this.canvas.width = w;
    this.canvas.height = h;
    this.ctx = this.canvas.getContext("2d");
    this.data = null;
    this.mission = null;
    this.color = "#39ff7a";
    this.last = 0;
    this.nodes = Array.from({ length: 9 }, (_, i) => ({ a: (i / 9) * Math.PI * 2, r: 60 + Math.random() * 50 }));
  }

  set(mission, color, data) {
    if (mission) this.mission = mission;
    if (color) this.color = color;
    if (data) this.data = data;
  }

  update(t) {
    if (t - this.last < 110) return false;
    this.last = t;
    this.draw(t);
    return true;
  }

  draw(t) {
    const { ctx, canvas } = this;
    const W = canvas.width, H = canvas.height;
    base(ctx, W, H, "rgba(57,255,122,0.06)");
    ctx.textBaseline = "top";
    ctx.font = `700 26px ${FONT}`;
    ctx.fillStyle = this.color;
    ctx.fillText("OPERACIÓN // " + (this.mission?.codename || "EN ESPERA"), 30, 24);

    // radar
    const cx = W - 160, cy = 190, R = 120;
    ctx.strokeStyle = "rgba(57,255,122,0.25)";
    for (let i = 1; i <= 3; i++) { ctx.beginPath(); ctx.arc(cx, cy, (R / 3) * i, 0, Math.PI * 2); ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy); ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R); ctx.stroke();
    const sweep = (t / 1400) % (Math.PI * 2);
    const grd = ctx.createConicGradient ? ctx.createConicGradient(sweep - 0.8, cx, cy) : null;
    if (grd) {
      grd.addColorStop(0, "rgba(57,255,122,0)");
      grd.addColorStop(0.12, "rgba(57,255,122,0.35)");
      grd.addColorStop(0.125, "rgba(57,255,122,0)");
      ctx.fillStyle = grd;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.fill();
    }
    for (const n of this.nodes) {
      const x = cx + Math.cos(n.a + t / 20000) * n.r;
      const y = cy + Math.sin(n.a + t / 20000) * n.r * 0.9;
      ctx.fillStyle = this.color;
      ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill();
    }

    const d = this.data;
    if (!d) { crt(ctx, W, H); return; }

    ctx.font = `15px ${FONT}`;
    ctx.fillStyle = "#6b8291";
    ctx.fillText("PUNTOS", 30, 74);
    ctx.font = `700 46px ${FONT}`;
    ctx.fillStyle = "#ffd23f";
    ctx.fillText(String(d.score), 30, 94);

    if (d.meter) {
      const m = d.meter;
      ctx.font = `15px ${FONT}`;
      ctx.fillStyle = "#6b8291";
      ctx.fillText(m.label, 30, 160);
      const pct = m.value / m.max;
      const danger = m.direction === "up" ? pct : 1 - pct;
      const col = danger > 0.7 ? "#ff2e4d" : danger > 0.4 ? "#ffd23f" : "#39ff7a";
      ctx.fillStyle = "rgba(255,255,255,0.08)";
      ctx.fillRect(30, 184, 520, 16);
      ctx.fillStyle = col;
      ctx.shadowBlur = 12; ctx.shadowColor = col;
      ctx.fillRect(30, 184, 520 * pct, 16);
      ctx.shadowBlur = 0;
      ctx.font = `700 18px ${FONT}`;
      ctx.fillText(m.format === "time" ? `${Math.floor(m.value / 60)}:${String(m.value % 60).padStart(2, "0")}` : `${m.value}%`, 562, 182);
    }

    ctx.font = `700 18px ${FONT}`;
    ctx.fillStyle = "#e8f2ee";
    ctx.fillText("OBJETIVOS", 30, 238);
    let y = 270;
    let currentShown = false;
    for (const o of d.objectives) {
      if (y > H - 30) break;
      let mark = "[ ]", col = "#4f6d5c";
      if (o.done) { mark = "[✔]"; col = "#39ff7a"; }
      else if (!currentShown) { mark = "[▸]"; col = "#ffd23f"; currentShown = true; }
      ctx.font = `${col === "#ffd23f" ? "700 " : ""}17px ${FONT}`;
      ctx.fillStyle = col;
      ctx.fillText(`${mark} ${o.title}`, 30, y);
      y += 28;
      if (mark === "[▸]") {
        ctx.font = `14px ${FONT}`;
        ctx.fillStyle = "#93a99c";
        for (const l of wrapText(ctx, o.desc, W - 120).slice(0, 2)) { ctx.fillText(l, 66, y); y += 20; }
        y += 6;
      }
    }
    crt(ctx, W, H);
  }
}

export function stickyNote(text, color = "#ffe56b") {
  const c = document.createElement("canvas");
  c.width = 256; c.height = 256;
  const ctx = c.getContext("2d");
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 256, 256);
  ctx.fillStyle = "rgba(0,0,0,0.05)";
  ctx.fillRect(0, 0, 256, 40);
  ctx.fillStyle = "#1d2a6b";
  ctx.font = "italic 30px 'Segoe Print', 'Comic Sans MS', cursive";
  text.split("\n").forEach((l, i) => ctx.fillText(l, 18, 70 + i * 40));
  return c;
}
