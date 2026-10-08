import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";

const carpeta = execFileSync("python3", ["-c", "import os, unfold; print(os.path.dirname(unfold.__file__))"], { encoding: "utf8" }).trim();
const fuente = readFileSync(`${carpeta}/styles.css`, "utf8")
    .split("\n")
    .filter((linea) => !/^@import ['"]tailwindcss['"];/.test(linea) && !/^@plugin /.test(linea))
    .join("\n");
const contenido = `@source "${carpeta}/templates";\n@source "${carpeta}/**/*.py";\n${fuente}`;
const destino = "scss/unfold.css";

if (!existsSync(destino) || readFileSync(destino, "utf8") !== contenido) {
    writeFileSync(destino, contenido);
}
