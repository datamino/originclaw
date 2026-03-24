#!/usr/bin/env python3
"""
Multi-channel alert delivery.
Supports: Telegram, Email (Resend), Discord, Slack
"""
import json, subprocess, os

def send_telegram(token: str, chat_id: str, message: str) -> bool:
    if not token or not chat_id: return False
    try:
        r = subprocess.run(["curl","-sf","-X","POST",
            f"https://api.telegram.org/bot{token}/sendMessage",
            "-H","Content-Type: application/json",
            "-d",json.dumps({"chat_id": chat_id, "text": message})],
            capture_output=True, text=True, timeout=10)
        return "true" in r.stdout.lower()
    except: return False

def send_email(resend_key: str, to: str, subject: str, html: str) -> bool:
    if not resend_key or not to: return False
    try:
        r = subprocess.run(["curl","-sf","-X","POST","https://api.resend.com/emails",
            "-H",f"Authorization: Bearer {resend_key}",
            "-H","Content-Type: application/json",
            "-d",json.dumps({"from":"OriginClaw Monitor <onboarding@resend.dev>",
                "to":[to],"subject":subject,"html":html})],
            capture_output=True, text=True, timeout=15)
        return "id" in json.loads(r.stdout)
    except: return False

def send_discord(webhook_url: str, message: str) -> bool:
    if not webhook_url: return False
    try:
        import re
        clean = re.sub(r'<[^>]+>', '', message)
        r = subprocess.run(["curl","-sf","-X","POST", webhook_url,
            "-H","Content-Type: application/json",
            "-d",json.dumps({"content": clean, "username": "OriginClaw Monitor"})],
            capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except: return False

def send_slack(webhook_url: str, message: str) -> bool:
    if not webhook_url: return False
    try:
        r = subprocess.run(["curl","-sf","-X","POST", webhook_url,
            "-H","Content-Type: application/json",
            "-d",json.dumps({"text": message})],
            capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except: return False

def format_alert_html(client: str, component: str, severity: str, detail: str) -> str:
    colors = {"critical":"#dc2626","warning":"#d97706","offline":"#6b7280","ok":"#16a34a"}
    emojis = {"critical":"🔴","warning":"🟡","offline":"⚫","ok":"🟢"}
    color = colors.get(severity, "#374151")
    emoji = emojis.get(severity, "⚪")
    import time
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    return f"""<div style="font-family:sans-serif;max-width:480px;margin:40px auto;border-radius:12px;overflow:hidden;border:1px solid #e5e7eb;">
<div style="background:#111827;padding:18px 22px;"><span style="color:white;font-weight:700;">⬡ OriginClaw Monitor</span></div>
<div style="padding:22px;">
<div style="background:{color}18;border:1px solid {color}44;border-radius:20px;display:inline-block;padding:4px 12px;margin-bottom:14px;">
<span style="color:{color};font-weight:700;font-size:11px;text-transform:uppercase;">{emoji} {severity.upper()}</span></div>
<h2 style="color:#111827;margin:0 0 4px;">{component}</h2>
<p style="color:#6b7280;font-size:13px;margin:0 0 16px;">{client}</p>
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:14px;">
<code style="color:#374151;font-size:12px;">{detail}</code></div>
<p style="color:#9ca3af;font-size:11px;margin-top:16px;">{ts}</p>
</div></div>"""

def deliver_all(config: dict, subject: str, message: str, html: str = None) -> dict:
    """Deliver alert to all configured channels."""
    results = {}
    if not html:
        html = f"<div style='font-family:sans-serif;padding:24px;'><p>{message}</p></div>"

    if config.get("telegram_token") and config.get("telegram_chat_id"):
        results["telegram"] = send_telegram(config["telegram_token"], config["telegram_chat_id"], message)

    if config.get("resend_api_key") and config.get("developer_email"):
        results["email"] = send_email(config["resend_api_key"], config["developer_email"], subject, html)

    if config.get("discord_webhook"):
        results["discord"] = send_discord(config["discord_webhook"], message)

    if config.get("slack_webhook"):
        results["slack"] = send_slack(config["slack_webhook"], message)

    return results
