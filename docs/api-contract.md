# ShadowAccess API Contract

Base URL (when running locally): `http://127.0.0.1:8000`
Interactive docs: `http://127.0.0.1:8000/docs`
All timestamps (`ts`) are in **seconds** (multiply by 1000 in JavaScript).

## Demo logins
| username | password |
|---|---|
| demo | demo123 |
| admin | admin123 |

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/login` | Log in, returns `session_id` |
| POST | `/events` | Send one activity event, returns the fresh risk |
| GET | `/risk/{session_id}` | Current score, status, reasons |
| GET | `/alerts?session_id=...` | Recent activity and alerts |
| POST | `/lock/{session_id}` | Lock a session manually |
| POST | `/simulate-attack` | Inject the fake attack events |
| POST | `/reset-demo` | Clear all sessions, events and alerts |

## POST /login
Send: `{"username": "demo", "password": "demo123"}`
Get: `{"session_id": "...", "username": "demo"}`
Wrong password: HTTP 401.

## POST /events
Send: `{"session_id": "...", "type": "typing", "data": {...}}`

| type | data keys |
|---|---|
| typing | `speed_cpm`, `baseline_cpm` (numbers) |
| mouse | `speed_px_s`, `straightness` (0 to 1) |
| download | `filename`, `size_kb` |
| ip_change | `old_ip`, `new_ip` |
| session_change | `reason` |
| action | `name`, `target` (normal activity, no risk) |
| failed_action | `action` |

Get: `{"ok": true, "risk": {...same as GET /risk...}}`
Errors: 404 unknown session, 422 unknown event type, **423 session is locked**.

## GET /risk/{session_id}
```json
{
  "score": 90,
  "status": "Critical",
  "reasons": ["Typing speed changed significantly", "..."],
  "contributions": [
    {"signal": "Rapid downloads", "points": 30, "reason": "..."}
  ],
  "recommended_action": "Block Session",
  "locked": true,
  "session_id": "..."
}
```
- `status` is exactly `Normal`, `Warning` or `Critical`.
- Bands: 0-29 Normal, 30-69 Warning, 70-100 Critical (session locks automatically).
- `contributions` feeds the dashboard bar chart.

## GET /alerts
Optional `?session_id=...`. Newest first.
```json
{
  "activity": [{"session_id": "...", "type": "typing", "data": {}, "ts": 1790925518.03}],
  "alerts": [{"session_id": "...", "score": 70, "status": "Critical", "reasons": ["..."], "ts": 1790925964.1}]
}
```

## POST /simulate-attack
Send: `{"session_id": "..."}`
Adds typing, rapid downloads, straight mouse movement and a session change.
Get: `{"ok": true, "injected": 9, "risk": {...}}` (score about 90, locked).

## Lock behaviour
When the score reaches 70 the session locks automatically. A locked session
returns **HTTP 423** on `/events` and `"locked": true` on `/risk`.
The frontend should show the lock screen when either happens.