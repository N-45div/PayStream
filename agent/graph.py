"""LangGraph agent that connects to the WDK MCP server and payroll tools."""

from __future__ import annotations
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

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

SYSTEM_PROMPT = """You are the AI Treasurer of PayStream, an Autonomous Payroll DAO.
You manage a self-custodial treasury wallet via Tether WDK (multi-chain USDT).
Your job is to autonomously reward contributors for their work.

Your capabilities:
1. WALLET: Check balances, send USDT, supply/withdraw from Aave V3 (via WDK MCP tools)
2. GITHUB: Monitor merged PRs, evaluate contributor work
3. PAYROLL: Register contributors, create payment streams, enforce policy
4. AUDIT: Every decision you make is logged for transparency

Decision process for paying a contributor:
1. Check if contributor is registered
2. Evaluate the PR (size, quality, labels)
3. Calculate fair payment based on role + effort
4. Check policy (daily limit, single tx limit, min balance)
5. Execute USDT transfer via WDK
6. Log everything

Rules:
- Never exceed policy limits
- Always check balance before paying
- Use Aave V3 to earn yield on idle treasury
- Explain your reasoning for every payment decision
- Flag suspicious PRs (auto-generated, trivial, etc.)
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

    mcp_client = MultiServerMCPClient(
        {
            "wdk": {
                "command": WDK_SERVER_CMD,
                "args": WDK_SERVER_ARGS,
                "transport": "stdio",
                "env": env,
            },
        }
    )

    # New API (v0.1.0+): no context manager, just await get_tools()
    wdk_tools = await mcp_client.get_tools()
    all_tools = wdk_tools + PYTHON_TOOLS

    model = get_llm()
    agent = create_react_agent(
        model,
        all_tools,
        prompt=SYSTEM_PROMPT,
    )
    return agent, mcp_client
