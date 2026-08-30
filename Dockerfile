FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libexpat1 \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        proj-bin \
        proj-data \
        gdal-bin \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["sh", "-c", "echo RAILWAY_PORT=$PORT && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
