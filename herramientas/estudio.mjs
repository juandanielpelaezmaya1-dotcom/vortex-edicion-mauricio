#!/usr/bin/env node
// Estudio de Video de Vortex — herramienta unica de VEGA.
// Se corre DESDE la carpeta del proyecto: node ../herramientas/estudio.mjs <comando>
//   probe                 inventario del material grabado
//   normalizar            manifest.json -> cache/ (cortes + specs comunes, cacheado)
//   subtitular            transcribe la voz ya cortada -> subtitulos/captions.json + .srt
//   render [--borrador [--hd]]  cache/ -> salida/  (borrador: solo 9x16 a media escala; --hd a escala completa)
//   revisar [--puerto N]  abre el borrador en el iPad para corregirlo con el Apple Pencil
//   test                  self-check e2e con material sintetico
import { execFileSync, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const RENDER = path.resolve(import.meta.dirname, "..", "_render");
// crf 16 + medium: el normalizado es una generacion mas de compresion antes del render; con
// crf 20 veryfast dejaba el material a la mitad del bitrate original y se notaba.
const SPECS = { fps: 30, ladoMayor: 1920, crf: 16, preset: "medium" };
const VIDEO = /\.(mp4|mov|m4v|avi|mkv|webm)$/i;

const morir = (msg) => {
  console.error(`\n  ${msg}\n`);
  process.exit(1);
};

const ffprobe = (archivo) => {
  const json = JSON.parse(
    execFileSync("ffprobe", [
      "-v", "error", "-print_format", "json",
      "-show_format", "-show_streams", archivo,
    ], { encoding: "utf8" }),
  );
  const v = json.streams.find((s) => s.codec_type === "video");
  if (!v) morir(`${archivo} no tiene pista de video.`);
  const [num, den] = (v.r_frame_rate ?? "0/1").split("/").map(Number);
  // Las camaras graban 3840x2160 y marcan rotacion +-90 en el display matrix: la imagen
  // real es vertical. ffmpeg la aplica solo al decodificar, asi que aca hay que hacer lo
  // mismo o la tabla reporta "horizontal" un material que es 9:16.
  const rot = Math.abs(Number(v.side_data_list?.find((s) => s.rotation != null)?.rotation ?? 0)) % 180;
  const girado = rot === 90;
  return {
    duracion_s: Number(json.format.duration),
    ancho: girado ? v.height : v.width,
    alto: girado ? v.width : v.height,
    fps: den ? Math.round((num / den) * 100) / 100 : 0,
    codec: v.codec_name,
    audio: json.streams.some((s) => s.codec_type === "audio"),
  };
};

const leerManifest = () => {
  const p = path.resolve("manifest.json");
  if (!fs.existsSync(p)) morir("No hay manifest.json aca. Corre el comando desde la carpeta del proyecto.");
  const m = JSON.parse(fs.readFileSync(p, "utf8"));
  if (!Array.isArray(m.clips) || m.clips.length === 0) morir("El manifest no tiene clips.");
  m.slug ??= path.basename(process.cwd());
  // `fps` en el manifest respeta el material (hay camaras que graban a 23,976): pasar a 30 duplica
  // un cuadro de cada cuatro y los paneos dan tirones.
  m.fps ??= SPECS.fps;
  return m;
};

// El nombre del cache depende de todo lo que cambia el resultado: si algo de esto
// cambia, el hash cambia y ffmpeg vuelve a correr. Si no, se reusa tal cual.
const rutaCache = (clip, i, fps, prefijo = "c", ext = "mp4", extra = "") => {
  const st = fs.statSync(clip.archivo);
  const h = createHash("sha1")
    .update([clip.archivo, clip.in_s ?? 0, clip.out_s ?? "", st.mtimeMs, st.size, JSON.stringify(SPECS), fps, clip.velocidad ?? 1, extra].join("|"))
    .digest("hex")
    .slice(0, 8);
  return path.join("cache", `${prefijo}${i + 1}-${h}.${ext}`);
};

// in/out validados contra la duracion real del archivo. Lo comparten tomas y pistas de voz.
const tramo = (x, n, que) => {
  if (!x.archivo) morir(`${que} ${n}: falta "archivo".`);
  if (!fs.existsSync(x.archivo)) morir(`${que} ${n}: no existe ${x.archivo}`);
  const info = ffprobe(x.archivo);
  const in_s = x.in_s ?? 0;
  const out_s = x.out_s ?? info.duracion_s;
  if (out_s <= in_s) morir(`${que} ${n}: out_s (${out_s}) tiene que ser mayor que in_s (${in_s}).`);
  if (out_s > info.duracion_s + 0.05) {
    morir(`${que} ${n}: out_s ${out_s}s se pasa de la duracion real (${info.duracion_s.toFixed(2)}s) de ${x.archivo}`);
  }
  return { info, in_s, out_s };
};

const planDeClips = (manifest) =>
  manifest.clips.map((clip, i) => {
    const { info, in_s, out_s } = tramo(clip, i + 1, "Clip");
    // `velocidad` cambia la duracion en la linea de tiempo: 0.5 es camara lenta (con material
    // a 60 fps salen cuadros reales, no repetidos), 2 va al doble.
    const v = clip.velocidad ?? 1;
    if (v < 0.25 || v > 4) morir(`Clip ${i + 1}: velocidad ${v} fuera de 0.25-4.`);
    return { ...clip, i, in_s, out_s, info, velocidad: v, duracion_s: (out_s - in_s) / v, cache: rutaCache(clip, i, manifest.fps) };
  });

// atempo solo acepta 0,5-100: una camara lenta a 0,4 va encadenada (0,5 x 0,8).
const atempo = (v) => {
  const f = [];
  while (v < 0.5) { f.push("atempo=0.5"); v /= 0.5; }
  return [...f, `atempo=${v}`].join(",");
};

// Pistas de voz: tramos de audio de cualquier archivo, colocados en un segundo de la linea de
// tiempo (`en_s`) sin depender de las tomas. Es lo que deja cantar a alguien sobre las tomas
// de apoyo. Se cortan, se limpian y se nivelan una vez y quedan en cache/ como las tomas.
// El nivel va en DOS pasadas (se mide y se aplica una ganancia fija): loudnorm de una pasada
// trabaja en modo dinamico y comprime el canto; con ganancia fija la dinamica queda como se grabo.
const FILTRO_VOZ = "highpass=f=80,afftdn=nr=12:nf=-50:tn=1";
const LUFS_VOZ = -16; // el nivel de un reel
const sonoridad = (args) => {
  const r = spawnSync("ffmpeg", ["-hide_banner", "-nostats", ...args, "-f", "null", "-"], { encoding: "utf8" });
  const m = [...r.stderr.matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop();
  return m ? Number(m[1]) : null;
};
const planDePistas = (manifest) =>
  (manifest.pistas ?? []).map((p, i) => {
    const { in_s, out_s } = tramo(p, i + 1, "Pista");
    if (p.en_s == null) morir(`Pista ${i + 1}: falta "en_s" (segundo de la linea de tiempo donde entra).`);
    // `limpiar: false` (musica, un aplauso) se salta la limpieza pero se nivela igual: una cancion
    // masterizada llega 10 dB por encima de una voz de campo y el salto entre las dos se nota.
    const filtro = p.limpiar === false ? "anull" : FILTRO_VOZ;
    const nivel = p.nivel_lufs ?? LUFS_VOZ;
    const fundido = [p.fundido_s ?? 0.06].flat();
    return { ...p, i, in_s, out_s, duracion_s: out_s - in_s, filtro, nivel, fundido,
      cache: rutaCache(p, i, 0, "p", "wav", [filtro, nivel, fundido, p.ganancia_db ?? ""].join("|")) };
  });

// Marcas del estilo editorial, compartidas por subtitulos y textos:
//   "*palabra*" serif italica grande · "**palabra**" ademas en el acento de la marca ·
//   "_palabra_" serif italica chica (un poco menor que la sans) · " / " parte la linea
const piezas = (texto) => {
  const lineas = [[]];
  let tipo = "sans";
  for (const tok of texto.split(/\s+/).filter(Boolean)) {
    if (tok === "/") { lineas.push([]); continue; }
    const abre = tok.startsWith("**") ? "oro" : tok.startsWith("*") ? "serif" : tok.startsWith("_") ? "chica" : null;
    if (abre) tipo = abre;
    lineas[lineas.length - 1].push({ texto: tok.replace(/^[*_]+|[*_]+$/g, ""), tipo });
    if (/[*_]$/.test(tok)) tipo = "sans";
  }
  return lineas;
};

// Sin whisper (texto de pantalla o una frase con `desde_s`): las palabras entran repartidas
// en `ventana` ms segun su largo, que es lo mas parecido a las silabas sin medirlas.
const repartir = (lineas, desde, ventana) => {
  const todas = lineas.flat();
  const total = todas.reduce((a, p) => a + p.texto.length + 1, 0);
  let acc = 0;
  for (const p of todas) {
    p.ms = Math.round(desde + (acc / total) * ventana);
    acc += p.texto.length + 1;
  }
  return lineas;
};

// Subtitulos "editorial": el editor escribe las frases en el manifest y aca se cuadran,
// palabra por palabra y en orden, con los tiempos de whisper. El texto que se ve es el
// de la frase (asi se corrige "Pazto" sin tocar captions.json); el tiempo, el de whisper.
// Las marcas (*grande*, **acento**, _chica_, " / ") son las de `piezas()`.
//   { "texto": "...", "palabras": 7 } cuando no calza palabra a palabra (una direccion):
//   cubre 7 palabras de whisper y la frase entra entera.
//   { "texto": "...", "y": 30 } altura del centro de la frase en % (por toma: que no tape
//   caras ni lo que protagoniza el plano). Sin ella, subtitulos.pos.y.
//   { "texto": "...", "desde_s": 12.4, "hasta_s": 15 } tiempo a mano, sin whisper: para
//   lo cantado, donde whisper estira y encoge las palabras. No consume palabras de whisper.
//   { "texto": "...", "hasta_s": 26.33 } tiempo de whisper, pero se cierra ahi (antes de un corte).
const armarPaginas = (captions, frases) => {
  // Whisper da sub-palabras: una palabra nueva empieza donde el token trae espacio delante.
  const palabras = captions.reduce((acc, c) => {
    const previa = acc[acc.length - 1];
    if (previa && !c.text.startsWith(" ")) {
      previa.text += c.text;
      previa.endMs = c.endMs;
    } else acc.push({ ...c });
    return acc;
  }, []);
  const norma = (s) => s.toLowerCase().normalize("NFD").replace(/[^a-z0-9]/g, "");
  let k = 0;
  const avisos = [];
  const paginas = frases.map((f, n) => {
    const { texto, palabras: cuantas, y, desde_s, hasta_s } = typeof f === "string" ? { texto: f } : f;
    // Zona segura de Instagram (plantilla de JD): nada por encima del 8 % ni por debajo del
    // 78,6 %; el centro de una frase de dos lineas necesita margen a los dos lados.
    if (y != null && (y < 14 || y > 74)) morir(`Frase ${n + 1} ("${texto}"): y=${y} sale de la zona segura (14-74).`);
    const lineas = piezas(texto);
    const extra = y != null ? { y } : {};
    if (desde_s != null) {
      const desde = desde_s * 1000;
      const span = hasta_s != null ? hasta_s * 1000 - desde : 2400;
      return { desde, fin: desde + span, ...(hasta_s != null ? { hasta: hasta_s * 1000 } : {}), lineas: repartir(lineas, desde, span * 0.7), ...extra };
    }
    const planas = lineas.flat();
    const suyas = palabras.slice(k, k + (cuantas ?? planas.length));
    if (!suyas.length) morir(`Frase ${n + 1} ("${texto}"): ya no quedan palabras de whisper.`);
    planas.forEach((p, j) => {
      const w = cuantas ? suyas[0] : suyas[j];
      if (!w) morir(`Frase ${n + 1} ("${texto}"): tiene mas palabras de las que quedan en whisper.`);
      if (!cuantas && norma(p.texto) !== norma(w.text)) avisos.push(`frase ${n + 1}: "${p.texto}" <- whisper "${w.text.trim()}"`);
      p.ms = Math.max(0, w.startMs - 60);
    });
    k += suyas.length;
    // `hasta_s` solo (sin `desde_s`): la frase toma el tiempo de whisper pero se cierra ahi, antes
    // de un corte. Sin el, la ultima frase se sostiene 0,9 s y puede meterse en la toma siguiente.
    return { desde: Math.max(0, suyas[0].startMs - 100), fin: suyas[suyas.length - 1].endMs,
      ...(hasta_s != null ? { hasta: hasta_s * 1000 } : {}), lineas, ...extra };
  });
  // Cada pagina dura hasta que empieza la siguiente; si hay un silencio largo, se va antes.
  paginas.forEach((p, i) => {
    const sig = paginas[i + 1];
    p.hasta ??= sig && sig.desde - p.fin < 700 ? sig.desde : p.fin + (sig ? 500 : 900);
    delete p.fin;
  });
  if (avisos.length) console.log(`\n  Texto distinto a whisper (revisar que sea a proposito):\n    ${avisos.join("\n    ")}`);
  if (k < palabras.length) {
    console.log(`\n  ${palabras.length - k} palabras de whisper sin frase (no salen): ${palabras.slice(k).map((w) => w.text.trim()).join(" ")}`);
  }
  return paginas;
};

const comandos = {
  probe() {
    const dir = "material";
    if (!fs.existsSync(dir)) morir("No existe material/ aca.");
    const archivos = fs.readdirSync(dir).filter((f) => VIDEO.test(f)).sort();
    if (archivos.length === 0) morir("material/ no tiene videos.");
    console.table(archivos.map((f) => {
      const i = ffprobe(path.join(dir, f));
      return {
        archivo: f,
        seg: i.duracion_s.toFixed(2),
        resolucion: `${i.ancho}x${i.alto}`,
        orientacion: i.alto > i.ancho ? "vertical" : "horizontal",
        fps: i.fps,
        codec: i.codec,
        audio: i.audio ? "si" : "no",
      };
    }));
  },

  normalizar() {
    const manifest = leerManifest();
    const plan = planDeClips(manifest);
    fs.mkdirSync("cache", { recursive: true });
    for (const c of plan) {
      if (fs.existsSync(c.cache)) {
        console.log(`  = clip ${c.i + 1}: cacheado (${path.basename(c.cache)})`);
        continue;
      }
      console.log(`  > clip ${c.i + 1}: ${c.archivo} [${c.in_s}s -> ${c.out_s}s]${c.velocidad !== 1 ? ` a ${c.velocidad}x` : ""}`);
      const lado = SPECS.ladoMayor;
      const escala =
        "scale='if(gt(iw,ih),trunc(min(" + lado + ",iw)/2)*2,-2)':" +
        "'if(gt(iw,ih),-2,trunc(min(" + lado + ",ih)/2)*2)'";
      // `-t` va del lado de la ENTRADA (mide el tramo original): con velocidad la salida dura
      // otra cosa y un -t de salida cortaria la camara lenta. setpts va antes de fps: asi la
      // lenta de un material a 60 fps usa sus cuadros reales.
      const v = c.velocidad;
      // El corte entra en un cuadro REAL del material: un in_s a medio cuadro (0,05 s a 30 fps)
      // hace que fps= empate y bote uno de cada tres cuadros, y la toma tiembla a 20 fps.
      const ss = c.info.fps ? Math.round(c.in_s * c.info.fps) / c.info.fps : c.in_s;
      execFileSync("ffmpeg", [
        "-y", "-hide_banner", "-loglevel", "error",
        "-ss", String(ss), "-t", String(c.out_s - c.in_s), "-i", c.archivo,
        "-vf", `${v !== 1 ? `setpts=PTS/${v},` : ""}${escala},fps=${manifest.fps}`,
        "-c:v", "libx264", "-preset", SPECS.preset, "-crf", String(SPECS.crf), "-pix_fmt", "yuv420p",
        ...(c.info.audio
          ? [...(v !== 1 ? ["-af", atempo(v)] : []), "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]
          : ["-an"]),
        c.cache,
      ], { stdio: "inherit" });
    }
    console.log(`\n  ${plan.length} clips listos en cache/.`);

    // Pistas de voz: corte + limpieza (graves, ruido de fondo) + nivel de redes (-16 LUFS) con
    // un limitador a -1,5 dBTP, y un fundido corto en los bordes para que el corte no haga clic.
    for (const p of planDePistas(manifest)) {
      if (fs.existsSync(p.cache)) {
        console.log(`  = pista ${p.i + 1}: cacheada (${path.basename(p.cache)})`);
        continue;
      }
      const entrada = ["-ss", String(p.in_s), "-t", String(p.duracion_s), "-i", p.archivo, "-vn"];
      // `ganancia_db` fija manda sobre la medicion: dos tramos de UNA cancion llevan la misma, o el
      // intro suave y el coro quedan igual de fuertes y el coro pierde su golpe.
      const medido = p.ganancia_db != null ? null : sonoridad([...entrada, "-af", `${p.filtro},ebur128`]);
      // Un tramo casi mudo mediria -70 y pediria +54 dB: la ganancia se acota.
      const ganancia = p.ganancia_db ?? (medido == null || medido < -60 ? 0 : Math.min(30, p.nivel - medido));
      console.log(`  > pista ${p.i + 1}: ${p.archivo} [${p.in_s}s -> ${p.out_s}s] en ${p.en_s}s (${medido != null ? `${medido} LUFS, ` : ""}${ganancia >= 0 ? "+" : ""}${ganancia.toFixed(1)} dB)`);
      // `fundido_s`: un numero para los dos bordes o [entrada, salida] (una musica que entra de
      // golpe en el coro y se va despacio al final).
      const [fe, fs_ = fe] = p.fundido;
      execFileSync("ffmpeg", [
        "-y", "-hide_banner", "-loglevel", "error", ...entrada,
        "-af", `${p.filtro},volume=${ganancia.toFixed(2)}dB,alimiter=limit=0.84:level=false,` +
          `afade=t=in:d=${fe},afade=t=out:st=${Math.max(0, p.duracion_s - fs_)}:d=${fs_}`,
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", p.cache,
      ], { stdio: "inherit" });
    }
  },

  render(args = []) {
    const borrador = args.includes("--borrador");
    const hd = args.includes("--hd"); // borrador a escala completa: para juzgar calidad, no solo montaje
    const manifest = leerManifest();
    const plan = planDeClips(manifest);
    const faltan = plan.filter((c) => !fs.existsSync(c.cache));
    if (faltan.length) morir(`Faltan ${faltan.length} clips en cache/. Corre primero: node ../herramientas/estudio.mjs normalizar`);

    if (manifest.musica?.archivo && !fs.existsSync(manifest.musica.archivo)) {
      morir(`No existe la musica: ${manifest.musica.archivo}`);
    }

    for (const e of manifest.efectos ?? []) {
      if (!fs.existsSync(e.archivo)) morir(`No existe el efecto: ${e.archivo}`);
    }

    const overlays = (manifest.overlays ?? []).map((o, i) => {
      if (!o.archivo) morir(`Overlay ${i + 1}: falta "archivo".`);
      if (!fs.existsSync(o.archivo)) morir(`No existe el overlay: ${o.archivo}`);
      // La duracion se mide del archivo: declararla a mano solo sirve para recortarlo.
      // Una imagen (el logo) no tiene duracion: la lleva el manifest.
      const imagen = /\.(png|svg|jpe?g|webp)$/i.test(o.archivo);
      if (imagen && o.duracion_s == null) morir(`Overlay ${i + 1}: una imagen necesita "duracion_s".`);
      const dur = o.duracion_s ?? ffprobe(o.archivo).duracion_s;
      return { ...o, src: o.archivo.replace(/\\/g, "/"), duracion_s: dur };
    });

    const pistas = planDePistas(manifest);
    const sinPista = pistas.filter((p) => !fs.existsSync(p.cache));
    if (sinPista.length) morir(`Faltan ${sinPista.length} pistas de voz en cache/. Corre primero: node ../herramientas/estudio.mjs normalizar`);

    const capPath = path.resolve("subtitulos", "captions.json");
    // Si todas las frases editoriales llevan su tiempo a mano, whisper no hace falta.
    const aMano = manifest.subtitulos?.estilo === "editorial" &&
      (manifest.subtitulos.frases ?? []).every((f) => typeof f === "object" && f.desde_s != null);
    const subsOn = manifest.subtitulos?.activo && (aMano || fs.existsSync(capPath));
    if (manifest.subtitulos?.activo && !subsOn) {
      morir("El manifest pide subtitulos pero no hay subtitulos/captions.json. Corre: node ../herramientas/estudio.mjs subtitular");
    }
    const captions = () => (fs.existsSync(capPath) ? JSON.parse(fs.readFileSync(capPath, "utf8")) : []);

    const props = {
      fps: manifest.fps,
      clips: plan.map((c) => ({
        src: c.cache.replace(/\\/g, "/"),
        duracion_s: c.duracion_s,
        ...(c.zoom ? { zoom: c.zoom } : {}),
        ...(c.transicion ? { transicion: c.transicion } : {}),
        ...(c.volumen != null ? { volumen: c.volumen } : {}),
      })),
      // `editorial` usa las marcas de los subtitulos; las palabras entran escalonadas.
      textos: (manifest.textos ?? []).map((t) =>
        t.estilo === "editorial"
          ? { ...t, lineas: repartir(piezas(t.texto), 0, Math.min(1400, t.texto.split(/\s+/).length * 130)) }
          : t),
      pistas: pistas.map((p) => ({ src: p.cache.replace(/\\/g, "/"), en_s: p.en_s, duracion_s: p.duracion_s, volumen: p.volumen ?? 1 })),
      velos: manifest.velos ?? [],
      desenfoques: manifest.desenfoques ?? [],
      ...(manifest.color ? { color: manifest.color } : {}),
      ...(manifest.acento ? { acento: manifest.acento } : {}),
      efectos: (manifest.efectos ?? []).map((e) => ({
        src: e.archivo.replace(/\\/g, "/"), en_s: e.en_s, volumen: e.volumen,
      })),
      elementos: manifest.elementos ?? [],
      destellos: manifest.destellos ?? [],
      overlays,
      progreso: manifest.progreso ?? false,
      ...(subsOn
        ? manifest.subtitulos.estilo === "editorial"
          ? { subtitulos: { paginas: armarPaginas(captions(), manifest.subtitulos.frases ?? []), pos: manifest.subtitulos.pos, sombra: manifest.subtitulos.sombra, marca: manifest.subtitulos.marca } }
          : { subtitulos: { captions: captions(), acento: manifest.subtitulos.acento, pos: manifest.subtitulos.pos } }
        : {}),
      ...(manifest.musica?.archivo
        ? { musica: { src: manifest.musica.archivo.replace(/\\/g, "/"), volumen: manifest.musica.volumen ?? 0.25 } }
        : {}),
    };
    fs.mkdirSync("cache", { recursive: true });
    const propsPath = path.resolve("cache", "props.json");
    fs.writeFileSync(propsPath, JSON.stringify(props, null, 2));

    const fecha = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const salidas = borrador
      ? [["Reel9x16", path.resolve("cache", "borrador.mp4")]]
      // `formatos: ["9x16"]` para un reel que no tiene version horizontal.
      : (manifest.formatos ?? ["9x16", "16x9"]).map((f) => [`Reel${f}`, path.resolve("salida", `${manifest.slug}_${f}_${fecha}.mp4`)]);
    if (!borrador) fs.mkdirSync("salida", { recursive: true });

    for (const [comp, out] of salidas) {
      console.log(`\n  > renderizando ${comp}${borrador ? " (borrador)" : ""}...`);
      remotion([
        "render", "src/index.ts", comp, out,
        `--props=${propsPath}`,
        `--public-dir=${process.cwd()}`,
        ...(borrador && !hd ? ["--scale=0.5"] : []),
      ]);
      console.log(`  ${out}`);
    }
  },

  // Transcribe la voz DE LOS CLIPS YA CORTADOS: asi los tiempos de cada palabra caen
  // sobre la linea de tiempo final, no sobre el material original.
  subtitular(args = []) {
    const i = args.indexOf("--modelo");
    const modelo = i !== -1 ? args[i + 1] : "small";
    const plan = planDeClips(leerManifest());
    const faltan = plan.filter((c) => !fs.existsSync(c.cache));
    if (faltan.length) morir(`Faltan ${faltan.length} clips en cache/. Corre primero: normalizar`);

    fs.mkdirSync("subtitulos", { recursive: true });
    const lista = path.resolve("cache", "audio-lista.txt");
    // Rutas ABSOLUTAS: el demuxer concat resuelve lo relativo contra la carpeta del
    // archivo de lista (cache/), no contra la del proyecto.
    fs.writeFileSync(lista, plan.map((c) => `file '${path.resolve(c.cache).replace(/'/g, "'\\''")}'`).join("\n"));
    const wav = path.resolve("cache", "voz-16k.wav");
    console.log("  > uniendo el audio de los clips cortados...");
    execFileSync("ffmpeg", [
      "-y", "-hide_banner", "-loglevel", "error",
      "-f", "concat", "-safe", "0", "-i", lista,
      "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav,
    ], { stdio: "inherit" });

    execFileSync(process.execPath, [
      path.join(RENDER, "herramientas", "transcribir.mjs"),
      "--wav", wav,
      "--json", path.resolve("subtitulos", "captions.json"),
      "--srt", path.resolve("subtitulos", "voz.es.srt"),
      "--modelo", modelo,
    ], { cwd: RENDER, stdio: "inherit" });

    console.log("\n  Revisa subtitulos/voz.es.srt contra el audio ANTES de renderizar.");
    console.log("  Si corriges texto ahi, corrige el MISMO texto en subtitulos/captions.json.");
  },

  // Levanta la revision para el iPad. El borrador tiene que existir: se corrige lo que
  // ya se puede ver, no un manifest en abstracto.
  async revisar(args = []) {
    if (!fs.existsSync(path.join("cache", "borrador.mp4"))) {
      morir("No hay cache/borrador.mp4. Corre primero: node ../herramientas/estudio.mjs render --borrador");
    }
    const i = args.indexOf("--puerto");
    const { servir } = await import(pathToFileURL(path.join(import.meta.dirname, "revisar.mjs")));
    await servir({ proyecto: process.cwd(), puerto: i !== -1 ? Number(args[i + 1]) : 7777 });
  },

  test() {
    const dir = path.resolve(import.meta.dirname, "..", "_prueba");
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(path.join(dir, "material"), { recursive: true });
    for (const [n, color] of [[1, "blue"], [2, "green"]]) {
      execFileSync("ffmpeg", [
        "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=60:duration=4",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
        "-vf", `drawbox=color=${color}@0.3:t=fill`, "-shortest",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        path.join(dir, "material", `clip${n}.mp4`),
      ], { stdio: "inherit" });
    }
    // Motion graphics sinteticos: uno con canal alfa y otro rodado sobre negro, que son
    // las dos familias que trae un pack. Si este ffmpeg no tiene el filtro geq, se salta
    // esa parte en vez de tumbar el self-check entero por algo ajeno.
    const mg = path.join(dir, "material", "mg");
    let overlays = [];
    try {
      fs.mkdirSync(mg, { recursive: true });
      execFileSync("ffmpeg", [
        "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=0x7cb9f2:s=600x600:r=30:d=1.2",
        "-vf", "format=yuva420p,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(between(hypot(X-300,Y-300),40+T*300,72+T*300),255,0)'",
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "1M", path.join(mg, "anillo.webm"),
      ], { stdio: "pipe" });
      execFileSync("ffmpeg", [
        "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "gradients=s=1080x1920:d=1.2:r=30:c0=0x000000:c1=0xff7a2f:speed=0.08:nb_colors=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", path.join(mg, "leak.mp4"),
      ], { stdio: "pipe" });
      overlays = [
        { archivo: "material/mg/anillo.webm", en_s: 0.4, pos: { x: 50, y: 35 }, escala: 0.75 },
        { archivo: "material/mg/leak.mp4", en_s: 2.2, mezcla: "screen", opacidad: 0.9, encima: true },
      ];
    } catch {
      console.log("  ! sin overlays en el test: este ffmpeg no genera los graficos sinteticos.");
    }

    fs.writeFileSync(path.join(dir, "manifest.json"), JSON.stringify({
      slug: "prueba",
      clips: [
        { archivo: "material/clip1.mp4", in_s: 0.5, out_s: 2.5, zoom: { tipo: "in", hacia: { x: 30, y: 25 }, intensidad: 1.2 } },
        {
          archivo: "material/clip2.mp4", in_s: 1, out_s: 3, velocidad: 2, volumen: 0,
          zoom: { tipo: "fijo", intensidad: 1.12 },
          transicion: { tipo: "desenfoque", duracion_s: 0.15 },
        },
      ],
      pistas: [{ archivo: "material/clip1.mp4", in_s: 0, out_s: 1, en_s: 2.1 }],
      velos: [{ desde_s: 2, hasta_s: 3, opacidad: 0.5, desenfoque: 12 }],
      color: { contraste: 1.06, saturacion: 1.1 },
      acento: "#C9973B",
      subtitulos: { activo: true, estilo: "editorial", frases: [{ texto: "voz a *mano*", desde_s: 0.2, hasta_s: 1.6, y: 60 }] },
      textos: [
        { texto: "Prueba del estudio", desde_s: 0.3, hasta_s: 2, posicion: "abajo", animacion: "subir" },
        { texto: "Texto senalado", desde_s: 2.2, hasta_s: 2.9, pos: { x: 28, y: 34 }, animacion: "resorte" },
        { texto: "Un *titulo* / **editorial**", desde_s: 2, hasta_s: 3, estilo: "editorial", pos: { x: 50, y: 45 } },
        { texto: "Antetitulo", desde_s: 2, hasta_s: 3, estilo: "antetitulo", pos: { x: 50, y: 30 } },
        { texto: "Nombre | Cargo", desde_s: 0.4, hasta_s: 1.8, posicion: "arriba", estilo: "credencial" },
      ],
      elementos: [{ icono: "pin", desde_s: 1.2, hasta_s: 2.4, pos: { x: 70, y: 60 } }],
      destellos: [{ en_s: 2.0, duracion_s: 0.25, intensidad: 0.6 }],
      overlays,
      progreso: true,
    }, null, 2));

    process.chdir(dir);
    comandos.normalizar();
    comandos.render(["--borrador"]);

    const out = path.join(dir, "cache", "borrador.mp4");
    const info = ffprobe(out);
    const esperado = 3; // 2s + (2s a 2x)
    if (Math.abs(info.duracion_s - esperado) > 0.2) morir(`FALLA: duracion ${info.duracion_s}s, esperada ${esperado}s`);
    if (info.ancho !== 540 || info.alto !== 960) {
      morir(`FALLA: resolucion ${info.ancho}x${info.alto}, esperada 540x960 (borrador = mitad de 1080x1920)`);
    }
    console.log(`\n  OK render: ${info.ancho}x${info.alto}, ${info.duracion_s.toFixed(2)}s -> ${out}`);
    return comandos.testRevision();
  },

  // Prueba el ida y vuelta de la revision sin iPad: levanta el server en un puerto
  // libre, pide la pagina y el video por partes, manda una nota y verifica que quedo
  // escrita con su PNG.
  async testRevision() {
    const { servir } = await import(pathToFileURL(path.join(import.meta.dirname, "revisar.mjs")));
    const server = await servir({ proyecto: process.cwd(), puerto: 0, callado: true });
    const base = `http://127.0.0.1:${server.address().port}`;
    try {
      const pagina = await fetch(base + "/");
      if (!pagina.ok || !(await pagina.text()).includes("Estudio Vortex")) morir("FALLA revision: no sirve la pagina.");

      const parcial = await fetch(base + "/borrador.mp4", { headers: { range: "bytes=0-99" } });
      if (parcial.status !== 206) morir(`FALLA revision: el video no responde por partes (status ${parcial.status}). Safari no podria mover el tiempo.`);

      const png = "data:image/png;base64," +
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
      const alta = await fetch(base + "/notas", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ t_s: 1.5, texto: "prueba", centro_pct: { x: 40, y: 60 }, png }),
      });
      if (alta.status !== 201) morir(`FALLA revision: POST /notas devolvio ${alta.status}`);

      const notas = await (await fetch(base + "/notas")).json();
      if (notas.length !== 1 || notas[0].texto !== "prueba") morir("FALLA revision: la nota no quedo guardada.");
      if (!fs.existsSync(path.join("revision", notas[0].imagen))) morir("FALLA revision: no se escribio el PNG de la nota.");
      console.log(`  OK revision: pagina, video por partes y nota con imagen (${notas[0].imagen}).`);
    } finally {
      server.close();
    }
  },
};

// Llama al CLI por su entry .js con el mismo node, no por node_modules/.bin:
// el .bin de Windows es un .cmd que exige shell, y con shell los args no se escapan.
function remotion(args) {
  const cli = path.join(RENDER, "node_modules", "@remotion", "cli", "remotion-cli.js");
  if (!fs.existsSync(cli)) morir(`Remotion no esta instalado. Corre: cd ${RENDER} && npm install`);
  execFileSync(process.execPath, [cli, ...args], { cwd: RENDER, stdio: "inherit" });
}

const [comando, ...args] = process.argv.slice(2);
if (!comandos[comando]) morir(`Comandos: ${Object.keys(comandos).join(" | ")}`);
comandos[comando](args);
