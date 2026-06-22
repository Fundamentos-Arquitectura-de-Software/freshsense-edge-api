from __future__ import annotations

import pytest

from src.app import create_app
from src.config import Settings


@pytest.fixture()
def client():
    settings = Settings(backend_url="", forward_timeout=1.0, forward_auth="", env="development")
    app = create_app(settings)
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
