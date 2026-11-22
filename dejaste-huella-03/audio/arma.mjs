// Arma manifest.json de dejaste-huella-03 (desde la carpeta del proyecto: node audio/arma.mjs).
// Video ya montado por Mauricio + subtitulos editoriales + fuga de luz y destello en cada corte
// + logo apilado con contactos + musica original (audio/musica.py).
// Cursivas: blancas por defecto (_chica_ y *grande*); dorado (**...**) solo en palabras clave.
import fs from "node:fs";

const VIDEO = 82.86;
const CORTES = [20.02, 33.88, 50.53, 53.69, 67.52, VIDEO]; // el ultimo es la entrada del logo
const Y = 66; // plantas y pantalon oscuro en todas las tomas (de pie y en el sofa)

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
  "en _veterinarias,_",
  "en peluquerías, / en guarderías",
  "y en todo / lo que tu",
  "_mascotica_ / necesite",
  "para darle la / _mejor atención_",
  "y la mejor / calidad de _vida_",
  "hasta que ese / momento llegue",
  "por eso creamos / nuestro plan",
  "de **previsión** / **exequial**",
  "para que tú / no tengas que / _preocuparte_",
  "por _absolutamente_ / nada más",
  "que cuidar / a tu _mascotica_",
  "dándole la / mejor calidad / de vida",
  "con _descuentos_ / en veterinarias,",
  "peluquerías, / guarderías, / hoteles",
  "y todo lo que / él necesite",
  "y también tiene / descuentos",
  "**para ti**",
  "así puedes / *ahorrar*",
  "mientras / lo _cuidas_",
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
  "_escríbenos_ / y te enviamos",
  "toda la / _información_",
  { texto: "¿qué / **esperas?**", hasta_s: VIDEO },
];

// Tomas partidas en las pausas para alternar zoom (4e): in / fijo / out. Los cortes reales
// llevan la fuga de luz; los de adentro de una toma son punch-ins secos. Ningun motion cruza uno.
const DE_PIE = { x: 50, y: 32 }, SOFA1 = { x: 40, y: 38 }, SOFA2 = { x: 50, y: 36 };
const z = (tipo, hacia, intensidad) => ({ tipo, hacia, intensidad });
const TOMAS = [
  [0, 6.2, z("in", DE_PIE, 1.12)],
  [6.2, 10.3, z("fijo", DE_PIE, 1.2)],      // lo mas dificil y doloroso
  [10.3, 17.45, z("out", DE_PIE, 1.12)],
  [17.45, 20.02, z("fijo", DE_PIE, 1.1)],
  [20.02, 29.86, z("in", DE_PIE, 1.1)],
  [29.86, 33.88, z("fijo", DE_PIE, 1.18)],  // la mejor calidad de vida
  [33.88, 38.9, z("out", DE_PIE, 1.12)],
  [38.9, 43.58, z("fijo", DE_PIE, 1.15)],
  [43.58, 50.53, z("in", DE_PIE, 1.06)],    // descuentos: suave, los iconos van a los lados
  [50.53, 53.69, z("fijo", DE_PIE, 1.15)],
  [53.69, 61.66, z("in", SOFA1, 1.12)],
  [61.66, 67.52, z("fijo", SOFA1, 1.18)],   // sala de velacion, homenaje
  [67.52, 75.3, z("in", SOFA2, 1.1)],
  [75.3, VIDEO, z("out", SOFA2, 1.12)],
];
// Motion a la medida (_render/src/DH03Motion.tsx), WebM con alfa en material/mg/.
const MG = [
  ["huellas-gancho", 0.9], ["llamadas", 12.1], ["servicios", 24.75], ["vida", 29.9],
  ["huellas-mascotica", 40.2], ["descuentos", 43.65], ["ahorro", 51.55], ["velacion", 61.7],
  ["oferta", 68.35], ["precio", 71.9], ["cta", 77.95],
];

const frases = F.map((f) => ({ ...(typeof f === "string" ? { texto: f } : f), y: Y }));

const m = {
  slug: "dejaste-huella-03",
  fps: 59.94,
  formatos: ["9x16"],
  clips: [
    ...TOMAS.map(([a, b, zoom]) => ({ archivo: "material/dejaste-huella-03.mp4", in_s: a, out_s: b, zoom })),
    { archivo: "material/logo-contactos-9x16.mp4", in_s: 0, out_s: 7.04, transicion: { tipo: "disolver", duracion_s: 0.3 } },
  ],
  // Sofa (53,69 s al final del video): tapizado claro, el dorado perdia contraste. Banda oscura
  // suave detras de los subtitulos (T6: degradado, no caja), debajo de los textos.
  // Fuga de luz: el pico (35 % de 1 s) cae en el corte. Destello blanco bajo (M4) en el corte.
  // Debajo de los subtitulos: vineta, polvo dorado que flota (M1) y la banda del sofa.
  overlays: [
    { archivo: "material/vineta.png", en_s: 0, duracion_s: VIDEO },
    { archivo: "material/polvo-oro.mp4", en_s: 0, mezcla: "screen", opacidad: 0.55 },
    { archivo: "material/banda-oscura.png", en_s: 53.69, duracion_s: +(VIDEO - 53.69).toFixed(2) },
    ...MG.map(([id, en_s]) => ({ archivo: `material/mg/${id}.webm`, en_s, encima: true })),
  ].concat(CORTES.map((c) => ({ archivo: "material/destello-oro.mp4", en_s: +(c - 0.35).toFixed(2), mezcla: "screen", opacidad: 0.85, encima: true }))),
  destellos: CORTES.map((c) => ({ en_s: +(c - 0.04).toFixed(2), duracion_s: 0.35, color: "white", intensidad: 0.45 })),
  // Se veia gris: contraste y color (probado contra 1,15 y 1,32 sobre las dos locaciones).
  color: { contraste: 1.22, saturacion: 1.15, brillo: 0.98 },
  subtitulos: { activo: true, estilo: "editorial", sombra: true, frases },
  musica: { archivo: "material/musica-ambiental.wav", volumen: 1 },
};
fs.writeFileSync("manifest.json", JSON.stringify(m, null, 2) + "\n");
console.log(`${frases.length} frases, ${CORTES.length} transiciones`);
