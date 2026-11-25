# Image for the Northvale University web application.
# Used both inside the Ubuntu VM (docker compose) and on Render (runtime: docker).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /srv/app

# Install dependencies first so this layer is cached between code changes
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Run as an unprivileged user instead of root
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'))" || exit 1

# gunicorn: production WSGI server. --preload runs init_db() once before forking workers.
# PORT is 8000 in the VM and is injected by Render on the PaaS.
CMD gunicorn --preload --workers 2 --bind 0.0.0.0:${PORT} --access-logfile - app:app
