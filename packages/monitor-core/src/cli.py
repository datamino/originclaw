#!/usr/bin/env python3
import argparse, json, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.state.store import init_db, get_latest, get_active_alerts
from src.collectors.infrastructure import collect_infrastructure
from src.collectors.openclaw_core import collect_openclaw_core

STATUS_ICON = {"ok": "✅", "warning": "⚠️ ", "critical": "🔴", "offline": "⚫"}

def cmd_status(args):
    client = args.client or "default"
    workspace = args.workspace or os.path.expanduser("~/.openclaw/workspace")
    print(f"\n{'━'*48}")
    print(f"  ORIGINCLAW MONITOR — {client.upper()}")
    print(f"{'━'*48}")
    components = ["gateway", "crons", "config", "cpu", "memory", "disk", "network"]
    all_ok = True
    for comp in components:
        rec = get_latest(client, comp)
        if rec:
            icon = STATUS_ICON.get(rec["status"], "?")
            print(f"  {icon} {comp:<18} {rec['status']:<10} {rec['value'] or ''}")
            if rec["status"] != "ok":
                all_ok = False
        else:
            print(f"  ⚫ {comp:<18} no data")
    print(f"{'━'*48}")
    alerts = get_active_alerts(client)
    if alerts:
        print(f"\n  ⚠️  {len(alerts)} active alert(s):")
        for a in alerts:
            print(f"     [{a['severity'].upper()}] {a['component']}: {a['message'][:60]}")
    else:
        print(f"\n  All green — no active alerts")
    print()

def cmd_collect(args):
    client = args.client or "default"
    workspace = args.workspace or os.path.expanduser("~/.openclaw/workspace")
    init_db()
    print(f"Collecting metrics for client: {client}")
    infra = collect_infrastructure(client)
    core = collect_openclaw_core(client, workspace)
    all_results = {**infra, **core}
    issues = {k: v for k, v in all_results.items() if v.get("status") != "ok"}
    if issues:
        print(f"⚠️  Issues detected: {', '.join(issues.keys())}")
    else:
        print("✅ All systems healthy")

def cmd_init(args):
    init_db()
    print("✅ Database initialized at ~/.originclaw/monitor.db")
    print("\nNext steps:")
    print("  originclaw-monitor collect --client <name>")
    print("  originclaw-monitor status --client <name>")

def main():
    parser = argparse.ArgumentParser(prog="originclaw-monitor", description="OriginClaw Monitor CLI")
    parser.add_argument("--client", help="Client name")
    parser.add_argument("--workspace", help="OpenClaw workspace path")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init")
    sub.add_parser("status")
    sub.add_parser("collect")
    args = parser.parse_args()
    if args.command == "init":
        cmd_init(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "collect":
        cmd_collect(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
