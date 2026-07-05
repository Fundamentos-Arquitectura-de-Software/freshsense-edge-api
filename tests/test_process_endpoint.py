from __future__ import annotations

import pytest

from src.app import create_app
from src.config import Settings
from src.iot_ingestion.infrastructure.memory_threshold_catalog import InMemoryThresholdCatalog


def _settings() -> Settings:
    # db_host vacio: no se toca MySQL en los tests (se inyecta un catalogo en memoria).
    return Settings(
        backend_url="",
        forward_timeout=1.0,
        forward_auth="",
        env="development",
        db_host="",
        db_port=3306,
        db_user="",
        db_password="",
        db_name="",
    )


@pytest.fixture()
def client():
    catalog = InMemoryThresholdCatalog.with_defaults()  # incluye esp32-freshsense-1 -> Lácteos
    app = create_app(_settings(), catalog=catalog)
    app.testing = True
    return app.test_client()


def _valid_body() -> dict:
    return {
        "deviceId": "esp32-freshsense-1",
        "temperature": 24,
        "humidity": 40,
        "time": "21/06/2026 10:48",
        "id": "34c0c05ad9f7e4397335",
    }


def test_accepts_valid_reading(client):
    response = client.post("/edge/process", json=_valid_body())

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["forwarded"] is False
    assert payload["reading"]["deviceId"] == "esp32-freshsense-1"
    assert payload["reading"]["recordedAt"].startswith("2026-06-21T10:48:00")


def test_classifies_reading_by_device_category(client):
    # 24 °C / 40 % para Lácteos (1–5 / 70–85) => ROJO.
    response = client.post("/edge/process", json=_valid_body())
    payload = response.get_json()
    assert payload["category"] == "Lácteos"
    assert payload["freshness"] == "RED"


def test_green_reading_within_range(client):
    body = _valid_body()
    body["temperature"] = 4
    body["humidity"] = 80
    response = client.post("/edge/process", json=body)
    assert response.get_json()["freshness"] == "GREEN"


def test_unknown_when_device_has_no_category(client):
    body = _valid_body()
    body["deviceId"] = "device-sin-mapeo"
    response = client.post("/edge/process", json=body)
    payload = response.get_json()
    assert payload["category"] is None
    assert payload["freshness"] == "UNKNOWN"


def test_lists_thresholds(client):
    response = client.get("/edge/thresholds")
    assert response.status_code == 200
    categories = [t["category"] for t in response.get_json()]
    assert "Lácteos" in categories
    assert len(categories) == 7


def test_registers_device_category(client):
    response = client.post("/edge/devices", json={"deviceId": "esp32-cocina", "category": "Frutas"})
    assert response.status_code == 201

    # Ahora una lectura de ese device se clasifica con el umbral de Frutas (2–8 / 85–95).
    reading = _valid_body()
    reading["deviceId"] = "esp32-cocina"
    reading["temperature"] = 5
    reading["humidity"] = 90
    classified = client.post("/edge/process", json=reading).get_json()
    assert classified["category"] == "Frutas"
    assert classified["freshness"] == "GREEN"


def test_rejects_device_with_unknown_category(client):
    response = client.post("/edge/devices", json={"deviceId": "x", "category": "NoExiste"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "VALIDATION_ERROR"


def test_rejects_missing_field(client):
    body = _valid_body()
    del body["temperature"]

    response = client.post("/edge/process", json=body)

    assert response.status_code == 400
    assert response.get_json()["code"] == "VALIDATION_ERROR"


def test_rejects_out_of_range_humidity(client):
    body = _valid_body()
    body["humidity"] = 150

    response = client.post("/edge/process", json=body)

    assert response.status_code == 400


def test_rejects_bad_time_format(client):
    body = _valid_body()
    body["time"] = "2026-06-21 10:48"

    response = client.post("/edge/process", json=body)

    assert response.status_code == 400


def test_setup_page_is_served(client):
    response = client.get("/edge/setup")
    assert response.status_code == 200
    assert b"Vincular" in response.data


def test_claim_fails_gracefully_without_backend(client):
    # En los tests backend_url="" -> claim_url="" -> el canje devuelve None -> 400.
    response = client.post("/edge/claim", json={"code": "ABC123"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "VALIDATION_ERROR"
