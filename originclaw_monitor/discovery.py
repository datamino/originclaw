#!/usr/bin/env python3
"""
Auto-discovery — reads OpenClaw config and discovers all components automatically.
Works on any OpenClaw deployment without manual configuration.
"""
import json, os, subprocess, glob

def discover_openclaw(workspace: str = None) -> dict:
    """Auto-discover all OpenClaw components from config files."""
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    mcporter_path = os.path.expanduser("~/.mcporter/mcporter.json")
    ws = workspace or os.path.expanduser("~/.openclaw/workspace")
    result = {
        "gateway_port": 18789,
        "telegram_token": "",
        "telegram_chat_id": "",
        "crons": [],
        "heartbeat": {},
        "mcp_servers": [],
        "skills": [],
        "daemons": [],
        "channels": [],
    }

    # Read openclaw.json
    if os.path.exists(config_path):
        with open(config_path) as f:
            oc = json.load(f)

        result["gateway_port"] = oc.get("gateway", {}).get("port", 18789)

        # Telegram
        tg = oc.get("channels", {}).get("telegram", {})
        result["telegram_token"] = tg.get("botToken", "")

        # Heartbeat config
        hb = oc.get("agents", {}).get("defaults", {}).get("heartbeat", {})
        result["heartbeat"] = {
            "interval_min": _parse_interval(hb.get("every", "30m")),
            "target": hb.get("target", "none"),
            "to": hb.get("to", ""),
        }
        if result["heartbeat"]["to"]:
            result["telegram_chat_id"] = result["heartbeat"]["to"]

        # Channels
        for ch_name in oc.get("channels", {}).keys():
            result["channels"].append(ch_name)

    # Read cron jobs from openclaw
    try:
        r = subprocess.run(["openclaw","cron","list","--json"],
            capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip().startswith("["):
            crons = json.loads(r.stdout)
            result["crons"] = [{"id": c.get("id"), "name": c.get("name"),
                "schedule": c.get("schedule",{}), "enabled": c.get("enabled", True),
                "last_status": c.get("lastStatus", ""), "next_run": c.get("state",{}).get("nextRunAtMs")}
                for c in crons]
    except:
        pass

    # Read MCP servers from mcporter
    if os.path.exists(mcporter_path):
        with open(mcporter_path) as f:
            mp = json.load(f)
        result["mcp_servers"] = list(mp.get("mcpServers", {}).keys())

    # Discover skills from workspace
    skills_dir = os.path.join(ws, "skills")
    if os.path.isdir(skills_dir):
        result["skills"] = [d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d))]

    # Discover LaunchAgent daemons
    la_dir = os.path.expanduser("~/Library/LaunchAgents")
    if os.path.isdir(la_dir):
        for plist in glob.glob(os.path.join(la_dir, "*.plist")):
            name = os.path.basename(plist).replace(".plist", "")
            if "openclaw" in name.lower() or "velan" in name.lower() or "originclaw" in name.lower():
                result["daemons"].append(name)

    return result

def _parse_interval(s: str) -> int:
    """Parse interval string like '30m', '1h', '180m' to minutes."""
    s = s.strip().lower()
    if s.endswith("h"):  return int(s[:-1]) * 60
    if s.endswith("m"):  return int(s[:-1])
    if s.endswith("s"):  return max(1, int(s[:-1]) // 60)
    return 30

def print_discovery(result: dict):
    print(f"\n⬡  OpenClaw Discovery Results")
    print("─" * 45)
    print(f"  Gateway port:   {result['gateway_port']}")
    print(f"  Channels:       {', '.join(result['channels']) or 'none'}")
    print(f"  Cron jobs:      {len(result['crons'])}")
    for c in result['crons']:
        print(f"    • {c['name']}")
    print(f"  MCP servers:    {len(result['mcp_servers'])}")
    for m in result['mcp_servers'][:8]:
        print(f"    • {m}")
    if len(result['mcp_servers']) > 8:
        print(f"    ... +{len(result['mcp_servers'])-8} more")
    print(f"  Skills:         {len(result['skills'])}")
    print(f"  Daemons:        {len(result['daemons'])}")
    for d in result['daemons']:
        print(f"    • {d}")
    print(f"  Heartbeat:      every {result['heartbeat'].get('interval_min', '?')}m")
    print("─" * 45 + "\n")
