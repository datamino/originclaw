#!/usr/bin/env python3
"""Called by internal monitor to tell watchdog it's alive."""
import json, time, os, sys

HEARTBEAT_FILE = os.path.expanduser("~/.originclaw/watchdog_heartbeat.json")

def ping(client: str = "wayne", status: str = "ok"):
    os.makedirs(os.path.dirname(HEARTBEAT_FILE), exist_ok=True)
    with open(HEARTBEAT_FILE, "w") as f:
        json.dump({"last_ping": time.time(), "client": client, "status": status}, f)
    print(f"[ping] Heartbeat sent at {time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    ping(sys.argv[1] if len(sys.argv) > 1 else "wayne")
