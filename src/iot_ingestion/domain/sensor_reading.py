from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SensorReading:
    device_id: str
    reading_id: str
    temperature: float
    humidity: float
    recorded_at: datetime
