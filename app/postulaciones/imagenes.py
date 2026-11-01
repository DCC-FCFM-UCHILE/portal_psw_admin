import io

from PIL import Image, ImageOps, UnidentifiedImageError

LADO = (640, 320)
MAXIMO_DE_PIXELES = 40_000_000
AHORRO_MINIMO = 0.9
AJUSTES = {
    "PNG": {"optimize": True},
    "JPEG": {"quality": 85, "optimize": True, "progressive": True},
}


class ImagenInvalida(ValueError):
    pass


def comprimir(contenido):
    try:
        with Image.open(io.BytesIO(contenido)) as original:
            formato = original.format
            if formato not in AJUSTES or original.width * original.height > MAXIMO_DE_PIXELES:
                raise ImagenInvalida
            imagen = ImageOps.exif_transpose(original)
            if imagen.mode in ("P", "1", "LA"):
                imagen = imagen.convert("RGBA")
            imagen.thumbnail(LADO, Image.Resampling.LANCZOS)
            if formato == "JPEG" and imagen.mode not in ("RGB", "L"):
                imagen = imagen.convert("RGB")
            perfil = original.info.get("icc_profile") if imagen.mode == original.mode else None
            salida = io.BytesIO()
            imagen.save(salida, formato, icc_profile=perfil, **AJUSTES[formato])
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as error:
        raise ImagenInvalida from error
    comprimido = salida.getvalue()
    return comprimido if len(comprimido) <= len(contenido) * AHORRO_MINIMO else None
