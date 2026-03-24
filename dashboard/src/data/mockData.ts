export type Status = 'ok' | 'warning' | 'critical' | 'offline';

export interface Metric { label: string; value: string; unit?: string; trend?: 'up'|'down'|'stable'; }
export interface SubComponent { id: string; name: string; status: Status; detail: string; }
export interface Component {
  id: string; type: string; name: string; status: Status;
  description: string; metrics: Metric[]; subComponents: SubComponent[];
  lastChecked: string; uptime?: string; connects: string[];
}

export const components: Component[] = [
  {
    id: 'gateway', type: 'gateway', name: 'Gateway', status: 'ok',
    description: 'OpenClaw core gateway — routes all messages and manages agent sessions',
    uptime: '3d 14h 22m', lastChecked: '12s ago', connects: ['sessions','crons','heartbeat','channels'],
    metrics: [
      { label: 'Uptime', value: '99.98', unit: '%', trend: 'stable' },
      { label: 'Sessions', value: '3', unit: 'active' },
      { label: 'Latency', value: '42', unit: 'ms', trend: 'stable' },
      { label: 'Queue', value: '0', unit: 'pending' },
    ],
    subComponents: [
      { id: 'gw-process', name: 'Process', status: 'ok', detail: 'PID 82442 — running' },
      { id: 'gw-config', name: 'Config', status: 'ok', detail: 'openclaw.json valid' },
      { id: 'gw-auth', name: 'Auth', status: 'ok', detail: 'Token valid' },
    ]
  },
  {
    id: 'sessions', type: 'sessions', name: 'Sessions', status: 'ok',
    description: 'Active agent sessions — main, cron, and DM sessions',
    lastChecked: '8s ago', connects: ['gateway'],
    metrics: [
      { label: 'Active', value: '3', trend: 'stable' },
      { label: 'Context', value: '124k', unit: 'tokens' },
    ],
    subComponents: [
      { id: 'sess-main', name: 'Main Session', status: 'ok', detail: 'Active — last message 4m ago' },
      { id: 'sess-cron', name: 'Cron Sessions', status: 'ok', detail: '4 isolated sessions available' },
      { id: 'sess-memory', name: 'Memory', status: 'ok', detail: 'Compaction: safeguard mode' },
    ]
  },
  {
    id: 'crons', type: 'crons', name: 'Cron Jobs', status: 'ok',
    description: 'Scheduled tasks — morning brief, S&P market checks',
    lastChecked: '1m ago', connects: ['gateway','skills'],
    metrics: [
      { label: 'Total', value: '4', unit: 'jobs' },
      { label: 'Active', value: '4' },
      { label: 'Next run', value: '38m' },
    ],
    subComponents: [
      { id: 'cron-brief', name: 'Morning Brief', status: 'ok', detail: 'Daily 8AM ET — last: 8:03 AM' },
      { id: 'cron-sp500-open', name: 'SP500 Open', status: 'ok', detail: '9:30 AM ET Mon-Fri' },
      { id: 'cron-sp500-mid', name: 'SP500 Midday', status: 'ok', detail: '1:00 PM ET Mon-Fri' },
      { id: 'cron-sp500-close', name: 'SP500 Close', status: 'ok', detail: '4:30 PM ET — in 38m' },
    ]
  },
  {
    id: 'heartbeat', type: 'heartbeat', name: 'Heartbeat', status: 'ok',
    description: 'Periodic agent runs — India deal monitoring, background awareness',
    lastChecked: '2m ago', connects: ['gateway','integrations'],
    metrics: [
      { label: 'Interval', value: '180', unit: 'min' },
      { label: 'Last run', value: '14m', unit: 'ago' },
      { label: 'Target', value: 'Telegram' },
    ],
    subComponents: [
      { id: 'hb-india', name: 'India Deal Watch', status: 'ok', detail: 'Last check: 14m ago — no new emails' },
      { id: 'hb-sp500', name: 'S&P Check', status: 'ok', detail: 'SPY $655.41 — not triggered' },
    ]
  },
  {
    id: 'channels', type: 'channels', name: 'Channels', status: 'ok',
    description: 'Message delivery — Telegram bot active',
    lastChecked: '30s ago', connects: ['gateway'],
    metrics: [
      { label: 'Telegram', value: 'online' },
      { label: 'Latency', value: '180', unit: 'ms' },
      { label: 'Success rate', value: '100', unit: '%' },
    ],
    subComponents: [
      { id: 'ch-telegram', name: 'Telegram', status: 'ok', detail: '@valenbosbot — active' },
      { id: 'ch-delivery', name: 'Delivery', status: 'ok', detail: 'Last delivered: 4m ago' },
    ]
  },
  {
    id: 'integrations', type: 'integrations', name: 'Integrations', status: 'warning',
    description: 'External API connections — Gmail, Calendar, market data, news, search',
    lastChecked: '15s ago', connects: ['gateway','skills'],
    metrics: [
      { label: 'Total', value: '7', unit: 'APIs' },
      { label: 'Healthy', value: '6' },
      { label: 'Warnings', value: '1' },
    ],
    subComponents: [
      { id: 'int-gmail', name: 'Gmail', status: 'ok', detail: '210ms — read/write active' },
      { id: 'int-cal', name: 'Google Calendar', status: 'ok', detail: '180ms — connected' },
      { id: 'int-yahoo', name: 'Yahoo Finance', status: 'ok', detail: '95ms — SPY $655.41' },
      { id: 'int-massive', name: 'Massive API', status: 'ok', detail: '340ms — live' },
      { id: 'int-marketaux', name: 'Marketaux', status: 'ok', detail: '290ms — news feed active' },
      { id: 'int-gdelt', name: 'GDELT', status: 'ok', detail: '520ms — geo-intelligence active' },
      { id: 'int-brave', name: 'Brave Search', status: 'warning', detail: 'MCP offline — direct API fallback active' },
    ]
  },
  {
    id: 'skills', type: 'skills', name: 'Skills', status: 'ok',
    description: 'Automation scripts — market monitor, morning brief, travel agent, portfolio tracker',
    lastChecked: '47s ago', connects: ['integrations','daemons'],
    metrics: [
      { label: 'Total', value: '6', unit: 'skills' },
      { label: 'Active', value: '6' },
    ],
    subComponents: [
      { id: 'sk-brief', name: 'Morning Brief', status: 'ok', detail: 'Last run: 8:03 AM — delivered' },
      { id: 'sk-sp500', name: 'Market Monitor', status: 'ok', detail: 'Every 30s — SPY $655.41' },
      { id: 'sk-travel', name: 'Travel Agent', status: 'ok', detail: 'On-demand — ready' },
      { id: 'sk-portfolio', name: 'Portfolio Tracker', status: 'ok', detail: 'On-demand — no new reports' },
      { id: 'sk-dubai', name: 'Dubai Tracker', status: 'ok', detail: '0/90 days logged' },
      { id: 'sk-yahoo', name: 'Yahoo Finance', status: 'ok', detail: 'Real-time quotes active' },
    ]
  },
  {
    id: 'daemons', type: 'daemons', name: 'Daemons', status: 'ok',
    description: 'Always-on background processes on the host machine',
    lastChecked: '47s ago', connects: ['skills'],
    metrics: [
      { label: 'Running', value: '1' },
      { label: 'Uptime', value: '14h' },
      { label: 'Last check', value: '47s ago' },
    ],
    subComponents: [
      { id: 'dm-sp500', name: 'SP500 Monitor', status: 'ok', detail: 'com.velan.sp500monitor — PID 27364' },
    ]
  },
];

export const nodePositions: Record<string, {x:number;y:number}> = {
  gateway:      { x: 460, y: 180 },
  sessions:     { x: 160, y: 60  },
  crons:        { x: 760, y: 60  },
  heartbeat:    { x: 160, y: 320 },
  channels:     { x: 760, y: 320 },
  integrations: { x: 460, y: 420 },
  skills:       { x: 160, y: 560 },
  daemons:      { x: 760, y: 560 },
};

export const statusColors: Record<Status, string> = {
  ok: '#10b981', warning: '#f59e0b', critical: '#ef4444', offline: '#6b7280'
};

export const typeIcons: Record<string, string> = {
  gateway: '⬡', sessions: '◈', crons: '⏱', heartbeat: '♡',
  channels: '◎', integrations: '⬢', skills: '◆', daemons: '⚙',
};

export const statusBg: Record<Status, string> = {
  ok: 'rgba(5,150,105,0.08)', warning: 'rgba(217,119,6,0.08)',
  critical: 'rgba(220,38,38,0.08)', offline: 'rgba(148,163,184,0.08)'
};
export const statusBorder: Record<Status, string> = {
  ok: 'rgba(5,150,105,0.25)', warning: 'rgba(217,119,6,0.3)',
  critical: 'rgba(220,38,38,0.3)', offline: 'rgba(148,163,184,0.2)'
};
export const typeGradients: Record<string, string> = {
  gateway: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  sessions: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  crons: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  heartbeat: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  channels: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  integrations: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  skills: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
  daemons: 'linear-gradient(135deg,#1a1f2e,#0f1623)',
};
