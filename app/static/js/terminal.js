// Terminal dibujada en un <canvas> que se usa como textura del monitor 3D.
const ESC = "\x1b";
// Paleta suavizada: menos neón para que el texto no se vea "quemado".
const COLORS = {
  g: "#5fd98a", r: "#ff6072", y: "#ead27a", c: "#6fcfe6", m: "#e07ad8",
  b: "#7fb0e6", w: "#eef4ef", d: "#5a7466", default: "#c4d4c8", pb: "#2b9fe6",
};

// Tema oh-my-posh (powerline) para el prompt activo.
const PL = {
  os: { bg: "#546e7a", fg: "#bfe9f2" },
  path: { bg: "#14c2dd", fg: "#0c2731" },
  git: { bg: "#a2c4e0", fg: "#15232e" },
  ok: { bg: "#2f8f3a", fg: "#eafff0" },
  err: { bg: "#f1184c", fg: "#ffffff" },
  arrow: "#2b9fe6",
};

function parse(line) {
  const segs = [];
  let color = "default";
  let buf = "";
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === ESC && i + 1 < line.length) {
      if (buf) segs.push({ text: buf, color });
      buf = "";
      const code = line[i + 1];
      color = code === "0" ? "default" : code;
      i++;
      continue;
    }
    buf += ch === "\t" ? "    " : ch;
  }
  if (buf || !segs.length) segs.push({ text: buf, color });
  return segs;
}

function wrap(segs, cols) {
  const rows = [];
  let row = [];
  let len = 0;
  for (const s of segs) {
    let text = s.text;
    while (text.length) {
      const room = cols - len;
      const part = text.slice(0, room);
      row.push({ text: part, color: s.color });
      len += part.length;
      text = text.slice(Math.max(1, part.length));
      if (len >= cols) {
        rows.push(row);
        row = [];
        len = 0;
      }
    }
  }
  if (row.length || !rows.length) rows.push(row);
  return rows;
}

export class Terminal {
  constructor({ width = 1280, height = 800, fontSize = 21, onSubmit, completions = [] }) {
    this.canvas = document.createElement("canvas");
    this.canvas.width = width;
    this.canvas.height = height;
    this.ctx = this.canvas.getContext("2d");
    this.fontSize = fontSize;
    this.lineH = Math.round(fontSize * 1.32);
    // Padding proporcional al tamaño de fuente: así se puede subir la resolución del canvas (más nitidez) escalando fontSize sin romper el diseño.
    this.padX = Math.round(fontSize * 1.6);
    this.padY = Math.round(fontSize * 1.43);
    this.onSubmit = onSubmit;
    this.completions = completions;
    this.rows = [];
    this.queue = [];
    this.input = "";
    this.cursor = 0;
    this.history = [];
    this.histIdx = -1;
    this.scroll = 0;
    this.busy = false;
    this.focused = false;
    this.prompt = { user: "ghost", host: "nullbox", cwd: "~", mode: null };
    this.home = "/home/ghost";
    this.dirty = true;
    this.lastBlink = 0;
    this.blinkOn = true;
    this.measure();
  }

  measure() {
    this.ctx.font = `${this.fontSize}px "JetBrains Mono", monospace`;
    this.charW = this.ctx.measureText("M").width;
    this.cols = Math.floor((this.canvas.width - this.padX * 2) / this.charW);
    this.visibleRows = Math.floor((this.canvas.height - this.padY * 2) / this.lineH);
    this._buildBg();
    this.dirty = true;
  }

  // Fondo (degradado + scanlines + vinneta) pre-renderizado una sola vez: antes se redibujaba entero en cada fotograma, incluso al parpadear el cursor.
  _buildBg() {
    const W = this.canvas.width, H = this.canvas.height;
    const bg = this._bg || (this._bg = document.createElement("canvas"));
    bg.width = W; bg.height = H;
    const ctx = bg.getContext("2d");
    ctx.fillStyle = "#020805";
    ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.1, W / 2, H / 2, H * 0.9);
    g.addColorStop(0, "rgba(20,60,35,0.35)");
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = "rgba(0,0,0,0.18)";
    for (let y = 0; y < H; y += 3) ctx.fillRect(0, y, W, 1);
    const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, W * 0.75);
    v.addColorStop(0, "rgba(0,0,0,0)");
    v.addColorStop(1, "rgba(0,0,0,0.55)");
    ctx.fillStyle = v;
    ctx.fillRect(0, 0, W, H);
  }

  reset() {
    this.rows = [];
    this.queue = [];
    this.input = "";
    this.cursor = 0;
    this.scroll = 0;
    this.dirty = true;
  }

  setPrompt(p) {
    if (!p) return;
    this.prompt = p;
    if (p.cwd && p.user && !p.mode) {
      this.home = p.user === "root" ? "/root" : `/home/${p.user}`;
    }
    this.dirty = true;
  }

  setHistory(list) {
    this.history = (list || []).slice();
    this.histIdx = -1;
  }

  shortCwd() {
    let cwd = this.prompt.cwd || "/";
    if (cwd === this.home) return "~";
    if (cwd.startsWith(this.home + "/")) return "~" + cwd.slice(this.home.length);
    return cwd;
  }

  // Eco compacto que queda en el historial (barato de redibujar): "➜ ruta  cmd".
  promptSegs() {
    const p = this.prompt;
    if (p.mode === "password") return [{ text: "🔒 ", color: "y" }];
    if (p.mode === "ftp") return [{ text: "ftp> ", color: "default" }];
    const folder = this.shortCwd().split("/").filter(Boolean).pop() || "~";
    return [
      { text: "➜ ", color: "pb" },
      { text: folder + " ", color: "d" },
    ];
  }

  // Línea de entrada activa (segunda línea del prompt oh-my-posh).
  inputSegs() {
    if (this.prompt.mode === "password") {
      return [{ text: "🔒 ", color: "y" }, { text: "•".repeat(this.input.length), color: "default" }];
    }
    if (this.prompt.mode === "ftp") {
      return [{ text: "ftp> ", color: "default" }, { text: this.input, color: "default" }];
    }
    return [{ text: "➜ ", color: "pb" }, { text: this.input, color: "default" }];
  }

  // Barra powerline (primera línea): OS · user@host · carpeta · git · estado.
  powerlineSegs() {
    const p = this.prompt;
    const root = p.user === "root";
    const segs = [
      { ...PL.os, icon: "linux", text: ` ${p.user}@${p.host} `, bold: root },
      { ...PL.path, icon: "folder", text: ` ${this.shortCwd()} ` },
    ];
    if (p.git) segs.push({ ...PL.git, icon: "git", text: ` ${p.git} ` });
    const st = p.code ? PL.err : PL.ok;
    segs.push({ ...st, icon: "bolt", text: " " });
    return segs;
  }

  drawPowerline(x0, yTop) {
    const ctx = this.ctx;
    const h = this.lineH, y = yTop + 1, hh = h - 2, cy = yTop + h / 2;
    const fs = Math.round(this.fontSize * 0.82);
    const font = `${fs}px "JetBrains Mono", monospace`;
    const boldFont = `700 ${fs}px "JetBrains Mono", monospace`;
    const cap = Math.round(h * 0.33);           // ancho del separador/triángulo
    const iconW = Math.round(fs * 1.15);
    const segs = this.powerlineSegs();
    ctx.textBaseline = "middle";
    let x = x0;
    segs.forEach((s, i) => {
      ctx.font = s.bold ? boldFont : font;
      const tw = ctx.measureText(s.text).width;
      const w = iconW + tw;
      // separador izquierdo: triángulo del color del segmento anterior
      if (i > 0) {
        const prev = segs[i - 1];
        ctx.fillStyle = prev.bg;
        ctx.beginPath();
        ctx.moveTo(x, y); ctx.lineTo(x + cap, cy); ctx.lineTo(x, y + hh); ctx.closePath(); ctx.fill();
      }
      // cuerpo del segmento
      ctx.fillStyle = s.bg;
      ctx.fillRect(x, y, w, hh);
      // icono + texto
      this.plIcon(s.icon, x + iconW * 0.5, cy, fs * 0.72, s.fg);
      ctx.fillStyle = s.fg;
      ctx.font = s.bold ? boldFont : font;
      ctx.fillText(s.text, x + iconW, cy + 1);
      x += w;
    });
    // cola: triángulo del último color hacia la transparencia
    ctx.fillStyle = segs[segs.length - 1].bg;
    ctx.beginPath();
    ctx.moveTo(x, y); ctx.lineTo(x + cap, cy); ctx.lineTo(x, y + hh); ctx.closePath(); ctx.fill();
    ctx.textBaseline = "top";
  }

  // Iconos vectoriales monocromos (sin depender de Nerd Fonts).
  plIcon(kind, cx, cy, s, col) {
    const ctx = this.ctx;
    ctx.fillStyle = col; ctx.strokeStyle = col;
    if (kind === "linux") {
      ctx.lineWidth = Math.max(1, s * 0.12);
      ctx.beginPath(); ctx.ellipse(cx, cy + s * 0.05, s * 0.45, s * 0.6, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(cx, cy - s * 0.55, s * 0.3, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#15232e";
      ctx.beginPath(); ctx.arc(cx - s * 0.11, cy - s * 0.6, s * 0.07, 0, Math.PI * 2);
      ctx.arc(cx + s * 0.11, cy - s * 0.6, s * 0.07, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#f6a623";
      ctx.beginPath(); ctx.moveTo(cx - s * 0.1, cy - s * 0.46); ctx.lineTo(cx + s * 0.1, cy - s * 0.46); ctx.lineTo(cx, cy - s * 0.33); ctx.closePath(); ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.moveTo(cx - s * 0.3, cy + s * 0.62); ctx.lineTo(cx - s * 0.05, cy + s * 0.62); ctx.lineTo(cx - s * 0.18, cy + s * 0.78); ctx.closePath();
      ctx.moveTo(cx + 0.3 * s, cy + s * 0.62); ctx.lineTo(cx + 0.05 * s, cy + s * 0.62); ctx.lineTo(cx + 0.18 * s, cy + s * 0.78); ctx.closePath(); ctx.fill();
    } else if (kind === "folder") {
      const w = s * 0.95, hgt = s * 0.72;
      ctx.beginPath();
      ctx.moveTo(cx - w / 2, cy - hgt / 2 + s * 0.1);
      ctx.lineTo(cx - w / 2 + s * 0.28, cy - hgt / 2 + s * 0.1);
      ctx.lineTo(cx - w / 2 + s * 0.4, cy - hgt / 2 + s * 0.26);
      ctx.lineTo(cx + w / 2, cy - hgt / 2 + s * 0.26);
      ctx.lineTo(cx + w / 2, cy + hgt / 2);
      ctx.lineTo(cx - w / 2, cy + hgt / 2);
      ctx.closePath(); ctx.fill();
    } else if (kind === "git") {
      ctx.lineWidth = Math.max(1.5, s * 0.16);
      const lx = cx - s * 0.28;
      ctx.beginPath(); ctx.moveTo(lx, cy - s * 0.5); ctx.lineTo(lx, cy + s * 0.5); ctx.stroke();
      ctx.beginPath(); ctx.arc(lx, cy - s * 0.5, s * 0.16, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(lx, cy + s * 0.5, s * 0.16, 0, Math.PI * 2); ctx.fill();
      const bx = cx + s * 0.32;
      ctx.beginPath(); ctx.arc(bx, cy - s * 0.3, s * 0.16, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.moveTo(lx, cy + s * 0.1); ctx.quadraticCurveTo(bx, cy + s * 0.05, bx, cy - s * 0.18); ctx.stroke();
    } else if (kind === "bolt") {
      ctx.beginPath();
      ctx.moveTo(cx + s * 0.18, cy - s * 0.55);
      ctx.lineTo(cx - s * 0.28, cy + s * 0.12);
      ctx.lineTo(cx + s * 0.02, cy + s * 0.12);
      ctx.lineTo(cx - s * 0.12, cy + s * 0.6);
      ctx.lineTo(cx + s * 0.32, cy - s * 0.1);
      ctx.lineTo(cx + s * 0.02, cy - s * 0.1);
      ctx.closePath(); ctx.fill();
    }
  }

  // Agrega líneas a la cola; se "teclean" con un efecto rápido.
  print(lines, immediate = false) {
    for (const l of lines) {
      const rows = wrap(parse(String(l)), this.cols);
      if (immediate) this.rows.push(...rows);
      else this.queue.push(...rows);
    }
    this.scroll = 0;
    this.dirty = true;
  }

  clear() {
    this.rows = [];
    this.queue = [];
    this.scroll = 0;
    this.dirty = true;
  }

  submit() {
    const line = this.input;
    if (this.queue.length) this.rows.push(...this.queue.splice(0));
    const echo = this.prompt.mode === "password" ? [] : this.promptSegs();
    const shown = this.prompt.mode === "password" ? "" : line;
    this.rows.push(...wrap([...echo, { text: shown, color: "default" }], this.cols));
    if (line.trim() && this.prompt.mode !== "password") {
      this.history.push(line);
      if (this.history.length > 100) this.history.shift();
    }
    this.histIdx = -1;
    this.input = "";
    this.cursor = 0;
    this.scroll = 0;
    this.dirty = true;
    this.busy = true;
    this.onSubmit?.(line);
  }

  complete() {
    if (this.queue.length) this.rows.push(...this.queue.splice(0));
    const before = this.input.slice(0, this.cursor);
    if (before.includes(" ")) return;
    const matches = this.completions.filter((c) => c.startsWith(before));
    if (matches.length === 1) {
      this.input = matches[0] + " " + this.input.slice(this.cursor);
      this.cursor = matches[0].length + 1;
    } else if (matches.length > 1) {
      this.rows.push(...wrap([...this.promptSegs(), { text: this.input, color: "default" }], this.cols));
      this.print([matches.join("  ")], true);
    }
    this.dirty = true;
  }

  paste(text) {
    if (this.busy) return;
    const clean = text.replace(/[\r\n]+/g, " ");
    this.input = this.input.slice(0, this.cursor) + clean + this.input.slice(this.cursor);
    this.cursor += clean.length;
    this.dirty = true;
  }

  handleKey(e) {
    const k = e.key;
    if (e.ctrlKey && (k === "l" || k === "L")) { this.clear(); return true; }
    if (e.ctrlKey && (k === "c" || k === "C")) {
      if (window.getSelection()?.toString()) return false;
      this.rows.push(...wrap([...this.promptSegs(), { text: this.input + "^C", color: "default" }], this.cols));
      this.input = ""; this.cursor = 0; this.dirty = true; return true;
    }
    if (e.ctrlKey && (k === "u" || k === "U")) { this.input = this.input.slice(this.cursor); this.cursor = 0; this.dirty = true; return true; }
    if (e.ctrlKey || e.metaKey || e.altKey) return false;
    if (k === "PageUp") { this.scrollBy(this.visibleRows - 2); return true; }
    if (k === "PageDown") { this.scrollBy(-(this.visibleRows - 2)); return true; }
    if (this.busy) return k.length === 1 || ["Enter", "Backspace", "Tab"].includes(k);
    switch (k) {
      case "Enter": this.submit(); return true;
      case "Backspace":
        if (this.cursor > 0) {
          this.input = this.input.slice(0, this.cursor - 1) + this.input.slice(this.cursor);
          this.cursor--;
        }
        break;
      case "Delete": this.input = this.input.slice(0, this.cursor) + this.input.slice(this.cursor + 1); break;
      case "ArrowLeft": this.cursor = Math.max(0, this.cursor - 1); break;
      case "ArrowRight": this.cursor = Math.min(this.input.length, this.cursor + 1); break;
      case "Home": this.cursor = 0; break;
      case "End": this.cursor = this.input.length; break;
      case "ArrowUp":
        if (this.history.length) {
          this.histIdx = this.histIdx < 0 ? this.history.length - 1 : Math.max(0, this.histIdx - 1);
          this.input = this.history[this.histIdx]; this.cursor = this.input.length;
        }
        break;
      case "ArrowDown":
        if (this.histIdx >= 0) {
          this.histIdx++;
          if (this.histIdx >= this.history.length) { this.histIdx = -1; this.input = ""; }
          else this.input = this.history[this.histIdx];
          this.cursor = this.input.length;
        }
        break;
      case "Tab": this.complete(); break;
      default:
        if (k.length === 1) {
          this.input = this.input.slice(0, this.cursor) + k + this.input.slice(this.cursor);
          this.cursor++;
        } else return false;
    }
    this.blinkOn = true;
    this.dirty = true;
    return true;
  }

  scrollBy(n) {
    const total = this.rows.length + 1;
    const max = Math.max(0, total - this.visibleRows);
    this.scroll = Math.max(0, Math.min(max, this.scroll + n));
    this.dirty = true;
  }

  done() {
    this.busy = false;
    this.dirty = true;
  }

  update(time) {
    if (this.queue.length) {
      const n = Math.max(1, Math.ceil(this.queue.length / 8));
      this.rows.push(...this.queue.splice(0, n));
      this.dirty = true;
      this.onReveal?.();   // sonido de texto (teletipo) mientras imprime
    }
    if (this.rows.length > 2000) this.rows.splice(0, this.rows.length - 2000);
    if (time - this.lastBlink > 530) {
      this.lastBlink = time;
      this.blinkOn = !this.blinkOn;
      this.dirty = true;
    }
    if (!this.dirty) return false;
    this.draw();
    this.dirty = false;
    return true;
  }

  draw() {
    const { ctx, canvas } = this;
    const W = canvas.width, H = canvas.height;
    // Fondo cacheado (incluye scanlines + viñeta): un solo blit en vez de cientos de rectángulos y dos degradados por fotograma.
    ctx.drawImage(this._bg, 0, 0);

    ctx.font = `${this.fontSize}px "JetBrains Mono", monospace`;
    ctx.textBaseline = "top";

    // Prompt activo = barra powerline (fila centinela) + línea de entrada "➜ ".
    const live = !this.busy && !this.queue.length;
    const inputRows = live ? wrap(this.inputSegs(), this.cols) : [];
    const showBar = live && this.prompt.mode !== "password" && this.prompt.mode !== "ftp";
    const promptRows = live ? (showBar ? [[{ pl: true }], ...inputRows] : inputRows) : [];
    const all = this.rows.concat(promptRows);
    const end = all.length - this.scroll;
    const start = Math.max(0, end - this.visibleRows);
    const view = all.slice(start, end);

    // Texto sin shadowBlur por segmento (era el mayor costo de CPU).
    let curFont = "";
    view.forEach((row, i) => {
      const y = this.padY + i * this.lineH;
      if (row[0] && row[0].pl) { this.drawPowerline(this.padX, y); curFont = ""; return; }
      let x = this.padX;
      for (const s of row) {
        if (!s.text) continue;
        ctx.fillStyle = COLORS[s.color] || COLORS.default;
        const f = `${s.color === "w" ? "700 " : ""}${this.fontSize}px "JetBrains Mono", monospace`;
        if (f !== curFont) { ctx.font = f; curFont = f; }
        ctx.fillText(s.text, x, y);
        x += s.text.length * this.charW;
      }
    });

    // cursor sobre la línea de entrada (después de "➜ ")
    if (live && this.scroll === 0 && this.blinkOn) {
      const prefix = this.inputSegs()[0].text.length;
      const pos = prefix + (this.prompt.mode === "password" ? this.input.length : this.cursor);
      const rowOff = Math.floor(pos / this.cols);
      const col = pos % this.cols;
      const firstInputRow = view.length - inputRows.length;
      const x = this.padX + col * this.charW;
      const y = this.padY + (firstInputRow + rowOff) * this.lineH;
      ctx.fillStyle = this.focused ? "rgba(120,235,160,0.9)" : "rgba(120,235,160,0.35)";
      ctx.fillRect(x, y + 2, this.charW, this.lineH - 4);
    }
    if (this.busy && this.blinkOn) {
      ctx.fillStyle = COLORS.d;
      ctx.font = `${this.fontSize}px "JetBrains Mono", monospace`;
      ctx.fillText("▌", this.padX, this.padY + view.length * this.lineH);
    }
    if (this.scroll > 0) {
      ctx.fillStyle = "rgba(255,210,63,0.9)";
      ctx.fillText(`↑ historial (${this.scroll})  PgDn para volver`, W - this.padX - 30 * this.charW, 8);
    }
  }
}
