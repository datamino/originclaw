# OriginClaw Monitor

> Observability for OpenClaw agentic AI deployments

Monitor every component of your OpenClaw deployment — gateway, crons, heartbeat, integrations, skills, and daemons. Get instant alerts when anything breaks.

## Install

```bash
pip install originclaw-monitor
```

## Quick Start

```bash
# 1. Configure (auto-discovers your OpenClaw)
originclaw-monitor init

# 2. Start watchdog (instant gateway alerts)
originclaw-monitor watchdog

# 3. Check status
originclaw-monitor status

# 4. Send test alert
originclaw-monitor test-alert
```

## What It Monitors

| Layer | Components |
|---|---|
| Infrastructure | CPU, memory, disk, network |
| OpenClaw Core | Gateway, crons, heartbeat, sessions |
| Integrations | Gmail, Calendar, APIs, MCP servers |
| Skills | Python daemons, scripts |
| Business | Morning brief delivery, S&P alerts |

## Alert Channels

- **Email** via Resend API (free tier)
- **Telegram** via bot
- **Discord** via webhook (coming soon)

## Dashboard

Premium React dashboard with live topology view of all components.

```bash
originclaw-monitor dashboard
```

Open: http://localhost:5173

## Watchdog

Independent gateway watchdog — fires alert the moment OpenClaw goes down.

```bash
originclaw-monitor watchdog
```

- Checks every 1 second
- Fires on first failure — no delay
- Recovery alert when gateway comes back

## License

MIT
