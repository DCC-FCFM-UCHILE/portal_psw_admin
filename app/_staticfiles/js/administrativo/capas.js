(() => {
const icono = ".material-symbols-outlined:not([aria-hidden])";
const asterisco = "label > span.text-red-600:not([aria-hidden])";
const ayuda = ".help-tooltip[aria-label]:not([role])";
const selectorDeFecha = 'a:is([id^="calendarlink"], [id^="clocklink"]):not([aria-label])';

const nombrarSelectorDeFecha = (enlace) => {
    const grupo = enlace.closest('[role="group"][aria-labelledby]');
    const etiqueta = grupo ? document.getElementById(grupo.getAttribute("aria-labelledby")) : enlace.closest(".grow")?.previousElementSibling;
    const nombre = etiqueta?.textContent.replace("*", "").replace(/\s+/g, " ").trim();
    const tipo = enlace.id.startsWith("calendar") ? "Elegir la fecha" : "Elegir la hora";
    enlace.setAttribute("aria-label", nombre ? `${tipo}: ${nombre}` : tipo);
};

const ajustar = (elemento) => {
    if (elemento.matches(`${icono}, ${asterisco}`)) {
        elemento.setAttribute("aria-hidden", "true");
    } else if (elemento.matches(ayuda)) {
        elemento.setAttribute("role", "img");
    } else if (elemento.matches(selectorDeFecha)) {
        nombrarSelectorDeFecha(elemento);
    }
};

const ajustarIconos = (raiz) => {
    raiz.querySelectorAll(`${icono}, ${asterisco}, ${ayuda}, ${selectorDeFecha}`).forEach(ajustar);
};

const capasModales = '#modal-overlay, .velo-lateral, [x-data="searchCommand()"], #changelist-filter, :has(> #modal-content), dialog[open]';

const bloquearDesplazamiento = () => {
    const raiz = document.documentElement;
    const abierta = [...document.querySelectorAll(capasModales)].some((capa) => capa.getClientRects().length > 0 && getComputedStyle(capa).position === "fixed");
    if (abierta && !raiz.classList.contains("sin-desplazamiento")) {
        raiz.style.setProperty("--barra-oculta", `${window.innerWidth - raiz.clientWidth}px`);
    }
    raiz.classList.toggle("sin-desplazamiento", abierta);
};

const alturas = new Map();

administrativo.bloquearDesplazamiento = bloquearDesplazamiento;

const medirAlto = (elemento, variable) => {
    alturas.get(variable)?.disconnect();
    if (!elemento || !("ResizeObserver" in window)) {
        return;
    }
    const observador = new ResizeObserver(() =>
        requestAnimationFrame(() => {
            const alto = `${Math.ceil(elemento.getBoundingClientRect().height)}px`;
            if (document.documentElement.style.getPropertyValue(variable) !== alto) {
                document.documentElement.style.setProperty(variable, alto);
            }
        }),
    );
    observador.observe(elemento);
    alturas.set(variable, observador);
};

administrativo.medirAlto = medirAlto;

document.addEventListener("DOMContentLoaded", () => {
    ajustarIconos(document);
    new MutationObserver((cambios) => {
        cambios.forEach((cambio) => {
            cambio.addedNodes.forEach((nodo) => {
                if (nodo.nodeType === Node.ELEMENT_NODE) {
                    ajustar(nodo);
                    ajustarIconos(nodo);
                }
            });
        });
    }).observe(document.body, { childList: true, subtree: true });

    const capas = new MutationObserver(bloquearDesplazamiento);
    document.querySelectorAll(`${capasModales}, .envoltura-lateral`).forEach((capa) => capas.observe(capa, { attributes: true, attributeFilter: ["style"] }));
    window.addEventListener("resize", bloquearDesplazamiento);

    medirAlto(document.getElementById("cabecera"), "--alto-cabecera");
    medirAlto(document.querySelector(".pie-paginacion"), "--alto-pie");
    medirAlto(document.querySelector(".barra-acciones"), "--alto-barra");

    const avisos = document.getElementById("avisos");
    if (avisos && !document.querySelector("[autofocus]")) {
        avisos.focus({ preventScroll: true });
    }

    if (administrativo.zonaListado()) {
        history.replaceState({ ...history.state, listado: true }, "");
    }
});
})();
