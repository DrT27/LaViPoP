
FROM python:3.12-slim

LABEL org.opencontainers.image.title="LaViPoP"
LABEL org.opencontainers.image.description="TopLab's Language-aware Video Post-Processor"
LABEL org.opencontainers.image.vendor="TopLab - Toplak Laboratory e.U."

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies for video processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libglib2.0-0 \
        libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy LaViPoP application
COPY lavipop/ ./lavipop/

# Prepare writable directories
RUN mkdir -p \
        /app/lavipop/vidpop_cache \
        /app/lavipop/vidpop_uploads && \
    useradd --create-home --uid 10001 vidpop && \
    chown -R vidpop:vidpop /app

WORKDIR /app/lavipop

USER vidpop

EXPOSE 8050

CMD ["python", "Top_LaViPoP.py"]
