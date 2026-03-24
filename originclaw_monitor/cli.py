#!/usr/bin/env python3
"""
originclaw-monitor CLI
Usage:
  originclaw-monitor init       — auto-discover OpenClaw and configure
  originclaw-monitor start      — start monitoring daemon
  originclaw-monitor status     — show current health
  originclaw-monitor run        — run one check cycle
  originclaw-monitor test-alert — send test alert
  originclaw-monitor watchdog   — start gateway watchdog
  originclaw-monitor dashboard  — start web dashboard
"""
import argparse, sys, os, json, subprocess, shutil, time

CONFIG_PATH = os.path.expanduser("~/.originclaw/config.json")
DB_PATH     = os.path.expanduser("~/.originclaw/monitor.db")
LOG_DIR     = os.path.expanduser("~/.originclaw/logs")

DEFAULT_CONFIG = {
    "client": "default",
    "client_name": "My OpenClaw",
    "interval_seconds": 300,
    "telegram_token": "",
    "telegram_chat_id": "",
    "resend_api_key": "",
    "developer_email": "",
    "gateway_port": 18789,
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            c = DEFAULT_CONFIG.copy()
            c.update(json.load(f))
            return c
    return DEFAULT_CONFIG.copy()

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def cmd_init(args):
    from .discovery import discover_openclaw, print_discovery
    discovered = discover_openclaw()
    print_discovery(discovered)
    # Pre-populate config from discovered values

    print("\n⬡  OriginClaw Monitor — Setup\n" + "─"*40)

    # Auto-discover OpenClaw
    openclaw_config = os.path.expanduser("~/.openclaw/openclaw.json")
    workspace = os.path.expanduser("~/.openclaw/workspace")
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(openclaw_config):
        print("✅ OpenClaw found:", openclaw_config)
        try:
            with open(openclaw_config) as f:
                oc = json.load(f)
            tg = oc.get("channels", {}).get("telegram", {})
            if tg.get("botToken"):
                config["telegram_token"] = tg["botToken"]
                print("✅ Telegram bot token found")
            config["gateway_port"] = oc.get("gateway", {}).get("port", 18789)
        except:
            pass
    else:
        print("⚠️  OpenClaw config not found — using defaults")

    # Prompt for missing values
    if not config.get("client_name") or config["client_name"] == "My OpenClaw":
        name = input("\nClient name (e.g. Wayne Bos): ").strip()
        if name: config["client_name"] = name
        config["client"] = name.lower().replace(" ", "_") if name else "default"

    if not config.get("developer_email"):
        email = input("Developer email for alerts: ").strip()
        if email: config["developer_email"] = email

    if not config.get("resend_api_key"):
        key = input("Resend API key (resend.com — free): ").strip()
        if key: config["resend_api_key"] = key

    if not config.get("telegram_chat_id"):
        chat_id = input("Developer Telegram chat ID (optional, press Enter to skip): ").strip()
        if chat_id: config["telegram_chat_id"] = chat_id

    save_config(config)
    os.makedirs(LOG_DIR, exist_ok=True)

    # Test gateway
    r = subprocess.run(["curl","-sf","--max-time","2",f"http://localhost:{config['gateway_port']}/health"],
        capture_output=True, text=True, timeout=3)
    gw_ok = r.returncode == 0

    print(f"\n{'─'*40}")
    print(f"  Config saved: {CONFIG_PATH}")
    print(f"  Gateway:      {'✅ running' if gw_ok else '⚠️  not detected'}")
    print(f"  Client:       {config['client_name']}")
    print(f"  Dev email:    {config.get('developer_email','not set')}")
    print(f"\nRun: originclaw-monitor start")
    print(f"{'─'*40}\n")

def cmd_status(args):
    config = load_config()
    print(f"\n⬡  OriginClaw Monitor — {config['client_name']}")
    print("─"*50)

    # Gateway
    r = subprocess.run(["curl","-sf","--max-time","2",f"http://localhost:{config.get('gateway_port',18789)}/health"],
        capture_output=True, text=True, timeout=3)
    gw = "✅ running" if r.returncode == 0 else "🔴 down"
    print(f"  Gateway         {gw}")

    # Watchdog
    r2 = subprocess.run(["pgrep","-f","gw-watch.py"], capture_output=True, text=True)
    wd = "✅ running" if r2.stdout.strip() else "⚠️  not running"
    print(f"  Watchdog        {wd}")

    # Crons
    r3 = subprocess.run(["openclaw","cron","list"], capture_output=True, text=True, timeout=10)
    cron_count = r3.stdout.count("idle") + r3.stdout.count("active") if r3.returncode == 0 else 0
    print(f"  Cron jobs       {cron_count} active")

    # Heartbeat ping
    hb_path = os.path.expanduser("~/.originclaw/watchdog_heartbeat.json")
    if os.path.exists(hb_path):
        with open(hb_path) as f:
            hb = json.load(f)
        age = round(time.time() - hb.get("last_ping", 0))
        print(f"  Last heartbeat  {age}s ago")

    print(f"  Dashboard       http://localhost:8787")
    print("─"*50 + "\n")

def cmd_watchdog(args):
    watchdog_script = os.path.expanduser("~/.originclaw/gw-watch.py")
    if not os.path.exists(watchdog_script):
        print("❌ Watchdog script not found. Run: originclaw-monitor init")
        sys.exit(1)
    print("Starting gateway watchdog...")
    os.system(f"nohup python3 {watchdog_script} >> {LOG_DIR}/gw-watch.log 2>&1 &")
    time.sleep(2)
    r = subprocess.run(["pgrep","-f","gw-watch.py"], capture_output=True, text=True)
    if r.stdout.strip():
        print(f"✅ Watchdog running (PID {r.stdout.strip()})")
    else:
        print("❌ Watchdog failed to start")

def cmd_dashboard(args):
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    api_path = os.path.join(pkg_dir, "..", "packages", "monitor-core", "src", "api.py")
    print("Starting dashboard API on http://localhost:8787 ...")
    os.system(f"uvicorn packages.monitor-core.src.api:app --host 127.0.0.1 --port 8787 --reload &")
    print("Dashboard: http://localhost:5173 (run: cd dashboard && npm run dev)")

def cmd_test_alert(args):
    config = load_config()
    print(f"Sending test alert to {config.get('developer_email', 'not configured')}...")
    resend_key = config.get("resend_api_key", os.environ.get("RESEND_API_KEY", ""))
    dev_email = config.get("developer_email", "")
    if not resend_key or not dev_email:
        print("❌ Configure resend_api_key and developer_email first (run: originclaw-monitor init)")
        return
    html = "<div style='font-family:sans-serif;padding:24px;'><h2>✅ Test Alert</h2><p>OriginClaw Monitor is configured correctly.</p></div>"
    r = subprocess.run(["curl","-sf","-X","POST","https://api.resend.com/emails",
        "-H",f"Authorization: Bearer {resend_key}","-H","Content-Type: application/json",
        "-d",json.dumps({"from":"OriginClaw <onboarding@resend.dev>","to":[dev_email],
            "subject":"✅ OriginClaw Monitor — Test Alert","html":html})],
        capture_output=True, text=True, timeout=15)
    try:
        result = json.loads(r.stdout)
        print(f"{'✅ Sent! id:'+result['id'] if 'id' in result else '❌ Failed: '+str(result)}")
    except:
        print(f"❌ Error: {r.stdout}")


def cmd_help(args=None):
    B = chr(27)+'[1m'
    G = chr(27)+'[0;32m'
    C = chr(27)+'[0;36m'
    D = chr(27)+'[2m'
    R = chr(27)+'[0m'
    print(B+'  OriginClaw Monitor'+R+' — Observability for OpenClaw deployments')
    print(D+'  v0.1.0 · github.com/datamino/originclaw'+R)
    print()
    print(B+'  SETUP'+R)
    print(G+'  originclaw-monitor init         '+R+' Auto-discover OpenClaw and configure')
    print(G+'  originclaw-monitor status       '+R+' Full system health at a glance')
    print(G+'  originclaw-monitor test-alert   '+R+' Send test email to verify alerts work')
    print()
    print(B+'  MONITORING'+R)
    print(G+'  originclaw-monitor start        '+R+' Start watchdog + monitoring daemon')
    print(G+'  originclaw-monitor run          '+R+' Run one full check cycle (all layers)')
    print(G+'  originclaw-monitor watchdog     '+R+' Start gateway watchdog (instant alerts)')
    print(G+'  originclaw-monitor dashboard    '+R+' Web dashboard at http://localhost:8787')
    print()
    print(B+'  WHAT IT MONITORS'+R)
    print(C+'  Layer 1'+R+' — Infrastructure    CPU · Memory · Disk · Network')
    print(C+'  Layer 2'+R+' — OpenClaw Core     Gateway · Crons · Heartbeat · Sessions')
    print(C+'  Layer 3'+R+' — Integrations      Gmail · Calendar · APIs · MCP servers')
    print(C+'  Layer 4'+R+' — Skills & Daemons  Python scripts · Background processes')
    print(C+'  Layer 5'+R+' — Business          Morning brief · S&P alerts · Delivery')
    print()
    print(B+'  ALERT CHANNELS'+R)
    print('  telegram_token + telegram_chat_id   Telegram alerts')
    print('  resend_api_key + developer_email    Email via Resend')
    print('  discord_webhook                     Discord alerts')
    print('  slack_webhook                       Slack alerts')
    print()
    print(B+'  WATCHDOG'+R)
    print('  Checks gateway every 1s — fires alert the moment it goes down.')
    print('  Recovery alert when it comes back. Fully independent of OpenClaw.')
    print()
    print(B+'  INSTALL'+R)
    print(D+'  pip install originclaw-monitor'+R)
    print()

def _fix_path():
    import sys, os
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    home = os.path.expanduser("~")
    for d in [f"{home}/Library/Python/{ver}/bin", f"{home}/.local/bin"]:
        if os.path.isfile(os.path.join(d, "originclaw-monitor")):
            if d not in os.environ.get("PATH", ""):
                for rc in [f"{home}/.zshenv", f"{home}/.zshrc", f"{home}/.bashrc"]:
                    try:
                        content = open(rc).read() if os.path.exists(rc) else ""
                        if d not in content:
                            open(rc, "a").write(f"
export PATH="{d}:\/Users/valen/Library/Python/3.9/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Users/valen/Library/Python/3.9/bin"
")
                    except: pass
            break

def main():
    _fix_path()
    parser = argparse.ArgumentParser(
        prog="originclaw-monitor",
        description="⬡ OriginClaw Monitor — Observability for OpenClaw deployments"
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init",        help="Auto-discover OpenClaw and configure")
    sub.add_parser("start",       help="Start monitoring daemon")
    sub.add_parser("status",      help="Show current system health")
    sub.add_parser("run",         help="Run one check cycle")
    sub.add_parser("test-alert",  help="Send test alert email")
    sub.add_parser("watchdog",    help="Start gateway watchdog")
    sub.add_parser("dashboard",   help="Start web dashboard")
    sub.add_parser("help", help="Show all commands and features")
    args = parser.parse_args()

    if args.command == "init":        cmd_init(args)
    elif args.command == "status":    cmd_status(args)
    elif args.command == "watchdog":  cmd_watchdog(args)
    elif args.command == "test-alert":cmd_test_alert(args)
    elif args.command == "dashboard": cmd_dashboard(args)
    elif args.command == "help": cmd_help(args)
    elif args.command == "start":
        print("Starting monitor... (run: originclaw-monitor status to check)")
        cmd_watchdog(args)
    else:
        cmd_help(args)

if __name__ == "__main__":
    main()
