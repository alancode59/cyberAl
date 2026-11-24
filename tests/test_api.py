import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


def make_client():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SQLALCHEMY_ENGINE_OPTIONS": {}, "TESTING": True})
    return app.test_client()


def test_flow():
    cl = make_client()
    assert cl.get("/").status_code == 200
    assert cl.get("/api/roles").json["roles"][0]["mission"]["title"]
    r = cl.post("/api/auth/register", json={"alias": "ghost_01", "pin": "1234"})
    assert r.status_code == 201, r.json
    assert cl.post("/api/auth/register", json={"alias": "ghost_01", "pin": "1234"}).status_code == 409
    r = cl.post("/api/game/start", json={"mission": "qa-pagaya"})
    assert r.status_code == 200 and r.json["briefing"]
    r = cl.post("/api/game/cmd", json={"line": "cat ~/plan_pruebas.txt"})
    assert r.json["score"] == 50
    assert any(e["kind"] == "objective" for e in r.json["events"])
    assert cl.get("/api/game/tick").status_code == 200
    assert cl.get("/api/game/state").json["mission"]["id"] == "qa-pagaya"
    assert cl.get("/api/me").json["active"]["role"] == "qa"
    cl.post("/api/auth/logout")
    assert cl.get("/api/me").status_code == 401
    assert cl.post("/api/auth/login", json={"alias": "ghost_01", "pin": "9999"}).status_code == 401
    assert cl.post("/api/auth/login", json={"alias": "ghost_01", "pin": "1234"}).status_code == 200
    assert cl.get("/api/leaderboard").json["leaders"][0]["alias"] == "ghost_01"


if __name__ == "__main__":
    test_flow()
    print("API OK")
