"""Persistent API-key authentication and rate limiting."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


class APIKeyError(Exception):
    """Raised when an API key is missing or invalid."""


class RateLimitError(Exception):
    """Raised when an API key exceeds its request limit."""

    def __init__(self, retry_after: int):
        super().__init__("API rate limit exceeded.")
        self.retry_after = retry_after


class APISecurity:
    """Store hashed API keys and request events in a SQL database."""

    def __init__(
        self,
        database_url: str,
        rate_limit_per_minute: int = 60,
    ):
        if rate_limit_per_minute < 1:
            raise ValueError("rate_limit_per_minute must be at least 1.")
        try:
            from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
            from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
        except ImportError as exc:
            raise RuntimeError(
                "Install API database support with: pip install 'scvp[api-security]'"
            ) from exc

        class Base(DeclarativeBase):
            pass

        class APIKey(Base):
            __tablename__ = "scvp_api_keys"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str] = mapped_column(String(120))
            key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
            active: Mapped[bool] = mapped_column(Boolean, default=True)
            created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

        class RequestEvent(Base):
            __tablename__ = "scvp_api_request_events"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            api_key_id: Mapped[int] = mapped_column(ForeignKey("scvp_api_keys.id"), index=True)
            path: Mapped[str] = mapped_column(String(255))
            created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

        self._engine = create_engine(database_url, future=True)
        self._Base = Base
        self._APIKey = APIKey
        self._RequestEvent = RequestEvent
        self._Session = Session
        self.rate_limit_per_minute = rate_limit_per_minute
        Base.metadata.create_all(self._engine)

    @staticmethod
    def _hash(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def create_key(self, name: str) -> str:
        if not name.strip():
            raise ValueError("name must not be empty.")
        raw_key = "scvp_" + secrets.token_urlsafe(32)
        with self._Session(self._engine) as session:
            session.add(
                self._APIKey(
                    name=name,
                    key_hash=self._hash(raw_key),
                    active=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()
        return raw_key

    def authorize(self, raw_key: Optional[str], path: str) -> None:
        if not raw_key:
            raise APIKeyError("X-API-Key header is required.")
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=1)
        with self._Session(self._engine) as session:
            key = session.query(self._APIKey).filter_by(
                key_hash=self._hash(raw_key), active=True
            ).one_or_none()
            if key is None:
                raise APIKeyError("Invalid API key.")
            count = session.query(self._RequestEvent).filter(
                self._RequestEvent.api_key_id == key.id,
                self._RequestEvent.created_at >= window_start,
            ).count()
            if count >= self.rate_limit_per_minute:
                raise RateLimitError(60)
            session.add(self._RequestEvent(api_key_id=key.id, path=path, created_at=now))
            session.commit()

    def usage(self) -> Dict[str, Any]:
        with self._Session(self._engine) as session:
            rows = session.query(self._APIKey).order_by(self._APIKey.created_at).all()
            return {
                "keys": [
                    {
                        "id": row.id,
                        "name": row.name,
                        "active": row.active,
                        "created_at": row.created_at.isoformat(),
                        "requests_last_minute": session.query(self._RequestEvent).filter(
                            self._RequestEvent.api_key_id == row.id,
                            self._RequestEvent.created_at >= datetime.now(timezone.utc) - timedelta(minutes=1),
                        ).count(),
                    }
                    for row in rows
                ]
            }

    def revoke(self, key_id: int) -> bool:
        with self._Session(self._engine) as session:
            row = session.get(self._APIKey, key_id)
            if row is None:
                return False
            row.active = False
            session.commit()
            return True

    @staticmethod
    def valid_admin_token(provided: Optional[str], expected: Optional[str]) -> bool:
        return bool(provided and expected and hmac.compare_digest(provided, expected))