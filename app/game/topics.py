"""Mini lecciones accesibles con `aprende <tema>`."""

TOPICS = {
    "etica": {
        "title": "Hacking ético y alcance",
        "body": [
            "Un hacker ético SOLO prueba sistemas con autorización escrita.",
            "El documento de 'Reglas de Enfrentamiento' (RoE) define:",
            "  • Qué IPs/dominios están dentro del alcance (scope).",
            "  • Qué técnicas están prohibidas (DoS, ingeniería social, borrar datos...).",
            "  • Ventanas de tiempo y contactos de emergencia.",
            "Salirte del alcance es un delito aunque tu intención sea buena.",
        ],
    },
    "nmap": {
        "title": "Reconocimiento con nmap",
        "body": [
            "nmap descubre hosts y servicios en una red.",
            "  nmap -sn 10.0.0.0/24    descubrimiento de hosts (ping sweep, sin puertos)",
            "  nmap -sV 10.0.0.5       detecta versiones de servicios",
            "  nmap -p- 10.0.0.5       escanea los 65535 puertos",
            "  nmap -A 10.0.0.5        agresivo: versiones, scripts, SO (MUY ruidoso)",
            "  -T0..-T5                velocidad; más rápido = más detectable por un IDS",
            "Defensa: un IDS (Suricata/Snort) detecta escaneos por volumen de conexiones.",
        ],
    },
    "ftp": {
        "title": "FTP anónimo",
        "body": [
            "FTP transmite todo en texto plano (usuario y contraseña incluidos).",
            "Muchos servidores permiten login 'anonymous' por error de configuración.",
            "Si el FTP anónimo expone respaldos o notas internas, es un hallazgo grave.",
            "Defensa: deshabilitar anonymous_enable en vsftpd y usar SFTP.",
        ],
    },
    "hash": {
        "title": "Hashes y cracking de contraseñas",
        "body": [
            "Un hash es una huella irreversible de un dato: md5('hola') = 4d186321...",
            "No se 'descifra': se prueban palabras candidatas hasta que un hash coincide.",
            "  john --wordlist=rockyou.txt hash.txt",
            "  hashcat -m 0 hash.txt rockyou.txt     (-m 0 = MD5)",
            "MD5 y SHA1 sin sal son débiles. Defensa: bcrypt/argon2 + contraseñas largas.",
        ],
    },
    "ssh": {
        "title": "SSH",
        "body": [
            "SSH da una shell remota cifrada:  ssh usuario@host",
            "Ataques comunes: fuerza bruta y reutilización de contraseñas filtradas.",
            "Defensa: llaves en vez de contraseñas, fail2ban, deshabilitar root login,",
            "MFA y monitorear /var/log/auth.log.",
        ],
    },
    "privesc": {
        "title": "Escalada de privilegios en Linux",
        "body": [
            "Tras entrar como usuario normal, el atacante busca convertirse en root.",
            "Revisiones clásicas:",
            "  sudo -l                         ¿qué puedo ejecutar como root?",
            "  find / -perm -4000              binarios SUID",
            "  cat /etc/crontab                tareas programadas inseguras",
            "Si 'find' corre con sudo, '-exec' lanza comandos como root (ver GTFOBins).",
            "Defensa: principio de mínimo privilegio en sudoers.",
        ],
    },
    "siem": {
        "title": "SIEM y análisis de logs",
        "body": [
            "Un SIEM centraliza logs y genera alertas por reglas de correlación.",
            "Logs clave en Linux:",
            "  /var/log/auth.log            logins SSH, sudo",
            "  /var/log/apache2/access.log  peticiones web",
            "  /var/log/syslog              eventos del sistema",
            "Flujo de respuesta (NIST): Preparar → Detectar/Analizar → Contener →",
            "Erradicar → Recuperar → Lecciones aprendidas.",
        ],
    },
    "firewall": {
        "title": "Firewall con iptables",
        "body": [
            "Bloquear una IP de origen:",
            "  iptables -A INPUT -s 203.0.113.5 -j DROP",
            "Listar reglas:  iptables -L",
            "Contener rápido es clave, pero bloquear IPs es temporal: el atacante",
            "puede rotar de IP. Combina con fail2ban y reglas de geobloqueo.",
        ],
    },
    "malware": {
        "title": "Procesos maliciosos y persistencia",
        "body": [
            "Un cryptominer suele delatarse por CPU al 100% y nombres que imitan",
            "procesos del kernel (kworkerds, kthreadd2...).",
            "  ps aux            listar procesos      kill -9 PID   terminar proceso",
            "Si no eliminas la PERSISTENCIA (crontab, systemd, .bashrc) vuelve a nacer.",
            "  crontab -l        ver tareas del usuario   crontab -r   borrarlas",
        ],
    },
    "webshell": {
        "title": "Webshells",
        "body": [
            "Una webshell es un script (ej. PHP) subido al servidor que ejecuta",
            "comandos recibidos por HTTP. Suele entrar por un formulario de carga",
            "que no valida el tipo de archivo.",
            "Detección: peticiones POST a archivos raros en /uploads, parámetros 'cmd='.",
            "Respuesta: aislar, eliminar, bloquear origen y corregir la carga.",
        ],
    },
    "sqli": {
        "title": "Inyección SQL (OWASP A03)",
        "body": [
            "Ocurre cuando la entrada del usuario se concatena en una consulta SQL:",
            "  SELECT * FROM productos WHERE id = '$id'",
            "Con id=1' la comilla rompe la consulta → error SQL visible = indicio.",
            "sqlmap automatiza la detección y extracción:  sqlmap -u 'URL?id=1' --dbs",
            "Defensa: consultas parametrizadas (prepared statements), nunca concatenar.",
        ],
    },
    "xss": {
        "title": "Cross-Site Scripting (XSS)",
        "body": [
            "XSS reflejado: el servidor devuelve tu entrada sin escapar dentro del HTML.",
            "  /buscar?q=<script>alert(1)</script>",
            "Si el payload aparece tal cual en la respuesta, se ejecuta en el navegador",
            "de la víctima: robo de sesión, phishing, etc.",
            "Defensa: escapar salida según contexto, Content-Security-Policy, HttpOnly.",
        ],
    },
    "fuzzing": {
        "title": "Descubrimiento de contenido (fuzzing de rutas)",
        "body": [
            "Herramientas como gobuster/ffuf prueban miles de rutas de un diccionario:",
            "  gobuster dir -u http://objetivo -w common.txt",
            "Encuentran paneles /admin, respaldos /backup, repos /.git expuestos...",
            "Un .git o un .bak expuesto suele filtrar código fuente y credenciales.",
        ],
    },
    "cvss": {
        "title": "Severidad con CVSS",
        "body": [
            "CVSS puntúa vulnerabilidades de 0.0 a 10.0:",
            "  0.1-3.9 baja   4.0-6.9 media   7.0-8.9 alta   9.0-10 crítica",
            "Considera vector (red/local), complejidad, privilegios requeridos,",
            "interacción del usuario e impacto en Confidencialidad/Integridad/Disponibilidad.",
            "SQLi sin autenticación que vuelca la BD suele ser crítica (9.8).",
        ],
    },
    "idor": {
        "title": "IDOR / Broken Object Level Authorization (OWASP API1)",
        "body": [
            "La API confía en el ID que mandas sin verificar que el objeto sea tuyo:",
            "  GET /api/v1/users/1001  → tu perfil",
            "  GET /api/v1/users/1002  → ¡el perfil de otra persona!",
            "Defensa: validar en el servidor que el recurso pertenece al usuario del token.",
        ],
    },
    "ratelimit": {
        "title": "Rate limiting (OWASP API4)",
        "body": [
            "Sin límite de peticiones, un atacante puede probar millones de contraseñas",
            "o abusar de recursos. Lo correcto: responder 429 Too Many Requests,",
            "bloqueos progresivos y CAPTCHA tras varios fallos.",
        ],
    },
    "validacion": {
        "title": "Validación de entradas y lógica de negocio",
        "body": [
            "Nunca confíes en el cliente: valida tipo, rango y formato en el servidor.",
            "Ejemplo clásico: transferir un monto NEGATIVO y que el sistema lo acepte,",
            "invirtiendo el flujo del dinero.",
            "Defensa: esquemas estrictos (pydantic, marshmallow), reglas de negocio.",
        ],
    },
    "errores": {
        "title": "Manejo de errores y fuga de información",
        "body": [
            "Un stack trace en producción revela rutas, versiones, consultas y a veces",
            "credenciales. Responde con mensajes genéricos y registra el detalle sólo",
            "en logs internos. Desactiva el modo DEBUG en producción.",
        ],
    },
}

TOPICS.update({
    "ciberseguridad": {
        "title": "¿Qué es la ciberseguridad?",
        "body": [
            "Es proteger la información y los sistemas que la guardan. Se resume en la tríada CIA:",
            "  C  Confidencialidad   sólo quien debe puede LEER la información",
            "  I  Integridad         nadie puede CAMBIARLA sin permiso",
            "  D  Disponibilidad     está ahí cuando se NECESITA (A = Availability)",
            "Cada ataque rompe al menos una: robar datos rompe C, alterar saldos rompe I,",
            "tirar un sitio rompe D. Cada rol de este juego protege la tríada a su manera.",
        ],
    },
    "terminal": {
        "title": "La terminal en 1 minuto",
        "body": [
            "  whoami            ¿quién soy?          pwd     ¿dónde estoy?",
            "  ls                ver archivos         ls -a   ver también los ocultos (.archivo)",
            "  cd carpeta        entrar a una carpeta cd ..   subir un nivel   cd ~  ir a tu casa",
            "  cat archivo       leer un archivo",
            "  find / -name x    buscar archivos por nombre (* es comodín: *.key)",
            "  grep texto arch   buscar un texto dentro de un archivo",
            "  cmd1 | cmd2       la tubería pasa la salida de cmd1 a cmd2",
            "TAB autocompleta, ↑/↓ repite comandos anteriores.",
        ],
    },
    "cifrado": {
        "title": "Cifrado, codificación y hashes",
        "body": [
            "  Codificar (base64)   cambia el formato. Cualquiera lo revierte. NO protege nada.",
            "  Cifrar (AES, RSA)    sólo quien tiene la LLAVE puede leerlo. Protege confidencialidad.",
            "  Hash (SHA-256, MD5)  huella de una sola vía. Sirve para guardar contraseñas e integridad.",
            "Una llave de cifrado (.key) es tan valiosa como los datos que protege:",
            "si la dejas junto a los datos, el cifrado no sirve.",
        ],
    },
    "phishing": {
        "title": "Cómo reconocer phishing",
        "body": [
            "  1. Remitente: ¿el dominio es EXACTO? banco-meridlano.com ≠ banco-meridiano.com",
            "  2. Urgencia o miedo: 'tu cuenta se bloqueará en 2 horas'",
            "  3. Enlaces: el texto dice una cosa y la URL real va a otro dominio",
            "  4. Te pide contraseñas, códigos o datos que la empresa ya tiene",
            "  5. Adjuntos inesperados: .zip, .html, .docm, .exe",
            "Defensa: SPF/DKIM/DMARC en el correo, MFA y reportar al SOC en vez de borrar.",
        ],
    },
    "cuentas": {
        "title": "Gestión de cuentas en Linux",
        "body": [
            "  /etc/passwd   usuario:x:UID:GID:descripción:home:shell   (UID 0 = root)",
            "  /etc/group    grupo:x:GID:miembros   (estar en 'sudo' = poder ser root)",
            "  last          historial de inicios de sesión (quién, desde qué IP, cuándo)",
            "  passwd -l u   bloquea la cuenta     passwd -e u   obliga a cambiar la contraseña",
            "  userdel u     elimina la cuenta     gpasswd -d u grupo   saca al usuario del grupo",
            "Principio de mínimo privilegio: cada cuenta con sólo lo que necesita.",
        ],
    },
    "logs": {
        "title": "Análisis de logs",
        "body": [
            "Los logs son la memoria del sistema. Preguntas clave: ¿quién? ¿desde dónde? ¿cuándo? ¿qué hizo?",
            "  grep \"Failed\" auth.log | wc -l                   cuántos intentos fallidos",
            "  awk '{print $1}' access.log | sort | uniq -c | sort -nr   IPs que más piden",
            "  grep \"Accepted\" auth.log                         logins que SÍ funcionaron",
            "Un intento fallido es ruido; mil fallidos y luego un 'Accepted' es un incidente.",
        ],
    },
    "ransomware": {
        "title": "Respuesta a ransomware",
        "body": [
            "Orden de respuesta: AISLAR → DETENER → ERRADICAR → RECUPERAR → APRENDER.",
            "  1. Aísla el equipo de la red (EDR) para que no cifre más recursos compartidos.",
            "  2. Detén el proceso que cifra.  3. Quita su persistencia (servicios, cron).",
            "  4. Revoca la cuenta con la que entró.",
            "  5. Restaura desde un respaldo LIMPIO (anterior al ataque) y verificado.",
            "Pagar no garantiza nada y financia al crimen. Los respaldos offline te salvan.",
        ],
    },
    "http": {
        "title": "HTTP básico",
        "body": [
            "Navegador → petición (GET /ruta) → servidor → respuesta (código + cabeceras + cuerpo).",
            "  200 OK   301 redirección   401 sin autenticar   403 prohibido   404 no existe   500 error",
            "  curl http://sitio/            descarga el HTML (lo que ves con 'ver código fuente')",
            "  curl -i http://sitio/         también muestra las cabeceras",
            "  /robots.txt  le dice a los buscadores qué NO indexar... y a ti dónde mirar.",
            "Los comentarios <!-- --> del HTML los ve cualquiera.",
        ],
    },
    "cabeceras": {
        "title": "Cabeceras de seguridad y cookies",
        "body": [
            "  Strict-Transport-Security   obliga a usar HTTPS",
            "  Content-Security-Policy     limita de dónde se carga JavaScript (frena XSS)",
            "  X-Frame-Options             evita que te metan en un iframe (clickjacking)",
            "  Server / X-Powered-By       revelan versiones: mejor ocultarlas",
            "Cookies de sesión:  HttpOnly (JS no la lee)  Secure (sólo HTTPS)  SameSite (CSRF)",
        ],
    },
    "jwt": {
        "title": "JSON Web Tokens (JWT)",
        "body": [
            "Formato: cabecera.payload.firma — las dos primeras partes son base64, NO cifradas.",
            "  echo <payload> | base64 -d    cualquiera puede leer lo que dice el token",
            "La firma (HS256) usa un secreto. Si el secreto es débil, se adivina y se",
            "pueden fabricar tokens con role=admin. Defensa: secreto largo y aleatorio,",
            "validar 'alg', expiración corta y nunca confiar en datos del token sin verificar.",
        ],
    },
    "ssrf": {
        "title": "SSRF (Server-Side Request Forgery)",
        "body": [
            "La app descarga una URL que tú le das (vista previa, webhooks, importar imagen).",
            "Si no valida, puedes hacer que el SERVIDOR pida direcciones internas:",
            "  http://127.0.0.1:8080/   http://169.254.169.254/  (metadatos de la nube → credenciales)",
            "Defensa: lista blanca de dominios, bloquear IPs privadas y IMDSv2 en la nube.",
        ],
    },
    "casos": {
        "title": "Casos de prueba",
        "body": [
            "Un caso de prueba tiene: ENTRADA → RESULTADO ESPERADO → RESULTADO OBTENIDO.",
            "Si esperado ≠ obtenido, es un bug. Prueba siempre:",
            "  • el camino feliz (datos correctos)     • campos vacíos",
            "  • valores límite (0, -1, máximo+1)      • tipos incorrectos (texto donde va número)",
            "  • textos muy largos y caracteres especiales (<script>, ' \" ;)",
        ],
    },
    "sesiones": {
        "title": "Sesiones y autenticación",
        "body": [
            "Al cerrar sesión, el servidor debe INVALIDAR el token (no sólo borrarlo del navegador).",
            "Los tokens de recuperación de contraseña deben ser aleatorios y de un solo uso.",
            "Cada endpoint que modifica datos debe exigir autenticación Y autorización.",
            "Bloqueo o retardo tras varios intentos fallidos frena la fuerza bruta.",
        ],
    },
    "race": {
        "title": "Condiciones de carrera y mass assignment",
        "body": [
            "Race condition: dos peticiones simultáneas pasan la misma validación",
            "('¿cupón ya usado?' → no, no) antes de que alguna guarde el cambio.",
            "  Defensa: transacciones, bloqueos (SELECT ... FOR UPDATE), restricciones únicas.",
            "Mass assignment: la API copia TODO el JSON al modelo, incluido \"role\":\"admin\".",
            "  Defensa: lista explícita de campos permitidos.",
        ],
    },
    "pivoting": {
        "title": "Movimiento lateral",
        "body": [
            "Tras el acceso inicial, el atacante busca credenciales para saltar a otros equipos:",
            "  archivos de configuración (.env, config.php), historiales (.bash_history),",
            "  llaves SSH (id_rsa) y contraseñas reutilizadas.",
            "  ssh -i llave usuario@host   entra con una llave privada en vez de contraseña",
            "Defensa: segmentar la red, secretos en un vault, no reutilizar contraseñas.",
        ],
    },
})
