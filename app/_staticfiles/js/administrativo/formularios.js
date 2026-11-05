(() => {
const marcarFormato = (evento) => {
    requestAnimationFrame(() => {
        evento.target.toolbarElement?.querySelectorAll("button[data-trix-attribute]").forEach((boton) => {
            boton.setAttribute("aria-pressed", boton.classList.contains("trix-active").toString());
        });
    });
};

document.addEventListener("trix-initialize", marcarFormato);
document.addEventListener("trix-selection-change", marcarFormato);

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
            dialogo.addEventListener("close", administrativo.bloquearDesplazamiento);
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
        administrativo.bloquearDesplazamiento();
    });

administrativo.confirmar = confirmar;

const preguntarSalida = () =>
    confirmar({ titulo: "Hay cambios sin guardar", texto: "Si sales de esta página, se pierden.", si: "Salir sin guardar", no: "Seguir editando" });

const mismaVista = (destino) => destino.pathname === location.pathname && destino.search === location.search;

document.addEventListener(
    "click",
    (evento) => {
        const enlace = evento.target.closest?.("a[href]");
        if (!enlace || !administrativo.clicSimple(evento) || !administrativo.enlaceComun(enlace) || enlace.matches(".related-widget-wrapper-link, [data-popup]")) {
            return;
        }
        if (mismaVista(new URL(enlace.href, location.href)) || !hayCambios()) {
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

const MAXIMO_EN_MB = 10;
const MAXIMO_ENVIO = MAXIMO_EN_MB * 1024 * 1024;
const bytes = new TextEncoder();

const pesoDelEnvio = (formulario) =>
    [...new FormData(formulario)].reduce((total, [nombre, valor]) => {
        const contenido = valor instanceof File ? valor.size + bytes.encode(valor.name).length : bytes.encode(valor).length;
        return total + 200 + bytes.encode(nombre).length + contenido;
    }, 0);

const megas = (peso) => {
    const exacto = peso / 1024 / 1024;
    const redondeado = Math.round(exacto * 10) / 10;
    const texto = redondeado > MAXIMO_EN_MB ? redondeado.toFixed(1) : (Math.ceil(exacto * 100) / 100).toFixed(2);
    return texto.replace(".", ",");
};

const marcarZona = (campo, rechazado) => {
    const zona = campo.closest(".zona-archivo");
    if (zona && window.Alpine) {
        Alpine.$data(zona).rechazado = rechazado;
    }
};

const quitarAvisoDePeso = (campo) => {
    document.getElementById(`${campo.id}_peso`)?.parentElement.remove();
    marcarZona(campo, false);
    const descripciones = (campo.getAttribute("aria-describedby") ?? "").split(" ").filter((id) => id && id !== `${campo.id}_peso`);
    campo.setAttribute("aria-describedby", descripciones.join(" "));
    if (campo.dataset.invalidoAntes !== undefined) {
        if (campo.dataset.invalidoAntes) {
            campo.setAttribute("aria-invalid", campo.dataset.invalidoAntes);
        } else {
            campo.removeAttribute("aria-invalid");
        }
        delete campo.dataset.invalidoAntes;
    }
};

const avisarPeso = (campo, texto, anunciar) => {
    const marco = document.createElement("div");
    marco.className = "mt-2 text-xs text-rojo dark:text-oscuro-acento";
    if (anunciar) {
        marco.setAttribute("role", "alert");
    }
    const lista = document.createElement("ul");
    lista.className = "errorlist";
    lista.id = `${campo.id}_peso`;
    const item = document.createElement("li");
    item.innerHTML = '<span class="material-symbols-outlined mr-1 select-none align-bottom text-[18px] leading-none" aria-hidden="true">warning</span>';
    item.append(texto);
    lista.append(item);
    marco.append(lista);
    (campo.closest(".zona-archivo") ?? campo).after(marco);
    marcarZona(campo, true);
    campo.dataset.invalidoAntes = campo.getAttribute("aria-invalid") ?? "";
    campo.setAttribute("aria-invalid", "true");
    campo.setAttribute("aria-describedby", [lista.id, campo.getAttribute("aria-describedby")].filter(Boolean).join(" "));
};

const revisarPeso = (formulario, cambiado, anunciar) => {
    const campos = [...formulario.querySelectorAll('input[type="file"]')];
    campos.forEach(quitarAvisoDePeso);
    const total = pesoDelEnvio(formulario);
    if (total <= MAXIMO_ENVIO) {
        return null;
    }
    const peso = (campo) => [...campo.files].reduce((suma, archivo) => suma + archivo.size, 0);
    const campo = campos.find((otro) => peso(otro) > MAXIMO_ENVIO) ?? cambiado ?? campos.reduce((mayor, otro) => (peso(otro) > peso(mayor) ? otro : mayor));
    const texto =
        peso(campo) > MAXIMO_ENVIO
            ? `El archivo pesa ${megas(peso(campo))} MB y el máximo por envío son ${MAXIMO_EN_MB} MB. Elige uno más liviano.`
            : `Los archivos de este formulario suman ${megas(total)} MB y el máximo por envío son ${MAXIMO_EN_MB} MB. Elige uno más liviano.`;
    avisarPeso(campo, texto, anunciar);
    return campo;
};

document.addEventListener("change", (evento) => {
    const campo = evento.target;
    if (campo.type === "file" && campo.form?.method === "post") {
        revisarPeso(campo.form, campo.files.length ? campo : null, true);
    }
});

document.addEventListener(
    "submit",
    (evento) => {
        const formulario = evento.target;
        if (formulario.method !== "post" || formulario.target || !formulario.querySelector('input[type="file"]')) {
            return;
        }
        const campo = revisarPeso(formulario, null, false);
        if (campo) {
            evento.preventDefault();
            evento.stopImmediatePropagation();
            campo.focus({ focusVisible: true });
            campo.closest(".zona-archivo")?.scrollIntoView({ block: "center" });
        }
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
    formulario.querySelectorAll(".campo-contrasena").forEach((marco) => {
        mostrarContrasena(marco.querySelector("input"), marco.querySelector("button"), false);
    });
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
        if (caja.height && (caja.top < techo - 4 || caja.bottom > innerHeight + 4)) {
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
    const contenido = document.getElementById("content") ?? document.getElementById("contenido");
    if (!contenido || document.getElementById("login-form")) {
        return;
    }
    const campo = [...contenido.querySelectorAll('[aria-invalid="true"]')].find((elemento) => elemento.type !== "hidden" && elemento.checkVisibility());
    const general = contenido.querySelector("div.errornote");
    if (campo) {
        campo.focus();
        document.getElementById(`${campo.id}_error`)?.scrollIntoView({ block: "nearest" });
    } else if (general) {
        general.setAttribute("tabindex", "-1");
        general.focus();
    }
});

document.addEventListener("formset:removed", (evento) => {
    document.getElementById(`${evento.detail.formsetName}-group`)?.querySelector(".add-row")?.focus();
});

if (!CSS.supports("field-sizing", "content")) {
    const ajustarAlto = (area) => {
        const bordes = area.offsetHeight - area.clientHeight;
        const marco = area.parentElement;
        marco.style.minHeight = `${marco.offsetHeight}px`;
        area.style.height = "0";
        area.style.height = `${area.scrollHeight + bordes}px`;
        marco.style.minHeight = "";
    };
    const ajustarTodas = () => document.querySelectorAll("#content textarea").forEach(ajustarAlto);
    document.addEventListener("input", (evento) => {
        if (evento.target.matches?.("#content textarea")) {
            ajustarAlto(evento.target);
        }
    });
    document.addEventListener("DOMContentLoaded", () => {
        ajustarTodas();
        document.fonts?.ready.then(ajustarTodas);
    });
    addEventListener("resize", () => requestAnimationFrame(ajustarTodas));
}

const estadoContrasena = document.createElement("p");
estadoContrasena.className = "sr-only";
estadoContrasena.setAttribute("aria-live", "polite");

const nombreDelCampo = (campo) => {
    const texto = campo.labels?.[0]?.textContent.replace("*", "").trim() || "contraseña";
    return texto.charAt(0).toLowerCase() + texto.slice(1);
};

const mostrarContrasena = (campo, boton, visible) => {
    campo.type = visible ? "text" : "password";
    boton.dataset.visible = visible;
    boton.setAttribute("aria-label", `${visible ? "Ocultar" : "Mostrar"} ${nombreDelCampo(campo)}`);
};

document.addEventListener("DOMContentLoaded", () => {
    const campos = document.querySelectorAll('input[type="password"]');
    if (!campos.length) {
        return;
    }
    document.body.append(estadoContrasena);
    campos.forEach((campo) => {
        campo.spellcheck = false;
        campo.setAttribute("autocapitalize", "none");
        const enIngreso = Boolean(campo.closest("#login-form"));
        const marco = document.createElement("div");
        marco.className = enIngreso ? "campo-contrasena campo-con-ojo" : "campo-contrasena";
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = enIngreso ? "boton-ojo" : "boton-campo";
        boton.setAttribute("aria-controls", campo.id);
        boton.innerHTML =
            '<span class="capas" aria-hidden="true"><span class="material-symbols-outlined md-18 si-oculta">visibility</span><span class="material-symbols-outlined md-18 si-visible">visibility_off</span></span>' +
            (enIngreso ? "" : '<span class="capas" aria-hidden="true"><span class="si-oculta">Mostrar</span><span class="si-visible">Ocultar</span></span>');
        campo.replaceWith(marco);
        marco.append(campo, boton);
        mostrarContrasena(campo, boton, false);
        boton.addEventListener("click", () => {
            const visible = campo.type === "password";
            mostrarContrasena(campo, boton, visible);
            const nombre = nombreDelCampo(campo);
            estadoContrasena.textContent = `${nombre.charAt(0).toUpperCase()}${nombre.slice(1)} ${visible ? "visible" : "oculta"}`;
        });
    });
});

const alternarClaves = (formulario) => {
    const opcion = formulario.querySelector('input[name="usable_password"]:checked');
    if (!opcion) {
        return;
    }
    const sinClave = opcion.value === "false";
    const filas = [...formulario.querySelectorAll(".field-password1, .field-password2")].map((campo) => campo.closest(".form-row"));
    filas.forEach((fila) => {
        fila.hidden = sinClave;
    });
    opcion.closest(".form-row")?.classList.toggle("last", sinClave);
};

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('input[name="usable_password"]').forEach((opcion) => opcion.form && alternarClaves(opcion.form));
});

document.addEventListener("change", (evento) => {
    if (evento.target.name === "usable_password" && evento.target.form) {
        alternarClaves(evento.target.form);
    }
});
})();
