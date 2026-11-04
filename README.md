# Portal administrativo de Proyecto de Software

Portal administrativo del ramo Proyecto de Software, DCC, Universidad de Chile.

Es un proyecto Django que usa django-unfold como tema del admin. Administra las
convocatorias, postulaciones, proyectos y cuentas que comparte con el portal público.

## Stack

- Django 5.2 LTS y PostgreSQL
- django-unfold, que trae su propio Tailwind compilado, Alpine y HTMX
- Tailwind CSS 4 para la hoja propia (`administrativo.css`), con los mismos colores y nombres
  que el portal público
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
make up
make migrate
make superuser
```

Queda en http://localhost:8003/admin/. El contenedor `portal-admin-tailwind` recompila
`administrativo.css` cada vez que cambia una plantilla, un `.py` o la hoja fuente.

Si el público vive en otra carpeta o con otro nombre de proyecto, `MEDIA_PUBLICO` y
`RED_PUBLICO` en el mismo `.env` apuntan a sus archivos y a su red.

Otros atajos: `make logs`, `make shell`, `make down`.

## Despliegue

```bash
cp .docker/app/.env.produccion.example .docker/app/.env
```

Se completa lo que quedó vacío (base y correo) y se revisan la dirección y los demás
valores. Si falta una variable obligatoria, el contenedor no arranca y
`docker logs portal-admin-psw` dice cuál.

```bash
cd .docker
make deploy
```

Al final del mismo archivo van el hostname, la red, los directorios del servidor y el
usuario del contenedor; si quedan comentados, valen los de `dc-produccion.yml`. El
directorio de archivos tiene que ser el mismo del portal público.

En producción el portal apunta a la base compartida con los otros portales. Ahí las
tablas ya existen y sus migraciones viven en otro repositorio, así que `make migrate` no
se corre contra esa base.

## Organización

```
app/core/           configuración y URLs raíz
app/core/settings/  base.py más un archivo por entorno
app/cuentas/        usuarios, grupos y restablecer la contraseña
app/interfaz/       etiquetas de plantilla, siluetas, recorte de íconos y política de contenido
app/postulaciones/  convocatorias, postulaciones, proyectos y correos a postulantes
app/convenios/      formatos de postulación
app/_templates/     plantillas que sobrescriben las de unfold y páginas de error
app/_node/          fuente de administrativo.css y su compilación
app/_staticfiles/   logo, favicon, fuente de íconos y js/administrativo/
app/_locale/        textos de unfold en español (unfold no trae traducción)
.docker/            Dockerfile, compose y Makefile
```

## Textos en español

unfold no trae catálogo en español. Los textos están en `app/_locale/es/LC_MESSAGES/django.po`.
Después de editarlo:

```bash
docker exec portal-admin-psw python manage.py compilemessages -l es
```

## Pruebas

```bash
cd app
make test
```

Necesitan una base PostgreSQL vacía; las tablas compartidas las crea la propia prueba.
