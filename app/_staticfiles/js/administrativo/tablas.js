(() => {
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
})();
