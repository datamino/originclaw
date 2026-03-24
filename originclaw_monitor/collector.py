#!/usr/bin/env python3
"""
Universal collector — auto-discovers and checks all OpenClaw components.
Works on any deployment without manual config.
"""
import subprocess, json, time, os
import psutil

def check_gateway(port: int = 18789) -> dict:
    try:
        r = subprocess.run(["curl","-sf","--max-time","2",f"http://localhost:{port}/health"],
            capture_output=True, text=True, timeout=3)
        ok = r.returncode == 0 and ("ok" in r.stdout or "live" in r.stdout)
        return {"status":"ok" if ok else "critical", "detail": "Running" if ok else "Not responding", "latency_ms": 0}
    except:
        return {"status":"critical","detail":"Connection refused"}

def check_infrastructure() -> dict:
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk_free = round(psutil.disk_usage("/").free / 1e9, 1)
    status = "critical" if cpu>90 or mem>90 else "warning" if cpu>80 or mem>80 else "ok"
    return {"status": status, "cpu": cpu, "memory": mem, "disk_free_gb": disk_free,
            "detail": f"CPU:{cpu}% RAM:{mem}% Disk:{disk_free}GB free"}

def check_all_crons() -> dict:
    try:
        r = subprocess.run(["openclaw","cron","list"], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return {"status":"warning","detail":"Could not list crons","jobs":[]}
        total = r.stdout.count("idle") + r.stdout.count("active")
        errors = r.stdout.count("error")
        status = "warning" if errors > 0 else "ok"
        return {"status":status,"detail":f"{total} jobs, {errors} errors","total":total,"errors":errors}
    except:
        return {"status":"warning","detail":"openclaw cron list failed"}

def check_heartbeat(expected_interval_min: int = 30) -> dict:
    try:
        r = subprocess.run(["openclaw","status","--json"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            data = json.loads(r.stdout)
            last_ms = data.get("heartbeat",{}).get("lastRunAtMs", 0)
            if last_ms:
                elapsed_min = (time.time()*1000 - last_ms) / 60000
                if elapsed_min > expected_interval_min * 2.5:
                    return {"status":"warning","detail":f"Last run {round(elapsed_min)}m ago (expected ≤{expected_interval_min*2}m)"}
                return {"status":"ok","detail":f"Last run {round(elapsed_min)}m ago"}
        return {"status":"ok","detail":"Active"}
    except:
        return {"status":"ok","detail":"Active"}

def check_mcp_servers(server_names: list) -> dict:
    results = {}
    for name in server_names[:10]:  # cap at 10 to avoid slowdown
        try:
            start = time.time()
            r = subprocess.run(["mcporter","list",name], capture_output=True, text=True, timeout=8)
            latency = round((time.time()-start)*1000)
            ok = "tools" in r.stdout.lower() or r.returncode == 0
            results[name] = {"status":"ok" if ok else "warning","latency_ms":latency}
        except:
            results[name] = {"status":"offline","latency_ms":0}
    total = len(results)
    issues = sum(1 for v in results.values() if v["status"] != "ok")
    return {"status":"warning" if issues else "ok","detail":f"{total-issues}/{total} healthy",
            "servers":results,"issues":issues}

def check_daemons(daemon_names: list) -> dict:
    results = {}
    try:
        r = subprocess.run(["launchctl","list"], capture_output=True, text=True, timeout=5)
        running = r.stdout
    except:
        running = ""
    for name in daemon_names:
        short = name.split(".")[-1]
        alive = name in running or short in running
        results[name] = {"status":"ok" if alive else "critical","detail":"Running" if alive else "Not running"}
    issues = sum(1 for v in results.values() if v["status"] != "ok")
    return {"status":"critical" if issues else "ok","detail":f"{len(daemon_names)-issues}/{len(daemon_names)} running","daemons":results}

def check_network() -> dict:
    try:
        start = time.time()
        r = subprocess.run(["curl","-sf","--max-time","3","https://1.1.1.1"],
            capture_output=True, timeout=4)
        latency = round((time.time()-start)*1000)
        return {"status":"ok","detail":f"{latency}ms","latency_ms":latency}
    except:
        return {"status":"critical","detail":"No internet connectivity"}

def collect_all(discovered: dict, config: dict) -> dict:
    results = {}
    results["gateway"]        = check_gateway(discovered.get("gateway_port", 18789))
    results["infrastructure"] = check_infrastructure()
    results["network"]        = check_network()
    results["crons"]          = check_all_crons()
    results["heartbeat"]      = check_heartbeat(discovered.get("heartbeat",{}).get("interval_min", 30))
    if discovered.get("mcp_servers"):
        mcp = check_mcp_servers(discovered["mcp_servers"])
        results["integrations"] = mcp
    if discovered.get("daemons"):
        results["daemons"] = check_daemons(discovered["daemons"])
    return results
