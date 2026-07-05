from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FreshnessStatus(str, Enum):
    """Estado de frescura tipo semaforo derivado de una lectura vs. su umbral."""

    GREEN = "GREEN"      # dentro del rango optimo
    YELLOW = "YELLOW"    # cerca del limite (margen de tolerancia)
    RED = "RED"          # fuera de rango
    UNKNOWN = "UNKNOWN"  # sin categoria o sin umbral para clasificar


@dataclass(frozen=True)
class CategoryThreshold:
    """Rango optimo de conservacion de una categoria de alimento."""

    category: str
    temp_min: float
    temp_max: float
    humidity_min: float
    humidity_max: float


# Margen relativo (15% del ancho del rango) que define la zona "amarilla":
# un valor justo fuera del rango pero dentro de este margen se considera YELLOW.
NEAR_MARGIN_RATIO = 0.15


def classify(temperature: float, humidity: float, threshold: CategoryThreshold) -> FreshnessStatus:
    """Clasifica una lectura contra un umbral. Manda el peor de los dos ejes
    (temperatura y humedad): si uno esta ROJO, el resultado es ROJO."""
    temp_state = _axis_state(temperature, threshold.temp_min, threshold.temp_max)
    humidity_state = _axis_state(humidity, threshold.humidity_min, threshold.humidity_max)
    return _worst(temp_state, humidity_state)


class _AxisState(Enum):
    OK = 0
    NEAR = 1
    OUT = 2


def _axis_state(value: float, low: float, high: float) -> _AxisState:
    if low <= value <= high:
        return _AxisState.OK
    margin = (high - low) * NEAR_MARGIN_RATIO
    if (low - margin) <= value < low or high < value <= (high + margin):
        return _AxisState.NEAR
    return _AxisState.OUT


def _worst(a: _AxisState, b: _AxisState) -> FreshnessStatus:
    worst = max(a.value, b.value)
    if worst == _AxisState.OK.value:
        return FreshnessStatus.GREEN
    if worst == _AxisState.NEAR.value:
        return FreshnessStatus.YELLOW
    return FreshnessStatus.RED
