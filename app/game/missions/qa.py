import json

from ..engine import c
from .base import Mission, http_response, parse_curl

API = "10.30.0.15"
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOjEwMDF9.qa-test-1001"
USERS = {
    1001: {"id": 1001, "nombre": "QA Tester", "email": "qa.tester@pagaya.mx", "saldo": 5000.0, "clabe": "0021********1001"},
    1002: {"id": 1002, "nombre": "Lucía Méndez", "email": "lucia.mendez@gmail.com", "saldo": 48210.5, "clabe": "0123********5521"},
    1003: {"id": 1003, "nombre": "Jorge Salas", "email": "jsalas@outlook.com", "saldo": 912.0, "clabe": "0144********8830"},
}
BUG_SEVERITY = {
    "idor": ("alta", "critica"),
    "validacion": ("alta", "critica"),
    "ratelimit": ("media", "alta"),
    "errores": ("media", "alta"),
}
BUG_OBJ = {"idor": "idor", "validacion": "validation", "ratelimit": "ratelimit", "errores": "errors"}
JSON_H = {"Content-Type": "application/json", "X-API-Version": "2.4.0-rc1"}


class QAMission(Mission):
    id = "qa-pagaya"
    role = "qa"
    role_name = "QA / Security Tester"
    title = "Release 2.4 de PagaYa"
    codename = "LUZ VERDE"
    summary = "PagaYa (fintech) sale a producción en 20 minutos con la versión 2.4 de su API. Como QA de seguridad, encuentra los bugs críticos y bloquea el release si es necesario."
    level = 4
    teaches = ["IDOR", "rate limiting", "validación de montos", "fuga de errores"]
    par_time = 1200
    start = {"host": "qa-ws", "user": "qa", "cwd": "/home/qa"}
    meter = {
        "key": "deploy", "label": "DEPLOY A PRODUCCIÓN EN", "start": 1200, "max": 1200, "fail_at": None,
        "direction": "down", "countdown": True, "format": "time",
        "fail_text": "El release salió a producción con vulnerabilidades críticas.",
    }
    briefing = [
        "PagaYa — billetera digital. Release 2.4.0-rc1 en el ambiente de staging.",
        f"API: http://{API}/api/v1  — tu token de pruebas está en ~/credenciales.txt",
        "Lee el plan de pruebas en ~/plan_pruebas.txt.",
        "Reporta cada bug con evidencia antes de que el contador de DEPLOY llegue a cero.",
    ]
    outro = "Release 2.4 bloqueado a tiempo. Los 4 bugs de seguridad pasaron al sprint de corrección."
    help_extra = []

    hosts = {
        "qa-ws": {
            "ip": "10.30.0.40",
            "users": {"qa": {"home": "/home/qa"}},
            "fs": {
                "/home/qa/plan_pruebas.txt": "\n".join([
                    "PLAN DE PRUEBAS DE SEGURIDAD — PagaYa API 2.4",
                    "Basado en OWASP API Security Top 10:",
                    "  [ ] API1  Autorización a nivel de objeto (¿puedo ver datos de otro usuario?)",
                    "  [ ] API4  Consumo de recursos / rate limiting en /login",
                    "  [ ] API6  Lógica de negocio en /transfers (montos inválidos)",
                    "  [ ] API8  Mala configuración: ¿los errores filtran información?",
                    "",
                    "Documentación: ~/docs/api.md",
                    "Reporta con:  bug nuevo <idor|ratelimit|validacion|errores> <baja|media|alta|critica>",
                    "Al final:     bug enviar",
                ]),
                "/home/qa/credenciales.txt": f"Usuario de pruebas: qa.tester@pagaya.mx (id 1001)\nToken: {TOKEN}\n\nUso: curl -H \"Authorization: Bearer <token>\" ...",
                "/home/qa/docs/api.md": "\n".join([
                    "# PagaYa API v1",
                    "GET  /api/v1/health                 estado del servicio",
                    "POST /api/v1/login                  {\"email\":..., \"password\":...}",
                    "GET  /api/v1/users/me               perfil del usuario autenticado",
                    "GET  /api/v1/users/{id}             perfil por id  (requiere token)",
                    "POST /api/v1/transfers              {\"to\": id, \"amount\": número}  (requiere token)",
                ]),
            },
        },
        "api": {
            "ip": API,
            "dns": "api.pagaya.local",
            "ports": [{"port": 80, "service": "http", "version": "gunicorn 21.2 (Flask)"}],
        },
    }

    objectives = [
        {"id": "plan", "title": "Leer el plan de pruebas", "points": 50,
         "desc": "cat ~/plan_pruebas.txt",
         "lesson": "Un buen plan de pruebas de seguridad se basa en un estándar: OWASP API Top 10.",
         "hints": ["cat ~/plan_pruebas.txt"]},
        {"id": "baseline", "title": "Hacer una petición autenticada válida", "points": 75,
         "desc": "Consulta tu propio perfil con tu token (línea base).",
         "lesson": "Primero confirma el comportamiento correcto; así sabrás reconocer el incorrecto.",
         "hints": ["cat ~/credenciales.txt", f"curl -H \"Authorization: Bearer {TOKEN}\" http://{API}/api/v1/users/me"]},
        {"id": "idor", "title": "API1: acceder a datos de otro usuario (IDOR)", "points": 150,
         "desc": "Tu id es 1001. ¿Qué pasa si pides otro id con tu token?",
         "lesson": "La API debe verificar que el recurso pertenece a quien hace la petición, no sólo que hay token.",
         "hints": ["aprende idor", f"curl -H \"Authorization: Bearer {TOKEN}\" http://{API}/api/v1/users/1002"]},
        {"id": "validation", "title": "API6: transferencia con monto inválido", "points": 150,
         "desc": "Prueba montos negativos o cero en /transfers.",
         "lesson": "Un monto negativo invierte la transferencia: le quitas dinero al otro. Valida siempre en servidor.",
         "hints": ["aprende validacion",
                   f"curl -X POST -H \"Authorization: Bearer {TOKEN}\" -d '{{\"to\":1002,\"amount\":-500}}' http://{API}/api/v1/transfers"]},
        {"id": "ratelimit", "title": "API4: verificar rate limiting en /login", "points": 125,
         "desc": "Envía muchas peticiones de login seguidas. ¿Te frena la API?",
         "lesson": "Sin respuesta 429, la API permite fuerza bruta y credential stuffing.",
         "hints": ["aprende ratelimit", f"loadtest -n 200 -m POST http://{API}/api/v1/login"]},
        {"id": "errors", "title": "API8: provocar un error que filtre información", "points": 125,
         "desc": "Manda un tipo de dato inesperado a un endpoint.",
         "lesson": "Un stack trace en producción regala rutas, librerías y a veces secretos.",
         "hints": ["aprende errores", f"curl -H \"Authorization: Bearer {TOKEN}\" http://{API}/api/v1/users/abc"]},
        {"id": "report", "title": "Reportar los bugs y bloquear el release", "points": 200,
         "desc": "bug nuevo <tipo> <severidad> por cada hallazgo y luego: bug enviar",
         "lesson": "QA de seguridad tiene poder de veto: un bug crítico detiene el release.",
         "hints": ["bug nuevo idor critica / bug nuevo validacion critica / bug nuevo ratelimit media / bug nuevo errores media",
                   "bug enviar"]},
    ]
    required = ["plan", "baseline", "idor", "validation", "ratelimit", "errors", "report"]

    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Andrea — Release Manager", "title": "Release 2.4",
         "text": "Hola. El deploy a producción es automático cuando el contador llegue a cero. Si encuentras algo crítico, repórtalo y lo detengo."},
        {"id": "dev", "at": 120, "kind": "msg", "sender": "Beto — Backend Dev", "title": "Slack #release",
         "text": "Ya probé todo en local, funciona perfecto 👍. No creo que encuentres nada jaja."},
        {"id": "ten", "at": 600, "unless": "report", "kind": "alert", "severity": "medium", "sender": "CI/CD",
         "title": "10 minutos para el deploy", "text": "El pipeline de producción se ejecutará en 10 minutos."},
        {"id": "three", "at": 1020, "unless": "report", "kind": "alert", "severity": "critical", "sender": "CI/CD",
         "title": "¡3 minutos para el deploy!", "text": "Pipeline 'prod-release' en cola. Reporta ya o saldrá con bugs."},
        {"id": "idor-reaction", "after": "idor", "delay": 2, "kind": "msg", "sender": "Andrea — Release Manager",
         "title": "😳", "text": "¿Puedes ver el saldo y correo de otros clientes? Eso es una fuga de datos personales. Documéntalo."},
    ]

    def commands(self):
        return {
            "curl": (self.cmd_curl, "peticiones HTTP:  curl [-i] [-X MÉTODO] [-H cabecera] [-d json] <url>"),
            "loadtest": (self.cmd_loadtest, "ráfaga de peticiones:  loadtest -n <N> [-m POST] <url>"),
            "jq": (self.cmd_jq, "formatea JSON de la tubería:  curl ... | jq"),
            "bug": (self.cmd_bug, "bug nuevo <tipo> <severidad> | bug lista | bug enviar"),
        }

    def on_read(self, ctx, path):
        if path == "/home/qa/plan_pruebas.txt":
            ctx.complete("plan")

    def cmd_jq(self, ctx, args, raw):
        text = "\n".join(ctx.stdin or [])
        start = text.find("{")
        try:
            obj = json.loads(text[start:]) if start >= 0 else None
        except ValueError:
            obj = None
        if obj is None:
            ctx.print("jq: error: entrada no es JSON")
            return
        ctx.print(*json.dumps(obj, indent=2, ensure_ascii=False).split("\n"))

    def _json(self, ctx, status, obj, include):
        http_response(ctx, status, JSON_H, json.dumps(obj, ensure_ascii=False), include)

    def cmd_curl(self, ctx, args, raw):
        r = parse_curl(args)
        if not r["url"]:
            ctx.print(f"curl: intenta 'curl http://{API}/api/v1/health'")
            return
        hid = self.resolve_host(r["host"].split(":")[0])
        if hid != "api":
            ctx.print(f"curl: (6) Could not resolve host: {r['host']}")
            return
        path = r["path"].rstrip("/")
        auth = r["headers"].get("authorization", "")
        authed = auth.replace("Bearer", "").strip() == TOKEN
        inc = r["include"]
        if path == "/api/v1/health":
            self._json(ctx, 200, {"status": "ok", "version": "2.4.0-rc1"}, inc)
            return
        if path == "/api/v1/login":
            if r["method"] != "POST":
                self._json(ctx, 405, {"error": "Method Not Allowed"}, inc)
            else:
                self._json(ctx, 401, {"error": "Credenciales inválidas"}, inc)
            return
        if path.startswith("/api/v1/users"):
            if not auth:
                self._json(ctx, 401, {"error": "Falta el token"}, inc)
                return
            if not authed:
                self._json(ctx, 401, {"error": "Token inválido"}, inc)
                return
            ident = path.rsplit("/", 1)[-1]
            if ident in ("me", "1001"):
                self._json(ctx, 200, USERS[1001], inc)
                ctx.complete("baseline")
                return
            if ident.isdigit():
                uid = int(ident)
                if uid in USERS:
                    self._json(ctx, 200, USERS[uid], inc)
                    ctx.print(c("y", f"↑ Con TU token obtuviste los datos del usuario {uid}. Eso no debería pasar."))
                    ctx.complete("baseline")
                    ctx.complete("idor")
                else:
                    self._json(ctx, 404, {"error": "Usuario no encontrado"}, inc)
                return
            http_response(ctx, 500, {"Content-Type": "text/html"}, [
                "<title>ValueError // Werkzeug Debugger</title>",
                "Traceback (most recent call last):",
                '  File "/srv/pagaya/api/users.py", line 42, in get_user',
                "    user = db.execute(\"SELECT * FROM users WHERE id=%s\" % int(user_id))",
                c("r", f"ValueError: invalid literal for int() with base 10: '{ident}'"),
                "",
                "Environment:",
                "  FLASK_ENV=development",
                c("r", "  DATABASE_URL=postgresql://pagaya_app:Pg_Pr0d_2026!@db-prod.pagaya.internal:5432/pagaya"),
            ], True)
            ctx.print(c("y", "↑ El servidor corre en modo DEBUG y filtra la cadena de conexión a la base de datos."))
            ctx.complete("errors")
            return
        if path == "/api/v1/transfers":
            if r["method"] != "POST":
                self._json(ctx, 405, {"error": "Method Not Allowed"}, inc)
                return
            if not authed:
                self._json(ctx, 401, {"error": "Falta el token"}, inc)
                return
            try:
                body = json.loads(r["data"] or "{}")
                amount = float(body.get("amount", 0))
                to = int(body.get("to", 0))
            except (ValueError, TypeError, AttributeError):
                self._json(ctx, 400, {"error": "JSON inválido. Ejemplo: {\"to\":1002,\"amount\":100}"}, inc)
                return
            if to not in USERS or to == 1001:
                self._json(ctx, 400, {"error": "Destinatario inválido"}, inc)
                return
            if amount > USERS[1001]["saldo"]:
                self._json(ctx, 400, {"error": "Saldo insuficiente"}, inc)
                return
            new_balance = USERS[1001]["saldo"] - amount
            self._json(ctx, 201, {"status": "completada", "to": to, "amount": amount, "saldo_nuevo": new_balance}, inc)
            if amount <= 0:
                ctx.print(c("y", f"↑ La API aceptó un monto de {amount}. Tu saldo SUBIÓ a {new_balance}: le quitaste dinero a {to}."))
                ctx.complete("validation")
            return
        self._json(ctx, 404, {"error": "Not Found"}, inc)

    def cmd_loadtest(self, ctx, args, raw):
        n = 100
        if "-n" in args and args.index("-n") + 1 < len(args) and args[args.index("-n") + 1].isdigit():
            n = min(10000, int(args[args.index("-n") + 1]))
        method = args[args.index("-m") + 1].upper() if "-m" in args and args.index("-m") + 1 < len(args) else "GET"
        url = next((a for a in args[1:] if a.startswith("http")), None)
        if not url:
            ctx.print("Uso: loadtest -n <N> [-m POST] <url>")
            return
        r = parse_curl(["curl", url])
        if self.resolve_host(r["host"].split(":")[0]) != "api":
            ctx.print("loadtest: host fuera del ambiente de pruebas.")
            return
        ctx.print(f"Enviando {n} peticiones {method} a {url} ...", "")
        if r["path"].rstrip("/") == "/api/v1/login" and method == "POST":
            ctx.print(f"  {n} x 401 Unauthorized", c("r", "  0 x 429 Too Many Requests"), "",
                      f"  Latencia p95: 41 ms   Duración: {n * 0.012:.1f} s")
            if n >= 20:
                ctx.print(c("y", "↑ La API nunca respondió 429. Un atacante puede probar contraseñas sin límite."))
                ctx.complete("ratelimit")
            else:
                ctx.print(c("d", "Muy pocas peticiones para concluir. Prueba con más (-n 100)."))
        else:
            ctx.print(f"  {n} x 200 OK", f"  Latencia p95: 18 ms",
                      c("d", "Tip: el plan de pruebas pide revisar el rate limit del login (POST)."))

    def cmd_bug(self, ctx, args, raw):
        bugs = ctx.flags.setdefault("bugs", {})
        sub = args[1] if len(args) > 1 else "lista"
        if sub == "nuevo":
            if len(args) < 4:
                ctx.print("Uso: bug nuevo <idor|ratelimit|validacion|errores> <baja|media|alta|critica>")
                return
            kind, sev = args[2].lower(), args[3].lower().replace("í", "i")
            if kind not in BUG_SEVERITY:
                ctx.print("Tipos: idor, ratelimit, validacion, errores")
                return
            if sev not in ("baja", "media", "alta", "critica"):
                ctx.print("Severidades: baja, media, alta, critica")
                return
            if not ctx.done(BUG_OBJ[kind]):
                ctx.print(c("r", "Sin evidencia no hay bug. Reprodúcelo primero."))
                return
            bugs[kind] = sev
            ctx.print(c("g", f"PAY-{2400 + len(bugs)} creado: [{kind}] severidad {sev}"))
        elif sub == "lista":
            if not bugs:
                ctx.print("Sin bugs reportados.")
            for k, v in bugs.items():
                ctx.print(f"  • {k:<12} {v}")
        elif sub == "enviar":
            missing = [k for k in BUG_SEVERITY if k not in bugs]
            if missing:
                ctx.print(c("r", "Aún no cubres el plan completo. Faltan: " + ", ".join(missing)))
                return
            wrong = [k for k, v in bugs.items() if v not in BUG_SEVERITY[k]]
            if wrong:
                ctx.print(c("y", "El líder técnico no está de acuerdo con estas severidades:"),
                          *[f"  • {k}: '{bugs[k]}' — esperado: {' o '.join(BUG_SEVERITY[k])}" for k in wrong],
                          c("d", "Corrige con 'bug nuevo' y reenvía. (-20 pts)"))
                ctx.s["score"] = max(0, ctx.s["score"] - 20)
                return
            ctx.print(c("g", "Release 2.4 BLOQUEADO. Bugs enviados al equipo de backend."))
            ctx.complete("report")
        else:
            ctx.print("Uso: bug nuevo <tipo> <severidad> | bug lista | bug enviar")
