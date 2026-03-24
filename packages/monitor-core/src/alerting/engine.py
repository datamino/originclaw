#!/usr/bin/env python3
"""
OriginClaw Monitor — Alert Engine (Phase 3)
- Multi-channel: Telegram, Discord, Email
- Deduplication: don't spam same alert
- Auto-recovery: notify when component comes back
- Severity escalation: warning → critical
- Cooldown: per-component alert cooldown
"""
import urllib.request, urllib.parse, urllib.error
import json, time, os, sqlite3
from dataclasses import dataclass
from typing import Optional

DB_PATH = os.path.expanduser("~/.originclaw/monitor.db")
COOLDOWN_SECONDS = 300  # 5 min per component

# ─── Alert State ──────────────────────────────────────────────────────────────

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_alert_state(client: str, component: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM alerts WHERE client=? AND component=? AND resolved_at IS NULL ORDER BY fired_at DESC LIMIT 1",
        (client, component)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def open_alert(client: str, component: str, severity: str, message: str) -> int:
    conn = get_conn()
    cursor = conn.execute(
        "INSERT INTO alerts (client, component, severity, message, fired_at) VALUES (?,?,?,?,?)",
        (client, component, severity, message, time.time())
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id

def resolve_alert(client: str, component: str):
    conn = get_conn()
    conn.execute(
        "UPDATE alerts SET resolved_at=? WHERE client=? AND component=? AND resolved_at IS NULL",
        (time.time(), client, component)
    )
    conn.commit()
    conn.close()

def was_recently_alerted(client: str, component: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT fired_at FROM alerts WHERE client=? AND component=? ORDER BY fired_at DESC LIMIT 1",
        (client, component)
    ).fetchone()
    conn.close()
    if not row:
        return False
    return (time.time() - row["fired_at"]) < COOLDOWN_SECONDS

# ─── Channel Delivery ─────────────────────────────────────────────────────────

def send_telegram(token: str, chat_id: str, message: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as r:
            result = json.loads(r.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"[alert] Telegram delivery failed: {e}")
        return False

def send_discord(webhook_url: str, message: str) -> bool:
    # Strip HTML tags for Discord
    import re
    clean = re.sub(r'<[^>]+>', '', message).strip()
    data = json.dumps({"content": clean}).encode()
    req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status in (200, 204)
    except Exception as e:
        print(f"[alert] Discord delivery failed: {e}")
        return False

def deliver(message: str, config: dict):
    delivered = []
    if config.get("telegram_token") and config.get("telegram_chat_id"):
        ok = send_telegram(config["telegram_token"], config["telegram_chat_id"], message)
        if ok: delivered.append("telegram")
    if config.get("discord_webhook"):
        ok = send_discord(config["discord_webhook"], message)
        if ok: delivered.append("discord")
    return delivered

# ─── Message Formatting ───────────────────────────────────────────────────────

SEVERITY_ICONS = {"critical": "🔴", "warning": "🟡", "ok": "🟢", "offline": "⚫"}
SEVERITY_LABELS = {"critical": "CRITICAL", "warning": "WARNING", "ok": "RECOVERED", "offline": "OFFLINE"}

def format_alert(client_name: str, component: str, severity: str, detail: str) -> str:
    icon = SEVERITY_ICONS.get(severity, "⚪")
    label = SEVERITY_LABELS.get(severity, severity.upper())
    ts = time.strftime("%H:%M UTC", time.gmtime())
    return (
        f"{icon} <b>ORIGINCLAW ALERT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• <b>Client:</b> {client_name}\n"
        f"• <b>Component:</b> {component}\n"
        f"• <b>Status:</b> {label}\n"
        f"• <b>Detail:</b> {detail}\n\n"
        f"<i>{ts}</i>"
    )

def format_recovery(client_name: str, component: str, downtime_seconds: float) -> str:
    mins = round(downtime_seconds / 60)
    ts = time.strftime("%H:%M UTC", time.gmtime())
    return (
        f"🟢 <b>RECOVERED</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• <b>Client:</b> {client_name}\n"
        f"• <b>Component:</b> {component}\n"
        f"• <b>Downtime:</b> {mins}m\n\n"
        f"<i>{ts}</i>"
    )

def format_summary(client_name: str, results: dict) -> str:
    issues = {k: v for k, v in results.items() if isinstance(v, dict) and v.get("status") not in ("ok", None)}
    healthy = len(results) - len(issues)
    ts = time.strftime("%H:%M UTC", time.gmtime())
    lines = [
        f"📊 <b>MONITOR SUMMARY</b>",
        f"━━━━━━━━━━━━━━━━━━━━\n",
        f"• <b>Client:</b> {client_name}",
        f"• <b>Healthy:</b> {healthy}/{len(results)}",
    ]
    if issues:
        lines.append(f"• <b>Issues:</b>")
        for comp, data in issues.items():
            icon = SEVERITY_ICONS.get(data.get("status",""), "⚪")
            lines.append(f"  {icon} {comp}: {data.get('detail', data.get('value',''))}")
    else:
        lines.append(f"• All systems operational ✅")
    lines.append(f"\n<i>{ts}</i>")
    return "\n".join(lines)

# ─── Main Evaluation Logic ────────────────────────────────────────────────────

def evaluate_and_alert(client: str, client_name: str, results: dict, config: dict) -> list:
    fired = []

    for component, data in results.items():
        if not isinstance(data, dict):
            continue

        status = data.get("status", "ok")
        detail = data.get("detail", data.get("value", ""))
        existing = get_alert_state(client, component)

        if status in ("warning", "critical", "offline"):
            if existing:
                # Already alerting — check if severity escalated
                if status == "critical" and existing["severity"] == "warning":
                    msg = format_alert(client_name, component, status, f"Escalated: {detail}")
                    channels = deliver(msg, config)
                    open_alert(client, component, status, detail)
                    fired.append({"component": component, "severity": status, "channels": channels, "type": "escalation"})
            else:
                # New issue — check cooldown
                if not was_recently_alerted(client, component):
                    msg = format_alert(client_name, component, status, detail)
                    channels = deliver(msg, config)
                    open_alert(client, component, status, detail)
                    fired.append({"component": component, "severity": status, "channels": channels, "type": "new"})
                    print(f"[alert] Fired {status} alert for {component} → {channels}")

        elif status == "ok" and existing:
            # Component recovered
            downtime = time.time() - existing["fired_at"]
            msg = format_recovery(client_name, component, downtime)
            deliver(msg, config)
            resolve_alert(client, component)
            fired.append({"component": component, "severity": "ok", "type": "recovery"})
            print(f"[alert] Recovery alert for {component} (down {round(downtime/60)}m)")

    return fired

def send_test_alert(config: dict):
    msg = format_alert(
        config.get("client_name", "Test Client"),
        "test-component",
        "warning",
        "This is a test alert from OriginClaw Monitor"
    )
    channels = deliver(msg, config)
    print(f"Test alert sent → {channels}")
    return channels

def send_daily_summary(client: str, client_name: str, results: dict, config: dict):
    msg = format_summary(client_name, results)
    channels = deliver(msg, config)
    print(f"Daily summary sent → {channels}")
    return channels
