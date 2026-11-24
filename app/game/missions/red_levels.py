"""Niveles 1, 2, 3 y 5 de Red Team."""
from ..engine import c
from .base import GuidedMission

class RedReconMission(GuidedMission):
    id = "red-recon"
    role = "red"
    role_name = "Red Team"
    title = "La llave olvidada"
    codename = "PRIMER ACCESO"
    level = 1
    teaches = ["objetivo autorizado", "explorar un servidor", "archivos ocultos", "find por extension"]
    par_time = 540
    summary = ("Ejercicio autorizado: entras a un servidor de practicas ya comprometido y tienes que encontrar un archivo de cifrado (.key) "
               "que el administrador dejo olvidado, igual que lo haria un atacante buscando secretos.")
    start = {"host": "lab01", "user": "operador", "cwd": "/home/operador"}
    briefing = [
        "Laboratorio de practicas lab01. Tienes acceso autorizado de 'operador'.",
        "Objetivo: localizar un archivo .key escondido y reportar su ruta.",
        "Recuerda: esto SOLO es legal en sistemas propios o con permiso por escrito.",
        "Empieza con:  aprende terminal   y luego explora con  ls -a",
    ]
    outro = "Encontraste la llave olvidada. Un secreto guardado junto a los datos que protege no sirve de nada: esa es la leccion."
    help_extra = [("responder <ruta>", "reporta la ruta de la llave")]

    hosts = {
        "lab01": {"ip": "10.10.0.5", "dns": "lab01", "users": {"operador": {"home": "/home/operador"}},
            "fs": {
                "/home/operador/LEEME.txt": "Guia del operador:\n- Explora con ls (y ls -a para ver archivos ocultos que empiezan con .)\n- Entra a carpetas con cd y lee con cat.\n- Para buscar por extension en todo el disco:  find / -name '*.key'\nObjetivo: halla el archivo .key y reporta su ruta con: responder <ruta>",
                "/srv/datos/memo.txt": "Memo interno:\nMovi los respaldos viejos a una carpeta oculta dentro de /srv/datos.\nLas carpetas ocultas empiezan con un punto. Usa ls -a para verlas.",
                "/srv/datos/.respaldo_viejo/boveda.key": "-----BEGIN KEY-----\nK9F2-7731-AC50-boveda\n-----END KEY-----",
                "/srv/datos/publico/reporte.pdf": "[pdf]",
                "/etc/hostname": "lab01",
            },
        },
    }

    objectives = [
        {"id": "readme", "title": "Leer la guia del operador", "points": 40, "read": "/home/operador/LEEME.txt",
         "desc": "cat LEEME.txt", "lesson": "Antes de atacar, entiende el objetivo y las reglas.", "hints": ["cat LEEME.txt"]},
        {"id": "hidden", "title": "Descubrir la carpeta oculta", "points": 80, "requires": "readme", "find": "/srv/datos/.respaldo_viejo/boveda.key",
         "desc": "Busca el archivo .key:  find / -name '*.key'", "lesson": "Los archivos y carpetas que empiezan con . estan ocultos a un ls normal.",
         "hints": ["cat /srv/datos/memo.txt", "ls -a /srv/datos", "find / -name '*.key'"]},
        {"id": "read_key", "title": "Leer la llave encontrada", "points": 80, "requires": "hidden", "read": "/srv/datos/.respaldo_viejo/boveda.key",
         "desc": "Leela con cat y su ruta completa.", "lesson": "Nunca guardes llaves de cifrado junto a los datos que protegen.",
         "hints": ["cat /srv/datos/.respaldo_viejo/boveda.key"]},
        {"id": "report", "title": "Reportar la ruta de la llave", "points": 100, "requires": "read_key",
         "question": "Cual es la ruta completa del archivo .key?", "answer": ["/srv/datos/.respaldo_viejo/boveda.key"],
         "desc": "responder <ruta>", "lesson": "El reporte con la ruta exacta es lo que el cliente necesita para corregirlo.",
         "hints": ["responder /srv/datos/.respaldo_viejo/boveda.key"]},
    ]
    required = ["readme", "hidden", "read_key", "report"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Lider del ejercicio", "title": "Objetivo",
               "text": "Todo autorizado. Encuentra el .key olvidado y pasame su ruta. Tomate tu tiempo."}]


# ----------------------------- Nivel 2 -----------------------------
WORDLIST_N2 = "\n".join(["123456", "password", "qwerty", "admin", "otono2024", "leon", "mexico2023", "casa1234", "pulpo", "invierno"])

class RedPasswordsMission(GuidedMission):
    id = "red-passwords"
    role = "red"
    role_name = "Red Team"
    title = "Contrasenas de papel"
    codename = "DICCIONARIO"
    level = 2
    teaches = ["hashes", "diccionario", "contrasenas debiles", "reutilizacion"]
    par_time = 600
    summary = ("Conseguiste un archivo con un usuario y el hash de su contrasena. Aprende por que una contrasena debil "
               "se rompe en segundos: usa un diccionario para 'crackear' el hash y recupera la contrasena en claro.")
    start = {"host": "kali", "user": "operador", "cwd": "/home/operador"}
    briefing = [
        "Tu maquina de trabajo (kali). Tienes un hash capturado en ~/botin.",
        "Un hash es una huella de una sola via. No se 'descifra': se adivina probando palabras.",
        "Diccionario de prueba:  /usr/share/wordlists/corto.txt",
        "Empieza con:  aprende cifrado   y luego   cat botin/hash.txt",
    ]
    outro = "Crackeaste la contrasena probando un diccionario. Leccion: contrasenas largas y unicas; el hash solo no basta si la contrasena es debil."
    help_extra = [("crackear <archivo>", "prueba el diccionario contra un hash"), ("responder <texto>", "responde la pregunta")]

    hosts = {
        "kali": {"ip": "10.10.0.9", "users": {"operador": {"home": "/home/operador"}},
            "fs": {
                "/home/operador/LEEME.txt": "\n".join([
                    "Objetivo: recuperar la contrasena de jperez a partir de su hash.",
                    "1. Lee botin/hash.txt",
                    "2. Crackea con:  crackear botin/hash.txt",
                    "3. responder <contrasena>  y luego  responder <otro-servicio donde la reutiliza>",
                ]),
                "/home/operador/botin/hash.txt": "usuario: jperez\nhash (md5): d8578edf8458ce06fbc5bb76a58c5ca4\nnota: el usuario reutiliza esta misma contrasena en el correo y la VPN.",
                "/usr/share/wordlists/corto.txt": WORDLIST_N2,
            },
        },
    }

    objectives = [
        {"id": "read", "title": "Leer el hash capturado", "points": 50, "read": "/home/operador/botin/hash.txt",
         "desc": "cat botin/hash.txt", "lesson": "md5 es un hash: huella de una via. No se revierte, se adivina.", "hints": ["cat botin/hash.txt"]},
        {"id": "crack", "title": "Crackear el hash con el diccionario", "points": 150, "requires": "read",
         "desc": "crackear botin/hash.txt", "lesson": "Si la contrasena esta en una lista comun, caer es cuestion de segundos.",
         "hints": ["crackear botin/hash.txt"]},
        {"id": "q_pass", "title": "Decir la contrasena recuperada", "points": 100, "requires": "crack",
         "question": "Cual era la contrasena de jperez?", "answer": ["qwerty"],
         "desc": "responder <contrasena>", "lesson": "'qwerty' esta en todos los diccionarios: es de las peores.", "hints": ["La encontro el comando crackear.", "responder qwerty"]},
        {"id": "q_reuse", "title": "Identificar el riesgo de reutilizar", "points": 100, "requires": "read",
         "question": "Donde mas reutiliza jperez esa contrasena? (un servicio)", "answer": ["vpn", "correo", "la vpn", "el correo"],
         "desc": "responder <servicio>", "lesson": "Reutilizar contrasenas convierte una fuga en muchas. Por eso: gestor de contrasenas + MFA.",
         "hints": ["Lo dice la nota del botin.", "responder VPN"]},
    ]
    required = ["read", "crack", "q_pass", "q_reuse"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Lider del ejercicio", "title": "A trabajar",
               "text": "Tienes el hash de jperez. Recupera su contrasena y dime donde mas la reutiliza."}]

    def extra_commands(self):
        return {"crackear": (self.cmd_crackear, "crackea un hash con el diccionario:  crackear <archivo>"),
                "john": (self.cmd_crackear, None), "hashcat": (self.cmd_crackear, None)}

    def cmd_crackear(self, ctx, args, raw):
        files = [a for a in args[1:] if not a.startswith("-")]
        target = ctx.read(files[0]) if files else None
        if not target or "d8578edf8458ce06fbc5bb76a58c5ca4" not in target:
            ctx.print("Uso: crackear botin/hash.txt"); return
        ctx.print(c("d", "Probando /usr/share/wordlists/corto.txt ..."),
                  c("g", "hash d8578e... crackeado:  qwerty"),
                  c("d", "(md5 de 'qwerty'). Tiempo: 0.3s"))
        ctx.complete("crack")


# ----------------------------- Nivel 3 -----------------------------
class RedMapaMission(GuidedMission):
    id = "red-mapa"
    role = "red"
    role_name = "Red Team"
    title = "Mapa de la red"
    codename = "RECONOCIMIENTO"
    level = 3
    teaches = ["nmap", "hosts vivos", "puertos y servicios", "priorizar objetivos"]
    par_time = 720
    summary = ("Antes de atacar hay que mirar. Usa nmap para descubrir que equipos estan vivos en la red autorizada, "
               "que servicios exponen y cual es el objetivo mas prometedor.")
    start = {"host": "kali", "user": "operador", "cwd": "/home/operador"}
    briefing = [
        "Red autorizada: 10.20.0.0/24. Tu maquina: kali (10.20.0.9).",
        "nmap descubre equipos y los puertos/servicios que tienen abiertos.",
        "Empieza con:  aprende nmap",
    ]
    outro = "Mapeaste la red: hallaste los hosts vivos, enumeraste sus servicios y detectaste el FTP anonimo como el punto mas debil."
    help_extra = [("nmap", "nmap -sn <red>  |  nmap -sV <ip>"), ("responder <texto>", "responde la pregunta")]

    hosts = {
        "kali": {"ip": "10.20.0.9", "users": {"operador": {"home": "/home/operador"}},
            "fs": {"/home/operador/LEEME.txt": "\n".join([
                "1. Descubre hosts vivos:  nmap -sn 10.20.0.0/24",
                "2. Enumera servicios:     nmap -sV 10.20.0.20",
                "3. responder <numero> de hosts vivos y  responder <servicio> mas debil.",
            ])}},
        "gw": {"ip": "10.20.0.1", "dns": "gw.lab", "ports": [{"port": 53, "service": "domain", "version": "dnsmasq"}]},
        "web": {"ip": "10.20.0.10", "dns": "web.lab", "ports": [{"port": 80, "service": "http", "version": "nginx 1.24"}, {"port": 443, "service": "https", "version": "nginx 1.24"}]},
        "files": {"ip": "10.20.0.20", "dns": "files.lab", "ports": [{"port": 21, "service": "ftp", "version": "vsftpd 3.0 (ANONYMOUS habilitado)", "scripts": ["ftp-anon: Anonymous FTP login allowed"]}, {"port": 22, "service": "ssh", "version": "OpenSSH 8.9"}]},
    }

    objectives = [
        {"id": "readme", "title": "Leer el plan de reconocimiento", "points": 40, "read": "/home/operador/LEEME.txt",
         "desc": "cat LEEME.txt", "lesson": "Primero hosts, luego servicios: de lo general a lo especifico.", "hints": ["cat LEEME.txt"]},
        {"id": "sweep", "title": "Descubrir los hosts vivos", "points": 100, "requires": "readme", "cmd": r"nmap\s+-sn\s+10\.20\.0\.0/24",
         "desc": "nmap -sn 10.20.0.0/24", "lesson": "-sn hace un barrido de ping sin tocar puertos: rapido y silencioso.", "hints": ["nmap -sn 10.20.0.0/24"]},
        {"id": "count", "title": "Contar los hosts vivos", "points": 80, "requires": "sweep",
         "question": "Cuantos hosts estan vivos en la red?", "answer": ["4"],
         "desc": "responder <numero>", "lesson": "Cada host vivo es una posible puerta. Priorizar ahorra tiempo.", "hints": ["Cuenta los 'Host is up' del barrido.", "responder 4"]},
        {"id": "enum", "title": "Enumerar los servicios del servidor de archivos", "points": 120, "requires": "sweep", "cmd": r"nmap\s+-s[VC].*10\.20\.0\.20",
         "desc": "nmap -sV 10.20.0.20", "lesson": "-sV detecta versiones; ahi se ven cosas como 'ANONYMOUS habilitado'.", "hints": ["nmap -sV 10.20.0.20"]},
        {"id": "weak", "title": "Identificar el servicio mas debil", "points": 100, "requires": "enum",
         "question": "Que servicio es el punto mas debil para entrar?", "answer": ["ftp", "ftp anonimo", "vsftpd", "ftp (21)"],
         "desc": "responder <servicio>", "lesson": "FTP anonimo deja entrar sin contrasena: el primer objetivo tipico.", "hints": ["Mira cual dice ANONYMOUS habilitado.", "responder FTP"]},
    ]
    required = ["readme", "sweep", "count", "enum", "weak"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Lider del ejercicio", "title": "Reconoce",
               "text": "Mapea 10.20.0.0/24: cuantos hosts hay y cual es el servicio mas facil de atacar."}]


# ----------------------------- Nivel 5 -----------------------------
class RedLateralMission(GuidedMission):
    id = "red-lateral"
    role = "red"
    role_name = "Red Team"
    title = "Salto lateral"
    codename = "PIVOTE"
    level = 5
    teaches = ["post-explotacion", "buscar credenciales", "llaves SSH", "movimiento lateral", "sigilo"]
    par_time = 1000
    summary = ("Ya tienes un punto de apoyo en un servidor web con un usuario limitado. El objetivo real es el servidor de base de datos, "
               "al que no llegas directo. Busca credenciales en el equipo, salta al siguiente y hazlo sin disparar el IDS.")
    start = {"host": "web01", "user": "www", "cwd": "/home/www"}
    meter = {"key": "noise", "label": "DETECCION IDS", "start": 0, "max": 100, "fail_at": 100,
             "direction": "up", "fail_text": "El IDS detecto tu actividad ruidosa y cerraron tu acceso."}
    briefing = [
        "Tienes shell como 'www' en web01 (10.30.0.10). Objetivo: db01 (10.30.0.20).",
        "No hay ruta directa util: necesitas credenciales que esten EN web01.",
        "Mira config de la app (.env, config.php), historiales (.bash_history) y llaves SSH (~/.ssh).",
        "Cada accion ruidosa (nmap agresivo, fuerza bruta) sube la DETECCION. Ve con calma.",
    ]
    outro = "Pivoteaste: sacaste credenciales de web01, saltaste a db01 con una llave SSH y llegaste a la base de datos sin que el IDS te quemara."
    initial_flags = {"creds_found": False}
    help_extra = [("ssh / ssh -i", "salta a otro host (con llave: ssh -i <llave> u@host)"), ("responder <texto>", "responde")]
    hosts = {
        "web01": {"ip": "10.30.0.10", "dns": "web01", "users": {"www": {"home": "/home/www"}},
            "fs": {
                "/home/www/LEEME.txt": "\n".join(["Objetivo: db01 (10.30.0.20).", "Busca credenciales en:", "  /var/www/app/.env", "  ~/.bash_history", "  ~/.ssh/", "Salta con:  ssh -i <llave> deploy@10.30.0.20", "Responde la IP del objetivo y como entraste."]),
                "/var/www/app/.env": "APP_ENV=production\nDB_HOST=10.30.0.20\nDB_USER=appuser\n# el deploy usa la llave de abajo para conectarse a db01 por ssh\nDEPLOY_SSH_KEY=/home/www/.ssh/deploy_db",
                "/home/www/.bash_history": "ls -la\ncat /var/www/app/.env\nssh -i ~/.ssh/deploy_db deploy@10.30.0.20\nclear",
                "/home/www/.ssh/deploy_db": "-----BEGIN OPENSSH PRIVATE KEY-----\n(llave de despliegue a db01)\n-----END OPENSSH PRIVATE KEY-----",
            },
        },
        "db01": {"ip": "10.30.0.20", "dns": "db01", "os": "5.15.0", "protected": ["/root"],
            "users": {"deploy": {"home": "/home/deploy", "key": "deploy_db"}},
            "ports": [{"port": 22, "service": "ssh"}, {"port": 3306, "service": "mysql"}],
            "fs": {"/home/deploy/BANDERA.txt": "FLAG{pivote-a-db01-con-llave-ssh}", "/etc/hostname": "db01"},
        },
    }

    objectives = [
        {"id": "loot_env", "title": "Encontrar la configuracion de la app", "points": 100, "read": "/var/www/app/.env",
         "desc": "Lee /var/www/app/.env", "lesson": "Los archivos .env suelen tener host, usuario y rutas de llaves de la base de datos.", "hints": ["cat /var/www/app/.env"]},
        {"id": "find_key", "title": "Localizar la llave SSH de despliegue", "points": 120, "requires": "loot_env", "find": "/home/www/.ssh/deploy_db",
         "desc": "Busca la llave privada:  find ~ -name 'deploy_db'  (o ls -la ~/.ssh)", "lesson": "Una llave privada deja entrar sin contrasena. Vale tanto como el acceso que da.",
         "hints": ["ls -la ~/.ssh", "find /home/www -name deploy_db"]},
        {"id": "pivot", "title": "Saltar a db01 con la llave", "points": 180, "requires": "find_key",
         "desc": "ssh -i ~/.ssh/deploy_db deploy@10.30.0.20", "lesson": "Eso es movimiento lateral: usar lo robado en un equipo para entrar al siguiente.",
         "hints": ["Lo ves en ~/.bash_history", "ssh -i ~/.ssh/deploy_db deploy@10.30.0.20"]},
        {"id": "flag", "title": "Leer la bandera en db01", "points": 150, "requires": "pivot", "read": "/home/deploy/BANDERA.txt",
         "desc": "Ya en db01:  cat ~/BANDERA.txt", "lesson": "Objetivo cumplido sin disparar el IDS: sigilo > velocidad.", "hints": ["cat /home/deploy/BANDERA.txt"]},
    ]
    required = ["loot_env", "find_key", "pivot", "flag"]
    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Lider del ejercicio", "title": "Pivotea",
         "text": "Estas en web01. El premio esta en db01. Busca credenciales aqui y salta. Sin ruido."},
        {"id": "ids", "at": 420, "unless": "pivot", "kind": "alert", "severity": "medium", "sender": "IDS", "title": "Actividad inusual",
         "text": "El IDS nota exploracion en web01. Avanza al objetivo antes de que suba la sospecha."},
    ]

    def reachable(self, ctx, host_id):
        if host_id == "db01":
            return ctx.s["flags"].get("creds_found")
        return host_id in self.hosts

    def on_read(self, ctx, path):
        super().on_read(ctx, path)
        if path in ("/home/www/.ssh/deploy_db", "/var/www/app/.env", "/home/www/.bash_history"):
            ctx.s["flags"]["creds_found"] = True

    def on_find(self, ctx, args, results):
        super().on_find(ctx, args, results)
        if any("deploy_db" in r for r in results):
            ctx.s["flags"]["creds_found"] = True

    def on_nmap(self, ctx, opts, target, hosts):
        if any(o in opts for o in ("-A", "-T4", "-T5", "-p-")):
            ctx.adjust_meter(35)
            ctx.print(c("y", "Escaneo ruidoso: la DETECCION del IDS subio."))

    def on_login(self, ctx, host_id, user):
        if host_id == "db01":
            ctx.complete("pivot")

    def handle_mode(self, ctx, line):
        # Permite ssh con llave sin pedir contrasena si uso -i deploy_db.
        if ctx.s["mode"] == "password" and ctx.s["pending"] and ctx.s["pending"].get("host") == "db01":
            super().handle_mode(ctx, line)
        else:
            super().handle_mode(ctx, line)

    def extra_commands(self):
        return {"ssh": (self.cmd_ssh_key, "ssh -i <llave> usuario@host")}

    def cmd_ssh_key(self, ctx, args, raw):
        from ..commands import cmd_ssh
        key = None
        if "-i" in args and args.index("-i") + 1 < len(args):
            key = args[args.index("-i") + 1]
        target = next((a for a in args[1:] if "@" in a), None)
        if target and target.endswith("10.30.0.20") and key and "deploy_db" in key:
            if not ctx.s["flags"].get("creds_found"):
                ctx.s["flags"]["creds_found"] = True
            user = target.split("@")[0]
            ctx.s["stack"].append({"host": ctx.s["host"], "user": ctx.s["user"], "cwd": ctx.s["cwd"]})
            ctx.s["host"] = "db01"; ctx.s["user"] = user; ctx.s["cwd"] = "/home/" + user
            ctx.print(c("g", "Autenticado con llave publica. Bienvenido a db01."))
            self.on_login(ctx, "db01", user)
            return
        cmd_ssh(ctx, args, raw)

