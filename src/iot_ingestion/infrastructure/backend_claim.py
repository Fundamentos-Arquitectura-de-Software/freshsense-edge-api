from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class BackendClaimClient:
    """Canjea el código de emparejamiento contra el backend
    (POST {claim_url} {code}) y devuelve (deviceId, secretKey)."""

    def __init__(self, claim_url: str, timeout: float) -> None:
        self._claim_url = claim_url
        self._timeout = timeout

    def claim(self, code: str) -> tuple[str, str] | None:
        if not self._claim_url:
            logger.warning("No hay claim_url configurada; no se puede canjear el código")
            return None
        try:
            response = requests.post(
                self._claim_url, json={"code": code}, timeout=self._timeout
            )
            if not (200 <= response.status_code < 300):
                logger.warning("El backend rechazó el código (%s): %s",
                               response.status_code, response.text)
                return None
            body = response.json()
            device_id = body.get("deviceId")
            secret_key = body.get("secretKey")
            if not device_id or not secret_key:
                return None
            return device_id, secret_key
        except requests.RequestException as exc:
            logger.warning("Fallo al canjear el código contra el backend: %s", exc)
            return None
