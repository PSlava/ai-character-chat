FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download free GeoIP database (DB-IP Lite Country, ~5MB, updated monthly)
# Try current month, fallback to previous month, skip on failure (app refreshes on startup)
RUN python -c "exec('''\nimport urllib.request, gzip, datetime, os\ntoday = datetime.date.today()\nmonths = [today.strftime(\"%Y-%m\"), (today.replace(day=1) - datetime.timedelta(days=1)).strftime(\"%Y-%m\")]\nfor m in months:\n    url = f\"https://download.db-ip.com/free/dbip-country-lite-{m}.mmdb.gz\"\n    print(f\"Trying GeoIP: {url}\")\n    try:\n        urllib.request.urlretrieve(url, \"/tmp/geo.gz\")\n        data = gzip.open(\"/tmp/geo.gz\", \"rb\").read()\n        open(\"/app/geoip.mmdb\", \"wb\").write(data)\n        os.remove(\"/tmp/geo.gz\")\n        print(f\"GeoIP DB: {len(data)//1024}KB\")\n        break\n    except Exception as e:\n        print(f\"Failed: {e}\")\nelse:\n    print(\"GeoIP download failed, will retry at app startup\")\n''')" || true

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
