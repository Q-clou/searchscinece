FROM python:3.11-slim

LABEL org.opencontainers.image.title="SearchScience"
LABEL org.opencontainers.image.description="Multi-source academic paper analysis system"
LABEL org.opencontainers.image.version="3.1.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/output

VOLUME ["/app/data", "/app/output"]

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "scripts/cli.py"]
CMD ["--help"]
