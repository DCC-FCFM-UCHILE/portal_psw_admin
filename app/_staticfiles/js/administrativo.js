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

const SEPARACION_MENU = 4;
const MARGEN_MENU = 5;

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
            const ancho = menu.offsetWidth;
            const alto = menu.offsetHeight;
            const limite = window.visualViewport?.height ?? window.innerHeight;
            const debajo = ancla.bottom + SEPARACION_MENU;
            const encima = ancla.top - SEPARACION_MENU - alto;
            const cabeDebajo = debajo + alto <= limite - MARGEN_MENU;
            const subir = !cabeDebajo && encima >= MARGEN_MENU;
            const ninguno = !cabeDebajo && !subir;
            const izquierda = Math.max(MARGEN_MENU, Math.min(ancla.right - ancho, document.documentElement.clientWidth - ancho - MARGEN_MENU));
            const arriba = ninguno ? Math.max(MARGEN_MENU, Math.min(debajo, limite - MARGEN_MENU - alto)) : subir ? encima : debajo;
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
    if (!contador || !todas || typeof ngettext !== "function") {
        return;
    }
    const casillas = casillasDeFila();
    const marcadas = casillas.filter((casilla) => casilla.checked).length;
    const texto = ngettext("%(sel)s of %(cnt)s selected", "%(sel)s of %(cnt)s selected", marcadas);
    contador.textContent = interpolate(texto, { sel: marcadas, cnt: Number(contador.dataset.actionsIcnt) }, true);
    todas.checked = casillas.length > 0 && marcadas === casillas.length;
    verSeleccion(todas.checked ? "pagina" : "ninguna");
};

const marcar = (casillas, marcada) => {
    casillas.forEach((casilla) => {
        casilla.checked = marcada;
        casilla.closest("tr").classList.toggle("selected", marcada);
    });
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

document.addEventListener("click", (evento) => {
    if (evento.target.id === "action-toggle") {
        marcar(casillasDeFila(), evento.target.checked);
        contarSeleccion();
        return;
    }
    if (evento.target.closest("#changelist-form span.question a")) {
        evento.preventDefault();
        verSeleccion("todas");
        evento.target.closest("form")?.querySelector("[data-accion]")?.focus();
        return;
    }
    const accion = evento.target.closest("[data-accion]");
    if (accion) {
        accion.form.elements.namedItem("action").value = accion.dataset.accion;
        const todas = accion.form.querySelector("input.select-across")?.value === "1";
        if (todas && ["aceptar", "rechazar"].includes(accion.dataset.accion) && !accion.dataset.confirmada) {
            evento.preventDefault();
            const verbo = accion.dataset.accion === "aceptar" ? "Aceptar" : "Rechazar";
            const total = accion.form.querySelector("span.all")?.textContent.match(/\d+/)?.[0] || "";
            confirmar({
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

let envios = new WeakMap();
let saliendo = false;

const formulariosConDatos = () => [...document.querySelectorAll('#content form[method="post"]:not(#changelist-form)')];

const huella = (formulario) =>
    JSON.stringify(
        [...new FormData(formulario)]
            .filter(([nombre]) => nombre !== "csrfmiddlewaretoken")
            .map(([nombre, valor]) => [nombre, valor instanceof File ? `${valor.name}:${valor.size}` : valor]),
    );

const huellas = new WeakMap();
const conErrores = (formulario) => formulario.querySelector('.errornote, .errorlist, [aria-invalid="true"]');
const tomarHuellas = () => {
    formulariosConDatos().forEach((formulario) => huellas.set(formulario, conErrores(formulario) ? "" : huella(formulario)));
    vigilarSalida();
};
const hayCambios = () => !saliendo && formulariosConDatos().some((formulario) => huellas.has(formulario) && huellas.get(formulario) !== huella(formulario));

const retener = (evento) => {
    evento.preventDefault();
    evento.returnValue = true;
};

const vigilarSalida = () => {
    if (hayCambios()) {
        window.addEventListener("beforeunload", retener);
    } else {
        window.removeEventListener("beforeunload", retener);
    }
};

window.addEventListener("load", tomarHuellas);
document.addEventListener("trix-initialize", (evento) => {
    const formulario = evento.target.closest("form");
    if (formulario && huellas.has(formulario) && huellas.get(formulario) !== "" && !formulario.dataset.editado) {
        huellas.set(formulario, huella(formulario));
    }
});
["input", "change", "trix-change"].forEach((tipo) =>
    document.addEventListener(tipo, (evento) => {
        const formulario = evento.target.closest?.("form");
        if (formulario && evento.isTrusted !== false) {
            formulario.dataset.editado = "1";
        }
        vigilarSalida();
    }),
);

const confirmar = ({ titulo, texto, si, no, principal = "no" }) =>
    new Promise((responder) => {
        let dialogo = document.getElementById("dialogo-confirmar");
        if (!dialogo) {
            dialogo = document.createElement("dialog");
            dialogo.id = "dialogo-confirmar";
            dialogo.setAttribute("aria-labelledby", "dialogo-confirmar-titulo");
            dialogo.setAttribute("aria-describedby", "dialogo-confirmar-texto");
            dialogo.className = "dialogo-confirmar rounded-lg border-base-200 text-gris-oscuro shadow-lg dark:border-oscuro-elevada dark:text-oscuro-texto";
            dialogo.innerHTML = `<form method="dialog" class="flex flex-col gap-3">
                <h2 id="dialogo-confirmar-titulo" class="text-lg font-semibold"></h2>
                <p id="dialogo-confirmar-texto" class="text-sm text-gris-medio dark:text-oscuro-suave"></p>
                <div class="mt-3 flex flex-wrap justify-end gap-2"></div>
            </form>`;
            dialogo.addEventListener("close", bloquearDesplazamiento);
            document.body.append(dialogo);
        }
        dialogo.querySelector("#dialogo-confirmar-titulo").textContent = titulo;
        dialogo.querySelector("#dialogo-confirmar-texto").textContent = texto;
        const botones = [
            ["si", si],
            ["no", no],
        ].map(([valor, rotulo]) => {
            const boton = document.createElement("button");
            boton.type = "submit";
            boton.value = valor;
            boton.textContent = rotulo;
            boton.className = valor === principal ? "boton-primario" : "boton-secundario";
            boton.autofocus = valor === "no";
            return boton;
        });
        dialogo.querySelector("div").replaceChildren(...(principal === "no" ? botones : botones.reverse()));
        dialogo.returnValue = "";
        let cerroCajon = false;
        try {
            const estado = Alpine.$data(document.documentElement);
            if (estado.esCajon && estado.sidebarOpen === true) {
                estado.sidebarOpen = false;
                cerroCajon = true;
            }
        } catch {}
        dialogo.addEventListener(
            "close",
            () => {
                const activo = document.activeElement;
                if (cerroCajon || !activo || activo === document.body || !activo.checkVisibility()) {
                    document.getElementById("alternar-menu")?.focus({ preventScroll: true });
                }
                responder(dialogo.returnValue === "si");
            },
            { once: true },
        );
        dialogo.showModal();
        bloquearDesplazamiento();
    });

const preguntarSalida = () =>
    confirmar({ titulo: "Hay cambios sin guardar", texto: "Si sales de esta página, se pierden.", si: "Salir sin guardar", no: "Seguir editando" });

document.addEventListener(
    "click",
    (evento) => {
        const enlace = evento.target.closest?.("a[href]");
        if (!enlace || evento.defaultPrevented || evento.button !== 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) {
            return;
        }
        if (enlace.target || enlace.hasAttribute("download") || enlace.getAttribute("href").startsWith("#") || enlace.matches(".related-widget-wrapper-link, [data-popup]")) {
            return;
        }
        const destino = new URL(enlace.href, location.href);
        if ((destino.pathname === location.pathname && destino.search === location.search) || !hayCambios()) {
            return;
        }
        evento.preventDefault();
        evento.stopPropagation();
        preguntarSalida().then((salir) => {
            if (salir) {
                saliendo = true;
                vigilarSalida();
                enlace.click();
            }
        });
    },
    true,
);

document.addEventListener(
    "submit",
    (evento) => {
        const formulario = evento.target;
        if (formulario.method !== "post" || formulario.target) {
            return;
        }
        const anterior = envios.get(formulario);
        if (anterior !== undefined && performance.now() - anterior < 10000) {
            evento.preventDefault();
            evento.stopImmediatePropagation();
            return;
        }
        envios.set(formulario, performance.now());
    },
    true,
);

window.addEventListener("submit", (evento) => {
    const formulario = evento.target;
    if (formulario.method !== "post" || formulario.target) {
        return;
    }
    if (evento.defaultPrevented) {
        envios.delete(formulario);
        return;
    }
    if (formulario.closest("#content")) {
        saliendo = true;
        vigilarSalida();
    }
});

window.addEventListener("pageshow", (evento) => {
    envios = new WeakMap();
    if (evento.persisted) {
        saliendo = false;
        vigilarSalida();
    }
});

document.addEventListener("formset:added", (evento) => {
    evento.target.querySelector('input:not([type="hidden"]), select, textarea')?.focus();
});

document.addEventListener("focusin", (evento) => {
    const elemento = evento.target;
    elemento.closest?.(".matriz-permisos-marco td, #nav-sidebar-apps a")?.scrollIntoView({ block: "nearest", inline: "nearest" });
    if (!elemento.closest?.("#content") || !elemento.matches(":focus-visible")) {
        return;
    }
    requestAnimationFrame(() => {
        if (document.activeElement !== elemento) {
            return;
        }
        const caja = elemento.getBoundingClientRect();
        const techo = document.getElementById("cabecera")?.getBoundingClientRect().bottom ?? 0;
        if (caja.height && (caja.top < techo || caja.bottom > innerHeight)) {
            elemento.scrollIntoView({ block: "nearest" });
        }
    });
});

const marcarMatrices = () => {
    document.querySelectorAll('.matriz-permisos-marco[role="region"]').forEach((marco) => {
        if (marco.scrollWidth > marco.clientWidth + 1) {
            marco.setAttribute("tabindex", "0");
        } else {
            marco.removeAttribute("tabindex");
        }
    });
};

const vigiaDeMatrices = new ResizeObserver(marcarMatrices);

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('.matriz-permisos-marco[role="region"]').forEach((marco) => {
        vigiaDeMatrices.observe(marco);
        vigiaDeMatrices.observe(marco.firstElementChild);
    });
    document.fonts?.ready.then(marcarMatrices);
});

window.addEventListener("load", () => {
    const contenido = document.getElementById("content");
    if (!contenido || document.getElementById("login-form")) {
        return;
    }
    const campo = [...contenido.querySelectorAll('[aria-invalid="true"]')].find((elemento) => elemento.type !== "hidden" && elemento.checkVisibility());
    const general = contenido.querySelector("div.errornote");
    if (campo) {
        campo.focus();
    } else if (general) {
        general.setAttribute("tabindex", "-1");
        general.focus();
    }
});

document.addEventListener("formset:removed", (evento) => {
    document.getElementById(`${evento.detail.formsetName}-group`)?.querySelector(".add-row")?.focus();
});

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

    if (zonaListado()) {
        history.replaceState({ ...history.state, listado: true }, "");
    }
});

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

if (window.parent !== window && (new URLSearchParams(location.search).has("_popup") || document.querySelector('input[name="_popup"]'))) {
    window.addEventListener("keydown", (evento) => {
        if (evento.defaultPrevented) {
            return;
        }
        if (evento.key === "Escape") {
            try {
                window.parent.Alpine.$data(window.parent.document.body).openModal = false;
            } catch {}
            return;
        }
        if (evento.key !== "Tab") {
            return;
        }
        const enfocables = tabulables(document);
        if (!enfocables.length) {
            return;
        }
        const extremo = evento.shiftKey ? enfocables[0] : enfocables.at(-1);
        if (document.activeElement === extremo || !enfocables.includes(document.activeElement)) {
            evento.preventDefault();
            const cerrar = window.parent.document.querySelector("#capa-emergente > button");
            if (cerrar) {
                cerrar.focus();
            } else {
                (evento.shiftKey ? enfocables.at(-1) : enfocables[0]).focus();
            }
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

const regionesDeTabla = () => document.querySelectorAll('.zona-tabla [role="region"]');

const marcarBordes = (region) => {
    const maximo = region.scrollWidth - region.clientWidth;
    region.classList.toggle("hay-antes", region.scrollLeft > 1);
    region.classList.toggle("hay-despues", region.scrollLeft < maximo - 1);
};

const marcarTablas = () => {
    regionesDeTabla().forEach((region) => {
        marcarBordes(region);
        const inicio = region.querySelector(`#result_list tbody tr > ${CELDA_DE_INICIO}`);
        const fin = region.querySelector(`#result_list tbody ${CELDA_DE_FIN}`);
        const borde = region.getBoundingClientRect().left + region.clientLeft;
        const izquierda = inicio ? Math.ceil(inicio.getBoundingClientRect().right - borde) : 0;
        region.style.scrollPaddingInline = `${izquierda}px ${fin ? fin.offsetWidth : 0}px`;
    });
};

const CELDA_DE_INICIO = ":is(.action-checkbox + th, .action-checkbox-column + th, th:first-child:not(.action-checkbox-column))";
const CELDA_DE_FIN = ":is(.field-actions_holder, .columna-acciones)";

const descubrirEnTabla = (region, elemento) => {
    const fila = elemento.closest("tr");
    const inicio = fila?.querySelector(CELDA_DE_INICIO);
    const fin = fila?.querySelector(CELDA_DE_FIN);
    const caja = elemento.getBoundingClientRect();
    const marco = region.getBoundingClientRect();
    const izquierda = inicio ? inicio.getBoundingClientRect().right : marco.left;
    const derecha = fin ? fin.getBoundingClientRect().left : marco.right;
    if (caja.left < izquierda || caja.width > derecha - izquierda) {
        region.scrollLeft -= izquierda - caja.left;
    } else if (caja.right > derecha) {
        region.scrollLeft += caja.right - derecha;
    }
};

document.addEventListener("focusin", (evento) => {
    const elemento = evento.target;
    const region = elemento.closest?.('.zona-tabla [role="region"]');
    if (!region || elemento === region || elemento.closest(`.action-checkbox, .action-checkbox-column, ${CELDA_DE_INICIO}, ${CELDA_DE_FIN}`)) {
        return;
    }
    requestAnimationFrame(() => descubrirEnTabla(region, elemento));
});

let tablasPendientes = false;
const remarcarTablas = () => {
    if (tablasPendientes) {
        return;
    }
    tablasPendientes = true;
    requestAnimationFrame(() => {
        tablasPendientes = false;
        marcarTablas();
    });
};

const vigiaDeTablas = new ResizeObserver(remarcarTablas);
const vigilarTablas = () =>
    regionesDeTabla().forEach((region) => {
        vigiaDeTablas.observe(region);
        const tabla = region.querySelector("table");
        if (tabla) {
            vigiaDeTablas.observe(tabla);
        }
    });

document.addEventListener("DOMContentLoaded", () => {
    marcarTablas();
    vigilarTablas();
    document.fonts?.ready.then(remarcarTablas);
});
window.addEventListener("resize", remarcarTablas);
document.addEventListener("htmx:afterSettle", () => {
    vigilarTablas();
    remarcarTablas();
});
document.addEventListener(
    "scroll",
    (evento) => {
        if (evento.target instanceof Element && evento.target.matches('.zona-tabla [role="region"]')) {
            marcarBordes(evento.target);
        }
    },
    { capture: true, passive: true },
);

const UMBRAL = 400;
const ASPECTO = ["opacity", "color", "borderColor", "backgroundColor"];
const contextoListado = "#listado, #pie-listado, #changelist-filter, #conteo-cabecera";
const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)");
let enCurso = null;
let espera = null;

const zonaListado = () => document.querySelector("#listado[data-nombre]");
const controlesPie = () => [...document.querySelectorAll("#pie-listado nav :is(a, button, .numero-pagina)")];
const enfocables = (raiz) => [...raiz.querySelectorAll("a[href], button:not([disabled]), input:not([type='hidden'], [disabled]), select:not([disabled])")];

const aspecto = (elemento) => {
    const estilo = getComputedStyle(elemento);
    return Object.fromEntries(ASPECTO.map((propiedad) => [propiedad, estilo[propiedad]]));
};

const textoDelConteo = () => {
    const parrafo = document.querySelector("#pie-listado p");
    if (!parrafo) {
        return "";
    }
    const copia = parrafo.cloneNode(true);
    copia.querySelectorAll("a").forEach((enlace) => enlace.remove());
    return copia.textContent.replace(/\s+/g, " ").trim();
};

const anunciarListado = (texto) => {
    const estado = document.getElementById("estado-listado");
    if (estado) {
        estado.textContent = texto;
    }
};

const llegada = (destino) =>
    new Promise((listo) => {
        const tope = performance.now() + 1000;
        let antes = window.scrollY;
        let quieta = 0;
        const mirar = (ahora) => {
            quieta = window.scrollY === antes ? quieta + 1 : 0;
            antes = window.scrollY;
            if (Math.abs(antes - destino) < 2 || quieta > 5 || ahora > tope) {
                listo();
            } else {
                requestAnimationFrame(mirar);
            }
        };
        mirar(performance.now());
    });

const traerALaVista = (elemento, suave) => {
    const margen = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    const caja = elemento.getBoundingClientRect();
    if (caja.top >= margen && caja.top < window.innerHeight) {
        return Promise.resolve();
    }
    const maximo = document.documentElement.scrollHeight - window.innerHeight;
    const destino = Math.max(0, Math.min(window.scrollY + caja.top - margen, maximo));
    if (!suave || sinMovimiento.matches) {
        window.scrollTo({ top: destino, behavior: "instant" });
        return Promise.resolve();
    }
    const tramo = window.innerHeight;
    if (Math.abs(window.scrollY - destino) > tramo) {
        window.scrollTo({ top: destino + Math.sign(window.scrollY - destino) * tramo, behavior: "instant" });
    }
    window.scrollTo({ top: destino, behavior: "smooth" });
    return llegada(destino);
};

const destinoDelFoco = () => {
    const zona = zonaListado();
    const region = zona.querySelector('.zona-tabla [role="region"]');
    if (region) {
        return region;
    }
    const titulo = zona.querySelector(".zona-tabla h2");
    titulo?.setAttribute("tabindex", "-1");
    return titulo || zona;
};

const enfocar = (elemento) => {
    elemento.focus({ preventScroll: true });
    traerALaVista(elemento, false);
};

const cerrarFiltros = () => {
    try {
        const datos = Alpine.$data(document.documentElement);
        if (datos.filterModalOpen) {
            datos.filterOpen = false;
            return true;
        }
    } catch {}
    return false;
};

const mostrarCarga = (pedido) => {
    const tabla = pedido.objetivo.querySelector(".zona-tabla");
    const molde = document.getElementById("silueta-tabla");
    if (tabla && molde && !tabla.querySelector(".silueta-tabla")) {
        tabla.prepend(molde.content.cloneNode(true));
    }
    tabla?.classList.add("cargando");
    pedido.objetivo.setAttribute("aria-busy", "true");
    anunciarListado(`Cargando ${zonaListado().dataset.nombre}…`);
};

const conservarFiltros = () => {
    document.querySelectorAll("a.addlink").forEach((enlace) => {
        const url = new URL(enlace.href);
        const filtros = location.search.slice(1);
        if (filtros) {
            url.searchParams.set("_changelist_filters", filtros);
        } else {
            url.searchParams.delete("_changelist_filters");
        }
        enlace.href = url.pathname + url.search;
    });
};

const quitarCarga = () => {
    clearTimeout(espera);
    document.querySelectorAll("#listado[aria-busy], #resultados-listado[aria-busy]").forEach((zona) => zona.removeAttribute("aria-busy"));
    document.querySelectorAll(".zona-tabla.cargando").forEach((tabla) => {
        tabla.classList.remove("cargando");
        tabla.querySelector(".silueta-tabla")?.remove();
    });
};

const listar = (url, alcance, fuente, empujar = true) => {
    const zona = zonaListado();
    const activo = document.activeElement;
    const panel = document.getElementById("changelist-filter");
    const pedido = {
        url,
        alcance,
        empujar,
        fuente,
        objetivo: alcance === "pagina" ? document.getElementById("resultados-listado") : zona,
        focoId: activo?.id || "",
        focoPanel: panel?.contains(activo) ? enfocables(panel).indexOf(activo) : -1,
    };
    if (panel?.contains(fuente) && cerrarFiltros()) {
        pedido.focoId = "abrir-filtros";
        pedido.focoPanel = -1;
    }
    quitarCarga();
    enCurso = pedido;
    const emitir = () => {
        if (enCurso !== pedido) {
            return;
        }
        if (!pedido.fuente.isConnected) {
            pedido.fuente = zona;
        }
        espera = setTimeout(() => enCurso === pedido && mostrarCarga(pedido), UMBRAL);
        htmx.ajax("GET", url, { source: pedido.fuente, target: pedido.objetivo, swap: `innerHTML swap:${sinMovimiento.matches ? 0 : 140}ms` }).catch(() => {});
    };
    if (alcance === "pagina") {
        traerALaVista(pedido.objetivo, true).then(emitir);
    } else {
        emitir();
    }
};

const esDelListado = (url) => url.origin === location.origin && url.pathname === location.pathname && "htmx" in window;

document.addEventListener(
    "click",
    (evento) => {
        const enlace = evento.target.closest?.("a[href]");
        if (!enlace || !zonaListado() || !enlace.closest(contextoListado) || enlace.getAttribute("href").startsWith("#")) {
            return;
        }
        if (evento.defaultPrevented || evento.button !== 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) {
            return;
        }
        const url = new URL(enlace.href);
        if (enlace.target || enlace.hasAttribute("download") || !esDelListado(url)) {
            return;
        }
        evento.preventDefault();
        listar(url.href, enlace.closest("#pie-listado") ? "pagina" : "listado", enlace);
    },
    true,
);

document.addEventListener(
    "submit",
    (evento) => {
        const formulario = evento.target;
        if (evento.defaultPrevented || !zonaListado() || formulario.method !== "get" || formulario.target || !formulario.closest(contextoListado)) {
            return;
        }
        const url = new URL(formulario.action);
        if (!esDelListado(url)) {
            return;
        }
        evento.preventDefault();
        url.search = new URLSearchParams(new FormData(formulario)).toString();
        listar(url.href, "listado", evento.submitter || zonaListado());
    },
    true,
);

window.addEventListener("popstate", (evento) => {
    if (evento.state?.listado && zonaListado()) {
        listar(location.href, "listado", zonaListado(), false);
    }
});

document.addEventListener("htmx:beforeRequest", (evento) => {
    if (enCurso && !enCurso.xhr && evento.detail.elt === enCurso.fuente) {
        enCurso.xhr = evento.detail.xhr;
    }
});

document.addEventListener("htmx:beforeSwap", (evento) => {
    const pedido = enCurso;
    const propio = evento.detail.target === zonaListado() || evento.detail.target?.id === "resultados-listado";
    if (!pedido || evento.detail.xhr !== pedido.xhr) {
        if (propio) {
            evento.detail.shouldSwap = false;
        }
        return;
    }
    const final = new URL(evento.detail.xhr.responseURL || pedido.url);
    if (evento.detail.isError || !esDelListado(final) || /<html/i.test(evento.detail.serverResponse.slice(0, 300))) {
        evento.detail.shouldSwap = false;
        enCurso = null;
        quitarCarga();
        location.assign(evento.detail.isError ? pedido.url : final.href);
        return;
    }
    pedido.final = final.href;
    pedido.pie = controlesPie().map(aspecto);
});

document.addEventListener("htmx:afterSwap", (evento) => {
    const pedido = enCurso;
    if (!pedido || evento.detail.xhr !== pedido.xhr || evento.target !== pedido.objetivo || pedido.alcance !== "pagina" || sinMovimiento.matches) {
        return;
    }
    const controles = controlesPie();
    if (controles.length !== pedido.pie.length) {
        return;
    }
    controles.forEach((control, indice) => {
        const desde = pedido.pie[indice];
        const hasta = aspecto(control);
        if (!ASPECTO.every((propiedad) => desde[propiedad] === hasta[propiedad])) {
            control.animate([{ ...desde, offset: 0 }], { duration: 220, easing: "cubic-bezier(0, 0, 0.2, 1)" });
        }
    });
});

document.addEventListener("htmx:sendError", (evento) => {
    if (enCurso && evento.detail.xhr === enCurso.xhr) {
        quitarCarga();
        location.assign(enCurso.url);
    }
});

document.addEventListener("htmx:afterSettle", (evento) => {
    const pedido = enCurso;
    if (!pedido || evento.detail.xhr !== pedido.xhr || evento.target !== pedido.objetivo) {
        return;
    }
    enCurso = null;
    quitarCarga();
    if (pedido.empujar && pedido.final !== location.href) {
        history.pushState({ listado: true }, "", pedido.final);
    }
    conservarFiltros();
    ultimaCasilla = null;
    contarSeleccion();
    medirAlto(document.querySelector(".barra-acciones"), "--alto-barra");

    const activo = document.activeElement;
    const perdido = !activo || activo === document.body || !activo.isConnected;
    if (pedido.alcance === "pagina") {
        enfocar(destinoDelFoco());
    } else if (perdido && pedido.focoId && document.getElementById(pedido.focoId)) {
        enfocar(document.getElementById(pedido.focoId));
    } else if (perdido && pedido.focoPanel >= 0) {
        const opciones = enfocables(document.getElementById("changelist-filter"));
        enfocar(opciones[Math.min(pedido.focoPanel, opciones.length - 1)] || destinoDelFoco());
    } else if (perdido && pedido.empujar) {
        enfocar(destinoDelFoco());
    }
    anunciarListado(textoDelConteo());
});

const delBuscador = (evento) => evento.detail.elt?.closest?.('[x-data="searchCommand()"]');

const avisarEnBuscador = (texto, ingreso) => {
    const buscador = document.querySelector('[x-data="searchCommand()"]');
    const resultados = document.getElementById("command-results");
    if (!buscador || !resultados) {
        return;
    }
    Object.assign(Alpine.$data(buscador), { hasResponse: false, totalItems: 0, currentIndex: 0 });
    const aviso = document.createElement("p");
    aviso.className = "px-4 py-4 text-sm";
    aviso.textContent = texto;
    if (ingreso) {
        const enlace = document.createElement("a");
        enlace.href = ingreso;
        enlace.className = "enlace";
        enlace.textContent = "Ingresar de nuevo";
        aviso.append(" ", enlace);
    }
    resultados.replaceChildren(aviso);
    const nota = document.getElementById("command-results-note");
    if (nota) {
        nota.textContent = texto;
    }
};

document.addEventListener("htmx:beforeSwap", (evento) => {
    if (!delBuscador(evento)) {
        return;
    }
    const final = new URL(evento.detail.xhr.responseURL || location.href);
    const busqueda = new URL(document.getElementById("search-input-command")?.getAttribute("hx-get") || "", location.href);
    if (evento.detail.isError) {
        avisarEnBuscador("No se pudo buscar. Inténtalo de nuevo en un momento.");
    } else if (final.pathname !== busqueda.pathname) {
        final.searchParams.set("next", location.pathname + location.search);
        evento.detail.shouldSwap = false;
        avisarEnBuscador("Tu sesión terminó.", final.pathname + final.search);
    }
});

document.addEventListener("htmx:sendError", (evento) => {
    if (delBuscador(evento)) {
        avisarEnBuscador("No se pudo buscar. Revisa la conexión e inténtalo de nuevo.");
    }
});
})();
