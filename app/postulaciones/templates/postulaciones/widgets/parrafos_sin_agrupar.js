(() => {
const parrafo = window.Trix?.config.blockAttributes.p;
if (parrafo) {
    parrafo.group = false;
}
})();
