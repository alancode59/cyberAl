"""Recorre de principio a fin cada nivel nuevo (tutorial + niveles 1,2,3,5)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.game.engine import new_state, run_line, strip_colors  # noqa: E402
from app.game.missions import LEVELS, MISSIONS  # noqa: E402

JWT_PART = None

PLAYS = {
    "tutorial": [
        "cat bienvenida.txt", "cd documentos", "cat mision.txt",
        "find / -name notas.txt", "cat /var/datos/archivo/notas.txt",
        "responder colibri", "cat ~/documentos/instrucciones.txt",
        "grep CLAVE ~/documentos/registro.txt", "responder ORION-7",
    ],
    "red-recon": [
        "cat LEEME.txt", "find / -name *.key",
        "cat /srv/datos/.respaldo_viejo/boveda.key",
        "responder /srv/datos/.respaldo_viejo/boveda.key",
    ],
    "red-passwords": [
        "cat botin/hash.txt", "crackear botin/hash.txt",
        "responder qwerty", "responder VPN",
    ],
    "red-mapa": [
        "cat LEEME.txt", "nmap -sn 10.20.0.0/24", "responder 4",
        "nmap -sV 10.20.0.20", "responder FTP",
    ],
    "red-lateral": [
        "cat /var/www/app/.env", "ls -la /home/www/.ssh",
        "find /home/www -name deploy_db",
        "ssh -i ~/.ssh/deploy_db deploy@10.30.0.20",
        "cat /home/deploy/BANDERA.txt",
    ],
    "blue-phishing": [
        "cat LEEME.txt", "cat correo/3_seguridad.eml",
        "reportar 3_seguridad.eml", "bloquear banco-meridlano.com",
        "responder contrasena",
    ],
    "blue-cuentas": [
        "cat /etc/passwd", "cat /etc/group", "responder sysbackup",
        "userdel sysbackup", "passwd -l jcarmona",
    ],
    "blue-logs": [
        "tail -n 40 /var/log/auth.log", "responder 45.33.12.9",
        "grep Accepted /var/log/auth.log", "responder admin",
        "grep Failed /var/log/auth.log", "responder 37",
    ],
    "blue-ransomware": [
        "aislar", "ps aux", "kill -9 6610",
        "systemctl disable sysupdate", "rm /etc/systemd/system/sysupdate.service",
        "passwd -l svc_app", "restaurar /respaldos/limpio-nov08",
    ],
    "pentest-vistazo": [
        "cat alcance.txt", "curl http://tienda.demo/", "responder Admin.2024",
        "curl http://tienda.demo/robots.txt", "responder /panel-interno",
    ],
    "pentest-cabeceras": [
        "cat alcance.txt", "curl -i http://app.demo/", "responder Apache",
        "responder Strict-Transport-Security",
    ],
    "pentest-olvidados": [
        "cat alcance.txt", "gobuster dir -u http://portal.demo",
        "curl http://portal.demo/.env.bak", "responder /.env.bak",
        "responder P0rtal-S3cr3t!",
    ],
    "qa-caso": [
        "cat datos.txt",
        "curl -i -d '{\"email\":\"ana@app.test\",\"password\":\"Correcta123\"}' http://app.test/api/login",
        "curl -i -d '{\"email\":\"ana@app.test\",\"password\":\"malo\"}' http://app.test/api/login",
        "responder 200",
    ],
    "qa-formularios": [
        "cat plan.txt",
        "curl -d '{\"monto\":100}' http://wallet.test/api/recarga",
        "curl -d '{\"monto\":-50}' http://wallet.test/api/recarga",
        "responder negativo",
    ],
    "qa-sesiones": [
        "cat plan.txt",
        "curl -H Authorization:Bearer tok-qa-1001 http://shop.test/api/usuarios/1001",
        "curl -H Authorization:Bearer tok-qa-1001 http://shop.test/api/usuarios/1002",
        "responder 1002",
    ],
    "qa-carrera": [
        "cat plan.txt",
        'curl -d {"cupon":"BIENVENIDA"} http://pay.test/api/cupon',
        "paralelo -n 10 http://pay.test/api/cupon",
        'curl -d {"nombre":"qa","role":"admin"} http://pay.test/api/perfil',
        "reporte enviar",
    ],
    "opsec-huella": ["cat LEEME.txt", "miip", "ip a", "responder MAC", "responder IP publica"],
    "opsec-mac": ["cat LEEME.txt", "macchanger -s eth0", "ifconfig eth0 down", "macchanger -r eth0", "ifconfig eth0 up", "macchanger -s eth0", "responder red local"],
    "opsec-ip": ["cat LEEME.txt", "miip", "tor start", "miip", "responder nodo de salida", "responder Tor"],
    "opsec-rastros": ["cat LEEME.txt", "exiftool foto.jpg", "responder GPS", "exiftool -all= foto.jpg", "history -c"],
    "opsec-cadena": ["cat PLAN.txt", "macchanger -r eth0", "tor start", "check dns", "exiftool -all= informe.jpg", "check anonimato"],
}



def _run(mid, lines):
    m = MISSIONS[mid]
    s = new_state(m)
    for ln in lines:
        run_line(m, s, ln)
    return m, s


def test_guided_levels_complete():
    failed = []
    for mid, lines in PLAYS.items():
        m, s = _run(mid, lines)
        if s["status"] != "completed":
            pend = [o["id"] for o in m.objectives if o["id"] not in s["done"]]
            failed.append(f"{mid}: {s['status']} (faltan: {pend})")
    assert not failed, "\n".join(failed)


def test_level4_missions_present():
    # Las 4 misiones originales siguen siendo el nivel 4 de su rol.
    for role, ms in LEVELS.items():
        assert ms[0].id == "tutorial"
        assert [x.level for x in ms] == [0, 1, 2, 3, 4, 5]


if __name__ == "__main__":
    for mid, lines in PLAYS.items():
        m, s = _run(mid, lines)
        tag = "OK " if s["status"] == "completed" else "XX "
        pend = "" if s["status"] == "completed" else "  faltan: " + ",".join(o["id"] for o in m.objectives if o["id"] not in s["done"])
        print(f"{tag}{mid:22} {s['status']:10} score={s['score']}{pend}")
