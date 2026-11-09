# Sentry demo (Flask + Sentry Python SDK)

A tiny "order service" that sends errors, a message and performance traces to Sentry.

## 1. Sentry side
1. Sign up at https://sentry.io/signup
2. Create a project: platform **Flask**
3. Copy the **DSN** it shows you (Settings > Projects > your project > Client Keys (DSN))

## 2. Run the app

**Windows (PowerShell)**
```powershell
cd sentry-demo
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SENTRY_DSN = "paste-your-dsn-here"
python app.py
```

**macOS / Linux**
```bash
cd sentry-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SENTRY_DSN="paste-your-dsn-here"
python app.py
```

## 3. Trigger events
Open http://127.0.0.1:5000 and click each link:

| Route | What Sentry receives |
|---|---|
| /error | Average price calculation; an empty order returns HTTP 400 with a descriptive error message |
| /handled | Caught `KeyError` with breadcrumb + `order` context (Issues) |
| /message | Warning-level message (Issues) |
| /checkout | Transaction with 3 custom spans (Performance / Traces) |

Every event is tagged `service: order-service`, user `demo-user-42`, release `sentry-demo@1.0.0`.

Not seeing anything? Run with `SENTRY_DEBUG=1` (PowerShell: `$env:SENTRY_DEBUG="1"`) to print what the SDK is doing.

## 4. Org URL
Your org URL is in the browser address bar: `https://<your-org-slug>.sentry.io`
