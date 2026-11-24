import os


def _db_url():
    """URL de la base, normalizada para que funcione en local (MySQL/SQLite) y en Render (Postgres)."""
    url = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://cyberal:cyberal@db:3306/cyberal?charset=utf8mb4",
    )
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-cambia-esto")
    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    JSON_AS_ASCII = False
