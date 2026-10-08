{% load interfaz %}(() => {
const raiz = document.documentElement;
const imitar = !("onpagereveal" in window) && !matchMedia("(prefers-reduced-motion: reduce)").matches;
const urlSiluetas = "{% url_siluetas %}";
const raizAdmin = "{% url 'admin:index' %}";
let esperas = [];
let moldes = null;
let ultimoCuadro = 0;
let focoAnterior = null;

const sesion = (operar) => {
    try {
        return operar(sessionStorage);
    } catch {
        return null;
    }
};

if (imitar) {
    if (sesion((almacen) => almacen.getItem("transicion-vistas"))) {
        sesion((almacen) => almacen.removeItem("transicion-vistas"));
        raiz.classList.add("vista-entrante");
    }
    document.addEventListener("animationend", (evento) => {
        if (evento.target.id === "contenido") {
            raiz.classList.remove("vista-entrante");
        }
    });
}

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
    if (!ruta.startsWith(raizAdmin)) {
        return "";
    }
    const partes = ruta.slice(raizAdmin.length).split("/").filter(Boolean);
    if (!partes.length) {
        return "inicio";
    }
    if (partes.length === 2) {
        return "listado";
    }
    if ((partes.length === 3 && partes[2] === "add") || (partes.length === 4 && partes[3] === "change")) {
        return "ficha";
    }
    return "";
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
    if (imitar) {
        sesion((almacen) => almacen.setItem("transicion-vistas", "1"));
        raiz.classList.add("vista-saliente");
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

const nombrar = (transicion) => {
    if (!transicion) {
        return;
    }
    raiz.classList.add("en-transicion");
    transicion.finished.finally(() => raiz.classList.remove("en-transicion"));
};

window.addEventListener("pageswap", (evento) => nombrar(evento.viewTransition));
window.addEventListener("pagereveal", (evento) => nombrar(evento.viewTransition));

window.addEventListener("pagehide", () => {
    esperas.forEach(clearTimeout);
});
window.addEventListener("pageshow", (evento) => {
    soltar();
    raiz.classList.remove("en-transicion");
    if (evento.persisted) {
        sesion((almacen) => almacen.removeItem("transicion-vistas"));
    }
});

if (window.navigation) {
    navigation.addEventListener("navigateerror", soltar);
}
window.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && esperas.length) {
        soltar();
    }
});
})();
