// Sonidos sintetizados con WebAudio + una pista de música de fondo.
let ac = null;
let master = null;
let ambient = null;
let muted = false;
let music = null;          // elemento <audio> de la música de fondo
let musicGain = null;
let lastType = 0;          // throttle del "teletipo" de texto

const MUSIC_URL = "/static/audio/bg_mrrobot.mp3";
const MUSIC_LEVEL = 0.30;  // bajo, pero audible por debajo del tecleo

function ensure() {
  if (ac) return ac;
  ac = new (window.AudioContext || window.webkitAudioContext)();
  master = ac.createGain();
  master.gain.value = 0.6;
  master.connect(ac.destination);
  return ac;
}

function noiseBuffer(seconds = 2) {
  const buf = ac.createBuffer(1, ac.sampleRate * seconds, ac.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  return buf;
}

function tone(freq, dur, { type = "sine", vol = 0.2, at = 0, slide = null } = {}) {
  if (!ac || muted) return;
  const t = ac.currentTime + at;
  const o = ac.createOscillator();
  const g = ac.createGain();
  o.type = type;
  o.frequency.setValueAtTime(freq, t);
  if (slide) o.frequency.exponentialRampToValueAtTime(slide, t + dur);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(master);
  o.start(t);
  o.stop(t + dur + 0.05);
}

export const sfx = {
  unlock() {
    ensure();
    if (ac.state === "suspended") ac.resume();
  },
  // Tecla mecánica: un "thock" con cuerpo grave + un click corto.
  key() {
    if (!ac || muted) return;
    const t = ac.currentTime;
    const o = ac.createOscillator();
    o.type = "sine";
    o.frequency.setValueAtTime(185 + Math.random() * 45, t);
    o.frequency.exponentialRampToValueAtTime(85, t + 0.05);
    const og = ac.createGain();
    og.gain.setValueAtTime(0.0001, t);
    og.gain.exponentialRampToValueAtTime(0.3, t + 0.004);
    og.gain.exponentialRampToValueAtTime(0.0001, t + 0.07);
    o.connect(og).connect(master);
    o.start(t);
    o.stop(t + 0.09);
    const src = ac.createBufferSource();
    src.buffer = noiseBuffer(0.02);
    const hp = ac.createBiquadFilter();
    hp.type = "highpass";
    hp.frequency.value = 1700 + Math.random() * 600;
    const g = ac.createGain();
    g.gain.setValueAtTime(0.13, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.022);
    src.connect(hp).connect(g).connect(master);
    src.start(t);
  },
  // Sonido de texto (teletipo) cuando la terminal imprime; suave y limitado.
  type() {
    if (!ac || muted) return;
    const now = performance.now();
    if (now - lastType < 55) return;
    lastType = now;
    const t = ac.currentTime;
    const o = ac.createOscillator();
    o.type = "square";
    o.frequency.setValueAtTime(600 + Math.random() * 220, t);
    const g = ac.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.045, t + 0.005);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.03);
    o.connect(g).connect(master);
    o.start(t);
    o.stop(t + 0.05);
  },
  enter() { tone(180, 0.08, { type: "square", vol: 0.05 }); },
  ping() { tone(880, 0.15, { vol: 0.12 }); tone(1320, 0.25, { vol: 0.1, at: 0.09 }); },
  success() { [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.22, { type: "triangle", vol: 0.12, at: i * 0.08 })); },
  alarm() {
    for (let i = 0; i < 4; i++) {
      tone(740, 0.22, { type: "sawtooth", vol: 0.07, at: i * 0.44 });
      tone(520, 0.22, { type: "sawtooth", vol: 0.07, at: i * 0.44 + 0.22 });
    }
  },
  warn() { tone(440, 0.18, { type: "square", vol: 0.05 }); tone(330, 0.25, { type: "square", vol: 0.05, at: 0.16 }); },
  fail() { tone(300, 1.2, { type: "sawtooth", vol: 0.1, slide: 60 }); },
  whoosh() { tone(120, 0.6, { type: "sine", vol: 0.08, slide: 40 }); },
  startAmbient() {
    if (!ac || ambient) return;
    const rain = ac.createBufferSource();
    rain.buffer = noiseBuffer(3);
    rain.loop = true;
    const lp = ac.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.value = 1400;
    const rg = ac.createGain();
    rg.gain.value = 0.05;
    rain.connect(lp).connect(rg).connect(master);
    rain.start();
    const hum = ac.createOscillator();
    hum.frequency.value = 55;
    const hg = ac.createGain();
    hg.gain.value = 0.025;
    hum.connect(hg).connect(master);
    hum.start();
    const fan = ac.createBufferSource();
    fan.buffer = noiseBuffer(2);
    fan.loop = true;
    const bp = ac.createBiquadFilter();
    bp.type = "bandpass";
    bp.frequency.value = 300;
    const fg = ac.createGain();
    fg.gain.value = 0.03;
    fan.connect(bp).connect(fg).connect(master);
    fan.start();
    ambient = { rain, hum, fan };
  },
  // Música de fondo (Mr.
  startMusic() {
    if (!ac || music) return;
    const el = new Audio(MUSIC_URL);
    el.loop = true;
    el.preload = "auto";
    el.crossOrigin = "anonymous";
    musicGain = ac.createGain();
    musicGain.gain.value = MUSIC_LEVEL;
    try {
      const node = ac.createMediaElementSource(el);
      node.connect(musicGain).connect(master);
    } catch (e) {
      el.volume = MUSIC_LEVEL * 0.6;  // respaldo si el navegador no permite el ruteo
    }
    el.play().catch(() => {});
    music = el;
  },
  setMuted(m) {
    muted = m;
    if (master) master.gain.value = m ? 0 : 0.6;
    if (music) music.muted = m;  // por si el ruteo al grafo no está disponible
  },
  get muted() { return muted; },
};
