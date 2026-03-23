# PayStream — Autonomous Payroll DAO Agent

> Autonomous AI treasury that pays contributors, manages yield, and bridges USDT across 4 chains — self-custodial, policy-governed, zero human intervention.

Built for [Hackathon Galáctica: WDK Edition](https://dorahacks.io/hackathon/hackathon-galactica-wdk-2026-01) — **Agent Wallets Track**

**Live:** [https://paystream-1064261519338.us-central1.run.app](https://paystream-1064261519338.us-central1.run.app)

---

## The Problem

Open-source projects and DAOs need to pay contributors. Today this means:
- A human treasurer manually reviewing PRs and sending payments
- No policy enforcement — one bad decision drains the treasury
- No audit trail — contributors don't know why they were paid (or weren't)
- Idle treasury capital earns zero yield
- Cross-chain complexity — contributors on different chains can't get paid easily

## The Solution

**PayStream** is a fully autonomous AI agent that manages a multi-chain contributor payroll treasury end-to-end:

```mermaid
graph LR
    A[Contributor merges PR] --> B[Agent detects via GitHub API]
    B --> C[AI evaluates quality + effort]
    C --> D{Policy engine check}
    D -->|Approved| E[USDT transferred via WDK]
    D -->|Rejected| F[Logged + reason recorded]
    E --> G[Full audit trail on dashboard]
    F --> G
    E --> H[Bridge cross-chain if needed]
```

No human in the loop. The agent decides who gets paid, how much, and on which chain — within policy guardrails you define. Every decision is logged and visible.

---

## Architecture

```mermaid
graph TB
    subgraph Dashboard["React Dashboard :5174"]
        UI["Chat Console · Contributors · Streams\nPolicy · Audit · Autonomous Loop"]
    end

    subgraph Agent["Python Agent :8001"]
        FA["FastAPI Server"]
        LG["LangGraph ReAct Agent"]
        EL["MCP Elicitation\n(Auto-accept for autonomy)"]
        LLM["OpenRouter LLM\n(Claude / GPT-4 / Llama)"]
        subgraph Core["Core Modules"]
            PE["Policy Engine"]
            CR["Contributor Registry"]
            SM["Stream Manager"]
            AL["Audit Log"]
        end
        subgraph Tools["LangChain Tools (14)"]
            GH["GitHub Tools"]
            PT["Payroll Tools"]
        end
    end

    subgraph WDK["WDK MCP Server (Node.js · stdio)"]
        SEED["Seed Persistence\n(.seed file auto-gen)"]
        WT["Wallet Tools ×11"]
        PRT["Pricing Tools ×2"]
        LT["Lending Tools ×8"]
        BT["Bridge Tools ×2"]
    end

    subgraph Chains["Supported Chains"]
        POL["Polygon — USDT"]
        ETH["Ethereum — USDT"]
        ARB["Arbitrum — USDT"]
        SOL["Solana — USDT"]
        AAVE["Aave V3 — Yield"]
        BR["USDT0 Bridge\n(LayerZero cross-chain)"]
    end

    UI -->|"REST API"| FA
    FA --> LG
    LG --> LLM
    LG --> EL
    LG --> Core
    LG --> Tools
    LG -->|"MCP Protocol\n(JSON-RPC 2.0 / stdio)"| WDK
    WT --> POL & ETH & ARB & SOL
    LT --> AAVE
    BT --> BR
```

### Component Overview

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| **Landing Page** | React + Mermaid.js | Interactive landing with 3 live mermaid diagrams (architecture, payment flow, policy engine) |
| **Dashboard** | React 18 + Tailwind CSS + Vite | Real-time treasury monitoring, agent chat with voice input (STT), autonomous loop, settings UI |
| **Agent** | Python + LangGraph + FastAPI | AI reasoning, policy enforcement, GitHub monitoring, payroll logic |
| **WDK MCP** | Node.js + `@tetherto/wdk-mcp-toolkit` | 35+ MCP tools — wallet, lending, pricing, bridging |
| **Chains** | Polygon, Ethereum, Arbitrum, **Solana** | USDT transfers, Aave V3 yield, USDT0 cross-chain bridge |

### Autonomous Loop

```mermaid
sequenceDiagram
    loop Every 2 minutes
        Agent->>Agent: Check active payment streams
        Agent->>Agent: Process due stream payments
        Agent->>GitHub: Scan for newly merged PRs
        Agent->>Agent: Evaluate + calculate bounties
        Agent->>WDK: Execute approved USDT payments
        Agent->>WDK: Check idle balance vs Aave yield
        Agent->>Agent: Log all decisions to audit trail
    end
```

---

## Features

### Autonomous Agent
- **LangGraph ReAct** agent with 37+ tools (23 MCP + 14 Python)
- Monitors GitHub for merged PRs, evaluates quality via LLM
- Calculates fair bounties based on contributor role + effort
- Creates time-based payment streams without human intervention
- **MCP elicitation auto-accept** — true autonomy (no human confirmation needed for transfers)
- **Voice input (STT)** — speak commands via browser SpeechRecognition API
- **Configurable GitHub repo** — change monitored repo from dashboard at runtime

### Multi-Chain Treasury (4 Chains)
- **Polygon** — low-fee USDT payments (default for payroll)
- **Ethereum** — USDT + Aave V3 yield on idle treasury
- **Arbitrum** — fast L2 USDT transfers
- **Solana** — SPL USDT via WDK Solana wallet module
- **USDT0 Bridge** — cross-chain transfers via LayerZero

### Policy Engine
- **Daily spend cap** — prevents treasury drain
- **Single payment limit** — per-transaction ceiling
- **Minimum balance reserve** — always keeps a safety floor
- **AI approval threshold** — large payments get extra AI scrutiny
- **Auto-pause on low balance** — self-protective shutdown

### Self-Custodial Wallet
- **Auto-generated BIP-39 seed** — persisted to `.seed` file, survives restarts
- **No manual config needed** — just start the agent and a wallet is created
- **Private keys never leave the process** — true self-custody
- **EIP-55 checksummed addresses** enforced for EVM chains

### Full Audit Trail
- Every decision logged with timestamp and context
- Policy check results (approved/rejected + reason)
- AI reasoning captured for every payment decision
- Transaction hashes linked to block explorers

### x402 Payment Protocol Ready
- WDK's EVM wallet natively satisfies the x402 `ClientEvmSigner` interface
- PayStream can **pay for** external API services autonomously via HTTP 402 — no accounts, no API keys
- Can also **charge other agents** for access to its payroll API — enabling agent-to-agent economy
- USDT payments over HTTP, machine-to-machine, trustless

### Landing Page & Interactive Diagrams
- Dedicated landing page with hero, feature grid, and CTA
- **3 live mermaid diagrams** rendered in-browser: system architecture, payment flow, policy engine
- WDK module breakdown table
- Hash-based routing: `/` = landing page, `/#dashboard` = full app

---

## Quick Start

### Prerequisites

- **Node.js** 18+ (with npm)
- **Python** 3.11+
- **OpenRouter API key** ([get one free](https://openrouter.ai))

### 1. Clone

```bash
git clone https://github.com/N-45div/PayStream.git
cd PayStream
```

### 2. Install WDK MCP Server

```bash
cd wdk-server
npm install
cd ..
```

### 3. Install Python Agent

```bash
cd agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY at minimum
cd ..
```

### 4. Install Dashboard

```bash
cd dashboard
npm install
cd ..
```

### 5. Run

**Terminal 1 — Agent** (auto-spawns WDK MCP server as subprocess):
```bash
cd agent && source .venv/bin/activate && python server.py
```

**Terminal 2 — Dashboard**:
```bash
cd dashboard && npm run dev
```

Open **http://localhost:5174** → you should see the PayStream dashboard connected.

> **Note:** The wallet seed is auto-generated on first run and persisted to `wdk-server/.seed`. No manual config needed — your wallet survives restarts automatically.

---

## Environment Variables

Create `agent/.env` (see `agent/.env.example`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | **Yes** | — | LLM API key from [OpenRouter](https://openrouter.ai) |
| `OPENROUTER_MODEL` | No | `stepfun/step-3.5-flash:free` | Any chat model on OpenRouter (must support tool calling) |
| `WDK_SEED` | No | Auto-generated + persisted | BIP-39 mnemonic for wallet |
| `GITHUB_TOKEN` | No | — | GitHub PAT for PR monitoring |
| `GITHUB_REPO` | No | — | Default repo to watch (`owner/repo`) |
| `POLYGON_RPC` | No | `https://polygon.llamarpc.com` | Custom Polygon RPC |
| `ETH_RPC` | No | `https://eth.llamarpc.com` | Custom Ethereum RPC |
| `ARB_RPC` | No | `https://arbitrum.llamarpc.com` | Custom Arbitrum RPC |
| `SOLANA_RPC` | No | `https://api.mainnet-beta.solana.com` | Custom Solana RPC |
| `PORT` | No | `8000` | FastAPI server port |

---

## Demo Flow

```mermaid
sequenceDiagram
    participant Admin as DAO Admin
    participant UI as PayStream Dashboard
    participant Agent as LangGraph Agent
    participant WDK as WDK MCP Server
    participant Chain as Polygon / Solana

    Admin->>UI: Register contributor @alice (developer, 0x...)
    UI->>Agent: POST /api/contributors
    Agent-->>UI: ✓ Registered

    Admin->>UI: "Check all USDT balances"
    UI->>Agent: POST /api/chat
    Agent->>WDK: getTokenBalance(polygon, USDT)
    Agent->>WDK: getTokenBalance(ethereum, USDT)
    Agent->>WDK: getTokenBalance(arbitrum, USDT)
    Agent->>WDK: getTokenBalance(solana, USDT)
    WDK-->>Agent: Balances across 4 chains
    Agent-->>UI: "Treasury: 400 USDT (Polygon) + 50 (ETH) + 30 (ARB) + 20 (SOL)"

    Admin->>UI: "Review merged PRs and pay contributors"
    UI->>Agent: POST /api/chat
    Agent->>Agent: get_merged_prs() → PR #42 by @alice
    Agent->>Agent: AI evaluation: quality 8/10, ~2h effort
    Agent->>Agent: Bounty: 2h × $50/hr = $100
    Agent->>Agent: Policy check: ✓ under limits
    Agent->>WDK: transfer(polygon, USDT, 0xAlice, "100")
    Note over WDK: Elicitation auto-accepted<br/>(autonomous mode)
    WDK->>Chain: Sign + broadcast tx
    Chain-->>WDK: tx 0xabc...
    WDK-->>Agent: {hash: "0xabc..."}
    Agent-->>UI: "Paid @alice $100 for PR #42 — tx: 0xabc..."
```

---

## Project Structure

```
PayStream/
├── wdk-server/                 # Node.js — WDK MCP Server
│   ├── index.js                # Multi-chain wallet + Aave + bridge + pricing
│   ├── .seed                   # Auto-generated wallet seed (gitignored)
│   └── package.json
├── agent/                      # Python — LangGraph AI Agent
│   ├── core/
│   │   ├── config.py           # Centralized configuration
│   │   ├── policy_engine.py    # Budget enforcement + auto-pause
│   │   ├── contributor_registry.py  # Team management + rate tracking
│   │   ├── stream_manager.py   # Payment streaming logic
│   │   └── audit_log.py        # Immutable decision log
│   ├── tools/
│   │   ├── github_tools.py     # PR monitoring via GitHub API
│   │   └── payroll_tools.py    # LangChain tools for payroll ops
│   ├── graph.py                # LangGraph ReAct agent + MCP elicitation
│   ├── server.py               # FastAPI REST server + static dashboard
│   ├── requirements.txt
│   └── .env.example
├── dashboard/                  # React — Real-time Dashboard + Landing
│   ├── src/
│   │   ├── App.jsx             # Dashboard UI (8 panels + stats + STT)
│   │   ├── Landing.jsx         # Landing page with mermaid diagrams
│   │   ├── Mermaid.jsx         # Mermaid diagram renderer (dark theme)
│   │   ├── api.js              # API client (chat, settings, autonomous)
│   │   ├── main.jsx            # Entry + hash-based routing
│   │   └── index.css           # Tailwind + custom styles
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── Dockerfile                  # Multi-stage: Node + Python + React
├── README.md
└── ARCHITECTURE.md
```

---

## How It Works — Policy Engine

```mermaid
flowchart TD
    Start([Payment Request]) --> P1{Agent paused?}
    P1 -->|Yes| R1[REJECT — agent paused]
    P1 -->|No| P2{Amount ≤ single tx limit?}
    P2 -->|No| R2[REJECT — exceeds per-tx max]
    P2 -->|Yes| P3{Daily spent + amount ≤ daily cap?}
    P3 -->|No| R3[REJECT — daily limit reached]
    P3 -->|Yes| P4{Balance − amount ≥ reserve floor?}
    P4 -->|No| P5[Auto-pause agent]
    P5 --> R4[REJECT — low balance]
    P4 -->|Yes| P6[APPROVE — execute via WDK]
    P6 --> P7{Contributor on same chain?}
    P7 -->|Yes| TX[Transfer USDT directly]
    P7 -->|No| BRG[Bridge USDT0 cross-chain]
    TX & BRG --> Log[Log to audit trail]
    R1 & R2 & R3 & R4 --> Log
```

## Wallet Seed Lifecycle

```mermaid
flowchart LR
    Start([Agent Starts]) --> A{WDK_SEED env set?}
    A -->|Yes + Valid| USE[Use env seed]
    A -->|No / Invalid| B{.seed file exists?}
    B -->|Yes + Valid| LOAD[Load from .seed file]
    B -->|No| GEN[Auto-generate BIP-39 seed]
    GEN --> SAVE[Save to .seed file]
    SAVE --> USE2[Use generated seed]
    USE & LOAD & USE2 --> WDK[Initialize WDK wallet]
    WDK --> CHAINS[Register 4 chains + tokens]
```

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Wallet | [Tether WDK](https://docs.wdk.tether.io) | Self-custodial, multi-chain, official toolkit |
| MCP Tools | [WDK MCP Toolkit](https://github.com/tetherto/wdk-mcp-toolkit) | 23+ tools — wallet, lending, pricing, bridge |
| Agent | [LangGraph](https://langchain-ai.github.io/langgraph/) | Production-grade stateful ReAct agent |
| MCP Bridge | [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) | Official LangChain ↔ MCP integration |
| LLM | [OpenRouter](https://openrouter.ai) | Vendor-agnostic — stepfun/step-3.5-flash:free (supports tool calling) |
| API | [FastAPI](https://fastapi.tiangolo.com) | Async Python, auto-docs, Pydantic validation |
| Dashboard | [React](https://react.dev) + [Tailwind CSS](https://tailwindcss.com) + [Mermaid.js](https://mermaid.js.org) | Modern UI, landing page with live diagrams, voice input |
| Chains | Polygon, Ethereum, Arbitrum, Solana | 4-chain USDT + Aave yield + USDT0 bridge |
| Deploy | Docker + Google Cloud Run | Multi-runtime container (Node + Python) |

---

## WDK Modules Used

| Package | Purpose |
|---------|--------|
| `@tetherto/wdk` | Core wallet orchestrator |
| `@tetherto/wdk-mcp-toolkit` | MCP server with 35 built-in tools |
| `@tetherto/wdk-wallet-evm` | Polygon, Ethereum, Arbitrum wallets |
| `@tetherto/wdk-wallet-solana` | Solana wallet (SPL tokens) |
| `@tetherto/wdk-protocol-lending-aave-evm` | Aave V3 supply/withdraw |
| `@tetherto/wdk-protocol-bridge-usdt0-evm` | USDT0 cross-chain bridge (LayerZero) |

---

## Deployment

PayStream ships with a multi-stage `Dockerfile` for Google Cloud Run:

```bash
# Build & deploy to Cloud Run
docker build -t paystream .
docker tag paystream us-central1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/paystream:latest
docker push us-central1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/paystream:latest

gcloud run deploy paystream \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT/cloud-run-source-deploy/paystream:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi --cpu 2 \
  --set-env-vars "OPENROUTER_API_KEY=...,OPENROUTER_MODEL=stepfun/step-3.5-flash:free,WDK_SEED=..."
```

The container bundles Node.js (WDK server) + Python (agent) + built React dashboard with landing page. FastAPI serves the static dashboard in production.

**Live deployment:** [https://paystream-1064261519338.us-central1.run.app](https://paystream-1064261519338.us-central1.run.app)

---

## License

MIT
