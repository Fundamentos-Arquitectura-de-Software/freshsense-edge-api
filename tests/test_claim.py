from __future__ import annotations

import pytest

from src.iot_ingestion.application.claim_device import ClaimDevice, DeviceAlreadyOwnedError
from src.iot_ingestion.infrastructure.memory_threshold_catalog import InMemoryThresholdCatalog


class _FakeClaimer:
    def __init__(self, result):
        self._result = result
        self.seen: str | None = None

    def claim(self, code):
        self.seen = code
        return self._result


def test_claim_stores_secret_in_catalog():
    catalog = InMemoryThresholdCatalog.with_defaults()
    claimer = _FakeClaimer(("esp32-freshsense-1", "secret123"))
    use_case = ClaimDevice(claimer, catalog)

    result = use_case.execute("ABC123")

    assert result.device_id == "esp32-freshsense-1"
    assert claimer.seen == "ABC123"
    # La clave queda guardada para reenviar con ella luego.
    assert catalog.secret_for_device("esp32-freshsense-1") == "secret123"


def test_claim_invalid_code_raises():
    catalog = InMemoryThresholdCatalog.with_defaults()
    use_case = ClaimDevice(_FakeClaimer(None), catalog)

    with pytest.raises(DeviceAlreadyOwnedError):
        use_case.execute("BADCODE")
