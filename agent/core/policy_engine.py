"""Policy engine - enforces treasury rules before any payment."""

from __future__ import annotations
from datetime import date
from typing import Any

from .config import DEFAULT_POLICY


class PolicyEngine:
    def __init__(self) -> None:
        self.policy = dict(DEFAULT_POLICY)
        self.daily_spent: float = 0.0
        self._last_reset: str = str(date.today())
        self.paused: bool = False
        self.pause_reason: str | None = None

    def update(self, changes: dict[str, Any]) -> dict:
        self.policy.update(changes)
        return self.policy

    def pause(self, reason: str = "Manual pause") -> None:
        self.paused = True
        self.pause_reason = reason

    def resume(self) -> None:
        self.paused = False
        self.pause_reason = None

    def _reset_daily(self) -> None:
        today = str(date.today())
        if today != self._last_reset:
            self.daily_spent = 0.0
            self._last_reset = today

    def can_pay(self, recipient: str, amount: float, balance: float) -> dict:
        """Check all policy rules. Returns {allowed, reason, checks}."""
        self._reset_daily()
        checks: list[dict] = []

        if self.paused:
            return {"allowed": False, "reason": f"Paused: {self.pause_reason}", "checks": checks}

        # Single payment limit
        ok = amount <= self.policy["max_single_payment"]
        checks.append({"rule": "max_single", "ok": ok, "detail": f"{amount} vs max {self.policy['max_single_payment']}"})
        if not ok:
            return {"allowed": False, "reason": "Exceeds single payment limit", "checks": checks}

        # Daily spend limit
        ok = (self.daily_spent + amount) <= self.policy["max_daily_spend"]
        checks.append({"rule": "max_daily", "ok": ok, "detail": f"today {self.daily_spent}+{amount} vs max {self.policy['max_daily_spend']}"})
        if not ok:
            return {"allowed": False, "reason": "Daily spend limit reached", "checks": checks}

        # Minimum balance
        after = balance - amount
        ok = after >= self.policy["min_balance"]
        checks.append({"rule": "min_balance", "ok": ok, "detail": f"after={after:.2f} vs min {self.policy['min_balance']}"})
        if not ok:
            if self.policy["auto_pause_low_balance"]:
                self.pause("Low balance")
            return {"allowed": False, "reason": "Would breach min balance", "checks": checks}

        return {"allowed": True, "reason": "All checks passed", "checks": checks}

    def record_payment(self, amount: float) -> None:
        self.daily_spent += amount

    def status(self) -> dict:
        return {
            "paused": self.paused,
            "pause_reason": self.pause_reason,
            "daily_spent": self.daily_spent,
            **self.policy,
        }


policy_engine = PolicyEngine()
