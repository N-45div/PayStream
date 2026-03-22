"""FastAPI server - exposes the LangGraph agent + state to the React dashboard."""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import PORT
from core.audit_log import audit_log
from core.policy_engine import policy_engine
from core.contributor_registry import contributor_registry
from core.stream_manager import stream_manager
from graph import make_graph


# ── State ────────────────────────────────────────────────────────────

agent_ref: dict[str, Any] = {"agent": None, "mcp_ctx": None, "running": False, "tick_count": 0}


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the LangGraph agent on server boot."""
    agent, mcp_client = await make_graph()
    agent_ref["agent"] = agent
    agent_ref["mcp_client"] = mcp_client
    yield
    agent_ref["agent"] = None
    agent_ref["mcp_client"] = None


app = FastAPI(title="PayStream — Autonomous Payroll DAO", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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
    agent = agent_ref["agent"]
    if not agent:
        return {"error": "Agent not initialized"}
    result = await agent.ainvoke({"messages": [{"role": "user", "content": req.message}]})
    messages = result.get("messages", [])
    # Return the last AI message
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai":
            return {"response": msg.content, "tool_calls": len([m for m in messages if m.type == "tool"])}
    return {"response": "No response", "tool_calls": 0}


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


# ── Health ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "agent_loaded": agent_ref["agent"] is not None,
        "contributors": len(contributor_registry.get_all()),
        "active_streams": len(stream_manager.active()),
        "policy": policy_engine.status(),
    }


# ── Run ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
