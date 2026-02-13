FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests docker

COPY responder.py /app/responder.py
COPY response_actions.yaml /app/response_actions.yaml

EXPOSE 5080

CMD ["python", "responder.py"]
