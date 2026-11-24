"""Niveles 1, 2, 3 y 5 de Blue Team / SOC."""
from ..engine import c
from .base import GuidedMission

OFICIAL = "banco-meridiano.com"
FALSO = "banco-meridlano.com"  # i -> l, dominio sosia

class BluePhishingMission(GuidedMission):
    id = "blue-phishing"
    role = "blue"
    role_name = "Blue Team / SOC"
    title = "El correo del lunes"
    codename = "ANZUELO"
    level = 1
    teaches = ["qué es el phishing", "remitentes falsos", "enlaces engañosos", "reportar al SOC"]
    par_time = 540
    summary = ("Tu primer dia en el SOC de Banco Meridiano. Llegaron tres correos al buzon de reportes. "
               "Aprende a distinguir un correo normal de uno de phishing, repórtalo y bloquea el dominio falso.")
    start = {"host": "soc-ws", "user": "analista", "cwd": "/home/analista"}
    briefing = [
        "Banco Meridiano - Centro de Operaciones de Seguridad (SOC). 09:02.",
        "Los correos reportados estan en ~/correo como archivos .eml; abrelos con cat.",
        "El dominio oficial del banco es banco-meridiano.com. Nada mas.",
        "Empieza con:  aprende phishing   y luego   ls correo",
    ]
    outro = "Detectaste el correo falso, lo reportaste y bloqueaste el dominio sosia. Asi se evita que alguien entregue su contrasena."
    help_extra = [("reportar <archivo>", "marca un correo como phishing"), ("bloquear <dominio>", "bloquea un dominio en el filtro")]

    MAILS = {
        "1_nomina.eml": "De: Recursos Humanos <rh@banco-meridiano.com>\nAsunto: Calendario de pago de noviembre\n\nHola equipo: el pago sera el viernes 14. Consulten su recibo en el\nportal de siempre: https://intranet.banco-meridiano.com/nomina\nSaludos, RH.",
        "2_mantenimiento.eml": "De: Boletin TI <noticias@banco-meridiano.com>\nAsunto: Mantenimiento programado del sabado\n\nEl sabado de 02:00 a 04:00 el portal estara en mantenimiento.\nNo se requiere ninguna accion de su parte.",
        "3_seguridad.eml": "De: Soporte Seguridad <seguridad@banco-meridlano.com>\nAsunto: URGENTE: su cuenta sera bloqueada en 2 horas\n\nDetectamos un acceso sospechoso. Para EVITAR el bloqueo inmediato,\nverifique su identidad AHORA en el siguiente enlace:\nhttps://banco-meridlano.com/verificar?id=982  (escriba su usuario y contrasena)\nSi no lo hace en 2 horas perdera el acceso a su dinero.",
    }

    hosts = {
        "soc-ws": {"ip": "10.0.8.21", "users": {"analista": {"home": "/home/analista"}},
            "fs": dict({
                "/home/analista/LEEME.txt": "\n".join([
                    "Procedimiento de correo sospechoso:",
                    "1. Lee cada correo con: cat correo/<archivo>",
                    "2. Compara el dominio del remitente con el oficial (banco-meridiano.com).",
                    "3. Reporta SOLO el malicioso con:  reportar <archivo>",
                    "4. Bloquea su dominio con:  bloquear <dominio>",
                    "5. Responde que dato te pedia el correo con: responder <dato>",
                ]),
            }, **{"/home/analista/correo/" + k: v for k, v in MAILS.items()}),
        },
    }

    objectives = [
        {"id": "learn", "title": "Leer el procedimiento del SOC", "points": 40, "read": "/home/analista/LEEME.txt",
         "desc": "Abre ~/LEEME.txt con cat.", "lesson": "Siempre hay un procedimiento: seguirlo evita errores bajo presion.",
         "hints": ["cat LEEME.txt"]},
        {"id": "read_all", "title": "Leer el correo sospechoso", "points": 60, "read": "/home/analista/correo/3_seguridad.eml",
         "desc": "Lee los tres correos; el tercero es el mas raro.", "lesson": "El dominio del remitente es lo primero que se revisa.",
         "hints": ["ls correo", "cat correo/3_seguridad.eml"]},
        {"id": "report", "title": "Reportar el correo de phishing", "points": 120, "requires": "read_all",
         "desc": "Reporta el archivo malicioso con: reportar <archivo>", "lesson": "Reportar (no borrar) permite al SOC avisar a los demas y bloquear al atacante.",
         "hints": ["Es el que mete miedo y usa un dominio parecido pero no igual.", "reportar 3_seguridad.eml"]},
        {"id": "block", "title": "Bloquear el dominio falso", "points": 120, "requires": "report",
         "desc": "Bloquea el dominio del remitente falso con: bloquear <dominio>", "lesson": "banco-meridlano.com usa una l en vez de i: es un dominio sosia (typosquatting).",
         "hints": ["Mira la linea 'De:' del correo 3.", "bloquear banco-meridlano.com"]},
        {"id": "q_data", "title": "Identificar que te robaban", "points": 80, "requires": "report",
         "question": "Que dato queria robar ese correo?", "answer": ["contrasena", "usuario y contrasena", "credenciales", "password"],
         "desc": "Responde con: responder <dato>", "lesson": "El phishing casi siempre busca credenciales. El banco NUNCA las pide por correo.",
         "hints": ["Relee que te pedia escribir el enlace.", "responder contrasena"]},
    ]
    required = ["learn", "read_all", "report", "block", "q_data"]
    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Marisol - Jefa del SOC", "title": "Bienvenido",
         "text": "Tranquilo, no hay prisa en este turno. Lee ~/LEEME.txt y revisa los tres correos. Uno es falso."},
    ]

    def extra_commands(self):
        return {"reportar": (self.cmd_reportar, "reporta un correo:  reportar <archivo>"),
                "bloquear": (self.cmd_bloquear, "bloquea un dominio:  bloquear <dominio>")}

    def cmd_reportar(self, ctx, args, raw):
        if len(args) < 2:
            ctx.print("Uso: reportar <archivo.eml>"); return
        name = args[1].split("/")[-1]
        if name == "3_seguridad.eml":
            ctx.print(c("g", "Correo reportado al SOC como phishing.")); ctx.complete("report")
        elif name in self.MAILS:
            ctx.flags["wrong"] = ctx.flags.get("wrong", 0) + 1
            ctx.print(c("y", "Ese correo es legitimo (dominio banco-meridiano.com). Reportarlo da falsos positivos. Revisa de nuevo."))
        else:
            ctx.print("reportar: no existe ese correo en ~/correo")

    def cmd_bloquear(self, ctx, args, raw):
        if len(args) < 2:
            ctx.print("Uso: bloquear <dominio>"); return
        dom = args[1].strip().lower().lstrip("@")
        if not ctx.done("report"):
            ctx.print(c("y", "Primero reporta el correo malicioso.")); return
        if dom == FALSO:
            ctx.print(c("g", f"Dominio {dom} bloqueado en el filtro de correo.")); ctx.complete("block")
        elif dom == OFICIAL:
            ctx.print(c("r", "No! Ese es el dominio REAL del banco. Bloquearlo deja a todos sin correo."))
        else:
            ctx.print(c("y", f"{dom} no es el dominio del atacante. Mira bien la linea 'De:' del correo 3."))


# ----------------------------- Nivel 2 -----------------------------
class BlueCuentasMission(GuidedMission):
    id = "blue-cuentas"
    role = "blue"
    role_name = "Blue Team / SOC"
    title = "Una cuenta de mas"
    codename = "INTRUSO"
    level = 2
    teaches = ["usuarios de Linux", "/etc/passwd", "grupo sudo", "ultimos accesos"]
    par_time = 600
    summary = ("Un ex-empleado se fue la semana pasada pero sus accesos siguen activos, y alguien creo una cuenta extra con permisos de administrador. "
               "Revisa las cuentas del servidor y deja solo las que deben existir.")
    start = {"host": "srv-rh", "user": "analista", "cwd": "/home/analista"}
    briefing = [
        "Servidor de Recursos Humanos (srv-rh). Auditoria de cuentas.",
        "Las cuentas estan en /etc/passwd y los grupos en /etc/group.",
        "Empleados que SI deben existir: ana, luis, root y las de sistema.",
        "Empieza con:  aprende cuentas   y luego   cat /etc/passwd",
    ]
    outro = "Diste de baja la cuenta del ex-empleado y eliminaste la cuenta intrusa con permisos de root. Principio de minimo privilegio aplicado."
    help_extra = [("last", "ultimos inicios de sesion"), ("userdel <u>", "elimina una cuenta"), ("passwd -l <u>", "bloquea una cuenta")]

    hosts = {
        "srv-rh": {"ip": "10.0.9.3", "users": {"analista": {"home": "/home/analista", "groups": "analista,soc,sudo"}},
            "fs": {
                "/home/analista/LEEME.txt": "\n".join([
                    "Auditoria de cuentas:",
                    "1. Lee /etc/passwd (cuentas) y /etc/group (quien es admin: grupo sudo).",
                    "2. Usa  last  para ver desde donde se conectaron.",
                    "3. El ex-empleado jcarmona (BAJA) debe quedar bloqueado o eliminado.",
                    "4. Hay UNA cuenta intrusa con UID 0 (root) que nadie creo. Eliminala.",
                    "   Comandos: passwd -l <usuario>   userdel <usuario>",
                    "5. responder <usuario> con el nombre de la cuenta intrusa.",
                ]),
                "/etc/passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\nana:x:1001:1001:Ana Reyes - RH:/home/ana:/bin/bash\nluis:x:1002:1002:Luis Ortega - RH:/home/luis:/bin/bash\njcarmona:x:1003:1003:Jose Carmona (BAJA 03/nov):/home/jcarmona:/bin/bash\nsysbackup:x:0:0:backup:/root:/bin/bash",
                "/etc/group": "root:x:0:\nsudo:x:27:ana,jcarmona,sysbackup\nwww-data:x:33:\nrh:x:1001:ana,luis",
                "/var/log/wtmp.txt": "ana      pts/0   10.0.9.5    Mon Nov  9 08:40   still logged in\nluis     pts/1   10.0.9.7    Mon Nov  9 08:12 - 08:55  (00:43)\njcarmona pts/2   201.item.ip Sat Nov  7 02:14 - 02:51  (00:37)\nsysbackup pts/3  185.220.101.47 Sun Nov  8 03:03 - 03:40 (00:37)\nreboot   system  6.1.0       Fri Nov  5 00:00",
            },
        },
    }

    objectives = [
        {"id": "passwd", "title": "Revisar las cuentas del sistema", "points": 60, "read": "/etc/passwd",
         "desc": "Lee /etc/passwd.", "lesson": "UID 0 = poderes de root. Solo 'root' deberia tener UID 0.", "hints": ["cat /etc/passwd"]},
        {"id": "intruder", "title": "Identificar la cuenta intrusa (UID 0)", "points": 120, "requires": "passwd",
         "question": "Que cuenta NO deberia existir y tiene UID 0?", "answer": ["sysbackup"],
         "desc": "responder <usuario>", "lesson": "sysbackup aparenta ser de sistema pero tiene UID 0 y shell real: puerta trasera.",
         "hints": ["Busca otra linea con :0:0: que no sea root.", "grep ':0:0:' /etc/passwd", "responder sysbackup"]},
        {"id": "del_intruder", "title": "Eliminar la cuenta intrusa", "points": 140, "requires": "intruder", "cmd": r"^userdel\s+sysbackup",
         "desc": "Eliminala con: userdel <usuario>", "lesson": "Eliminar la cuenta corta el acceso del atacante.", "hints": ["userdel sysbackup"]},
        {"id": "ex_emp", "title": "Dar de baja al ex-empleado jcarmona", "points": 100, "requires": "passwd", "cmd": r"^(passwd\s+-l|userdel)\s+jcarmona",
         "desc": "Bloquea o elimina la cuenta jcarmona (ya no trabaja aqui).", "lesson": "Las cuentas de quien se va deben desactivarse de inmediato.",
         "hints": ["passwd -l jcarmona", "o userdel jcarmona"]},
    ]
    required = ["passwd", "intruder", "del_intruder", "ex_emp"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Marisol - Jefa del SOC", "title": "Auditoria",
               "text": "Revisa las cuentas de srv-rh. Hay una que nadie reconoce y jcarmona ya no trabaja con nosotros."}]

    def on_read(self, ctx, path):
        super().on_read(ctx, path)
        if path == "/etc/group":
            ctx.complete("passwd")

    def extra_commands(self):
        return {"userdel": (self.cmd_userdel, "elimina una cuenta:  userdel <usuario>"),
                "passwd": (self.cmd_passwd, "bloquea una cuenta:  passwd -l <usuario>"),
                "last": (self.cmd_last, "ultimos inicios de sesion")}

    def cmd_last(self, ctx, args, raw):
        ctx.print(*(ctx.read("/var/log/wtmp.txt") or "").split("\n"))
        ctx.m_on = True

    def cmd_userdel(self, ctx, args, raw):
        if len(args) < 2:
            ctx.print("Uso: userdel <usuario>"); return
        u = args[1]
        if u in ("root", "ana", "luis", "www-data", "daemon"):
            ctx.print(c("r", f"Peligro: {u} es una cuenta legitima/critica. No la elimines.")); return
        if u in ("sysbackup", "jcarmona"):
            ctx.print(c("g", f"Cuenta {u} eliminada."))
        else:
            ctx.print(f"userdel: el usuario '{u}' no existe")

    def cmd_passwd(self, ctx, args, raw):
        if "-l" in args and len(args) > args.index("-l") + 1:
            u = args[args.index("-l") + 1]
            ctx.print(c("g", f"Cuenta {u} bloqueada (passwd -l)."))
        else:
            ctx.print("Uso: passwd -l <usuario>")


# ----------------------------- Nivel 3 -----------------------------
def _authlog_n3():
    return "Nov  9 04:10:02 srv-app sshd[900]: Failed password for ubuntu from 45.33.12.9 port 57833 ssh2\nNov  9 04:10:04 srv-app sshd[901]: Failed password for test from 45.33.12.9 port 59789 ssh2\nNov  9 04:10:08 srv-app sshd[902]: Failed password for ubuntu from 45.33.12.9 port 42147 ssh2\nNov  9 04:10:09 srv-app sshd[903]: Failed password for oracle from 45.33.12.9 port 48498 ssh2\nNov  9 04:10:11 srv-app sshd[904]: Failed password for admin from 45.33.12.9 port 55409 ssh2\nNov  9 04:10:15 srv-app sshd[905]: Failed password for oracle from 45.33.12.9 port 44935 ssh2\nNov  9 04:10:17 srv-app sshd[906]: Failed password for admin from 45.33.12.9 port 57143 ssh2\nNov  9 04:10:21 srv-app sshd[907]: Failed password for root from 45.33.12.9 port 42098 ssh2\nNov  9 04:10:23 srv-app sshd[908]: Failed password for ubuntu from 45.33.12.9 port 41402 ssh2\nNov  9 04:10:26 srv-app sshd[909]: Failed password for root from 45.33.12.9 port 48828 ssh2\nNov  9 04:10:30 srv-app sshd[910]: Failed password for ubuntu from 45.33.12.9 port 52701 ssh2\nNov  9 04:10:34 srv-app sshd[911]: Failed password for oracle from 45.33.12.9 port 58904 ssh2\nNov  9 04:10:38 srv-app sshd[912]: Failed password for admin from 45.33.12.9 port 51977 ssh2\nNov  9 04:10:39 srv-app sshd[913]: Failed password for root from 45.33.12.9 port 44455 ssh2\nNov  9 04:10:43 srv-app sshd[914]: Failed password for admin from 45.33.12.9 port 48453 ssh2\nNov  9 04:10:47 srv-app sshd[915]: Failed password for test from 45.33.12.9 port 53800 ssh2\nNov  9 04:10:51 srv-app sshd[916]: Failed password for ubuntu from 45.33.12.9 port 51498 ssh2\nNov  9 04:10:55 srv-app sshd[917]: Failed password for ubuntu from 45.33.12.9 port 47614 ssh2\nNov  9 04:10:58 srv-app sshd[918]: Failed password for root from 45.33.12.9 port 49164 ssh2\nNov  9 04:11:00 srv-app sshd[919]: Failed password for test from 45.33.12.9 port 57752 ssh2\nNov  9 04:11:01 srv-app sshd[920]: Failed password for admin from 45.33.12.9 port 58793 ssh2\nNov  9 04:11:04 srv-app sshd[921]: Failed password for test from 45.33.12.9 port 44077 ssh2\nNov  9 04:11:05 srv-app sshd[922]: Failed password for oracle from 45.33.12.9 port 55843 ssh2\nNov  9 04:11:06 srv-app sshd[923]: Failed password for test from 45.33.12.9 port 42182 ssh2\nNov  9 04:11:10 srv-app sshd[924]: Failed password for admin from 45.33.12.9 port 40659 ssh2\nNov  9 04:11:13 srv-app sshd[925]: Failed password for oracle from 45.33.12.9 port 53605 ssh2\nNov  9 04:11:14 srv-app sshd[926]: Failed password for root from 45.33.12.9 port 59824 ssh2\nNov  9 04:11:15 srv-app sshd[927]: Failed password for oracle from 45.33.12.9 port 59214 ssh2\nNov  9 04:11:18 srv-app sshd[928]: Failed password for ubuntu from 45.33.12.9 port 49144 ssh2\nNov  9 04:11:20 srv-app sshd[929]: Failed password for root from 45.33.12.9 port 50147 ssh2\nNov  9 04:11:21 srv-app sshd[930]: Failed password for root from 45.33.12.9 port 43542 ssh2\nNov  9 04:11:22 srv-app sshd[931]: Failed password for admin from 45.33.12.9 port 53367 ssh2\nNov  9 04:11:25 srv-app sshd[932]: Failed password for ubuntu from 45.33.12.9 port 48630 ssh2\nNov  9 04:11:27 srv-app sshd[933]: Failed password for root from 45.33.12.9 port 51135 ssh2\nNov  9 04:11:30 srv-app sshd[934]: Accepted password for admin from 45.33.12.9 port 50122 ssh2\nNov  9 04:11:33 srv-app sshd[935]: Failed password for admin from 45.33.12.9 port 52379 ssh2\nNov  9 04:11:37 srv-app sshd[936]: Failed password for oracle from 45.33.12.9 port 57041 ssh2\nNov  9 04:11:41 srv-app sshd[937]: Failed password for ubuntu from 45.33.12.9 port 58325 ssh2"

class BlueLogsMission(GuidedMission):
    id = "blue-logs"
    role = "blue"
    role_name = "Blue Team / SOC"
    title = "Lo que dicen los logs"
    codename = "RASTRO"
    level = 3
    teaches = ["leer logs", "grep y conteo", "awk + sort + uniq", "fuerza bruta exitosa"]
    par_time = 720
    summary = ("Hubo movimiento raro de madrugada en el servidor de aplicaciones. Nadie sabe si entraron. "
               "Usa los logs para reconstruir que paso: cuantos intentos hubo, desde que IP y si alguno tuvo exito.")
    start = {"host": "srv-app", "user": "analista", "cwd": "/home/analista"}
    briefing = [
        "Servidor de aplicaciones (srv-app). Revision de madrugada.",
        "Log de accesos SSH: /var/log/auth.log",
        "Pista de oro: muchos 'Failed password' y luego un 'Accepted' = entraron.",
        "Empieza con:  aprende logs",
    ]
    outro = "Reconstruiste el ataque: fuerza bruta desde 45.33.12.9 que termino en un login exitoso de 'admin'. Esa cuenta hay que resetearla."
    help_extra = [("grep / wc", "cuenta coincidencias"), ("awk '{print $N}'", "saca una columna")]

    hosts = {
        "srv-app": {"ip": "10.0.7.4", "users": {"analista": {"home": "/home/analista", "groups": "analista,soc"}},
            "fs": {
                "/home/analista/LEEME.txt": "\n".join([
                    "Analisis de /var/log/auth.log:",
                    "  grep Failed /var/log/auth.log | wc -l    cuantos intentos fallidos",
                    "  awk '{print $(NF-3)}' ... | sort | uniq -c  agrupa por IP de origen",
                    "  grep Accepted /var/log/auth.log           que login SI funciono",
                    "Responde: responder <ip>  y  responder <usuario> de la cuenta comprometida.",
                ]),
                "/var/log/auth.log": _authlog_n3(),
            },
        },
    }

    objectives = [
        {"id": "read_log", "title": "Abrir el log de accesos", "points": 50, "read": "/var/log/auth.log",
         "desc": "Lee (o haz tail de) /var/log/auth.log.", "lesson": "auth.log registra cada intento de inicio de sesion SSH.",
         "hints": ["tail -n 20 /var/log/auth.log"]},
        {"id": "find_ip", "title": "Encontrar la IP atacante", "points": 120, "requires": "read_log",
         "question": "Desde que IP vienen casi todos los intentos?", "answer": ["45.33.12.9"],
         "desc": "responder <ip>", "lesson": "Una sola IP concentrando decenas de fallos = fuerza bruta.",
         "hints": ["grep Failed /var/log/auth.log", "Es la IP que mas se repite.", "responder 45.33.12.9"]},
        {"id": "find_user", "title": "Averiguar si entraron y con que cuenta", "points": 150, "requires": "find_ip",
         "question": "Que usuario tuvo un login ACEPTADO desde esa IP?", "answer": ["admin"],
         "desc": "responder <usuario>", "lesson": "Un 'Accepted password' despues de muchos 'Failed' significa que adivinaron la contrasena.",
         "hints": ["grep Accepted /var/log/auth.log", "responder admin"]},
        {"id": "count", "title": "Contar los intentos fallidos", "points": 100, "requires": "read_log",
         "question": "Cuantos 'Failed password' hay en total?", "answer": ["37"],
         "desc": "responder <numero>", "lesson": "grep ... | wc -l cuenta lineas sin que las tengas que contar a mano.",
         "hints": ["grep Failed /var/log/auth.log | wc -l", "responder 37"]},
    ]
    required = ["read_log", "find_ip", "find_user", "count"]
    events = [{"id": "intro", "at": 2, "kind": "msg", "sender": "Marisol - Jefa del SOC", "title": "Revision",
               "text": "Dime tres cosas del log: desde que IP vino el ataque, si entraron y con que cuenta."}]


# ----------------------------- Nivel 5 -----------------------------
RANSOM_PROC = {"pid": 6610, "user": "svc_app", "cpu": 93.4, "mem": 5.0, "cmd": "/usr/bin/python3 /opt/.cryptor/lock.py --ext .locked"}
SVC_PATH = "/etc/systemd/system/sysupdate.service"
BAD_IP = "193.47.61.20"

class BlueRansomwareMission(GuidedMission):
    id = "blue-ransomware"
    role = "blue"
    role_name = "Blue Team / SOC"
    title = "Hora cero: ransomware"
    codename = "CANDADO"
    level = 5
    teaches = ["respuesta a incidentes", "aislar", "persistencia en systemd", "restaurar respaldos"]
    par_time = 900
    summary = ("Los archivos de un servidor de archivos se estan cifrando AHORA y aparecio una nota de rescate. "
               "Tienes que aislar el equipo, detener el proceso, quitar su persistencia, cortar la cuenta y restaurar desde un respaldo limpio, en orden y contrarreloj.")
    start = {"host": "srv-files", "user": "analista", "cwd": "/home/analista"}
    meter = {"key": "files", "label": "ARCHIVOS SANOS", "start": 100, "max": 100, "fail_at": 0,
             "direction": "down", "fail_text": "El ransomware cifro todo el servidor de archivos antes de que lo contuvieras."}
    briefing = [
        "Servidor de archivos (srv-files). 11:58. ALERTA ROJA.",
        "Un proceso esta cifrando archivos en este momento. El medidor ARCHIVOS SANOS baja mientras siga vivo.",
        "Orden recomendado: aislar -> matar proceso -> quitar persistencia -> cortar cuenta -> restaurar.",
        "Empieza ya con:  aprende ransomware   (rapido) y luego  ps aux",
    ]
    outro = "Contuviste el ransomware: red aislada, proceso muerto, servicio de persistencia eliminado, cuenta revocada y datos restaurados desde respaldo limpio."
    initial_flags = {"procs": [
        {"pid": 1, "user": "root", "cpu": 0.0, "mem": 0.2, "cmd": "/sbin/init"},
        {"pid": 702, "user": "root", "cpu": 0.0, "mem": 0.4, "cmd": "/usr/sbin/sshd -D"},
        {"pid": 980, "user": "root", "cpu": 0.1, "mem": 1.1, "cmd": "/usr/sbin/smbd"},
        RANSOM_PROC,
    ], "isolated": False, "killed": False, "service": True, "account": True, "restored": False, "decay": True}
    help_extra = [("netcut / aislar", "aisla el equipo de la red"), ("ps / kill", "procesos"), ("systemctl", "servicios de persistencia")]

    hosts = {
        "srv-files": {"ip": "10.0.6.9", "users": {"analista": {"home": "/home/analista", "groups": "analista,soc,sudo"}},
            "fs": {
                "/home/analista/PROCEDIMIENTO.txt": "\n".join([
                    "RESPUESTA A RANSOMWARE (en orden):",
                    "1. AISLAR de la red:        aislar        (evita que cifre recursos compartidos)",
                    "2. DETENER el proceso:      kill -9 <PID>  (el que esta al 90% de CPU)",
                    "3. QUITAR persistencia:     systemctl disable sysupdate   y   rm del .service",
                    "4. CORTAR la cuenta usada:  passwd -l svc_app",
                    "5. RESTAURAR:               restaurar /respaldos/limpio-nov08",
                ]),
                "/srv/compartido/NOTA_DE_RESCATE.txt": "TUS ARCHIVOS HAN SIDO CIFRADOS (.locked)\nPara recuperarlos envia 2 BTC a la cartera bc1q...no-pagar\nTienes 48 horas o se borran. Contacto: candado@protonmail.fake",
                "/srv/compartido/nomina.xlsx.locked": "[cifrado]",
                "/srv/compartido/contratos.pdf.locked": "[cifrado]",
                SVC_PATH: "\n".join(["[Unit]", "Description=sysupdate", "[Service]", "ExecStart=/opt/.cryptor/lock.py", "[Install]", "WantedBy=multi-user.target"]),
                "/opt/.cryptor/lock.py": "# binario de cifrado del atacante",
                "/respaldos/limpio-nov08/INFO.txt": "Respaldo verificado del 8-nov, anterior al ataque. Integro.",
            },
        },
    }

    objectives = [
        {"id": "isolate", "title": "Aislar el servidor de la red", "points": 120, "cmd": r"^(aislar|netcut)\b",
         "desc": "Aisla el equipo con: aislar", "lesson": "Aislar primero evita que el ransomware llegue a otros equipos por la red compartida.",
         "hints": ["aislar"]},
        {"id": "kill", "title": "Detener el proceso que cifra", "points": 150, "requires": "isolate",
         "desc": "Encuentra el proceso al 90% de CPU y matalo con kill -9.", "lesson": "Mientras el proceso viva, sigue cifrando. kill -9 lo fuerza a terminar.",
         "hints": ["ps aux", "kill -9 6610"]},
        {"id": "persist", "title": "Eliminar la persistencia", "points": 180, "requires": "kill",
         "desc": "Un servicio de systemd lo relanza al reiniciar. Deshabilitalo y borra su archivo.",
         "lesson": "sysupdate.service apunta a /opt/.cryptor: deshabilitar + rm evita que vuelva.",
         "hints": ["systemctl disable sysupdate", "rm /etc/systemd/system/sysupdate.service"]},
        {"id": "account", "title": "Cortar la cuenta comprometida", "points": 120, "requires": "kill", "cmd": r"^passwd\s+-l\s+svc_app",
         "desc": "El proceso corria como svc_app. Bloquea esa cuenta: passwd -l svc_app",
         "lesson": "Si no revocas la cuenta, el atacante vuelve a entrar y relanza todo.", "hints": ["passwd -l svc_app"]},
        {"id": "restore", "title": "Restaurar desde un respaldo limpio", "points": 200, "requires": "persist",
         "desc": "Restaura con: restaurar /respaldos/limpio-nov08", "lesson": "Nunca se paga. Un respaldo offline y verificado, anterior al ataque, es lo que te salva.",
         "hints": ["ls /respaldos", "restaurar /respaldos/limpio-nov08"]},
    ]
    required = ["isolate", "kill", "persist", "account", "restore"]
    events = [
        {"id": "intro", "at": 1, "kind": "alert", "severity": "critical", "sender": "EDR", "title": "Cifrado masivo en curso",
         "text": "Extension .locked apareciendo en /srv/compartido. Actua YA: lee ~/PROCEDIMIENTO.txt."},
        {"id": "note", "at": 20, "unless": "kill", "kind": "alert", "severity": "high", "sender": "Usuario", "title": "Apareció una nota de rescate",
         "text": "Un usuario reporta un archivo NOTA_DE_RESCATE.txt en la carpeta compartida."},
    ]

    def _procs(self, ctx):
        return ctx.flags["procs"]

    def on_tick(self, ctx, elapsed):
        # Los archivos sanos bajan mientras el proceso siga vivo.
        if ctx.flags.get("decay") and not ctx.done("kill"):
            target = max(0, 100 - int(elapsed * 0.6))
            if target < ctx.s["meter"]:
                ctx.s["meter"] = target
                if target <= 0:
                    ctx.finish(False, self.meter["fail_text"])

    def extra_commands(self):
        return {"aislar": (self.cmd_aislar, "aisla el equipo de la red"), "netcut": (self.cmd_aislar, None),
                "ps": (self.cmd_ps, "procesos: ps aux"), "top": (self.cmd_ps, None),
                "kill": (self.cmd_kill, "termina un proceso: kill -9 <PID>"),
                "systemctl": (self.cmd_systemctl, "servicios: systemctl disable <servicio>"),
                "passwd": (self.cmd_passwd, "bloquea cuenta: passwd -l <usuario>"),
                "restaurar": (self.cmd_restaurar, "restaura un respaldo: restaurar <ruta>")}

    def cmd_aislar(self, ctx, args, raw):
        if ctx.flags["isolated"]:
            ctx.print(c("d", "El equipo ya estaba aislado.")); return
        ctx.flags["isolated"] = True
        ctx.print(c("g", "Interfaz de red desactivada. El equipo quedo aislado del resto.")); ctx.complete("isolate")

    def cmd_ps(self, ctx, args, raw):
        procs = sorted(self._procs(ctx), key=lambda p: -p["cpu"])
        ctx.print(c("w", "USER         PID %CPU %MEM COMMAND"))
        for p in procs:
            line = f"{p['user']:<10} {p['pid']:>5} {p['cpu']:>4} {p['mem']:>4} {p['cmd']}"
            ctx.print(c("r", line) if p["cpu"] > 50 else line)

    def cmd_kill(self, ctx, args, raw):
        pids = [a for a in args[1:] if a.isdigit()]
        force = any(x in args for x in ("-9", "-KILL"))
        for spid in pids:
            pid = int(spid); proc = next((p for p in self._procs(ctx) if p["pid"] == pid), None)
            if not proc:
                ctx.print(f"kill: ({pid}) - No existe el proceso"); continue
            if pid == RANSOM_PROC["pid"]:
                if not force:
                    ctx.print(c("y", "El proceso ignoro la senal. Usa kill -9.")); continue
                ctx.flags["procs"] = [p for p in self._procs(ctx) if p["pid"] != pid]
                ctx.flags["decay"] = False
                ctx.print(c("g", "Proceso de cifrado terminado. El medidor dejo de bajar.")); ctx.complete("kill")
            else:
                ctx.print(c("r", f"Mataste un servicio legitimo ({proc['cmd']})."))

    def cmd_systemctl(self, ctx, args, raw):
        if len(args) >= 3 and args[1] in ("disable", "stop", "mask") and "sysupdate" in args[2]:
            ctx.flags["service"] = False
            ctx.print(c("g", "Servicio sysupdate deshabilitado."))
            self._check_persist(ctx)
        elif len(args) >= 2 and args[1] == "list-units":
            ctx.print("sysupdate.service   loaded active running  sysupdate")
        else:
            ctx.print("Uso: systemctl disable <servicio>")

    def on_rm(self, ctx, path):
        if path == SVC_PATH:
            ctx.flags["service_file"] = False
            ctx.print(c("g", "Archivo del servicio eliminado."))
            self._check_persist(ctx)

    def allow_rm(self, ctx, path):
        return path in (SVC_PATH, "/opt/.cryptor/lock.py")

    def _check_persist(self, ctx):
        if not ctx.flags["service"] and ctx.flags.get("service_file") is False:
            ctx.complete("persist")
        elif not ctx.flags["service"]:
            ctx.print(c("y", "Servicio deshabilitado. Borra tambien su archivo .service para erradicarlo."))

    def cmd_passwd(self, ctx, args, raw):
        if "-l" in args and "svc_app" in args:
            ctx.print(c("g", "Cuenta svc_app bloqueada.")); ctx.complete("account")
        else:
            ctx.print("Uso: passwd -l <usuario>")

    def cmd_restaurar(self, ctx, args, raw):
        if len(args) < 2:
            ctx.print("Uso: restaurar <ruta-del-respaldo>"); return
        if not ctx.done("persist"):
            ctx.print(c("y", "Antes de restaurar, erradica el ransomware o volvera a cifrar el respaldo.")); return
        if "limpio-nov08" in args[1]:
            ctx.print(c("g", "Restaurando desde respaldo verificado del 8-nov... archivos recuperados.")); ctx.complete("restore")
        else:
            ctx.print(c("r", "Esa ruta no es un respaldo limpio conocido. Usa /respaldos/limpio-nov08."))

