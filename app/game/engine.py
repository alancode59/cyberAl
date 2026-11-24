"""Motor de la terminal simulada."""
import posixpath
import shlex
import time

ESC = "\x1b"


def c(color, text):
    """Colorea texto para la terminal del cliente."""
    return f"{ESC}{color}{text}{ESC}0"


def strip_colors(text):
    out, i = [], 0
    while i < len(text):
        if text[i] == ESC and i + 1 < len(text):
            i += 2
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def tokenize(line):
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return line.split()


def split_pipes(line):
    parts, buf, quote = [], [], None
    for ch in line:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == "|":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())
    return [p for p in parts if p]


class Ctx:
    """Contexto de ejecución de un comando: misión, estado y salida."""

    def __init__(self, mission, state, now=None):
        self.m = mission
        self.s = state
        self.now = now or time.time()
        self.out = []
        self.events = []
        self.clear = False
        self.stdin = None
        self.notes = []

    def note(self, *lines):
        for line in lines:
            self.notes.extend(str(line).split("\n"))

    def print(self, *lines):
        for line in lines:
            self.out.extend(str(line).split("\n"))

    @property
    def flags(self):
        return self.s["flags"]

    @property
    def host_id(self):
        return self.s["host"]

    @property
    def host(self):
        return self.m.hosts[self.s["host"]]

    @property
    def user(self):
        return self.s["user"]

    def home(self, user=None, host_id=None):
        user = user or self.user
        host = self.m.hosts[host_id or self.host_id]
        return host.get("users", {}).get(user, {}).get("home", "/root" if user == "root" else f"/home/{user}")

    def abspath(self, path):
        if not path:
            return self.s["cwd"]
        if path == "~" or path.startswith("~/"):
            path = self.home() + path[1:]
        if not path.startswith("/"):
            path = posixpath.join(self.s["cwd"], path)
        norm = posixpath.normpath(path)
        return "/" if norm in ("", ".") else norm.replace("//", "/")

    def _fs(self, host_id):
        base = dict(self.m.hosts[host_id].get("fs", {}))
        base.update(self.s["fs_add"].get(host_id, {}))
        for p in self.s["fs_rm"].get(host_id, []):
            base.pop(p, None)
        return base

    def read(self, path, host_id=None):
        return self._fs(host_id or self.host_id).get(self.abspath(path))

    def write(self, path, content, host_id=None):
        host_id = host_id or self.host_id
        p = self.abspath(path)
        self.s["fs_add"].setdefault(host_id, {})[p] = content
        rm = self.s["fs_rm"].get(host_id, [])
        if p in rm:
            rm.remove(p)

    def remove(self, path, host_id=None):
        host_id = host_id or self.host_id
        p = self.abspath(path)
        if p not in self._fs(host_id):
            return False
        self.s["fs_add"].get(host_id, {}).pop(p, None)
        self.s["fs_rm"].setdefault(host_id, [])
        if p in self.m.hosts[host_id].get("fs", {}):
            self.s["fs_rm"][host_id].append(p)
        return True

    def isdir(self, path, host_id=None):
        p = self.abspath(path)
        if p == "/":
            return True
        prefix = p.rstrip("/") + "/"
        return any(k.startswith(prefix) for k in self._fs(host_id or self.host_id))

    def listdir(self, path, host_id=None):
        p = self.abspath(path)
        prefix = "/" if p == "/" else p.rstrip("/") + "/"
        names = {}
        for k in self._fs(host_id or self.host_id):
            if k.startswith(prefix):
                rest = k[len(prefix):]
                name = rest.split("/")[0]
                names[name] = names.get(name, False) or ("/" in rest)
        return sorted(names.items())

    def all_files(self, host_id=None):
        return sorted(self._fs(host_id or self.host_id).keys())

    def can_read(self, path):
        p = self.abspath(path)
        if self.user == "root":
            return True
        if p.startswith("/root"):
            return False
        protected = self.host.get("protected", [])
        return not any(p == x or p.startswith(x.rstrip("/") + "/") for x in protected)

    def done(self, obj_id):
        return obj_id in self.s["done"]

    def complete(self, obj_id):
        if self.done(obj_id) or self.s["status"] != "active":
            return
        obj = self.m.objective(obj_id)
        self.s["done"][obj_id] = self.now
        self.s["score"] += obj["points"]
        self.note(
            "",
            c("g", f"[+] OBJETIVO COMPLETADO: {obj['title']}  (+{obj['points']} pts)"),
        )
        if obj.get("lesson"):
            self.note(c("c", "    ▸ Lección: ") + obj["lesson"])
        self.note("")
        self.events.append({
            "id": f"obj-{obj_id}",
            "kind": "objective",
            "severity": "success",
            "sender": "SISTEMA",
            "title": "Objetivo completado",
            "text": obj["title"],
        })
        if all(self.done(o) for o in self.m.required):
            self.finish(True)

    def adjust_meter(self, delta):
        meter = self.m.meter
        if not meter:
            return
        v = max(0, min(meter["max"], self.s["meter"] + delta))
        self.s["meter"] = v
        fail_at = meter.get("fail_at")
        if fail_at is not None and self.s["status"] == "active":
            failed = v >= fail_at if meter["direction"] == "up" else v <= fail_at
            if failed:
                self.finish(False, meter.get("fail_text"))

    def finish(self, success, reason=None):
        if self.s["status"] != "active":
            return
        elapsed = int(self.now - self.s["started"])
        if success:
            bonus = max(0, self.m.par_time - elapsed) // 3
            self.s["score"] += bonus
            self.s["status"] = "completed"
            self.note(
                c("g", "══════════════════════════════════════════════"),
                c("g", f"  MISIÓN CUMPLIDA: {self.m.title}"),
                c("g", f"  Bono de tiempo: +{bonus}   Puntuación final: {self.s['score']}"),
                c("g", "══════════════════════════════════════════════"),
            )
        else:
            self.s["status"] = "failed"
            self.note(
                c("r", "══════════════════════════════════════════════"),
                c("r", "  MISIÓN FALLIDA"),
                c("r", f"  {reason or 'La operación fue comprometida.'}"),
                c("r", "══════════════════════════════════════════════"),
            )
        self.events.append({
            "id": "end",
            "kind": "end",
            "severity": "success" if success else "critical",
            "sender": "SISTEMA",
            "title": "Misión cumplida" if success else "Misión fallida",
            "text": reason or self.m.outro if success else (reason or ""),
        })

    def emit(self, ev):
        self.events.append(ev)


def new_state(mission):
    start = mission.start
    return {
        "mission": mission.id,
        "role": mission.role,
        "started": time.time(),
        "status": "active",
        "host": start["host"],
        "user": start["user"],
        "cwd": start["cwd"],
        "stack": [],
        "mode": None,
        "pending": None,
        "flags": dict(mission.initial_flags),
        "fs_add": {},
        "fs_rm": {},
        "done": {},
        "fired": {},
        "timed_out": [],
        "hints": {},
        "history": [],
        "score": 0,
        "meter": mission.meter["start"] if mission.meter else 0,
    }


def process_time(ctx):
    """Dispara eventos programados y aplica penalizaciones por vencimiento."""
    s, m = ctx.s, ctx.m
    if s["status"] != "active":
        return
    elapsed = ctx.now - s["started"]
    if m.meter and m.meter.get("countdown"):
        s["meter"] = max(0, int(m.meter["start"] - elapsed))
        if s["meter"] <= 0:
            ctx.finish(False, m.meter.get("fail_text"))
            return
    m.on_tick(ctx, elapsed)
    if s["status"] != "active":
        return
    for ev in m.events:
        if ev["id"] in s["fired"]:
            continue
        due = False
        if "at" in ev:
            due = elapsed >= ev["at"]
        elif "after" in ev and ev["after"] in s["done"]:
            due = ctx.now >= s["done"][ev["after"]] + ev.get("delay", 0)
        if ev.get("unless") and ev["unless"] in s["done"]:
            s["fired"][ev["id"]] = ctx.now
            continue
        if not due:
            continue
        s["fired"][ev["id"]] = ctx.now
        m.on_event(ctx, ev["id"])
        ctx.emit(event_payload(ev))
    for ev in m.events:
        if "deadline" not in ev or ev["id"] not in s["fired"] or ev["id"] in s["timed_out"]:
            continue
        if ev.get("resolve") in s["done"]:
            continue
        if ctx.now > s["fired"][ev["id"]] + ev["deadline"]:
            s["timed_out"].append(ev["id"])
            t = ev.get("on_timeout", {})
            ctx.s["score"] = max(0, ctx.s["score"] - t.get("score", 0))
            ctx.emit({
                "id": f"{ev['id']}-timeout",
                "kind": "alert",
                "severity": "critical",
                "sender": ev.get("sender", "SIEM"),
                "title": t.get("title", "Tiempo agotado"),
                "text": t.get("text", ""),
            })
            if t.get("meter"):
                ctx.adjust_meter(t["meter"])


def event_payload(ev):
    return {
        "id": ev["id"],
        "kind": ev.get("kind", "msg"),
        "severity": ev.get("severity", "info"),
        "sender": ev.get("sender", "SISTEMA"),
        "title": ev.get("title", ""),
        "text": ev.get("text", ""),
        "deadline": ev.get("deadline"),
    }


def active_timers(ctx):
    timers = []
    for ev in ctx.m.events:
        if "deadline" not in ev or ev["id"] not in ctx.s["fired"]:
            continue
        if ev["id"] in ctx.s["timed_out"] or ev.get("resolve") in ctx.s["done"]:
            continue
        remaining = int(ctx.s["fired"][ev["id"]] + ev["deadline"] - ctx.now)
        timers.append({"id": ev["id"], "title": ev.get("timer", ev.get("title")), "remaining": max(0, remaining)})
    return timers


def run_line(mission, state, line, now=None):
    from .commands import dispatch

    ctx = Ctx(mission, state, now)
    process_time(ctx)
    if state["status"] != "active":
        ctx.print(c("d", "La misión terminó. Usa el menú para iniciar otra."))
        return ctx
    line = line.rstrip("\n")
    if state["mode"]:
        mission.handle_mode(ctx, line)
    elif line.strip():
        state["history"] = (state["history"] + [line])[-60:]
        stages = split_pipes(line)
        for i, stage in enumerate(stages):
            args = tokenize(stage)
            if not args:
                continue
            if i > 0:
                ctx.stdin = [strip_colors(x) for x in ctx.out]
                ctx.out = []
            dispatch(ctx, args, stage)
            if state["status"] == "active":
                mission.on_command(ctx, args, stage)
    process_time(ctx)
    ctx.out.extend(ctx.notes)
    ctx.notes = []
    return ctx


def prompt(state, mission=None):
    p = {"user": state["user"], "host": state["host"], "cwd": state["cwd"], "mode": state["mode"]}
    if mission is None:
        return p
    host = mission.hosts.get(state["host"], {})
    p["os"] = host.get("osname", "windows" if "win" in str(host.get("os", "")).lower() else "linux")
    # Rama git: si el directorio actual está dentro de un repo (una carpeta que contiene .git en el sistema de archivos del host), mostrarla en el prompt.
    fs = dict(host.get("fs", {}))
    fs.update(state.get("fs_add", {}))
    cwd = state["cwd"].rstrip("/") or "/"
    roots = set()
    for path in fs:
        idx = path.find("/.git/")
        if idx == -1 and path.endswith("/.git"):
            idx = len(path) - 5
        if idx > 0:
            roots.add(path[:idx] or "/")
    for root in sorted(roots, key=len, reverse=True):
        if cwd == root or cwd.startswith(root + "/"):
            p["git"] = host.get("branch", "main")
            break
    return p
