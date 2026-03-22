"""Contributor registry - manages team members, roles, wallet addresses."""

from __future__ import annotations
from typing import Any

from .config import ROLES


class Contributor:
    def __init__(
        self,
        id: int,
        github_username: str,
        wallet_address: str,
        role: str = "developer",
        name: str | None = None,
        custom_rate: float | None = None,
    ) -> None:
        role_cfg = ROLES.get(role)
        if not role_cfg:
            raise ValueError(f"Unknown role: {role}. Valid: {list(ROLES)}")
        self.id = id
        self.github_username = github_username.lower()
        self.wallet_address = wallet_address.lower()
        self.name = name or github_username
        self.role = role
        self.role_label = role_cfg["label"]
        self.hourly_rate = custom_rate if custom_rate else role_cfg["hourly_rate"]
        self.status = "active"
        self.total_earned: float = 0.0
        self.total_payments: int = 0
        self.prs_processed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "github_username": self.github_username,
            "wallet_address": self.wallet_address,
            "name": self.name,
            "role": self.role,
            "role_label": self.role_label,
            "hourly_rate": self.hourly_rate,
            "status": self.status,
            "total_earned": self.total_earned,
            "total_payments": self.total_payments,
            "prs_processed": self.prs_processed,
        }


class ContributorRegistry:
    def __init__(self) -> None:
        self._contributors: dict[int, Contributor] = {}
        self._next_id = 1

    def register(
        self,
        github_username: str,
        wallet_address: str,
        role: str = "developer",
        name: str | None = None,
        custom_rate: float | None = None,
    ) -> Contributor:
        existing = self.get_by_github(github_username)
        if existing:
            raise ValueError(f"@{github_username} already registered")
        c = Contributor(self._next_id, github_username, wallet_address, role, name, custom_rate)
        self._contributors[c.id] = c
        self._next_id += 1
        return c

    def get_by_id(self, cid: int) -> Contributor | None:
        return self._contributors.get(cid)

    def get_by_github(self, username: str) -> Contributor | None:
        u = username.lower()
        return next((c for c in self._contributors.values() if c.github_username == u), None)

    def get_active(self) -> list[Contributor]:
        return [c for c in self._contributors.values() if c.status == "active"]

    def get_all(self) -> list[Contributor]:
        return list(self._contributors.values())

    def suspend(self, cid: int, reason: str = "Manual") -> Contributor | None:
        c = self._contributors.get(cid)
        if c:
            c.status = "suspended"
        return c

    def activate(self, cid: int) -> Contributor | None:
        c = self._contributors.get(cid)
        if c:
            c.status = "active"
        return c

    def record_payment(self, cid: int, amount: float) -> None:
        c = self._contributors.get(cid)
        if c:
            c.total_earned += amount
            c.total_payments += 1

    def to_list(self) -> list[dict]:
        return [c.to_dict() for c in self._contributors.values()]


contributor_registry = ContributorRegistry()
