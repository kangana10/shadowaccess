## Backend (FastAPI + SQLite)

Requires Python 3.11 or newer and Git.

```
git clone https://github.com/kangana10/shadowaccess.git
cd shadowaccess/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

On Mac or Linux, activate with `source venv/bin/activate` instead.

Open http://127.0.0.1:8000/docs to try every endpoint.
The full list of endpoints and event formats is in `docs/api-contract.md`.

Demo logins: `demo` / `demo123` and `admin` / `admin123`.

To wipe all sessions, events and alerts between demo runs, call `POST /reset-demo`.

**Note:** ShadowAccess is a controlled hackathon prototype. It demonstrates detecting
suspicious behavior and containing a simulated takeover. It is not a production
security system.