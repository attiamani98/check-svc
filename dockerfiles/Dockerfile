FROM python:3.11-slim

WORKDIR /app

COPY test.py /app

RUN pip install kubernetes aiohttp prometheus_client

EXPOSE 9000

ENTRYPOINT ["python", "/app/service_checker.py"]
