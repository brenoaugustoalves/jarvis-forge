FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/config ./config
COPY dashboard ./dashboard

EXPOSE 8000
ENV JARVIS_FORGE_RUNTIME=1
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
