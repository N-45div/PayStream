"""Payroll DAO internal tools - contributor management, policy, streams."""

from __future__ import annotations
from langchain_core.tools import tool

from core.contributor_registry import contributor_registry
from core.policy_engine import policy_engine
from core.stream_manager import stream_manager
from core.audit_log import audit_log


# ── Contributor management ──────────────────────────────────────────

@tool
def register_contributor(
    github_username: str,
    wallet_address: str,
    role: str = "developer",
    name: str = "",
) -> dict:
    """Register a new contributor to the Payroll DAO.
    Roles: lead, developer, reviewer, designer, intern."""
    try:
        c = contributor_registry.register(github_username, wallet_address, role, name or None)
        audit_log.log("CONTRIBUTOR_REGISTERED", c.to_dict())
        return c.to_dict()
    except ValueError as e:
        return {"error": str(e)}


@tool
def list_contributors() -> list[dict]:
    """List all registered contributors with their roles, rates, and earnings."""
    return contributor_registry.to_list()


@tool
def suspend_contributor(contributor_id: int, reason: str = "Manual") -> dict:
    """Suspend a contributor by ID. They will stop receiving payments."""
    c = contributor_registry.suspend(contributor_id, reason)
    if c:
        audit_log.log("CONTRIBUTOR_SUSPENDED", {"id": contributor_id, "reason": reason})
        return c.to_dict()
    return {"error": "Contributor not found"}


# ── Policy management ───────────────────────────────────────────────

@tool
def get_policy() -> dict:
    """Get current treasury policy (spend limits, min balance, etc.)."""
    return policy_engine.status()


@tool
def update_policy(
    max_daily_spend: float | None = None,
    max_single_payment: float | None = None,
    min_balance: float | None = None,
) -> dict:
    """Update treasury policy. Only provided fields are changed."""
    changes = {}
    if max_daily_spend is not None:
        changes["max_daily_spend"] = max_daily_spend
    if max_single_payment is not None:
        changes["max_single_payment"] = max_single_payment
    if min_balance is not None:
        changes["min_balance"] = min_balance
    if changes:
        policy_engine.update(changes)
        audit_log.log("POLICY_UPDATED", changes)
    return policy_engine.status()


@tool
def pause_agent(reason: str = "Manual pause") -> dict:
    """Pause the agent - stops all payments."""
    policy_engine.pause(reason)
    audit_log.log("AGENT_PAUSED", {"reason": reason})
    return {"paused": True, "reason": reason}


@tool
def resume_agent() -> dict:
    """Resume the agent after being paused."""
    policy_engine.resume()
    audit_log.log("AGENT_RESUMED", {})
    return {"paused": False}


# ── Stream management ───────────────────────────────────────────────

@tool
def create_stream(
    recipient: str,
    total_amount: float,
    duration_seconds: float,
    contributor_id: int | None = None,
    reason: str = "",
) -> dict:
    """Create a payment stream. The agent will autonomously send USDT
    to the recipient over the given duration."""
    s = stream_manager.create(recipient, total_amount, duration_seconds, contributor_id, reason)
    audit_log.log("STREAM_CREATED", s.to_dict())
    return s.to_dict()


@tool
def list_streams() -> list[dict]:
    """List all payment streams with their progress."""
    return stream_manager.to_list()


@tool
def cancel_stream(stream_id: int) -> dict:
    """Cancel an active payment stream."""
    s = stream_manager.cancel(stream_id)
    if s:
        audit_log.log("STREAM_CANCELLED", {"stream_id": stream_id})
        return s.to_dict()
    return {"error": "Stream not found or not active"}


# ── Audit ───────────────────────────────────────────────────────────

@tool
def get_audit_log(limit: int = 30) -> list[dict]:
    """Get recent audit log entries showing all agent decisions."""
    return [e.model_dump() for e in audit_log.get_recent(limit)]


@tool
def get_audit_summary() -> dict:
    """Get summary stats of the audit log."""
    return audit_log.summary()
