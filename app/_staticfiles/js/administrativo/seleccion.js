(() => {
const casillasDeFila = () => [...document.querySelectorAll("#result_list input.action-select")];
let ultimaCasilla = null;
let conMayuscula = false;

const verSeleccion = (estado) => {
    const acciones = document.querySelector("#changelist-form div.actions");
    if (!acciones) {
        return;
    }
    acciones.querySelector("span.question")?.classList.toggle("hidden", estado !== "pagina");
    const contador = acciones.querySelector("span.action-counter");
    const todas = acciones.querySelector("span.all");
    if (estado === "todas" && contador && todas) {
        contador.textContent = todas.textContent.trim();
    }
    acciones.querySelector("input.select-across").value = estado === "todas" ? 1 : 0;
};

const contarSeleccion = () => {
    const contador = document.querySelector("#changelist-form span.action-counter");
    const todas = document.getElementById("action-toggle");
    if (!contador || !todas) {
        return;
    }
    const casillas = casillasDeFila();
    const marcadas = casillas.filter((casilla) => casilla.checked).length;
    contador.textContent = contador.dataset.plantilla.replace("%(sel)s", marcadas).replace("%(cnt)s", contador.dataset.actionsIcnt);
    todas.checked = casillas.length > 0 && marcadas === casillas.length;
    verSeleccion(todas.checked ? "pagina" : "ninguna");
};

administrativo.olvidarSeleccion = () => {
    ultimaCasilla = null;
    contarSeleccion();
};

const marcar = (casillas, marcada) => {
    casillas.forEach((casilla) => {
        casilla.checked = marcada;
        casilla.closest("tr").classList.toggle("selected", marcada);
    });
};

administrativo.marcarSeleccion = (valores) => {
    marcar(casillasDeFila().filter((casilla) => valores.includes(casilla.value)), true);
    contarSeleccion();
};

document.addEventListener("keydown", (evento) => {
    conMayuscula = evento.shiftKey;
});
document.addEventListener("keyup", (evento) => {
    conMayuscula = evento.shiftKey;
});

document.addEventListener("change", (evento) => {
    const casilla = evento.target;
    if (!casilla.matches?.("#result_list input.action-select")) {
        return;
    }
    const casillas = casillasDeFila();
    let afectadas = [casilla];
    if (conMayuscula && ultimaCasilla !== casilla && casillas.includes(ultimaCasilla)) {
        const [desde, hasta] = [casillas.indexOf(ultimaCasilla), casillas.indexOf(casilla)].sort((a, b) => a - b);
        afectadas = casillas.slice(desde, hasta + 1);
    }
    marcar(afectadas, casilla.checked);
    contarSeleccion();
    ultimaCasilla = casilla;
});

window.addEventListener("pageshow", contarSeleccion);

const pideConfirmacion = (accion) =>
    accion.form.querySelector("input.select-across")?.value === "1" && ["aceptar", "rechazar"].includes(accion.dataset.accion) && !accion.dataset.confirmada;

const confirmarEnLote = (accion) => {
    const verbo = accion.dataset.accion === "aceptar" ? "Aceptar" : "Rechazar";
    const total = accion.form.querySelector("span.all")?.textContent.match(/\d+/)?.[0] || "";
    administrativo.confirmar({
        titulo: `¿${verbo} ${total ? `las ${total} postulaciones` : "todas las postulaciones"}?`,
        texto: "Incluye las que no están en esta página. Las que ya estaban en ese estado no cambian; las demás quedan sin notificar.",
        si: total ? `${verbo} ${total}` : verbo,
        no: "Cancelar",
        principal: "si",
    }).then((si) => {
        if (si) {
            accion.dataset.confirmada = "1";
            accion.click();
            delete accion.dataset.confirmada;
        }
    });
};

document.addEventListener("click", (evento) => {
    if (evento.target.id === "action-toggle") {
        marcar(casillasDeFila(), evento.target.checked);
        contarSeleccion();
        return;
    }
    if (evento.target.closest("#changelist-form span.question button")) {
        evento.preventDefault();
        verSeleccion("todas");
        evento.target.closest("form")?.querySelector("[data-accion]")?.focus();
        return;
    }
    const accion = evento.target.closest("[data-accion]");
    if (accion) {
        accion.form.elements.namedItem("action").value = accion.dataset.accion;
        if (pideConfirmacion(accion)) {
            evento.preventDefault();
            confirmarEnLote(accion);
        }
        return;
    }
    if (evento.target.closest("[data-quitar-seleccion]")) {
        const todas = document.getElementById("action-toggle");
        todas.checked = true;
        todas.click();
        todas.focus();
    }
});

const temporizadores = new WeakMap();

const esperarParaConfirmar = () => {
    document.querySelectorAll("button[data-espera]").forEach((boton) => {
        clearInterval(temporizadores.get(boton));
        const cuenta = boton.querySelector("[data-cuenta]");
        const aviso = document.getElementById(boton.getAttribute("aria-describedby"));
        let restante = Number(boton.dataset.espera);
        boton.disabled = true;
        cuenta.hidden = false;
        cuenta.textContent = `(${restante})`;
        aviso.textContent = `Podrás confirmar en ${restante} segundos.`;
        temporizadores.set(
            boton,
            setInterval(() => {
                restante -= 1;
                cuenta.textContent = `(${restante})`;
                if (restante > 0) {
                    return;
                }
                clearInterval(temporizadores.get(boton));
                cuenta.hidden = true;
                boton.disabled = false;
                aviso.textContent = "Ya puedes confirmar.";
            }, 1000),
        );
    });
};

window.addEventListener("pageshow", esperarParaConfirmar);
})();
