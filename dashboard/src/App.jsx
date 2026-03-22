import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from './api';
import {
  Send, Users, Wallet, Activity, Shield, ScrollText,
  Plus, X, Play, Pause, ChevronRight, ExternalLink,
  CircleDollarSign, Clock, CheckCircle2, XCircle, AlertTriangle,
  Bot, Loader2, ArrowUpRight, ArrowDownRight,
} from 'lucide-react';

// ─── Hooks ──────────────────────────────────────────────────────────

function usePolling(fetcher, intervalMs = 4000) {
  const [data, setData] = useState(null);
  const cb = useCallback(async () => {
    try { setData(await fetcher()); } catch {}
  }, [fetcher]);
  useEffect(() => { cb(); const id = setInterval(cb, intervalMs); return () => clearInterval(id); }, [cb, intervalMs]);
  return [data, cb];
}

// ─── Small components ───────────────────────────────────────────────

function Badge({ children, color = 'accent' }) {
  const map = {
    accent: 'bg-accent/15 text-accent-bright border-accent/20',
    danger: 'bg-danger/15 text-red-400 border-danger/20',
    warn:   'bg-warn/15 text-amber-400 border-warn/20',
    info:   'bg-info/15 text-blue-400 border-info/20',
    muted:  'bg-surface-3 text-zinc-400 border-surface-4',
  };
  return <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${map[color] || map.muted}`}>{children}</span>;
}

function Card({ children, className = '' }) {
  return <div className={`bg-surface-1 border border-surface-3 rounded-2xl ${className}`}>{children}</div>;
}

function CardHeader({ icon: Icon, title, children }) {
  return (
    <div className="flex items-center justify-between px-5 py-4 border-b border-surface-3">
      <div className="flex items-center gap-2.5">
        {Icon && <Icon className="w-4 h-4 text-zinc-500" />}
        <h3 className="text-sm font-semibold text-zinc-200">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Stat({ label, value, sub }) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] text-zinc-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-lg font-semibold text-zinc-100 truncate">{value}</p>
      {sub && <p className="text-[11px] text-zinc-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function ProgressBar({ pct, color = 'bg-accent' }) {
  return (
    <div className="h-1 w-full bg-surface-3 rounded-full overflow-hidden">
      <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
    </div>
  );
}

const statusColor = (s) => s === 'active' ? 'accent' : s === 'completed' ? 'info' : 'danger';

// ─── Panels ─────────────────────────────────────────────────────────

function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput('');
    setMessages(m => [...m, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await api.chat(msg);
      setMessages(m => [...m, { role: 'ai', content: res.response || res.error, tools: res.tool_calls }]);
    } catch (e) {
      setMessages(m => [...m, { role: 'ai', content: 'Connection error', tools: 0 }]);
    }
    setLoading(false);
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader icon={Bot} title="Agent Console">
        <Badge color="accent">LangGraph + WDK</Badge>
      </CardHeader>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-zinc-600 gap-2">
            <Bot className="w-8 h-8" />
            <p className="text-sm">Ask the agent to check balances, pay contributors, review PRs...</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-accent/15 text-accent-bright rounded-br-md'
                : 'bg-surface-2 text-zinc-300 rounded-bl-md border border-surface-3'
            }`}>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.tools > 0 && <p className="text-[10px] text-zinc-500 mt-1">{m.tools} tool calls</p>}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-zinc-500 text-sm">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Thinking...
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="p-3 border-t border-surface-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="e.g. Check Polygon USDT balance..."
            className="flex-1 bg-surface-2 border border-surface-4 rounded-xl px-4 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40 transition-colors"
          />
          <button onClick={send} disabled={loading || !input.trim()}
            className="bg-accent hover:bg-accent-bright text-surface-0 rounded-xl px-4 py-2.5 font-medium text-sm disabled:opacity-30 transition-colors">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </Card>
  );
}

function ContributorsPanel() {
  const [data, refresh] = usePolling(api.getContributors, 5000);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ github_username: '', wallet_address: '', role: 'developer', name: '' });

  const submit = async (e) => {
    e.preventDefault();
    await api.addContributor(form);
    setForm({ github_username: '', wallet_address: '', role: 'developer', name: '' });
    setShow(false);
    refresh();
  };

  const contributors = data || [];

  return (
    <Card>
      <CardHeader icon={Users} title={`Contributors (${contributors.length})`}>
        <button onClick={() => setShow(!show)} className="text-zinc-500 hover:text-accent transition-colors">
          {show ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
        </button>
      </CardHeader>
      {show && (
        <form onSubmit={submit} className="p-4 border-b border-surface-3 space-y-2">
          <input value={form.github_username} onChange={e => setForm(f => ({ ...f, github_username: e.target.value }))}
            placeholder="GitHub username" required className="w-full bg-surface-2 border border-surface-4 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40" />
          <input value={form.wallet_address} onChange={e => setForm(f => ({ ...f, wallet_address: e.target.value }))}
            placeholder="0x wallet address" required className="w-full bg-surface-2 border border-surface-4 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-accent/40" />
          <div className="flex gap-2">
            <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
              className="flex-1 bg-surface-2 border border-surface-4 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-accent/40">
              <option value="lead">Lead ($75/hr)</option>
              <option value="developer">Developer ($50/hr)</option>
              <option value="reviewer">Reviewer ($30/hr)</option>
              <option value="designer">Designer ($40/hr)</option>
              <option value="intern">Intern ($15/hr)</option>
            </select>
            <button type="submit" className="bg-accent hover:bg-accent-bright text-surface-0 rounded-lg px-4 py-2 text-sm font-medium transition-colors">Add</button>
          </div>
        </form>
      )}
      <div className="divide-y divide-surface-3 max-h-72 overflow-y-auto">
        {contributors.length === 0 ? (
          <p className="text-sm text-zinc-600 p-5 text-center">No contributors yet</p>
        ) : contributors.map(c => (
          <div key={c.id} className="px-5 py-3 flex items-center gap-3 hover:bg-surface-2/50 transition-colors">
            <div className="w-8 h-8 rounded-full bg-surface-3 flex items-center justify-center text-xs font-mono text-zinc-400">
              {c.github_username.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-zinc-200 truncate">@{c.github_username}</span>
                <Badge color={c.status === 'active' ? 'accent' : 'danger'}>{c.role_label}</Badge>
              </div>
              <p className="text-[11px] text-zinc-500 font-mono truncate">{c.wallet_address}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-sm font-semibold text-zinc-200">${c.total_earned.toFixed(2)}</p>
              <p className="text-[10px] text-zinc-500">{c.total_payments} payouts</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function StreamsPanel() {
  const [data, refresh] = usePolling(api.getStreams, 3000);
  const streams = data || [];

  return (
    <Card>
      <CardHeader icon={CircleDollarSign} title={`Streams (${streams.length})`} />
      <div className="divide-y divide-surface-3 max-h-80 overflow-y-auto">
        {streams.length === 0 ? (
          <p className="text-sm text-zinc-600 p-5 text-center">No active streams</p>
        ) : streams.map(s => (
          <div key={s.id} className="px-5 py-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono text-zinc-300">#{s.id}</span>
                <Badge color={statusColor(s.status)}>{s.status}</Badge>
              </div>
              <span className="text-sm font-semibold text-zinc-200">${s.total_amount.toFixed(2)}</span>
            </div>
            <p className="text-[11px] text-zinc-500 font-mono truncate">{s.recipient}</p>
            {s.reason && <p className="text-[11px] text-zinc-400">{s.reason}</p>}
            <div className="space-y-1">
              <ProgressBar pct={s.progress?.paid_pct || 0} />
              <div className="flex justify-between text-[10px] text-zinc-500">
                <span>${s.amount_paid.toFixed(2)} paid</span>
                <span>{(s.progress?.paid_pct || 0).toFixed(0)}%</span>
              </div>
            </div>
            {s.status === 'active' && (
              <button onClick={async () => { await api.cancelStream(s.id); refresh(); }}
                className="text-[11px] text-red-400 hover:text-red-300 transition-colors">Cancel stream</button>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
}

function PolicyPanel() {
  const [data, refresh] = usePolling(api.getPolicy, 5000);
  if (!data) return null;

  return (
    <Card>
      <CardHeader icon={Shield} title="Treasury Policy">
        {data.paused ? (
          <button onClick={async () => { await api.resume(); refresh(); }}
            className="flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-warn/10 border border-warn/20 rounded-lg px-3 py-1.5 hover:bg-warn/20 transition-colors">
            <Play className="w-3 h-3" /> Resume
          </button>
        ) : (
          <button onClick={async () => { await api.pause(); refresh(); }}
            className="flex items-center gap-1.5 text-xs font-medium text-zinc-400 bg-surface-3 rounded-lg px-3 py-1.5 hover:bg-surface-4 transition-colors">
            <Pause className="w-3 h-3" /> Pause
          </button>
        )}
      </CardHeader>
      <div className="p-5 grid grid-cols-2 gap-4">
        <Stat label="Daily Limit" value={`$${data.max_daily_spend}`} sub={`$${data.daily_spent?.toFixed(2) || '0.00'} spent today`} />
        <Stat label="Single Tx Max" value={`$${data.max_single_payment}`} />
        <Stat label="Reserve Floor" value={`$${data.min_balance}`} />
        <Stat label="Status" value={data.paused ? 'PAUSED' : 'ACTIVE'} sub={data.pause_reason || 'Operational'} />
      </div>
    </Card>
  );
}

function AuditPanel() {
  const [data] = usePolling(api.getAudit, 3000);
  const entries = data || [];

  const typeIcon = (t) => {
    if (t.includes('SUCCESS')) return <CheckCircle2 className="w-3 h-3 text-accent" />;
    if (t.includes('FAIL') || t.includes('REJECT')) return <XCircle className="w-3 h-3 text-danger" />;
    if (t.includes('PAUSE')) return <AlertTriangle className="w-3 h-3 text-warn" />;
    return <ChevronRight className="w-3 h-3 text-zinc-600" />;
  };

  const typeColor = (t) => {
    if (t.includes('SUCCESS') || t.includes('REGISTER') || t.includes('RESUME')) return 'text-accent';
    if (t.includes('FAIL') || t.includes('REJECT') || t.includes('CANCEL') || t.includes('SUSPEND')) return 'text-red-400';
    if (t.includes('PAUSE')) return 'text-amber-400';
    return 'text-zinc-500';
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader icon={ScrollText} title="Audit Trail" />
      <div className="flex-1 overflow-y-auto min-h-0">
        {entries.length === 0 ? (
          <p className="text-sm text-zinc-600 p-5 text-center">No activity yet</p>
        ) : (
          <div className="divide-y divide-surface-3">
            {entries.slice().reverse().map(e => (
              <div key={e.id} className="px-4 py-2.5 flex items-start gap-2.5 hover:bg-surface-2/30 transition-colors">
                <div className="mt-0.5 shrink-0">{typeIcon(e.entry_type)}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-[11px] font-mono font-medium ${typeColor(e.entry_type)}`}>{e.entry_type}</span>
                    <span className="text-[10px] text-zinc-600">{new Date(e.timestamp * 1000).toLocaleTimeString()}</span>
                  </div>
                  {e.data?.amount && <p className="text-[11px] text-zinc-400">${e.data.amount} USDT</p>}
                  {e.data?.reason && <p className="text-[10px] text-zinc-500 truncate">{e.data.reason}</p>}
                  {e.data?.github_username && <p className="text-[10px] text-zinc-500">@{e.data.github_username}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

// ─── Main App ───────────────────────────────────────────────────────

export default function App() {
  const [health] = usePolling(api.health, 5000);
  const connected = !!health?.status;

  return (
    <div className="min-h-screen bg-surface-0 text-zinc-100">
      {/* Topbar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-surface-0/80 border-b border-surface-3">
        <div className="max-w-[1440px] mx-auto flex items-center justify-between px-6 h-14">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent to-emerald-400 flex items-center justify-center">
              <CircleDollarSign className="w-4 h-4 text-surface-0" />
            </div>
            <div>
              <span className="text-sm font-semibold tracking-tight">PayStream</span>
              <span className="text-[11px] text-zinc-500 ml-2">Autonomous Payroll DAO Agent</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-accent animate-pulse-dot' : 'bg-danger'}`} />
              <span className="text-zinc-500">{connected ? 'Connected' : 'Offline'}</span>
            </div>
            <Badge color="muted">WDK Edition</Badge>
          </div>
        </div>
      </header>

      {/* Grid */}
      <main className="max-w-[1440px] mx-auto p-6">
        <div className="grid grid-cols-12 gap-4 auto-rows-min">
          {/* Left column: Chat */}
          <div className="col-span-12 lg:col-span-5 xl:col-span-4 h-[calc(100vh-8rem)]">
            <ChatPanel />
          </div>

          {/* Right column: Data panels */}
          <div className="col-span-12 lg:col-span-7 xl:col-span-8 space-y-4">
            {/* Top stats row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card className="p-5">
                <Stat label="Contributors" value={health?.contributors ?? '-'} sub="Registered team" />
              </Card>
              <Card className="p-5">
                <Stat label="Active Streams" value={health?.active_streams ?? '-'} sub="Streaming USDT" />
              </Card>
              <Card className="p-5">
                <Stat label="Agent" value={health?.agent_loaded ? 'Online' : 'Offline'} sub="LangGraph + WDK MCP" />
              </Card>
            </div>

            {/* Main panels */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <ContributorsPanel />
              <StreamsPanel />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              <PolicyPanel />
              <div className="max-h-96">
                <AuditPanel />
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-3 py-4 text-center text-[11px] text-zinc-600">
        PayStream &middot; Built with Tether WDK &middot; LangGraph &middot; OpenRouter
      </footer>
    </div>
  );
}
