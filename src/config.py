from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    backend_url: str
    forward_timeout: float
    forward_auth: str
    env: str

    @property
    def is_development(self) -> bool:
        return self.env.lower() == "development"


def load_settings() -> Settings:
    return Settings(
        backend_url=os.environ.get(
            "FRESHSENSE_BACKEND_URL", "http://localhost:8080/api/edge/readings"
        ),
        forward_timeout=float(os.environ.get("FRESHSENSE_FORWARD_TIMEOUT", "5")),
        forward_auth=os.environ.get("FRESHSENSE_FORWARD_AUTH", ""),
        env=os.environ.get("FRESHSENSE_ENV", "development"),
    )
