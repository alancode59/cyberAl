"""Servidor de desarrollo local con SQLite (sin Docker ni MySQL)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///cyberal_dev.db")

from app import create_app  # noqa: E402

app = create_app({"SQLALCHEMY_ENGINE_OPTIONS": {}})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
