# Portal administrativo de Proyecto de Software

Portal administrativo del ramo Proyecto de Software, DCC, Universidad de Chile.

Es un proyecto Django que usa django-unfold como tema del admin. Administra las
convocatorias, postulaciones, proyectos y cuentas que comparte con el portal público.

## Stack

- Django 5.2 LTS y PostgreSQL
- django-unfold (trae Tailwind, Alpine y HTMX ya compilados, no hay pipeline de Node)
- Docker Compose

## Levantarlo en local

Hace falta Docker con Compose v2 y el portal público levantado: en local el
administrativo usa la base y los archivos subidos del público, igual que en producción
ambos usan la base compartida.

```bash
cp .docker/app/.env.example .docker/app/.env
```

En ese archivo hay que generar un `DJANGO_SECRET_KEY` y copiar `DJANGO_DB_NAME`,
`DJANGO_DB_USER` y `DJANGO_DB_PASSWORD` desde el `.env` del público.
`DJANGO_DB_HOST` queda en `postgresql-portal-publico`.

```bash
cd .docker
make levantar
make migrar
make superusuario
```

Queda en http://localhost:8003/admin/.

Si el público vive en otra carpeta o con otro nombre de proyecto, `MEDIA_PUBLICO` y
`RED_PUBLICO` en el mismo `.env` apuntan a sus archivos y a su red.

Otros atajos: `make logs`, `make consola`, `make bajar`.

## Base de datos en producción

En producción el portal apunta a la base compartida con los otros portales. Ahí las
tablas ya existen y sus migraciones viven en otro repositorio, así que `make migrar` no
se corre contra esa base.

## Organización

```
app/core/           configuración y URLs raíz
app/core/settings/  base.py más un archivo por entorno
app/cuentas/        usuarios, grupos y restablecer la contraseña
app/postulaciones/  convocatorias, postulaciones, proyectos y correos a postulantes
app/convenios/      formatos de postulación
app/_templates/     plantillas que sobrescriben las de unfold
.docker/            Dockerfile, compose y Makefile
```

## Pruebas

```bash
cd app
make test
```

Necesitan una base PostgreSQL vacía; las tablas compartidas las crea la propia prueba.
