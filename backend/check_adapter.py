import time
from risk_adapter import calculate_risk

now = time.time()

normal = [{"type": "typing", "data": {"speed_cpm": 252, "baseline_cpm": 180}, "ts": now}]

warning = [
    {"type": "typing", "data": {"speed_cpm": 400, "baseline_cpm": 180}, "ts": now},
    {"type": "ip_change", "data": {"new_ip": "1.2.3.4"}, "ts": now + 1},
]

attack = [
    {"type": "typing", "data": {"speed_cpm": 420, "baseline_cpm": 180}, "ts": now},
] + [
    {"type": "download", "data": {"filename": f"f{i}.csv"}, "ts": now + i}
    for i in range(6)
] + [
    {"type": "mouse", "data": {"straightness": 0.99}, "ts": now + 7},
    {"type": "session_change", "data": {"reason": "new device"}, "ts": now + 8},
]

for name, events in [("empty", []), ("normal", normal), ("warning", warning), ("attack", attack)]:
    r = calculate_risk(events)
    print(name, "->", r["score"], r["status"], r["reasons"])