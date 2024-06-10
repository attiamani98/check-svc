FROM python:3.11-slim

WORKDIR /app 

RUN cd ..

COPY ./dockerfiles/service_checker.py  /app

RUN pip install kubernetes aiohttp

ENTRYPOINT [ "python", "/app/service_checker.py" ]
