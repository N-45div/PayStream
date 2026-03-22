# PayStream — Architecture

Deep technical documentation for the Autonomous Payroll DAO Agent.

---

## System Overview

PayStream is a **three-layer system**: a React dashboard for humans, a Python LangGraph agent for reasoning, and a Node.js WDK MCP server for blockchain operations.

```mermaid
flowchart TB
    subgraph Human["Human Layer"]
        Admin["DAO Admin"]
        Browser["React Dashboard\n:5174"]
    end

    subgraph Intelligence["Intelligence Layer — Python"]
        FastAPI["FastAPI Server\n:8001"]
        LangGraph["LangGraph ReAct Agent"]
        OpenRouter["OpenRouter LLM\n(Claude / GPT-4 / Llama)"]
        
        subgraph CoreModules["Core Modules"]
            PE["Policy Engine"]
            CR["Contributor Registry"]
            SM["Stream Manager"]
            AL["Audit Log"]
        end

        subgraph Tools["LangChain Tools"]
            GH["GitHub Tools\n(PR monitoring)"]
            PT["Payroll Tools\n(contributors, streams, policy)"]
        end
    end

    subgraph Wallet["Wallet Layer — Node.js"]
        MCP["WDK MCP Server\n(stdio transport)"]
        
        subgraph MCPTools["21 MCP Tools"]
            WT["Wallet Tools ×11\ngetBalance, transfer, sign..."]
            PRT["Pricing Tools ×2\ngetCurrentPrice, getHistoricalPrice"]
            LT["Lending Tools ×8\nsupply, withdraw, borrow, repay..."]
        end
    end

    subgraph Blockchain["Blockchain Layer"]
        Polygon["Polygon\nUSDT transfers"]
        Ethereum["Ethereum\nUSDT transfers"]
        Arbitrum["Arbitrum\nUSDT transfers"]
        Aave["Aave V3\nYield on idle treasury"]
    end

    Admin -->|interacts| Browser
    Browser -->|REST API| FastAPI
    FastAPI --> LangGraph
    LangGraph --> OpenRouter
    LangGraph --> CoreModules
    LangGraph --> Tools
    LangGraph -->|"MCP protocol via langchain-mcp-adapters"| MCP
    MCP --> MCPTools
    WT --> Polygon & Ethereum & Arbitrum
    LT --> Aave
```

---

## Data Flow: PR → Payment

The core value proposition — turning a merged GitHub PR into an autonomous USDT payment.

```mermaid
sequenceDiagram
    participant GH as GitHub API
    participant Agent as LangGraph Agent
    participant LLM as OpenRouter LLM
    participant PE as Policy Engine
    participant CR as Contributor Registry
    participant WDK as WDK MCP Server
    participant Chain as Polygon
    participant AL as Audit Log

    Note over Agent: Agent processes request
    Agent->>GH: get_merged_prs()
    GH-->>Agent: PR #42 by @alice (+180 -30, 5 files)

    Agent->>CR: Look up @alice
    CR-->>Agent: Developer, $50/hr, wallet 0x...

    Agent->>LLM: Evaluate PR #42 quality + effort
    LLM-->>Agent: Quality 8/10, est 2h → $100 bounty

    Agent->>PE: can_pay(0x..., $100, balance=$500)
    PE-->>Agent: APPROVED (all checks passed)

    Agent->>WDK: transfer(polygon, USDT, 0x..., "100")
    WDK->>Chain: Sign + broadcast tx
    Chain-->>WDK: tx_hash: 0xabc...
    WDK-->>Agent: {hash: "0xabc...", fee: "0.002"}

    Agent->>CR: record_payment(@alice, $100)
    Agent->>PE: record_spend($100)
    Agent->>AL: PAYMENT_SUCCESS {amount: 100, tx: 0xabc...}
```

---

## Component Details

### 1. WDK MCP Server (`wdk-server/`)

A Node.js process that runs as a **subprocess** of the Python agent, communicating via **stdio** using the Model Context Protocol (JSON-RPC 2.0).

```mermaid
flowchart LR
    subgraph NodeProcess["Node.js Subprocess"]
        WdkMcpServer["WdkMcpServer"]
        WDKCore["WDK Core\n(BIP-39 key derivation)"]
        EVM["WalletManagerEvm\n(Polygon · Ethereum · Arbitrum)"]
        AAVE["AaveProtocolEvm\n(Aave V3 lending)"]
        BFX["Bitfinex Pricing\n(no API key)"]
    end

    WdkMcpServer --> WDKCore
    WDKCore --> EVM
    WdkMcpServer --> AAVE
    WdkMcpServer --> BFX

    PythonAgent["Python Agent\n(langchain-mcp-adapters)"] <-->|"stdio · JSON-RPC 2.0"| WdkMcpServer
```

**Key implementation details:**
- Auto-generates BIP-39 seed phrase if `WDK_SEED` is missing or invalid (`WDK.isValidSeed()` + `WDK.getRandomSeedPhrase()`)
- Explicitly creates `StdioServerTransport` and connects — required by WDK MCP Toolkit
- Registers USDT token addresses on all three chains for balance queries and transfers

**Registered chains:**

| Chain | Provider | USDT Address |
|-------|----------|-------------|
| Polygon | `polygon-rpc.com` | `0xc2132D05D31c914a87C6611C10748AEb04B58e8F` |
| Ethereum | `eth.drpc.org` | `0xdAC17F958D2ee523a2206206994597C13D831ec7` |
| Arbitrum | `arb1.arbitrum.io/rpc` | `0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9` |

**MCP tools (21 registered):**
- **11 Wallet** — getAddress, getBalance, getTokenBalance, getFeeRates, quoteSendTransaction, quoteTransfer, sendTransaction, transfer, sign, verify, getMaxSpendableBtc
- **2 Pricing** — getCurrentPrice, getHistoricalPrice
- **8 Lending** — quoteSupply, supply, quoteWithdraw, withdraw, quoteBorrow, borrow, quoteRepay, repay

### 2. Python Agent (`agent/`)

The intelligence layer built on **LangGraph**.

```mermaid
flowchart TB
    subgraph AgentGraph["LangGraph ReAct Agent"]
        direction TB
        Start([User message]) --> Reason["LLM Reasoning\n(OpenRouter)"]
        Reason --> ToolCall{Tool call needed?}
        ToolCall -->|Yes| Execute["Execute Tool"]
        Execute --> Observe["Observe Result"]
        Observe --> Reason
        ToolCall -->|No| Response([Final response])
    end

    subgraph AvailableTools["35 Tools Available"]
        direction LR
        subgraph PythonTools["14 Python Tools"]
            G1["get_merged_prs"]
            G2["get_pr_details"]
            P1["register_contributor"]
            P2["list_contributors"]
            P3["suspend_contributor"]
            P4["create_stream"]
            P5["list_streams"]
            P6["cancel_stream"]
            P7["get_policy"]
            P8["update_policy"]
            P9["pause_agent"]
            P10["resume_agent"]
            P11["get_audit_log"]
            P12["get_audit_summary"]
        end
        subgraph MCPTools["21 WDK MCP Tools"]
            M1["getBalance · getTokenBalance"]
            M2["transfer · sendTransaction"]
            M3["supply · withdraw (Aave)"]
            M4["getCurrentPrice"]
            M5["+ 14 more..."]
        end
    end

    Execute --> AvailableTools
```

**MCP connection (langchain-mcp-adapters v0.1.0+):**
```python
# No context manager — new API
mcp_client = MultiServerMCPClient({
    "wdk": {
        "command": "node",
        "args": ["../wdk-server/index.js"],
        "transport": "stdio",
        "env": {**os.environ, "WDK_SEED": seed},
    },
})
wdk_tools = await mcp_client.get_tools()
```

**Core modules:**

| Module | File | Responsibility |
|--------|------|---------------|
| **Policy Engine** | `core/policy_engine.py` | Budget enforcement: daily caps, single tx limits, min balance, auto-pause |
| **Contributor Registry** | `core/contributor_registry.py` | Team management: roles, hourly rates, earnings tracking, suspension |
| **Stream Manager** | `core/stream_manager.py` | Payment streaming: continuous USDT drip to recipients over time |
| **Audit Log** | `core/audit_log.py` | Immutable timestamped record of every decision and action |

**FastAPI endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send natural language message to the agent |
| `GET` | `/api/contributors` | List all contributors |
| `POST` | `/api/contributors` | Register a new contributor |
| `GET` | `/api/streams` | List all payment streams |
| `POST` | `/api/streams` | Create a new stream |
| `POST` | `/api/streams/:id/cancel` | Cancel an active stream |
| `GET` | `/api/policy` | Get current policy + status |
| `PUT` | `/api/policy` | Update policy limits |
| `POST` | `/api/policy/pause` | Pause the agent |
| `POST` | `/api/policy/resume` | Resume the agent |
| `GET` | `/api/audit` | Get recent audit entries |
| `GET` | `/api/audit/summary` | Get audit statistics |
| `GET` | `/api/health` | Health check |

### 3. Dashboard (`dashboard/`)

Production React app with **real-time polling** (3–5s intervals).

```mermaid
flowchart LR
    subgraph Panels["Dashboard Panels"]
        Chat["Agent Console\n(natural language chat)"]
        Contrib["Contributors\n(register · view · roles)"]
        Streams["Streams\n(progress · cancel)"]
        Policy["Treasury Policy\n(limits · pause/resume)"]
        Audit["Audit Trail\n(timestamped decision log)"]
    end

    subgraph API["FastAPI Endpoints"]
        ChatAPI["POST /api/chat"]
        ContribAPI["GET/POST /api/contributors"]
        StreamAPI["GET/POST /api/streams"]
        PolicyAPI["GET/PUT /api/policy"]
        AuditAPI["GET /api/audit"]
        HealthAPI["GET /api/health"]
    end

    Chat --> ChatAPI
    Contrib --> ContribAPI
    Streams --> StreamAPI
    Policy --> PolicyAPI
    Audit --> AuditAPI
    Panels -.->|"polling 3-5s"| HealthAPI
```

**UI features:**
- Dark theme with custom color palette (surface, accent, danger, warn)
- Inter + JetBrains Mono fonts
- Stats row (contributors, active streams, agent status)
- Real-time connection status indicator
- Custom `usePolling` hook for automatic data refresh

---

## Policy Engine Decision Tree

```mermaid
flowchart TD
    Start([Payment request]) --> Paused{Agent paused?}
    Paused -->|Yes| Reject1["REJECT\nAgent paused"]
    Paused -->|No| Single{Amount ≤ max_single_payment?}
    Single -->|No| Reject2["REJECT\nExceeds per-tx limit"]
    Single -->|Yes| Daily{daily_spent + amount ≤ max_daily_spend?}
    Daily -->|No| Reject3["REJECT\nDaily limit reached"]
    Daily -->|Yes| Balance{balance − amount ≥ min_balance?}
    Balance -->|No| AutoPause["Auto-pause agent"]
    AutoPause --> Reject4["REJECT\nLow balance"]
    Balance -->|Yes| Approve["APPROVE\nExecute via WDK"]
    
    Approve --> LogOK["Audit: PAYMENT_SUCCESS"]
    Reject1 & Reject2 & Reject3 & Reject4 --> LogFail["Audit: PAYMENT_REJECTED"]
```

**Default policy values:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_daily_spend` | $500 | Total USDT per 24h |
| `max_single_payment` | $100 | Max per transaction |
| `min_balance` | $10 | Treasury reserve floor |
| `ai_approval_threshold` | $25 | AI reviews payments above this |
| `tick_interval_s` | 30 | Agent loop interval |

---

## Security Model

```mermaid
flowchart TB
    Seed["BIP-39 Seed Phrase\n(.env — never committed)"] --> WDKCore["WDK Core\n(HD key derivation)"]
    WDKCore --> Keys["Private Keys\n(in-memory only)"]
    Keys --> Sign["Transaction Signing\n(local · self-custodial)"]
    Sign --> Broadcast["Broadcast to EVM chain"]

    subgraph NeverLeaves["Never leaves the Node.js process"]
        Seed
        WDKCore
        Keys
    end

    PolicyGate["Policy Engine\n(must approve first)"] -->|gate| Sign
    AuditLog["Audit Log\n(records everything)"] -->|observe| Sign
```

**Security properties:**
- **Self-custodial** — private keys derived from BIP-39 seed, never leave the WDK subprocess
- **Process isolation** — WDK MCP server runs as a child process, communicates only via stdio
- **Policy-gated** — every payment must pass policy checks before the agent can call `transfer`
- **Auditable** — every decision (approved or rejected) is logged with full context
- **Env-only secrets** — seed phrase and API keys loaded from `.env`, never hardcoded
- **Auto-validation** — WDK server validates seed with `WDK.isValidSeed()` before use

---

## Technology Rationale

| Decision | Choice | Why |
|----------|--------|-----|
| Agent framework | LangGraph | Production-grade stateful agent with ReAct loop, tool calling, and message history |
| LLM access | OpenRouter | Vendor-agnostic — swap between Claude, GPT-4, Llama without code changes |
| Wallet | Tether WDK + MCP Toolkit | Official toolkit, 21 tools, multi-chain, self-custodial, Aave V3 built-in |
| Agent ↔ WDK bridge | `langchain-mcp-adapters` | Official LangChain library for MCP tool integration (v0.1.0+ API) |
| API server | FastAPI | Async Python, auto-generated OpenAPI docs, Pydantic validation |
| Dashboard | React 18 + Tailwind CSS | Lightweight, production-ready, no heavy component libraries |
| Build tool | Vite | Fast HMR, ES module native, minimal config |

---

## Future Extensions

- **Persistent storage** — PostgreSQL for contributors, streams, audit (currently in-memory)
- **GitHub webhooks** — real-time PR detection instead of polling
- **Multi-repo monitoring** — watch multiple repositories simultaneously
- **Salary streaming** — continuous per-second USDT streams (stream manager already supports this)
- **Cross-chain bridging** — auto-bridge USDT between chains based on gas costs (WDK bridge tools available)
- **Multi-sig governance** — require multiple approvals for payments above threshold
- **Cloudflare Workers deployment** — deploy MCP server as edge function for global availability
