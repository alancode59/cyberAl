"""Rol Privacidad / OPSEC — niveles 1 a 5."""
import random

from ..engine import c
from .base import GuidedMission

REAL_PUB_IP = "189.203.44.12"   # IP pública real (tu ISP)
VPN_IP = "45.83.91.10"          # IP de salida del VPN
TOR_IP = "185.220.101.47"       # IP del nodo de salida de Tor
PRIV_IP = "192.168.1.37"        # IP privada (LAN)
ORIG_MAC = "a4:5e:60:c2:19:7f"  # MAC de fábrica
HOST = "tu-equipo"


def _rand_mac():
    # Primer octeto par = unicast, localmente administrada (bit 0x02).
    o = [random.randint(0, 255) for _ in range(6)]
    o[0] = (o[0] & 0xFE) | 0x02
    return ":".join("%02x" % x for x in o)


class OpsecMission(GuidedMission):
    """Base del rol: comandos simulados de privacidad compartidos por los niveles."""
    role = "opsec"
    role_name = "Privacidad / OPSEC"
    start = {"host": "equipo", "user": "tu", "cwd": "/home/tu"}
    initial_flags = {"mac": ORIG_MAC, "tunnel": None, "meta_clean": False, "hist_clean": False}

    def _has(self, oid):
        return any(o["id"] == oid for o in self.objectives)

    def _try(self, ctx, oid):
        if self._has(oid) and not ctx.done(oid):
            ctx.complete(oid)

    # ---- comandos ----
    def cmd_miip(self, ctx, args, raw):
        t = ctx.flags.get("tunnel")
        pub = {"tor": TOR_IP, "vpn": VPN_IP}.get(t, REAL_PUB_IP)
        ctx.print(c("w", "Tu IP pública (como te ve Internet):"), c("g", "  " + pub))
        if t:
            ctx.print(c("d", f"  via {t.upper()} — NO es tu IP real; el sitio ve esta."))
            if self._has("oculta") and not ctx.done("oculta") and ctx.done("conectar"):
                ctx.print(c("g", "✔ Tu IP real quedó oculta."))
                self._try(ctx, "oculta")
        else:
            ctx.print(c("d", "  esta es tu IP REAL: tu ISP y cada sitio que visitas la ven."))
        self._try(ctx, "antes")

    def cmd_ip(self, ctx, args, raw):
        mac = ctx.flags.get("mac", ORIG_MAC)
        sub = args[1] if len(args) > 1 else "a"
        if sub in ("a", "addr", "address"):
            ctx.print(
                "1: lo: <LOOPBACK,UP>  inet 127.0.0.1/8",
                "2: eth0: <BROADCAST,MULTICAST,UP>",
                c("w", f"    inet {PRIV_IP}/24") + c("d", "   (IP privada, solo en tu red local)"),
                c("w", f"    link/ether {mac}") + c("d", "   (tu MAC)"),
            )
        elif sub == "link":
            ctx.print(c("w", f"2: eth0: link/ether {mac}"))
        else:
            ctx.print("Uso: ip a   |   ip link")

    def cmd_ifconfig(self, ctx, args, raw):
        mac = ctx.flags.get("mac", ORIG_MAC)
        if "down" in args:
            ctx.flags["iface_up"] = False
            ctx.print(c("d", "eth0 desactivada."))
        elif "up" in args:
            ctx.flags["iface_up"] = True
            ctx.print(c("d", "eth0 activada."))
        else:
            ctx.print(f"eth0: inet {PRIV_IP}  netmask 255.255.255.0", f"      ether {mac}  (MAC)")

    def cmd_hostname(self, ctx, args, raw):
        ctx.print(HOST)

    def cmd_macchanger(self, ctx, args, raw):
        mac = ctx.flags.get("mac", ORIG_MAC)
        if "-s" in args or "--show" in args:
            ctx.print(f"MAC permanente (de fábrica): {ORIG_MAC}", c("w", f"MAC actual:                  {mac}"))
            if mac != ORIG_MAC:
                ctx.print(c("g", "La MAC actual ya NO es la de fábrica."))
                self._try(ctx, "verificar")
            self._try(ctx, "ver")
        elif "-r" in args or "-a" in args:
            new = _rand_mac()
            ctx.flags["mac"] = new
            ctx.print(c("g", f"Nueva MAC asignada: {new}"), c("d", "(aleatoria; en tu red local ahora apareces distinto)"))
            self._try(ctx, "cambiar")
            self._try(ctx, "mac")
        elif "-m" in args:
            i = args.index("-m")
            new = args[i + 1] if i + 1 < len(args) else None
            if new:
                ctx.flags["mac"] = new
                ctx.print(c("g", f"MAC fijada a: {new}"))
                self._try(ctx, "cambiar")
                self._try(ctx, "mac")
            else:
                ctx.print("Uso: macchanger -m XX:XX:XX:XX:XX:XX eth0")
        else:
            ctx.print("Uso: macchanger -s eth0 (ver)  |  -r eth0 (aleatoria)  |  -m <mac> eth0 (fijar)")

    def cmd_vpn(self, ctx, args, raw):
        sub = args[1] if len(args) > 1 else "status"
        if sub in ("connect", "on", "up"):
            ctx.flags["tunnel"] = "vpn"
            ctx.print(c("g", f"VPN conectada. Tu tráfico sale por {VPN_IP}."), c("d", "El sitio ve la IP del VPN, no la tuya."))
            self._try(ctx, "conectar")
            self._try(ctx, "tunel")
        elif sub in ("disconnect", "off", "down"):
            ctx.flags["tunnel"] = None
            ctx.print(c("d", "VPN desconectada."))
        else:
            ctx.print(f"VPN: {'conectada' if ctx.flags.get('tunnel') == 'vpn' else 'desconectada'}", c("d", "Uso: vpn connect | vpn disconnect"))

    def cmd_tor(self, ctx, args, raw):
        sub = args[1] if len(args) > 1 else "status"
        if sub in ("start", "on", "connect"):
            ctx.flags["tunnel"] = "tor"
            ctx.print(c("g", f"Tor arrancado. Tu tráfico pasa por 3 saltos; sale por {TOR_IP}."),
                      c("d", "Cifrado en capas (como una cebolla): ningún salto conoce origen y destino a la vez."))
            self._try(ctx, "conectar")
            self._try(ctx, "tunel")
        elif sub in ("stop", "off"):
            ctx.flags["tunnel"] = None
            ctx.print(c("d", "Tor detenido."))
        else:
            ctx.print(f"Tor: {'activo' if ctx.flags.get('tunnel') == 'tor' else 'inactivo'}", c("d", "Uso: tor start | tor stop"))

    def cmd_exiftool(self, ctx, args, raw):
        if "-all=" in args:
            ctx.flags["meta_clean"] = True
            ctx.print(c("g", "Todos los metadatos eliminados de foto.jpg."), c("d", "Ya no revela ubicación, equipo ni autor."))
            self._try(ctx, "limpiar")
            self._try(ctx, "meta")
            return
        if ctx.flags.get("meta_clean"):
            ctx.print(c("d", "foto.jpg: sin metadatos (ya la limpiaste)."))
            return
        ctx.print(
            c("w", "foto.jpg — metadatos:"),
            "  Make/Model      : Samsung SM-G991B",
            "  Create Date     : 2026:10:14 18:22:03",
            c("r", "  GPS Position    : 19.4326 N, 99.1332 W") + c("d", "  <- ¡tu ubicación exacta!"),
            "  Artist          : tu-equipo / Alan",
            "  Software        : Camera 13.2",
        )
        self._try(ctx, "ver_meta")

    def cmd_history(self, ctx, args, raw):
        if "-c" in args:
            ctx.flags["hist_clean"] = True
            ctx.print(c("g", "Historial de comandos borrado."))
            self._try(ctx, "hist")
        else:
            ctx.print("  1  ip a", "  2  macchanger -r eth0", "  3  tor start", c("d", "Uso: history -c  (borra el historial)"))

    def cmd_check(self, ctx, args, raw):
        sub = args[1] if len(args) > 1 else ""
        if sub == "dns":
            if ctx.flags.get("tunnel"):
                ctx.print(c("g", "Sin fugas de DNS: tus consultas viajan por el túnel."))
                self._try(ctx, "dns")
            else:
                ctx.print(c("r", "⚠ Fuga de DNS: tus consultas DNS van por tu ISP (te delatan)."),
                          c("d", "Conecta el túnel (tor start / vpn connect) y vuelve a revisar."))
        elif sub in ("anonimato", "anon"):
            mac_ok = ctx.flags.get("mac", ORIG_MAC) != ORIG_MAC
            tun = ctx.flags.get("tunnel")
            dns_ok = ctx.done("dns") if self._has("dns") else True
            meta_ok = ctx.flags.get("meta_clean")
            mark = lambda ok: c("g", "✔") if ok else c("r", "✘")
            ctx.print(
                c("w", "Chequeo de anonimato:"),
                f"  {mark(mac_ok)} MAC cambiada",
                f"  {mark(bool(tun))} Túnel activo ({tun or 'ninguno'})",
                f"  {mark(dns_ok)} Sin fuga de DNS",
                f"  {mark(meta_ok)} Archivos sin metadatos",
            )
            if mac_ok and tun and dns_ok and meta_ok:
                ctx.print(c("g", "✔ Perfil anónimo. Puedes operar sin dejar una huella que te señale."))
                self._try(ctx, "final")
            else:
                ctx.print(c("y", "Aún te falta alguna capa. Complétala y vuelve a verificar."))
        else:
            ctx.print("Uso: check dns   |   check anonimato")


# ----------------------------- Nivel 1 -----------------------------
class OpsecHuellaMission(OpsecMission):
    id = "opsec-huella"
    title = "¿Quién soy en la red?"
    codename = "HUELLA"
    level = 1
    teaches = ["IP pública vs privada", "qué es la MAC", "ip a", "tu huella digital"]
    par_time = 480
    summary = ("Antes de ocultarte, entiende qué te delata. Descubre tu IP pública (la que ve Internet), "
               "tu IP privada y tu dirección MAC, y para qué sirve cada una.")
    briefing = [
        "Laboratorio de privacidad. Este es TU equipo simulado.",
        "Tres cosas te identifican: tu IP pública, tu IP privada y tu MAC.",
        "Empieza con:  aprende terminal   y luego   miip",
    ]
    outro = "Ya sabes qué te identifica: la IP pública te ubica en Internet, la privada en tu red, y la MAC es tu tarjeta de red. Saber esto es el primer paso para protegerte."
    help_extra = [("miip", "muestra tu IP pública"), ("ip a / ifconfig", "tu IP privada y tu MAC"), ("hostname", "nombre del equipo")]
    hosts = {"equipo": {"ip": PRIV_IP, "dns": HOST, "users": {"tu": {"home": "/home/tu"}},
        "fs": {"/home/tu/LEEME.txt": "\n".join([
            "Tu huella en la red:",
            "  miip           -> tu IP PÚBLICA (la que ve cualquier sitio web)",
            "  ip a           -> tu IP PRIVADA (solo en tu red local) y tu MAC",
            "  hostname       -> el nombre de tu equipo",
            "Luego responde: cuál identifica tu hardware y cuál ve un sitio web.",
        ])}}}
    objectives = [
        {"id": "guia", "title": "Leer la guía", "points": 40, "read": "/home/tu/LEEME.txt",
         "desc": "cat LEEME.txt", "lesson": "Saber qué te expone es el primer paso.", "hints": ["cat LEEME.txt"]},
        {"id": "pub", "title": "Ver tu IP pública", "points": 70, "requires": "guia", "cmd": r"^(miip|curl\s+.*(ifconfig|ipinfo|icanhazip))",
         "desc": "miip", "lesson": "La IP pública te ubica (país, ISP) ante cada web que visitas.", "hints": ["miip"]},
        {"id": "priv", "title": "Ver tu IP privada y tu MAC", "points": 70, "requires": "guia", "cmd": r"^(ip\s+(a|addr|address|link)\b|ifconfig)",
         "desc": "ip a", "lesson": "La IP privada solo vale en tu red local; la MAC identifica tu tarjeta de red.", "hints": ["ip a"]},
        {"id": "q_hw", "title": "¿Qué identifica tu hardware?", "points": 90, "requires": "priv",
         "question": "¿Qué identificador pertenece a tu tarjeta de red (tu hardware)?", "answer": ["mac", "la mac", "direccion mac", "la direccion mac"],
         "desc": "responder <texto>", "lesson": "La MAC viene de fábrica en la tarjeta de red.", "hints": ["responder MAC"]},
        {"id": "q_web", "title": "¿Qué ve una web?", "points": 90, "requires": "pub",
         "question": "¿Qué dirección ve un sitio web cuando lo visitas?", "answer": ["ip publica", "la ip publica", "mi ip publica", "ip publica", "publica"],
         "desc": "responder <texto>", "lesson": "Por eso ocultar la IP pública es la base del anonimato.", "hints": ["responder IP pública"]},
    ]
    required = ["guia", "pub", "priv", "q_hw", "q_web"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Mentora", "title": "Primero, conócete",
               "text": "No puedes proteger lo que no entiendes. Mira qué te identifica en la red."}]

    def extra_commands(self):
        return {"miip": (self.cmd_miip, "tu IP pública"), "ip": (self.cmd_ip, "ip a | ip link"),
                "ifconfig": (self.cmd_ifconfig, "tu IP y MAC"), "hostname": (self.cmd_hostname, "nombre del equipo")}


# ----------------------------- Nivel 2 -----------------------------
class OpsecMacMission(OpsecMission):
    id = "opsec-mac"
    title = "Cambia tu MAC"
    codename = "MÁSCARA"
    level = 2
    teaches = ["dirección MAC", "macchanger", "privacidad en la LAN", "identidad de hardware"]
    par_time = 540
    summary = ("Tu MAC es visible para todo el que esté en tu misma red (una Wi-Fi pública, por ejemplo) y permite rastrearte. "
               "Aprende a cambiarla en tu propio equipo para no dejar ese rastro.")
    briefing = [
        "Estás por conectarte a una red que no controlas (una Wi-Fi pública).",
        "Tu MAC real quedaría registrada. Vamos a cambiarla por una aleatoria.",
        "Empieza con:  aprende terminal   y luego   macchanger -s eth0",
    ]
    outro = "Cambiaste tu MAC por una aleatoria: en la red local ya no apareces con tu identidad de hardware real. Esto se hace SOLO en tu propio equipo."
    help_extra = [("macchanger -s eth0", "ver la MAC"), ("macchanger -r eth0", "MAC aleatoria"), ("ifconfig eth0 down/up", "bajar/subir la interfaz")]
    hosts = {"equipo": {"ip": PRIV_IP, "dns": HOST, "users": {"tu": {"home": "/home/tu"}},
        "fs": {"/home/tu/LEEME.txt": "\n".join([
            "Cambiar tu MAC (en TU equipo):",
            "  1. Mira la actual:   macchanger -s eth0",
            "  2. (opcional) baja la interfaz:  ifconfig eth0 down",
            "  3. Asigna una aleatoria:         macchanger -r eth0",
            "  4. Súbela otra vez:              ifconfig eth0 up",
            "  5. Verifica el cambio:           macchanger -s eth0",
            "Responde dónde es visible tu MAC.",
        ])}}}
    objectives = [
        {"id": "guia", "title": "Leer la guía", "points": 40, "read": "/home/tu/LEEME.txt", "desc": "cat LEEME.txt",
         "lesson": "La MAC se cambia en tu propio equipo, por privacidad.", "hints": ["cat LEEME.txt"]},
        {"id": "ver", "title": "Ver tu MAC actual", "points": 60, "requires": "guia", "cmd": r"^(macchanger\s+(-s|--show)|ip\s+link)",
         "desc": "macchanger -s eth0", "lesson": "La MAC de fábrica es única y rastreable.", "hints": ["macchanger -s eth0"]},
        {"id": "cambiar", "title": "Asignar una MAC aleatoria", "points": 140, "requires": "ver",
         "desc": "macchanger -r eth0", "lesson": "Una MAC aleatoria rompe el rastreo por hardware en la red local.", "hints": ["macchanger -r eth0"]},
        {"id": "verificar", "title": "Verificar que cambió", "points": 90, "requires": "cambiar",
         "desc": "macchanger -s eth0", "lesson": "Siempre confirma: la MAC actual ya no debe ser la de fábrica.", "hints": ["macchanger -s eth0"]},
        {"id": "q_scope", "title": "¿Dónde se ve tu MAC?", "points": 80, "requires": "guia",
         "question": "¿Dónde es visible tu MAC: en todo Internet o solo en tu red local?", "answer": ["red local", "la red local", "lan", "en la red local", "en la lan", "local"],
         "desc": "responder <texto>", "lesson": "La MAC no cruza routers: solo la ve tu red local. La IP pública sí viaja por Internet.", "hints": ["responder red local"]},
    ]
    required = ["guia", "ver", "cambiar", "verificar", "q_scope"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Mentora", "title": "Ponte una máscara",
               "text": "Antes de usar esa Wi-Fi, cambia tu MAC. Así no dejas tu identidad de hardware."}]

    def extra_commands(self):
        return {"macchanger": (self.cmd_macchanger, "cambia tu MAC"), "ifconfig": (self.cmd_ifconfig, "baja/sube la interfaz"),
                "ip": (self.cmd_ip, "ip link")}


# ----------------------------- Nivel 3 -----------------------------
class OpsecIpMission(OpsecMission):
    id = "opsec-ip"
    title = "Oculta tu IP"
    codename = "TÚNEL"
    level = 3
    teaches = ["VPN", "Tor", "nodo de salida", "fugas de DNS"]
    par_time = 600
    summary = ("Tu IP pública revela quién y dónde eres. Aprende a enrutar tu tráfico por un VPN o por Tor "
               "para que los sitios vean otra IP, no la tuya.")
    briefing = [
        "Tu IP pública te ubica. Vamos a ocultarla tras un túnel.",
        "Mira tu IP, conéctate (VPN o Tor), y vuelve a mirar: debe cambiar.",
        "Empieza con:  aprende terminal   y luego   miip",
    ]
    outro = "Ocultaste tu IP real tras un túnel: el sitio ve el nodo de salida, no a ti. Tor da más anonimato (varios saltos, cifrado en capas); un VPN es más rápido pero confías en el proveedor."
    help_extra = [("miip", "ver tu IP pública"), ("vpn connect", "conectar VPN"), ("tor start", "arrancar Tor")]
    hosts = {"equipo": {"ip": PRIV_IP, "dns": HOST, "users": {"tu": {"home": "/home/tu"}},
        "fs": {"/home/tu/LEEME.txt": "\n".join([
            "Ocultar tu IP:",
            "  1. Mira tu IP real:   miip",
            "  2. Conéctate:         vpn connect    (o)   tor start",
            "  3. Vuelve a mirar:    miip    -> debe ser otra IP",
            "Responde qué IP ve el sitio y qué red usa saltos con cifrado en capas.",
        ])}}}
    objectives = [
        {"id": "guia", "title": "Leer la guía", "points": 40, "read": "/home/tu/LEEME.txt", "desc": "cat LEEME.txt",
         "lesson": "Un túnel cambia la IP que el mundo ve.", "hints": ["cat LEEME.txt"]},
        {"id": "antes", "title": "Ver tu IP real", "points": 60, "requires": "guia", "cmd": r"^(miip|curl\s+.*ifconfig)",
         "desc": "miip", "lesson": "Esta es la IP que quieres esconder.", "hints": ["miip"]},
        {"id": "conectar", "title": "Conectar VPN o Tor", "points": 120, "requires": "antes", "cmd": r"^(vpn\s+(connect|on|up)|tor\s+(start|on|connect))",
         "desc": "vpn connect   (o)   tor start", "lesson": "Tu tráfico sale ahora por el servidor del túnel.", "hints": ["tor start", "o: vpn connect"]},
        {"id": "oculta", "title": "Comprobar que tu IP cambió", "points": 120, "requires": "conectar",
         "desc": "Vuelve a correr: miip", "lesson": "El sitio ve la IP del nodo de salida, no la tuya.", "hints": ["miip"]},
        {"id": "q_exit", "title": "¿Qué IP ve el sitio?", "points": 90, "requires": "oculta",
         "question": "Con el túnel activo, ¿qué IP ve el sitio web que visitas?", "answer": ["la del vpn", "la del tor", "nodo de salida", "el nodo de salida", "la del nodo de salida", "la del servidor vpn", "exit node", "la del tunel"],
         "desc": "responder <texto>", "lesson": "Nunca ve tu IP real mientras el túnel esté bien configurado.", "hints": ["responder nodo de salida"]},
        {"id": "q_tor", "title": "¿Cuál usa varios saltos?", "points": 80, "requires": "guia",
         "question": "¿Qué red usa varios saltos con cifrado en capas (como una cebolla)?", "answer": ["tor"],
         "desc": "responder <texto>", "lesson": "Tor = The Onion Router. Más anonimato; un VPN es un solo salto y confías en el proveedor.", "hints": ["responder Tor"]},
    ]
    required = ["guia", "antes", "conectar", "oculta", "q_exit", "q_tor"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Mentora", "title": "Entra al túnel",
               "text": "Esconde tu IP real detrás de un VPN o de Tor y confírmalo."}]

    def extra_commands(self):
        return {"miip": (self.cmd_miip, "tu IP pública"), "vpn": (self.cmd_vpn, "vpn connect/disconnect"),
                "tor": (self.cmd_tor, "tor start/stop")}


# ----------------------------- Nivel 4 -----------------------------
class OpsecRastrosMission(OpsecMission):
    id = "opsec-rastros"
    title = "Limpia tus rastros"
    codename = "SIN HUELLA"
    level = 4
    teaches = ["metadatos EXIF", "exiftool", "historial de comandos", "higiene de archivos"]
    par_time = 660
    summary = ("Ocultar tu IP no sirve si el archivo que compartes lleva tu ubicación GPS, tu nombre y tu equipo "
               "en los metadatos. Aprende a verlos y a borrarlos, y a limpiar tu historial.")
    briefing = [
        "Vas a compartir una foto. Antes, revisa qué delata.",
        "Los archivos guardan metadatos (EXIF): GPS, autor, equipo, fecha.",
        "Empieza con:  aprende terminal   y luego   exiftool foto.jpg",
    ]
    outro = "Viste que la foto traía tu ubicación GPS y tu nombre, los borraste y limpiaste tu historial. Compartir sin limpiar metadatos es una de las fugas más comunes."
    help_extra = [("exiftool foto.jpg", "ver metadatos"), ("exiftool -all= foto.jpg", "borrar metadatos"), ("history -c", "borrar el historial")]
    hosts = {"equipo": {"ip": PRIV_IP, "dns": HOST, "users": {"tu": {"home": "/home/tu"}},
        "fs": {"/home/tu/foto.jpg": "[imagen con metadatos]",
            "/home/tu/LEEME.txt": "\n".join([
                "Limpiar rastros antes de compartir:",
                "  1. Mira los metadatos:   exiftool foto.jpg",
                "  2. Responde qué dato de ubicación trae.",
                "  3. Bórralos todos:       exiftool -all= foto.jpg",
                "  4. Limpia tu historial:  history -c",
            ])}}}
    objectives = [
        {"id": "guia", "title": "Leer la guía", "points": 40, "read": "/home/tu/LEEME.txt", "desc": "cat LEEME.txt",
         "lesson": "Los metadatos delatan tanto como la IP.", "hints": ["cat LEEME.txt"]},
        {"id": "ver_meta", "title": "Ver los metadatos de la foto", "points": 100, "requires": "guia",
         "desc": "exiftool foto.jpg", "lesson": "Una foto puede traer tu ubicación exacta sin que lo sepas.", "hints": ["exiftool foto.jpg"]},
        {"id": "q_gps", "title": "¿Qué dato delator trae?", "points": 90, "requires": "ver_meta",
         "question": "¿Qué dato de ubicación trae la foto en sus metadatos?", "answer": ["gps", "coordenadas", "ubicacion", "la ubicacion", "ubicacion gps", "las coordenadas gps", "coordenadas gps"],
         "desc": "responder <texto>", "lesson": "El GPS en EXIF revela dónde se tomó la foto, calle incluida.", "hints": ["responder GPS"]},
        {"id": "limpiar", "title": "Borrar los metadatos", "points": 130, "requires": "ver_meta",
         "desc": "exiftool -all= foto.jpg", "lesson": "Borrar EXIF antes de compartir quita ubicación, equipo y autor.", "hints": ["exiftool -all= foto.jpg"]},
        {"id": "hist", "title": "Limpiar tu historial", "points": 90, "requires": "guia", "cmd": r"^history\s+-c",
         "desc": "history -c", "lesson": "El historial guarda todo lo que escribiste; límpialo al terminar.", "hints": ["history -c"]},
    ]
    required = ["guia", "ver_meta", "q_gps", "limpiar", "hist"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Mentora", "title": "No dejes rastro",
               "text": "Antes de compartir esa foto, mira qué esconde en sus metadatos."}]

    def extra_commands(self):
        return {"exiftool": (self.cmd_exiftool, "ver/borrar metadatos"), "history": (self.cmd_history, "history -c")}


# ----------------------------- Nivel 5 -----------------------------
class OpsecCadenaMission(OpsecMission):
    id = "opsec-cadena"
    title = "Cadena de anonimato"
    codename = "FANTASMA"
    level = 5
    teaches = ["OPSEC por capas", "MAC + Tor + DNS", "fuga de DNS", "verificación final"]
    par_time = 840
    summary = ("El anonimato es por capas: una sola falla te descubre. Combina todo lo aprendido —cambiar la MAC, "
               "levantar un túnel, cerrar la fuga de DNS y limpiar metadatos— y verifícalo antes de operar.")
    briefing = [
        "Ejercicio final. Vas a prepararte para operar sin dejar una huella que te señale.",
        "Capas: MAC aleatoria -> túnel (Tor/VPN) -> sin fuga de DNS -> archivos limpios.",
        "Al final, verifica todo con:  check anonimato",
    ]
    outro = "Armaste la cadena completa: MAC cambiada, túnel activo, sin fuga de DNS y archivos sin metadatos. Así trabaja un profesional que respeta su propia privacidad y la de otros."
    help_extra = [("macchanger -r eth0", "MAC aleatoria"), ("tor start / vpn connect", "túnel"),
                  ("check dns", "revisar fuga de DNS"), ("exiftool -all= informe.jpg", "limpiar metadatos"), ("check anonimato", "verificación final")]
    hosts = {"equipo": {"ip": PRIV_IP, "dns": HOST, "users": {"tu": {"home": "/home/tu"}},
        "fs": {"/home/tu/informe.jpg": "[captura con metadatos]",
            "/home/tu/PLAN.txt": "\n".join([
                "Cadena de anonimato (en orden):",
                "  1. Cambia tu MAC:        macchanger -r eth0",
                "  2. Levanta el túnel:     tor start   (o vpn connect)",
                "  3. Revisa fuga de DNS:   check dns",
                "  4. Limpia metadatos:     exiftool -all= informe.jpg",
                "  5. Verificación final:   check anonimato",
            ])}}}
    objectives = [
        {"id": "guia", "title": "Leer el plan", "points": 40, "read": "/home/tu/PLAN.txt", "desc": "cat PLAN.txt",
         "lesson": "El orden importa: capa por capa.", "hints": ["cat PLAN.txt"]},
        {"id": "mac", "title": "Cambiar la MAC", "points": 110, "requires": "guia",
         "desc": "macchanger -r eth0", "lesson": "Primera capa: tu identidad de hardware.", "hints": ["macchanger -r eth0"]},
        {"id": "tunel", "title": "Levantar el túnel", "points": 120, "requires": "guia",
         "desc": "tor start  (o vpn connect)", "lesson": "Segunda capa: oculta tu IP.", "hints": ["tor start"]},
        {"id": "dns", "title": "Cerrar la fuga de DNS", "points": 130, "requires": "tunel",
         "desc": "check dns", "lesson": "De nada sirve el túnel si tu DNS sale por el ISP y te delata.", "hints": ["check dns"]},
        {"id": "meta", "title": "Limpiar los metadatos", "points": 120, "requires": "guia",
         "desc": "exiftool -all= informe.jpg", "lesson": "Tercera capa: lo que compartes no debe delatarte.", "hints": ["exiftool -all= informe.jpg"]},
        {"id": "final", "title": "Verificación final", "points": 160, "requires": "dns",
         "desc": "check anonimato", "lesson": "Nunca operes sin verificar las cuatro capas.", "hints": ["check anonimato"]},
    ]
    required = ["guia", "mac", "tunel", "dns", "meta", "final"]
    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Mentora", "title": "El examen",
         "text": "Arma la cadena completa y verifícala. Una sola capa floja y te descubren."},
        {"id": "tip", "at": 180, "unless": "final", "kind": "msg", "sender": "Mentora", "title": "Orden",
         "text": "Recuerda revisar la fuga de DNS DESPUÉS de levantar el túnel, y verificar todo al final."},
    ]

    def extra_commands(self):
        return {"macchanger": (self.cmd_macchanger, "MAC aleatoria"), "ifconfig": (self.cmd_ifconfig, "interfaz"),
                "tor": (self.cmd_tor, "tor start/stop"), "vpn": (self.cmd_vpn, "vpn connect/disconnect"),
                "miip": (self.cmd_miip, "tu IP pública"), "exiftool": (self.cmd_exiftool, "limpiar metadatos"),
                "check": (self.cmd_check, "check dns | check anonimato")}
