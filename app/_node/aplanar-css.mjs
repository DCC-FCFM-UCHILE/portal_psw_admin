import { transform } from "lightningcss";
import { readFileSync, writeFileSync } from "node:fs";

const ruta = process.argv[2];
if (!ruta) {
    console.error("uso: node aplanar-css.mjs <archivo.css> [--minify]");
    process.exit(1);
}

const minificar = process.argv.includes("--minify");
const codigo = readFileSync(ruta);

const resultado = transform({
    filename: ruta,
    code: codigo,
    targets: { safari: 15 << 16 },
    minify: minificar,
});

if (resultado.warnings.length) {
    for (const w of resultado.warnings) console.error("lightningcss:", w.message);
    process.exit(1);
}

writeFileSync(ruta, resultado.code);
