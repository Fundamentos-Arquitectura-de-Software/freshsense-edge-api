from __future__ import annotations

from typing import Protocol

from src.iot_ingestion.domain.freshness import CategoryThreshold, FreshnessStatus
from src.iot_ingestion.domain.sensor_reading import SensorReading


class ReadingStore(Protocol):
    def add(self, reading: SensorReading) -> None:
        ...


class UpstreamForwarder(Protocol):
    def forward(
        self, reading: SensorReading, category: str | None, status: FreshnessStatus
    ) -> bool:
        ...


class ThresholdCatalog(Protocol):
    """Catalogo de umbrales por categoria y del mapeo device -> categoria.
    La aplicacion lo requiere para clasificar; la infraestructura lo resuelve
    (MySQL local del Edge, o en memoria para pruebas)."""

    def category_for_device(self, device_id: str) -> str | None:
        ...

    def threshold_for_category(self, category: str) -> CategoryThreshold | None:
        ...

    def list_thresholds(self) -> list[CategoryThreshold]:
        ...

    def list_device_categories(self) -> dict[str, str]:
        ...

    def set_device_category(self, device_id: str, category: str) -> None:
        ...

    def secret_for_device(self, device_id: str) -> str | None:
        ...

    def set_secret_for_device(self, device_id: str, secret_key: str) -> None:
        ...


class DeviceClaimer(Protocol):
    """Canjea un código de emparejamiento contra el backend y devuelve
    (deviceId, secretKey). None si el código es inválido o hubo error."""

    def claim(self, code: str) -> tuple[str, str] | None:
        ...
