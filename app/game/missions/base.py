import re
import unicodedata

from ..engine import c

LEVEL_NAMES = {0: "Tutorial", 1: "Muy fácil", 2: "Fácil", 3: "Intermedio", 4: "Difícil", 5: "Muy difícil"}


class Mission:
    id = ""
    role = ""
    role_name = ""
    title = ""
    codename = ""
    summary = ""
    level = 1
    teaches = []
    par_time = 900
    start = {}
    hosts = {}
    objectives = []
    required = []
    events = []
    meter = None
    initial_flags = {}
    briefing = []
    outro = ""
    help_extra = []

    def objective(self, obj_id):
        return next(o for o in self.objectives if o["id"] == obj_id)

    def commands(self):
        return {}

    def resolve_host(self, target):
        target = target.strip().lower().split(":")[0]
        for hid, h in self.hosts.items():
            if target in (hid.lower(), h.get("ip"), h.get("dns", "").lower()):
                return hid
        return None

    def reachable(self, ctx, host_id):
        return host_id in self.hosts

    def public(self):
        return {
            "id": self.id,
            "role": self.role,
            "title": self.title,
            "codename": self.codename,
            "summary": self.summary,
            "level": self.level,
            "difficulty": LEVEL_NAMES.get(self.level, ""),
            "teaches": list(self.teaches),
            "objectives": len(self.objectives),
            "minutes": max(5, round(self.par_time / 60)),
            "pressure": self.meter["label"] if self.meter else None,
        }

    def handle_mode(self, ctx, line):
        if ctx.s["mode"] == "password" and ctx.s["pending"]["action"] == "ssh":
            p = ctx.s["pending"]
            h = self.hosts[p["host"]]
            user = h.get("users", {}).get(p["user"])
            if user and user.get("password") and line == user["password"]:
                ctx.s["mode"] = None
                ctx.s["pending"] = None
                ctx.s["stack"].append({"host": ctx.s["host"], "user": ctx.s["user"], "cwd": ctx.s["cwd"]})
                ctx.s["host"] = p["host"]
                ctx.s["user"] = p["user"]
                ctx.s["cwd"] = ctx.home(p["user"], p["host"])
                ctx.print(*h.get("motd", [f"Bienvenido a {p['host']}"]))
                self.on_login(ctx, p["host"], p["user"])
                return
            p["tries"] += 1
            self.on_bad_password(ctx, p)
            if p["tries"] >= 3:
                ctx.s["mode"] = None
                ctx.s["pending"] = None
                ctx.print(f"{p['user']}@{h['ip']}: Permission denied (publickey,password).")
            else:
                ctx.print("Permission denied, please try again.", f"{p['user']}@{h['ip']}'s password: ")
            return
        ctx.s["mode"] = None
        ctx.s["pending"] = None

    def on_read(self, ctx, path):
        pass

    def on_grep(self, ctx, pattern, path, matches):
        pass

    def on_nmap(self, ctx, opts, target, hosts):
        pass

    def on_login(self, ctx, host_id, user):
        pass

    def on_bad_password(self, ctx, pending):
        pass

    def on_sudo_l(self, ctx):
        pass

    def on_sudo(self, ctx, args, raw):
        ctx.print(f"Lo sentimos, el usuario {ctx.user} no puede ejecutar '{' '.join(args[1:])}' como root en {ctx.host_id}.")

    def on_find(self, ctx, args, results):
        pass

    def on_find_exec(self, ctx, args, raw):
        ctx.print("find: -exec no permitido en este contexto")

    def on_rm(self, ctx, path):
        pass

    def allow_rm(self, ctx, path):
        return False

    def on_event(self, ctx, ev_id):
        pass

    def on_tick(self, ctx, elapsed):
        pass

    def on_command(self, ctx, args, raw):
        pass


def norm(text):
    """Normaliza respuestas: minúsculas, sin acentos, comillas ni espacios extra."""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return " ".join(text.lower().replace('"', " ").replace("'", " ").split())


class GuidedMission(Mission):
    """Misión declarativa para los niveles de aprendizaje."""

    par_time = 600

    def commands(self):
        cmds = {"responder": (self.cmd_responder, "contesta una pregunta del objetivo:  responder <texto>")}
        cmds.update(self.extra_commands())
        return cmds

    def extra_commands(self):
        return {}

    def _ready(self, ctx, o):
        return not ctx.done(o["id"]) and (not o.get("requires") or ctx.done(o["requires"]))

    def _hit(self, ctx, key, test):
        for o in self.objectives:
            if key in o and self._ready(ctx, o) and test(o[key]):
                ctx.complete(o["id"])

    @staticmethod
    def _as_list(v):
        return v if isinstance(v, (list, tuple)) else [v]

    def on_read(self, ctx, path):
        self._hit(ctx, "read", lambda v: path in self._as_list(v) or (path.endswith("/") and path.rstrip("/") + "/" in self._as_list(v)))

    def on_find(self, ctx, args, results):
        self._hit(ctx, "find", lambda v: any(r in results for r in self._as_list(v)))

    def on_grep(self, ctx, pattern, path, matches):
        from ..engine import strip_colors
        text = strip_colors("\n".join(matches))
        self._hit(ctx, "grep", lambda v: any(x in text for x in self._as_list(v)))

    def on_command(self, ctx, args, raw):
        self._hit(ctx, "cmd", lambda v: re.search(v, raw.strip()) is not None)

    def cmd_responder(self, ctx, args, raw):
        text = norm(" ".join(args[1:]))
        if not text:
            pending = [o for o in self.objectives if "answer" in o and not ctx.done(o["id"])]
            if pending:
                ctx.print(c("w", "Preguntas pendientes:"), *[f"  ? {o.get('question', o['title'])}" for o in pending])
            ctx.print(c("d", "Uso: responder <texto>"))
            return
        blocked = None
        for o in self.objectives:
            if "answer" not in o or ctx.done(o["id"]):
                continue
            if text in [norm(a) for a in self._as_list(o["answer"])]:
                if o.get("requires") and not ctx.done(o["requires"]):
                    blocked = o
                    continue
                ctx.print(c("g", "✔ Correcto."))
                ctx.complete(o["id"])
                return
        if blocked:
            ctx.print(c("y", f"Vas bien, pero primero completa: {self.objective(blocked['requires'])['title']}"))
            return
        ctx.s["flags"]["wrong"] = ctx.s["flags"].get("wrong", 0) + 1
        ctx.print(c("r", "✘ Esa no es la respuesta."), c("d", "Revisa la evidencia otra vez o usa 'pista' (-10 pts)."))
        self.on_wrong_answer(ctx, text)

    def on_wrong_answer(self, ctx, text):
        pass


def http_response(ctx, status, headers, body, include_headers):
    reason = {200: "OK", 201: "Created", 301: "Moved Permanently", 401: "Unauthorized", 403: "Forbidden",
              404: "Not Found", 429: "Too Many Requests", 500: "Internal Server Error"}.get(status, "")
    if include_headers:
        color = "g" if status < 400 else "r"
        ctx.print(c(color, f"HTTP/1.1 {status} {reason}"))
        for k, v in headers.items():
            ctx.print(f"{k}: {v}")
        ctx.print("")
    ctx.print(*body if isinstance(body, list) else [body])


def parse_curl(args):
    """Extrae método, URL, cabeceras y cuerpo de una línea de curl."""
    method, url, data, headers, include = None, None, None, {}, False
    i = 1
    while i < len(args):
        a = args[i]
        if a in ("-X", "--request") and i + 1 < len(args):
            method = args[i + 1].upper()
            i += 2
            continue
        if a in ("-d", "--data", "--data-raw") and i + 1 < len(args):
            data = args[i + 1]
            i += 2
            continue
        if a in ("-H", "--header") and i + 1 < len(args):
            if ":" in args[i + 1]:
                k, v = args[i + 1].split(":", 1)
                headers[k.strip().lower()] = v.strip()
            i += 2
            continue
        if a in ("-i", "-I", "--include", "-v"):
            include = True
        elif not a.startswith("-") and url is None:
            url = a
        i += 1
    if method is None:
        method = "POST" if data is not None else "GET"
    path, query = "/", {}
    host = ""
    if url:
        u = url.split("://", 1)[-1]
        host, _, rest = u.partition("/")
        rest = "/" + rest
        path, _, qs = rest.partition("?")
        for pair in qs.split("&"):
            if pair:
                k, _, v = pair.partition("=")
                query[k] = v
    return {"method": method, "url": url, "host": host, "path": path or "/", "query": query,
            "data": data, "headers": headers, "include": include}
