(() => {
const raiz = document.documentElement;
const imitar = !("onpagereveal" in window) && !matchMedia("(prefers-reduced-motion: reduce)").matches;
let esperas = [];

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

const soltar = () => {
    esperas.forEach(clearTimeout);
    esperas = [];
    raiz.classList.remove("vista-saliente");
    if (document.body) {
        document.body.classList.remove("navegando");
    }
};

const salir = () => {
    if (imitar) {
        sesion((almacen) => almacen.setItem("transicion-vistas", "1"));
        raiz.classList.add("vista-saliente");
    }
};

document.addEventListener("click", (evento) => {
    const enlace = evento.target.closest && evento.target.closest("a[href]");
    if (!enlace || enlace.getAttribute("href").startsWith("#") || !navegaAOtraVista(evento, enlace)) {
        return;
    }
    soltar();
    esperas.push(setTimeout(barra, 300));
    salir();
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
