FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download free GeoIP database (DB-IP Lite Country, ~5MB, updated monthly)
# Try current month, fallback to previous month, skip on failure (app refreshes on startup)
RUN python -c "\
import urllib.request, gzip, datetime, os;\
today = datetime.date.today();\
months = [today.strftime('%Y-%m'), (today.replace(day=1) - datetime.timedelta(days=1)).strftime('%Y-%m')];\
ok = False;\
for m in months:\
    url = f'https://download.db-ip.com/free/dbip-country-lite-{m}.mmdb.gz';\
    print(f'Trying GeoIP: {url}');\
    try:\
        urllib.request.urlretrieve(url, '/tmp/geo.gz');\
        data = gzip.open('/tmp/geo.gz', 'rb').read();\
        open('/app/geoip.mmdb', 'wb').write(data);\
        os.remove('/tmp/geo.gz');\
        print(f'GeoIP DB: {len(data)//1024}KB');\
        ok = True; break;\
    except Exception as e: print(f'Failed: {e}');\
if not ok: print('GeoIP download failed, will retry at app startup')" || true

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
