// Servidor de revision del estudio: sirve el borrador al iPad y recibe las correcciones
// dibujadas con el Apple Pencil. Node puro, sin dependencias.
//   GET  /            la interfaz de revision
//   GET  /borrador.mp4  el ultimo borrador (con Range: Safari lo exige para hacer seek)
//   GET  /notas       las correcciones ya enviadas
//   POST /notas       guarda una correccion (json + png del cuadro anotado)
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const TOPE_BYTES = 12 * 1024 * 1024; // un PNG de cuadro completo pesa < 1 MB; 12 es techo de sobra

const ipLocal = () =>
  Object.values(os.networkInterfaces())
    .flat()
    .find((i) => i && i.family === "IPv4" && !i.internal)?.address ?? "localhost";

const json = (res, code, dato) => {
  res.writeHead(code, { "content-type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(dato));
};

/** Video por partes. Sin esto Safari en iOS reproduce pero no deja mover el tiempo. */
const servirVideo = (req, res, archivo) => {
  const { size } = fs.statSync(archivo);
  const rango = /bytes=(\d*)-(\d*)/.exec(req.headers.range ?? "");
  if (!rango) {
    res.writeHead(200, { "content-type": "video/mp4", "content-length": size, "accept-ranges": "bytes" });
    return fs.createReadStream(archivo).pipe(res);
  }
  const desde = rango[1] ? Number(rango[1]) : 0;
  const hasta = rango[2] ? Math.min(Number(rango[2]), size - 1) : size - 1;
  if (desde >= size || hasta < desde) {
    res.writeHead(416, { "content-range": `bytes */${size}` });
    return res.end();
  }
  res.writeHead(206, {
    "content-type": "video/mp4",
    "content-range": `bytes ${desde}-${hasta}/${size}`,
    "content-length": hasta - desde + 1,
    "accept-ranges": "bytes",
  });
  fs.createReadStream(archivo, { start: desde, end: hasta }).pipe(res);
};

const leerCuerpo = (req) =>
  new Promise((ok, falla) => {
    let bytes = 0;
    const partes = [];
    req.on("data", (ch) => {
      bytes += ch.length;
      if (bytes > TOPE_BYTES) { falla(new Error("cuerpo demasiado grande")); req.destroy(); return; }
      partes.push(ch);
    });
    req.on("end", () => ok(Buffer.concat(partes).toString("utf8")));
    req.on("error", falla);
  });

/**
 * Levanta la revision para el proyecto en `proyecto`. Devuelve el server ya escuchando.
 * `puerto: 0` deja que el sistema elija uno libre (lo usa el self-check).
 */
export const servir = ({ proyecto = process.cwd(), puerto = 7777, callado = false } = {}) => {
  const borrador = path.join(proyecto, "cache", "borrador.mp4");
  const carpeta = path.join(proyecto, "revision");
  const indice = path.join(carpeta, "notas.json");
  const html = path.join(import.meta.dirname, "revision.html");

  const leerNotas = () => (fs.existsSync(indice) ? JSON.parse(fs.readFileSync(indice, "utf8")) : []);

  const server = http.createServer(async (req, res) => {
    const ruta = new URL(req.url, "http://x").pathname;
    try {
      if (req.method === "GET" && (ruta === "/" || ruta === "/index.html")) {
        // no-store: si Safari cachea la pagina, un rediseno no llega al iPad hasta
        // que JD vacia el cache a mano, y parece que el cambio no se hizo.
        res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
        return res.end(fs.readFileSync(html));
      }
      if (req.method === "GET" && ruta === "/borrador.mp4") {
        if (!fs.existsSync(borrador)) return json(res, 404, { error: "no hay borrador" });
        return servirVideo(req, res, borrador);
      }
      if (req.method === "GET" && ruta === "/notas") return json(res, 200, leerNotas());

      // Las tomas de la linea de tiempo salen de props.json, que el render ya dejo
      // calculado con ffprobe: aca no se vuelve a medir nada.
      if (req.method === "GET" && ruta === "/tomas") {
        const props = path.join(proyecto, "cache", "props.json");
        if (!fs.existsSync(props)) return json(res, 200, { proyecto: path.basename(proyecto), tomas: [] });
        const { clips } = JSON.parse(fs.readFileSync(props, "utf8"));
        return json(res, 200, {
          proyecto: path.basename(proyecto),
          tomas: (clips ?? []).map((c) => c.duracion_s),
        });
      }

      if (req.method === "POST" && ruta === "/notas") {
        const nota = JSON.parse(await leerCuerpo(req));
        if (typeof nota.t_s !== "number" || !Number.isFinite(nota.t_s)) {
          return json(res, 400, { error: "falta t_s" });
        }
        fs.mkdirSync(carpeta, { recursive: true });
        const notas = leerNotas();
        const n = notas.length + 1;
        let imagen = null;
        const b64 = /^data:image\/png;base64,(.+)$/s.exec(nota.png ?? "");
        if (b64) {
          imagen = `nota-${String(n).padStart(2, "0")}.png`;
          fs.writeFileSync(path.join(carpeta, imagen), Buffer.from(b64[1], "base64"));
        }
        const { png, ...resto } = nota;
        notas.push({ n, ...resto, imagen, creada: new Date().toISOString(), aplicada: false });
        fs.writeFileSync(indice, JSON.stringify(notas, null, 2));
        if (!callado) console.log(`  + nota ${n} en ${nota.t_s}s${nota.texto ? `: ${nota.texto}` : ""}`);
        return json(res, 201, { n, imagen });
      }
      json(res, 404, { error: "no existe" });
    } catch (e) {
      json(res, 500, { error: e.message });
    }
  });

  return new Promise((ok) => {
    server.listen(puerto, () => {
      if (!callado) {
        const url = `http://${ipLocal()}:${server.address().port}`;
        console.log(`\n  Revisión de "${path.basename(proyecto)}" abierta.\n`);
        console.log(`  Abre esto en el iPad (misma WiFi):  ${url}\n`);
        console.log(`  Las correcciones caen en ${path.relative(proyecto, carpeta) || "revision"}/notas.json`);
        console.log("  Ctrl+C para cerrar.\n");
      }
      ok(server);
    });
  });
};
