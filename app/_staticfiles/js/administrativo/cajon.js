(() => {
const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)");
const arrastreCajon = { activo: null };

const estadoRaiz = () => {
    try {
        return Alpine.$data(document.documentElement);
    } catch {
        return null;
    }
};

const soltarCajon = (lateral, velo) => {
    [lateral, velo].forEach((elemento) => elemento.style.removeProperty("transition"));
    lateral.style.removeProperty("translate");
    velo.style.removeProperty("opacity");
};

document.addEventListener(
    "touchstart",
    (evento) => {
        const estado = estadoRaiz();
        const lateral = document.getElementById("nav-sidebar");
        const velo = document.querySelector(".velo-lateral");
        if (!estado?.esCajon || estado.sidebarOpen !== true || !lateral || !velo || evento.touches.length !== 1) {
            return;
        }
        if (!lateral.contains(evento.target) && evento.target !== velo) {
            return;
        }
        const toque = evento.touches[0];
        arrastreCajon.activo = { lateral, velo, x: toque.clientX, y: toque.clientY, dx: 0, rumbo: null, muestras: [[performance.now(), toque.clientX]] };
    },
    { passive: true },
);

document.addEventListener(
    "touchmove",
    (evento) => {
        const arrastre = arrastreCajon.activo;
        if (!arrastre || evento.touches.length !== 1) {
            return;
        }
        const toque = evento.touches[0];
        const dx = toque.clientX - arrastre.x;
        const dy = toque.clientY - arrastre.y;
        if (!arrastre.rumbo) {
            if (Math.hypot(dx, dy) < 10) {
                return;
            }
            arrastre.rumbo = Math.abs(dx) > Math.abs(dy) && dx < 0 ? "cerrar" : "otro";
            if (arrastre.rumbo === "cerrar") {
                [arrastre.lateral, arrastre.velo].forEach((elemento) => (elemento.style.transition = "none"));
            }
        }
        if (arrastre.rumbo !== "cerrar") {
            return;
        }
        const ancho = arrastre.lateral.offsetWidth;
        arrastre.dx = Math.max(-ancho, Math.min(0, dx));
        arrastre.lateral.style.translate = `${arrastre.dx}px 0`;
        arrastre.velo.style.opacity = String(1 + arrastre.dx / ancho);
        arrastre.muestras = [...arrastre.muestras, [performance.now(), toque.clientX]].slice(-5);
    },
    { passive: true },
);

const terminarArrastre = (evento) => {
    const arrastre = arrastreCajon.activo;
    arrastreCajon.activo = null;
    if (!arrastre || arrastre.rumbo !== "cerrar") {
        return;
    }
    const { lateral, velo } = arrastre;
    const ancho = lateral.offsetWidth;
    const [[t0, x0], [t1, x1]] = [arrastre.muestras[0], arrastre.muestras.at(-1)];
    const velocidad = t1 > t0 ? (x1 - x0) / (t1 - t0) : 0;
    const cierra = evento.type === "touchend" && (-arrastre.dx > ancho * 0.4 || velocidad < -0.3);
    const salida = cierra ? "--duracion-capa-salida" : "--duracion-capa-entrada";
    const curva = cierra ? "--ease-enfatizada-salida" : "--ease-enfatizada-entrada";
    const duracion = sinMovimiento.matches ? "0s" : `var(${salida})`;
    lateral.style.transition = `translate ${duracion} var(${curva})`;
    velo.style.transition = `opacity ${duracion} var(${curva})`;
    lateral.style.translate = cierra ? "-100% 0" : "0 0";
    velo.style.opacity = cierra ? "0" : "1";
    if (cierra) {
        estadoRaiz()?.cerrarCajon();
    }
    setTimeout(() => soltarCajon(lateral, velo), sinMovimiento.matches ? 0 : 320);
};

document.addEventListener("touchend", terminarArrastre, { passive: true });
document.addEventListener("touchcancel", terminarArrastre, { passive: true });
})();
