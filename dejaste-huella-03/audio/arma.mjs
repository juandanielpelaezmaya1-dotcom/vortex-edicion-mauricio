// Arma manifest.json de dejaste-huella-03 (desde la carpeta del proyecto: node audio/arma.mjs).
// Video ya montado por Mauricio + subtitulos editoriales + transiciones suaves con fuga de luz
// + motion a la medida + logo apilado con contactos + musica original (audio/musica.py).
// Cursivas: blancas por defecto (_chica_ y *grande*); dorado (**...**) solo en palabras clave.
//
// Borrador 3 (notas de Mauricio, 2026-11-22): sin polvo dorado, sin corazones ni huellas,
// fuera 33,88-50,53 (la segunda toma de "por eso creamos nuestro plan", repetida) y fuera
// 53,69-56,0 (la cuenta regresiva antes del sofa), transiciones mas suaves, y botones solo en
// dos secciones: beneficios y WhatsApp al final.
//
// Tambien re-mapea subtitulos/captions-fuente.json (whisper sobre el video entero) a la linea
// de tiempo nueva -> subtitulos/captions.json. Asi no hay que volver a correr whisper.
import fs from "node:fs";

const FUENTE = "material/dejaste-huella-03.mp4";
const DE_PIE = { x: 50, y: 32 }, SOFA1 = { x: 40, y: 38 }, SOFA2 = { x: 50, y: 36 };
const z = (tipo, hacia, intensidad) => ({ tipo, hacia, intensidad });

// [in_s, out_s, zoom, corte real?] en segundos del video de Mauricio. Los cortes de adentro de
// una toma (punch-ins) llevan un desenfoque corto; los reales, desenfoque + fuga de luz.
const TOMAS = [
  // Borrador 4: sin los punch-ins de 6,2 / 10,3 / 17,45 (Mauricio): un acercamiento lento entero.
  [0, 20.02, z("in", DE_PIE, 1.1)],
  [20.02, 29.86, z("out", DE_PIE, 1.1), true], // sale del 1,1 de la toma anterior: el salto se nota menos
  [29.86, 33.88, z("fijo", DE_PIE, 1.15)], // la mejor calidad de vida
  [50.53, 53.69, z("in", DE_PIE, 1.1), true], // asi puedes ahorrar mientras lo cuidas
  [56.0, 67.52, z("in", SOFA1, 1.12), true], // sin la cuenta regresiva (53,7-55,3) ni el punch-in de 61,66
  [67.52, 75.3, z("in", SOFA2, 1.1), true],
  [75.3, 82.86, z("out", SOFA2, 1.12)],
];

// Linea de tiempo nueva
let acc = 0;
const LINEA = TOMAS.map(([a, b, zoom, real]) => {
  const t = { a, b, zoom, real: !!real, en: acc };
  acc += b - a;
  return t;
});
const VIDEO = +acc.toFixed(3);
const CORTES = LINEA.filter((t) => t.real).map((t) => +t.en.toFixed(2)).concat(VIDEO); // + entrada del logo
const aLinea = (s) => {
  const t = LINEA.find((t) => s >= t.a && s < t.b);
  return t ? t.en + (s - t.a) : null;
};
const SOFA_DESDE = +aLinea(56.0).toFixed(2);

// Subtitulos: whisper del video entero -> linea nueva (lo que cae en lo quitado se va)
const fuente = JSON.parse(fs.readFileSync("subtitulos/captions-fuente.json", "utf8"));
const caps = [];
for (const c of fuente) {
  const ini = aLinea(c.startMs / 1000);
  if (ini == null) continue;
  const fin = aLinea(Math.max(c.startMs, c.endMs - 1) / 1000) ?? ini + (c.endMs - c.startMs) / 1000;
  caps.push({ ...c, startMs: Math.round(ini * 1000), endMs: Math.round(Math.max(fin, ini) * 1000) });
}
fs.writeFileSync("subtitulos/captions.json", JSON.stringify(caps, null, 2));

const Y = 66; // plantas y pantalon oscuro en todas las tomas (de pie y en el sofa)
const OCULTA = (palabras) => ({ texto: "", palabras }); // consume whisper sin mostrar: ahi hablan los botones

const F = [
  "llevo / _cinco años_",
  "acompañando / a más de",
  "**dos mil** / familias",
  "en las / despedidas",
  "de sus / _mascoticas_",
  "y lo más / _difícil_",
  "y *doloroso*",
  "no es solo / ver su llanto",
  "y la _tristeza_",
  "sino que / en ese momento",
  "tienen que / hacer _llamadas,_",
  "cuentas y un / _montón_ de cosas",
  "para poderle dar",
  "la despedida / que se **merece**",
  "por eso creamos",
  "nuestro plan de / _previsión exequial_",
  "porque además / de prever / ese momento",
  "lo que haces / es **ahorrar**",
  OCULTA(14), // en veterinarias, en peluquerias, en guarderias y en todo lo que tu mascotica necesite -> tarjetas
  "para darle la / _mejor atención_",
  "y la mejor / calidad de _vida_",
  { texto: "hasta que ese / momento llegue", hasta_s: +aLinea(33.85).toFixed(2) },
  "así puedes / *ahorrar*",
  { texto: "mientras / lo _cuidas_", hasta_s: SOFA_DESDE - 0.03 },
  "y cuando ese / momento llegue",
  "que esperamos / que sea",
  "dentro de / _mucho tiempo_",
  "ya todo va a / estar _preparado,_",
  "su sala / de *velación*",
  "su / **homenaje**",
  "para que no / tengas que / preocuparte",
  "por nada más / que _estar con él_",
  "esta oferta / es por / _tiempo limitado_",
  "hasta el mes de / _diciembre_",
  { texto: "por / **$14.900**", palabras: 2 },
  "para mascoticas",
  "menores a / los *9 años*",
  "y si tu _peludito_",
  "tiene más / de 9 años",
  "también lo / **afiliamos**",
  OCULTA(7), // escribenos y te enviamos toda la informacion -> botones de WhatsApp
  { texto: "¿qué / **esperas?**", hasta_s: VIDEO, y: 70 },
];
const frases = F.map((f) => ({ y: Y, ...(typeof f === "string" ? { texto: f } : f) }));

// Motion a la medida (_render/src/DH03Motion.tsx), WebM con alfa en material/mg/.
const MG = [["beneficios", 24.3], ["precio", 52.94], ["whatsapp", 59.95]];

const m = {
  slug: "dejaste-huella-03",
  fps: 59.94,
  formatos: ["9x16"],
  clips: [
    ...LINEA.map((t, i) => ({
      archivo: FUENTE, in_s: t.a, out_s: t.b, zoom: t.zoom,
      ...(i ? { transicion: { tipo: "desenfoque", duracion_s: t.real ? 0.3 : 0.15 } } : {}),
    })),
    { archivo: "material/logo-contactos-9x16.mp4", in_s: 0, out_s: 7.04, transicion: { tipo: "disolver", duracion_s: 0.5 } },
  ],
  overlays: [
    // Debajo de los subtitulos: vineta y, en el sofa (tapizado claro), una banda oscura suave (T6).
    { archivo: "material/vineta.png", en_s: 0, duracion_s: VIDEO },
    { archivo: "material/banda-oscura.png", en_s: SOFA_DESDE, duracion_s: +(VIDEO - SOFA_DESDE).toFixed(2) },
    ...MG.map(([id, en_s]) => ({ archivo: `material/mg/${id}.webm`, en_s, encima: true })),
    // Fuga de luz suave en cada corte real (el pico, al 35 % de 1 s, cae en el corte). Sin
    // destello blanco: a 0,85 quemaba el cuadro (segundo 20 del borrador 2).
    ...CORTES.map((c) => ({ archivo: "material/destello-oro.mp4", en_s: +(c - 0.35).toFixed(2), mezcla: "screen", opacidad: 0.45, encima: true })),
  ],
  // Se veia gris: contraste y color (probado contra 1,15 y 1,32 sobre las dos locaciones).
  color: { contraste: 1.22, saturacion: 1.15, brillo: 0.98 },
  subtitulos: { activo: true, estilo: "editorial", sombra: true, frases },
  musica: { archivo: "material/musica-ambiental.wav", volumen: 1 },
};
fs.writeFileSync("manifest.json", JSON.stringify(m, null, 2) + "\n");
console.log(`${frases.length} frases · video ${VIDEO} s + logo 7,04 s · cortes reales ${CORTES.join(", ")}`);
console.log(LINEA.map((t) => `${t.en.toFixed(2)}  ${t.a}-${t.b}`).join("\n"));
