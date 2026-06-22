from __future__ import annotations

import logging
from dataclasses import dataclass

from src.iot_ingestion.application.ports import ReadingStore, UpstreamForwarder
from src.iot_ingestion.application.validation import ValidatedReading
from src.iot_ingestion.domain.sensor_reading import SensorReading

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessResult:
    reading: SensorReading
    forwarded: bool


class ProcessReading:
    def __init__(self, readings: ReadingStore, forwarder: UpstreamForwarder) -> None:
        self._readings = readings
        self._forwarder = forwarder

    def execute(self, validated: ValidatedReading) -> ProcessResult:
        reading = SensorReading(
            device_id=validated.device_id,
            reading_id=validated.reading_id,
            temperature=validated.temperature,
            humidity=validated.humidity,
            recorded_at=validated.recorded_at,
        )
        self._readings.add(reading)
        return ProcessResult(reading=reading, forwarded=self._try_forward(reading))

    def _try_forward(self, reading: SensorReading) -> bool:
        try:
            return self._forwarder.forward(reading)
        except Exception:
            logger.exception("Fallo al reenviar la lectura %s", reading.reading_id)
            return False
