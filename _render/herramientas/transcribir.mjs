// Transcripcion local con whisper.cpp (paquetes de Remotion, $0, offline tras la descarga).
// Vive DENTRO de _render porque necesita su node_modules.
//
//   node herramientas/transcribir.mjs --wav <abs-16k.wav> --json <abs-captions.json> --srt <abs.srt> [--modelo small]

import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { installWhisperCpp, downloadWhisperModel, transcribe } from "@remotion/install-whisper-cpp";
import { serializeSrt } from "@remotion/captions";

const args = process.argv.slice(2);
const opt = (n, d) => {
  const i = args.indexOf(`--${n}`);
  return i !== -1 ? args[i + 1] : d;
};

const wav = opt("wav");
const outJson = opt("json");
const outSrt = opt("srt");
const modelo = opt("modelo", "small"); // multilingue — NUNCA variantes .en

if (!wav || !outJson || !outSrt) {
  console.error("Uso: node transcribir.mjs --wav <16k.wav> --json <captions.json> --srt <voz.es.srt> [--modelo small|medium]");
  process.exit(1);
}

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
// whisper.cpp y modelos viven en _assets/modelos (gitignored, compartidos entre proyectos)
const whisperDir = path.resolve(raiz, "..", "_assets", "modelos", "whisper.cpp");

await installWhisperCpp({ to: whisperDir, version: "1.6.0" });
await downloadWhisperModel({ folder: whisperDir, model: modelo });

const salida = await transcribe({
  inputPath: wav,
  whisperPath: whisperDir,
  whisperCppVersion: "1.6.0",
  model: modelo,
  language: "es",
  tokenLevelTimestamps: true,
});

// Tiempos por DTW (t_dtw), no por `offsets` (que es lo que toma toCaptions): con musica de fondo
// o ruido de calle, offsets se corre hasta 2 s (lote Ray-Ban, 28-sep). El DTW, a su vez, llega
// ~0,2 s tarde al arranque real de la voz (medido contra la energia de la banda de voz en los reels
// de Mi Vieja Burger, 6-oct-2026): se adelanta ADELANTO_MS para que la palabra entre con la voz.
// DTW no da el final: la palabra dura lo que tarda en decirse (~70 ms por letra) o hasta la siguiente.
const ADELANTO_MS = 200;
const tokens = [];
for (const c of salida.transcription) {
  if (!c.text) continue;
  const previa = tokens[tokens.length - 1];
  // Whisper da sub-palabras: una palabra nueva empieza donde el token trae espacio delante.
  if (previa && !c.text.startsWith(" ")) previa.text += c.text;
  else {
    const dtw = c.tokens?.find((k) => !k.text.startsWith("[_"))?.t_dtw ?? -1;
    tokens.push({ text: c.text, startMs: Math.max(0, Math.round((dtw >= 0 ? dtw * 10 : c.offsets.from) - ADELANTO_MS)) });
  }
}
// Fuera la puntuacion suelta y las marcas tipo [MUSICA]: no son palabras que se digan.
const dichas = tokens.filter((p) => /[\p{L}\p{N}]/u.test(p.text) && !/^\s*\[/.test(p.text));
const captions = dichas.map((p, i) => ({
  text: p.text,
  startMs: p.startMs,
  endMs: Math.min(dichas[i + 1]?.startMs ?? Infinity, p.startMs + 120 + 70 * p.text.trim().length),
  timestampMs: null,
  confidence: null,
}));
fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(captions, null, 2));
fs.writeFileSync(outSrt, serializeSrt({ lines: captions.map((c) => [c]) }));

console.log(`[transcribir] ${captions.length} palabras -> ${outJson}`);
console.log(`[transcribir] TEXTO: ${captions.map((c) => c.text).join("").trim()}`);
