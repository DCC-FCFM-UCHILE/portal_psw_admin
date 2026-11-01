(() => {
const marca = document.getElementById("sesion");
if (!marca) {
    return;
}

const AVISO = 5 * 60 * 1000;
const CLAVE = "sesion-vence";
let vence = Number(marca.dataset.vence);
let reloj = null;
let fin = null;
let origen = null;
let dialogo = null;

const hora = (milisegundos) => new Date(milisegundos).toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
const token = () => document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ?? "";
const anunciar = (texto) => {
    const estado = document.getElementById("estado-navegacion");
    if (estado) {
        estado.textContent = texto;
    }
};

const consultar = async (metodo) => {
    const respuesta = await fetch(marca.dataset.url, {
        method: metodo,
        credentials: "same-origin",
        headers: metodo === "POST" ? { "X-CSRFToken": token() } : {},
    });
    if (respuesta.status === 401 || respuesta.status === 403) {
        return 0;
    }
    if (!respuesta.ok) {
        throw new Error(respuesta.status);
    }
    return (await respuesta.json()).vence;
};

const armar = () => {
    dialogo = document.createElement("dialog");
    dialogo.id = "dialogo-sesion";
    dialogo.setAttribute("aria-labelledby", "dialogo-sesion-titulo");
    dialogo.setAttribute("aria-describedby", "dialogo-sesion-texto");
    dialogo.className = "dialogo-confirmar rounded-lg border-base-200 text-gris-oscuro shadow-lg dark:border-oscuro-elevada dark:text-oscuro-texto";
    dialogo.innerHTML = `<form method="dialog" class="flex flex-col gap-3">
        <h2 id="dialogo-sesion-titulo" class="text-lg font-semibold"></h2>
        <p id="dialogo-sesion-texto" class="text-sm text-gris-medio dark:text-oscuro-suave"></p>
        <div class="mt-3 flex flex-wrap justify-end gap-2"></div>
    </form>`;
    dialogo.addEventListener("close", () => {
        administrativo.bloquearDesplazamiento();
        const destino = origen && origen !== document.body && origen.isConnected && origen.checkVisibility() ? origen : document.getElementById("contenido");
        destino?.focus({ preventScroll: true });
    });
    document.body.append(dialogo);
};

const boton = (texto, clase, accion) => {
    const elemento = document.createElement("button");
    elemento.type = accion ? "button" : "submit";
    elemento.className = clase;
    elemento.textContent = texto;
    if (accion) {
        elemento.addEventListener("click", accion);
    }
    return elemento;
};

const mostrar = (titulo, texto, botones) => {
    if (!dialogo) {
        armar();
    }
    dialogo.querySelector("h2").textContent = titulo;
    dialogo.querySelector("p").textContent = texto;
    dialogo.querySelector("div").replaceChildren(...botones);
    if (!dialogo.open) {
        origen = document.activeElement;
        dialogo.showModal();
        administrativo.bloquearDesplazamiento();
    }
    botones[0].focus();
};

const cerrar = () => {
    if (dialogo?.open) {
        dialogo.close();
    }
};

const programar = () => {
    clearTimeout(reloj);
    clearTimeout(fin);
    const espera = vence - AVISO - Date.now();
    reloj = setTimeout(revisar, Math.min(Math.max(espera, 0), 2 ** 31 - 1));
};

const terminada = () => {
    clearTimeout(fin);
    const ingresar = document.createElement("a");
    ingresar.className = "boton-primario";
    ingresar.href = `${marca.dataset.ingresar}?next=${encodeURIComponent(location.pathname + location.search)}`;
    ingresar.textContent = "Ingresar de nuevo";
    mostrar("Tu sesión terminó", "Lo que no hayas guardado ya no se puede guardar desde esta página. Ingresa de nuevo para seguir.", [
        ingresar,
        boton("Cerrar", "boton-secundario"),
    ]);
};

const seguir = async (evento) => {
    const elegido = evento.currentTarget;
    elegido.disabled = true;
    try {
        const nuevo = await consultar("POST");
        if (!nuevo) {
            terminada();
            return;
        }
        vence = nuevo;
        try {
            localStorage.setItem(CLAVE, String(vence));
        } catch {}
        cerrar();
        anunciar(`Seguirás conectado hasta las ${hora(vence)}.`);
        programar();
    } catch {
        elegido.disabled = false;
        dialogo.querySelector("p").textContent = "No se pudo extender la sesión. Revisa la conexión y vuelve a intentarlo.";
        elegido.focus();
    }
};

const avisar = () => {
    mostrar("Tu sesión está por terminar", `Termina a las ${hora(vence)}. Para seguir trabajando sin perder lo que no hayas guardado, elige «Seguir conectado».`, [
        boton("Seguir conectado", "boton-primario", seguir),
        boton("Cerrar", "boton-secundario"),
    ]);
    clearTimeout(fin);
    fin = setTimeout(revisar, Math.max(vence - Date.now(), 0) + 1000);
};

const revisar = async () => {
    try {
        vence = await consultar("GET");
    } catch {}
    if (!vence || vence <= Date.now()) {
        terminada();
    } else if (vence - Date.now() > AVISO) {
        cerrar();
        programar();
    } else {
        avisar();
    }
};

addEventListener("storage", (evento) => {
    if (evento.key === CLAVE && Number(evento.newValue) > vence) {
        vence = Number(evento.newValue);
        cerrar();
        programar();
    }
});

const alVolver = () => {
    if (document.visibilityState === "visible" && vence - Date.now() <= AVISO) {
        revisar();
    }
};
document.addEventListener("visibilitychange", alVolver);
addEventListener("pageshow", (evento) => evento.persisted && alVolver());

programar();
})();
