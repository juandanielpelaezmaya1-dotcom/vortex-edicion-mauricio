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

const frases = F.map((f) => ({ ...(typeof f === "string" ? { texto: f } : f), y: Y }));

const m = {
  slug: "dejaste-huella-03",
  fps: 59.94,
  formatos: ["9x16"],
  clips: [
    { archivo: "material/dejaste-huella-03.mp4", in_s: 0, out_s: VIDEO },
    { archivo: "material/logo-contactos-9x16.mp4", in_s: 0, out_s: 7.04, transicion: { tipo: "disolver", duracion_s: 0.3 } },
  ],
  // Sofa (53,69 s al final del video): tapizado claro, el dorado perdia contraste. Banda oscura
  // suave detras de los subtitulos (T6: degradado, no caja), debajo de los textos.
  // Fuga de luz: el pico (35 % de 1 s) cae en el corte. Destello blanco bajo (M4) en el corte.
  overlays: [{ archivo: "material/banda-oscura.png", en_s: 53.69, duracion_s: +(VIDEO - 53.69).toFixed(2) }].concat(CORTES.map((c) => ({ archivo: "material/destello-oro.mp4", en_s: +(c - 0.35).toFixed(2), mezcla: "screen", opacidad: 0.85, encima: true }))),
  destellos: CORTES.map((c) => ({ en_s: +(c - 0.04).toFixed(2), duracion_s: 0.35, color: "white", intensidad: 0.45 })),
  subtitulos: { activo: true, estilo: "editorial", sombra: true, frases },
  musica: { archivo: "material/musica-ambiental.wav", volumen: 1 },
};
fs.writeFileSync("manifest.json", JSON.stringify(m, null, 2) + "\n");
console.log(`${frases.length} frases, ${CORTES.length} transiciones`);
