from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.shared.errors import ValidationError

TEMP_MIN, TEMP_MAX = -40.0, 85.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0
TIME_FORMAT = "%d/%m/%Y %H:%M"


@dataclass(frozen=True)
class ValidatedReading:
    device_id: str
    reading_id: str
    temperature: float
    humidity: float
    recorded_at: datetime


def validate_reading_request(body: Any) -> ValidatedReading:
    if not isinstance(body, dict):
        raise ValidationError("El cuerpo de la peticion debe ser un objeto JSON")
    return ValidatedReading(
        device_id=_require_str(body, "deviceId"),
        reading_id=_require_str(body, "id"),
        temperature=_require_number(body, "temperature", TEMP_MIN, TEMP_MAX),
        humidity=_require_number(body, "humidity", HUMIDITY_MIN, HUMIDITY_MAX),
        recorded_at=_require_timestamp(body, "time"),
    )


def _require_str(body: dict[str, Any], field: str) -> str:
    value = body.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} es obligatorio y debe ser un texto no vacio")
    return value


def _require_number(body: dict[str, Any], field: str, low: float, high: float) -> float:
    value = body.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} es obligatorio y debe ser un numero")
    if not low <= float(value) <= high:
        raise ValidationError(f"{field} debe estar entre {low} y {high}")
    return float(value)


def _require_timestamp(body: dict[str, Any], field: str) -> datetime:
    value = body.get(field)
    if not isinstance(value, str):
        raise ValidationError(f"{field} es obligatorio y debe ser un texto con formato {TIME_FORMAT}")
    try:
        return datetime.strptime(value, TIME_FORMAT)
    except ValueError as exc:
        raise ValidationError(f"{field} debe tener el formato {TIME_FORMAT}") from exc
