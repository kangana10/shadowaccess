import json
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import get_conn, init_db
from risk_adapter import calculate_risk

LOCK_THRESHOLD = 70


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="ShadowAccess API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "ShadowAccess API is running"}

class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(body: LoginIn):
    with get_conn() as c:
        user = c.execute(
            "SELECT 1 FROM users WHERE username=? AND password=?",
            (body.username, body.password),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        session_id = str(uuid.uuid4())
        c.execute(
            "INSERT INTO sessions (id, username, created_at) VALUES (?, ?, ?)",
            (session_id, body.username, time.time()),
        )
    return {"session_id": session_id, "username": body.username}

ALLOWED_EVENT_TYPES = {
    "typing", "mouse", "download",
    "ip_change", "session_change",
    "action", "failed_action",
}


class EventIn(BaseModel):
    session_id: str
    type: str
    data: dict = {}


def get_session(session_id: str):
    with get_conn() as c:
        row = c.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


def add_event(session_id: str, event_type: str, data: dict):
    with get_conn() as c:
        c.execute(
            "INSERT INTO events (session_id, type, data, ts) VALUES (?, ?, ?, ?)",
            (session_id, event_type, json.dumps(data), time.time()),
        )


@app.post("/events")
def post_event(body: EventIn):
    if body.type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=422, detail=f"Unknown event type: {body.type}")
    session = get_session(body.session_id)
    if session["locked"]:
        raise HTTPException(status_code=423, detail="Session is locked")
    add_event(body.session_id, body.type, body.data)
    return {"ok": True, "risk": evaluate(body.session_id)}

def load_events(session_id: str):
    with get_conn() as c:
        rows = c.execute(
            "SELECT type, data, ts FROM events WHERE session_id=? ORDER BY id DESC LIMIT 200",
            (session_id,),
        ).fetchall()
    return [
        {"type": r["type"], "data": json.loads(r["data"]), "ts": r["ts"]}
        for r in reversed(rows)
    ]


def lock_session(session_id: str):
    with get_conn() as c:
        c.execute(
            "UPDATE sessions SET locked=1, locked_at=? WHERE id=?",
            (time.time(), session_id),
        )


def save_alert_if_new(session_id: str, result: dict):
    if result["status"] == "Normal":
        return
    with get_conn() as c:
        last = c.execute(
            "SELECT status FROM alerts WHERE session_id=? ORDER BY id DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        if last is None or last["status"] != result["status"]:
            c.execute(
                "INSERT INTO alerts (session_id, score, status, reasons, ts) VALUES (?, ?, ?, ?, ?)",
                (session_id, result["score"], result["status"],
                 json.dumps(result["reasons"]), time.time()),
            )


def evaluate(session_id: str):
    session = get_session(session_id)
    result = calculate_risk(load_events(session_id), user_id=session["username"])
    locked = bool(session["locked"])
    if result["score"] >= LOCK_THRESHOLD and not locked:
        lock_session(session_id)
        locked = True
    save_alert_if_new(session_id, result)
    return {**result, "locked": locked, "session_id": session_id}


@app.get("/risk/{session_id}")
def get_risk(session_id: str):
    return evaluate(session_id)

@app.get("/alerts")
def get_alerts(session_id: Optional[str] = None):
    with get_conn() as c:
        if session_id:
            events = c.execute(
                "SELECT session_id, type, data, ts FROM events WHERE session_id=? ORDER BY id DESC LIMIT 30",
                (session_id,),
            ).fetchall()
            alerts = c.execute(
                "SELECT session_id, score, status, reasons, ts FROM alerts WHERE session_id=? ORDER BY id DESC LIMIT 20",
                (session_id,),
            ).fetchall()
        else:
            events = c.execute(
                "SELECT session_id, type, data, ts FROM events ORDER BY id DESC LIMIT 30"
            ).fetchall()
            alerts = c.execute(
                "SELECT session_id, score, status, reasons, ts FROM alerts ORDER BY id DESC LIMIT 20"
            ).fetchall()
    return {
        "activity": [
            {"session_id": r["session_id"], "type": r["type"],
             "data": json.loads(r["data"]), "ts": r["ts"]}
            for r in events
        ],
        "alerts": [
            {"session_id": r["session_id"], "score": r["score"], "status": r["status"],
             "reasons": json.loads(r["reasons"]), "ts": r["ts"]}
            for r in alerts
        ],
    }

@app.post("/lock/{session_id}")
def lock(session_id: str):
    get_session(session_id)
    lock_session(session_id)
    return {"locked": True, "session_id": session_id}


class SimIn(BaseModel):
    session_id: str


@app.post("/simulate-attack")
def simulate_attack(body: SimIn):
    session = get_session(body.session_id)
    if session["locked"]:
        raise HTTPException(status_code=423, detail="Session is locked")
    sid = body.session_id
    add_event(sid, "typing", {"speed_cpm": 420, "baseline_cpm": 180})
    for i in range(6):
        add_event(sid, "download", {"filename": f"customers_{i}.csv", "size_kb": 2048})
    add_event(sid, "mouse", {"speed_px_s": 5200, "straightness": 0.99})
    add_event(sid, "session_change", {"reason": "new device"})
    return {"ok": True, "injected": 9, "risk": evaluate(sid)}


@app.post("/reset-demo")
def reset_demo():
    with get_conn() as c:
        c.executescript("DELETE FROM events; DELETE FROM alerts; DELETE FROM sessions;")
    return {"ok": True}