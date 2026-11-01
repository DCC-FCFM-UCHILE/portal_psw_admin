{% load interfaz %}(() => {
const raiz = document.documentElement;
const conMovimiento = !matchMedia("(prefers-reduced-motion: reduce)").matches;
const nativa = "onpagereveal" in window;
const urlSiluetas = "{% url_siluetas %}";
const raizAdmin = "{% url 'admin:index' %}";
const listados = {% rutas_listado %};
const anchoCajon = matchMedia("(max-width: 1280px)");
let esperas = [];
let moldes = null;
let ultimoCuadro = 0;
let focoAnterior = null;
let nombrados = [];

const sesion = (operar) => {
    try {
        return operar(sessionStorage);
    } catch {
        return null;
    }
};

const vieneDeOtraVista = () => {
    const marca = sesion((almacen) => almacen.getItem("transicion-vistas"));
    sesion((almacen) => almacen.removeItem("transicion-vistas"));
    return Boolean(marca) && conMovimiento;
};

const entrar = () => raiz.classList.add("vista-entrante");

if (!nativa && vieneDeOtraVista()) {
    entrar();
}
document.addEventListener("animationend", (evento) => {
    if (evento.target.id === "contenido") {
        raiz.classList.remove("vista-entrante");
    }
});

const cargarMoldes = (html) => {
    const plantilla = document.createElement("template");
    plantilla.innerHTML = html;
    moldes = plantilla.content;
};

const moldesGuardados = () => {
    if (!moldes && urlSiluetas) {
        const html = sesion((almacen) => almacen.getItem(urlSiluetas));
        if (html) {
            cargarMoldes(html);
        }
    }
    return moldes;
};

window.addEventListener("load", () => {
    if (!urlSiluetas || !document.getElementById("content") || moldesGuardados() || (navigator.connection && navigator.connection.saveData)) {
        return;
    }
    fetch(urlSiluetas, { priority: "low" })
        .then((respuesta) => (respuesta.ok && !respuesta.redirected ? respuesta.text() : ""))
        .then((html) => {
            if (!html) {
                return;
            }
            sesion((almacen) => {
                Object.keys(almacen)
                    .filter((clave) => clave.includes("/siluetas/"))
                    .forEach((clave) => almacen.removeItem(clave));
                almacen.setItem(urlSiluetas, html);
            });
            cargarMoldes(html);
        })
        .catch(() => {});
});

const formaDe = (ruta) => {
    if (ruta === raizAdmin) {
        return "inicio";
    }
    const listado = listados.find((base) => ruta.startsWith(base));
    if (!listado) {
        return "";
    }
    const partes = ruta.slice(listado.length).split("/").filter(Boolean);
    if (!partes.length) {
        return "listado";
    }
    return partes.length === 1 ? "ficha" : "";
};

const navegaAOtraVista = (evento, enlace) => {
    if (evento.defaultPrevented || evento.button !== 0 || evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) {
        return false;
    }
    if (enlace.target || enlace.hasAttribute("download") || enlace.origin !== location.origin || /\.[a-z0-9]+$/i.test(enlace.pathname)) {
        return false;
    }
    return enlace.pathname !== location.pathname || enlace.search !== location.search;
};

const barra = () => document.body.classList.add("navegando");

const anunciar = (texto) => {
    const estado = document.getElementById("estado-navegacion");
    if (estado) {
        estado.textContent = texto;
    }
};

const cajonAbierto = () => {
    try {
        const estado = window.Alpine && Alpine.$data(raiz);
        return estado && estado.esCajon && estado.sidebarOpen ? estado : null;
    } catch {
        return null;
    }
};

const despedirCajon = () => {
    const estado = cajonAbierto();
    const envoltura = document.querySelector(".envoltura-lateral");
    if (!estado || !envoltura) {
        return;
    }
    let listo = false;
    const cerrar = () => {
        if (listo) {
            return;
        }
        listo = true;
        estado.sidebarOpen = false;
        const llevarFoco = () => {
            const activo = document.activeElement;
            if (!activo || activo === document.body || envoltura.contains(activo)) {
                document.getElementById("contenido")?.focus({ preventScroll: true });
            }
        };
        Alpine.nextTick(llevarFoco);
        let cuadros = 0;
        const esperar = () => {
            llevarFoco();
            if (envoltura.checkVisibility() && cuadros++ < 30) {
                requestAnimationFrame(esperar);
            } else {
                raiz.classList.remove("cajon-saliente");
            }
        };
        requestAnimationFrame(esperar);
    };
    const yaFundido = raiz.classList.contains("vista-saliente") || !conMovimiento;
    raiz.classList.add("cajon-saliente");
    if (yaFundido) {
        cerrar();
    } else {
        envoltura.addEventListener("animationend", (evento) => evento.target === envoltura && cerrar());
        setTimeout(cerrar, 400);
    }
};

const marcarDestino = (destino) => {
    const enlaces = [...document.querySelectorAll("#nav-sidebar a.lateral-enlace, #ir-al-inicio")];
    const coincide = (enlace) => enlace.pathname === destino || (enlace.pathname !== raizAdmin && destino.startsWith(enlace.pathname));
    const largo = Math.max(0, ...enlaces.filter(coincide).map((enlace) => enlace.pathname.length));
    enlaces.filter((enlace) => coincide(enlace) && enlace.pathname.length === largo).forEach((enlace) => enlace.setAttribute("data-destino", ""));
};

const mostrarSilueta = (destino) => {
    const contenido = document.getElementById("content");
    const forma = formaDe(destino);
    const molde = forma && moldesGuardados() && moldes.querySelector(`[data-forma="${forma}"]`);
    if (!molde || !contenido) {
        return;
    }
    const silueta = molde.cloneNode(true);
    if (contenido.contains(document.activeElement)) {
        focoAnterior = document.activeElement;
        document.getElementById("contenido").focus({ preventScroll: true });
    }
    despedirCajon();
    marcarDestino(destino);
    raiz.classList.remove("vista-saliente");
    raiz.classList.add("cargando-vista");
    if (performance.now() - ultimoCuadro < 100) {
        silueta.classList.add("entrando");
    }
    contenido.prepend(silueta);
    document.getElementById("contenido").setAttribute("aria-busy", "true");
    window.scrollTo(0, 0);
    anunciar(`Cargando ${silueta.dataset.titulo}…`);
};

const quitarSilueta = () => {
    raiz.classList.remove("vista-saliente", "cargando-vista");
    document.querySelectorAll("[data-destino]").forEach((enlace) => enlace.removeAttribute("data-destino"));
    const silueta = document.querySelector("#content > .silueta-vista");
    if (silueta) {
        silueta.remove();
        document.getElementById("contenido").removeAttribute("aria-busy");
        anunciar("");
        if (focoAnterior?.isConnected && document.activeElement === document.getElementById("contenido")) {
            focoAnterior.focus({ preventScroll: true });
        }
    }
    focoAnterior = null;
};

const soltar = () => {
    esperas.forEach(clearTimeout);
    esperas = [];
    quitarSilueta();
    if (document.body) {
        document.body.classList.remove("navegando");
    }
};

const olvidarMarca = () => sesion((almacen) => almacen.removeItem("transicion-vistas"));

const cancelar = () => {
    olvidarMarca();
    soltar();
};

const contarCuadros = () => {
    ultimoCuadro = performance.now();
    if (esperas.length && !raiz.classList.contains("cargando-vista")) {
        requestAnimationFrame(contarCuadros);
    }
};

document.addEventListener("click", (evento) => {
    const enlace = evento.target.closest && evento.target.closest("a[href]");
    if (!enlace || enlace.getAttribute("href").startsWith("#") || !navegaAOtraVista(evento, enlace)) {
        return;
    }
    soltar();
    esperas.push(
        setTimeout(barra, 300),
        setTimeout(() => mostrarSilueta(enlace.pathname), 1000),
        setTimeout(quitarSilueta, 10000),
    );
    requestAnimationFrame(contarCuadros);
    if (conMovimiento) {
        sesion((almacen) => almacen.setItem("transicion-vistas", "1"));
        if (!nativa) {
            raiz.classList.add("vista-saliente");
        }
    }
});

document.addEventListener("submit", (evento) => {
    const formulario = evento.target;
    if (evento.defaultPrevented || formulario.target || formulario.hasAttribute("hx-get") || formulario.hasAttribute("hx-post")) {
        return;
    }
    soltar();
    esperas.push(setTimeout(barra, 300));
});

const nombrar = (elemento, nombre, clase) => {
    if (!elemento || !elemento.checkVisibility()) {
        return;
    }
    elemento.style.setProperty("view-transition-name", nombre);
    if (clase) {
        elemento.style.setProperty("view-transition-class", clase);
    }
    nombrados.push(elemento);
};

const olvidarNombres = () => {
    nombrados.forEach((elemento) => {
        elemento.style.removeProperty("view-transition-name");
        elemento.style.removeProperty("view-transition-class");
    });
    nombrados = [];
};

const capasAbiertas = () => {
    const capas = [...document.querySelectorAll(".velo-lateral, #modal-overlay, #modal-content, [x-data='searchCommand()'], [aria-modal='true']")];
    return [...new Set(capas.map((capa) => (capa.id === "modal-content" ? capa.closest(".fixed") : capa)))];
};

const nombrarVista = (fase) => {
    const lateral = document.getElementById("nav-sidebar");
    if (!anchoCajon.matches) {
        nombrar(lateral, "lateral");
    } else if (fase === "saliente") {
        nombrar(lateral, "cajon", "capa");
    }
    nombrar(document.getElementById("cabecera"), "cabecera");
    nombrar(document.getElementById("titulo-cabecera"), `titulo-${fase}`, "contenido");
    document.querySelectorAll("#cabecera .ml-auto > .flex-row").forEach((acciones, indice) => nombrar(acciones, `acciones-${fase}-${indice}`, "contenido"));
    if (fase === "saliente") {
        capasAbiertas().forEach((capa, indice) => nombrar(capa, `capa-${indice}`, "capa"));
        if (document.body.classList.contains("navegando")) {
            nombrar(document.getElementById("barra-progreso"), "barra");
        }
    }
};

const atender = (transicion) => {
    [transicion.ready, transicion.finished, transicion.updateCallbackDone].forEach((promesa) => promesa?.catch(() => {}));
};

window.addEventListener("pageswap", (evento) => {
    const transicion = evento.viewTransition;
    if (transicion) {
        atender(transicion);
        nombrarVista("saliente");
    }
});

window.addEventListener("pagereveal", (evento) => {
    const transicion = evento.viewTransition;
    const venia = vieneDeOtraVista();
    if (!transicion) {
        if (venia) {
            entrar();
        }
        return;
    }
    atender(transicion);
    nombrarVista("entrante");
    transicion.finished.then(olvidarNombres, olvidarNombres);
});

window.addEventListener("pagehide", () => {
    esperas.forEach(clearTimeout);
});
window.addEventListener("pageshow", (evento) => {
    soltar();
    if (evento.persisted) {
        olvidarMarca();
        olvidarNombres();
        raiz.classList.remove("cajon-saliente", "vista-entrante");
        const estado = cajonAbierto();
        if (estado) {
            raiz.classList.add("restaurada");
            estado.sidebarOpen = false;
            requestAnimationFrame(() => requestAnimationFrame(() => raiz.classList.remove("restaurada")));
        }
    }
});

if (window.navigation) {
    navigation.addEventListener("navigateerror", cancelar);
}
window.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && esperas.length) {
        cancelar();
    }
});
})();
