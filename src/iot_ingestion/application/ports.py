from __future__ import annotations

from typing import Protocol

from src.iot_ingestion.domain.sensor_reading import SensorReading


class ReadingStore(Protocol):
    def add(self, reading: SensorReading) -> None:
        ...


class UpstreamForwarder(Protocol):
    def forward(self, reading: SensorReading) -> bool:
        ...
