"""Comandos genéricos de la terminal simulada."""
import base64
import fnmatch
import hashlib
import ipaddress
import re
import time

from .engine import c
from .topics import TOPICS

GENERIC_HELP = [
    ("help", "muestra esta ayuda"),
    ("objetivos", "lista los objetivos de la misión"),
    ("pista", "pide una pista para el objetivo actual (-10 pts)"),
    ("aprende <tema>", "mini lección: nmap, ssh, hash, sqli, xss, idor, firewall..."),
    ("ls, cd, pwd, cat", "navegar y leer archivos"),
    ("head, tail, grep, wc, sort, uniq", "filtrar texto (admiten tuberías |)"),
    ("cut, awk '{print $1}'", "sacar columnas de un texto"),
    ("file", "¿qué tipo de archivo es?"),
    ("find", "buscar archivos"),
    ("whoami, id, hostname, ip", "información del sistema"),
    ("history, clear", "historial y limpiar pantalla"),
    ("uptime, free, df", "estado del sistema"),
    ("neofetch / fastfetch", "info del equipo con logo"),
]


def dispatch(ctx, args, raw):
    name = args[0]
    special = ctx.m.commands()
    if name in special:
        special[name][0](ctx, args, raw)
        return
    fn = COMMANDS.get(name)
    if fn:
        fn(ctx, args, raw)
        return
    ctx.print(f"bash: {name}: comando no encontrado", c("d", "Escribe 'help' para ver los comandos disponibles."))


def _input_lines(ctx, args, path_index):
    if len(args) > path_index:
        path = args[path_index]
        content = ctx.read(path)
        if content is None:
            ctx.print(f"{args[0]}: {path}: No existe el archivo o directorio")
            return None
        if not ctx.can_read(path):
            ctx.print(f"{args[0]}: {path}: Permiso denegado")
            return None
        return content.split("\n")
    if ctx.stdin is not None:
        return ctx.stdin
    return []


def cmd_help(ctx, args, raw):
    ctx.print(c("w", "COMANDOS DISPONIBLES"), "")
    for name, desc in GENERIC_HELP:
        ctx.print(f"  {c('g', name.ljust(34))}{desc}")
    tools = [(n, d) for n, (_, d) in ctx.m.commands().items() if d] + list(ctx.m.help_extra)
    if tools:
        ctx.print("", c("w", f"HERRAMIENTAS DE {ctx.m.role_name.upper()}"), "")
        for name, desc in tools:
            ctx.print(f"  {c('c', name.ljust(34))}{desc}")
    ctx.print("", c("d", "Tip: usa ↑/↓ para el historial y TAB para autocompletar."))


def cmd_clear(ctx, args, raw):
    ctx.clear = True


def cmd_whoami(ctx, args, raw):
    ctx.print(ctx.user)


def cmd_id(ctx, args, raw):
    if ctx.user == "root":
        ctx.print("uid=0(root) gid=0(root) groups=0(root)")
    else:
        groups = ctx.host.get("users", {}).get(ctx.user, {}).get("groups", ctx.user)
        ctx.print(f"uid=1000({ctx.user}) gid=1000({ctx.user}) groups=1000({groups})")


def cmd_hostname(ctx, args, raw):
    ctx.print(ctx.host_id)


def cmd_pwd(ctx, args, raw):
    ctx.print(ctx.s["cwd"])


def cmd_ls(ctx, args, raw):
    opts = "".join(a[1:] for a in args[1:] if a.startswith("-"))
    paths = [a for a in args[1:] if not a.startswith("-")] or [ctx.s["cwd"]]
    for path in paths:
        p = ctx.abspath(path)
        if ctx.read(p) is not None:
            ctx.print(path)
            continue
        if not ctx.isdir(p):
            ctx.print(f"ls: no se puede acceder a '{path}': No existe el archivo o directorio")
            continue
        if not ctx.can_read(p + "/x"):
            ctx.print(f"ls: no se puede abrir el directorio '{path}': Permiso denegado")
            continue
        entries = ctx.listdir(p)
        if "a" not in opts:
            entries = [e for e in entries if not e[0].startswith(".")]
        if "l" in opts:
            ctx.print(f"total {len(entries) * 4}")
            for name, is_dir in entries:
                full = (p.rstrip("/") + "/" + name)
                owner = "root" if full.startswith(("/root", "/etc", "/var", "/usr", "/opt")) else ctx.user
                if is_dir:
                    ctx.print(f"drwxr-xr-x 2 {owner:<8} {owner:<8}  4096 nov  9 03:14 {c('b', name)}")
                else:
                    size = len(ctx.read(full) or "")
                    perm = ctx.host.get("perms", {}).get(full, "-rw-r--r--")
                    shown = c("r", name) if "s" in perm else name
                    ctx.print(f"{perm} 1 {owner:<8} {owner:<8} {size:>5} nov  9 03:14 {shown}")
        else:
            ctx.print("  ".join(c("b", n) if d else n for n, d in entries) if entries else "")


def cmd_cd(ctx, args, raw):
    target = args[1] if len(args) > 1 else "~"
    if target == "-":
        target = ctx.s.get("oldpwd", ctx.s["cwd"])
    p = ctx.abspath(target)
    if not ctx.isdir(p):
        ctx.print(f"cd: {target}: No existe el directorio")
        return
    if not ctx.can_read(p + "/x"):
        ctx.print(f"cd: {target}: Permiso denegado")
        return
    ctx.s["oldpwd"] = ctx.s["cwd"]
    ctx.s["cwd"] = p
    ctx.m.on_read(ctx, p + "/")


def cmd_cat(ctx, args, raw):
    files = [a for a in args[1:] if not a.startswith("-")]
    if not files:
        if ctx.stdin is not None:
            ctx.print(*ctx.stdin)
        return
    for path in files:
        if ctx.isdir(path) and ctx.read(path) is None:
            ctx.print(f"cat: {path}: Es un directorio")
            continue
        content = ctx.read(path)
        if content is None:
            ctx.print(f"cat: {path}: No existe el archivo o directorio")
            continue
        if not ctx.can_read(path):
            ctx.print(f"cat: {path}: Permiso denegado")
            continue
        ctx.print(content)
        ctx.m.on_read(ctx, ctx.abspath(path))


def _head_tail(ctx, args, tail):
    n = 10
    rest = []
    i = 1
    while i < len(args):
        a = args[i]
        if a == "-n" and i + 1 < len(args):
            n = int(args[i + 1]) if args[i + 1].isdigit() else 10
            i += 2
            continue
        if a.startswith("-") and a[1:].isdigit():
            n = int(a[1:])
        elif a == "-f":
            pass
        else:
            rest.append(a)
        i += 1
    lines = _input_lines(ctx, [args[0]] + rest, 1)
    if lines is None:
        return
    ctx.print(*(lines[-n:] if tail else lines[:n]))
    if rest:
        ctx.m.on_read(ctx, ctx.abspath(rest[0]))


def cmd_head(ctx, args, raw):
    _head_tail(ctx, args, False)


def cmd_tail(ctx, args, raw):
    _head_tail(ctx, args, True)


def cmd_grep(ctx, args, raw):
    flags = "".join(a[1:] for a in args[1:] if a.startswith("-") and len(a) > 1)
    rest = [a for a in args[1:] if not (a.startswith("-") and len(a) > 1)]
    if not rest:
        ctx.print("Uso: grep [-i] [-c] [-v] PATRÓN [ARCHIVO]")
        return
    pattern = rest[0]
    lines = _input_lines(ctx, ["grep"] + rest, 2)
    if lines is None:
        return
    ci = "i" in flags
    pat = pattern.lower() if ci else pattern
    matches = [ln for ln in lines if (pat in (ln.lower() if ci else ln)) != ("v" in flags)]
    if "c" in flags:
        ctx.print(str(len(matches)))
    else:
        if "v" in flags:
            ctx.print(*matches)
        else:
            for ln in matches:
                idx = (ln.lower() if ci else ln).find(pat)
                ctx.print(ln[:idx] + c("r", ln[idx:idx + len(pat)]) + ln[idx + len(pat):])
    target = ctx.abspath(rest[1]) if len(rest) > 1 else None
    ctx.m.on_grep(ctx, pattern, target, matches)


def cmd_wc(ctx, args, raw):
    lines = _input_lines(ctx, [a for a in args if not a.startswith("-")], 1)
    if lines is None:
        return
    while lines and lines[-1] == "":
        lines = lines[:-1]
    ctx.print(str(len(lines)))


def cmd_sort(ctx, args, raw):
    lines = _input_lines(ctx, [a for a in args if not a.startswith("-")], 1) or []
    out = sorted(lines, reverse="-r" in args)
    if "-n" in args or "-nr" in args or "-rn" in args:
        def key(x):
            head = x.strip().split(" ")[0]
            return int(head) if head.isdigit() else 0
        out = sorted(lines, key=key, reverse="r" in "".join(args[1:]))
    ctx.print(*out)


def cmd_uniq(ctx, args, raw):
    lines = _input_lines(ctx, [a for a in args if not a.startswith("-")], 1) or []
    out, prev, count = [], None, 0
    for ln in lines + [None]:
        if ln == prev:
            count += 1
            continue
        if prev is not None:
            out.append(f"{count:>7} {prev}" if "-c" in args else prev)
        prev, count = ln, 1
    ctx.print(*out)


def _fields(line, sep):
    return line.split(sep) if sep not in (None, " ") else line.split()


def cmd_cut(ctx, args, raw):
    sep, spec, rest, i = "\t", None, [], 1
    while i < len(args):
        a = args[i]
        if a == "-d" and i + 1 < len(args):
            sep, i = args[i + 1], i + 2
            continue
        if a.startswith("-d") and len(a) > 2:
            sep = a[2:]
        elif a == "-f" and i + 1 < len(args):
            spec, i = args[i + 1], i + 2
            continue
        elif a.startswith("-f") and len(a) > 2:
            spec = a[2:]
        else:
            rest.append(a)
        i += 1
    if not spec:
        ctx.print("Uso: cut -d'<separador>' -f<campo> [ARCHIVO]", c("d", "Ej: cut -d' ' -f1 access.log   |   cut -d: -f1 /etc/passwd"))
        return
    lines = _input_lines(ctx, ["cut"] + rest, 1)
    if lines is None:
        return
    idx = [int(x) - 1 for x in spec.split(",") if x.isdigit()]
    out = []
    for ln in lines:
        parts = ln.split(sep) if sep != " " else ln.split(" ")
        out.append(sep.join(parts[k] for k in idx if k < len(parts)))
    ctx.print(*out)


def cmd_awk(ctx, args, raw):
    sep, prog, rest = None, None, []
    for a in args[1:]:
        if a.startswith("-F"):
            sep = a[2:] or None
        elif prog is None and "{" in a:
            prog = a
        else:
            rest.append(a)
    m = re.match(r"^\s*\{\s*print\s+(.*?)\s*\}\s*$", prog or "")
    if not m:
        ctx.print("Este laboratorio sólo admite:  awk '{print $N}'  (o $1, $3)", c("d", "Ej: awk '{print $1}' access.log | sort | uniq -c"))
        return
    cols = [x.strip() for x in m.group(1).split(",")]
    lines = _input_lines(ctx, ["awk"] + rest, 1)
    if lines is None:
        return
    out = []
    for ln in lines:
        parts = _fields(ln, sep)
        vals = []
        for col in cols:
            if col == "$0":
                vals.append(ln)
            elif col.startswith("$") and col[1:].isdigit():
                k = int(col[1:]) - 1
                vals.append(parts[k] if 0 <= k < len(parts) else "")
            elif col == "$NF":
                vals.append(parts[-1] if parts else "")
        out.append(" ".join(vals))
    ctx.print(*out)


def cmd_file(ctx, args, raw):
    for path in [a for a in args[1:] if not a.startswith("-")]:
        content = ctx.read(path)
        if content is None:
            ctx.print(f"{path}: cannot open (No existe el archivo)" if not ctx.isdir(path) else f"{path}: directory")
            continue
        kind = ctx.host.get("types", {}).get(ctx.abspath(path))
        if not kind:
            head = content[:20]
            if head.startswith("ELF"):
                kind = "ELF 64-bit LSB executable, x86-64"
            elif head.startswith("\x89PNG"):
                kind = "PNG image data"
            elif head.startswith("<?php"):
                kind = "PHP script, ASCII text"
            elif head.startswith("-----BEGIN"):
                kind = "PEM key / certificate"
            elif head.startswith("#!"):
                kind = "script, ASCII text executable"
            else:
                kind = "ASCII text"
        ctx.print(f"{path}: {kind}")


def cmd_echo(ctx, args, raw):
    ctx.print(" ".join(args[1:]))


def cmd_date(ctx, args, raw):
    ctx.print(time.strftime("%a %d %b %Y %H:%M:%S UTC", time.gmtime()))


def cmd_uname(ctx, args, raw):
    os_name = ctx.host.get("os", "Linux 6.1.0-amd64")
    ctx.print(f"Linux {ctx.host_id} {os_name} x86_64 GNU/Linux" if "-a" in args else "Linux")


def cmd_ip(ctx, args, raw):
    ip = ctx.host.get("ip", "127.0.0.1")
    ctx.print(
        "1: lo: <LOOPBACK,UP> mtu 65536",
        "    inet 127.0.0.1/8 scope host lo",
        "2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500",
        f"    inet {c('g', ip)}/24 brd {ip.rsplit('.', 1)[0]}.255 scope global eth0",
    )


def cmd_history(ctx, args, raw):
    for i, h in enumerate(ctx.s["history"], 1):
        ctx.print(f"{i:>5}  {h}")


def cmd_objetivos(ctx, args, raw):
    ctx.print(c("w", f"OBJETIVOS — {ctx.m.title}"), "")
    current_found = False
    for o in ctx.m.objectives:
        if ctx.done(o["id"]):
            ctx.print(f"  {c('g', '[✔]')} {o['title']}")
        elif not current_found:
            current_found = True
            ctx.print(f"  {c('y', '[▸]')} {c('w', o['title'])}", f"      {c('d', o['desc'])}")
            if o.get("question"):
                ctx.print(f"      {c('c', '? ' + o['question'])}", f"      {c('d', 'contesta con: responder <tu respuesta>')}")
        else:
            ctx.print(f"  {c('d', '[ ] ' + o['title'])}")
    ctx.print("", f"  Puntos: {c('y', str(ctx.s['score']))}")


def current_objective(ctx):
    for o in ctx.m.objectives:
        if not ctx.done(o["id"]):
            return o
    return None


def cmd_pista(ctx, args, raw):
    o = current_objective(ctx)
    if not o:
        ctx.print("No quedan objetivos pendientes.")
        return
    used = ctx.s["hints"].get(o["id"], 0)
    hints = o.get("hints", [])
    if used >= len(hints):
        ctx.print(c("y", "Ya viste todas las pistas de este objetivo:"))
        for h in hints:
            ctx.print("  • " + h)
        return
    ctx.s["hints"][o["id"]] = used + 1
    ctx.s["score"] = max(0, ctx.s["score"] - 10)
    ctx.print(c("y", f"PISTA {used + 1}/{len(hints)} (-10 pts):"), "  " + hints[used])


def cmd_aprende(ctx, args, raw):
    if len(args) < 2 or args[1].lower() not in TOPICS:
        ctx.print(c("w", "Temas disponibles:"), "  " + ", ".join(sorted(TOPICS)), c("d", "Uso: aprende <tema>"))
        return
    topic = TOPICS[args[1].lower()]
    ctx.print(c("c", f"━━ {topic['title']} ━━"), "")
    ctx.print(*topic["body"])


def cmd_find(ctx, args, raw):
    root = args[1] if len(args) > 1 and not args[1].startswith("-") else "."
    name = None
    perm = None
    if "-name" in args:
        i = args.index("-name")
        name = args[i + 1] if i + 1 < len(args) else "*"
    if "-perm" in args:
        i = args.index("-perm")
        perm = args[i + 1] if i + 1 < len(args) else None
    if "-exec" in args:
        ctx.m.on_find_exec(ctx, args, raw)
        return
    base = ctx.abspath(root)
    prefix = "/" if base == "/" else base.rstrip("/") + "/"
    perms = ctx.host.get("perms", {})
    results = []
    for f in ctx.all_files():
        if not f.startswith(prefix) and f != base:
            continue
        if perm in ("-4000", "-u=s", "/4000"):
            if "s" not in perms.get(f, ""):
                continue
        elif not ctx.can_read(f):
            continue
        if name and not fnmatch.fnmatch(f.rsplit("/", 1)[-1], name):
            continue
        results.append(f)
    if perm and ctx.user != "root":
        ctx.print(c("d", "find: '/root': Permiso denegado"))
    ctx.print(*results)
    ctx.m.on_find(ctx, args, results)


def cmd_base64(ctx, args, raw):
    data = [a for a in args[1:] if not a.startswith("-")]
    text = " ".join(data) if data else "\n".join(ctx.stdin or [])
    content = ctx.read(text) if data else None
    if content is not None:
        text = content
    try:
        if "-d" in args:
            ctx.print(base64.b64decode(text.strip()).decode("utf-8", "replace"))
        else:
            ctx.print(base64.b64encode(text.encode()).decode())
    except Exception:
        ctx.print("base64: entrada inválida")


def cmd_md5sum(ctx, args, raw):
    text = " ".join(args[1:])
    ctx.print(f"{hashlib.md5(text.encode()).hexdigest()}  -")


def cmd_ssh(ctx, args, raw):
    target = next((a for a in args[1:] if not a.startswith("-")), None)
    if not target or "@" not in target:
        ctx.print("Uso: ssh usuario@host")
        return
    user, host = target.split("@", 1)
    host_id = ctx.m.resolve_host(host)
    if not host_id or not ctx.m.reachable(ctx, host_id):
        ctx.print(f"ssh: connect to host {host} port 22: Connection timed out")
        return
    h = ctx.m.hosts[host_id]
    if 22 not in [p["port"] for p in h.get("ports", [])]:
        ctx.print(f"ssh: connect to host {host} port 22: Connection refused")
        return
    ctx.s["mode"] = "password"
    ctx.s["pending"] = {"action": "ssh", "host": host_id, "user": user, "tries": 0}
    ctx.print(f"{user}@{host}'s password: ")


def cmd_exit(ctx, args, raw):
    if not ctx.s["stack"]:
        ctx.print(c("d", "Estás en tu máquina. Usa el menú (ESC) para salir del juego."))
        return
    prev = ctx.s["stack"].pop()
    ctx.print("logout", f"Connection to {ctx.host.get('ip')} closed.")
    ctx.s["host"], ctx.s["user"], ctx.s["cwd"] = prev["host"], prev["user"], prev["cwd"]


def cmd_ping(ctx, args, raw):
    target = next((a for a in args[1:] if not a.startswith("-") and not a.isdigit()), None)
    if not target:
        ctx.print("Uso: ping <host>")
        return
    host_id = ctx.m.resolve_host(target)
    if not host_id or not ctx.m.reachable(ctx, host_id):
        ctx.print(f"PING {target}: 56 data bytes", "--- estadísticas ---", c("r", "4 paquetes transmitidos, 0 recibidos, 100% pérdida"))
        return
    ip = ctx.m.hosts[host_id]["ip"]
    ctx.print(f"PING {target} ({ip}) 56(84) bytes of data.")
    for i in range(1, 5):
        ctx.print(f"64 bytes from {ip}: icmp_seq={i} ttl=64 time={0.3 + i * 0.07:.2f} ms")
    ctx.print("--- estadísticas ---", c("g", "4 paquetes transmitidos, 4 recibidos, 0% pérdida"))


def cmd_nmap(ctx, args, raw):
    opts = [a for a in args[1:] if a.startswith("-")]
    targets = [a for a in args[1:] if not a.startswith("-") and not a.isdigit()]
    if "-p" in args:
        i = args.index("-p")
        if i + 1 < len(args) and args[i + 1] in targets:
            targets.remove(args[i + 1])
    if not targets:
        ctx.print("Uso: nmap [opciones] <objetivo>", c("d", "Ejemplos: nmap -sn 10.0.0.0/24   |   nmap -sV 10.0.0.5"))
        return
    target = targets[0]
    ctx.print(f"Starting Nmap 7.95 ( https://nmap.org ) at {time.strftime('%Y-%m-%d %H:%M')} UTC")
    hosts = []
    if "/" in target:
        try:
            net = ipaddress.ip_network(target, strict=False)
        except ValueError:
            ctx.print(f"Failed to resolve \"{target}\".")
            return
        for hid, h in ctx.m.hosts.items():
            if h.get("ip") and ipaddress.ip_address(h["ip"]) in net and ctx.m.reachable(ctx, hid):
                hosts.append(hid)
    else:
        hid = ctx.m.resolve_host(target)
        if hid and ctx.m.reachable(ctx, hid):
            hosts.append(hid)
    discovery = "-sn" in opts
    for hid in hosts:
        h = ctx.m.hosts[hid]
        ctx.print(f"Nmap scan report for {h.get('dns', hid)} ({c('g', h['ip'])})", "Host is up (0.00042s latency).")
        if discovery:
            continue
        ports = h.get("ports", [])
        full = "-p-" in opts
        shown = [p for p in ports if full or not p.get("high")]
        if not shown:
            ctx.print("All 1000 scanned ports are closed")
            continue
        version = any(o in opts for o in ("-sV", "-A", "-sC"))
        ctx.print(f"Not shown: {65535 - len(shown) if full else 1000 - len(shown)} closed tcp ports")
        ctx.print(c("w", "PORT      STATE SERVICE" + ("     VERSION" if version else "")))
        for p in shown:
            line = f"{(str(p['port']) + '/tcp').ljust(9)} {c('g', 'open ')} {p['service'].ljust(11)}"
            if version:
                line += " " + p.get("version", "")
            ctx.print(line)
            if "-A" in opts or "-sC" in opts:
                for s in p.get("scripts", []):
                    ctx.print("| " + s)
    if not hosts:
        ctx.print("Note: Host seems down. If it is really up, but blocking our ping probes, try -Pn")
    ctx.print(f"Nmap done: {'256' if '/' in target else '1'} IP address{'es' if '/' in target else ''} ({len(hosts)} host{'s' if len(hosts) != 1 else ''} up) scanned in {2.1 + len(hosts) * 1.7:.2f} seconds")
    ctx.m.on_nmap(ctx, opts, target, hosts)


def cmd_sudo(ctx, args, raw):
    if len(args) < 2:
        ctx.print("uso: sudo -l | sudo <comando>")
        return
    if ctx.user == "root":
        from .commands import dispatch as _d
        _d(ctx, args[1:], raw)
        return
    rules = ctx.host.get("users", {}).get(ctx.user, {}).get("sudo")
    if args[1] == "-l":
        if not rules:
            ctx.print(f"Lo sentimos, el usuario {ctx.user} no puede ejecutar sudo en {ctx.host_id}.")
        else:
            ctx.print(f"El usuario {ctx.user} puede ejecutar los siguientes comandos en {ctx.host_id}:")
            for r in rules:
                ctx.print("    " + c("y", r))
        ctx.m.on_sudo_l(ctx)
        return
    ctx.m.on_sudo(ctx, args, raw)


def cmd_rm(ctx, args, raw):
    files = [a for a in args[1:] if not a.startswith("-")]
    if not files:
        ctx.print("rm: falta un operando")
        return
    for f in files:
        if not ctx.can_read(f) or (ctx.user != "root" and ctx.abspath(f).startswith(("/etc", "/var", "/usr"))):
            if not ctx.m.allow_rm(ctx, ctx.abspath(f)):
                ctx.print(f"rm: no se puede borrar '{f}': Permiso denegado")
                continue
        if not ctx.remove(f):
            ctx.print(f"rm: no se puede borrar '{f}': No existe el archivo o directorio")
            continue
        ctx.m.on_rm(ctx, ctx.abspath(f))


def _uptime_str(ctx):
    sec = max(0, int(ctx.now - ctx.s["started"]))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


NEOFETCH_LOGO = [
    " ███╗   ██╗ ",
    " ████╗  ██║ ",
    " ██╔██╗ ██║ ",
    " ██║╚██╗██║ ",
    " ██║ ╚████║ ",
    " ╚═╝  ╚═══╝ ",
    "           ",
    "  nullsec  ",
]


def cmd_neofetch(ctx, args, raw):
    host = ctx.host
    hid = ctx.host_id
    distro = host.get("distro", "nullsector GNU/Linux")
    kernel = host.get("os", "6.1.0-amd64")
    if not str(kernel).startswith(("5", "6")):
        kernel = "6.1.0-amd64"
    title = f"{ctx.s['user']}@{hid}"
    info = [
        c("g", title),
        "─" * len(title),
        f"{c('c', 'OS')}: {distro} x86_64",
        f"{c('c', 'Host')}: {host.get('dns', hid)}",
        f"{c('c', 'Kernel')}: Linux {kernel}",
        f"{c('c', 'Uptime')}: {_uptime_str(ctx)}",
        f"{c('c', 'Shell')}: cysh 1.2",
        f"{c('c', 'Terminal')}: cyberal-term",
        f"{c('c', 'CPU')}: Virtual x86_64 (4)",
        f"{c('c', 'Memory')}: 512MiB / 2048MiB",
        f"{c('c', 'IP')}: {c('g', host.get('ip', '127.0.0.1'))}",
    ]
    lw = max(len(x) for x in NEOFETCH_LOGO)
    rows = max(len(NEOFETCH_LOGO), len(info))
    out = []
    for i in range(rows):
        logo = NEOFETCH_LOGO[i] if i < len(NEOFETCH_LOGO) else " " * lw
        right = info[i] if i < len(info) else ""
        out.append(f"{c('g', logo)}  {right}")
    ctx.print(*out)


def cmd_fastfetch(ctx, args, raw):
    cmd_neofetch(ctx, args, raw)


def cmd_uptime(ctx, args, raw):
    now = time.strftime("%H:%M:%S", time.gmtime())
    ctx.print(f" {now} up {_uptime_str(ctx)},  1 user,  load average: 0.08, 0.03, 0.01")


def cmd_free(ctx, args, raw):
    ctx.print(
        "               total        used        free      shared  buff/cache   available",
        "Mem:            2048         512        1120          24         416        1392",
        "Swap:           1024           0        1024",
    )


def cmd_df(ctx, args, raw):
    ctx.print(
        "Filesystem     1K-blocks     Used Available Use% Montado en",
        "/dev/vda1       41251136 12880320  26250112  33% /",
        "tmpfs            1048576        0   1048576   0% /dev/shm",
    )


COMMANDS = {
    "neofetch": cmd_neofetch,
    "fastfetch": cmd_fastfetch,
    "screenfetch": cmd_neofetch,
    "uptime": cmd_uptime,
    "free": cmd_free,
    "df": cmd_df,
    "help": cmd_help,
    "ayuda": cmd_help,
    "clear": cmd_clear,
    "whoami": cmd_whoami,
    "id": cmd_id,
    "hostname": cmd_hostname,
    "pwd": cmd_pwd,
    "ls": cmd_ls,
    "ll": lambda ctx, a, r: cmd_ls(ctx, ["ls", "-la"] + a[1:], r),
    "cd": cmd_cd,
    "cat": cmd_cat,
    "less": cmd_cat,
    "more": cmd_cat,
    "head": cmd_head,
    "tail": cmd_tail,
    "grep": cmd_grep,
    "wc": cmd_wc,
    "sort": cmd_sort,
    "uniq": cmd_uniq,
    "echo": cmd_echo,
    "cut": cmd_cut,
    "awk": cmd_awk,
    "file": cmd_file,
    "date": cmd_date,
    "uname": cmd_uname,
    "ip": cmd_ip,
    "ifconfig": cmd_ip,
    "history": cmd_history,
    "objetivos": cmd_objetivos,
    "objectives": cmd_objetivos,
    "pista": cmd_pista,
    "hint": cmd_pista,
    "aprende": cmd_aprende,
    "learn": cmd_aprende,
    "find": cmd_find,
    "base64": cmd_base64,
    "md5sum": cmd_md5sum,
    "ssh": cmd_ssh,
    "exit": cmd_exit,
    "logout": cmd_exit,
    "ping": cmd_ping,
    "nmap": cmd_nmap,
    "sudo": cmd_sudo,
    "rm": cmd_rm,
}

COMPLETIONS = sorted(set(COMMANDS) - {"ayuda", "objectives", "hint", "learn", "less", "more", "ll", "logout"})
