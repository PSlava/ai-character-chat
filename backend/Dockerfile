FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=${GIT_COMMIT}

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# WEB_WORKERS can be overridden: docker run -e WEB_WORKERS=4
ENV WEB_WORKERS=2

CMD gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${WEB_WORKERS} \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --keep-alive 65
