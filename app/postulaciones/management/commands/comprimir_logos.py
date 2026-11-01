import os
import tempfile

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from postulaciones.imagenes import ImagenInvalida, comprimir
from postulaciones.models import Unit


def kb(peso):
    return f"{peso / 1024:.0f} KB"


class Command(BaseCommand):
    help = (
        "Comprime los logos de las unidades que ya están guardados, con el mismo nombre y formato, para que el portal "
        "actual los siga encontrando. No cambia la base. Sin --aplicar solo informa."
    )

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true", help="Reemplaza los archivos. Sin esto no escribe nada.")

    def handle(self, *args, aplicar=False, **options):
        nombres = sorted(set(Unit.objects.exclude(logo="").exclude(logo__isnull=True).values_list("logo", flat=True)))
        antes = despues = comprimidos = 0
        for nombre in nombres:
            if not nombre.lower().endswith((".png", ".jpg", ".jpeg")):
                self.stdout.write(f"se omite, no es PNG ni JPG: {nombre}")
                continue
            if not default_storage.exists(nombre):
                self.stdout.write(f"no está en disco: {nombre}")
                continue
            with default_storage.open(nombre, "rb") as archivo:
                contenido = archivo.read()
            try:
                resultado = comprimir(contenido)
            except ImagenInvalida:
                self.stdout.write(f"no es una imagen que se pueda abrir: {nombre}")
                continue
            antes += len(contenido)
            if resultado is None:
                despues += len(contenido)
                continue
            despues += len(resultado)
            comprimidos += 1
            self.stdout.write(f"{nombre}: {kb(len(contenido))} → {kb(len(resultado))}")
            if aplicar:
                ruta = default_storage.path(nombre)
                descriptor, temporal = tempfile.mkstemp(dir=os.path.dirname(ruta))
                with os.fdopen(descriptor, "wb") as salida:
                    salida.write(resultado)
                os.chmod(temporal, os.stat(ruta).st_mode)
                os.replace(temporal, ruta)
        accion = "comprimidos" if aplicar else "se comprimirían (sin --aplicar no se escribió nada)"
        self.stdout.write(f"{comprimidos} de {len(nombres)} logos {accion}: {kb(antes)} → {kb(despues)}")
