import urllib.request, urllib.parse, json

class TelegramAlert:
    def __init__(self, bot_token: str, chat_id: str):
        self.token = bot_token
        self.chat_id = chat_id

    def send(self, severity: str, component: str, message: str, client: str = ""):
        icons = {"critical": "🔴", "warning": "🟡", "ok": "🟢", "info": "ℹ️"}
        icon = icons.get(severity, "⚪")
        text = (
            f"{icon} ORIGINCLAW MONITOR\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• Client: {client or 'Unknown'}\n"
            f"• Component: {component}\n"
            f"• Severity: {severity.upper()}\n\n"
            f"{message}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": self.chat_id, "text": text}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as r:
                return json.loads(r.read()).get("ok")
        except Exception as e:
            print(f"Telegram alert failed: {e}")
            return False
