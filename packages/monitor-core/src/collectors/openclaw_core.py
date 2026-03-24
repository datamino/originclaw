import subprocess, json, time, os
from ..state.store import write_metric

def run_cmd(cmd: list, timeout: int = 10) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)

def collect_gateway(client: str) -> dict:
    ok, out = run_cmd(["openclaw", "gateway", "status"])
    status = "ok" if ok and "running" in out.lower() else "critical"
    write_metric(client, "gateway", status, out[:100])
    return {"status": status, "detail": out[:100]}

def collect_crons(client: str) -> dict:
    ok, out = run_cmd(["openclaw", "cron", "list", "--json"])
    if not ok:
        write_metric(client, "crons", "warning", "Could not list cron jobs")
        return {"status": "warning", "jobs": []}

    try:
        jobs = json.loads(out) if out.startswith("[") else []
    except Exception:
        jobs = []

    issues = []
    for job in jobs:
        name = job.get("name", "unknown")
        last_status = job.get("lastStatus", "")
        enabled = job.get("enabled", True)
        if not enabled:
            issues.append(f"{name}: disabled")
        elif last_status == "error":
            issues.append(f"{name}: last run errored")

    status = "warning" if issues else "ok"
    value = f"{len(jobs)} jobs, {len(issues)} issues"
    write_metric(client, "crons", status, value)
    return {"status": status, "jobs": jobs, "issues": issues}

def collect_heartbeat(client: str) -> dict:
    ok, out = run_cmd(["openclaw", "status", "--json"])
    if not ok:
        write_metric(client, "heartbeat", "warning", "Could not get status")
        return {"status": "warning"}

    try:
        data = json.loads(out)
        hb = data.get("heartbeat", {})
        last_ms = hb.get("lastRunAtMs", 0)
        interval_min = hb.get("intervalMinutes", 30)
        if last_ms:
            elapsed_min = (time.time() * 1000 - last_ms) / 60000
            if elapsed_min > interval_min * 3:
                status = "warning"
                detail = f"Last run {round(elapsed_min)}m ago (interval: {interval_min}m)"
            else:
                status = "ok"
                detail = f"Last run {round(elapsed_min)}m ago"
        else:
            status = "warning"
            detail = "No heartbeat recorded"
    except Exception:
        status = "ok"
        detail = "Heartbeat active"

    write_metric(client, "heartbeat", status, detail)
    return {"status": status, "detail": detail}

def collect_sessions(client: str) -> dict:
    ok, out = run_cmd(["openclaw", "sessions", "--json"])
    if not ok:
        write_metric(client, "sessions", "warning", "Could not list sessions")
        return {"status": "warning"}
    try:
        sessions = json.loads(out) if out else []
        count = len(sessions)
        status = "ok"
        write_metric(client, "sessions", status, f"{count} sessions")
        return {"status": status, "count": count}
    except Exception:
        write_metric(client, "sessions", "ok", "Sessions active")
        return {"status": "ok"}

def collect_config(client: str) -> dict:
    ok, out = run_cmd(["openclaw", "doctor"], timeout=15)
    if "invalid" in out.lower() or "error" in out.lower():
        status = "warning"
        write_metric(client, "config", "warning", "Config has issues")
        return {"status": "warning", "detail": "Config issues detected"}
    status = "ok"
    write_metric(client, "config", "ok", "Config valid")
    return {"status": "ok", "detail": "Config valid"}

def collect_all(client: str) -> dict:
    return {
        "gateway":   collect_gateway(client),
        "crons":     collect_crons(client),
        "heartbeat": collect_heartbeat(client),
        "sessions":  collect_sessions(client),
        "config":    collect_config(client),
    }
