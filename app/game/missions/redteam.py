from ..engine import c
from .base import Mission

HASH = "89d307951fff5d9f3c8d8a5d44da3ea9"
FLAG = "FLAG{nu11_s3ct0r_0wn5_h3l1x}"
WORDLIST = "\n".join([
    "123456", "password", "12345678", "qwerty", "admin", "iloveyou", "princesa", "monkey",
    "dragon", "letmein", "football", "superman", "helix2020", "invierno2018", "primavera2019",
    "verano2019", "otono2019", "trustno1", "batman", "shadow", "master", "abc123", "mexico",
    "tlaxcala1", "contraseña", "cambiame", "bienvenido", "sol123", "access", "hunter2",
])


class RedTeamMission(Mission):
    id = "red-espejo"
    role = "red"
    role_name = "Red Team"
    title = "Operación Espejo Roto"
    codename = "ESPEJO ROTO"
    summary = "Helix Dynamics contrató a tu colectivo para un ejercicio de Red Team. Entra a su servidor de archivos y llega a root sin que su IDS te queme."
    level = 4
    teaches = ["FTP anónimo", "cracking", "SSH", "escalada con sudo"]
    par_time = 1200
    start = {"host": "nullbox", "user": "ghost", "cwd": "/home/ghost"}
    help_extra = [
        ("nmap", "escáner de red:  nmap -sn | -sV | -sC | -A | -p- | -T0..5"),
        ("ssh", "shell remota:  ssh usuario@ip"),
        ("sudo", "sudo -l  /  sudo <comando>"),
    ]
    meter = {
        "key": "noise", "label": "DETECCIÓN IDS", "start": 0, "max": 100, "fail_at": 100,
        "direction": "up", "fail_text": "El IDS de Helix te detectó y cerró el ejercicio. Te quemaron.",
    }
    briefing = [
        "Contrato firmado con Helix Dynamics. Ejercicio de Red Team autorizado.",
        "Tu máquina: nullbox (10.13.37.66). Red objetivo: 10.13.37.0/24.",
        "Lee las reglas en ~/mision/reglas.txt antes de tocar NADA.",
        "Mantén el medidor de DETECCIÓN bajo: los escaneos agresivos hacen ruido.",
    ]
    outro = "Reporte entregado a Helix: FTP anónimo, contraseña débil reutilizada y sudo inseguro."

    hosts = {
        "nullbox": {
            "ip": "10.13.37.66",
            "dns": "nullbox",
            "os": "6.6.9-kali-amd64",
            "users": {"ghost": {"home": "/home/ghost"}},
            "fs": {
                "/home/ghost/mision/reglas.txt": "\n".join([
                    "══ REGLAS DE ENFRENTAMIENTO — HELIX DYNAMICS ══",
                    "Autorizado por: Dir. de Seguridad, Helix Dynamics (contrato HX-0451)",
                    "",
                    "ALCANCE PERMITIDO:  10.13.37.0/24",
                    "FUERA DE ALCANCE:   10.13.37.30 (web01 — PRODUCCIÓN, NO ESCANEAR PUERTOS)",
                    "",
                    "PROHIBIDO: denegación de servicio, borrar datos, ingeniería social.",
                    "OBJETIVO:  obtener /root/flag.txt en el servidor de archivos.",
                    "Entrega la bandera con:  entregar FLAG{...}",
                ]),
                "/home/ghost/mision/notas.txt": "\n".join([
                    "— N —",
                    "Empieza descubriendo qué hosts están vivos. Luego mira qué servicios exponen.",
                    "Los escaneos lentos (-T2) hacen menos ruido. -A es un megáfono.",
                ]),
                "/usr/share/wordlists/rockyou.txt": WORDLIST,
                "/home/ghost/.bash_history": "ls\ncat mision/reglas.txt",
            },
        },
        "gw-helix": {
            "ip": "10.13.37.1",
            "dns": "gw.helix.lab",
            "ports": [
                {"port": 53, "service": "domain", "version": "dnsmasq 2.89"},
                {"port": 443, "service": "https", "version": "nginx (Helix VPN portal)"},
            ],
        },
        "fs01": {
            "ip": "10.13.37.20",
            "dns": "fs01.helix.lab",
            "os": "5.4.0-169-generic",
            "protected": ["/root"],
            "motd": [
                "Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.4.0-169-generic x86_64)",
                c("d", "Last login: Tue Oct 28 02:11:44 2026 from 10.13.37.12"),
            ],
            "ports": [
                {"port": 21, "service": "ftp", "version": "vsftpd 3.0.3",
                 "scripts": ["ftp-anon: Anonymous FTP login allowed (FTP code 230)",
                             "  -rw-r--r--  1 0  0  250 Oct 02 respaldo_notas.txt",
                             "  -rw-r--r--  1 0  0   39 Oct 02 hash_backup.txt"]},
                {"port": 22, "service": "ssh", "version": "OpenSSH 8.2p1 Ubuntu 4ubuntu0.11"},
                {"port": 445, "service": "microsoft-ds", "version": "Samba smbd 4.x"},
            ],
            "users": {
                "dperez": {
                    "home": "/home/dperez", "password": "verano2019", "groups": "dperez,ti",
                    "sudo": ["(root) NOPASSWD: /usr/bin/find"],
                },
            },
            "perms": {"/usr/bin/passwd": "-rwsr-xr-x", "/usr/bin/su": "-rwsr-xr-x", "/usr/bin/mount": "-rwsr-xr-x"},
            "fs": {
                "/home/dperez/user.txt": "Buen trabajo. Ahora sé root.",
                "/home/dperez/pendientes.txt": "- pedir a infra que quite sudo de find (lo puse para respaldos)\n- cambiar pass vieja!!!",
                "/root/flag.txt": FLAG,
                "/root/.bash_history": "tar czf /srv/respaldo.tgz /srv/compartido",
                "/srv/compartido/organigrama.pdf": "%PDF-1.4 ...",
                "/srv/ftp/respaldo_notas.txt": "",
                "/etc/hostname": "fs01",
                "/usr/bin/find": "ELF", "/usr/bin/passwd": "ELF", "/usr/bin/su": "ELF", "/usr/bin/mount": "ELF",
            },
        },
        "web01": {
            "ip": "10.13.37.30",
            "dns": "web01.helix.lab",
            "ports": [
                {"port": 80, "service": "http", "version": "Apache httpd 2.4.41"},
                {"port": 443, "service": "https", "version": "Apache httpd 2.4.41"},
            ],
        },
    }

    ftp_files = {
        "respaldo_notas.txt": "\n".join([
            "Notas TI — Daniel Pérez (dperez)",
            "- Migrar este FTP a SFTP (pendiente desde 2021...)",
            "- Mi usuario en fs01 es dperez",
            "- Guardé el hash de mi contraseña vieja en hash_backup.txt por si la olvido",
            "  (es la misma de siempre, la de la temporada en que entré)",
        ]),
        "hash_backup.txt": f"dperez:{HASH}",
    }

    objectives = [
        {"id": "roe", "title": "Leer las reglas de enfrentamiento", "points": 50,
         "desc": "Un hacker ético conoce su alcance antes de empezar. Lee ~/mision/reglas.txt",
         "lesson": "Sin autorización escrita y alcance definido, un pentest es un delito.",
         "hints": ["Usa: cat ~/mision/reglas.txt"]},
        {"id": "discover", "title": "Descubrir hosts vivos en 10.13.37.0/24", "points": 100,
         "desc": "Haz un barrido de descubrimiento sin escanear puertos.",
         "lesson": "-sn hace un 'ping sweep': rápido y poco ruidoso. Siempre mapea antes de atacar.",
         "hints": ["nmap tiene una opción para sólo descubrir hosts sin puertos.", "nmap -sn 10.13.37.0/24"]},
        {"id": "enum", "title": "Enumerar servicios del servidor de archivos (fs01)", "points": 100,
         "desc": "Identifica puertos y versiones en 10.13.37.20.",
         "lesson": "Conocer la versión exacta de cada servicio permite buscar configuraciones débiles y CVEs.",
         "hints": ["Detecta versiones con -sV. Añade -sC para scripts por defecto.", "nmap -sV -sC 10.13.37.20"]},
        {"id": "ftp", "title": "Entrar al FTP anónimo y descargar el hash", "points": 150,
         "desc": "nmap reveló FTP anónimo. Conéctate y descarga lo interesante.",
         "lesson": "FTP anónimo + respaldos = fuga de información. Hallazgo típico en auditorías reales.",
         "hints": ["Conéctate con: ftp 10.13.37.20", "Dentro del FTP usa 'ls' y 'get hash_backup.txt'"]},
        {"id": "crack", "title": "Crackear el hash de dperez", "points": 150,
         "desc": "Es un hash MD5. Usa un diccionario de contraseñas comunes.",
         "lesson": "MD5 sin sal se rompe en segundos con diccionarios. Usa bcrypt/argon2 y contraseñas largas.",
         "hints": ["John the Ripper con el diccionario rockyou.", "john --wordlist=/usr/share/wordlists/rockyou.txt hash_backup.txt"]},
        {"id": "foothold", "title": "Acceso inicial por SSH como dperez", "points": 150,
         "desc": "Reutiliza la contraseña crackeada en el servicio SSH de fs01.",
         "lesson": "La reutilización de contraseñas convierte una fuga pequeña en acceso total.",
         "hints": ["ssh dperez@10.13.37.20  y escribe la contraseña crackeada."]},
        {"id": "privesc", "title": "Escalar privilegios a root", "points": 200,
         "desc": "Revisa qué puede ejecutar dperez como root.",
         "lesson": "Un binario permitido en sudo con '-exec' equivale a dar root (GTFOBins).",
         "hints": ["sudo -l muestra los permisos de sudo.", "sudo find . -exec /bin/sh \\; -quit"]},
        {"id": "flag", "title": "Capturar y entregar la bandera", "points": 100,
         "desc": "Lee /root/flag.txt y entrégala con: entregar FLAG{...}",
         "lesson": "En un reporte real, la 'bandera' es la evidencia del impacto.",
         "hints": ["cat /root/flag.txt", "entregar <la bandera completa>"]},
    ]
    required = ["roe", "discover", "enum", "ftp", "crack", "foothold", "privesc", "flag"]

    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "N // nullsector", "title": "Mensaje cifrado",
         "text": "Ghost. Helix firmó. Nos pagan por romperlos antes que alguien de verdad lo haga. Lee las reglas. No me hagas quedar mal."},
        {"id": "after-discover", "after": "discover", "delay": 3, "kind": "msg", "sender": "N // nullsector",
         "title": "Mensaje cifrado", "text": "fs01 es su servidor de archivos. Los admins flojos dejan puertas abiertas ahí. Empieza por ahí."},
        {"id": "after-ftp", "after": "ftp", "delay": 2, "kind": "msg", "sender": "N // nullsector",
         "title": "Mensaje cifrado", "text": "FTP anónimo en 2026. Hay gente que todavía guarda su vida en texto plano."},
        {"id": "soc-shift", "at": 300, "unless": "foothold", "kind": "alert", "severity": "medium",
         "sender": "INTEL", "title": "Cambio de turno en el SOC de Helix",
         "text": "El turno nocturno del SOC de Helix entra pronto. Tu ventana de sigilo se reduce."},
        {"id": "blue-hunting", "after": "foothold", "delay": 4, "kind": "alert", "severity": "high",
         "sender": "INTEL", "title": "El blue team de Helix revisa auth.log",
         "text": "Detectaron un login inusual de dperez. Escala privilegios antes de que te expulsen.",
         "deadline": 180, "resolve": "privesc", "timer": "Blue team cazándote",
         "on_timeout": {"title": "Te expulsaron de fs01", "meter": 45, "score": 100,
                        "text": "El blue team reseteó la contraseña de dperez. Ruido +45."}},
        {"id": "after-root", "after": "privesc", "delay": 2, "kind": "msg", "sender": "N // nullsector",
         "title": "Mensaje cifrado", "text": "root. Así se siente controlar el sistema. Toma la bandera y sal limpio."},
    ]

    def commands(self):
        return {
            "ftp": (self.cmd_ftp, "cliente FTP:  ftp <ip>"),
            "john": (self.cmd_john, "John the Ripper:  john --wordlist=<lista> <archivo>"),
            "hashcat": (self.cmd_hashcat, "hashcat -m 0 <hashes> <lista>"),
            "entregar": (self.cmd_entregar, "entrega la bandera:  entregar FLAG{...}"),
        }

    def noise(self, ctx, amount, reason):
        before = ctx.s["meter"]
        ctx.adjust_meter(amount)
        after = ctx.s["meter"]
        if amount > 0:
            ctx.print(c("y", f"[!] Ruido +{amount} ({reason}). Detección: {after}%"))
        for threshold, sev, text in ((50, "high", "Regla ET SCAN disparada desde 10.13.37.66"),
                                     (80, "critical", "El SOC de Helix está investigando tu IP")):
            if before < threshold <= after:
                ctx.emit({"id": f"ids-{threshold}", "kind": "alert", "severity": sev,
                          "sender": "IDS HELIX (interceptado)", "title": "¡Te están viendo!", "text": text})

    def on_read(self, ctx, path):
        if path == "/home/ghost/mision/reglas.txt" and ctx.host_id == "nullbox":
            ctx.complete("roe")
        if path == "/root/flag.txt" and ctx.host_id == "fs01" and ctx.user == "root":
            ctx.flags["saw_flag"] = True

    def on_nmap(self, ctx, opts, target, hosts):
        stealth = any(o in opts for o in ("-T0", "-T1", "-T2"))
        amount = 3
        if "-sn" not in opts:
            amount = 8
            if "-sV" in opts or "-sC" in opts:
                amount += 6
            if "-A" in opts:
                amount += 22
            if "-p-" in opts:
                amount += 12
        if "-T4" in opts or "-T5" in opts:
            amount += 10
        if stealth:
            amount = max(1, amount // 2)
        if "-sn" not in opts and "web01" in hosts:
            ctx.print(c("r", "[✖] VIOLACIÓN DE ALCANCE: escaneaste puertos de 10.13.37.30 (producción)."),
                      c("r", "    Las reglas lo prohíben. En la vida real esto rompe el contrato. -75 pts"))
            ctx.s["score"] = max(0, ctx.s["score"] - 75)
            amount += 20
        self.noise(ctx, amount, "escaneo sigiloso" if stealth else "escaneo nmap")
        if "/" in target and "-sn" in opts and "fs01" in hosts:
            ctx.complete("discover")
        if "fs01" in hosts and "-sn" not in opts and any(o in opts for o in ("-sV", "-A", "-sC")):
            ctx.complete("enum")

    def on_bad_password(self, ctx, pending):
        self.noise(ctx, 6, "login SSH fallido")

    def on_login(self, ctx, host_id, user):
        if host_id == "fs01" and user == "dperez":
            ctx.complete("foothold")

    def cmd_ftp(self, ctx, args, raw):
        target = args[1] if len(args) > 1 else None
        hid = self.resolve_host(target) if target else None
        if not hid:
            ctx.print("Uso: ftp <ip>")
            return
        if hid != "fs01":
            ctx.print(f"ftp: connect: Connection refused")
            return
        ip = self.hosts[hid]["ip"]
        ctx.print(f"Connected to {ip}.", "220 (vsFTPd 3.0.3)", f"Name ({ip}:{ctx.user}): anonymous",
                  "331 Please specify the password.", "Password:", c("g", "230 Login successful."),
                  "Remote system type is UNIX.", c("d", "Comandos FTP: ls, get <archivo>, pwd, help, bye"))
        ctx.s["mode"] = "ftp"
        ctx.s["pending"] = {"action": "ftp", "host": hid}
        self.noise(ctx, 2, "login FTP")

    def handle_mode(self, ctx, line):
        if ctx.s["mode"] != "ftp":
            return super().handle_mode(ctx, line)
        parts = line.split()
        if not parts:
            return
        cmd = parts[0].lower()
        if cmd in ("ls", "dir"):
            ctx.print("229 Entering Extended Passive Mode (|||40312|)", "150 Here comes the directory listing.")
            for name, content in self.ftp_files.items():
                ctx.print(f"-rw-r--r--    1 0        0        {len(content):>5} Oct 02 09:14 {name}")
            ctx.print("226 Directory send OK.")
        elif cmd == "get" and len(parts) > 1:
            name = parts[1]
            if name not in self.ftp_files:
                ctx.print("550 Failed to open file.")
                return
            ctx.write(ctx.abspath(name), self.ftp_files[name])
            ctx.print(f"local: {name} remote: {name}", "150 Opening BINARY mode data connection.",
                      c("g", "226 Transfer complete."), f"{len(self.ftp_files[name])} bytes received.")
            if name == "hash_backup.txt":
                ctx.complete("ftp")
        elif cmd == "pwd":
            ctx.print('257 "/" is the current directory')
        elif cmd in ("bye", "quit", "exit"):
            ctx.s["mode"] = None
            ctx.s["pending"] = None
            ctx.print("221 Goodbye.")
        elif cmd in ("help", "?"):
            ctx.print("Comandos: ls  get <archivo>  pwd  bye")
        elif cmd in ("put", "delete", "rm"):
            ctx.print("550 Permission denied.")
        else:
            ctx.print("?Invalid command.")

    def _crack(self, ctx, files, tool):
        target = next((f for f in files if ctx.read(f) is not None and "rockyou" not in f), None)
        if not target:
            ctx.print(f"{tool}: no se encontró el archivo de hashes.")
            return
        content = ctx.read(target)
        if HASH not in content:
            ctx.print("No password hashes loaded (see FAQ)")
            return
        if tool == "john":
            ctx.print("Using default input encoding: UTF-8",
                      "Loaded 1 password hash (Raw-MD5 [MD5 256/256 AVX2 8x3])",
                      "Press 'q' or Ctrl-C to abort, almost any other key for status",
                      c("g", "verano2019") + "       (dperez)",
                      "1g 0:00:00:00 DONE (2026-11-09 03:14) 33.33g/s 1000p/s",
                      "Session completed.")
        else:
            ctx.print("hashcat (v6.2.6) starting", "", f"{HASH}:{c('g', 'verano2019')}", "",
                      "Session..........: hashcat", "Status...........: Cracked",
                      "Hash.Mode........: 0 (MD5)")
        ctx.complete("crack")

    def cmd_john(self, ctx, args, raw):
        if "--show" in args:
            files = [a for a in args[1:] if not a.startswith("-")]
            if ctx.done("crack") and files:
                ctx.print("dperez:verano2019", "", "1 password hash cracked, 0 left")
            else:
                ctx.print("0 password hashes cracked, 1 left")
            return
        files = [a for a in args[1:] if not a.startswith("-")]
        if not files:
            ctx.print("Uso: john --wordlist=<diccionario> <archivo_hashes>")
            return
        self._crack(ctx, files, "john")

    def cmd_hashcat(self, ctx, args, raw):
        files = [a for a in args[1:] if not a.startswith("-") and not a.isdigit()]
        if not files:
            ctx.print("Uso: hashcat -m 0 <hashes> <diccionario>")
            return
        if "-m" not in args:
            ctx.print(c("y", "Aviso: sin -m hashcat intentará autodetectar. MD5 es -m 0."))
        self._crack(ctx, files, "hashcat")

    def on_sudo_l(self, ctx):
        if ctx.host_id == "fs01":
            ctx.flags["sudo_l"] = True

    def on_sudo(self, ctx, args, raw):
        cmd = args[1].rsplit("/", 1)[-1]
        if ctx.host_id == "fs01" and ctx.user == "dperez" and cmd == "find":
            if "-exec" in args and any(s in raw for s in ("/bin/sh", "/bin/bash", " sh", " bash")):
                ctx.s["stack"].append({"host": ctx.s["host"], "user": ctx.s["user"], "cwd": ctx.s["cwd"]})
                ctx.s["user"] = "root"
                ctx.print(c("r", "# ") + "whoami", "root")
                ctx.complete("privesc")
                return
            from ..commands import cmd_find
            ctx.s["user"] = "root"
            try:
                cmd_find(ctx, ["find"] + [a for a in args[2:] if a != "-exec"], raw)
            finally:
                ctx.s["user"] = "dperez"
            return
        super().on_sudo(ctx, args, raw)

    def on_find_exec(self, ctx, args, raw):
        ctx.print("$ whoami", ctx.user, c("d", "Obtuviste una shell... pero como tu mismo usuario. Necesitas privilegios."))

    def cmd_entregar(self, ctx, args, raw):
        if len(args) < 2:
            ctx.print("Uso: entregar FLAG{...}")
            return
        if args[1].strip() == FLAG:
            ctx.print(c("g", "Bandera verificada por Helix Dynamics. Evidencia aceptada."))
            ctx.complete("flag")
        else:
            ctx.print(c("r", "Bandera incorrecta."))
