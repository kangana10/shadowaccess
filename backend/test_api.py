import pytest
from fastapi.testclient import TestClient

import database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Use a temporary database so real data is never touched
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    from main import app
    with TestClient(app) as c:
        yield c


def login(client):
    r = client.post("/login", json={"username": "demo", "password": "demo123"})
    assert r.status_code == 200
    return r.json()["session_id"]


def send(client, sid, etype, data=None):
    return client.post("/events", json={"session_id": sid, "type": etype, "data": data or {}})


def test_wrong_password_is_rejected(client):
    r = client.post("/login", json={"username": "demo", "password": "wrong"})
    assert r.status_code == 401


def test_unknown_session_returns_404(client):
    assert send(client, "does-not-exist", "typing").status_code == 404


def test_unknown_event_type_returns_422(client):
    sid = login(client)
    assert send(client, sid, "typng").status_code == 422


def test_normal_activity_stays_normal(client):
    sid = login(client)
    r = send(client, sid, "typing", {"speed_cpm": 252, "baseline_cpm": 180})
    assert r.status_code == 200
    risk = r.json()["risk"]
    assert risk["score"] < 30
    assert risk["status"] == "Normal"
    assert risk["locked"] is False


def test_attack_locks_session_and_blocks_new_events(client):
    sid = login(client)
    r = client.post("/simulate-attack", json={"session_id": sid})
    assert r.status_code == 200
    risk = r.json()["risk"]
    assert 80 <= risk["score"] <= 95
    assert risk["status"] == "Critical"
    assert risk["locked"] is True
    assert send(client, sid, "typing").status_code == 423


def test_manual_lock(client):
    sid = login(client)
    assert client.post(f"/lock/{sid}").json()["locked"] is True
    assert client.get(f"/risk/{sid}").json()["locked"] is True


def test_alerts_after_attack(client):
    sid = login(client)
    client.post("/simulate-attack", json={"session_id": sid})
    data = client.get("/alerts", params={"session_id": sid}).json()
    assert len(data["activity"]) == 9
    assert data["alerts"][0]["status"] == "Critical"


def test_reset_clears_everything(client):
    sid = login(client)
    client.post("/simulate-attack", json={"session_id": sid})
    assert client.post("/reset-demo").json()["ok"] is True
    assert client.get(f"/risk/{sid}").status_code == 404
    data = client.get("/alerts").json()
    assert data["activity"] == []
    assert data["alerts"] == []


def test_attack_locks_five_times_in_a_row(client):
    for _ in range(5):
        sid = login(client)
        r = client.post("/simulate-attack", json={"session_id": sid})
        assert r.json()["risk"]["locked"] is True