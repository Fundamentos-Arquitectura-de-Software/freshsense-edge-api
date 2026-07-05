from __future__ import annotations

from src.iot_ingestion.domain.freshness import CategoryThreshold, FreshnessStatus, classify

# Lácteos: 1–5 °C / 70–85 %
LACTEOS = CategoryThreshold("Lácteos", 1, 5, 70, 85)


def test_green_when_both_axes_in_range():
    assert classify(4, 80, LACTEOS) is FreshnessStatus.GREEN


def test_yellow_when_axis_is_near_the_limit():
    # 5.5 °C esta fuera del rango pero dentro del margen del 15% ((5-1)*0.15 = 0.6).
    assert classify(5.5, 80, LACTEOS) is FreshnessStatus.YELLOW


def test_red_when_an_axis_is_far_out_of_range():
    # 24 °C esta muy por encima del maximo (5 °C) -> ROJO manda sobre la humedad ok.
    assert classify(24, 80, LACTEOS) is FreshnessStatus.RED


def test_worst_axis_wins():
    # Temperatura ok (4) pero humedad muy baja (40) -> ROJO.
    assert classify(4, 40, LACTEOS) is FreshnessStatus.RED
