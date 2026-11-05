import io
import logging
import re
import shutil
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ORIGEN = Path("node_modules/@fontsource-variable/inter")
DESTINO = Path("../_staticfiles/fuentes")
PESOS = (400, 900)


def rango(nombre):
    hoja = (ORIGEN / "wght.css").read_text()
    regla = re.search(rf"inter-{nombre}-wght-normal\.woff2.*?unicode-range:\s*([^;]+);", hoja, re.S).group(1)
    return subset.parse_unicodes(regla.replace("U+", ""))


def recortar(nombre):
    fuente = TTFont(ORIGEN / "files" / f"inter-{nombre}-wght-normal.woff2")
    intermedia = io.BytesIO()
    instancer.instantiateVariableFont(fuente, {"wght": PESOS}).save(intermedia)
    fuente = TTFont(intermedia)
    opciones = subset.Options(layout_features=["*"], name_IDs=["*"], name_languages=["*"], flavor="woff2")
    recorte = subset.Subsetter(opciones)
    recorte.populate(unicodes=rango(nombre))
    recorte.subset(fuente)
    destino = DESTINO / f"inter-{nombre}.woff2"
    fuente.save(destino)
    return destino


if __name__ == "__main__":
    if not ORIGEN.exists():
        sys.exit("uso: python3 recortar-inter.py, desde _node y con las dependencias de npm instaladas")
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    DESTINO.mkdir(exist_ok=True)
    for nombre in ("latin", "latin-ext"):
        destino = recortar(nombre)
        print(f"{destino.name}: {destino.stat().st_size} bytes")
    shutil.copyfile(ORIGEN / "LICENSE", DESTINO / "LICENSE-inter")
