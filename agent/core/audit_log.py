"""Immutable audit log for all agent decisions and actions."""

from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel


class AuditEntry(BaseModel):
    id: int
    timestamp: float
    iso_time: str
    entry_type: str
    data: dict[str, Any]


class AuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def log(self, entry_type: str, data: dict[str, Any] | None = None) -> AuditEntry:
        data = data or {}
        entry = AuditEntry(
            id=len(self._entries) + 1,
            timestamp=time.time(),
            iso_time=datetime.now(timezone.utc).isoformat(),
            entry_type=entry_type,
            data=data,
        )
        self._entries.append(entry)
        return entry

    def get_recent(self, count: int = 50) -> list[AuditEntry]:
        return self._entries[-count:]

    def get_by_type(self, entry_type: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.entry_type == entry_type]

    def get_payments(self) -> list[AuditEntry]:
        return [
            e for e in self._entries
            if e.entry_type in ("PAYMENT_SUCCESS", "PAYMENT_FAILED")
        ]

    def summary(self) -> dict[str, Any]:
        payments = self.get_payments()
        ok = [p for p in payments if p.entry_type == "PAYMENT_SUCCESS"]
        return {
            "total_entries": len(self._entries),
            "total_payments": len(payments),
            "successful": len(ok),
            "failed": len(payments) - len(ok),
            "total_paid": sum(p.data.get("amount", 0) for p in ok),
        }

    def to_list(self) -> list[dict]:
        return [e.model_dump() for e in self._entries]


audit_log = AuditLog()
