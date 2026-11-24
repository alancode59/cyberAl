"""Nivel 0 - comun a todos los roles."""
from ..engine import c
from .base import GuidedMission

HOME = "/home/novato"

class TutorialMission(GuidedMission):
    id = "tutorial"
    role = "base"
    role_name = "Academia"
    title = "Primer dia en la terminal"
    codename = "PRIMER DIA"
    level = 0
    teaches = ["triada CIA", "ls / cd / cat", "archivos ocultos", "find", "grep"]
    par_time = 600
    summary = ("Nunca has usado una terminal? Empieza aqui. Aprenderas que es la ciberseguridad y a moverte por un servidor "
               "paso a paso: ver archivos, entrar a carpetas, leerlos y buscar dentro de ellos.")
    start = {"host": "academia", "user": "novato", "cwd": HOME}
    briefing = [
        "Bienvenido a la Academia nullsector. Esto es un laboratorio: no puedes romper nada.",
        "La pantalla del centro es una TERMINAL: escribes un comando y presionas Enter.",
        "Si te pierdes escribe 'objetivos'. Si te atoras, 'pista'.",
        "Tu primer comando:  aprende ciberseguridad",
    ]
    outro = "Ya sabes ver archivos, entrar a carpetas, leer su contenido y buscar dentro de un servidor. Elige un rol y continua al nivel 1."
    help_extra = [("responder <texto>", "contesta la pregunta del objetivo")]

    hosts = {
        "academia": {"ip": "10.0.0.8", "dns": "academia.nullsector.lab",
            "users": {"novato": {"home": HOME, "groups": "novato,estudiantes"}},
            "fs": {
                HOME + "/bienvenida.txt": "Lo lograste: acabas de LEER un archivo con el comando cat.\n\nLos archivos viven en carpetas, como en tu computadora.\nAqui hay una carpeta llamada 'documentos'. Entra con:\n    cd documentos\ny mira que hay adentro con:  ls",
                HOME + "/documentos/mision.txt": "PRACTICA GUIADA\nEl administrador dejo por error un archivo importante entre muchos otros.\nSe llama 'notas.txt'. Encuentralo en todo el servidor con:\n    find / -name notas.txt\nCuando sepas donde esta, leelo con cat usando su ruta completa.",
                HOME + "/documentos/registro.txt": "linea de relleno numero 1 sin importancia\nlinea de relleno numero 2 sin importancia\nlinea de relleno numero 3 sin importancia\nlinea de relleno numero 4 sin importancia\nlinea de relleno numero 5 sin importancia\nlinea de relleno numero 6 sin importancia\nlinea de relleno numero 7 sin importancia\nlinea de relleno numero 8 sin importancia\nlinea de relleno numero 9 sin importancia\naqui va algo util: la CLAVE de acceso es ORION-7\nlinea de relleno numero 10 sin importancia\nlinea de relleno numero 11 sin importancia\nlinea de relleno numero 12 sin importancia\nlinea de relleno numero 13 sin importancia\nlinea de relleno numero 14 sin importancia\nlinea de relleno numero 15 sin importancia\nlinea de relleno numero 16 sin importancia\nlinea de relleno numero 17 sin importancia",
                HOME + "/documentos/instrucciones.txt": "Dentro de un archivo largo a veces buscas una sola linea.\nPara eso sirve grep. Este archivo tiene muchas lineas;\nbusca la que contiene la palabra CLAVE asi:\n    grep CLAVE ~/documentos/registro.txt",
                "/var/datos/archivo/notas.txt": "notas del administrador\nrecordatorio: la palabra clave del dia es COLIBRI\npendiente: revisar respaldos",
                "/etc/hostname": "academia",
            },
        },
    }

    objectives = [
        {"id": "welcome", "title": "Leer tu archivo de bienvenida", "points": 40, "read": HOME + "/bienvenida.txt",
         "desc": "Escribe:  cat bienvenida.txt", "lesson": "cat muestra el contenido de un archivo de texto.",
         "hints": ["ls para ver los archivos", "cat bienvenida.txt"]},
        {"id": "enter", "title": "Entrar a la carpeta documentos y leer la mision", "points": 60, "requires": "welcome", "read": HOME + "/documentos/mision.txt",
         "desc": "cd documentos  y luego  cat mision.txt", "lesson": "cd entra a una carpeta; cd .. regresa; cd ~ va a tu carpeta personal.",
         "hints": ["cd documentos", "ls", "cat mision.txt"]},
        {"id": "find", "title": "Encontrar notas.txt en el servidor", "points": 80, "requires": "enter", "find": "/var/datos/archivo/notas.txt",
         "desc": "find / -name notas.txt", "lesson": "find busca archivos por nombre en todo el sistema. El * es comodin: *.txt",
         "hints": ["find / -name notas.txt"]},
        {"id": "read_found", "title": "Leer notas.txt y memorizar la palabra clave", "points": 80, "requires": "find", "read": "/var/datos/archivo/notas.txt",
         "desc": "cat /var/datos/archivo/notas.txt", "lesson": "Puedes leer cualquier archivo con cat y su ruta completa.",
         "hints": ["cat /var/datos/archivo/notas.txt"]},
        {"id": "keyword", "title": "Decir la palabra clave del dia", "points": 60, "requires": "read_found",
         "question": "Cual era la palabra clave del dia?", "answer": ["colibri"],
         "desc": "responder <palabra>", "lesson": "Leer con atencion es media ciberseguridad.", "hints": ["Estaba en notas.txt", "responder COLIBRI"]},
        {"id": "grep", "title": "Usar grep para hallar la CLAVE de acceso", "points": 100, "requires": "read_found",
         "question": "Cual es la CLAVE de acceso del registro? (usa grep)", "answer": ["orion-7", "orion7"],
         "desc": "Lee ~/documentos/instrucciones.txt, luego usa grep y responde con: responder <clave>",
         "lesson": "grep PALABRA archivo encuentra solo las lineas que te interesan sin leerlo todo.",
         "hints": ["cat ~/documentos/instrucciones.txt", "grep CLAVE ~/documentos/registro.txt", "responder ORION-7"]},
    ]
    required = ["welcome", "enter", "find", "read_found", "keyword", "grep"]
    events = [
        {"id": "intro", "at": 2, "kind": "msg", "sender": "Profe Nina", "title": "Hola!",
         "text": "Sin prisa. Lee tu bienvenida con 'cat bienvenida.txt' y sigue los objetivos uno por uno."},
        {"id": "half", "after": "find", "delay": 1, "kind": "msg", "sender": "Profe Nina", "title": "Vas muy bien",
         "text": "Eso es find. Ahora lee el archivo que encontraste con cat y su ruta completa."},
    ]

