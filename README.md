# FreshSense Edge API

Servicio edge IoT que recibe lecturas ambientales (temperatura y humedad) de dispositivos
ESP32, las procesa localmente y las reenvia al backend de FreshSense. Ademas **clasifica la
frescura** (semaforo VERDE / AMARILLO / ROJO) comparando cada lectura contra el umbral de la
categoria del dispositivo, usando un **MySQL local** propio del Edge.

## Arquitectura

Un contexto acotado (`iot_ingestion`) dividido en domain / application / infrastructure /
interfaces, siguiendo la estructura de referencia de `eduspace-edge-api-main`:

- **domain** — `SensorReading` (entidad pura) y `freshness` (`FreshnessStatus`,
  `CategoryThreshold` y la funcion pura `classify`), sin dependencias de framework.
- **application** — `validation` (valida el cuerpo), `process_reading` (caso de uso: guarda,
  clasifica y reenvia), `ports` (interfaces: `ReadingStore`, `UpstreamForwarder`,
  `ThresholdCatalog`).
- **infrastructure** — `InMemoryReadingRepository`, `BackendForwarder` (reenvio HTTP),
  `mysql` (conexion + esquema + seed), `MySqlThresholdCatalog` (umbrales/mapeo en MySQL),
  `InMemoryThresholdCatalog` (fallback/pruebas) y `seed_data` (umbrales por defecto).
- **interfaces** — blueprint Flask: `POST /edge/process`, `GET /edge/thresholds`,
  `GET|POST /edge/devices`.

El dominio nunca importa infraestructura ni interfaces.

### Clasificacion de frescura (semaforo)

Cada dispositivo se mapea a **una** categoria (`device_categories`). Al llegar una lectura, el
Edge busca la categoria del `deviceId`, obtiene el umbral de esa categoria
(`category_thresholds`) y clasifica:

- **GREEN** — temperatura y humedad dentro del rango optimo.
- **YELLOW** — algun eje justo fuera del rango, dentro de un margen del 15%.
- **RED** — algun eje claramente fuera de rango (manda el peor de los dos ejes).
- **UNKNOWN** — el dispositivo no tiene categoria asignada o no hay umbral para ella.

Umbrales sembrados por defecto (temp °C / humedad %): Frutas 2–8/85–95, Verduras 0–6/90–98,
Lacteos 1–5/70–85, Carnes −1–4/75–85, Proteinas 0–4/75–85, Panaderia 16–24/50–65,
Snacks 16–24/40–55. Dispositivo demo sembrado: `esp32-freshsense-1 -> Lácteos`.

## Requisitos

- Python 3.10+
- MySQL 8.0 accesible localmente (el Edge crea la base y las tablas en el primer arranque).
  Si no hay MySQL, el Edge degrada a un catalogo en memoria con los umbrales por defecto y
  sigue funcionando (clasifica igual, pero los cambios de mapeo no persisten).

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
| `FRESHSENSE_DB_HOST`        | Host del MySQL local del Edge                          | `localhost`                          |
| `FRESHSENSE_DB_PORT`        | Puerto del MySQL local                                 | `3306`                               |
| `FRESHSENSE_DB_USER`        | Usuario del MySQL local                                | `root`                               |
| `FRESHSENSE_DB_PASSWORD`    | Contraseña del MySQL local                             | `root`                               |
| `FRESHSENSE_DB_NAME`        | Base de datos del Edge (se crea si no existe)          | `freshsense_edge`                    |

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

Respuesta `202` (incluye la clasificacion de frescura):

```json
{
  "status": "ok",
  "forwarded": true,
  "category": "Lácteos",
  "freshness": "RED",
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

### Gestion de umbrales y dispositivos

```bash
# Listar los umbrales por categoria
curl http://localhost:5000/edge/thresholds

# Listar el mapeo dispositivo -> categoria
curl http://localhost:5000/edge/devices

# Asignar un dispositivo a una categoria (debe existir umbral para esa categoria)
curl -X POST http://localhost:5000/edge/devices \
  -H "Content-Type: application/json" \
  -d '{"deviceId":"esp32-cocina","category":"Frutas"}'
```

## Pruebas

```bash
pytest
```
