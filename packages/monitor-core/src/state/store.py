import sqlite3, json, time, os
from dataclasses import dataclass
from typing import Optional

DB_PATH = os.path.expanduser("~/.originclaw/monitor.db")

@dataclass
class MetricRecord:
    client: str
    component: str
    status: str
    value: str
    latency_ms: Optional[float]
    checked_at: float

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT NOT NULL,
        component TEXT NOT NULL,
        status TEXT NOT NULL,
        value TEXT,
        latency_ms REAL,
        checked_at REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_metrics_client_component ON metrics(client, component);
    CREATE INDEX IF NOT EXISTS idx_metrics_checked_at ON metrics(checked_at);
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client TEXT NOT NULL,
        component TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        fired_at REAL NOT NULL,
        resolved_at REAL,
        notified INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()

def write_metric(client: str, component: str, status: str, value: str = "", latency_ms: float = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO metrics (client, component, status, value, latency_ms, checked_at) VALUES (?,?,?,?,?,?)",
        (client, component, status, value, latency_ms, time.time())
    )
    conn.commit()
    conn.close()

def get_latest(client: str, component: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM metrics WHERE client=? AND component=? ORDER BY checked_at DESC LIMIT 1",
        (client, component)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_history(client: str, component: str, hours: int = 24) -> list:
    conn = get_conn()
    since = time.time() - hours * 3600
    rows = conn.execute(
        "SELECT * FROM metrics WHERE client=? AND component=? AND checked_at>? ORDER BY checked_at DESC",
        (client, component, since)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def write_alert(client: str, component: str, severity: str, message: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO alerts (client, component, severity, message, fired_at) VALUES (?,?,?,?,?)",
        (client, component, severity, message, time.time())
    )
    conn.commit()
    conn.close()

def get_active_alerts(client: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM alerts WHERE client=? AND resolved_at IS NULL ORDER BY fired_at DESC",
        (client,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
