import { CircleDollarSign, ArrowRight, Zap, Shield, GitBranch, Globe, Layers, Bot } from 'lucide-react';
import Mermaid from './Mermaid';

const CHAINS = [
  { name: 'Polygon', color: '#8247E5' },
  { name: 'Ethereum', color: '#627EEA' },
  { name: 'Arbitrum', color: '#28A0F0' },
  { name: 'Solana', color: '#14F195' },
];

const FEATURES = [
  {
    icon: Bot,
    title: 'Fully Autonomous',
    desc: 'LangGraph ReAct agent with 37+ tools. Makes payment decisions, evaluates PRs, manages treasury.',
  },
  {
    icon: Shield,
    title: 'Policy Guardrails',
    desc: 'Daily limits, per-tx caps, reserve floor. Auto-pauses on low balance. Every decision audited.',
  },
  {
    icon: GitBranch,
    title: 'GitHub Native',
    desc: 'Monitors merged PRs, scores contributor work via LLM, calculates fair bounties automatically.',
  },
  {
    icon: Layers,
    title: '4-Chain Treasury',
    desc: 'USDT on Polygon, Ethereum, Arbitrum, and Solana. USDT0 cross-chain bridge via LayerZero.',
  },
  {
    icon: Zap,
    title: 'Aave V3 Yield',
    desc: 'Idle capital earns yield on Aave. Agent auto-manages supply/withdraw based on policy.',
  },
  {
    icon: Globe,
    title: 'Self-Custodial',
    desc: 'Built on Tether WDK. Keys never leave the process. Seed auto-generated and persisted.',
  },
];

const ARCH_DIAGRAM = `graph TB
    subgraph Dashboard["React Dashboard"]
        UI["Chat · Contributors · Streams\\nPolicy · Audit · Autonomous Loop"]
    end
    subgraph Agent["Python Agent — FastAPI"]
        LG["LangGraph ReAct Agent"]
        LLM["OpenRouter LLM"]
        subgraph Core["Core Modules"]
            PE["Policy Engine"]
            CR["Contributor Registry"]
            SM["Stream Manager"]
            AL["Audit Log"]
        end
        subgraph Tools["LangChain Tools"]
            GH["GitHub Tools"]
            PT["Payroll Tools"]
        end
    end
    subgraph WDK["WDK MCP Server — Node.js"]
        WT["Wallet ×11"]
        PRT["Pricing ×2"]
        LT["Lending ×8"]
        BT["Bridge ×2"]
    end
    subgraph Chains["Supported Chains"]
        POL["Polygon — USDT"]
        ETH["Ethereum — USDT"]
        ARB["Arbitrum — USDT"]
        SOL["Solana — USDT"]
        AAVE["Aave V3 Yield"]
    end
    UI -->|REST API| LG
    LG --> LLM
    LG --> Core
    LG --> Tools
    LG -->|"MCP stdio"| WDK
    WT --> POL & ETH & ARB & SOL
    LT --> AAVE
    BT -->|LayerZero| POL`;

const FLOW_DIAGRAM = `sequenceDiagram
    participant GH as GitHub
    participant Agent as AI Agent
    participant WDK as WDK MCP
    participant Chain as Polygon / Solana
    Agent->>GH: Scan merged PRs
    GH-->>Agent: PR #42 by @alice
    Agent->>Agent: Evaluate quality + effort
    Agent->>Agent: Policy check ✓
    Agent->>WDK: transfer(polygon, USDT, 0xAlice, "100")
    Note over WDK: Elicitation auto-accepted
    WDK->>Chain: Sign + broadcast tx
    Chain-->>WDK: tx 0xabc...
    WDK-->>Agent: Success
    Agent->>Agent: Log to audit trail`;

const POLICY_DIAGRAM = `flowchart LR
    Start([Payment]) --> P1{Paused?}
    P1 -->|Yes| R1[Reject]
    P1 -->|No| P2{Under tx limit?}
    P2 -->|No| R2[Reject]
    P2 -->|Yes| P3{Under daily cap?}
    P3 -->|No| R3[Reject]
    P3 -->|Yes| P4{Above reserve?}
    P4 -->|No| R4[Auto-pause]
    P4 -->|Yes| OK[Execute via WDK]`;

const WDK_PACKAGES = [
  { pkg: '@tetherto/wdk', purpose: 'Core wallet orchestrator' },
  { pkg: '@tetherto/wdk-mcp-toolkit', purpose: 'MCP server — 35 built-in tools' },
  { pkg: '@tetherto/wdk-wallet-evm', purpose: 'Polygon, Ethereum, Arbitrum' },
  { pkg: '@tetherto/wdk-wallet-solana', purpose: 'Solana SPL tokens' },
  { pkg: '@tetherto/wdk-protocol-lending-aave-evm', purpose: 'Aave V3 supply/withdraw' },
  { pkg: '@tetherto/wdk-protocol-bridge-usdt0-evm', purpose: 'USDT0 cross-chain (LayerZero)' },
];

export default function Landing({ onEnter }) {
  return (
    <div className="min-h-screen bg-surface-0 text-zinc-100">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-surface-0/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 h-14">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent to-emerald-400 flex items-center justify-center">
              <CircleDollarSign className="w-4 h-4 text-surface-0" />
            </div>
            <span className="text-sm font-semibold tracking-tight">PayStream</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#architecture" className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors hidden sm:block">Architecture</a>
            <a href="#features" className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors hidden sm:block">Features</a>
            <a href="https://github.com/N-45div/PayStream" target="_blank" rel="noreferrer"
              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">GitHub</a>
            <button onClick={onEnter}
              className="text-xs font-medium text-surface-0 bg-accent hover:bg-accent-bright rounded-lg px-4 py-1.5 transition-colors">
              Open Dashboard
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-[11px] text-zinc-500 border border-surface-3 rounded-full px-3 py-1 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            Built with Tether WDK &middot; Hackathon Galáctica
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1] mb-5">
            Autonomous Payroll
            <br />
            <span className="bg-gradient-to-r from-accent via-emerald-400 to-teal-300 bg-clip-text text-transparent">
              Treasury Agent
            </span>
          </h1>
          <p className="text-base sm:text-lg text-zinc-400 max-w-xl mx-auto mb-8 leading-relaxed">
            An AI agent that monitors GitHub, evaluates contributor work,
            and pays USDT across 4 chains — with policy guardrails, Aave yield,
            and a full audit trail. Zero human intervention.
          </p>
          <div className="flex items-center justify-center gap-3">
            <button onClick={onEnter}
              className="flex items-center gap-2 text-sm font-medium text-surface-0 bg-accent hover:bg-accent-bright rounded-xl px-6 py-2.5 transition-all hover:shadow-lg hover:shadow-accent/20">
              Launch Dashboard <ArrowRight className="w-4 h-4" />
            </button>
            <a href="https://github.com/N-45div/PayStream" target="_blank" rel="noreferrer"
              className="text-sm font-medium text-zinc-400 border border-surface-4 hover:border-zinc-600 rounded-xl px-6 py-2.5 transition-colors">
              View Source
            </a>
          </div>
          <div className="flex items-center justify-center gap-2 mt-10">
            {CHAINS.map(c => (
              <span key={c.name} className="flex items-center gap-1.5 text-[11px] text-zinc-400 bg-surface-1 border border-surface-3 rounded-full px-3 py-1">
                <span className="w-2 h-2 rounded-full" style={{ background: c.color }} />
                {c.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xl font-semibold text-center mb-10">What it does</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(f => (
              <div key={f.title} className="bg-surface-1 border border-surface-3 rounded-2xl p-5 hover:border-surface-4 transition-colors">
                <f.icon className="w-5 h-5 text-accent mb-3" />
                <h3 className="text-sm font-semibold mb-1.5">{f.title}</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xl font-semibold text-center mb-2">Architecture</h2>
          <p className="text-xs text-zinc-500 text-center mb-8">React Dashboard → FastAPI Agent → WDK MCP Server → 4 Chains</p>
          <div className="bg-surface-1 border border-surface-3 rounded-2xl p-6 overflow-x-auto">
            <Mermaid chart={ARCH_DIAGRAM} className="flex justify-center [&_svg]:max-w-full" />
          </div>
        </div>
      </section>

      {/* Payment Flow */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xl font-semibold text-center mb-2">Payment Flow</h2>
          <p className="text-xs text-zinc-500 text-center mb-8">From merged PR to on-chain USDT transfer — fully autonomous</p>
          <div className="bg-surface-1 border border-surface-3 rounded-2xl p-6 overflow-x-auto">
            <Mermaid chart={FLOW_DIAGRAM} className="flex justify-center [&_svg]:max-w-full" />
          </div>
        </div>
      </section>

      {/* Policy Engine */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-xl font-semibold text-center mb-2">Policy Engine</h2>
          <p className="text-xs text-zinc-500 text-center mb-8">Every payment passes through configurable guardrails</p>
          <div className="bg-surface-1 border border-surface-3 rounded-2xl p-6 overflow-x-auto">
            <Mermaid chart={POLICY_DIAGRAM} className="flex justify-center [&_svg]:max-w-full" />
          </div>
        </div>
      </section>

      {/* WDK Modules */}
      <section className="pb-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-xl font-semibold text-center mb-2">WDK Modules</h2>
          <p className="text-xs text-zinc-500 text-center mb-8">6 Tether WDK packages powering the treasury</p>
          <div className="space-y-2">
            {WDK_PACKAGES.map(p => (
              <div key={p.pkg} className="flex items-center justify-between bg-surface-1 border border-surface-3 rounded-xl px-5 py-3 hover:border-surface-4 transition-colors">
                <code className="text-xs text-accent font-mono">{p.pkg}</code>
                <span className="text-xs text-zinc-500">{p.purpose}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-20 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-3">Try it live</h2>
          <p className="text-sm text-zinc-500 mb-6">Open the dashboard, set a GitHub repo, register a contributor, and watch the agent work.</p>
          <button onClick={onEnter}
            className="inline-flex items-center gap-2 text-sm font-medium text-surface-0 bg-accent hover:bg-accent-bright rounded-xl px-8 py-3 transition-all hover:shadow-lg hover:shadow-accent/20">
            Launch Dashboard <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-surface-3 py-6 text-center text-[11px] text-zinc-600">
        PayStream &middot; Built with Tether WDK &middot; LangGraph &middot; OpenRouter &middot; Hackathon Galáctica 2026
      </footer>
    </div>
  );
}
