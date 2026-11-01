import re
from pathlib import Path

import unfold
from django.conf import settings

UNFOLD = Path(unfold.__file__).parent
FUENTE = UNFOLD / "static/unfold/fonts/material-symbols/Material-Symbols-Outlined.woff2"
CARPETA = Path(settings.BASE_DIR) / "_staticfiles/fuentes"
LISTA = CARPETA / "iconos.txt"
RECORTE = CARPETA / "iconos.woff2"

EN_SPAN = re.compile(r"material-symbols-outlined[^>]*>(.{0,300}?)</span>", re.S)
ETIQUETA = re.compile(r"<[^>]*material-symbols-outlined[^>]*>", re.S)
ARGUMENTO = re.compile(r"""icono?["']?\s*[=:]\s*["']([a-z0-9_]+)["']""")
PALABRA = re.compile(r"[a-z0-9_]+")
CITADA = re.compile(r"'([a-z0-9_]+)'")
CONTENIDO = re.compile(r"""content(?::\s*|-\[)["']([a-z0-9_\\]+)["']""")
OMITIR = {"node_modules", "_media", "__pycache__", "migrations"}
COMPILADOS = ("_staticfiles/unfold", "_staticfiles/vendor", "_staticfiles/fuentes")
PROPIOS = {".html", ".py", ".js", ".css"}


def candidatos(texto):
    encontrados = set(ARGUMENTO.findall(texto)) | {nombre.replace("\\", "") for nombre in CONTENIDO.findall(texto)}
    for contenido in EN_SPAN.findall(texto):
        encontrados |= set(PALABRA.findall(contenido))
    for etiqueta in ETIQUETA.findall(texto):
        encontrados |= set(CITADA.findall(etiqueta))
    return encontrados


def archivos_propios():
    raiz = Path(settings.BASE_DIR)
    for ruta in raiz.rglob("*"):
        relativa = ruta.relative_to(raiz)
        if ruta.suffix in PROPIOS and not OMITIR & set(relativa.parts) and not relativa.as_posix().startswith(COMPILADOS):
            yield ruta


def archivos_de_unfold():
    yield UNFOLD / "static/unfold/js/app.js"
    for ruta in UNFOLD.rglob("*"):
        if ruta.suffix in {".html", ".py"}:
            yield ruta
    yield from (UNFOLD / "static/unfold/css").rglob("*.css")


def iconos_posibles():
    encontrados = set()
    for ruta in [*archivos_propios(), *archivos_de_unfold()]:
        encontrados |= candidatos(ruta.read_text(encoding="utf-8", errors="replace"))
    for grupo in settings.NAVEGACION:
        encontrados |= {item["icon"] for item in grupo["items"] if item.get("icon")}
    return encontrados


def iconos_recortados():
    return set(LISTA.read_text().split())
