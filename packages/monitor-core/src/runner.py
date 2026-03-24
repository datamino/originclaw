#!/usr/bin/env python3
"""OriginClaw Monitor — Runner"""
import time, json, os, argparse
from .state.store import init_db, get_latest
from .collectors.infrastructure import collect_infrastructure
from .collectors.openclaw_core import collect_all as collect_openclaw
from .collectors.integrations import collect_integrations
from .collectors.skills import collect_skills
from .alerting.engine import evaluate_and_alert, send_test_alert, send_daily_summary
from .alerting.email_alert import HEARTBEAT_FILE
from .alerting.email_alert import send_email, _html_alert

DEFAULT_CONFIG = {
    "client": "wayne",
    "client_name": "Wayne Bos",
    "interval_seconds": 300,
    "telegram_token": "8609655398:AAGGAN7D1LptaK4yXi_kmZ9DJ0ChpRw-wuY",
    "telegram_chat_id": "8364129276",
}

def run_once(config: dict, verbose: bool = False) -> dict:
    client = config["client"]
    results = {}

    
    # Ping watchdog heartbeat
    import json as _json
    _hb_path = os.path.expanduser('~/.originclaw/watchdog_heartbeat.json')
    os.makedirs(os.path.dirname(_hb_path), exist_ok=True)
    with open(_hb_path, 'w') as _f:
        _json.dump({'last_ping': time.time(), 'client': client, 'status': 'ok'}, _f)

    print(f"[{time.strftime('%H:%M:%S')}] Collecting — {config['client_name']}")

    results.update(collect_infrastructure(client))
    results.update(collect_openclaw(client))
    results.update(collect_integrations(client))
    results.update(collect_skills(client))

    fired = evaluate_and_alert(client, config["client_name"], results, config)

    issues = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") not in ("ok", None))
    
    # Ping watchdog heartbeat
    import json as _json
    _hb_path = os.path.expanduser('~/.originclaw/watchdog_heartbeat.json')
    os.makedirs(os.path.dirname(_hb_path), exist_ok=True)
    with open(_hb_path, 'w') as _f:
        _json.dump({'last_ping': time.time(), 'client': client, 'status': 'ok'}, _f)

    print(f"[{time.strftime('%H:%M:%S')}] Done — {len(results)} checks, {issues} issues, {len(fired)} alerts fired")
    if verbose and fired:
        for f in fired:
            print(f"  → {f}")
    return results

def status(config: dict):
    client = config["client"]
    components = ["cpu","memory","disk","network","gateway","crons","heartbeat","sessions",
                  "yahoo-finance","marketaux","massive-api","gmail","google-calendar","telegram",
                  "sp500-daemon","morning-brief-skill"]
    print(f"\n{'─'*52}")
    print(f"  OriginClaw Monitor — {config['client_name']}")
    print(f"{'─'*52}")
    for comp in components:
        row = get_latest(client, comp)
        if row:
            icon = "✅" if row["status"]=="ok" else "⚠️ " if row["status"]=="warning" else "🔴"
            print(f"  {icon}  {comp:<30} {row['status']:<10} {row['value'] or ''}")
        else:
            print(f"  ⚪   {comp:<30} no data")
    print(f"{'─'*52}\n")

def main():
    parser = argparse.ArgumentParser(description="OriginClaw Monitor")
    parser.add_argument("command", choices=["start","run","status","test-alert","summary"])
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    config = DEFAULT_CONFIG.copy()
    if args.config and os.path.exists(args.config):
        with open(args.config) as f:
            config.update(json.load(f))

    init_db()

    if args.command == "status":
        status(config)
    elif args.command == "run":
        run_once(config, verbose=args.verbose)
    elif args.command == "test-alert":
        print("Sending test alert...")
        channels = send_test_alert(config)
        print(f"Delivered to: {channels}")
    elif args.command == "summary":
        results = run_once(config, verbose=False)
        send_daily_summary(config["client"], config["client_name"], results, config)
    elif args.command == "start":
        print(f"Starting OriginClaw Monitor (interval: {config['interval_seconds']}s)")
        while True:
            run_once(config, verbose=args.verbose)
            time.sleep(config["interval_seconds"])

if __name__ == "__main__":
    main()
