FROM python:3.9-slim

LABEL maintainer="OpenCode Monitor Dashboard"
LABEL description="Real-time web dashboard for OpenCode sessions"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/

RUN mkdir -p /data/opencode

EXPOSE 38002

ENV OPENCODE_DATA_DIR=/data/opencode/storage/message \
    DASHBOARD_HOST=0.0.0.0 \
    DASHBOARD_PORT=38002 \
    AUTO_REFRESH_INTERVAL=5 \
    PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:38002/api/sessions')" || exit 1

CMD ["python", "app.py"]
