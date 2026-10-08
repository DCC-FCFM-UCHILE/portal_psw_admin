(() => {
const atajosDeUnaTecla = new Set(["[", "f", "c", "/", "?"]);

const esEditable = (elemento) =>
    elemento instanceof HTMLElement && (elemento.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(elemento.tagName));

window.addEventListener(
    "keydown",
    (evento) => {
        if (!evento.ctrlKey && !evento.metaKey && !evento.altKey && atajosDeUnaTecla.has(evento.key) && !esEditable(document.activeElement)) {
            evento.stopImmediatePropagation();
        }
    },
    true,
);

document.addEventListener("alpine:init", () => {
    const original = window.theme;
    if (typeof original !== "function") {
        return;
    }
    window.theme = (...argumentos) => {
        const datos = original(...argumentos);
        const sistema = matchMedia("(prefers-color-scheme: dark)");
        const iniciar = datos.init;
        datos.sistemaOscuro = sistema.matches;
        datos.init = function () {
            iniciar?.call(this);
            sistema.addEventListener("change", (evento) => {
                this.sistemaOscuro = evento.matches;
            });
        };
        datos.themeBindings["x-bind:class"] = function () {
            if (this.adminTheme === "dark" || (this.adminTheme === "auto" && this.sistemaOscuro)) {
                return "dark";
            }
            return this.adminTheme === "light" ? "light" : "";
        };
        return datos;
    };
});

const marcarFormato = (evento) => {
    requestAnimationFrame(() => {
        evento.target.toolbarElement?.querySelectorAll("button[data-trix-attribute]").forEach((boton) => {
            boton.setAttribute("aria-pressed", boton.classList.contains("trix-active").toString());
        });
    });
};

document.addEventListener("trix-initialize", marcarFormato);
document.addEventListener("trix-selection-change", marcarFormato);

const icono = ".material-symbols-outlined:not([aria-hidden])";
const ayuda = ".help-tooltip[aria-label]:not([role])";

const ajustar = (elemento) => {
    if (elemento.matches(icono)) {
        elemento.setAttribute("aria-hidden", "true");
    } else if (elemento.matches(ayuda)) {
        elemento.setAttribute("role", "img");
    }
};

const ajustarIconos = (raiz) => {
    raiz.querySelectorAll(`${icono}, ${ayuda}`).forEach(ajustar);
};

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

    const avisos = document.getElementById("avisos");
    if (avisos && !document.querySelector("[autofocus]")) {
        avisos.focus({ preventScroll: true });
    }
});
})();
