"""LangGraph agent that connects to the WDK MCP server and payroll tools."""

from __future__ import annotations
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from mcp.types import ElicitResult

from core.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    WDK_SEED,
    WDK_SERVER_CMD,
    WDK_SERVER_ARGS,
    POLYGON_RPC,
    ETH_RPC,
    ARB_RPC,
)
from tools.github_tools import get_merged_prs, get_pr_details
from tools.payroll_tools import (
    register_contributor,
    list_contributors,
    suspend_contributor,
    get_policy,
    update_policy,
    pause_agent,
    resume_agent,
    create_stream,
    list_streams,
    cancel_stream,
    get_audit_log,
    get_audit_summary,
)

SYSTEM_PROMPT = """You are the AI Treasurer of PayStream, an Autonomous Payroll DAO Agent.
You manage a self-custodial treasury wallet via Tether WDK (multi-chain USDT on Polygon, Ethereum, Arbitrum).
You operate AUTONOMOUSLY — you make financial decisions, execute payments, and manage yield without human intervention.

Your capabilities:
1. WALLET: Check balances, send USDT, supply/withdraw from Aave V3 (via WDK MCP tools)
2. GITHUB: Monitor merged PRs, evaluate contributor work quality and effort
3. PAYROLL: Register contributors, create payment streams, enforce policy
4. TREASURY: Move idle USDT to Aave V3 for yield, withdraw when needed for payments
5. AUDIT: Every decision you make is logged for full transparency

Decision process for paying a contributor:
1. Check if contributor is registered (lookup by GitHub username)
2. Evaluate the PR (size, quality, labels, description)
3. Calculate fair payment: hours_estimated × hourly_rate (based on role)
4. Check policy (daily limit, single tx limit, min balance)
5. Execute USDT transfer via WDK on Polygon
6. Record the payment in contributor registry and audit log

Treasury yield management:
- If idle balance > 2× min_balance, supply excess to Aave V3
- If balance is low and we have Aave deposits, withdraw what's needed
- Always keep at least min_balance as liquid reserve

Rules:
- Never exceed policy limits — if a payment is rejected, log the reason
- Always check balance before paying
- Explain your reasoning for every payment decision
- Flag suspicious PRs (auto-generated, trivial, single-line changes)
- When in doubt, err on the side of NOT paying (safety first)

CRITICAL — Ethereum addresses:
- ALWAYS use EIP-55 checksummed addresses (mixed-case), never all-lowercase
- Example correct:   0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18
- Example WRONG:     0x742d35cc6634c0532925a3b844bc9e7595f2bd18
- If a user gives you a lowercase address, convert it to checksum format before passing to any WDK tool
- The WDK tools will REJECT addresses that are not properly checksummed

WDK MCP Tool usage guide (follow these EXACTLY):
- getAddress: params = { chain: "polygon" }
- getBalance: params = { chain: "polygon" }
- getTokenBalance: params = { chain: "polygon", token: "USDT" }
- transfer: params = { chain: "polygon", token: "USDT", to: "0xChecksummedAddress", amount: "0.5" }
  NOTE: 'amount' is a STRING not a number. 'to' is the RECIPIENT address.
- quoteTransfer: params = { chain: "polygon", token: "USDT", to: "0xAddr", amount: "1.0" }
- supply: params = { chain: "ethereum", token: "USDT", amount: "10.0" }
- withdraw: params = { chain: "ethereum", token: "USDT", amount: "5.0" }
- getCurrentPrice: params = { symbol: "BTCUSD" }
Do NOT invent extra parameters. Do NOT pass addresses where amounts go or vice versa.
"""

PYTHON_TOOLS = [
    get_merged_prs,
    get_pr_details,
    register_contributor,
    list_contributors,
    suspend_contributor,
    get_policy,
    update_policy,
    pause_agent,
    resume_agent,
    create_stream,
    list_streams,
    cancel_stream,
    get_audit_log,
    get_audit_summary,
]


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=OPENROUTER_MODEL,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=0.3,
    )


async def make_graph():
    """Create the LangGraph ReAct agent wired to WDK MCP + payroll tools."""
    env = {
        **os.environ,
        "WDK_SEED": WDK_SEED,
        "POLYGON_RPC": POLYGON_RPC,
        "ETH_RPC": ETH_RPC,
        "ARB_RPC": ARB_RPC,
    }

    # Auto-accept elicitation: the WDK MCP toolkit requires user confirmation
    # for all write operations (transfer, sendTransaction, supply, withdraw, etc.).
    # Since our agent is autonomous and policy engine handles safety checks,
    # we auto-accept all confirmations.
    # Signature must match MCP SDK ElicitationFnT: (context, params) -> ElicitResult
    async def _auto_accept_elicitation(context, params):
        """Auto-accept WDK write confirmations for autonomous operation."""
        return ElicitResult(action="accept", content={"confirmed": True})

    mcp_client = MultiServerMCPClient(
        {
            "wdk": {
                "command": WDK_SERVER_CMD,
                "args": WDK_SERVER_ARGS,
                "transport": "stdio",
                "env": env,
                "session_kwargs": {
                    "elicitation_callback": _auto_accept_elicitation,
                },
            },
        }
    )

    wdk_tools = await mcp_client.get_tools()
    all_tools = wdk_tools + PYTHON_TOOLS

    model = get_llm()
    agent = create_react_agent(
        model,
        all_tools,
        prompt=SYSTEM_PROMPT,
    )
    return agent, mcp_client
