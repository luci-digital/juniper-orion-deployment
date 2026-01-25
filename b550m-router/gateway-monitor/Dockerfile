FROM python:3.11-slim

LABEL maintainer="Aethon <aethon@lucidigital.io>"
LABEL description="LuciVerse Gateway Monitor for B550M Router"
LABEL genesis_bond="ACTIVE @ 432 Hz"

# Install network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY gateway_monitor.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

CMD ["python3", "gateway_monitor.py"]
