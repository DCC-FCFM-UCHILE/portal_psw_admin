from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.http import JsonResponse

TEXTOS = {
    "MinimumLengthValidator": lambda validador: f"Al menos {validador.min_length} caracteres.",
    "NumericPasswordValidator": lambda validador: "Que no sea solo números.",
    "CommonPasswordValidator": lambda validador: "Que no sea una contraseña muy usada, como «abcd1234» o «qwerty123».",
    "UserAttributeSimilarityValidator": lambda validador: (
        "Que no se parezca al nombre de usuario, al nombre, al apellido ni al correo de la cuenta."
    ),
}
ESTADOS = {None: "", True: "cumple", False: "falla"}
NO_CUMPLE = "La contraseña no cumple todos los requisitos."
CODIGOS = {"password_too_short", "password_entirely_numeric", "password_too_common", "password_too_similar"}


def requisitos(contrasena="", usuario=None):
    lista = []
    for validador in password_validation.get_default_password_validators():
        clave = type(validador).__name__
        cumple = None
        if contrasena:
            try:
                validador.validate(contrasena, usuario)
                cumple = True
            except ValidationError:
                cumple = False
        texto = TEXTOS[clave](validador) if clave in TEXTOS else validador.get_help_text()
        lista.append({"clave": clave, "texto": texto, "cumple": cumple, "estado": ESTADOS[cumple]})
    orden = list(TEXTOS)
    return sorted(lista, key=lambda requisito: orden.index(requisito["clave"]) if requisito["clave"] in orden else len(orden))


def pide_requisitos(request):
    return request.method == "POST" and request.POST.get("_requisitos") == "1"


def responder(formulario):
    return JsonResponse({"requisitos": formulario.requisitos()}, headers={"Cache-Control": "no-store"})
