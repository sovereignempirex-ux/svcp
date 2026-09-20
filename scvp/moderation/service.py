"""Deterministic moderation policy with temporary and permanent bans."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional


class ViolationCategory(str, Enum):
    SEXUAL_EXPLICIT = "sexual_explicit"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    ILLEGAL = "illegal"


class BanStatus(str, Enum):
    NONE = "none"
    TEMPORARY = "temporary"
    PERMANENT = "permanent"


@dataclass(frozen=True)
class ModerationDecision:
    allowed: bool
    category: Optional[ViolationCategory] = None
    severity: int = 0
    ban_status: BanStatus = BanStatus.NONE
    reason: str = ""


@dataclass
class _Account:
    violations: List[datetime]
    temp_until: Optional[datetime] = None
    permanently_banned: bool = False


class ModerationService:
    """Moderate text and apply an auditable ban policy per actor id.

    The default detector is intentionally conservative and deterministic. A
    production deployment can replace ``moderate`` with an external provider
    while retaining the same ban policy and API contract.
    """

    _RULES = (
        (ViolationCategory.SELF_HARM, 3, re.compile(r"\b(suicide|self[- ]harm|kill myself)\b|انتحار|إيذاء النفس", re.I)),
        (ViolationCategory.VIOLENCE, 3, re.compile(r"\b(bomb|terrorist attack|massacre|murder)\b|تفجير|مجزرة|قتل جماعي", re.I)),
        (ViolationCategory.ILLEGAL, 2, re.compile(r"\b(build a bomb|buy illegal drugs|credit card fraud)\b|صنع قنبلة|مخدرات|احتيال", re.I)),
        (ViolationCategory.SEXUAL_EXPLICIT, 2, re.compile(r"\b(porn|xxx|nsfw|sex video|nude|naked)\b|إباحي|عري|جنس صريح", re.I)),
    )

    def __init__(self, violations_before_temp_ban: int = 3, temp_ban_minutes: int = 60):
        if violations_before_temp_ban < 1 or temp_ban_minutes < 1:
            raise ValueError("Ban policy values must be greater than zero.")
        self.violations_before_temp_ban = violations_before_temp_ban
        self.temp_ban_minutes = temp_ban_minutes
        self._accounts: Dict[str, _Account] = {}

    def moderate(self, actor_id: str, text: str) -> ModerationDecision:
        if not actor_id:
            raise ValueError("actor_id must not be empty.")
        if not isinstance(text, str):
            raise TypeError("text must be a string.")
        account = self._accounts.setdefault(actor_id, _Account([]))
        now = datetime.now(timezone.utc)
        self._expire_old_violations(account, now)
        active_ban = self._ban_status(account, now)
        if active_ban != BanStatus.NONE:
            return ModerationDecision(False, ban_status=active_ban, reason="actor_banned")

        match = next(((category, severity) for category, severity, rule in self._RULES if rule.search(text)), None)
        if match is None:
            return ModerationDecision(True)

        category, severity = match
        account.violations.append(now)
        if severity >= 3 or len(account.violations) >= self.violations_before_temp_ban * 2:
            account.permanently_banned = True
            status = BanStatus.PERMANENT
        elif len(account.violations) >= self.violations_before_temp_ban:
            account.temp_until = now + timedelta(minutes=self.temp_ban_minutes)
            status = BanStatus.TEMPORARY
        else:
            status = BanStatus.NONE
        return ModerationDecision(False, category, severity, status, "content_policy_violation")

    def unban(self, actor_id: str) -> bool:
        account = self._accounts.get(actor_id)
        if account is None:
            return False
        account.temp_until = None
        account.permanently_banned = False
        account.violations.clear()
        return True

    def ban_status(self, actor_id: str) -> BanStatus:
        account = self._accounts.get(actor_id)
        return self._ban_status(account, datetime.now(timezone.utc)) if account else BanStatus.NONE

    def _ban_status(self, account: Optional[_Account], now: datetime) -> BanStatus:
        if account is None:
            return BanStatus.NONE
        if account.permanently_banned:
            return BanStatus.PERMANENT
        if account.temp_until and account.temp_until > now:
            return BanStatus.TEMPORARY
        account.temp_until = None
        return BanStatus.NONE

    @staticmethod
    def _expire_old_violations(account: _Account, now: datetime) -> None:
        cutoff = now - timedelta(hours=1)
        account.violations[:] = [event for event in account.violations if event > cutoff]