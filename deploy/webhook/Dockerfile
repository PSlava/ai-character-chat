FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

# Install docker CLI (static binary)
RUN curl -fsSL "https://download.docker.com/linux/static/stable/$(uname -m)/docker-27.5.1.tgz" \
    | tar xz --strip-components=1 -C /usr/local/bin docker/docker

# Install docker compose v2 + buildx CLI plugins
COPY --from=docker/buildx-bin /buildx /usr/local/lib/docker/cli-plugins/docker-buildx
RUN mkdir -p /usr/local/lib/docker/cli-plugins && \
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

RUN groupadd -g 999 docker && useradd -m -u 1000 -G docker webhook

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
RUN mkdir -p /var/log && chown webhook:webhook /var/log

USER webhook

EXPOSE 9000
CMD ["python", "server.py"]
