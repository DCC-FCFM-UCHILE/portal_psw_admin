(() => {
const SEPARACION_MENU = 4;
const MARGEN_MENU = 5;

const posicionDelMenu = (ancla, ancho, alto, limite) => {
    const debajo = ancla.bottom + SEPARACION_MENU;
    const encima = ancla.top - SEPARACION_MENU - alto;
    const cabeDebajo = debajo + alto <= limite - MARGEN_MENU;
    const subir = !cabeDebajo && encima >= MARGEN_MENU;
    const ninguno = !cabeDebajo && !subir;
    const izquierda = Math.max(MARGEN_MENU, Math.min(ancla.right - ancho, document.documentElement.clientWidth - ancho - MARGEN_MENU));
    const arriba = ninguno ? Math.max(MARGEN_MENU, Math.min(debajo, limite - MARGEN_MENU - alto)) : subir ? encima : debajo;
    return { izquierda, arriba, subir, ninguno };
};

document.addEventListener("alpine:init", () => {
    Alpine.data("menuEmergente", () => ({
        abierto: false,
        reubicar: null,

        init() {
            this.$watch("abierto", (abierto) => (abierto ? this.seguir() : this.soltar()));
        },

        destroy() {
            this.soltar();
        },

        lista() {
            return document.getElementById(this.$refs.disparador.getAttribute("aria-controls"));
        },

        opciones() {
            const menu = this.lista();
            return menu ? [...menu.querySelectorAll("a[href], button")] : [];
        },

        ubicar() {
            const menu = this.lista();
            if (!menu || !this.$refs.disparador.isConnected) {
                return;
            }
            const ancla = this.$refs.disparador.getBoundingClientRect();
            Object.assign(menu.style, { maxHeight: "", overflowY: "" });
            const limite = window.visualViewport?.height ?? window.innerHeight;
            const { izquierda, arriba, subir, ninguno } = posicionDelMenu(ancla, menu.offsetWidth, menu.offsetHeight, limite);
            Object.assign(menu.style, {
                position: "fixed",
                left: `${Math.round(izquierda)}px`,
                top: `${Math.round(arriba)}px`,
                transformOrigin: subir ? "bottom right" : "top right",
                maxHeight: ninguno ? `${Math.floor(limite - 2 * MARGEN_MENU)}px` : "",
                overflowY: ninguno ? "auto" : "",
            });
        },

        seguir() {
            this.soltar();
            let pendiente = false;
            this.reubicar = () => {
                if (pendiente) {
                    return;
                }
                pendiente = true;
                requestAnimationFrame(() => {
                    pendiente = false;
                    this.ubicar();
                });
            };
            document.addEventListener("scroll", this.reubicar, { capture: true, passive: true });
            window.addEventListener("resize", this.reubicar);
            window.visualViewport?.addEventListener("resize", this.reubicar);
            this.$nextTick(() => this.ubicar());
        },

        soltar() {
            if (!this.reubicar) {
                return;
            }
            document.removeEventListener("scroll", this.reubicar, { capture: true });
            window.removeEventListener("resize", this.reubicar);
            window.visualViewport?.removeEventListener("resize", this.reubicar);
            this.reubicar = null;
        },

        enfocar(indice) {
            const opciones = this.opciones();
            const opcion = opciones[(indice + opciones.length) % opciones.length];
            opcion?.focus({ preventScroll: true });
            if (this.lista()?.style.overflowY === "auto") {
                opcion?.scrollIntoView({ block: "nearest", inline: "nearest" });
            }
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
                    this.$nextTick(() => {
                        this.ubicar();
                        this.enfocar(0);
                    });
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
})();
