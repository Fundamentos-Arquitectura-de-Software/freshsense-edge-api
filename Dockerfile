# FreshSense Edge API (Python/Flask). Recibe lecturas del ESP32, clasifica la
# frescura contra el umbral de la categoria del dispositivo (MySQL local) y las
# reenvia al backend.
FROM python:3.12-slim

WORKDIR /app

# Dependencias primero (mejor cache de capas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

EXPOSE 5000

# Servidor de desarrollo de Flask: suficiente para pruebas locales / demo.
CMD ["python", "-m", "flask", "--app", "src.app", "run", "--host", "0.0.0.0", "--port", "5000"]
