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
            this.$nextTick(() => document.getElementById("alternar-menu")?.focus());
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

document.addEventListener("alpine:init", () => {
    Alpine.data("menuEmergente", () => ({
        abierto: false,

        opciones() {
            const menu = document.getElementById(this.$refs.disparador.getAttribute("aria-controls"));
            return menu ? [...menu.querySelectorAll("a[href]")] : [];
        },

        enfocar(indice) {
            const opciones = this.opciones();
            opciones[(indice + opciones.length) % opciones.length]?.focus();
        },

        cerrar() {
            this.abierto = false;
            this.$refs.disparador.focus();
        },

        disparador: {
            ":aria-expanded"() {
                return this.abierto.toString();
            },
            "@click"() {
                this.abierto = !this.abierto;
                if (this.abierto) {
                    this.$nextTick(() => this.enfocar(0));
                }
            },
            "@keydown.escape"() {
                this.abierto = false;
            },
        },

        menu: {
            "x-show"() {
                return this.abierto;
            },
            "@click.outside"(evento) {
                if (!this.$refs.disparador.contains(evento.target)) {
                    this.abierto = false;
                }
            },
            "@keydown.escape.stop"() {
                this.cerrar();
            },
            "@keydown.down.prevent"() {
                this.enfocar(this.opciones().indexOf(document.activeElement) + 1);
            },
            "@keydown.up.prevent"() {
                this.enfocar(this.opciones().indexOf(document.activeElement) - 1);
            },
            "@keydown.tab"(evento) {
                const opciones = this.opciones();
                const actual = opciones.indexOf(document.activeElement);
                if (evento.shiftKey && actual <= 0) {
                    evento.preventDefault();
                    this.cerrar();
                } else if (!evento.shiftKey && actual === opciones.length - 1) {
                    this.cerrar();
                }
            },
        },
    }));

    Alpine.data("zonaArchivo", () => ({
        nombre: "",
        encima: false,

        init() {
            this.$refs.entrada.hasChangeListener = true;
        },

        entrada: {
            "@change"(evento) {
                this.nombre = evento.target.files[0]?.name ?? "";
                this.encima = false;
            },
            "@dragenter"() {
                this.encima = true;
            },
            "@dragleave"() {
                this.encima = false;
            },
            "@drop"() {
                this.encima = false;
            },
        },
    }));

    Alpine.data("matrizPermisos", () => ({
        init() {
            this.$el.querySelectorAll("tr[data-fila]").forEach((fila) => this.sincronizar(fila));
        },

        sincronizar(fila) {
            const casillas = [...fila.querySelectorAll("input[name]")];
            const todas = fila.querySelector("input[data-todas]");
            const marcadas = casillas.filter((casilla) => casilla.checked).length;
            todas.checked = casillas.length > 0 && marcadas === casillas.length;
            todas.indeterminate = marcadas > 0 && marcadas < casillas.length;
        },

        cambio(evento) {
            const fila = evento.target.closest("tr[data-fila]");
            if (evento.target.hasAttribute("data-todas")) {
                fila.querySelectorAll("input[name]").forEach((casilla) => {
                    casilla.checked = evento.target.checked;
                });
            }
            if (fila) {
                this.sincronizar(fila);
            }
        },
    }));
});

document.addEventListener("trix-before-initialize", () => {
    const parrafo = window.Trix?.config.blockAttributes.p;
    if (parrafo) {
        parrafo.group = false;
    }
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

document.addEventListener("click", (evento) => {
    const accion = evento.target.closest("[data-accion]");
    if (accion) {
        accion.form.elements.namedItem("action").value = accion.dataset.accion;
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

document.addEventListener("formset:removed", (evento) => {
    document.getElementById(`${evento.detail.formsetName}-group`)?.querySelector(".add-row")?.focus();
});

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

    const cabecera = document.getElementById("cabecera");
    if (cabecera && "ResizeObserver" in window) {
        new ResizeObserver(() => {
            document.documentElement.style.setProperty("--alto-cabecera", `${Math.ceil(cabecera.getBoundingClientRect().height)}px`);
        }).observe(cabecera);
    }

    const avisos = document.getElementById("avisos");
    if (avisos && !document.querySelector("[autofocus]")) {
        avisos.focus({ preventScroll: true });
    }
});
})();
