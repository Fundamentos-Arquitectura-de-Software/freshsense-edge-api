from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from src.config import Settings
from src.iot_ingestion.application.process_reading import ProcessReading
from src.iot_ingestion.application.validation import validate_reading_request
from src.iot_ingestion.infrastructure.reading_repository import InMemoryReadingRepository
from src.iot_ingestion.infrastructure.upstream_forwarder import BackendForwarder

ROUTE = "/edge/process"


def build_ingestion_blueprint(
    settings: Settings, readings: InMemoryReadingRepository
) -> Blueprint:
    blueprint = Blueprint("ingestion", __name__)
    use_case = ProcessReading(
        readings,
        BackendForwarder(settings.backend_url, settings.forward_timeout, settings.forward_auth),
    )

    @blueprint.post(ROUTE)
    def process_reading() -> tuple[Response, int]:
        validated = validate_reading_request(request.get_json(silent=True))
        result = use_case.execute(validated)
        body = {
            "status": "ok",
            "forwarded": result.forwarded,
            "reading": {
                "deviceId": result.reading.device_id,
                "id": result.reading.reading_id,
                "temperature": result.reading.temperature,
                "humidity": result.reading.humidity,
                "recordedAt": result.reading.recorded_at.isoformat(),
            },
        }
        return jsonify(body), 202

    return blueprint
