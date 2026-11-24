import re
import time
from functools import wraps

from flask import Blueprint, jsonify, request, session

from .extensions import db
from .game.commands import COMPLETIONS
from .game.engine import Ctx, active_timers, new_state, process_time, prompt, run_line
from .game.missions import BY_ROLE, LEVELS, MISSIONS, ROLES
from .models import GameSession, Player, utcnow

api = Blueprint("api", __name__, url_prefix="/api")
ALIAS_RE = re.compile(r"^[A-Za-z0-9_\-]{3,24}$")


def current_player():
    pid = session.get("player_id")
    return db.session.get(Player, pid) if pid else None


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        player = current_player()
        if not player:
            return jsonify(error="No autenticado"), 401
        return fn(player, *args, **kwargs)
    return wrapper


@api.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    alias = (data.get("alias") or "").strip()
    pin = str(data.get("pin") or "")
    if not ALIAS_RE.match(alias):
        return jsonify(error="El alias debe tener 3-24 caracteres: letras, números, _ o -"), 400
    if not pin.isdigit() or not 4 <= len(pin) <= 8:
        return jsonify(error="El PIN debe tener de 4 a 8 dígitos"), 400
    if Player.query.filter_by(alias=alias).first():
        return jsonify(error="Ese alias ya existe"), 409
    player = Player(alias=alias)
    player.set_pin(pin)
    db.session.add(player)
    db.session.commit()
    session.clear()
    session["player_id"] = player.id
    return jsonify(player=player.to_dict()), 201


@api.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    player = Player.query.filter_by(alias=(data.get("alias") or "").strip()).first()
    if not player or not player.check_pin(str(data.get("pin") or "")):
        return jsonify(error="Alias o PIN incorrectos"), 401
    session.clear()
    session["player_id"] = player.id
    return jsonify(player=player.to_dict())


@api.post("/auth/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@api.get("/me")
@login_required
def me(player):
    active = _active_session(player)
    return jsonify(player=player.to_dict(), active=_summary(active) if active else None)


def _progress(player):
    """Mejor puntuación y número de victorias por misión del jugador."""
    if not player:
        return {}
    rows = (db.session.query(GameSession.mission_id, db.func.max(GameSession.score), db.func.count(GameSession.id))
            .filter(GameSession.player_id == player.id, GameSession.status == "completed")
            .group_by(GameSession.mission_id).all())
    return {mid: {"best": best, "wins": wins} for mid, best, wins in rows}


@api.get("/roles")
def roles():
    progress = _progress(current_player())
    out = []
    for r in ROLES:
        levels = []
        for m in LEVELS[r["id"]]:
            p = progress.get(m.id)
            levels.append(dict(m.public(), completed=bool(p), best=p["best"] if p else 0))
        done = sum(1 for lv in levels if lv["completed"])
        out.append(dict(r, levels=levels, mission=BY_ROLE[r["id"]].public(), completed=done, total=len(levels)))
    return jsonify(roles=out)


@api.get("/leaderboard")
def leaderboard():
    players = Player.query.order_by(Player.xp.desc()).limit(10).all()
    return jsonify(leaders=[{"alias": p.alias, "xp": p.xp} for p in players])


def _active_session(player):
    return player.sessions.filter_by(status="active").order_by(GameSession.id.desc()).first()


def _summary(gs):
    m = MISSIONS[gs.mission_id]
    return {"id": gs.id, "role": gs.role, "mission": m.public()}


def _locked_session(player):
    return (GameSession.query.filter_by(player_id=player.id, status="active")
            .order_by(GameSession.id.desc()).with_for_update().first())


def _payload(mission, state, ctx=None, output=None):
    ctx = ctx or Ctx(mission, state)
    objectives = [
        {"id": o["id"], "title": o["title"], "desc": o["desc"], "done": o["id"] in state["done"]}
        for o in mission.objectives
    ]
    meter = None
    if mission.meter:
        meter = {"label": mission.meter["label"], "value": state["meter"], "max": mission.meter["max"],
                 "direction": mission.meter["direction"], "format": mission.meter.get("format", "pct")}
    return {
        "output": output or [],
        "clear": bool(ctx.clear),
        "events": ctx.events,
        "timers": active_timers(ctx),
        "prompt": prompt(state, mission),
        "objectives": objectives,
        "score": state["score"],
        "meter": meter,
        "status": state["status"],
        "elapsed": int(time.time() - state["started"]),
    }


def _finalize(gs, state):
    gs.state = state
    gs.score = state["score"]
    if state["status"] != "active" and gs.status == "active":
        gs.status = state["status"]
        gs.finished_at = utcnow()
        if state["status"] == "completed":
            gs.player.xp += state["score"]
    db.session.commit()


@api.post("/game/start")
@login_required
def start(player):
    data = request.get_json(silent=True) or {}
    mission = MISSIONS.get(data.get("mission") or "") or BY_ROLE.get(data.get("role") or "")
    if not mission:
        return jsonify(error="Misión inválida"), 400
    role = mission.role
    for gs in player.sessions.filter_by(status="active"):
        gs.status = "abandoned"
        gs.finished_at = utcnow()
    state = new_state(mission)
    gs = GameSession(player_id=player.id, role=role, mission_id=mission.id, state_json="{}")
    gs.state = state
    db.session.add(gs)
    db.session.commit()
    out = _payload(mission, state)
    out["briefing"] = mission.briefing
    out["mission"] = mission.public()
    out["completions"] = COMPLETIONS + list(mission.commands().keys())
    return jsonify(out)


@api.get("/game/state")
@login_required
def game_state(player):
    gs = _active_session(player)
    if not gs:
        return jsonify(error="Sin misión activa"), 404
    mission = MISSIONS[gs.mission_id]
    state = gs.state
    out = _payload(mission, state)
    out["briefing"] = mission.briefing
    out["mission"] = mission.public()
    out["completions"] = COMPLETIONS + list(mission.commands().keys())
    out["history"] = state["history"]
    return jsonify(out)


@api.post("/game/cmd")
@login_required
def game_cmd(player):
    data = request.get_json(silent=True) or {}
    line = str(data.get("line", ""))[:500]
    gs = _locked_session(player)
    if not gs:
        return jsonify(error="Sin misión activa"), 404
    mission = MISSIONS[gs.mission_id]
    state = gs.state
    ctx = run_line(mission, state, line)
    _finalize(gs, state)
    return jsonify(_payload(mission, state, ctx, ctx.out))


@api.get("/game/tick")
@login_required
def game_tick(player):
    gs = _locked_session(player)
    if not gs:
        db.session.rollback()
        return jsonify(error="Sin misión activa"), 404
    mission = MISSIONS[gs.mission_id]
    state = gs.state
    ctx = Ctx(mission, state)
    process_time(ctx)
    ctx.out.extend(ctx.notes)
    _finalize(gs, state)
    return jsonify(_payload(mission, state, ctx, ctx.out))


@api.post("/game/abandon")
@login_required
def abandon(player):
    gs = _active_session(player)
    if gs:
        gs.status = "abandoned"
        gs.finished_at = utcnow()
        db.session.commit()
    return jsonify(ok=True)
