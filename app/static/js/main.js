import { World } from "./scene.js";
import { Terminal } from "./terminal.js";
import { SiemScreen, OpsScreen } from "./screens.js";
import { sfx } from "./audio.js";

const $ = (id) => document.getElementById(id);
const ESC = "\x1b";
const col = (c, t) => `${ESC}${c}${t}${ESC}0`;

const state = {
  player: null,
  roles: [],
  role: null,
  game: null,
  inGame: false,
  ending: false,
  poll: null,
  elapsed: 0,
  elapsedAt: 0,
  lastEndEvent: null,
};

// ---------- API ----------
async function api(path, opts = {}) {
  const res = await fetch(`/api${path}`, {
    method: opts.method || "GET",
    headers: opts.body ? { "Content-Type": "application/json" } : {},
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: "same-origin",
  });
  let data = {};
  try { data = await res.json(); } catch { /* sin cuerpo */ }
  if (!res.ok) {
    const err = new Error(data.error || `Error ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ---------- pantallas ----------
function show(id) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("show", s.id === id));
}
function hideScreens() {
  document.querySelectorAll(".screen").forEach((s) => s.classList.remove("show"));
}

// ---------- terminal y monitores ---------- Canvas de más resolución (1600×1000) con fuente escalada: mismo diseño, texto más nítido en el monitor.
const term = new Terminal({ onSubmit: sendCommand, width: 1600, height: 1000, fontSize: 26 });
term.onReveal = () => sfx.type();
const siem = new SiemScreen();
const ops = new OpsScreen();

let world;
try {
  world = new World($("gl"), {
    term: term.canvas, siem: siem.canvas, ops: ops.canvas,
    onProgress: (p, txt) => { $("loadBar").style.width = `${p * 100}%`; $("loadText").textContent = txt; },
  });
} catch (e) {
  console.error(e);
  $("loadText").textContent = "Tu navegador no soporta WebGL. Activa la aceleración por hardware.";
}

function loop(t) {
  requestAnimationFrame(loop);
  let changed = false;
  if (term.update(t)) { world.markScreen("term"); changed = true; }
  if (siem.update(t)) { world.markScreen("siem"); changed = true; }
  if (ops.update(t)) { world.markScreen("ops"); changed = true; }
  world.frame(changed);
  tickClock();
}

// ---------- arranque ----------
async function boot() {
  try { await document.fonts.ready; } catch { /* ok */ }
  term.measure();
  if (!world) return;
  requestAnimationFrame(loop);
  setTimeout(async () => {
    try {
      const me = await api("/me");
      state.player = me.player;
      await showRoles(me.active);
    } catch {
      showLogin();
    }
  }, 500);
}

const BOOT_LINES = [
  "[ OK ] montando /dev/nullsector",
  "[ OK ] túnel cifrado establecido (wg0)",
  "[ OK ] ocultando huella de red",
  "[ .. ] verificando identidad del operador",
];

function showLogin() {
  show("login");
  const log = $("bootLog");
  log.textContent = "";
  let i = 0;
  const step = () => {
    if (i >= BOOT_LINES.length) return;
    log.textContent += BOOT_LINES[i++] + "\n";
    setTimeout(step, 260);
  };
  step();
  setTimeout(() => $("alias").focus(), 300);
}

async function auth(kind) {
  sfx.unlock();
  $("loginError").textContent = "";
  try {
    const data = await api(`/auth/${kind}`, { method: "POST", body: { alias: $("alias").value.trim(), pin: $("pin").value } });
    state.player = data.player;
    const me = await api("/me");
    await showRoles(me.active);
  } catch (e) {
    $("loginError").textContent = e.message;
    sfx.warn();
  }
}

$("loginForm").addEventListener("submit", (e) => { e.preventDefault(); auth("login"); });
$("registerBtn").addEventListener("click", () => auth("register"));
$("logoutBtn").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  state.player = null;
  showLogin();
});

// ---------- roles ----------
async function showRoles(active) {
  stopGame();
  world.setMode("menu");
  const [{ roles }, { leaders }] = await Promise.all([api("/roles"), api("/leaderboard")]);
  state.roles = roles;
  $("whoAlias").textContent = state.player.alias;
  $("whoXp").textContent = state.player.xp;
  const box = $("roleCards");
  box.innerHTML = "";
  for (const r of roles) {
    const card = document.createElement("div");
    card.className = "card";
    card.style.setProperty("--c", r.color);
    card.innerHTML = `
      <span class="kicker">${r.tagline}</span>
      <h3>${r.name}</h3>
      <p>${r.desc}</p>
      <div class="skills">${r.skills.map((s) => `<span>${s}</span>`).join("")}</div>
      <div class="mission">misión · ${r.mission.difficulty}<b>${r.mission.title}</b></div>`;
    const prog = r.total ? `<span class="prog">${r.completed}/${r.total}</span>` : "";
    card.querySelector(".mission").innerHTML = `niveles · ${r.total || 6}${prog}`;
    card.addEventListener("click", () => showLevels(r));
    card.addEventListener("mouseenter", () => sfx.key());
    box.appendChild(card);
  }
  $("leaders").innerHTML = leaders.map((l) => `<li>${escapeHtml(l.alias)} — ${l.xp} xp</li>`).join("") || "<li>nadie todavía</li>";
  if (active) {
    $("resumeBox").classList.remove("hidden");
    $("resumeName").textContent = `${active.mission.title} (${roles.find((r) => r.id === active.role)?.name || active.role})`;
  } else {
    $("resumeBox").classList.add("hidden");
  }
  show("roles");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- niveles ----------
const LVL_TONE = ["#8aa0b4", "#20e3a2", "#6ee36e", "#ffd23f", "#ff9d3f", "#ff3b5c"];

function showLevels(role) {
  sfx.enter();
  state.role = role;
  world.setAccent(role.color);
  $("levelsRoleName").textContent = role.name;
  $("levelsTagline").textContent = role.tagline;
  $("levelsProgress").textContent = `${role.completed}/${role.total}`;
  const box = $("levelList");
  box.innerHTML = "";
  for (const lv of role.levels) {
    const el = document.createElement("div");
    el.className = "level" + (lv.completed ? " done" : "") + (lv.level === 0 ? " tutorial" : "");
    el.style.setProperty("--c", role.color);
    const tone = LVL_TONE[lv.level] || role.color;
    const teaches = (lv.teaches || []).map((t) => `<span>${escapeHtml(t)}</span>`).join("");
    const meta = [lv.pressure ? "⏱ " + escapeHtml(lv.pressure) : "práctica sin presión", `~${lv.minutes} min`, `${lv.objectives} objetivos`];
    el.innerHTML = `
      <div class="lv-badge" style="--t:${tone}">${lv.level === 0 ? "T" : lv.level}</div>
      <div class="lv-body">
        <div class="lv-top"><span class="lv-diff" style="color:${tone}">${escapeHtml(lv.difficulty)}</span>${lv.completed ? `<span class="lv-best">✔ mejor: ${lv.best} pts</span>` : ""}</div>
        <h3>${escapeHtml(lv.title)}</h3>
        <p>${escapeHtml(lv.summary)}</p>
        <div class="lv-teach">${teaches}</div>
        <div class="lv-meta mono">${meta.join(" · ")}</div>
      </div>
      <div class="lv-go">${lv.completed ? "repetir ›" : "jugar ›"}</div>`;
    el.addEventListener("click", () => startMission(lv.id));
    el.addEventListener("mouseenter", () => sfx.key());
    box.appendChild(el);
  }
  show("levels");
}

$("backRoles").addEventListener("click", async () => showRoles((await api("/me")).active));

async function startMission(missionId) {
  sfx.unlock();
  sfx.enter();
  try {
    const data = await api("/game/start", { method: "POST", body: { mission: missionId } });
    showBriefing(data, false);
  } catch (e) {
    alert(e.message);
  }
}

$("resumeBtn").addEventListener("click", async () => {
  sfx.unlock();
  const data = await api("/game/state");
  state.role = state.roles.find((r) => r.id === data.mission.role);
  enterGame(data, true);
});

// ---------- briefing ----------
function showBriefing(data, resumed) {
  show("briefing");
  $("briefRole").textContent = `${state.role.name.toUpperCase()} // ${data.mission.codename}`;
  $("briefTitle").textContent = data.mission.title;
  const el = $("briefText");
  el.textContent = "";
  const text = data.mission.summary + "\n\n" + data.briefing.map((l) => "› " + l).join("\n");
  let i = 0;
  clearInterval(state.typer);
  state.typer = setInterval(() => {
    el.textContent = text.slice(0, i += 3);
    if (i % 6 === 0) sfx.type();
    if (i >= text.length) clearInterval(state.typer);
  }, 16);
  $("beginBtn").onclick = () => {
    clearInterval(state.typer);
    enterGame(data, resumed);
  };
}

// ---------- juego ----------
function banner(data) {
  const lines = [
    col("d", "┌──────────────────────────────────────────────────────────────┐"),
    col("d", "│ ") + col("r", "nullsector") + col("d", " :: canal seguro :: ") + col("w", data.mission.codename.padEnd(30)) + col("d", "│"),
    col("d", "└──────────────────────────────────────────────────────────────┘"),
    "",
  ];
  for (const l of data.briefing) lines.push(col("c", "› ") + l);
  lines.push("", col("y", "Escribe 'help' para ver comandos y 'objetivos' para tu misión."), "");
  return lines;
}

function enterGame(data, resumed) {
  hideScreens();
  $("hud").classList.remove("hidden");
  state.inGame = true;
  state.ending = data.status !== "active";
  state.game = data;
  const color = state.role?.color || "#39ff7a";
  world.setAccent(color);
  world.setMode("seated");
  sfx.startAmbient();
  sfx.startMusic();
  sfx.whoosh();
  term.reset();
  term.completions = data.completions || [];
  term.setHistory(data.history || []);
  term.print(banner(data));
  if (resumed) term.print([col("y", "[sesión restaurada]"), ""]);
  siem.reset();
  ops.set(data.mission, color, null);
  $("hudRole").textContent = state.role?.name || "";
  $("hudTitle").textContent = data.mission.title;
  $("hudHint").style.opacity = 1;
  apply(data);
  clearInterval(state.poll);
  state.poll = setInterval(poll, 3000);
}

function stopGame() {
  state.inGame = false;
  clearInterval(state.poll);
  $("hud").classList.add("hidden");
  document.body.classList.remove("alarm");
  $("toasts").innerHTML = "";
  $("timers").innerHTML = "";
}

async function sendCommand(line) {
  sfx.enter();
  try {
    const data = await api("/game/cmd", { method: "POST", body: { line } });
    apply(data);
  } catch (e) {
    term.print([col("r", `[conexión] ${e.message}`)]);
    if (e.status === 401) setTimeout(showLogin, 1500);
  } finally {
    term.done();
  }
}

async function poll() {
  if (!state.inGame || term.busy || document.hidden) return;
  try {
    apply(await api("/game/tick"));
  } catch (e) {
    if (e.status === 404 || e.status === 401) stopGame();
  }
}

function apply(data) {
  if (data.clear) term.clear();
  if (data.output?.length) term.print(data.output);
  term.setPrompt(data.prompt);
  for (const ev of data.events || []) handleEvent(ev);
  renderTimers(data.timers || []);
  siem.timers = data.timers || [];
  ops.set(null, null, data);
  renderHud(data);
  if (data.status && data.status !== "active" && !state.ending) {
    state.ending = true;
    setTimeout(() => endGame(data), 2600);
  }
}

function renderHud(data) {
  $("hudScore").textContent = data.score;
  state.elapsed = data.elapsed || 0;
  state.elapsedAt = performance.now();
  const m = data.meter;
  if (m) {
    $("meterLabel").textContent = m.label;
    const pct = (m.value / m.max) * 100;
    const fill = $("meterFill");
    fill.style.width = `${pct}%`;
    const danger = m.direction === "up" ? pct : 100 - pct;
    const meter = fill.parentElement;
    meter.classList.toggle("warn", danger > 40 && danger <= 70);
    meter.classList.toggle("danger", danger > 70);
    $("meterValue").textContent = m.format === "time" ? fmtTime(m.value) : `${m.value}%`;
  }
  const cur = data.objectives?.find((o) => !o.done);
  $("hudObjective").innerHTML = cur
    ? `<span class="lbl">OBJETIVO ACTUAL</span>${escapeHtml(cur.title)}`
    : `<span class="lbl">OBJETIVOS</span>todos completados`;
}

function fmtTime(s) {
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function tickClock() {
  if (!state.inGame) return;
  const s = state.elapsed + Math.floor((performance.now() - state.elapsedAt) / 1000);
  const el = $("hudClock");
  const txt = fmtTime(s);
  if (el.textContent !== txt) el.textContent = txt;
}

function renderTimers(timers) {
  const box = $("timers");
  box.innerHTML = "";
  for (const t of timers) {
    state.timerMax = state.timerMax || {};
    if (!(t.id in state.timerMax)) state.timerMax[t.id] = Math.max(t.remaining, 1);
    const max = state.timerMax[t.id];
    const div = document.createElement("div");
    div.className = "timer";
    div.innerHTML = `${escapeHtml(t.title)} <b>${fmtTime(t.remaining)}</b><div class="bar"><span style="width:${(t.remaining / max) * 100}%"></span></div>`;
    box.appendChild(div);
  }
  document.body.classList.toggle("alarm", timers.some((t) => t.remaining < 30));
}

function handleEvent(ev) {
  if (ev.kind === "end") {
    state.lastEndEvent = ev;
    return;
  }
  siem.push(ev);
  toast(ev);
  if (ev.kind === "objective") {
    sfx.success();
    world.pulseGlitch(0.3);
  } else if (ev.kind === "msg") {
    sfx.ping();
    world.pulseGlitch(0.4);
  } else if (ev.severity === "critical") {
    sfx.alarm();
    world.setAlarm(1);
    world.pulseGlitch(1);
    flashAlarm();
  } else if (ev.severity === "high") {
    sfx.alarm();
    world.setAlarm(0.7);
    world.pulseGlitch(0.7);
    flashAlarm();
  } else {
    sfx.warn();
  }
}

function flashAlarm() {
  document.body.classList.add("alarm");
  clearTimeout(state.alarmT);
  state.alarmT = setTimeout(() => {
    if (!document.querySelector(".timer")) document.body.classList.remove("alarm");
  }, 3500);
}

function toast(ev) {
  const box = $("toasts");
  const div = document.createElement("div");
  const cls = ev.kind === "msg" ? "msg" : ev.severity;
  div.className = `toast ${cls}`;
  div.innerHTML = `<span class="from">${escapeHtml(ev.sender || "")}</span><span class="t">${escapeHtml(ev.title || "")}</span>${escapeHtml(ev.text || "")}`;
  box.prepend(div);
  while (box.children.length > 4) box.lastChild.remove();
  const life = ev.kind === "objective" ? 4500 : ev.severity === "critical" ? 12000 : 9000;
  setTimeout(() => {
    div.classList.add("out");
    setTimeout(() => div.remove(), 400);
  }, life);
}

async function endGame(data) {
  clearInterval(state.poll);
  const win = data.status === "completed";
  win ? sfx.success() : sfx.fail();
  world.pulseGlitch(1);
  stopGame();
  const end = $("end");
  end.classList.toggle("win", win);
  end.classList.toggle("lose", !win);
  const title = win ? "MISIÓN CUMPLIDA" : "MISIÓN FALLIDA";
  $("endTitle").textContent = title;
  $("endTitle").dataset.text = title;
  $("endText").textContent = state.lastEndEvent?.text || "";
  $("endScore").textContent = data.score;
  show("end");
  try { state.player = (await api("/me")).player; } catch { /* ok */ }
}
$("endBtn").addEventListener("click", async () => showRoles((await api("/me")).active));

// ---------- entrada ----------
function focusTerm() {
  if (world.mode !== "focus-term") sfx.whoosh();
  world.setMode("focus-term");
  term.focused = true;
  term.dirty = true;
  $("hudHint").style.opacity = 0;
}

function unfocus() {
  world.setMode("seated");
  term.focused = false;
  term.dirty = true;
}

const NAV_KEYS = ["Enter", "Backspace", "Tab", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Delete", "Home", "End", "PageUp", "PageDown"];

document.addEventListener("keydown", (e) => {
  if (!state.inGame) return;
  if ($("pause").classList.contains("show")) {
    if (e.key === "Escape") closePause();
    return;
  }
  if (e.key === "Escape") {
    e.preventDefault();
    if (world.mode.startsWith("focus")) unfocus();
    else openPause();
    return;
  }
  const relevant = e.key.length === 1 || NAV_KEYS.includes(e.key) || e.ctrlKey;
  if (!relevant) return;
  if (world.mode !== "focus-term") {
    if (e.key.length === 1 || e.key === "Enter") focusTerm();
    else if (e.key !== "PageUp" && e.key !== "PageDown") return;
  }
  if (term.handleKey(e)) {
    e.preventDefault();
    if (e.key.length === 1 || e.key === "Backspace") {
      sfx.key();
      world.pressKey();
    }
  }
});

document.addEventListener("paste", (e) => {
  if (!state.inGame || $("pause").classList.contains("show")) return;
  const text = e.clipboardData?.getData("text");
  if (text) {
    focusTerm();
    term.paste(text);
    e.preventDefault();
  }
});

$("gl").addEventListener("wheel", (e) => {
  if (state.inGame && world.mode === "focus-term") term.scrollBy(e.deltaY < 0 ? 3 : -3);
}, { passive: true });

$("gl").addEventListener("click", (e) => {
  if (!state.inGame) return;
  sfx.unlock();
  const hit = world.pick(e.clientX, e.clientY);
  if (hit === "term") focusTerm();
  else if (hit) {
    sfx.whoosh();
    world.setMode(`focus-${hit}`);
    term.focused = false;
    term.dirty = true;
  } else if (world.mode !== "seated") unfocus();
});

// ---------- pausa ----------
function openPause() {
  show("pause");
}
function closePause() {
  hideScreens();
}
$("resumeGame").addEventListener("click", closePause);
$("toggleSound").addEventListener("click", () => {
  sfx.setMuted(!sfx.muted);
  $("toggleSound").textContent = `sonido: ${sfx.muted ? "off" : "on"}`;
});
// Cicla: auto → alto → medio → bajo → auto. En "auto" la calidad se ajusta sola.
const FX_CYCLE = ["auto", "alto", "medio", "bajo"];
const FX_LABEL = { auto: "auto", alto: "altos", medio: "medios", bajo: "bajos" };
$("toggleFx").addEventListener("click", () => {
  const cur = world.autoQuality ? "auto" : world.quality;
  const next = FX_CYCLE[(FX_CYCLE.indexOf(cur) + 1) % FX_CYCLE.length];
  world.autoQuality = next === "auto";
  if (next !== "auto") world.setQuality(next);
  $("toggleFx").textContent = `efectos: ${FX_LABEL[next]}`;
});
$("toRoles").addEventListener("click", async () => showRoles((await api("/me")).active));
$("abandonBtn").addEventListener("click", async () => {
  if (!confirm("¿Abandonar la misión? Perderás el progreso.")) return;
  await api("/game/abandon", { method: "POST" });
  showRoles(null);
});

if (new URLSearchParams(location.search).has("debug")) {
  window.__send = (l) => { if (!term.busy) { term.input = l; term.cursor = l.length; term.submit(); } };
  // HUD de depuración: FPS + nivel de calidad actual.
  const hud = document.createElement("div");
  hud.style.cssText = "position:fixed;top:8px;left:8px;z-index:9999;font:12px/1.4 monospace;color:#5fd98a;background:rgba(0,0,0,.6);padding:4px 8px;border-radius:6px;pointer-events:none;white-space:pre";
  document.body.appendChild(hud);
  setInterval(() => {
    const q = world.autoQuality ? `auto→${world.quality}` : world.quality;
    hud.textContent = `FPS ${world.fps || "--"}   calidad: ${q}`;
  }, 500);
}

boot();
