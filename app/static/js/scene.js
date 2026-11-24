import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { stickyNote } from "./screens.js";

// ---------- utilidades de texturas procedurales ----------
function canvasTex(w, h, draw, { repeat = [1, 1], srgb = true } = {}) {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(...repeat);
  t.anisotropy = 8;
  return t;
}

function rng(seed) {
  let s = seed;
  return () => ((s = (s * 16807) % 2147483647) / 2147483647);
}

function noise(ctx, w, h, amount, alpha, r) {
  for (let i = 0; i < amount; i++) {
    const v = Math.floor(r() * 255);
    ctx.fillStyle = `rgba(${v},${v},${v},${alpha * r()})`;
    ctx.fillRect(r() * w, r() * h, 1 + r() * 2, 1 + r() * 2);
  }
}

const woodTex = () => canvasTex(1024, 512, (ctx, w, h) => {
  const r = rng(3);
  ctx.fillStyle = "#2b1a10";
  ctx.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 1) {
    const v = Math.sin(y * 0.09 + Math.sin(y * 0.013) * 6) * 0.5 + 0.5;
    ctx.fillStyle = `rgba(${70 + v * 40},${42 + v * 22},${24 + v * 10},0.55)`;
    ctx.fillRect(0, y, w, 1);
  }
  for (let i = 0; i < 260; i++) {
    ctx.strokeStyle = `rgba(20,10,4,${0.08 + r() * 0.15})`;
    ctx.beginPath();
    const y = r() * h;
    ctx.moveTo(0, y);
    for (let x = 0; x < w; x += 40) ctx.lineTo(x, y + Math.sin(x * 0.01 + i) * 4);
    ctx.stroke();
  }
  noise(ctx, w, h, 4000, 0.12, r);
}, { repeat: [2, 1] });

const concreteTex = (base = "#23262b", seed = 5) => canvasTex(512, 512, (ctx, w, h) => {
  const r = rng(seed);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, w, h);
  for (let i = 0; i < 60; i++) {
    const g = ctx.createRadialGradient(r() * w, r() * h, 0, r() * w, r() * h, 40 + r() * 120);
    g.addColorStop(0, `rgba(0,0,0,${r() * 0.18})`);
    g.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }
  noise(ctx, w, h, 14000, 0.16, r);
}, { repeat: [3, 2] });

const floorTex = () => canvasTex(1024, 1024, (ctx, w, h) => {
  const r = rng(9);
  ctx.fillStyle = "#16120f";
  ctx.fillRect(0, 0, w, h);
  const plank = 128;
  for (let x = 0; x < w; x += plank) {
    const off = r() * h;
    for (let y = -h; y < h; y += 512) {
      const shade = 18 + r() * 14;
      ctx.fillStyle = `rgb(${shade + 10},${shade + 4},${shade})`;
      ctx.fillRect(x + 2, y + off, plank - 4, 508);
      for (let k = 0; k < 30; k++) {
        ctx.fillStyle = `rgba(0,0,0,${r() * 0.15})`;
        ctx.fillRect(x + 2 + r() * (plank - 6), y + off, 1, 508);
      }
    }
  }
  noise(ctx, w, h, 9000, 0.1, r);
}, { repeat: [3, 3] });

const cityTex = () => canvasTex(2048, 1024, (ctx, w, h) => {
  const r = rng(42);
  const sky = ctx.createLinearGradient(0, 0, 0, h);
  sky.addColorStop(0, "#03040b");
  sky.addColorStop(0.55, "#0c0f24");
  sky.addColorStop(0.8, "#2a1630");
  sky.addColorStop(1, "#3a1c22");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, w, h);
  const layers = [
    { n: 40, hmin: 200, hmax: 480, shade: 10, lit: 0.10 },
    { n: 26, hmin: 300, hmax: 760, shade: 6, lit: 0.18 },
  ];
  for (const L of layers) {
    for (let i = 0; i < L.n; i++) {
      const bw = 60 + r() * 140;
      const bh = L.hmin + r() * (L.hmax - L.hmin);
      const x = r() * w;
      const y = h - bh;
      ctx.fillStyle = `rgb(${L.shade},${L.shade + 2},${L.shade + 8})`;
      ctx.fillRect(x, y, bw, bh);
      for (let wy = y + 12; wy < h - 10; wy += 16) {
        for (let wx = x + 8; wx < x + bw - 8; wx += 12) {
          if (r() < L.lit) {
            const warm = r() < 0.7;
            ctx.fillStyle = warm ? `rgba(255,${190 + r() * 50},${110 + r() * 60},${0.5 + r() * 0.5})` : `rgba(120,200,255,${0.4 + r() * 0.5})`;
            ctx.fillRect(wx, wy, 6, 8);
          }
        }
      }
      if (r() < 0.4) {
        ctx.fillStyle = "#ff2030";
        ctx.beginPath(); ctx.arc(x + bw / 2, y - 4, 3, 0, Math.PI * 2); ctx.fill();
      }
    }
  }
  ctx.globalCompositeOperation = "lighter";
  const haze = ctx.createLinearGradient(0, h * 0.6, 0, h);
  haze.addColorStop(0, "rgba(0,0,0,0)");
  haze.addColorStop(1, "rgba(120,40,60,0.25)");
  ctx.fillStyle = haze;
  ctx.fillRect(0, 0, w, h);
}, { repeat: [1, 1] });

const posterTex = () => canvasTex(512, 768, (ctx, w, h) => {
  ctx.fillStyle = "#0b0b0d";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#ff2e4d";
  ctx.lineWidth = 6;
  ctx.strokeRect(30, 30, w - 60, h - 60);
  ctx.font = "700 92px 'Chakra Petch', sans-serif";
  ctx.textAlign = "center";
  const lines = ["NADA", "ES", "SEGURO"];
  lines.forEach((l, i) => {
    ctx.fillStyle = "#3fe0ff"; ctx.fillText(l, w / 2 + 4, 250 + i * 110);
    ctx.fillStyle = "#ff2e4d"; ctx.fillText(l, w / 2 - 4, 250 + i * 110);
    ctx.fillStyle = "#f1f1f1"; ctx.fillText(l, w / 2, 250 + i * 110);
  });
  ctx.font = "24px 'JetBrains Mono', monospace";
  ctx.fillStyle = "#777";
  ctx.fillText("// nullsector", w / 2, h - 80);
  for (let i = 0; i < 14; i++) {
    ctx.fillStyle = `rgba(255,255,255,${Math.random() * 0.12})`;
    ctx.fillRect(0, Math.random() * h, w, 2 + Math.random() * 6);
  }
});

const corkTex = () => canvasTex(512, 384, (ctx, w, h) => {
  const r = rng(77);
  ctx.fillStyle = "#6b4a2b";
  ctx.fillRect(0, 0, w, h);
  noise(ctx, w, h, 20000, 0.35, r);
});

const paperTex = (kind, seed) => canvasTex(256, 320, (ctx, w, h) => {
  const r = rng(seed);
  ctx.fillStyle = "#dcd6c8";
  ctx.fillRect(0, 0, w, h);
  if (kind === "photo") {
    ctx.fillStyle = "#3a3f46";
    ctx.fillRect(16, 16, w - 32, h - 90);
    ctx.fillStyle = "#1c1f24";
    ctx.beginPath(); ctx.arc(w / 2, 120, 50, 0, Math.PI * 2); ctx.fill();
    ctx.fillRect(w / 2 - 70, 170, 140, 60);
  }
  ctx.fillStyle = "#333";
  for (let y = kind === "photo" ? h - 60 : 30; y < h - 20; y += 18) {
    ctx.fillRect(18, y, 40 + r() * (w - 80), 4);
  }
  if (kind !== "photo") {
    ctx.fillStyle = "#c0141f";
    ctx.font = "700 30px monospace";
    ctx.fillText(["HELIX", "IP?", "C2", "VPN"][seed % 4], 30, h - 30);
  }
}, { repeat: [1, 1] });

// ---------- shaders ----------
const RainShader = {
  uniforms: { uTime: { value: 0 } },
  vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
  fragmentShader: `
    uniform float uTime; varying vec2 vUv;
    float h(float n){ return fract(sin(n)*43758.5453); }
    void main(){
      float a = 0.0;
      for (int k = 0; k < 2; k++) {
        float cols = k == 0 ? 70.0 : 130.0;
        vec2 uv = vUv * vec2(cols, 1.0);
        float c = floor(uv.x);
        float sp = 0.25 + h(c + float(k) * 13.1) * 0.5;
        float y = fract(vUv.y * (1.5 + h(c) * 2.0) + uTime * sp + h(c * 3.7));
        float streak = smoothstep(0.0, 0.03, y) * smoothstep(0.22, 0.0, y);
        float x = abs(fract(uv.x) - 0.5);
        a += streak * smoothstep(0.12, 0.0, x) * (k == 0 ? 0.35 : 0.18);
      }
      gl_FragColor = vec4(vec3(0.75, 0.85, 1.0), a);
    }`,
};

const FinalShader = {
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uGlitch: { value: 0 }, uAlarm: { value: 0 } },
  vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uTime; uniform float uGlitch; uniform float uAlarm; varying vec2 vUv;
    float r(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    void main(){
      vec2 uv = vUv;
      float band = step(0.993 - uGlitch * 0.04, r(vec2(floor(uv.y * 40.0), floor(uTime * 12.0))));
      uv.x += band * (r(vec2(uTime)) - 0.5) * 0.02 * (0.2 + uGlitch);
      vec2 d = (uv - 0.5);
      float ca = 0.0006 + uGlitch * 0.005 + dot(d, d) * 0.002;
      vec3 col;
      col.r = texture2D(tDiffuse, uv + d * ca * 2.0).r;
      col.g = texture2D(tDiffuse, uv).g;
      col.b = texture2D(tDiffuse, uv - d * ca * 2.0).b;
      col += (r(uv * 800.0 + uTime) - 0.5) * 0.045;
      col *= 1.0 - dot(d, d) * 1.25;
      col = mix(col, col * vec3(1.35, 0.55, 0.55), uAlarm * 0.35);
      gl_FragColor = vec4(col, 1.0);
    }`,
};

// ---------- escena ----------
export class World {
  constructor(canvas, { onProgress, term, siem, ops } = {}) {
    this.canvas = canvas;
    this.termCanvas = term;
    this.siemCanvas = siem;
    this.opsCanvas = ops;
    this.onProgress = onProgress || (() => {});
    // MSAA (antialias) apagado: en las GPUs Intel integradas (UHD 630 y similares) el driver marca MSAA como lento.
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: "high-performance" });
    this.maxDpr = 1.75;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.maxDpr));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#020305");
    this.scene.fog = new THREE.FogExp2("#05070b", 0.06);
    this.camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.02, 60);
    this.timer = new THREE.Timer();
    this.mode = "menu";
    this.camPos = new THREE.Vector3(2.4, 1.8, 2.6);
    this.camLook = new THREE.Vector3(0, 1.0, -0.3);
    this.curLook = this.camLook.clone();
    this.camera.position.copy(this.camPos);
    this.mouse = new THREE.Vector2();
    this.alarm = 0;
    this.glitch = 0;
    this.quality = "alto";
    this.autoQuality = true;   // ajusta la calidad sola según los FPS
    this.screens = {};
    this.keys = [];
    this.raycaster = new THREE.Raycaster();

    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this._env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environment = this._env;   // se puede apagar en calidad baja
    this.scene.environmentIntensity = 0.12;

    this.build();
    this.setupPost();
    window.addEventListener("resize", () => this.resize());
    window.addEventListener("pointermove", (e) => {
      this.mouse.set((e.clientX / window.innerWidth) * 2 - 1, -(e.clientY / window.innerHeight) * 2 + 1);
    });
  }

  std(color, rough = 0.7, metal = 0, extra = {}) {
    return new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
  }

  box(w, h, d, mat, x, y, z, { cast = true, receive = true, parent = this.scene } = {}) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    m.castShadow = cast;
    m.receiveShadow = receive;
    parent.add(m);
    return m;
  }

  build() {
    const S = this.scene;
    this.onProgress(0.1, "levantando paredes…");

    // --- cuarto ---
    const wallMat = this.std("#ffffff", 0.95, 0, { map: concreteTex() });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), this.std("#ffffff", 0.62, 0, { map: floorTex() }));
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(0, 0, 1.5);
    floor.receiveShadow = true;
    S.add(floor);
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), this.std("#0d0f12", 1));
    ceil.rotation.x = Math.PI / 2;
    ceil.position.set(0, 2.8, 1.5);
    S.add(ceil);
    // pared trasera con hueco de ventana (x -2.3..-0.9, y 0.95..2.25)
    const zW = -0.85;
    this.box(1.7, 2.8, 0.12, wallMat, -3.15, 1.4, zW);
    this.box(4.0, 2.8, 0.12, wallMat, 1.1, 1.4, zW);
    this.box(1.4, 0.95, 0.12, wallMat, -1.6, 0.475, zW);
    this.box(1.4, 0.55, 0.12, wallMat, -1.6, 2.525, zW);
    const sideMat = this.std("#ffffff", 0.95, 0, { map: concreteTex("#1d2025", 8) });
    this.box(0.12, 2.8, 6, sideMat, -3.0, 1.4, 2.1);
    this.box(0.12, 2.8, 6, sideMat, 3.0, 1.4, 2.1);
    this.box(6, 2.8, 0.12, sideMat, 0, 1.4, 5.0);
    // zoclo
    this.box(6, 0.08, 0.02, this.std("#0a0b0d", 0.5), 0, 0.04, zW + 0.07);

    this.onProgress(0.25, "conectando la ciudad…");
    this.buildWindow(zW);
    this.onProgress(0.4, "armando el escritorio…");
    this.buildDesk();
    this.onProgress(0.55, "encendiendo monitores…");
    this.buildMonitors();
    this.buildKeyboard();
    this.buildProps();
    this.onProgress(0.7, "racks y cables…");
    this.buildRack();
    this.buildWallDecor(zW);
    this.buildLights();
    this.buildDust();
    this.onProgress(0.85, "post-procesado…");
  }

  buildWindow(zW) {
    const S = this.scene;
    const frameMat = this.std("#0b0c0e", 0.45, 0.6);
    const x0 = -1.6, y0 = 1.6;
    this.box(1.44, 0.05, 0.16, frameMat, x0, 0.95, zW);
    this.box(1.44, 0.05, 0.16, frameMat, x0, 2.25, zW);
    this.box(0.05, 1.32, 0.16, frameMat, -2.3, y0, zW);
    this.box(0.05, 1.32, 0.16, frameMat, -0.9, y0, zW);
    this.box(0.035, 1.3, 0.1, frameMat, x0, y0, zW);
    this.box(0.06, 0.05, 0.3, frameMat, x0, 0.93, zW + 0.12);
    // persianas semiabiertas
    const slatMat = this.std("#1a1c20", 0.6, 0.2);
    for (let i = 0; i < 16; i++) {
      const s = this.box(1.36, 0.004, 0.05, slatMat, x0, 2.18 - i * 0.055, zW + 0.09);
      s.rotation.x = -0.9;
    }
    // ciudad
    const city = new THREE.Mesh(new THREE.PlaneGeometry(16, 8), new THREE.MeshBasicMaterial({ map: cityTex(), fog: false }));
    city.position.set(-1.5, 2.4, -8);
    S.add(city);
    // vidrio + lluvia
    const glass = new THREE.Mesh(new THREE.PlaneGeometry(1.36, 1.26),
      new THREE.MeshStandardMaterial({ color: "#8aa4c8", roughness: 0.1, metalness: 0, transparent: true, opacity: 0.12, envMapIntensity: 1 }));
    glass.position.set(x0, y0, zW - 0.02);
    S.add(glass);
    this.rain = new THREE.Mesh(new THREE.PlaneGeometry(1.36, 1.26), new THREE.ShaderMaterial({ ...RainShader, transparent: true, depthWrite: false }));
    this.rain.position.set(x0, y0, zW - 0.01);
    S.add(this.rain);
    // haz de luz de luna (falso volumétrico)
    const shaftGeo = new THREE.PlaneGeometry(1.3, 3.2);
    const shaftTex = canvasTex(64, 256, (ctx, w, h) => {
      const g = ctx.createLinearGradient(0, 0, 0, h);
      g.addColorStop(0, "rgba(140,170,255,0.55)");
      g.addColorStop(1, "rgba(140,170,255,0)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
      ctx.globalCompositeOperation = "destination-in";
      const s = ctx.createLinearGradient(0, 0, w, 0);
      s.addColorStop(0, "rgba(0,0,0,0)"); s.addColorStop(0.5, "rgba(0,0,0,1)"); s.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = s; ctx.fillRect(0, 0, w, h);
    });
    const shaft = new THREE.Mesh(shaftGeo, new THREE.MeshBasicMaterial({ map: shaftTex, transparent: true, opacity: 0.07, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    shaft.position.set(-1.35, 1.0, -0.1);
    shaft.rotation.set(-0.75, 0.25, 0);
    S.add(shaft);
  }

  buildDesk() {
    const S = this.scene;
    const top = this.box(2.4, 0.045, 0.85, this.std("#ffffff", 0.48, 0, { map: woodTex() }), 0, 0.735, -0.05);
    top.name = "desk";
    const legMat = this.std("#111214", 0.35, 0.85);
    for (const [x, z] of [[-1.15, 0.33], [1.15, 0.33], [-1.15, -0.43], [1.15, -0.43]]) {
      this.box(0.05, 0.72, 0.05, legMat, x, 0.36, z);
    }
    this.box(2.3, 0.08, 0.02, legMat, 0, 0.66, -0.43);
    // tira LED bajo el escritorio
    const led = this.box(2.3, 0.008, 0.012, new THREE.MeshBasicMaterial({ color: new THREE.Color("#00e5ff").multiplyScalar(2) }), 0, 0.705, 0.36, { cast: false });
    this.ledStrip = led;
    const under = new THREE.PointLight("#00d0ff", 0.6, 1.6, 2);
    under.position.set(0, 0.6, 0.45);
    S.add(under);
    // tapete de escritorio
    const mat = new THREE.Mesh(new RoundedBoxGeometry(0.95, 0.004, 0.36, 2, 0.01), this.std("#0c0d10", 0.9));
    mat.position.set(0.05, 0.76, 0.12);
    mat.receiveShadow = true;
    S.add(mat);
  }

  makeMonitor(w, h, canvas, pos, rotY, glowColor, name) {
    const S = this.scene;
    const g = new THREE.Group();
    const bezel = new THREE.Mesh(new RoundedBoxGeometry(w + 0.03, h + 0.03, 0.028, 3, 0.008), this.std("#0b0c0e", 0.35, 0.2));
    bezel.castShadow = true;
    g.add(bezel);
    const back = new THREE.Mesh(new RoundedBoxGeometry(w * 0.6, h * 0.55, 0.06, 3, 0.02), this.std("#0e0f12", 0.5, 0.2));
    back.position.z = -0.035;
    back.castShadow = true;
    g.add(back);
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    // Anisotropía al máximo que soporte la GPU: clave para que el texto de los monitores (sobre todo los laterales, en ángulo) se vea nítido y no "480p".
    tex.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    // Sin sobre-exposición (antes 1.35 reventaba el verde y disparaba el bloom);
    const screenMat = new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(1.0, 1.0, 1.0), toneMapped: false });
    const screen = new THREE.Mesh(new THREE.PlaneGeometry(w, h), screenMat);
    screen.position.z = 0.0145;
    screen.name = name;
    g.add(screen);
    // base
    const standMat = this.std("#16171a", 0.3, 0.8);
    const footY = 0.764 - pos.y;
    const neckH = (-h / 2) - footY + 0.06;
    const neck = new THREE.Mesh(new THREE.BoxGeometry(0.04, neckH, 0.03), standMat);
    neck.position.set(0, footY + neckH / 2, -0.05);
    neck.castShadow = true;
    g.add(neck);
    const foot = new THREE.Mesh(new RoundedBoxGeometry(0.24, 0.012, 0.17, 2, 0.005), standMat);
    foot.position.set(0, footY, -0.04);
    foot.castShadow = true;
    foot.receiveShadow = true;
    g.add(foot);
    // LED de encendido
    const pled = new THREE.Mesh(new THREE.BoxGeometry(0.006, 0.003, 0.002), new THREE.MeshBasicMaterial({ color: "#3cff8a" }));
    pled.position.set(w / 2 - 0.02, -h / 2 - 0.008, 0.015);
    g.add(pled);
    g.position.copy(pos);
    g.rotation.y = rotY;
    S.add(g);
    // Antes cada monitor tenía una RectAreaLight (de las luces más caras de la GPU).
    this.screens[name] = { mesh: screen, tex, group: g, light: null, w, h };
    return g;
  }

  buildMonitors() {
    this.termCanvas = this.termCanvas || document.createElement("canvas");
    this.siemCanvas = this.siemCanvas || document.createElement("canvas");
    this.opsCanvas = this.opsCanvas || document.createElement("canvas");
    this.makeMonitor(0.64, 0.4, this.termCanvas, new THREE.Vector3(0, 1.0, -0.3), 0, "#39ff7a", "term");
    this.makeMonitor(0.52, 0.325, this.siemCanvas, new THREE.Vector3(-0.66, 0.96, -0.2), 0.42, "#ff3b5c", "siem");
    this.makeMonitor(0.52, 0.325, this.opsCanvas, new THREE.Vector3(0.66, 0.96, -0.2), -0.42, "#3fe0ff", "ops");
    // Resplandor compartido de los monitores sobre el escritorio y el teclado (reemplaza las 3 RectAreaLight por 1 luz puntual barata).
    const glow = new THREE.PointLight("#58d6ff", 0.9, 1.9, 2);
    glow.position.set(0, 1.02, 0.1);
    this.scene.add(glow);
    // notas adhesivas
    const notes = [["chmod 600\nid_rsa!!", "#ffe56b", -0.86, 1.15, -0.23, 0.42], ["no reusar\npasswords", "#ff9ecb", 0.39, 0.82, -0.28, -0.1]];
    for (const [txt, col, x, y, z, ry] of notes) {
      const tex = new THREE.CanvasTexture(stickyNote(txt, col));
      tex.colorSpace = THREE.SRGBColorSpace;
      const n = new THREE.Mesh(new THREE.PlaneGeometry(0.065, 0.065), this.std("#fff", 0.9, 0, { map: tex }));
      n.position.set(x, y, z);
      n.rotation.set(0, ry, (Math.random() - 0.5) * 0.3);
      this.scene.add(n);
    }
  }

  setScreenCanvases(term, siem, ops) {
    for (const [name, c] of [["term", term], ["siem", siem], ["ops", ops]]) {
      const s = this.screens[name];
      s.tex.dispose();
      s.tex = new THREE.CanvasTexture(c);
      s.tex.colorSpace = THREE.SRGBColorSpace;
      s.tex.anisotropy = 8;
      s.mesh.material.map = s.tex;
      s.mesh.material.needsUpdate = true;
    }
  }

  markScreen(name) {
    const s = this.screens[name];
    if (s) s.tex.needsUpdate = true;
  }

  buildKeyboard() {
    const S = this.scene;
    const kb = new THREE.Group();
    const base = new THREE.Mesh(new RoundedBoxGeometry(0.44, 0.022, 0.15, 3, 0.006), this.std("#101114", 0.4, 0.4));
    base.castShadow = true;
    base.receiveShadow = true;
    kb.add(base);
    const glow = new THREE.Mesh(new THREE.BoxGeometry(0.43, 0.004, 0.14), new THREE.MeshBasicMaterial({ color: new THREE.Color("#ff2e4d").multiplyScalar(1.5) }));
    glow.position.y = 0.006;
    kb.add(glow);
    this.kbGlow = glow;
    const keyGeo = new RoundedBoxGeometry(0.024, 0.012, 0.024, 2, 0.004);
    const keyMat = this.std("#1b1c20", 0.55, 0.1);
    const step = 0.0285;
    // Antes cada tecla era una malla aparte (~46 draw calls).
    const specs = [];
    const addKey = (x, z, sx = 1) => specs.push({ x, z, sx });
    for (let r = 0; r < 4; r++) {
      const n = 14 - (r > 1 ? 1 : 0);
      const off = r * 0.006;
      for (let i = 0; i < n; i++) addKey(-0.2 + step / 2 + i * step + off, -0.057 + r * step);
    }
    const zs = -0.057 + 4 * step;
    for (let i = 0; i < 3; i++) addKey(-0.2 + step / 2 + i * step, zs);
    addKey(0, zs, 7.2);
    for (let i = 0; i < 3; i++) addKey(0.2 - step / 2 - i * step, zs);
    this.keyY = 0.016;
    this.keySpecs = specs;
    this.keyUntil = new Float64Array(specs.length);
    this._keyDummy = new THREE.Object3D();
    const km = new THREE.InstancedMesh(keyGeo, keyMat, specs.length);
    km.castShadow = true;
    specs.forEach((s, i) => this._setKeyY(i, this.keyY, km));
    km.instanceMatrix.needsUpdate = true;
    kb.add(km);
    this.keyInst = km;
    kb.position.set(0, 0.77, 0.12);
    kb.rotation.x = 0.05;
    S.add(kb);
    // mouse
    const mouse = new THREE.Mesh(new THREE.CapsuleGeometry(0.022, 0.04, 6, 12), this.std("#121316", 0.35, 0.3));
    mouse.rotation.x = Math.PI / 2;
    mouse.scale.set(1, 1, 0.55);
    mouse.position.set(0.36, 0.77, 0.14);
    mouse.castShadow = true;
    S.add(mouse);
  }

  _setKeyY(i, y, mesh = this.keyInst) {
    const s = this.keySpecs[i], d = this._keyDummy;
    d.position.set(s.x, y, s.z);
    d.scale.set(s.sx, 1, 1);
    d.rotation.set(0, 0, 0);
    d.updateMatrix();
    mesh.setMatrixAt(i, d.matrix);
  }

  pressKey() {
    if (!this.keyInst) return;
    const i = Math.floor(Math.random() * this.keySpecs.length);
    this._setKeyY(i, this.keyY - 0.004);
    this.keyInst.instanceMatrix.needsUpdate = true;
    this.keyUntil[i] = performance.now() + 90;
  }

  buildProps() {
    const S = this.scene;
    // taza con vapor
    const pts = [];
    for (let i = 0; i <= 10; i++) pts.push(new THREE.Vector2(0.035 + Math.sin(i / 10 * 0.3) * 0.004, i * 0.009));
    const mug = new THREE.Mesh(new THREE.LatheGeometry(pts, 32), this.std("#e8e4dc", 0.35, 0, { side: THREE.DoubleSide }));
    mug.position.set(-0.42, 0.758, 0.12);
    mug.castShadow = true;
    S.add(mug);
    const coffee = new THREE.Mesh(new THREE.CircleGeometry(0.036, 24), this.std("#1a0d05", 0.15));
    coffee.rotation.x = -Math.PI / 2;
    coffee.position.set(-0.42, 0.835, 0.12);
    S.add(coffee);
    const handle = new THREE.Mesh(new THREE.TorusGeometry(0.022, 0.006, 8, 16, Math.PI), this.std("#e8e4dc", 0.35));
    handle.position.set(-0.458, 0.8, 0.12);
    handle.rotation.z = Math.PI / 2;
    S.add(handle);
    const steamGeo = new THREE.BufferGeometry();
    const N = 40;
    const sp = new Float32Array(N * 3);
    this.steamSeeds = [];
    for (let i = 0; i < N; i++) this.steamSeeds.push(Math.random());
    steamGeo.setAttribute("position", new THREE.BufferAttribute(sp, 3));
    this.steam = new THREE.Points(steamGeo, new THREE.PointsMaterial({ color: "#cfd8e0", size: 0.018, transparent: true, opacity: 0.06, depthWrite: false, map: this.softDot() }));
    S.add(this.steam);
    // lata de energética
    const can = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.12, 24), this.std("#ffffff", 0.25, 0.8, {
      map: canvasTex(256, 128, (ctx, w, h) => {
        ctx.fillStyle = "#0a0a0a"; ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = "#39ff7a"; ctx.font = "700 46px sans-serif"; ctx.fillText("VOLT", 60, 80);
        ctx.fillStyle = "#39ff7a"; ctx.fillRect(0, 100, w, 6);
      }),
    }));
    can.position.set(0.55, 0.818, 0.18);
    can.castShadow = true;
    S.add(can);
    // libros
    const bookCols = ["#3a1218", "#13233a", "#20301c", "#2b2b2b"];
    bookCols.forEach((c, i) => {
      const b = this.box(0.22, 0.035, 0.16, this.std(c, 0.8), 0.95, 0.775 + i * 0.036, -0.25, {});
      b.rotation.y = (Math.random() - 0.5) * 0.25;
    });
    // lámpara de escritorio
    const lampMat = this.std("#1a1b1e", 0.3, 0.8);
    const lb = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.08, 0.02, 24), lampMat);
    lb.position.set(-1.0, 0.768, -0.25);
    lb.castShadow = true;
    S.add(lb);
    const arm1 = this.box(0.015, 0.45, 0.015, lampMat, -1.0, 0.98, -0.25);
    arm1.rotation.z = -0.15;
    const arm2 = this.box(0.015, 0.35, 0.015, lampMat, -0.9, 1.25, -0.12);
    arm2.rotation.set(0.9, 0, -0.5);
    const head = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.12, 24, 1, true), this.std("#1a1b1e", 0.3, 0.8, { side: THREE.DoubleSide }));
    head.position.set(-0.8, 1.33, -0.02);
    head.rotation.set(0.5, 0, -0.5);
    head.castShadow = true;
    S.add(head);
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.025, 16, 16), new THREE.MeshBasicMaterial({ color: new THREE.Color("#ffcf8a").multiplyScalar(3) }));
    bulb.position.set(-0.79, 1.3, 0.0);
    S.add(bulb);
    this.lamp = new THREE.SpotLight("#ffb56b", 9, 3, 0.75, 0.6, 1.6);
    this.lamp.position.set(-0.78, 1.28, 0.0);
    this.lamp.target.position.set(-0.5, 0.74, 0.15);
    // La lámpara ya NO proyecta sombra: ilumina igual, pero se ahorra un mapa de sombra entero por fotograma.
    this.lamp.castShadow = false;
    S.add(this.lamp, this.lamp.target);
    // cables
    const cableMat = this.std("#0a0a0a", 0.6);
    for (const [x, rx] of [[0, 0.02], [-0.6, 0.05], [0.6, -0.05], [0.1, 0.0]]) {
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(x, 0.85, -0.36), new THREE.Vector3(x + rx, 0.76, -0.42),
        new THREE.Vector3(x * 0.8, 0.5, -0.47), new THREE.Vector3(x * 0.5 + 0.3, 0.05, -0.6),
      ]);
      const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 30, 0.005, 6), cableMat);
      tube.castShadow = true;
      S.add(tube);
    }
  }

  softDot() {
    if (this._dot) return this._dot;
    this._dot = canvasTex(64, 64, (ctx, w, h) => {
      const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      g.addColorStop(0, "rgba(255,255,255,1)");
      g.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    });
    return this._dot;
  }

  buildRack() {
    const S = this.scene;
    const rack = new THREE.Group();
    const frame = this.std("#0b0c0e", 0.4, 0.7);
    this.box(0.6, 1.9, 0.75, frame, 0, 0.95, 0, { parent: rack });
    const unitMat = this.std("#17181b", 0.45, 0.6);
    const ledGeo = new THREE.BoxGeometry(0.008, 0.008, 0.004);
    const ledMat = new THREE.MeshBasicMaterial({ color: "#ffffff" });
    const units = 16;
    this.leds = new THREE.InstancedMesh(ledGeo, ledMat, units * 6);
    let idx = 0;
    const dummy = new THREE.Object3D();
    for (let i = 0; i < units; i++) {
      const y = 0.18 + i * 0.1;
      this.box(0.52, 0.085, 0.02, unitMat, 0, y, 0.38, { parent: rack });
      for (let v = 0; v < 8; v++) this.box(0.004, 0.05, 0.004, this.std("#050506", 0.9), -0.12 + v * 0.025, y, 0.392, { parent: rack, cast: false });
      for (let l = 0; l < 6; l++) {
        dummy.position.set(0.12 + l * 0.022, y + 0.02, 0.392);
        dummy.updateMatrix();
        this.leds.setMatrixAt(idx, dummy.matrix);
        this.leds.setColorAt(idx, new THREE.Color("#39ff7a"));
        idx++;
      }
    }
    rack.add(this.leds);
    // puerta de vidrio
    const door = new THREE.Mesh(new THREE.PlaneGeometry(0.56, 1.82), new THREE.MeshStandardMaterial({ color: "#223", roughness: 0.1, transparent: true, opacity: 0.18, envMapIntensity: 1 }));
    door.position.set(0, 0.95, 0.4);
    rack.add(door);
    // baliza de alarma
    const beacon = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.09, 20), new THREE.MeshStandardMaterial({ color: "#400", emissive: "#ff0020", emissiveIntensity: 0.15, roughness: 0.2, transparent: true, opacity: 0.9 }));
    beacon.position.set(0, 1.95, 0.1);
    rack.add(beacon);
    this.beacon = beacon;
    this.alarmLight = new THREE.PointLight("#ff1030", 0, 6, 1.5);
    this.alarmLight.position.set(0, 2.1, 0.3);
    rack.add(this.alarmLight);
    this.alarmSpot = new THREE.SpotLight("#ff1030", 0, 7, 0.45, 0.5, 1);
    this.alarmSpot.position.set(0, 1.95, 0.1);
    rack.add(this.alarmSpot);
    rack.add(this.alarmSpot.target);
    rack.position.set(2.15, 0, -0.35);
    rack.rotation.y = -0.55;
    S.add(rack);
    this.rack = rack;
  }

  buildWallDecor(zW) {
    const S = this.scene;
    const poster = new THREE.Mesh(new THREE.PlaneGeometry(0.46, 0.69), this.std("#fff", 0.6, 0, { map: posterTex() }));
    poster.position.set(-0.05, 1.82, zW + 0.065);
    poster.castShadow = false;
    S.add(poster);
    // neón
    const neonMat = new THREE.MeshBasicMaterial({ color: new THREE.Color("#ff1f45").multiplyScalar(4) });
    this.neon = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 1.6, 8), neonMat);
    this.neon.rotation.z = Math.PI / 2;
    this.neon.position.set(0.15, 2.35, zW + 0.08);
    S.add(this.neon);
    // Neón: antes RectAreaLight (cara).
    this.neonLight = new THREE.PointLight("#ff1f45", 1.3, 2.4, 2);
    this.neonLight.position.set(0.15, 2.3, zW + 0.22);
    S.add(this.neonLight);
    // corcho con hilos rojos
    const cork = this.box(0.95, 0.68, 0.02, this.std("#fff", 0.95, 0, { map: corkTex() }), 1.25, 1.55, zW + 0.07);
    cork.castShadow = false;
    const pins = [];
    const papers = [[1.0, 1.72, "photo", 1], [1.35, 1.75, "doc", 2], [1.55, 1.45, "photo", 3], [1.1, 1.38, "doc", 4], [1.4, 1.32, "doc", 5]];
    for (const [x, y, kind, seed] of papers) {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(0.14, 0.175), this.std("#fff", 0.9, 0, { map: paperTex(kind, seed) }));
      p.position.set(x, y, zW + 0.083);
      p.rotation.z = (seed % 2 ? 1 : -1) * 0.06 * seed;
      S.add(p);
      const pin = new THREE.Mesh(new THREE.SphereGeometry(0.008, 10, 10), this.std("#d0101d", 0.3));
      pin.position.set(x, y + 0.07, zW + 0.09);
      S.add(pin);
      pins.push(pin.position);
    }
    const strMat = this.std("#c0101a", 0.8);
    const link = (a, b) => {
      const d = new THREE.Vector3().subVectors(b, a);
      const s = new THREE.Mesh(new THREE.CylinderGeometry(0.0018, 0.0018, d.length(), 4), strMat);
      s.position.copy(a).addScaledVector(d, 0.5);
      s.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
      S.add(s);
    };
    link(pins[0], pins[1]); link(pins[1], pins[2]); link(pins[0], pins[3]); link(pins[3], pins[4]); link(pins[2], pins[4]); link(pins[0], pins[4]);
  }

  buildLights() {
    const S = this.scene;
    S.add(new THREE.HemisphereLight("#2a3a66", "#070505", 0.35));
    const moon = new THREE.DirectionalLight("#9fb6ff", 1.6);
    moon.position.set(-2.4, 4.0, -3.6);
    moon.target.position.set(-0.4, 0.4, 1.4);
    moon.castShadow = true;
    moon.shadow.mapSize.set(1024, 1024);
    const sc = moon.shadow.camera;
    sc.left = -3; sc.right = 3; sc.top = 3; sc.bottom = -3; sc.near = 0.5; sc.far = 12;
    moon.shadow.bias = -0.0004;
    moon.shadow.normalBias = 0.02;
    S.add(moon, moon.target);
    const fill = new THREE.PointLight("#3b4f7a", 0.8, 6, 2);
    fill.position.set(0.5, 2.4, 2.2);
    S.add(fill);
    this.shadowLights = [moon];  // solo la luna proyecta sombra
  }

  buildDust() {
    const N = 220;
    const pos = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 3.2;
      pos[i * 3 + 1] = 0.6 + Math.random() * 1.9;
      pos[i * 3 + 2] = -0.7 + Math.random() * 2.2;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    this.dust = new THREE.Points(geo, new THREE.PointsMaterial({ color: "#a8c4ff", size: 0.006, transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending, map: this.softDot() }));
    this.scene.add(this.dust);
  }

  setupPost() {
    const size = new THREE.Vector2(window.innerWidth, window.innerHeight);
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    // Bloom a MEDIA resolución y más tenue: sube FPS (el bloom es el pase más caro) y quita el exceso de brillo del texto.
    this.bloom = new UnrealBloomPass(size.clone().multiplyScalar(0.5), 0.32, 0.5, 0.85);
    this.composer.addPass(this.bloom);
    this.composer.addPass(new OutputPass());
    this.finalPass = new ShaderPass(FinalShader);
    this.composer.addPass(this.finalPass);
    this.onProgress(1, "listo");
  }

  // 3 niveles.
  setQuality(q) {
    if (q === "high") q = "alto";
    if (q === "low") q = "bajo";
    const dpr = window.devicePixelRatio || 1;
    // 'dpr' aquí es el ratio EFECTIVO: resolución de pantalla × escala interna.
    const T = {
      alto: { dpr: Math.min(dpr, this.maxDpr), bloom: 0.32, rain: true, dust: true, shadow: true, env: true },
      medio: { dpr: Math.min(dpr, 1.25) * 0.82, bloom: 0.2, rain: true, dust: false, shadow: false, env: true },
      bajo: { dpr: Math.min(dpr, 1) * 0.65, bloom: 0, rain: false, dust: false, shadow: false, env: false },
    }[q];
    if (!T) return;
    this.quality = q;
    this._tierRatio = T.dpr;
    this._setShadows(T.shadow);
    this.scene.environment = T.env ? this._env : null;
    this.bloom.enabled = T.bloom > 0;
    this.bloom.strength = T.bloom;
    if (this.dust) this.dust.visible = T.dust;
    if (this.rain) this.rain.visible = T.rain;
    this._applyRatio();
  }

  // Al enfocar un monitor para leer/escribir se renderiza a resolución COMPLETA (ahí es donde importa la nitidez del texto, y la vista acercada es más barata);
  _applyRatio() {
    const dpr = window.devicePixelRatio || 1;
    const full = Math.min(dpr, this.maxDpr);
    this._ratio = this._focused ? full : (this._tierRatio || full);
    this.renderer.setPixelRatio(this._ratio);
    if (this.composer.setPixelRatio) this.composer.setPixelRatio(this._ratio);
    this.resize();
  }

  // Enciende/apaga las sombras.
  _setShadows(on) {
    if (this.renderer.shadowMap.enabled === on) return;
    this.renderer.shadowMap.enabled = on;
    this.renderer.shadowMap.needsUpdate = on;
    this.scene.traverse((o) => {
      const m = o.material;
      if (!m) return;
      (Array.isArray(m) ? m : [m]).forEach((mat) => { mat.needsUpdate = true; });
    });
  }

  // Calidad automática: mide los FPS cada segundo y sube/baja de nivel con histéresis, así cada equipo va lo más fluido que su GPU permita sin que el usuario toque nada.
  _autoTune(now) {
    if (!this.autoQuality) return;
    const a = this._auto || (this._auto = { t: now, n: 0, since: now });
    a.n++;
    if (now - a.t < 1000) return;
    const fps = (a.n * 1000) / (now - a.t);
    a.t = now; a.n = 0;
    const order = ["bajo", "medio", "alto"];
    let lvl = order.indexOf(this.quality);
    if (lvl < 0) lvl = 2;
    if (fps < 48 && lvl > 0) { this.setQuality(order[--lvl]); a.since = now; }
    else if (fps >= 57 && lvl < 2 && now - a.since > 4000) { this.setQuality(order[++lvl]); a.since = now; }
  }

  resize() {
    const w = window.innerWidth, h = window.innerHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.composer.setSize(w, h);
    // Bloom a media resolución de la escena YA escalada (ratio efectivo).
    const r = this._ratio || this.renderer.getPixelRatio();
    this.bloom.setSize(Math.max(2, Math.round(w * r * 0.5)), Math.max(2, Math.round(h * r * 0.5)));
    if (this.mode.startsWith("focus")) this.setMode(this.mode, true);
  }

  // --- cámara ---
  focusPose(name) {
    const s = this.screens[name];
    s.mesh.updateWorldMatrix(true, false);
    const center = new THREE.Vector3();
    s.mesh.getWorldPosition(center);
    const normal = new THREE.Vector3(0, 0, 1).applyQuaternion(s.group.quaternion);
    const t = Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    const dist = Math.max((s.h / 2) / t, (s.w / 2) / (t * this.camera.aspect)) * 1.22;
    return { pos: center.clone().addScaledVector(normal, dist), look: center };
  }

  setMode(mode) {
    this.mode = mode;
    const focused = mode.startsWith("focus");
    if (focused !== this._focused) { this._focused = focused; this._applyRatio(); }
    if (mode === "menu") return;
    if (mode === "seated") {
      this.camPos.set(0, 1.2, 0.85);
      this.camLook.set(0, 1.0, -0.3);
    } else if (mode.startsWith("focus-")) {
      const p = this.focusPose(mode.slice(6));
      this.camPos.copy(p.pos);
      this.camLook.copy(p.look);
    }
  }

  pick(clientX, clientY) {
    const v = new THREE.Vector2((clientX / window.innerWidth) * 2 - 1, -(clientY / window.innerHeight) * 2 + 1);
    this.raycaster.setFromCamera(v, this.camera);
    const meshes = Object.values(this.screens).map((s) => s.mesh);
    const hit = this.raycaster.intersectObjects(meshes, false)[0];
    return hit ? hit.object.name : null;
  }

  setAlarm(level) { this.alarm = Math.max(this.alarm, level); }
  pulseGlitch(v = 1) { this.glitch = Math.max(this.glitch, v); }
  setAccent(color) {
    this.kbGlow.material.color.set(color).multiplyScalar(1.5);
  }

  frame(changed = true) {
    this.timer.update();
    const dt = Math.min(this.timer.getDelta(), 0.05);
    const t = this.timer.getElapsed();
    this._fc = (this._fc || 0) + 1;

    // La escena es estática: tras unos cuadros congelamos los mapas de sombra (antes se recalculaban 2048² + 1024² en CADA fotograma sin cambiar nada).
    if (this._fc === 4 && this.renderer.shadowMap.enabled) {
      this.renderer.shadowMap.autoUpdate = false;
      this.renderer.shadowMap.needsUpdate = true;
    }
    const slow = this._fc % 2 === 0;  // polvo y vapor: mitad de frecuencia

    // cámara
    if (this.mode === "menu") {
      const a = t * 0.06;
      this.camPos.set(Math.sin(a) * 1.9 + 0.2, 1.55 + Math.sin(t * 0.3) * 0.08, 1.5 + Math.cos(a) * 1.1);
      this.camLook.set(0, 1.05, -0.3);
    }
    const k = 1 - Math.pow(0.0025, dt);
    this.camera.position.lerp(this.camPos, k);
    this.curLook.lerp(this.camLook, k);
    const look = this.curLook.clone();
    if (this.mode === "seated") {
      look.x += this.mouse.x * 0.55;
      look.y += this.mouse.y * 0.3;
    } else if (this.mode.startsWith("focus")) {
      look.x += this.mouse.x * 0.01;
      look.y += this.mouse.y * 0.006;
    }
    this.camera.position.y += Math.sin(t * 0.9) * 0.0006;
    this.camera.lookAt(look);

    // lluvia (en shader, barato), polvo y vapor (CPU, a media frecuencia)
    this.rain.material.uniforms.uTime.value = t;
    if (slow) {
      const dt2 = dt * 2;
      const dp = this.dust.geometry.attributes.position;
      for (let i = 0; i < dp.count; i++) {
        let y = dp.getY(i) + Math.sin(t * 0.3 + i) * 0.0006 - 0.0003;
        if (y < 0.5) y = 2.5;
        dp.setY(i, y);
        dp.setX(i, dp.getX(i) + Math.cos(t * 0.2 + i * 1.3) * 0.0004);
      }
      dp.needsUpdate = true;
      const sp = this.steam.geometry.attributes.position;
      for (let i = 0; i < sp.count; i++) {
        const p = (this.steamSeeds[i] + t * 0.12) % 1;
        sp.setXYZ(i, -0.42 + Math.sin(p * 9 + i) * 0.015 * p, 0.84 + p * 0.22, 0.12 + Math.cos(p * 7 + i) * 0.012 * p);
      }
      sp.needsUpdate = true;
    }

    // teclas
    const now = performance.now();
    if (this.keyInst) {
      let kdirty = false;
      for (let i = 0; i < this.keyUntil.length; i++) {
        if (this.keyUntil[i] && now > this.keyUntil[i]) {
          this._setKeyY(i, this.keyY);
          this.keyUntil[i] = 0;
          kdirty = true;
        }
      }
      if (kdirty) this.keyInst.instanceMatrix.needsUpdate = true;
    }

    // LEDs del rack
    if (!this._ledT || t - this._ledT > 0.09) {
      this._ledT = t;
      const c = new THREE.Color();
      for (let i = 0; i < this.leds.count; i++) {
        const r = Math.random();
        if (i % 6 === 0) c.set("#39ff7a").multiplyScalar(2);
        else if (r < 0.45) c.set(this.alarm > 0.1 && i % 3 === 0 ? "#ff2e4d" : (i % 6 < 3 ? "#39ff7a" : "#3fe0ff")).multiplyScalar(2.5);
        else c.set("#061008");
        this.leds.setColorAt(i, c);
      }
      this.leds.instanceColor.needsUpdate = true;
    }

    // neón con parpadeo ocasional
    const flick = Math.random() < 0.006 ? 0.15 : 1;
    this.neon.material.color.setRGB(4 * flick, 0.5 * flick, 1.1 * flick);
    this.neonLight.intensity = 1.3 * flick;

    // alarma
    this.alarm = Math.max(0, this.alarm - dt * 0.12);
    const pulse = (Math.sin(t * 9) * 0.5 + 0.5) * this.alarm;
    this.alarmLight.intensity = pulse * 14;
    this.alarmSpot.intensity = this.alarm * 40;
    this.alarmSpot.target.position.set(Math.sin(t * 4) * 3, 0.5, Math.cos(t * 4) * 3);
    this.beacon.material.emissiveIntensity = 0.15 + pulse * 6;

    this.glitch = Math.max(0, this.glitch - dt * 1.5);
    this.finalPass.uniforms.uTime.value = t;
    this.finalPass.uniforms.uGlitch.value = this.glitch;
    this.finalPass.uniforms.uAlarm.value = pulse;

    // Tope de ~60 fps: no renderiza más rápido que una pantalla normal, lo que ahorra GPU en monitores de 120 Hz sin afectar la fluidez percibida.
    const tnow = performance.now();
    if (tnow - (this._lastRender || 0) < 15) return;
    this._lastRender = tnow;
    // contador de FPS (para el HUD de depuración)
    this._fcount = (this._fcount || 0) + 1;
    if (tnow - (this._ft || tnow) >= 1000) {
      this.fps = Math.round((this._fcount * 1000) / (tnow - this._ft));
      this._fcount = 0; this._ft = tnow;
    } else if (!this._ft) { this._ft = tnow; }
    this._autoTune(tnow);

    this.composer.render(dt);
  }
}
