from .blue_levels import (BlueCuentasMission, BlueLogsMission, BluePhishingMission,
                          BlueRansomwareMission)
from .blueteam import BlueTeamMission
from .pentest import PentestMission
from .pentest_levels import (PentestCabecerasMission, PentestCadenaMission,
                             PentestOlvidadosMission, PentestVistazoMission)
from .qa import QAMission
from .qa_levels import (QACarreraMission, QACasoMission, QAFormulariosMission,
                        QASesionesMission)
from .red_levels import (RedLateralMission, RedMapaMission, RedPasswordsMission,
                         RedReconMission)
from .redteam import RedTeamMission
from .opsec_levels import (OpsecHuellaMission, OpsecMacMission, OpsecIpMission,
                           OpsecRastrosMission, OpsecCadenaMission)
from .tutorial import TutorialMission

# Para agregar un nivel: crea una clase (hereda de GuidedMission para niveles guiados), ponle role y level (0 tutorial … 5 muy dificil) y agregala a _ALL.
ROLES = [
    {"id": "red", "name": "Red Team", "tagline": "Ataca como el adversario",
     "desc": "Simulas a un atacante real con autorizacion: reconocimiento, acceso inicial y escalada de privilegios.",
     "skills": ["nmap", "FTP", "cracking", "SSH", "privesc"], "color": "#ff2e4d"},
    {"id": "blue", "name": "Blue Team / SOC", "tagline": "Defiende bajo fuego",
     "desc": "Detectas phishing, auditas cuentas y logs, respondes incidentes y frenas un ransomware en tiempo real.",
     "skills": ["phishing", "cuentas", "logs", "IR", "ransomware"], "color": "#2ea8ff"},
    {"id": "pentest", "name": "Pentester", "tagline": "Encuentra, demuestra, reporta",
     "desc": "Auditas aplicaciones web con contrato: codigo fuente, cabeceras, archivos expuestos, SQLi, XSS y JWT.",
     "skills": ["HTTP", "cabeceras", "gobuster", "SQLi", "JWT"], "color": "#b06bff"},
    {"id": "qa", "name": "QA / Security Tester", "tagline": "Deten el release",
     "desc": "Disenas casos de prueba y rompes APIs antes de produccion: validaciones, sesiones, IDOR y carreras.",
     "skills": ["casos", "validacion", "sesiones", "IDOR", "race"], "color": "#20e3a2"},
    {"id": "opsec", "name": "Privacidad / OPSEC", "tagline": "Protege tu identidad",
     "desc": "Aprende jugando la higiene digital que practica todo profesional etico: conoce tu huella, cambia tu MAC, oculta tu IP, limpia metadatos y arma una cadena de anonimato.",
     "skills": ["IP/MAC", "macchanger", "VPN/Tor", "metadatos", "anonimato"], "color": "#f5a623"},
]

TUTORIAL = TutorialMission()

_ALL = [
    TUTORIAL,
    RedReconMission(), RedPasswordsMission(), RedMapaMission(), RedTeamMission(), RedLateralMission(),
    BluePhishingMission(), BlueCuentasMission(), BlueLogsMission(), BlueTeamMission(), BlueRansomwareMission(),
    PentestVistazoMission(), PentestCabecerasMission(), PentestOlvidadosMission(), PentestMission(), PentestCadenaMission(),
    QACasoMission(), QAFormulariosMission(), QASesionesMission(), QAMission(), QACarreraMission(),
    OpsecHuellaMission(), OpsecMacMission(), OpsecIpMission(), OpsecRastrosMission(), OpsecCadenaMission(),
]

MISSIONS = {m.id: m for m in _ALL}

# Niveles por rol: tutorial (0) primero, luego 1→5.
LEVELS = {
    r["id"]: [TUTORIAL] + sorted((m for m in _ALL if m.role == r["id"]), key=lambda m: m.level)
    for r in ROLES
}

# Compatibilidad: el primer nivel real (1) de cada rol.
BY_ROLE = {role: next(m for m in ms if m.level == 1) for role, ms in LEVELS.items()}
