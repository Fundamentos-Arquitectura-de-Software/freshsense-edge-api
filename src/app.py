from __future__ import annotations

import logging

from flask import Flask, Response, jsonify

from src.config import Settings, load_settings
from src.iot_ingestion.application.ports import ThresholdCatalog
from src.iot_ingestion.infrastructure.memory_threshold_catalog import InMemoryThresholdCatalog
from src.iot_ingestion.infrastructure.reading_repository import InMemoryReadingRepository
from src.iot_ingestion.interfaces.routes import build_ingestion_blueprint
from src.shared.errors import AppError, error_payload

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    catalog: ThresholdCatalog | None = None,
) -> Flask:
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    readings = InMemoryReadingRepository()
    catalog = catalog or _build_catalog(settings)

    _register_health(app)
    _register_error_handlers(app)
    app.register_blueprint(build_ingestion_blueprint(settings, readings, catalog))
    return app


def _build_catalog(settings: Settings) -> ThresholdCatalog:
    """Intenta usar el MySQL local del Edge (inicializando esquema + seed).
    Si no esta disponible, degrada a un catalogo en memoria con los umbrales
    por defecto para que la clasificacion siga funcionando en desarrollo."""
    try:
        from src.iot_ingestion.infrastructure.mysql import init_schema_and_seed
        from src.iot_ingestion.infrastructure.mysql_threshold_catalog import MySqlThresholdCatalog

        init_schema_and_seed(settings)
        logger.info("Usando catalogo de umbrales MySQL en %s:%s/%s",
                    settings.db_host, settings.db_port, settings.db_name)
        return MySqlThresholdCatalog(settings)
    except Exception:
        logger.exception(
            "MySQL local no disponible; se usa catalogo en memoria (umbrales por defecto)"
        )
        return InMemoryThresholdCatalog.with_defaults()


def _register_health(app: Flask) -> None:
    @app.get("/health")
    def health() -> tuple[Response, int]:
        return jsonify({"status": "ok"}), 200


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(error: AppError) -> tuple[Response, int]:
        return jsonify(error_payload(error)), error.http_status


app = create_app()
