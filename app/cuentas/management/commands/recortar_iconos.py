import logging
import shutil

from django.core.management.base import BaseCommand

from cuentas.iconos import CARPETA, FUENTE, LISTA, RECORTE, iconos_posibles


def ligaduras(fuente):
    letras = {glifo: chr(codigo) for codigo, glifo in fuente.getBestCmap().items()}
    nombres = {}
    for consulta in fuente["GSUB"].table.LookupList.Lookup:
        for tabla in consulta.SubTable:
            tabla = getattr(tabla, "ExtSubTable", tabla)
            for primero, lista in getattr(tabla, "ligatures", {}).items():
                for ligadura in lista:
                    nombres["".join(letras.get(glifo, "") for glifo in [primero, *ligadura.Component])] = ligadura.LigGlyph
    return nombres


class Command(BaseCommand):
    help = "Deja en _staticfiles/fuentes la fuente de íconos de unfold con solo los íconos que usa el portal."

    def handle(self, *args, **options):
        from fontTools import subset
        from fontTools.ttLib import TTFont

        logging.getLogger("fontTools").setLevel(logging.ERROR)
        fuente = TTFont(FUENTE)
        nombres = ligaduras(fuente)
        iconos = sorted(iconos_posibles() & nombres.keys())
        opciones = subset.Options(layout_features=["rlig"], layout_closure=False, name_IDs=["*"], name_languages=["*"])
        recorte = subset.Subsetter(opciones)
        recorte.populate(text="".join(sorted(set("".join(iconos)))), glyphs=[nombres[icono] for icono in iconos])
        recorte.subset(fuente)
        CARPETA.mkdir(exist_ok=True)
        fuente.flavor = "woff2"
        fuente.save(RECORTE)
        shutil.copyfile(FUENTE.parent / "LICENSE", CARPETA / "LICENSE-material-symbols")
        LISTA.write_text("\n".join(iconos) + "\n")
        self.stdout.write(f"{len(iconos)} íconos en {RECORTE.name} ({RECORTE.stat().st_size} bytes)")
