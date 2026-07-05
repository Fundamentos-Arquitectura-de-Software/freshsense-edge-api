from __future__ import annotations

import logging

import pymysql
from pymysql.cursors import DictCursor

from src.config import Settings
from src.iot_ingestion.infrastructure.seed_data import (
    DEFAULT_DEVICE_CATEGORIES,
    DEFAULT_THRESHOLDS,
)

logger = logging.getLogger(__name__)


def connect(settings: Settings) -> pymysql.connections.Connection:
    """Abre una conexion al MySQL local del Edge (autocommit, filas como dict)."""
    return pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        cursorclass=DictCursor,
        autocommit=True,
        charset="utf8mb4",
        connect_timeout=5,
    )


def init_schema_and_seed(settings: Settings) -> None:
    """Crea la base y las tablas si no existen y siembra los umbrales por defecto.
    Idempotente: se puede llamar en cada arranque sin efectos secundarios."""
    # Primero conectar sin base para poder crearla.
    root = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        autocommit=True,
        charset="utf8mb4",
        connect_timeout=5,
    )
    try:
        with root.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        root.close()

    conn = connect(settings)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS category_thresholds (
                    category      VARCHAR(50)  NOT NULL PRIMARY KEY,
                    temp_min      DOUBLE       NOT NULL,
                    temp_max      DOUBLE       NOT NULL,
                    humidity_min  DOUBLE       NOT NULL,
                    humidity_max  DOUBLE       NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS device_categories (
                    device_id   VARCHAR(100) NOT NULL PRIMARY KEY,
                    category    VARCHAR(50)  NULL,
                    secret_key  VARCHAR(64)  NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            # Migración defensiva: si la tabla ya existía sin estas columnas
            # (volumen previo), añadirlas. MySQL no soporta IF NOT EXISTS aquí,
            # así que ignoramos el error de columna duplicada.
            _add_column_if_missing(cur, "device_categories", "secret_key VARCHAR(64) NULL")
            try:
                cur.execute("ALTER TABLE device_categories MODIFY category VARCHAR(50) NULL")
            except Exception:  # noqa: BLE001 - ya era nullable
                pass
            # Seed de umbrales (no pisa cambios manuales existentes).
            for t in DEFAULT_THRESHOLDS:
                cur.execute(
                    "INSERT IGNORE INTO category_thresholds "
                    "(category, temp_min, temp_max, humidity_min, humidity_max) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (t.category, t.temp_min, t.temp_max, t.humidity_min, t.humidity_max),
                )
            for device_id, category in DEFAULT_DEVICE_CATEGORIES.items():
                cur.execute(
                    "INSERT IGNORE INTO device_categories (device_id, category) VALUES (%s, %s)",
                    (device_id, category),
                )
        logger.info("Esquema del Edge inicializado y umbrales sembrados en '%s'", settings.db_name)
    finally:
        conn.close()


def _add_column_if_missing(cur, table: str, column_def: str) -> None:
    """ALTER TABLE ADD COLUMN idempotente (ignora 'columna duplicada')."""
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
    except Exception:  # noqa: BLE001 - la columna ya existe
        pass
