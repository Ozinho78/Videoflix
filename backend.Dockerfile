FROM python:3.12-alpine

LABEL maintainer="mihai@developerakademie.com"
LABEL version="1.0"
LABEL description="Python 3.14.0a7 Alpine 3.21"

WORKDIR /app

COPY . .

RUN apk update && \
    apk add --no-cache --upgrade bash && \
    apk add --no-cache postgresql-client ffmpeg && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && \
    chmod +x backend.entrypoint.sh

RUN pip install --upgrade pip && pip install -r requirements.txt

RUN mkdir -p /app/logs && chmod -R 777 /app/logs

COPY ./backend.entrypoint.sh ./backend.entrypoint.sh
RUN dos2unix ./backend.entrypoint.sh || true
RUN chmod +x ./backend.entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./backend.entrypoint.sh"]
