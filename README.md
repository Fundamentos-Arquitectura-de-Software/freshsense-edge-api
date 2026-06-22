# FreshSense Edge API

Servicio edge IoT que recibe lecturas ambientales (temperatura y humedad) de dispositivos
ESP32, las procesa localmente y las reenvia al backend de FreshSense. Es la version **V1**:
solo recibe, valida y reenvia. La logica avanzada (umbrales por producto, clasificacion de
riesgo, prediccion de deterioro) se anadira en iteraciones posteriores.

## Arquitectura

Un contexto acotado (`iot_ingestion`) dividido en domain / application / infrastructure /
interfaces, siguiendo la estructura de referencia de `eduspace-edge-api-main`:

- **domain** — `SensorReading`, entidad pura sin dependencias de framework.
- **application** — `validation` (valida el cuerpo), `process_reading` (caso de uso),
  `ports` (interfaces que la aplicacion requiere de la infraestructura).
- **infrastructure** — `InMemoryReadingRepository` (almacen en memoria) y `BackendForwarder`
  (reenvio HTTP con `requests`).
- **interfaces** — blueprint Flask que expone `POST /edge/process`.

El dominio nunca importa infraestructura ni interfaces. Esto permite extender V2 (umbrales,
alertas, persistencia) anadiendo piezas sin reescribir el flujo.

## Requisitos

- Python 3.10+

## Instalacion

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Configuracion (variables de entorno)

| Variable                    | Proposito                                              | Por defecto                          |
|-----------------------------|--------------------------------------------------------|--------------------------------------|
| `FRESHSENSE_BACKEND_URL`    | URL del backend para reenviar las lecturas             | `http://localhost:8080/api/edge/readings`|
| `FRESHSENSE_FORWARD_TIMEOUT`| Timeout de la peticion al backend (segundos)           | `5`                                  |
| `FRESHSENSE_FORWARD_AUTH`   | Secreto del dispositivo enviado como `X-Device-Key` (vacio = sin cabecera) | _(vacio)_           |
| `FRESHSENSE_ENV`            | Contexto de ejecucion (`development` / `production`)   | `development`                        |

## Ejecucion

```bash
flask --app src.app run
```

## Endpoint

`POST /edge/process` recibe el JSON enviado por el dispositivo:

```bash
curl -X POST http://localhost:5000/edge/process \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"esp32-freshsense-1","temperature":24,"humidity":40,"time":"21/06/2026 10:48","id":"34c0c05ad9f7e4397335"}'
```

Respuesta `202`:

```json
{
  "status": "ok",
  "forwarded": true,
  "reading": {
    "deviceId": "esp32-freshsense-1",
    "id": "34c0c05ad9f7e4397335",
    "temperature": 24.0,
    "humidity": 40.0,
    "recordedAt": "2026-06-21T10:48:00"
  }
}
```

Tras procesar, el edge reenvia la lectura a `POST {FRESHSENSE_BACKEND_URL}` (por defecto
`/api/edge/readings` del backend Spring, que espera la cabecera `X-Device-Key` y los campos
`deviceId`, `temperature`, `humidity`, `time`, `id`). El reenvio es best-effort: un fallo del
backend no rompe la respuesta al dispositivo (`forwarded: false`).

Errores de validacion devuelven `400 {"code":"VALIDATION_ERROR","message":"..."}`.

## Pruebas

```bash
pytest
```
