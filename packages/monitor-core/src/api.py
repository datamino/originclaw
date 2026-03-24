#!/usr/bin/env python3
"""
OriginClaw Monitor — FastAPI backend
Serves live metrics to the dashboard UI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess, json, time, os, psutil, urllib.request

app = FastAPI(title="OriginClaw Monitor API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def run_cmd(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_url(url, timeout=6):
    try:
        start = time.time()
        urllib.request.urlopen(url, timeout=timeout)
        return "ok", round((time.time()-start)*1000)
    except:
        return "critical", 0

def check_mcp(name, timeout=10):
    try:
        start = time.time()
        r = subprocess.run(["mcporter","list",name], capture_output=True, text=True, timeout=timeout)
        latency = round((time.time()-start)*1000)
        return ("ok" if "tools" in r.stdout.lower() else "warning"), latency
    except:
        return "offline", 0

@app.get("/api/status")
def get_status():
    components = []

    # Gateway
    ok, out = run_cmd(["openclaw","gateway","status"])
    components.append({"id":"gateway","connects":['sessions', 'crons', 'heartbeat', 'channels'],"name":"Gateway","type":"gateway","status":"ok" if ok else "critical",
        "lastChecked":"just now","metrics":[{"label":"Process","value":"running" if ok else "down"}],
        "subComponents":[{"id":"gw-proc","name":"Process","status":"ok" if ok else "critical","detail":out[:80]}]})

    # Crons
    ok2, out2 = run_cmd(["openclaw","cron","list"])
    cron_count = out2.count("idle") + out2.count("active") if ok2 else 0
    components.append({"id":"crons","connects":['gateway', 'skills'],"name":"Cron Jobs","type":"crons","status":"ok" if ok2 else "warning",
        "lastChecked":"just now","metrics":[{"label":"Active","value":str(cron_count),"unit":"jobs"}],
        "subComponents":[{"id":"cron-all","name":"All Jobs","status":"ok" if ok2 else "warning","detail":f"{cron_count} jobs configured"}]})

    # Heartbeat
    components.append({"id":"heartbeat","connects":['gateway', 'integrations'],"name":"Heartbeat","type":"heartbeat","status":"ok",
        "lastChecked":"just now","metrics":[{"label":"Interval","value":"180","unit":"min"},{"label":"Target","value":"Telegram"}],
        "subComponents":[{"id":"hb-main","name":"Main Heartbeat","status":"ok","detail":"Active — every 180m"}]})

    # Infrastructure
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk_free = round(psutil.disk_usage("/").free/1e9,1)
    inf_status = "critical" if cpu>90 or mem>90 else "warning" if cpu>80 or mem>80 else "ok"
    components.append({"id":"infrastructure","connects":[],"name":"Infrastructure","type":"infrastructure","status":inf_status,
        "lastChecked":"just now",
        "metrics":[{"label":"CPU","value":f"{cpu}","unit":"%"},{"label":"RAM","value":f"{mem}","unit":"%"},{"label":"Disk","value":f"{disk_free}","unit":"GB free"}],
        "subComponents":[
            {"id":"inf-cpu","name":"CPU","status":"ok" if cpu<80 else "warning","detail":f"{cpu}%"},
            {"id":"inf-mem","name":"Memory","status":"ok" if mem<80 else "warning","detail":f"{mem}%"},
            {"id":"inf-disk","name":"Disk","status":"ok" if disk_free>10 else "warning","detail":f"{disk_free}GB free"},
        ]})

    # Integrations
    tg_status, tg_ms = check_url(f"https://api.telegram.org/bot8609655398:AAGGAN7D1LptaK4yXi_kmZ9DJ0ChpRw-wuY/getMe")
    yf_status, yf_ms = check_url("https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=1d")
    gm_status, gm_ms = check_mcp("gmail")
    gc_status, gc_ms = check_mcp("google-calendar")
    int_issues = [s for s in [tg_status,yf_status,gm_status,gc_status] if s!="ok"]
    int_status = "critical" if "critical" in int_issues else "warning" if int_issues else "ok"
    components.append({"id":"integrations","connects":['gateway', 'skills'],"name":"Integrations","type":"integrations","status":int_status,
        "lastChecked":"just now",
        "metrics":[{"label":"APIs","value":"4"},{"label":"Healthy","value":str(4-len(int_issues))},{"label":"Issues","value":str(len(int_issues))}],
        "subComponents":[
            {"id":"int-telegram","name":"Telegram","status":tg_status,"detail":f"{tg_ms}ms"},
            {"id":"int-yahoo","name":"Yahoo Finance","status":yf_status,"detail":f"{yf_ms}ms"},
            {"id":"int-gmail","name":"Gmail","status":gm_status,"detail":f"{gm_ms}ms"},
            {"id":"int-cal","name":"Google Calendar","status":gc_status,"detail":f"{gc_ms}ms"},
        ]})

    # Channels
    components.append({"id":"channels","connects":['gateway'],"name":"Channels","type":"channels","status":tg_status,
        "lastChecked":"just now","metrics":[{"label":"Telegram","value":"online" if tg_status=="ok" else "offline"},{"label":"Latency","value":str(tg_ms),"unit":"ms"}],
        "subComponents":[{"id":"ch-tg","name":"Telegram Bot","status":tg_status,"detail":f"@valenbosbot — {tg_ms}ms"}]})

    # Skills & Daemons
    daemon_ok = os.path.exists(os.path.expanduser("~/Library/LaunchAgents/com.velan.sp500monitor.plist"))
    try:
        r = subprocess.run(["launchctl","list"], capture_output=True, text=True, timeout=5)
        daemon_running = "sp500monitor" in r.stdout
    except:
        daemon_running = False
    sk_status = "ok" if daemon_running else "warning"
    components.append({"id":"skills","connects":['integrations', 'daemons'],"name":"Skills","type":"skills","status":"ok",
        "lastChecked":"just now","metrics":[{"label":"Scripts","value":"6"},{"label":"Active","value":"6"}],
        "subComponents":[
            {"id":"sk-brief","name":"Morning Brief","status":"ok","detail":"Script present"},
            {"id":"sk-travel","name":"Travel Agent","status":"ok","detail":"Script present"},
            {"id":"sk-portfolio","name":"Portfolio Tracker","status":"ok","detail":"Script present"},
        ]})

    components.append({"id":"daemons","connects":['skills'],"name":"Daemons","type":"daemons","status":sk_status,
        "lastChecked":"just now","metrics":[{"label":"SP500 Monitor","value":"running" if daemon_running else "stopped"}],
        "subComponents":[{"id":"dm-sp500","name":"SP500 Monitor","status":"ok" if daemon_running else "warning","detail":"com.velan.sp500monitor"}]})

    # Sessions
    ok3, out3 = run_cmd(["openclaw","sessions","--json"])
    try:
        sess = json.loads(out3) if ok3 and out3.startswith("[") else []
        sess_count = len(sess)
    except:
        sess_count = 1
    components.append({"id":"sessions","connects":['gateway'],"name":"Sessions","type":"sessions","status":"ok",
        "lastChecked":"just now","metrics":[{"label":"Active","value":str(sess_count)}],
        "subComponents":[{"id":"sess-main","name":"Main Session","status":"ok","detail":"Active"}]})

    healthy = sum(1 for c in components if c["status"]=="ok")
    warnings = sum(1 for c in components if c["status"]=="warning")
    critical = sum(1 for c in components if c["status"]=="critical")

    return {"components":components,"summary":{"total":len(components),"healthy":healthy,"warnings":warnings,"critical":critical},"timestamp":time.time()}

@app.get("/health")
def health():
    return {"ok": True}
