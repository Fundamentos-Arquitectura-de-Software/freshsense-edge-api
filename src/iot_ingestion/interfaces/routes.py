from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from src.config import Settings
from src.iot_ingestion.application.claim_device import ClaimDevice, DeviceAlreadyOwnedError
from src.iot_ingestion.application.ports import ReadingStore, ThresholdCatalog
from src.iot_ingestion.application.process_reading import ProcessReading
from src.iot_ingestion.application.validation import validate_reading_request
from src.iot_ingestion.infrastructure.backend_claim import BackendClaimClient
from src.iot_ingestion.infrastructure.upstream_forwarder import BackendForwarder
from src.shared.errors import ValidationError

PROCESS_ROUTE = "/edge/process"


def build_ingestion_blueprint(
    settings: Settings,
    readings: ReadingStore,
    catalog: ThresholdCatalog,
) -> Blueprint:
    blueprint = Blueprint("ingestion", __name__)
    use_case = ProcessReading(
        readings,
        BackendForwarder(settings.backend_url, settings.forward_timeout, settings.forward_auth),
        catalog,
    )
    claim_use_case = ClaimDevice(
        BackendClaimClient(settings.claim_url, settings.forward_timeout),
        catalog,
    )

    @blueprint.post(PROCESS_ROUTE)
    def process_reading() -> tuple[Response, int]:
        validated = validate_reading_request(request.get_json(silent=True))
        result = use_case.execute(validated)
        body = {
            "status": "ok",
            "forwarded": result.forwarded,
            "category": result.category,
            "freshness": result.status.value,
            "reading": {
                "deviceId": result.reading.device_id,
                "id": result.reading.reading_id,
                "temperature": result.reading.temperature,
                "humidity": result.reading.humidity,
                "recordedAt": result.reading.recorded_at.isoformat(),
            },
        }
        return jsonify(body), 202

    @blueprint.get("/edge/thresholds")
    def list_thresholds() -> tuple[Response, int]:
        thresholds = [
            {
                "category": t.category,
                "tempMin": t.temp_min,
                "tempMax": t.temp_max,
                "humidityMin": t.humidity_min,
                "humidityMax": t.humidity_max,
            }
            for t in catalog.list_thresholds()
        ]
        return jsonify(thresholds), 200

    @blueprint.get("/edge/devices")
    def list_devices() -> tuple[Response, int]:
        mappings = [
            {"deviceId": device_id, "category": category}
            for device_id, category in catalog.list_device_categories().items()
        ]
        return jsonify(mappings), 200

    @blueprint.post("/edge/devices")
    def set_device() -> tuple[Response, int]:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValidationError("El cuerpo debe ser un objeto JSON")
        device_id = body.get("deviceId")
        category = body.get("category")
        if not isinstance(device_id, str) or not device_id.strip():
            raise ValidationError("deviceId es obligatorio y debe ser un texto no vacio")
        if not isinstance(category, str) or not category.strip():
            raise ValidationError("category es obligatoria y debe ser un texto no vacio")
        if catalog.threshold_for_category(category) is None:
            raise ValidationError(f"No existe umbral para la categoria '{category}'")
        catalog.set_device_category(device_id, category)
        return jsonify({"deviceId": device_id, "category": category}), 201

    @blueprint.post("/edge/claim")
    def claim() -> tuple[Response, int]:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ValidationError("El cuerpo debe ser un objeto JSON")
        code = body.get("code")
        if not isinstance(code, str) or not code.strip():
            raise ValidationError("code es obligatorio y debe ser un texto no vacio")
        try:
            result = claim_use_case.execute(code.strip().upper())
        except DeviceAlreadyOwnedError as exc:
            raise ValidationError(str(exc)) from exc
        return jsonify({"status": "linked", "deviceId": result.device_id}), 200

    @blueprint.get("/edge/setup")
    def setup_page() -> Response:
        # Página mínima para que el instalador pegue el código de emparejamiento
        # de la app y vincule el Edge, sin usar consola.
        return Response(_SETUP_HTML, mimetype="text/html")

    return blueprint


_SETUP_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FreshSense Edge — Vincular dispositivo</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:520px;margin:3rem auto;padding:0 1rem;color:#0f172a}
 h1{font-size:1.3rem} input{font-size:1.1rem;padding:.6rem;width:100%;box-sizing:border-box;text-transform:uppercase}
 button{margin-top:.75rem;padding:.6rem 1.2rem;font-size:1rem;background:#1f9c59;color:#fff;border:0;border-radius:6px;cursor:pointer}
 .msg{margin-top:1rem;padding:.75rem;border-radius:6px} .ok{background:#f3fbf6;border:1px solid #1f9c59}
 .err{background:#fdecea;border:1px solid #c0392b;color:#c0392b}
 code{background:#0f172a;color:#e2e8f0;padding:.15rem .4rem;border-radius:4px}
</style></head><body>
 <h1>Vincular este Edge a tu dispositivo</h1>
 <p>Registra el dispositivo en la app FreshSense (menú <strong>Dispositivos</strong>) y pega aquí el
    <strong>código de emparejamiento</strong> que te muestra (válido 10 minutos).</p>
 <input id="code" placeholder="Código (ej. 7K4Q2P)" autofocus>
 <button onclick="claim()">Vincular</button>
 <div id="out"></div>
<script>
 async function claim(){
   const code=document.getElementById('code').value.trim();
   const out=document.getElementById('out');
   out.innerHTML='';
   try{
     const r=await fetch('/edge/claim',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code})});
     const b=await r.json();
     if(r.ok){ out.innerHTML='<div class="msg ok">Vinculado el dispositivo <code>'+b.deviceId+'</code>. Ya puede enviar lecturas.</div>'; }
     else { out.innerHTML='<div class="msg err">'+(b.message||'No se pudo vincular')+'</div>'; }
   }catch(e){ out.innerHTML='<div class="msg err">Error de red</div>'; }
 }
</script>
</body></html>"""
