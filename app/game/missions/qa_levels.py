"""Niveles 1, 2, 3 y 5 de QA / Security Tester."""
import json
from ..engine import c
from .base import GuidedMission, http_response, parse_curl

JSON_H = {"Content-Type": "application/json"}

def _j(ctx, status, obj, inc):
    http_response(ctx, status, JSON_H, json.dumps(obj, ensure_ascii=False), inc)

class QACasoMission(GuidedMission):
    id = "qa-caso"
    role = "qa"
    role_name = "QA / Security Tester"
    title = "Tu primer caso de prueba"
    codename = "CAMINO FELIZ"
    level = 1
    teaches = ["caso de prueba", "camino feliz", "camino triste", "codigos HTTP"]
    par_time = 540
    summary = ("Ser QA es comparar lo que DEBERIA pasar con lo que PASA. Vas a probar el login de una app con datos correctos "
               "y con datos incorrectos, y a leer el codigo HTTP que responde cada vez.")
    start = {"host": "qa-ws", "user": "qa", "cwd": "/home/qa"}
    briefing = [
        "App de prueba: http://app.test/api . Tu usuario valido esta en ~/datos.txt.",
        "curl manda peticiones. -i muestra el codigo (200 ok, 401 sin autorizar...).",
        "Empieza con:  aprende casos   y luego   cat datos.txt",
    ]
    outro = "Probaste el camino feliz (login correcto = 200) y el triste (login malo = 401). Comparar esperado vs obtenido es el corazon del QA."
    help_extra = [("curl -i -d <json> <url>", "peticion con datos"), ("responder <texto>", "responde")]
    hosts = {
        "qa-ws": {"ip": "10.50.0.9", "users": {"qa": {"home": "/home/qa"}},
            "fs": {"/home/qa/datos.txt": "\n".join(["Usuario valido: ana@app.test  /  contrasena: Correcta123", "Endpoint: POST http://app.test/api/login  con  {\"email\":..., \"password\":...}", "Prueba 1 (feliz): credenciales correctas -> esperas 200.", "Prueba 2 (triste): contrasena mal -> esperas 401.", "responder <codigo> que devuelve el login correcto y el incorrecto."])}},
        "api": {"ip": "10.50.0.10", "dns": "app.test", "ports": [{"port": 80, "service": "http"}]},
    }

    objectives = [
        {"id": "read", "title": "Leer los datos de prueba", "points": 40, "read": "/home/qa/datos.txt", "desc": "cat datos.txt",
         "lesson": "Un caso de prueba define entrada y resultado esperado.", "hints": ["cat datos.txt"]},
        {"id": "happy", "title": "Probar el login correcto (camino feliz)", "points": 110, "requires": "read",
         "desc": "curl -i -d '{\"email\":\"ana@app.test\",\"password\":\"Correcta123\"}' http://app.test/api/login",
         "lesson": "Credenciales validas deben responder 200 y un token.", "hints": ["Copia el comando del objetivo tal cual."]},
        {"id": "sad", "title": "Probar el login incorrecto (camino triste)", "points": 110, "requires": "read",
         "desc": "Repite el curl con una contrasena equivocada.", "lesson": "Credenciales malas deben responder 401, nunca 200.",
         "hints": ["curl -i -d '{\"email\":\"ana@app.test\",\"password\":\"malo\"}' http://app.test/api/login"]},
        {"id": "codes", "title": "Anotar los codigos observados", "points": 90, "requires": "happy",
         "question": "Que codigo devuelve un login CORRECTO?", "answer": ["200", "200 ok"],
         "desc": "responder <codigo>", "lesson": "200 = exito. Documentar el codigo hace el bug reproducible.", "hints": ["responder 200"]},
    ]
    required = ["read", "happy", "sad", "codes"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Andrea - QA Lead", "title": "Bienvenida",
               "text": "Prueba el login con datos buenos y malos. Dime que codigo responde cada caso."}]

    def extra_commands(self):
        return {"curl": (self.cmd_curl, "curl -i -d <json> <url>")}

    def cmd_curl(self, ctx, args, raw):
        r = parse_curl(args)
        if not r["url"] or self.resolve_host(r["host"].split(":")[0]) != "api":
            ctx.print("Uso: curl -i -d '{...}' http://app.test/api/login"); return
        if r["path"].rstrip("/") != "/api/login":
            _j(ctx, 404, {"error": "Not Found"}, r["include"]); return
        try:
            body = json.loads(r["data"] or "{}")
        except ValueError:
            body = {}
        if body.get("email") == "ana@app.test" and body.get("password") == "Correcta123":
            _j(ctx, 200, {"token": "ok-123", "user": "ana"}, r["include"])
            ctx.complete("happy")
        else:
            _j(ctx, 401, {"error": "Credenciales invalidas"}, r["include"])
            if body:
                ctx.complete("sad")


# ----------------------------- Nivel 2 -----------------------------
class QAFormulariosMission(GuidedMission):
    id = "qa-formularios"
    role = "qa"
    role_name = "QA / Security Tester"
    title = "Valores que no deberian pasar"
    codename = "LIMITES"
    level = 2
    teaches = ["valores limite", "validacion de entrada", "montos negativos", "tipos incorrectos"]
    par_time = 600
    summary = ("Un buen tester prueba lo que el programador no penso: montos negativos, cero, texto donde va un numero. "
               "Encuentra el bug de validacion en el formulario de recarga de una billetera.")
    start = {"host": "qa-ws", "user": "qa", "cwd": "/home/qa"}
    briefing = [
        "API de billetera: http://wallet.test/api . Prueba POST /recarga con {\"monto\": N}.",
        "Tu saldo inicial es 100. Una recarga valida lo sube.",
        "Empieza con:  aprende casos",
    ]
    outro = "Encontraste que la API acepta montos negativos: recargar -50 BAJA tu saldo. Falta validar que el monto sea > 0. Bug de logica reportado."
    help_extra = [("curl -d <json> <url>", "peticion"), ("responder <texto>", "responde")]
    hosts = {
        "qa-ws": {"ip": "10.51.0.9", "users": {"qa": {"home": "/home/qa"}},
            "fs": {"/home/qa/plan.txt": "\n".join(["Endpoint: POST http://wallet.test/api/recarga  con {\"monto\": numero}", "Saldo inicial: 100.", "Prueba estos valores y observa el saldo resultante:", "  100 (normal)   0 (cero)   -50 (negativo)   \"abc\" (texto)", "responder <valor> que NO deberia aceptarse pero se acepta."])}},
        "api": {"ip": "10.51.0.10", "dns": "wallet.test", "ports": [{"port": 80, "service": "http"}]},
    }

    objectives = [
        {"id": "plan", "title": "Leer el plan de pruebas", "points": 40, "read": "/home/qa/plan.txt", "desc": "cat plan.txt",
         "lesson": "Prueba siempre valores limite: 0, negativos, maximo+1 y tipos incorrectos.", "hints": ["cat plan.txt"]},
        {"id": "valid", "title": "Hacer una recarga valida", "points": 90, "requires": "plan",
         "desc": "curl -d '{\"monto\":100}' http://wallet.test/api/recarga", "lesson": "Primero confirma el camino feliz.", "hints": ["curl -d '{\"monto\":100}' http://wallet.test/api/recarga"]},
        {"id": "negative", "title": "Probar un monto negativo", "points": 150, "requires": "valid",
         "desc": "curl -d '{\"monto\":-50}' http://wallet.test/api/recarga", "lesson": "La API acepto -50 y tu saldo BAJO: bug de validacion de negocio.",
         "hints": ["curl -d '{\"monto\":-50}' http://wallet.test/api/recarga"]},
        {"id": "q_bug", "title": "Identificar el valor problematico", "points": 120, "requires": "negative",
         "question": "Que tipo de monto NO deberia aceptarse pero se acepta?", "answer": ["negativo", "negativos", "-50", "monto negativo"],
         "desc": "responder <valor>", "lesson": "Validar: el monto debe ser un numero mayor que cero.", "hints": ["responder negativo"]},
    ]
    required = ["plan", "valid", "negative", "q_bug"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Andrea - QA Lead", "title": "Rompe la recarga",
               "text": "Prueba el formulario de recarga con valores raros. Algo no esta validado."}]

    initial_flags = {"saldo": 100}

    def extra_commands(self):
        return {"curl": (self.cmd_curl, "curl -d '{\"monto\":N}' http://wallet.test/api/recarga")}

    def cmd_curl(self, ctx, args, raw):
        import json as _j2
        r = parse_curl(args)
        if not r["url"] or self.resolve_host(r["host"].split(":")[0]) != "api":
            ctx.print("Uso: curl -d '{\"monto\":100}' http://wallet.test/api/recarga"); return
        if r["path"].rstrip("/") != "/api/recarga":
            _j(ctx, 404, {"error": "Not Found"}, r["include"]); return
        try:
            monto = _j2.loads(r["data"] or "{}").get("monto")
        except ValueError:
            monto = None
        if not isinstance(monto, (int, float)):
            _j(ctx, 400, {"error": "monto debe ser numero"}, r["include"])
            ctx.print(c("g", "Bien: rechazo el texto. (Ese caso SI esta validado.)")); return
        ctx.flags["saldo"] = round(ctx.flags["saldo"] + monto, 2)
        _j(ctx, 200, {"ok": True, "saldo": ctx.flags["saldo"]}, r["include"])
        if monto > 0:
            ctx.complete("valid")
        elif monto < 0:
            ctx.print(c("y", f"Acepto un monto negativo: tu saldo BAJO a {ctx.flags['saldo']}. Eso es un bug."))
            ctx.complete("valid"); ctx.complete("negative")


# ----------------------------- Nivel 3 -----------------------------
USERS_N3 = {
    1001: {"id": 1001, "nombre": "QA Tester", "email": "qa@shop.test", "pedidos": 2},
    1002: {"id": 1002, "nombre": "Cliente Real", "email": "cliente@shop.test", "pedidos": 9, "tarjeta": "**** 5521"},
}
TOKEN_N3 = "tok-qa-1001"

class QASesionesMission(GuidedMission):
    id = "qa-sesiones"
    role = "qa"
    role_name = "QA / Security Tester"
    title = "La cuenta de alguien mas"
    codename = "IDOR"
    level = 3
    teaches = ["autenticacion", "autorizacion", "IDOR", "datos de otro usuario"]
    par_time = 660
    summary = ("Una app pide token para ver tu perfil, pero quiza no revisa que el perfil sea TUYO. Prueba cambiar el id en la URL "
               "y descubre si puedes ver los datos de otro cliente: eso es un IDOR.")
    start = {"host": "qa-ws", "user": "qa", "cwd": "/home/qa"}
    briefing = [
        "Tienda online: http://shop.test/api . Tu token (usuario 1001) esta en ~/token.txt.",
        "GET /usuarios/<id> devuelve un perfil. Tu id es 1001.",
        "Empieza con:  aprende sesiones",
    ]
    outro = "Confirmaste un IDOR: con tu token pudiste leer el perfil del usuario 1002. Falta comprobar que el dueno del token sea el dueno del recurso."
    help_extra = [("curl -H 'Authorization: Bearer <tok>' <url>", "peticion autenticada"), ("responder <texto>", "responde")]
    hosts = {
        "qa-ws": {"ip": "10.52.0.9", "users": {"qa": {"home": "/home/qa"}},
            "fs": {"/home/qa/token.txt": "Token (usuario 1001): tok-qa-1001", "/home/qa/plan.txt": "\n".join(["1. Mira tu perfil:  curl -H 'Authorization: Bearer tok-qa-1001' http://shop.test/api/usuarios/1001", "2. Cambia el id a 1002 y repite.", "3. Si ves datos que no son tuyos, es IDOR. responder <id> ajeno al que accediste."])}},
        "api": {"ip": "10.52.0.10", "dns": "shop.test", "ports": [{"port": 80, "service": "http"}]},
    }

    objectives = [
        {"id": "plan", "title": "Leer el plan y tu token", "points": 40, "read": "/home/qa/plan.txt", "desc": "cat plan.txt",
         "lesson": "Autenticacion = quien eres. Autorizacion = que puedes ver. Son distintas.", "hints": ["cat plan.txt", "cat token.txt"]},
        {"id": "mine", "title": "Ver tu propio perfil", "points": 90, "requires": "plan", "cmd": r"usuarios/1001",
         "desc": "curl -H 'Authorization: Bearer tok-qa-1001' http://shop.test/api/usuarios/1001", "lesson": "Tu token te da tu propio perfil: correcto.",
         "hints": ["curl -H 'Authorization: Bearer tok-qa-1001' http://shop.test/api/usuarios/1001"]},
        {"id": "idor", "title": "Intentar ver el perfil de otro usuario", "points": 170, "requires": "mine", "cmd": r"usuarios/1002",
         "desc": "Cambia el id a 1002 y repite la peticion.", "lesson": "Si con TU token ves datos del 1002, la API no comprueba autorizacion: IDOR.",
         "hints": ["curl -H 'Authorization: Bearer tok-qa-1001' http://shop.test/api/usuarios/1002"]},
        {"id": "q", "title": "Confirmar el acceso indebido", "points": 110, "requires": "idor",
         "question": "A que id de usuario accediste sin ser tuyo?", "answer": ["1002"],
         "desc": "responder <id>", "lesson": "Defensa: comprobar que el dueno del token sea el dueno del recurso.", "hints": ["responder 1002"]},
    ]
    required = ["plan", "mine", "idor", "q"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Andrea - QA Lead", "title": "Prueba de acceso",
               "text": "Revisa si un usuario puede ver la cuenta de otro cambiando el id en la URL."}]

    def extra_commands(self):
        return {"curl": (self.cmd_curl, "curl -H 'Authorization: Bearer <tok>' <url>")}

    def cmd_curl(self, ctx, args, raw):
        r = parse_curl(args)
        if not r["url"] or self.resolve_host(r["host"].split(":")[0]) != "api":
            ctx.print("Uso: curl -H 'Authorization: Bearer tok-qa-1001' http://shop.test/api/usuarios/1001"); return
        auth = r["headers"].get("authorization", "").replace("Bearer", "").strip()
        path = r["path"].rstrip("/")
        if not path.startswith("/api/usuarios/"):
            _j(ctx, 404, {"error": "Not Found"}, r["include"]); return
        if auth != TOKEN_N3:
            _j(ctx, 401, {"error": "Falta token valido"}, r["include"]); return
        ident = path.rsplit("/", 1)[-1]
        if not ident.isdigit() or int(ident) not in USERS_N3:
            _j(ctx, 404, {"error": "Usuario no encontrado"}, r["include"]); return
        uid = int(ident)
        _j(ctx, 200, USERS_N3[uid], r["include"])
        if uid == 1002:
            ctx.print(c("y", "Con TU token (1001) viste los datos del usuario 1002. Eso es un IDOR."))


# ----------------------------- Nivel 5 -----------------------------
class QACarreraMission(GuidedMission):
    id = "qa-carrera"
    role = "qa"
    role_name = "QA / Security Tester"
    title = "Dos clics a la vez"
    codename = "CONDICION DE CARRERA"
    level = 5
    teaches = ["condicion de carrera", "peticiones concurrentes", "mass assignment", "reporte"]
    par_time = 900
    summary = ("El bug mas elegante: un cupon de un solo uso que, enviado muchas veces a la vez, se aplica varias. "
               "Reproduce la condicion de carrera con peticiones concurrentes y de paso prueba subir tu rol por mass assignment.")
    start = {"host": "qa-ws", "user": "qa", "cwd": "/home/qa"}
    meter = {"key": "deploy", "label": "RELEASE EN", "start": 900, "max": 900, "fail_at": None,
             "direction": "down", "countdown": True, "format": "time", "fail_text": "El release salio con el bug de carrera sin reportar."}
    briefing = [
        "API de pagos: http://pay.test/api . Release en minutos.",
        "El cupon BIENVENIDA da 1 descuento por cuenta. Pruebalo UNA vez y luego MUCHAS a la vez.",
        "Empieza con:  aprende race",
    ]
    outro = "Reprodujiste la condicion de carrera (el cupon se aplico varias veces enviandolo en paralelo) y el mass assignment (role:admin). Dos bugs criticos reportados a tiempo."
    help_extra = [("curl -d <json> <url>", "peticion"), ("paralelo -n <N> <url>", "envia N peticiones a la vez"), ("reporte enviar", "entrega")]
    initial_flags = {"cupon_usos": 0}
    hosts = {
        "qa-ws": {"ip": "10.55.0.9", "users": {"qa": {"home": "/home/qa"}},
            "fs": {"/home/qa/plan.txt": "\n".join(["1. Aplica el cupon UNA vez:  curl -d '{\"cupon\":\"BIENVENIDA\"}' http://pay.test/api/cupon", "2. Reproduce la carrera:  paralelo -n 10 http://pay.test/api/cupon", "3. Mass assignment:  curl -d '{\"nombre\":\"qa\",\"role\":\"admin\"}' http://pay.test/api/perfil", "4. reporte enviar"])}},
        "api": {"ip": "10.55.0.10", "dns": "pay.test", "ports": [{"port": 80, "service": "http"}]},
    }

    objectives = [
        {"id": "plan", "title": "Leer el plan", "points": 40, "read": "/home/qa/plan.txt", "desc": "cat plan.txt",
         "lesson": "Las condiciones de carrera aparecen cuando dos peticiones pasan la misma validacion antes de guardar.", "hints": ["cat plan.txt"]},
        {"id": "once", "title": "Aplicar el cupon una vez", "points": 90, "requires": "plan", "cmd": r"curl.*cupon",
         "desc": "curl -d '{\"cupon\":\"BIENVENIDA\"}' http://pay.test/api/cupon", "lesson": "La primera vez funciona: es de un solo uso.", "hints": ["curl -d '{\"cupon\":\"BIENVENIDA\"}' http://pay.test/api/cupon"]},
        {"id": "race", "title": "Reproducir la condicion de carrera", "points": 200, "requires": "once", "cmd": r"paralelo\s+-n",
         "desc": "paralelo -n 10 http://pay.test/api/cupon", "lesson": "Enviadas a la vez, varias pasan la validacion antes de que alguna marque el cupon como usado.",
         "hints": ["paralelo -n 10 http://pay.test/api/cupon"]},
        {"id": "mass", "title": "Probar mass assignment (subir tu rol)", "points": 150, "requires": "plan", "cmd": r"curl.*role.*admin|curl.*perfil",
         "desc": "curl -d '{\"nombre\":\"qa\",\"role\":\"admin\"}' http://pay.test/api/perfil", "lesson": "Si la API copia todo el JSON al modelo, te vuelves admin. Defensa: lista blanca de campos.",
         "hints": ["curl -d '{\"nombre\":\"qa\",\"role\":\"admin\"}' http://pay.test/api/perfil"]},
        {"id": "report", "title": "Entregar el reporte", "points": 160, "requires": "race", "cmd": r"reporte\s+enviar",
         "desc": "reporte enviar", "lesson": "Carrera + mass assignment: dos bugs de alto impacto en pagos.", "hints": ["reporte enviar"]},
    ]
    required = ["plan", "once", "race", "mass", "report"]
    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Andrea - QA Lead", "title": "Ultima revision",
         "text": "El cupon deberia ser de un solo uso. Ponlo a prueba con peticiones en paralelo."},
        {"id": "half", "at": 450, "unless": "report", "kind": "alert", "severity": "medium", "sender": "CI/CD", "title": "Mitad del tiempo",
         "text": "Va la mitad de la ventana. Reproduce el bug y reporta."},
    ]

    def extra_commands(self):
        return {"curl": (self.cmd_curl, "curl -d '{...}' <url>"), "paralelo": (self.cmd_paralelo, "paralelo -n <N> <url>")}

    def cmd_curl(self, ctx, args, raw):
        import json as _j2
        r = parse_curl(args)
        if not r["url"] or self.resolve_host(r["host"].split(":")[0]) != "api":
            ctx.print("Uso: curl -d '{...}' http://pay.test/api/..."); return
        path = r["path"].rstrip("/")
        try:
            body = _j2.loads(r["data"] or "{}")
        except ValueError:
            body = {}
        if path == "/api/cupon":
            if ctx.flags["cupon_usos"] == 0:
                ctx.flags["cupon_usos"] = 1
                _j(ctx, 200, {"ok": True, "descuento": 1, "mensaje": "cupon aplicado"}, r["include"])
            else:
                _j(ctx, 409, {"error": "cupon ya usado"}, r["include"])
        elif path == "/api/perfil":
            if body.get("role") == "admin":
                _j(ctx, 200, {"ok": True, "nombre": body.get("nombre"), "role": "admin"}, r["include"])
                ctx.print(c("y", "La API copio role:admin de tu JSON. Mass assignment confirmado."))
                ctx.complete("mass")
            else:
                _j(ctx, 200, {"ok": True, "role": "user"}, r["include"])
        else:
            _j(ctx, 404, {"error": "Not Found"}, r["include"])

    def cmd_paralelo(self, ctx, args, raw):
        n = 10
        if "-n" in args and args.index("-n") + 1 < len(args) and args[args.index("-n") + 1].isdigit():
            n = min(50, int(args[args.index("-n") + 1]))
        if not any("cupon" in a for a in args):
            ctx.print("Uso: paralelo -n 10 http://pay.test/api/cupon"); return
        exitos = 1 + max(0, n - 1) // 2 if ctx.flags["cupon_usos"] else n // 2 + 1
        ctx.flags["cupon_usos"] += exitos
        ctx.print(f"Enviando {n} peticiones simultaneas a /api/cupon ...", "",
                  c("r", f"  {exitos} x 200 OK (cupon aplicado)   {n - exitos} x 409 (ya usado)"),
                  c("y", f"El cupon de UN solo uso se aplico {exitos} veces: condicion de carrera confirmada."))
        ctx.complete("race")

    def on_command(self, ctx, args, raw):
        super().on_command(ctx, args, raw)
        if args and args[0] == "reporte" and len(args) > 1 and args[1] == "enviar":
            if ctx.done("race"):
                ctx.print(c("g", "Reporte entregado: condicion de carrera en /cupon (alta) y mass assignment en /perfil (alta). Release en revision."))
                ctx.complete("report")
            else:
                ctx.print(c("y", "Reproduce primero el bug de carrera antes de reportar."))

