import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from engine.risk_engine import calculate_risk as team_engine

# Tunable rules: when does an event pattern count as "yes"?
TYPING_DEVIATION = 0.5      # typing speed 50% away from baseline
RAPID_COUNT = 3             # this many downloads...
RAPID_WINDOW_SEC = 10       # ...within this many seconds
STRAIGHTNESS_LIMIT = 0.95   # mouse path this straight looks like a bot
FAILED_LIMIT = 3            # this many failed actions

# Same order as the rules in engine/risk_engine.py: (flag, signal name, points)
SIGNALS = [
    ("typing_speed_changed", "Typing change", 20),
    ("mouse_anomaly", "Mouse anomaly", 20),
    ("rapid_downloads", "Rapid downloads", 30),
    ("ip_changed", "IP/location change", 20),
    ("failed_actions", "Repeated actions", 10),
]


def events_to_flags(events):
    flags = {name: False for name, _, _ in SIGNALS}

    typing = [e for e in events if e["type"] == "typing"]
    if typing:
        d = typing[-1]["data"]
        base = d.get("baseline_cpm") or 1
        dev = abs(d.get("speed_cpm", base) - base) / base
        flags["typing_speed_changed"] = dev >= TYPING_DEVIATION

    flags["mouse_anomaly"] = any(
        e["type"] == "mouse" and e["data"].get("straightness", 0) > STRAIGHTNESS_LIMIT
        for e in events
    )

    times = sorted(e["ts"] for e in events if e["type"] == "download")
    flags["rapid_downloads"] = any(
        times[i + RAPID_COUNT - 1] - times[i] <= RAPID_WINDOW_SEC
        for i in range(len(times) - RAPID_COUNT + 1)
    )

    flags["ip_changed"] = any(e["type"] in ("ip_change", "session_change") for e in events)

    flags["failed_actions"] = sum(1 for e in events if e["type"] == "failed_action") >= FAILED_LIMIT
    return flags


def calculate_risk(events, user_id=None):
    flags = events_to_flags(events)
    flags["user_id"] = user_id
    result = team_engine(flags)

    triggered = [(sig, pts) for name, sig, pts in SIGNALS if flags[name]]
    contributions = [
        {"signal": sig, "points": pts, "reason": reason}
        for (sig, pts), reason in zip(triggered, result["reasons"])
    ]
    return {
        "score": result["risk_score"],
        "status": result["risk_level"].split(" / ")[0],
        "reasons": result["reasons"],
        "contributions": contributions,
        "recommended_action": result["recommended_action"],
    }