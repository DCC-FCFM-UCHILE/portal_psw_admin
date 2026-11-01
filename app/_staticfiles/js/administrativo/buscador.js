(() => {
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
