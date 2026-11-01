(() => {
const raiz = document.documentElement;
const leer = (clave) => {
    try {
        return localStorage.getItem(clave);
    } catch {
        return null;
    }
};
const claseDelTema = () => {
    let tema = "auto";
    try {
        tema = JSON.parse(leer("adminTheme")) || "auto";
    } catch {}
    if (tema === "dark" || (tema === "auto" && matchMedia("(prefers-color-scheme: dark)").matches)) {
        return "dark";
    }
    return tema === "light" ? "light" : "";
};
const marcas = [];
raiz.removeAttribute("x-cloak");
if (!raiz.classList.contains("dark") && !raiz.classList.contains("light")) {
    const clase = claseDelTema();
    if (clase) {
        raiz.classList.add(clase);
        marcas.push(clase);
    }
}
raiz.dataset.arranque = innerWidth > 1280 && leer("sidebarOpen") !== "0" ? "lateral-abierta" : "lateral-cerrada";
raiz.style.setProperty("--ancho-lateral", `${Number(leer("sidebarWidth")) || 288}px`);
document.addEventListener("alpine:init", () => {
    raiz.classList.remove(...marcas);
    delete raiz.dataset.arranque;
});
})();
