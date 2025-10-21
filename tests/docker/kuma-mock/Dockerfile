FROM python:3.11-slim
WORKDIR /app
COPY collector.py /app/collector.py
ENV LISTEN_PORT=8080 KUMA_DATA_DIR=/app/data
EXPOSE 8080
CMD ["python", "/app/collector.py"]
