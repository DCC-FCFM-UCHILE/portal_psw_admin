(() => {
const tabulables = (raiz) =>
    [...raiz.querySelectorAll('a[href], button:not([disabled]), input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')].filter((elemento) => elemento.checkVisibility());

let origenDeEmergente = null;

window.addEventListener(
    "click",
    (evento) => {
        const enlace = evento.target.closest?.("a.related-widget-wrapper-link, a.related-lookup");
        if (!enlace) {
            return;
        }
        const menu = enlace.closest("nav[id]");
        const disparador = menu && document.querySelector(`[aria-controls="${menu.id}"]`);
        origenDeEmergente = disparador || enlace;
        if (disparador) {
            try {
                Alpine.$data(disparador).abierto = false;
            } catch {}
        }
    },
    true,
);

const cerrarCapaMadre = () => {
    try {
        window.parent.Alpine.$data(window.parent.document.body).openModal = false;
    } catch {}
};

const salirPorLosBordes = (evento) => {
    const enfocables = tabulables(document);
    if (!enfocables.length) {
        return;
    }
    const extremo = evento.shiftKey ? enfocables[0] : enfocables.at(-1);
    if (document.activeElement !== extremo && enfocables.includes(document.activeElement)) {
        return;
    }
    evento.preventDefault();
    const cerrar = window.parent.document.querySelector("#capa-emergente > button");
    if (cerrar) {
        cerrar.focus();
    } else {
        (evento.shiftKey ? enfocables.at(-1) : enfocables[0]).focus();
    }
};

if (window.parent !== window && (new URLSearchParams(location.search).has("_popup") || document.querySelector('input[name="_popup"]'))) {
    window.addEventListener("keydown", (evento) => {
        if (evento.defaultPrevented) {
            return;
        }
        if (evento.key === "Escape") {
            cerrarCapaMadre();
        } else if (evento.key === "Tab") {
            salirPorLosBordes(evento);
        }
    });
}

const prepararEmergente = (marco) => {
    marco.addEventListener("load", () => {
        const documento = marco.contentDocument;
        if (!documento || documento.getElementById("django-admin-popup-response-constants")) {
            return;
        }
        const titulo = documento.title.split(" | ")[0].trim();
        marco.title = titulo;
        document.getElementById("capa-emergente")?.setAttribute("aria-label", titulo);
        const enfocarDentro = (intentos) => {
            const campo = documento.querySelector('#content :is(input:not([type="hidden"]), select, textarea):not([disabled])');
            const yaEnfocado = documento.activeElement && documento.activeElement !== documento.body;
            if (marco.checkVisibility() && (campo || yaEnfocado)) {
                marco.contentWindow.focus();
                if (yaEnfocado) {
                    documento.activeElement.focus();
                } else {
                    campo.focus();
                }
            } else if (intentos > 0) {
                requestAnimationFrame(() => enfocarDentro(intentos - 1));
            }
        };
        requestAnimationFrame(() => enfocarDentro(30));
    });
};

document.addEventListener("DOMContentLoaded", () => {
    const contenido = document.getElementById("modal-content");
    const capa = document.getElementById("capa-emergente");
    if (!contenido || !capa) {
        return;
    }
    capa.querySelector(":scope > button")?.addEventListener("keydown", (evento) => {
        const marco = contenido.querySelector("iframe");
        const documento = marco?.contentDocument;
        if (evento.key !== "Tab" || !documento) {
            return;
        }
        const enfocables = tabulables(documento);
        if (enfocables.length) {
            evento.preventDefault();
            marco.contentWindow.focus();
            (evento.shiftKey ? enfocables.at(-1) : enfocables[0]).focus();
        }
    });
    new MutationObserver(() => contenido.querySelectorAll("iframe:not([data-preparado])").forEach((marco) => {
        marco.dataset.preparado = "1";
        prepararEmergente(marco);
    })).observe(contenido, { childList: true });
    new MutationObserver(() => {
        if (capa.style.display === "none" && origenDeEmergente) {
            const destino = origenDeEmergente;
            origenDeEmergente = null;
            requestAnimationFrame(() => destino.isConnected && destino.checkVisibility() && destino.focus({ preventScroll: true }));
        }
    }).observe(capa, { attributes: true, attributeFilter: ["style"] });
});
})();
