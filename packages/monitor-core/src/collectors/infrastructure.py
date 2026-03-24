import psutil, subprocess, urllib.request, time
from ..state.store import write_metric

def collect_infrastructure(client: str) -> dict:
    results = {}

    # CPU
    cpu = psutil.cpu_percent(interval=1)
    status = "critical" if cpu > 90 else "warning" if cpu > 80 else "ok"
    write_metric(client, "cpu", status, f"{cpu}%")
    results["cpu"] = {"status": status, "value": f"{cpu}%"}

    # Memory
    mem = psutil.virtual_memory()
    mem_pct = mem.percent
    status = "critical" if mem_pct > 90 else "warning" if mem_pct > 80 else "ok"
    write_metric(client, "memory", status, f"{mem_pct}%")
    results["memory"] = {"status": status, "value": f"{mem_pct}%"}

    # Disk
    disk = psutil.disk_usage("/")
    free_gb = round(disk.free / 1e9, 1)
    status = "critical" if free_gb < 5 else "warning" if free_gb < 10 else "ok"
    write_metric(client, "disk", status, f"{free_gb}GB free")
    results["disk"] = {"status": status, "value": f"{free_gb}GB free"}

    # Network
    try:
        start = time.time()
        urllib.request.urlopen("https://1.1.1.1", timeout=3)
        latency = round((time.time() - start) * 1000)
        status = "ok"
        write_metric(client, "network", "ok", f"{latency}ms", latency)
        results["network"] = {"status": "ok", "value": f"{latency}ms"}
    except Exception:
        write_metric(client, "network", "critical", "unreachable")
        results["network"] = {"status": "critical", "value": "unreachable"}

    return results
