from __future__ import annotations

import logging
from dataclasses import dataclass

from src.iot_ingestion.application.ports import ReadingStore, ThresholdCatalog, UpstreamForwarder
from src.iot_ingestion.application.validation import ValidatedReading
from src.iot_ingestion.domain.freshness import FreshnessStatus, classify
from src.iot_ingestion.domain.sensor_reading import SensorReading

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProcessResult:
    reading: SensorReading
    forwarded: bool
    category: str | None
    status: FreshnessStatus


class ProcessReading:
    def __init__(
        self,
        readings: ReadingStore,
        forwarder: UpstreamForwarder,
        catalog: ThresholdCatalog,
    ) -> None:
        self._readings = readings
        self._forwarder = forwarder
        self._catalog = catalog

    def execute(self, validated: ValidatedReading) -> ProcessResult:
        reading = SensorReading(
            device_id=validated.device_id,
            reading_id=validated.reading_id,
            temperature=validated.temperature,
            humidity=validated.humidity,
            recorded_at=validated.recorded_at,
        )
        self._readings.add(reading)

        category, status = self._classify(reading)
        logger.info(
            "Lectura %s del device %s clasificada como %s (categoria=%s)",
            reading.reading_id, reading.device_id, status.value, category,
        )

        return ProcessResult(
            reading=reading,
            forwarded=self._try_forward(reading, category, status),
            category=category,
            status=status,
        )

    def _classify(self, reading: SensorReading) -> tuple[str | None, FreshnessStatus]:
        category = self._catalog.category_for_device(reading.device_id)
        if category is None:
            return None, FreshnessStatus.UNKNOWN
        threshold = self._catalog.threshold_for_category(category)
        if threshold is None:
            return category, FreshnessStatus.UNKNOWN
        return category, classify(reading.temperature, reading.humidity, threshold)

    def _try_forward(
        self, reading: SensorReading, category: str | None, status: FreshnessStatus
    ) -> bool:
        try:
            # La clave (X-Device-Key) sale del catálogo local, puesta al vincular
            # el dispositivo (claiming). Si aún no está, el reenvío dará 401.
            secret = self._catalog.secret_for_device(reading.device_id)
            return self._forwarder.forward(reading, category, status, secret)
        except Exception:
            logger.exception("Fallo al reenviar la lectura %s", reading.reading_id)
            return False
