from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    backend_url: str
    forward_timeout: float
    forward_auth: str
    env: str
    # MySQL local del Edge (umbrales por categoria + mapeo device -> categoria)
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    @property
    def is_development(self) -> bool:
        return self.env.lower() == "development"

    @property
    def db_configured(self) -> bool:
        return bool(self.db_host)

    @property
    def claim_url(self) -> str:
        """URL del backend para canjear el código de emparejamiento.
        Se deriva de backend_url reemplazando el último segmento por 'claim'
        (p. ej. .../api/edge/readings -> .../api/edge/claim)."""
        if not self.backend_url:
            return ""
        return self.backend_url.rsplit("/", 1)[0] + "/claim"


def load_settings() -> Settings:
    return Settings(
        backend_url=os.environ.get(
            "FRESHSENSE_BACKEND_URL", "http://localhost:8080/api/edge/readings"
        ),
        forward_timeout=float(os.environ.get("FRESHSENSE_FORWARD_TIMEOUT", "5")),
        forward_auth=os.environ.get("FRESHSENSE_FORWARD_AUTH", ""),
        env=os.environ.get("FRESHSENSE_ENV", "development"),
        db_host=os.environ.get("FRESHSENSE_DB_HOST", "localhost"),
        db_port=int(os.environ.get("FRESHSENSE_DB_PORT", "3306")),
        db_user=os.environ.get("FRESHSENSE_DB_USER", "root"),
        db_password=os.environ.get("FRESHSENSE_DB_PASSWORD", "root"),
        db_name=os.environ.get("FRESHSENSE_DB_NAME", "freshsense_edge"),
    )
