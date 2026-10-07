FROM python:3.12.7-bookworm AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /static /logs /media /backup

COPY app/_requirements/ ./_requirements/
RUN pip install --upgrade pip && pip install -r _requirements/base.txt

COPY app/ .

FROM base AS production

ARG UID
ARG GID

RUN pip install -r _requirements/production.txt

RUN groupadd -r instalar
RUN useradd -m instalar -u ${UID} -g ${GID} -s /sbin/nologin
RUN chown -R instalar:instalar /static /logs /media /backup /app
USER instalar

FROM base AS develop

ENV PYDEVD_DISABLE_FILE_VALIDATION=1

RUN pip install -r _requirements/develop.txt
