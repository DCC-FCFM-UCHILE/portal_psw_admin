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

window.administrativo = {
    clicSimple: (evento) => !evento.defaultPrevented && evento.button === 0 && !(evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey),
    enlaceComun: (enlace) => !enlace.target && !enlace.hasAttribute("download") && !enlace.getAttribute("href").startsWith("#"),
};

let sinFoco = null;
document.addEventListener("focusout", (evento) => {
    sinFoco = evento.relatedTarget ? null : evento.target;
});

document.addEventListener("alpine:init", () => {
    const original = window.theme;
    if (typeof original !== "function") {
        return;
    }
    window.theme = (...argumentos) => {
        const datos = original(...argumentos);
        const sistema = matchMedia("(prefers-color-scheme: dark)");
        const cajon = matchMedia("(max-width: 1280px)");
        const iniciar = datos.init;
        datos.sistemaOscuro = sistema.matches;
        datos.esCajon = cajon.matches;
        datos.cerrarCajon = function () {
            this.sidebarOpen = false;
            this.$nextTick(() => document.getElementById("alternar-menu")?.focus({ preventScroll: true }));
        };
        datos.init = function () {
            iniciar?.call(this);
            if (typeof this.sidebarOpen === "function") {
                this.sidebarOpen = this.sidebarOpen();
            }
            sistema.addEventListener("change", (evento) => {
                this.sistemaOscuro = evento.matches;
            });
            cajon.addEventListener("change", (evento) => {
                const enfocado = document.activeElement === document.body ? sinFoco : document.activeElement;
                if (evento.matches) {
                    if (document.getElementById("nav-sidebar")?.contains(enfocado)) {
                        document.getElementById("alternar-menu")?.focus();
                    }
                    this.sidebarOpen = false;
                } else {
                    try {
                        this.sidebarOpen = localStorage.getItem("sidebarOpen") !== "0";
                    } catch {
                        this.sidebarOpen = true;
                    }
                    if (enfocado?.id === "cerrar-menu") {
                        const alternar = document.getElementById("alternar-menu");
                        alternar?.focus();
                        setTimeout(() => {
                            if (document.activeElement === document.body || document.activeElement?.id === "cerrar-menu") {
                                alternar?.focus();
                            }
                        });
                    }
                }
                this.esCajon = evento.matches;
            });
        };
        delete datos.themeBindings["x-resize.window"];
        datos.themeBindings["x-bind:class"] = function () {
            if (this.adminTheme === "dark" || (this.adminTheme === "auto" && this.sistemaOscuro)) {
                return "dark";
            }
            return this.adminTheme === "light" ? "light" : "";
        };
        return datos;
    };
});
})();
