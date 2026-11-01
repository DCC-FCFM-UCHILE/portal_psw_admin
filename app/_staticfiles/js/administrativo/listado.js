(() => {
const UMBRAL = 400;
const ASPECTO = ["opacity", "color", "borderColor", "backgroundColor"];
const contextoListado = "#listado, #pie-listado, #changelist-filter, #conteo-cabecera";
const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)");
let enCurso = null;
let espera = null;

const zonaListado = () => document.querySelector("#listado[data-nombre]");
administrativo.zonaListado = zonaListado;

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

const nuevoPedido = (url, alcance, fuente, empujar, valores) => {
    const activo = document.activeElement;
    const panel = document.getElementById("changelist-filter");
    return {
        url,
        respaldo: valores ? location.href : url,
        metodo: valores ? "POST" : "GET",
        alcance,
        empujar,
        fuente,
        objetivo: alcance === "pagina" ? document.getElementById("resultados-listado") : zonaListado(),
        focoId: activo?.id || "",
        focoPanel: panel?.contains(activo) ? enfocables(panel).indexOf(activo) : -1,
    };
};

const listar = (url, alcance, fuente, empujar = true, valores = null) => {
    const zona = zonaListado();
    const pedido = nuevoPedido(url, alcance, fuente, empujar, valores);
    if (document.getElementById("changelist-filter")?.contains(fuente) && cerrarFiltros()) {
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
        const opciones = { source: pedido.fuente, target: pedido.objetivo, swap: `innerHTML swap:${sinMovimiento.matches ? 0 : 140}ms` };
        if (valores) {
            opciones.values = valores;
        }
        htmx.ajax(pedido.metodo, url, opciones).catch(() => {});
    };
    if (alcance === "pagina") {
        traerALaVista(pedido.objetivo, true).then(emitir);
    } else {
        emitir();
    }
};

const esDelListado = (url) => url.origin === location.origin && url.pathname === location.pathname && "htmx" in window;

const enlaceDelListado = (enlace) =>
    enlace && zonaListado() && enlace.closest(contextoListado) && administrativo.enlaceComun(enlace) && esDelListado(new URL(enlace.href));

const envioEnListado = (evento) =>
    !evento.defaultPrevented && evento.target.id === "changelist-form" && evento.submitter?.hasAttribute("data-en-listado") && zonaListado() && "htmx" in window;

const cerrarMenuDe = (boton) => {
    const menu = boton.closest("nav[id]");
    const disparador = menu && document.querySelector(`[aria-controls="${menu.id}"]`);
    if (disparador) {
        Alpine.$data(disparador).cerrar();
    }
};

const respuestaDelListado = (detalle, final) => !detalle.isError && esDelListado(final) && !/<html/i.test(detalle.serverResponse.slice(0, 300));

const focoTrasListar = (pedido) => {
    const activo = document.activeElement;
    const perdido = !activo || activo === document.body || !activo.isConnected;
    if (pedido.alcance === "pagina") {
        return destinoDelFoco();
    }
    if (!perdido) {
        return null;
    }
    if (pedido.focoId && document.getElementById(pedido.focoId)) {
        return document.getElementById(pedido.focoId);
    }
    if (pedido.focoPanel >= 0) {
        const opciones = enfocables(document.getElementById("changelist-filter"));
        return opciones[Math.min(pedido.focoPanel, opciones.length - 1)] || destinoDelFoco();
    }
    return pedido.empujar ? destinoDelFoco() : null;
};

document.addEventListener(
    "click",
    (evento) => {
        const enlace = evento.target.closest?.("a[href]");
        if (!administrativo.clicSimple(evento) || !enlaceDelListado(enlace)) {
            return;
        }
        evento.preventDefault();
        listar(new URL(enlace.href).href, enlace.closest("#pie-listado, .paginacion-superior") ? "pagina" : "listado", enlace);
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

document.addEventListener(
    "submit",
    (evento) => {
        if (!envioEnListado(evento)) {
            return;
        }
        evento.preventDefault();
        if (enCurso?.metodo === "POST") {
            return;
        }
        const boton = evento.submitter;
        cerrarMenuDe(boton);
        listar(boton.formAction || location.href, "listado", evento.target, false, boton.name ? { [boton.name]: boton.value } : {});
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
    if (!respuestaDelListado(evento.detail, final)) {
        evento.detail.shouldSwap = false;
        enCurso = null;
        quitarCarga();
        location.assign(evento.detail.isError ? pedido.respaldo : final.href);
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
        location.assign(enCurso.respaldo);
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
    administrativo.olvidarSeleccion();
    administrativo.medirAlto(document.querySelector(".barra-acciones"), "--alto-barra");

    if (pedido.metodo === "POST") {
        enfocar(document.getElementById("avisos") || destinoDelFoco());
        anunciarListado("");
        return;
    }
    const destino = focoTrasListar(pedido);
    if (destino) {
        enfocar(destino);
    }
    anunciarListado(textoDelConteo());
});
})();
