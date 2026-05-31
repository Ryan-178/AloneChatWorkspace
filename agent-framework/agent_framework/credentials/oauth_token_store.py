"""
OAuth token store - high-level API for OAuth token lifecycle management
Stores tokens securely using platform-native keychain or encrypted file fallback
"""
from __future__ import annotations
import time
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from agent_framework.credentials.credential_store import (
    CredentialStore,
    CredentialType,
    StoredCredential,
)


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    acquired_at: float = field(default_factory=time.time)
    scope: Optional[str] = None
    provider: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_in is None:
            return False
        elapsed = time.time() - self.acquired_at
        return elapsed >= self.expires_in

    @property
    def remaining_seconds(self) -> Optional[int]:
        if self.expires_in is None:
            return None
        remaining = self.expires_in - (time.time() - self.acquired_at)
        return max(0, int(remaining))

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "acquired_at": self.acquired_at,
            "scope": self.scope,
            "provider": self.provider,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OAuthToken":
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            acquired_at=data.get("acquired_at", time.time()),
            scope=data.get("scope"),
            provider=data.get("provider", "unknown"),
            metadata=data.get("metadata", {}),
        )


class OAuthTokenStore:
    """
    High-level OAuth token management with secure storage.
    Handles token storage, retrieval, refresh, and cleanup.
    """

    def __init__(self, app_name: str = "AloneChat"):
        self._store = CredentialStore(app_name=app_name)
        self._app_name = app_name

    def save_token(self, provider: str, token: OAuthToken) -> bool:
        stored = StoredCredential(
            service=f"{self._app_name}_oauth",
            username=provider,
            credential_type=CredentialType.OAUTH_TOKEN,
            secret=json.dumps(token.to_dict()),
            metadata={
                "provider": provider,
                "acquired_at": token.acquired_at,
                "expires_in": token.expires_in,
            },
        )
        return self._store.store(stored)

    def get_token(self, provider: str) -> Optional[OAuthToken]:
        credential = self._store.retrieve(
            service=f"{self._app_name}_oauth",
            username=provider,
        )
        if credential is None:
            return None

        try:
            data = json.loads(credential.secret)
            return OAuthToken.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def get_valid_token(self, provider: str) -> Optional[OAuthToken]:
        token = self.get_token(provider)
        if token is None:
            return None
        if token.is_expired:
            return token
        return token

    def delete_token(self, provider: str) -> bool:
        return self._store.delete(
            service=f"{self._app_name}_oauth",
            username=provider,
        )

    def save_api_key(self, provider: str, api_key: str) -> bool:
        stored = StoredCredential(
            service=f"{self._app_name}_apikey",
            username=provider,
            credential_type=CredentialType.API_KEY,
            secret=api_key,
            metadata={"provider": provider},
        )
        return self._store.store(stored)

    def get_api_key(self, provider: str) -> Optional[str]:
        credential = self._store.retrieve(
            service=f"{self._app_name}_apikey",
            username=provider,
        )
        if credential is None:
            return None
        return credential.secret

    def list_providers(self) -> list:
        services = self._store.list_services()
        providers = set()
        for s in services:
            if s.endswith("_oauth") or s.endswith("_apikey"):
                providers.add(s)
        return list(providers)
