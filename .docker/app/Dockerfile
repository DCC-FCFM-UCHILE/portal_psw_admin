FROM node:24.22.2-bookworm-slim AS node

FROM python:3.12.15-bookworm AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node /usr/local/bin/node /usr/local/bin/
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

COPY app/_requirements/ ./_requirements/
RUN pip install pip==26.2.2 && pip install -r _requirements/base.txt

COPY app/_node/package*.json ./_node/
RUN cd _node && npm ci

COPY app/ .

FROM base AS construccion

RUN cd _node && npm run tailwind-prod && rm -rf /app/_node

FROM python:3.12.15-slim-bookworm AS production

ARG UID
ARG GID

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1

COPY app/_requirements/ ./_requirements/
RUN pip install --no-cache-dir pip==26.2.2 && pip install --no-cache-dir -r _requirements/production.txt

RUN (getent group ${GID} || groupadd -g ${GID} instalar) \
    && useradd -m -u ${UID} -g ${GID} -s /sbin/nologin instalar \
    && mkdir -p /static /media \
    && chown instalar:${GID} /static /media

COPY --from=construccion --chown=0:0 /app/ ./

USER instalar

FROM base AS develop

RUN pip install -r _requirements/develop.txt
