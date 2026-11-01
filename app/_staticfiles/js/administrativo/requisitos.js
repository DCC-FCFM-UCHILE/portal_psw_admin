(() => {
const ESPERA = 250;
const ICONOS = { cumple: "check_circle", falla: "cancel", "": "radio_button_unchecked" };
const LECTURA = { cumple: " Cumple.", falla: " No cumple.", "": "" };
const estado = document.createElement("p");
estado.className = "sr-only";
estado.setAttribute("role", "status");
const alerta = document.createElement("p");
alerta.className = "sr-only";
alerta.setAttribute("role", "alert");

const mostrarError = (campo, lista) => {
    const id = `${campo.id}_error`;
    if (!document.getElementById(id)) {
        const marco = document.createElement("div");
        marco.className = "mt-2 text-xs text-rojo dark:text-oscuro-acento";
        marco.innerHTML = `<ul class="errorlist" id="${id}"><li><span class="material-symbols-outlined mr-1 select-none align-bottom text-[18px] leading-none" aria-hidden="true">warning</span></li></ul>`;
        marco.querySelector("li").append(`${lista.dataset.error} `);
        lista.closest('[id$="_helptext"]').before(marco);
        const otras = (campo.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
        campo.setAttribute("aria-describedby", [id, ...otras].join(" "));
    }
    campo.setAttribute("aria-invalid", "true");
    alerta.textContent = "";
    setTimeout(() => {
        alerta.textContent = lista.dataset.error;
    }, 150);
};

const preparar = (lista) => {
    const ayuda = lista.closest('[id$="_helptext"]');
    const campo = ayuda && document.getElementById(ayuda.id.replace(/_helptext$/, ""));
    const formulario = campo?.form;
    if (!formulario) {
        return;
    }
    const requisitos = [...lista.querySelectorAll("[data-requisito]")];
    const usuario = formulario.elements.namedItem("username");
    let reloj = null;
    let pedido = null;
    let resumen = "";
    let aprobado = false;
    let revisando = false;

    const marcar = (resultado, { forzar = false } = {}) => {
        let cumplidos = 0;
        requisitos.forEach((requisito) => {
            const valor = resultado?.[requisito.dataset.requisito];
            const clase = valor === true ? "cumple" : valor === false || (resultado && forzar) ? "falla" : "";
            cumplidos += clase === "cumple";
            requisito.classList.toggle("cumple", clase === "cumple");
            requisito.classList.toggle("falla", clase === "falla");
            requisito.querySelector(".material-symbols-outlined").textContent = ICONOS[clase];
            requisito.querySelector(".estado").textContent = LECTURA[clase];
        });
        const nuevo = !resultado || forzar ? "" : cumplidos === requisitos.length ? "La contraseña cumple todos los requisitos." : `Cumple ${cumplidos} de ${requisitos.length} requisitos.`;
        if (nuevo && nuevo !== resumen && document.activeElement === campo) {
            estado.textContent = nuevo;
        }
        resumen = nuevo;
        return cumplidos === requisitos.length;
    };

    const consultar = async () => {
        pedido?.abort();
        pedido = new AbortController();
        const enviada = campo.value;
        const datos = new FormData();
        datos.append("csrfmiddlewaretoken", formulario.elements.namedItem("csrfmiddlewaretoken")?.value ?? "");
        datos.append("_requisitos", "1");
        datos.append(campo.name, enviada);
        if (usuario) {
            datos.append("username", usuario.value);
        }
        try {
            const respuesta = await fetch(formulario.action, { method: "POST", body: datos, credentials: "same-origin", signal: pedido.signal });
            if (!respuesta.ok || campo.value !== enviada) {
                return null;
            }
            return (await respuesta.json()).requisitos;
        } catch {
            return null;
        }
    };

    const programar = () => {
        clearTimeout(reloj);
        if (!campo.value) {
            pedido?.abort();
            marcar(null);
            return;
        }
        reloj = setTimeout(async () => {
            const resultado = await consultar();
            if (resultado) {
                marcar(resultado);
            }
        }, ESPERA);
    };

    campo.addEventListener("input", programar);
    usuario?.addEventListener("input", () => campo.value && programar());

    formulario.addEventListener("submit", async (evento) => {
        if (aprobado || !campo.checkVisibility()) {
            return;
        }
        evento.preventDefault();
        if (revisando) {
            return;
        }
        revisando = true;
        clearTimeout(reloj);
        const boton = evento.submitter;
        const resultado = await consultar();
        revisando = false;
        if (!resultado || marcar(resultado, { forzar: !campo.value })) {
            aprobado = true;
            formulario.requestSubmit(boton?.form === formulario ? boton : null);
            return;
        }
        mostrarError(campo, lista);
        campo.focus();
        document.getElementById(`${campo.id}_error`)?.scrollIntoView({ block: "nearest" });
    });
};

document.addEventListener("DOMContentLoaded", () => {
    const listas = document.querySelectorAll("[data-requisitos]");
    if (listas.length) {
        document.body.append(estado, alerta);
        listas.forEach(preparar);
    }
});
})();
