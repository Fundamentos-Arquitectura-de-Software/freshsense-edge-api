from __future__ import annotations

import logging
from dataclasses import dataclass

from src.iot_ingestion.application.ports import DeviceClaimer, ThresholdCatalog

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClaimResult:
    device_id: str


class DeviceAlreadyOwnedError(Exception):
    """Se lanza cuando el código no pudo canjearse (inválido, expirado o error)."""


class ClaimDevice:
    """Caso de uso: canjea un código de emparejamiento y guarda la clave del
    dispositivo en el catálogo local del Edge, para reenviar con ella después."""

    def __init__(self, claimer: DeviceClaimer, catalog: ThresholdCatalog) -> None:
        self._claimer = claimer
        self._catalog = catalog

    def execute(self, code: str) -> ClaimResult:
        result = self._claimer.claim(code)
        if result is None:
            raise DeviceAlreadyOwnedError("Código inválido, expirado o backend inaccesible")
        device_id, secret_key = result
        self._catalog.set_secret_for_device(device_id, secret_key)
        logger.info("Dispositivo %s vinculado; clave guardada localmente", device_id)
        return ClaimResult(device_id=device_id)
