from __future__ import annotations

from src.iot_ingestion.domain.freshness import CategoryThreshold


class InMemoryThresholdCatalog:
    """Catalogo de umbrales en memoria. Sirve para pruebas y como fallback
    cuando el MySQL local no esta disponible."""

    def __init__(
        self,
        thresholds: list[CategoryThreshold] | None = None,
        device_categories: dict[str, str] | None = None,
    ) -> None:
        self._thresholds: dict[str, CategoryThreshold] = {
            t.category: t for t in (thresholds or [])
        }
        self._device_categories: dict[str, str] = dict(device_categories or {})
        self._device_secrets: dict[str, str] = {}

    @classmethod
    def with_defaults(cls) -> "InMemoryThresholdCatalog":
        # seed_data no depende de ningun driver de BD (no arrastra pymysql).
        from src.iot_ingestion.infrastructure.seed_data import (
            DEFAULT_DEVICE_CATEGORIES,
            DEFAULT_THRESHOLDS,
        )

        return cls(list(DEFAULT_THRESHOLDS), dict(DEFAULT_DEVICE_CATEGORIES))

    def category_for_device(self, device_id: str) -> str | None:
        return self._device_categories.get(device_id)

    def threshold_for_category(self, category: str) -> CategoryThreshold | None:
        return self._thresholds.get(category)

    def list_thresholds(self) -> list[CategoryThreshold]:
        return sorted(self._thresholds.values(), key=lambda t: t.category)

    def list_device_categories(self) -> dict[str, str]:
        return dict(self._device_categories)

    def set_device_category(self, device_id: str, category: str) -> None:
        self._device_categories[device_id] = category

    def secret_for_device(self, device_id: str) -> str | None:
        return self._device_secrets.get(device_id)

    def set_secret_for_device(self, device_id: str, secret_key: str) -> None:
        self._device_secrets[device_id] = secret_key
