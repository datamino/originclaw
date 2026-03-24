#!/usr/bin/env python3
"""
OriginClaw Monitor — Email Alert via Resend API
Free tier: 3,000 emails/month
Sign up: https://resend.com
"""
import urllib.request, urllib.parse, json, time, os

DEVELOPER_EMAIL = "p229279@pwr.nu.edu.pk"
FROM_EMAIL = "OriginClaw Monitor <onboarding@resend.dev>"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
STRIKE_WAIT = 30
_strikes: dict = {}

def _html_alert(client_name: str, component: str, severity: str, detail: str) -> str:
    color = {"critical": "#dc2626", "warning": "#d97706", "offline": "#6b7280"}.get(severity, "#374151")
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f9fafb;font-family:Inter,sans-serif;">
<div style="max-width:520px;margin:40px auto;background:white;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden;">
  <div style="background:#111827;padding:20px 24px;display:flex;align-items:center;gap:10px;">
    <span style="color:white;font-size:16px;font-weight:700;">⬡ OriginClaw Monitor</span>
  </div>
  <div style="padding:28px 24px;">
    <div style="display:inline-block;background:{color}18;border:1px solid {color}44;border-radius:20px;padding:4px 14px;margin-bottom:18px;">
      <span style="color:{color};font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">{severity.upper()}</span>
    </div>
    <h2 style="margin:0 0 4px;color:#111827;font-size:22px;font-weight:700;letter-spacing:-0.02em;">{component}</h2>
    <p style="margin:0 0 24px;color:#6b7280;font-size:14px;">{client_name}</p>
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:16px 18px;margin-bottom:24px;">
      <code style="color:#374151;font-size:13px;font-family:monospace;">{detail}</code>
    </div>
    <p style="color:#9ca3af;font-size:12px;margin:0;border-top:1px solid #f3f4f6;padding-top:16px;">
      Confirmed after 3 consecutive checks &nbsp;·&nbsp; {ts}
    </p>
  </div>
</div>
</body></html>"""

def _html_recovery(client_name: str, component: str, downtime_min: int) -> str:
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f9fafb;font-family:Inter,sans-serif;">
<div style="max-width:520px;margin:40px auto;background:white;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden;">
  <div style="background:#111827;padding:20px 24px;">
    <span style="color:white;font-size:16px;font-weight:700;">⬡ OriginClaw Monitor</span>
  </div>
  <div style="padding:28px 24px;">
    <div style="display:inline-block;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:20px;padding:4px 14px;margin-bottom:18px;">
      <span style="color:#15803d;font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;">RECOVERED</span>
    </div>
    <h2 style="margin:0 0 4px;color:#111827;font-size:22px;font-weight:700;">{component}</h2>
    <p style="margin:0 0 8px;color:#6b7280;font-size:14px;">{client_name}</p>
    <p style="margin:0 0 24px;color:#374151;font-size:14px;">Downtime: <strong>{downtime_min} minutes</strong></p>
    <p style="color:#9ca3af;font-size:12px;margin:0;border-top:1px solid #f3f4f6;padding-top:16px;">{ts}</p>
  </div>
</div>
</body></html>"""

def send_email(subject: str, html_body: str) -> bool:
    if not RESEND_API_KEY:
        # Log to file until API key is configured
        os.makedirs(os.path.expanduser("~/.originclaw"), exist_ok=True)
        log_path = os.path.expanduser("~/.originclaw/pending_alerts.json")
        alerts = []
        if os.path.exists(log_path):
            with open(log_path) as f:
                alerts = json.load(f)
        alerts.append({"subject": subject, "to": DEVELOPER_EMAIL, "at": time.time(), "status": "pending_smtp"})
        with open(log_path, "w") as f:
            json.dump(alerts, f, indent=2)
        print(f"[email] No RESEND_API_KEY — logged: {subject} → {DEVELOPER_EMAIL}")
        return False

    import subprocess as _sp
    _d = json.dumps({"from": FROM_EMAIL, "to": [DEVELOPER_EMAIL], "subject": subject, "html": html_body})
    _r = _sp.run(["curl","-s","-X","POST","https://api.resend.com/emails","-H",f"Authorization: Bearer {RESEND_API_KEY}","-H","Content-Type: application/json","-d",_d], capture_output=True, text=True, timeout=15)
    try:
        _res = json.loads(_r.stdout)
        if "id" in _res:
            print(f"[email] Sent to {DEVELOPER_EMAIL} (id: {_res[chr(105)+chr(100)]})") 
            return True
        print(f"[email] Failed: {_res}")
        return False
    except Exception as _e:
        print(f"[email] Error: {_e} raw: {_r.stdout[:100]}")
        return False
def check_and_alert(client_name: str, component: str, status: str, detail: str, check_fn) -> bool:
    key = f"{client_name}:{component}"

    if status in ("warning", "critical", "offline"):
        if key not in _strikes:
            _strikes[key] = {"count": 1, "first_seen": time.time(), "severity": status}
            print(f"[strike 1/3] {component} — waiting {STRIKE_WAIT}s")
            time.sleep(STRIKE_WAIT)

            new_status, new_detail = check_fn()
            if new_status not in ("warning", "critical", "offline"):
                del _strikes[key]
                print(f"[cleared] {component} recovered after strike 1")
                return False

            _strikes[key]["count"] = 2
            print(f"[strike 2/3] {component} — still broken, waiting {STRIKE_WAIT}s")
            time.sleep(STRIKE_WAIT)

            new_status, new_detail = check_fn()
            if new_status not in ("warning", "critical", "offline"):
                del _strikes[key]
                print(f"[cleared] {component} recovered after strike 2")
                return False

            # 3 strikes — confirmed broken
            _strikes[key]["count"] = 3
            print(f"[strike 3/3] {component} confirmed broken — sending email")
            subject = f"🔴 [{status.upper()}] {component} — {client_name}"
            html = _html_alert(client_name, component, status, new_detail or detail)
            return send_email(subject, html)
    else:
        if key in _strikes:
            downtime = round((time.time() - _strikes[key]["first_seen"]) / 60)
            del _strikes[key]
            subject = f"🟢 [RECOVERED] {component} — {client_name}"
            html = _html_recovery(client_name, component, downtime)
            send_email(subject, html)
    return False

def send_test_email() -> bool:
    subject = "✅ OriginClaw Monitor — Test Alert"
    html = _html_alert("Wayne Bos", "test-component", "warning", "This is a test alert. If you receive this, email alerts are working correctly.")
    return send_email(subject, html)
