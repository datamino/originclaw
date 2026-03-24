#!/usr/bin/env python3
"""
OriginClaw Monitor — External Watchdog (Phase 5)
Dead man's switch — runs COMPLETELY independent of OpenClaw.
If internal monitor goes silent → sends alert directly.

Architecture:
  Internal monitor → pings watchdog every 60s
  Watchdog → if silent for 5min → fires alert independently
  If Mac mini loses power → cloud ping stops → cloud watchdog alerts

This process has ZERO OpenClaw dependencies.
It only uses: stdlib, curl, launchctl
"""
import time, os, json, subprocess, urllib.request, urllib.parse
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
HEARTBEAT_FILE = os.path.expanduser("~/.originclaw/watchdog_heartbeat.json")
MAX_SILENCE_SECONDS = 300   # 5 min without ping = alert
CHECK_INTERVAL = 30         # check every 30s
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_aA59kgTU_7c5b3i758hMCukf528Tj3fo9")
DEVELOPER_EMAIL = "p229279@pwr.nu.edu.pk"
TELEGRAM_TOKEN = "8609655398:AAGGAN7D1LptaK4yXi_kmZ9DJ0ChpRw-wuY"
TELEGRAM_CHAT_ID = "8364129276"  # Wayne — immediate alert if system dies

# ─── Heartbeat File ───────────────────────────────────────────────────────────
def read_heartbeat() -> dict:
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE) as f:
                return json.load(f)
    except:
        pass
    return {"last_ping": 0, "client": "unknown", "status": "unknown"}

def write_heartbeat(client: str = "wayne", status: str = "ok"):
    os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
    with open(HEARTBEAT_FILE, "w") as f:
        json.dump({"last_ping": time.time(), "client": client, "status": status}, f)

# ─── Alert Delivery ───────────────────────────────────────────────────────────
def send_telegram(message: str):
    try:
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message})
        r = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            "-H", "Content-Type: application/json",
            "-d", data
        ], capture_output=True, text=True, timeout=10)
        return "ok" in r.stdout.lower()
    except:
        return False

def send_email(subject: str, body: str):
    try:
        html = f"""<div style="font-family:sans-serif;max-width:520px;margin:40px auto;background:white;border-radius:12px;border:1px solid #e5e7eb;">
<div style="background:#111827;padding:20px 24px;"><span style="color:white;font-weight:700;">⬡ OriginClaw Watchdog</span></div>
<div style="padding:24px;">
<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:20px;display:inline-block;padding:4px 14px;margin-bottom:16px;">
<span style="color:#dc2626;font-weight:700;font-size:11px;">SYSTEM DOWN</span></div>
<h2 style="color:#111827;">Monitor Heartbeat Lost</h2>
<p style="color:#374151;">{body}</p>
<p style="color:#9ca3af;font-size:12px;margin-top:20px;">{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}</p>
</div></div>"""
        data = json.dumps({"from": "OriginClaw Watchdog <onboarding@resend.dev>", "to": [DEVELOPER_EMAIL], "subject": subject, "html": html})
        r = subprocess.run([
            "curl", "-s", "-X", "POST", "https://api.resend.com/emails",
            "-H", f"Authorization: Bearer {RESEND_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", data
        ], capture_output=True, text=True, timeout=15)
        result = json.loads(r.stdout)
        return "id" in result
    except:
        return False

def fire_alert(silence_seconds: float, hb: dict):
    mins = round(silence_seconds / 60)
    client = hb.get("client", "unknown")
    msg = (
        f"🚨 WATCHDOG ALERT\n\n"
        f"OriginClaw Monitor has been SILENT for {mins} minutes.\n"
        f"Client: {client}\n"
        f"Last ping: {time.strftime('%H:%M UTC', time.gmtime(hb.get('last_ping', 0)))}\n\n"
        f"Possible causes:\n"
        f"• OpenClaw gateway crashed\n"
        f"• Mac mini lost power/network\n"
        f"• Monitor process killed\n\n"
        f"Action required: Check the host machine."
    )
    tg_ok = send_telegram(msg)
    email_ok = send_email(
        f"🚨 WATCHDOG: OriginClaw Monitor silent for {mins}m — {client}",
        f"The OriginClaw Monitor has been silent for {mins} minutes. Last ping was at {time.strftime('%H:%M UTC', time.gmtime(hb.get('last_ping', 0)))}. Check the host machine immediately."
    )
    print(f"[watchdog] Alert fired — telegram:{tg_ok} email:{email_ok}")
    return tg_ok or email_ok

def fire_recovery(silence_seconds: float):
    mins = round(silence_seconds / 60)
    msg = f"✅ WATCHDOG: Monitor heartbeat restored (was silent {mins}m)"
    send_telegram(msg)
    print(f"[watchdog] Recovery alert sent")

# ─── Main Loop ────────────────────────────────────────────────────────────────
def main():
    print(f"[watchdog] Started — checking every {CHECK_INTERVAL}s, alert after {MAX_SILENCE_SECONDS}s silence")
    print(f"[watchdog] Heartbeat file: {HEARTBEAT_FILE}")
    alert_fired = False
    alert_time = None

    while True:
        try:
            hb = read_heartbeat()
            last_ping = hb.get("last_ping", 0)
            silence = time.time() - last_ping if last_ping > 0 else MAX_SILENCE_SECONDS + 1

            if silence > MAX_SILENCE_SECONDS:
                if not alert_fired:
                    print(f"[watchdog] ⚠️  Silence detected: {round(silence)}s — firing alert")
                    fire_alert(silence, hb)
                    alert_fired = True
                    alert_time = time.time()
                else:
                    print(f"[watchdog] Still silent: {round(silence)}s (alert already sent)")
            else:
                if alert_fired:
                    # Monitor came back
                    fire_recovery(time.time() - alert_time if alert_time else 0)
                    alert_fired = False
                    alert_time = None
                print(f"[watchdog] ✅ Heartbeat OK — last ping {round(silence)}s ago")

        except Exception as e:
            print(f"[watchdog] Error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
