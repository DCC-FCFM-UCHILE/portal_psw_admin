(() => {
const raiz = document.documentElement;
const leer = (clave) => {
    try {
        return localStorage.getItem(clave);
    } catch {
        return null;
    }
};
const marcas = [];
raiz.removeAttribute("x-cloak");
if (!raiz.classList.contains("dark") && !raiz.classList.contains("light")) {
    let tema = "auto";
    try {
        tema = JSON.parse(leer("adminTheme")) || "auto";
    } catch {}
    const oscuro = tema === "dark" || (tema === "auto" && matchMedia("(prefers-color-scheme: dark)").matches);
    const clase = oscuro ? "dark" : tema === "light" ? "light" : "";
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
