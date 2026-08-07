FROM python:3.12-slim

# GeoDjango needs GDAL, GEOS and PROJ as system libraries. Installing these is the
# main reason the backend runs in a container rather than on the host.
RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

EXPOSE 8000
