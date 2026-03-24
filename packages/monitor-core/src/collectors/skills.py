import subprocess, os, time
from ..state.store import write_metric

def check_process(launchagent_name: str) -> tuple[str, str]:
    try:
        r = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=5)
        if launchagent_name in r.stdout:
            parts = [l for l in r.stdout.split("\n") if launchagent_name in l]
            if parts:
                pid = parts[0].split()[0]
                return ("ok" if pid != "-" else "warning"), f"PID {pid}"
        return "offline", "Not running"
    except Exception as e:
        return "warning", str(e)

def check_log_freshness(log_path: str, max_age_seconds: int = 300) -> tuple[str, str]:
    path = os.path.expanduser(log_path)
    if not os.path.exists(path):
        return "warning", "Log file not found"
    age = time.time() - os.path.getmtime(path)
    if age > max_age_seconds:
        return "warning", f"Log stale ({round(age/60)}m old)"
    return "ok", f"Updated {round(age)}s ago"

def collect_skills(client: str) -> dict:
    results = {}

    # S&P 500 daemon
    status, detail = check_process("com.velan.sp500monitor")
    write_metric(client, "sp500-daemon", status, detail)
    results["sp500-daemon"] = {"status": status, "detail": detail}

    # S&P log freshness (only during market hours Mon-Fri)
    log_status, log_detail = check_log_freshness("~/.openclaw/workspace/logs/sp500-monitor.log", max_age_seconds=120)
    write_metric(client, "sp500-log", log_status, log_detail)
    results["sp500-log"] = {"status": log_status, "detail": log_detail}

    # Morning brief script exists
    brief_path = os.path.expanduser("~/.openclaw/workspace/skills/morning-brief/scripts/morning-brief.py")
    status = "ok" if os.path.exists(brief_path) else "warning"
    write_metric(client, "morning-brief-skill", status, "Script present" if status == "ok" else "Script missing")
    results["morning-brief"] = {"status": status}

    # Portfolio tracker
    pt_path = os.path.expanduser("~/.openclaw/workspace/skills/portfolio-tracker/scripts/portfolio-tracker.py")
    status = "ok" if os.path.exists(pt_path) else "warning"
    write_metric(client, "portfolio-tracker-skill", status, "Script present" if status == "ok" else "Script missing")
    results["portfolio-tracker"] = {"status": status}

    return results
