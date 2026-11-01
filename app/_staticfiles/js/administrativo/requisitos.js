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

const descripciones = (campo) => (campo.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
const textos = (error) => [...error.querySelectorAll("li")].map((li) => [...li.childNodes].filter((nodo) => nodo.nodeType === Node.TEXT_NODE).map((nodo) => nodo.textContent).join("").trim());

const mostrarError = (campo, lista, texto) => {
    const id = `${campo.id}_error`;
    let error = document.getElementById(id);
    if (!error) {
        const marco = document.createElement("div");
        marco.className = "mt-2 text-xs text-rojo dark:text-oscuro-acento";
        marco.innerHTML = `<ul class="errorlist" id="${id}"></ul>`;
        lista.closest('[id$="_helptext"]').before(marco);
        error = marco.firstElementChild;
    }
    error.innerHTML = '<li><span class="material-symbols-outlined mr-1 select-none align-bottom text-[18px] leading-none" aria-hidden="true">warning</span></li>';
    error.firstElementChild.append(`${texto} `);
    campo.setAttribute("aria-describedby", [id, ...descripciones(campo).filter((otra) => otra !== id)].join(" "));
    campo.setAttribute("aria-invalid", "true");
    alerta.textContent = "";
    setTimeout(() => {
        alerta.textContent = texto;
    }, 150);
};

const quitarError = (campo, lista) => {
    const id = `${campo.id}_error`;
    const error = document.getElementById(id);
    if (!error || !textos(error).every((texto) => texto === lista.dataset.error || texto === lista.dataset.obligatorio)) {
        return;
    }
    error.parentElement.remove();
    campo.setAttribute("aria-describedby", descripciones(campo).filter((otra) => otra !== id).join(" "));
    campo.removeAttribute("aria-invalid");
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

    const marcar = (resultado) => {
        let cumplidos = 0;
        requisitos.forEach((requisito) => {
            const valor = resultado?.[requisito.dataset.requisito];
            const clase = valor === true ? "cumple" : valor === false ? "falla" : "";
            cumplidos += clase === "cumple";
            requisito.classList.toggle("cumple", clase === "cumple");
            requisito.classList.toggle("falla", clase === "falla");
            requisito.querySelector(".material-symbols-outlined").textContent = ICONOS[clase];
            requisito.querySelector(".estado").textContent = LECTURA[clase];
        });
        const todos = cumplidos === requisitos.length;
        const nuevo = !resultado ? "" : todos ? "La contraseña cumple todos los requisitos." : `Cumple ${cumplidos} de ${requisitos.length} requisitos.`;
        if (!nuevo) {
            estado.textContent = "";
        } else if (nuevo !== resumen && document.activeElement === campo) {
            estado.textContent = nuevo;
        }
        resumen = nuevo;
        if (resultado && todos) {
            quitarError(campo, lista);
        }
        return todos;
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
        const error = document.getElementById(`${campo.id}_error`);
        if (error && textos(error).includes(lista.dataset.obligatorio)) {
            quitarError(campo, lista);
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
        clearTimeout(reloj);
        if (!campo.value) {
            pedido?.abort();
            marcar(null);
            mostrarError(campo, lista, lista.dataset.obligatorio);
            campo.focus();
            document.getElementById(`${campo.id}_error`)?.scrollIntoView({ block: "nearest" });
            return;
        }
        revisando = true;
        const boton = evento.submitter;
        const resultado = await consultar();
        revisando = false;
        if (!resultado || marcar(resultado)) {
            aprobado = true;
            formulario.requestSubmit(boton?.form === formulario ? boton : null);
            return;
        }
        mostrarError(campo, lista, lista.dataset.error);
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
