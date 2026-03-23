"""FastAPI server - exposes the LangGraph agent + autonomous background loop."""

from __future__ import annotations
import asyncio
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.config import PORT, DEFAULT_POLICY, GITHUB_REPO
from core.audit_log import audit_log
from core.policy_engine import policy_engine
from core.contributor_registry import contributor_registry
from core.stream_manager import stream_manager
from graph import make_graph


# ── State ────────────────────────────────────────────────────────────

_agent_lock = asyncio.Lock()

agent_ref: dict[str, Any] = {
    "agent": None,
    "mcp_client": None,
    "running": False,
    "tick_count": 0,
    "last_tick_time": None,
    "last_tick_result": None,
    "processed_prs": set(),       # PR numbers already processed
    "autonomous_enabled": False,    # Off by default — enable via dashboard
    "tick_task": None,
    "github_repo": GITHUB_REPO,   # mutable at runtime from dashboard
}


# ── Autonomous Loop ──────────────────────────────────────────────────

async def _agent_invoke(message: str, timeout: float = 120) -> dict:
    """Send a message to the agent and return the last AI response."""
    agent = agent_ref["agent"]
    if not agent:
        return {"response": "Agent not ready", "tool_calls": 0}
    try:
        async with _agent_lock:
            result = await asyncio.wait_for(
                agent.ainvoke({"messages": [{"role": "user", "content": message}]}),
                timeout=timeout,
            )
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.type == "ai":
                return {"response": msg.content, "tool_calls": len([m for m in messages if m.type == "tool"])}
        return {"response": "No response", "tool_calls": 0}
    except asyncio.TimeoutError:
        audit_log.log("AGENT_INVOKE_TIMEOUT", {"prompt": message[:100]})
        return {"response": "Request timed out after 120s. Try a simpler query.", "tool_calls": 0}
    except Exception as e:
        err_msg = str(e)[:300]
        audit_log.log("AGENT_INVOKE_ERROR", {"error": err_msg, "prompt": message[:100]})
        return {"response": f"Error: {err_msg}", "tool_calls": 0}


async def _autonomous_tick():
    """One autonomous tick: check PRs, process streams, manage yield."""
    tick_results = []

    # 1. Process active streams (pay due amounts)
    active_streams = stream_manager.active()
    for s in active_streams:
        due = s.due_amount()
        if due >= 0.01:  # minimum $0.01 to avoid dust
            check = policy_engine.can_pay(s.recipient, due, float('inf'))  # balance checked by agent
            if check["allowed"]:
                prompt = (
                    f"A payment stream #{s.id} has ${due:.2f} USDT due for recipient {s.recipient}. "
                    f"Reason: {s.reason}. Please execute this transfer on Polygon using the WDK transfer tool. "
                    f"After sending, report the transaction hash."
                )
                result = await _agent_invoke(prompt)
                tick_results.append({"type": "stream_payment", "stream_id": s.id, "amount": due, "result": result["response"], "tool_calls": result["tool_calls"]})
                audit_log.log("AUTONOMOUS_STREAM_TICK", {"stream_id": s.id, "due": due})

    # 2. Check GitHub for new merged PRs (if configured)
    github_repo = agent_ref.get("github_repo", "")
    if github_repo and contributor_registry.get_active():
        prompt = (
            f"TASK: GitHub PR scan ONLY. Do NOT touch Aave, do NOT do yield management.\n\n"
            f"Check the GitHub repo '{github_repo}' for recently merged pull requests. "
            f"For each merged PR by a registered contributor that hasn't been paid yet, "
            f"evaluate the work quality, calculate a fair bounty based on their role and effort, "
            f"run the policy check, and if approved, execute the USDT payment via WDK on Polygon. "
            f"Already processed PR numbers (skip these): {list(agent_ref['processed_prs'])}. "
            f"Report what you did for each PR. Only use GitHub and payment tools."
        )
        result = await _agent_invoke(prompt)
        tick_results.append({"type": "github_scan", "result": result["response"], "tool_calls": result["tool_calls"]})
        audit_log.log("AUTONOMOUS_GITHUB_SCAN", {"tool_calls": result["tool_calls"]})

    # 3. Treasury yield management — check if idle USDT should go to Aave (every 10th tick)
    if agent_ref["tick_count"] % 10 == 0:
        prompt = (
            "Check the treasury USDT balance on Polygon. If the balance is significantly above "
            "the minimum reserve (more than 2x the min_balance policy), consider supplying the "
            "excess to Aave V3 on Ethereum to earn yield. If there's already USDT supplied to Aave "
            "and we need funds for upcoming stream payments, consider withdrawing. "
            "Report your decision and reasoning."
        )
        result = await _agent_invoke(prompt)
        tick_results.append({"type": "yield_management", "result": result["response"], "tool_calls": result["tool_calls"]})
        audit_log.log("AUTONOMOUS_YIELD_CHECK", {"tool_calls": result["tool_calls"]})

    return tick_results


async def _autonomous_loop():
    """Background loop that runs autonomous ticks at configured intervals."""
    await asyncio.sleep(5)  # initial delay to let everything start
    audit_log.log("AUTONOMOUS_LOOP_STARTED", {"interval_s": DEFAULT_POLICY["tick_interval_s"]})

    while True:
        interval = policy_engine.policy.get("tick_interval_s", 30)
        try:
            if agent_ref["autonomous_enabled"] and not policy_engine.paused and agent_ref["agent"]:
                # Skip tick if a chat request is in progress
                if _agent_lock.locked():
                    await asyncio.sleep(interval)
                    continue
                agent_ref["tick_count"] += 1
                agent_ref["last_tick_time"] = time.time()
                results = await _autonomous_tick()
                agent_ref["last_tick_result"] = {
                    "tick": agent_ref["tick_count"],
                    "time": time.time(),
                    "results": results,
                }
        except Exception as e:
            audit_log.log("AUTONOMOUS_TICK_ERROR", {"error": str(e), "traceback": traceback.format_exc()[:500]})
        await asyncio.sleep(interval)


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the LangGraph agent and autonomous loop on server boot."""
    agent, mcp_client = await make_graph()
    agent_ref["agent"] = agent
    agent_ref["mcp_client"] = mcp_client
    # Start autonomous background loop
    agent_ref["tick_task"] = asyncio.create_task(_autonomous_loop())
    audit_log.log("AGENT_STARTED", {"tools": "35 (21 MCP + 14 Python)"})
    yield
    # Shutdown
    if agent_ref["tick_task"]:
        agent_ref["tick_task"].cancel()
    agent_ref["agent"] = None
    agent_ref["mcp_client"] = None


app = FastAPI(title="PayStream — Autonomous Payroll DAO", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Autonomous control endpoints ─────────────────────────────────────

@app.get("/api/autonomous/status")
async def autonomous_status():
    return {
        "enabled": agent_ref["autonomous_enabled"],
        "tick_count": agent_ref["tick_count"],
        "last_tick_time": agent_ref["last_tick_time"],
        "last_tick_result": agent_ref["last_tick_result"],
        "processed_prs": list(agent_ref["processed_prs"]),
        "interval_s": policy_engine.policy.get("tick_interval_s", 30),
    }

@app.post("/api/autonomous/enable")
async def autonomous_enable():
    agent_ref["autonomous_enabled"] = True
    audit_log.log("AUTONOMOUS_ENABLED", {})
    return {"enabled": True}

@app.post("/api/autonomous/disable")
async def autonomous_disable():
    agent_ref["autonomous_enabled"] = False
    audit_log.log("AUTONOMOUS_DISABLED", {})
    return {"enabled": False}

@app.post("/api/autonomous/trigger")
async def autonomous_trigger():
    """Manually trigger one autonomous tick (for demo)."""
    if not agent_ref["agent"]:
        return {"error": "Agent not ready"}
    agent_ref["tick_count"] += 1
    agent_ref["last_tick_time"] = time.time()
    try:
        results = await _autonomous_tick()
        agent_ref["last_tick_result"] = {
            "tick": agent_ref["tick_count"],
            "time": time.time(),
            "results": results,
        }
        return agent_ref["last_tick_result"]
    except Exception as e:
        return {"error": str(e)}


# ── Request models ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class ContributorRequest(BaseModel):
    github_username: str
    wallet_address: str
    role: str = "developer"
    name: str = ""

class StreamRequest(BaseModel):
    recipient: str
    total_amount: float
    duration_seconds: float
    contributor_id: int | None = None
    reason: str = ""

class PolicyRequest(BaseModel):
    max_daily_spend: float | None = None
    max_single_payment: float | None = None
    min_balance: float | None = None


# ── Chat (agent reasoning) ──────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Send a message to the AI agent. It can reason, check balances, pay people, etc."""
    result = await _agent_invoke(req.message)
    return result


# ── Contributors ─────────────────────────────────────────────────────

@app.get("/api/contributors")
async def get_contributors():
    return contributor_registry.to_list()

@app.post("/api/contributors")
async def add_contributor(req: ContributorRequest):
    try:
        c = contributor_registry.register(req.github_username, req.wallet_address, req.role, req.name or None)
        audit_log.log("CONTRIBUTOR_REGISTERED", c.to_dict())
        return c.to_dict()
    except ValueError as e:
        return {"error": str(e)}


# ── Streams ──────────────────────────────────────────────────────────

@app.get("/api/streams")
async def get_streams():
    return stream_manager.to_list()

@app.post("/api/streams")
async def add_stream(req: StreamRequest):
    s = stream_manager.create(req.recipient, req.total_amount, req.duration_seconds, req.contributor_id, req.reason)
    audit_log.log("STREAM_CREATED", s.to_dict())
    return s.to_dict()

@app.post("/api/streams/{stream_id}/cancel")
async def api_cancel_stream(stream_id: int):
    s = stream_manager.cancel(stream_id)
    if s:
        audit_log.log("STREAM_CANCELLED", {"stream_id": stream_id})
        return s.to_dict()
    return {"error": "Not found or not active"}


# ── Policy ───────────────────────────────────────────────────────────

@app.get("/api/policy")
async def api_get_policy():
    return policy_engine.status()

@app.put("/api/policy")
async def api_update_policy(req: PolicyRequest):
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    if changes:
        policy_engine.update(changes)
        audit_log.log("POLICY_UPDATED", changes)
    return policy_engine.status()

@app.post("/api/policy/pause")
async def api_pause():
    policy_engine.pause("Manual pause from dashboard")
    audit_log.log("AGENT_PAUSED", {"reason": "dashboard"})
    return policy_engine.status()

@app.post("/api/policy/resume")
async def api_resume():
    policy_engine.resume()
    audit_log.log("AGENT_RESUMED", {})
    return policy_engine.status()


# ── Audit ────────────────────────────────────────────────────────────

@app.get("/api/audit")
async def api_audit(limit: int = 50):
    return [e.model_dump() for e in audit_log.get_recent(limit)]

@app.get("/api/audit/summary")
async def api_audit_summary():
    return audit_log.summary()


# ── Wallet ──────────────────────────────────────────────────────────

@app.get("/api/wallet/address")
async def wallet_address():
    """Ask the agent for the treasury wallet address."""
    result = await _agent_invoke(
        "What is our wallet address on Polygon? Just return the address, nothing else."
    )
    return result


# ── Settings (GitHub repo, etc.) ─────────────────────────────────────

class SettingsRequest(BaseModel):
    github_repo: str | None = None

@app.get("/api/settings")
async def get_settings():
    return {"github_repo": agent_ref["github_repo"]}

@app.put("/api/settings")
async def update_settings(req: SettingsRequest):
    if req.github_repo is not None:
        agent_ref["github_repo"] = req.github_repo
        audit_log.log("SETTINGS_UPDATED", {"github_repo": req.github_repo})
    return {"github_repo": agent_ref["github_repo"]}


# ── Health ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agent_loaded": agent_ref["agent"] is not None,
        "contributors": len(contributor_registry.get_all()),
        "active_streams": len(stream_manager.active()),
        "policy": policy_engine.status(),
        "autonomous": {
            "enabled": agent_ref["autonomous_enabled"],
            "tick_count": agent_ref["tick_count"],
            "last_tick_time": agent_ref["last_tick_time"],
        },
    }


# ── Static dashboard (production) ────────────────────────────────────

DASHBOARD_DIR = Path(__file__).parent.parent / "dashboard" / "dist"
if DASHBOARD_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(DASHBOARD_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA — any non-API route returns index.html."""
        file_path = DASHBOARD_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DASHBOARD_DIR / "index.html"))


# ── Run ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
