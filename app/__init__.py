import time

from flask import Flask, render_template
from sqlalchemy.exc import OperationalError

from .config import Config
from .extensions import db


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)

    from .api import api
    app.register_blueprint(api)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    with app.app_context():
        from . import models  # noqa: F401
        for attempt in range(30):
            try:
                db.create_all()
                if db.engine.dialect.name != "sqlite":
                    db.engine.dispose()
                break
            except OperationalError:
                if attempt == 29:
                    raise
                time.sleep(2)

    return app
