FROM python:3.12.7-bookworm AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /static /logs /media /backup

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gettext \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY app/_requirements/ ./_requirements/
RUN pip install --upgrade pip && pip install -r _requirements/base.txt

COPY app/_node/package*.json ./_node/
RUN cd _node && npm install

COPY app/ .

FROM base AS production

ARG UID
ARG GID

RUN pip install -r _requirements/production.txt
RUN cd _node && npm run tailwind-prod

RUN groupadd -r instalar
RUN useradd -m instalar -u ${UID} -g ${GID} -s /sbin/nologin
RUN chown -R instalar:instalar /static /logs /media /backup /app
USER instalar

FROM base AS develop

ENV PYDEVD_DISABLE_FILE_VALIDATION 1

RUN pip install -r _requirements/develop.txt
