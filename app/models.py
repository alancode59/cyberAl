import json
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    alias = db.Column(db.String(32), unique=True, nullable=False, index=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    xp = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    sessions = db.relationship("GameSession", backref="player", lazy="dynamic")

    def set_pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def check_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

    def to_dict(self):
        done = self.sessions.filter_by(status="completed").count()
        return {"alias": self.alias, "xp": self.xp, "missions_completed": done}


class GameSession(db.Model):
    __tablename__ = "game_sessions"

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False, index=True)
    role = db.Column(db.String(16), nullable=False)
    mission_id = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="active")
    score = db.Column(db.Integer, nullable=False, default=0)
    state_json = db.Column(db.Text().with_variant(db.Text(length=4294967295), "mysql"), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    finished_at = db.Column(db.DateTime)

    @property
    def state(self):
        return json.loads(self.state_json)

    @state.setter
    def state(self, value):
        self.state_json = json.dumps(value, ensure_ascii=False)
