import subprocess, urllib.request, time, json
from ..state.store import write_metric

def check_api(url: str, timeout: int = 8) -> tuple[str, float]:
    try:
        start = time.time()
        urllib.request.urlopen(url, timeout=timeout)
        latency = round((time.time() - start) * 1000)
        return "ok", latency
    except Exception:
        return "critical", 0

def check_mcp(name: str, timeout: int = 10) -> tuple[str, float]:
    try:
        start = time.time()
        r = subprocess.run(["mcporter", "call", f"{name}.health_check"], capture_output=True, text=True, timeout=timeout)
        latency = round((time.time() - start) * 1000)
        return ("ok" if r.returncode == 0 else "warning"), latency
    except Exception:
        # Fall back to mcporter list check
        try:
            r = subprocess.run(["mcporter", "list", name], capture_output=True, text=True, timeout=timeout)
            latency = round((time.time() - time.time()) * 1000)
            return ("ok" if "tools" in r.stdout.lower() else "warning"), 0
        except Exception:
            return "offline", 0

def collect_integrations(client: str) -> dict:
    results = {}

    # Yahoo Finance
    status, latency = check_api("https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&range=1d")
    write_metric(client, "yahoo-finance", status, f"{latency}ms", latency)
    results["yahoo-finance"] = {"status": status, "latency_ms": latency}

    # Marketaux
    token = "p68Dk00MaqC3A3KQfCKNVzJ8LT4S7UYLW53oLIKL"
    status, latency = check_api(f"https://api.marketaux.com/v1/news/all?language=en&limit=1&api_token={token}")
    write_metric(client, "marketaux", status, f"{latency}ms", latency)
    results["marketaux"] = {"status": status, "latency_ms": latency}

    # Massive API
    key = "K8tQcabsrlTqvqxcD3Pvoaz4Inl4yIgi"
    status, latency = check_api(f"https://api.massive.com/v3/reference/tickers/SPY?apiKey={key}")
    write_metric(client, "massive-api", status, f"{latency}ms", latency)
    results["massive-api"] = {"status": status, "latency_ms": latency}

    # Gmail MCP
    status, latency = check_mcp("gmail")
    write_metric(client, "gmail", status, f"{latency}ms", latency)
    results["gmail"] = {"status": status, "latency_ms": latency}

    # Google Calendar MCP
    status, latency = check_mcp("google-calendar")
    write_metric(client, "google-calendar", status, f"{latency}ms", latency)
    results["google-calendar"] = {"status": status, "latency_ms": latency}

    # Telegram bot
    tg_token = "8609655398:AAGGAN7D1LptaK4yXi_kmZ9DJ0ChpRw-wuY"
    status, latency = check_api(f"https://api.telegram.org/bot{tg_token}/getMe")
    write_metric(client, "telegram", status, f"{latency}ms", latency)
    results["telegram"] = {"status": status, "latency_ms": latency}

    return results
