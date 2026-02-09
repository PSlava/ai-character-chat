FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY deploy/webhook/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY deploy/webhook/server.py .

EXPOSE 9000
CMD ["python", "server.py"]
