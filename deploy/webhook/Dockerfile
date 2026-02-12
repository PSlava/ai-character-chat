FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io git curl && rm -rf /var/lib/apt/lists/*

# Install docker compose v2 CLI plugin (standalone)
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 9000
CMD ["python", "server.py"]
