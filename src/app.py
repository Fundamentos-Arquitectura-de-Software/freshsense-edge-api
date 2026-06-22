from __future__ import annotations

from flask import Flask, Response, jsonify

from src.config import Settings, load_settings
from src.iot_ingestion.infrastructure.reading_repository import InMemoryReadingRepository
from src.iot_ingestion.interfaces.routes import build_ingestion_blueprint
from src.shared.errors import AppError, error_payload


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    readings = InMemoryReadingRepository()

    _register_health(app)
    _register_error_handlers(app)
    app.register_blueprint(build_ingestion_blueprint(settings, readings))
    return app


def _register_health(app: Flask) -> None:
    @app.get("/health")
    def health() -> tuple[Response, int]:
        return jsonify({"status": "ok"}), 200


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(error: AppError) -> tuple[Response, int]:
        return jsonify(error_payload(error)), error.http_status


app = create_app()
