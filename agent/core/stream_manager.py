"""Stream manager - tracks payment streams (continuous salary / bounty payouts)."""

from __future__ import annotations
import time
from typing import Any


class Stream:
    def __init__(
        self,
        id: int,
        recipient: str,
        contributor_id: int | None,
        total_amount: float,
        duration_s: float,
        reason: str = "",
    ) -> None:
        self.id = id
        self.recipient = recipient
        self.contributor_id = contributor_id
        self.total_amount = total_amount
        self.duration_s = duration_s
        self.rate_per_s = total_amount / duration_s if duration_s > 0 else 0
        self.start_time = time.time()
        self.end_time = self.start_time + duration_s
        self.amount_paid: float = 0.0
        self.status = "active"  # active, completed, cancelled
        self.payments: list[dict] = []
        self.reason = reason
        self.created_at = time.time()

    def due_amount(self) -> float:
        if self.status != "active":
            return 0.0
        now = time.time()
        if now < self.start_time:
            return 0.0
        elapsed = min(now - self.start_time, self.duration_s)
        total_due = elapsed * self.rate_per_s
        due = total_due - self.amount_paid
        remaining = self.total_amount - self.amount_paid
        return min(max(due, 0), remaining)

    def record_payment(self, amount: float, tx_hash: str) -> None:
        self.amount_paid += amount
        self.payments.append({"amount": amount, "tx_hash": tx_hash, "ts": time.time()})
        if self.amount_paid >= self.total_amount:
            self.status = "completed"

    def cancel(self) -> None:
        self.status = "cancelled"

    def progress(self) -> dict:
        now = time.time()
        elapsed = max(0, min(now - self.start_time, self.duration_s))
        return {
            "elapsed_s": round(elapsed, 1),
            "progress_pct": round(elapsed / self.duration_s * 100, 1) if self.duration_s else 100,
            "paid_pct": round(self.amount_paid / self.total_amount * 100, 1) if self.total_amount else 100,
            "remaining": round(self.total_amount - self.amount_paid, 6),
            "time_remaining_s": round(max(0, self.end_time - now), 1),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "recipient": self.recipient,
            "contributor_id": self.contributor_id,
            "total_amount": self.total_amount,
            "amount_paid": self.amount_paid,
            "status": self.status,
            "reason": self.reason,
            "payments": self.payments,
            "progress": self.progress(),
        }


class StreamManager:
    def __init__(self) -> None:
        self._streams: dict[int, Stream] = {}
        self._next_id = 1

    def create(
        self,
        recipient: str,
        total_amount: float,
        duration_s: float,
        contributor_id: int | None = None,
        reason: str = "",
    ) -> Stream:
        s = Stream(self._next_id, recipient, contributor_id, total_amount, duration_s, reason)
        self._streams[s.id] = s
        self._next_id += 1
        return s

    def get(self, sid: int) -> Stream | None:
        return self._streams.get(sid)

    def active(self) -> list[Stream]:
        return [s for s in self._streams.values() if s.status == "active"]

    def all(self) -> list[Stream]:
        return list(self._streams.values())

    def cancel(self, sid: int) -> Stream | None:
        s = self._streams.get(sid)
        if s and s.status == "active":
            s.cancel()
        return s

    def to_list(self) -> list[dict]:
        return [s.to_dict() for s in self._streams.values()]


stream_manager = StreamManager()
