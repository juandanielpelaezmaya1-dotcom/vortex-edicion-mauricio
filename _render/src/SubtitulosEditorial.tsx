import React, { useEffect, useState } from "react";
import { cancelRender, continueRender, delayRender, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
// Importada (no staticFile): el --public-dir de los reels es la carpeta de cada proyecto.
// Poppins y Playfair Display, las dos OFL (ver fuentes/OFL-*.txt). Solo el subset latin.
// Fjalla One (OFL) y Permanent Marker (Apache 2.0): las del manual de Mi Vieja Burger.
import playfair from "./fuentes/playfair-display-italic.woff2";
import poppins from "./fuentes/poppins-semibold.woff2";
import fjalla from "./fuentes/fjalla-one.ttf";
import marker from "./fuentes/permanent-marker.ttf";
// Inter y Montserrat (OFL): la sans de Team Leon y los titulos neon.
import inter from "./fuentes/inter.ttf";
import montserrat from "./fuentes/montserrat.ttf";

/**
 * Subtitulos "editorial": frases cortas escritas por el editor, con dos familias. La sans
 * es Poppins; la serif (Playfair italica) va a veces grande, a 2,3 veces la sans, y a veces
 * chica como acento; muchas frases van solo en Poppins. Cada palabra aparece cuando se dice
 * (fundido, sube un poco y se enfoca), sin rebote ni color de karaoke. Sin sombra: primero
 * se quito la de fondo (ensuciaba la imagen) y despues la de las letras, a pedido del
 * cliente (22-sep). Las paginas las arma `estudio.mjs` desde el manifest: aqui solo se pintan.
 */
/** `serif` y `oro` van grandes (el golpe, de vez en cuando); `chica` es la serif como acento
 *  secundario, un poco menor que la sans. La variedad es la gracia: si todo es grande, nada pesa. */
export type Pieza = { texto: string; tipo: "sans" | "serif" | "oro" | "chica"; ms: number };
/** `y`: altura del centro en %, elegida por toma para no tapar caras. */
export type Pagina = { desde: number; hasta: number; lineas: Pieza[][]; y?: number };

/**
 * La tipografia de cada cliente (`subtitulos.marca` en el manifest). El lenguaje es el mismo
 * (sans de base, la segunda familia chica de acento o grande de golpe, `oro` para la marca);
 * cambian las familias, la escala y como se pinta el acento. Sin `marca`, Dejaste Huella.
 *  - `anchoEm`: ancho medio de un caracter en em (medido). Solo sirve para achicar una linea
 *    que no cabe ("ultima despedida" a 2,3x se salia).
 *  - `oro`: "texto" pinta las letras en el acento (el dorado de Dejaste Huella); "cinta" las
 *    pone en blanco sobre una cinta del acento, como los posts de Mi Vieja Burger.
 *  - `inclinar`: grados de las piezas de la segunda familia (el marcador va torcido, a mano).
 */
type Marca = {
  sans: string; serif: string; pesoSans: number; pesoSerif: number; italica: boolean; mayusculas: boolean;
  base: number; grande: number; chica: number; cinta: number;
  anchoEm: { sans: number; serif: number }; espaciado: { sans: string; serif: string };
  oro: "texto" | "cinta"; acento: string; inclinar: number;
  /** Corre cada linea a la derecha de la anterior, en veces `base` (escalera). 0 = centrado. */
  escalon?: number;
  /** Sombra propia de la marca (con `subtitulos.sombra`). Team Leon va sobre chaquetas de colores. */
  sombra?: string;
};
const MARCAS: Record<string, Marca> = {
  "dejaste-huella": {
    sans: '"Poppins", "Avenir Next", sans-serif', serif: '"Playfair Display", Georgia, serif',
    pesoSans: 600, pesoSerif: 600, italica: true, mayusculas: false,
    // La serif de acento: su x es mas baja que la de Poppins, asi a 1,06 se ve apenas menor.
    base: 0.06, grande: 2.3, chica: 1.06, cinta: 2.3,
    anchoEm: { sans: 0.6, serif: 0.47 }, espaciado: { sans: "-0.005em", serif: "-0.01em" },
    oro: "texto", acento: "#CFAA58", inclinar: 0, // oroLuz de Dejaste Huella (las luces de la fachada)
  },
  // Manual de marca (oct-2024) y sus posts: Fjalla One en mayusculas para todo, Permanent Marker
  // torcida para el acento y la palabra de marca en blanco sobre cinta naranja.
  "mi-vieja-burger": {
    sans: '"Fjalla One", "Impact", sans-serif', serif: '"Permanent Marker", "Marker Felt", cursive',
    pesoSans: 400, pesoSerif: 400, italica: false, mayusculas: true,
    base: 0.076, grande: 1.65, chica: 1, cinta: 1.1,
    anchoEm: { sans: 0.43, serif: 0.62 }, espaciado: { sans: "0.01em", serif: "0.02em" },
    oro: "cinta", acento: "#F24405", inclinar: -4,
  },
  // Referencia del cliente (video de la academia, nov-2026): sans blanca liviana y chica, la frase
  // clave en serif italica negra en naranja, mas grande, y las lineas en escalera hacia la derecha.
  "team-leon": {
    sans: '"Inter", "Helvetica Neue", sans-serif', serif: '"Playfair Display", Georgia, serif',
    pesoSans: 500, pesoSerif: 800, italica: true, mayusculas: false,
    base: 0.056, grande: 1.5, chica: 0.9, cinta: 1.5,
    anchoEm: { sans: 0.55, serif: 0.5 }, espaciado: { sans: "-0.01em", serif: "-0.01em" },
    oro: "texto", acento: "#E8772E", inclinar: 0, escalon: 1.3,
    sombra: "0 0.03em 0.1em rgba(0,0,0,0.9), 0 0 0.3em rgba(0,0,0,0.7), 0 0 0.8em rgba(0,0,0,0.45)",
  },
};
const marcaDe = (nombre?: string) => {
  if (nombre && !MARCAS[nombre]) throw new Error(`subtitulos.marca "${nombre}" no existe. Hay: ${Object.keys(MARCAS).join(", ")}`);
  return MARCAS[nombre ?? "dejaste-huella"];
};

/** Carga las fuentes una vez por proceso de render: la usan subtitulos, titulos y antetitulos. */
export const useFuentes = () => {
  const [espera] = useState(() => delayRender("Fuentes de los subtitulos editoriales"));
  useEffect(() => {
    const fuentes = [
      new FontFace("Playfair Display", `url(${playfair}) format("woff2")`, { style: "italic", weight: "400 900" }),
      new FontFace("Poppins", `url(${poppins}) format("woff2")`, { weight: "600" }),
      new FontFace("Fjalla One", `url(${fjalla}) format("truetype")`),
      new FontFace("Permanent Marker", `url(${marker}) format("truetype")`),
      new FontFace("Inter", `url(${inter}) format("truetype")`, { weight: "100 900" }),
      new FontFace("Montserrat", `url(${montserrat}) format("truetype")`, { weight: "100 900" }),
    ];
    Promise.all(fuentes.map((f) => f.load()))
      .then(() => {
        fuentes.forEach((f) => document.fonts.add(f));
        continueRender(espera);
      })
      .catch((e: unknown) => cancelRender(e));
  }, [espera]);
};

const entra = (ms: number, desde: number, dur: number) =>
  interpolate(ms, [desde, desde + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

/**
 * Un bloque de frases en el lenguaje editorial (lo usan los subtitulos y los titulos de
 * pantalla). `ms` es el tiempo actual en la misma escala que `Pieza.ms`; `y` la altura del
 * centro en %; `oro` el color de las piezas `oro` (el acento de la marca).
 */
export const BloqueEditorial: React.FC<{ lineas: Pieza[][]; ms: number; y: number; opacity: number; oro?: string; sombra?: boolean; marca?: string }> = ({
  lineas, ms, y, opacity, oro, sombra, marca,
}) => {
  const { width, height } = useVideoConfig();
  const m = marcaDe(marca);
  const acento = oro ?? m.acento;
  const base = width * m.base;
  const enCinta = (p: Pieza) => p.tipo === "oro" && m.oro === "cinta";
  // TODO centrado: nada corrido a los lados. Cuando el bloque baja hasta los
  // botones de Instagram (62,5 % del alto) se acota el ancho a lo que queda libre (54 %,
  // centrado). Por eso las frases van en trozos cortos: que no haya que encoger la letra.
  const esGrande = (p: Pieza) => p.tipo === "serif" || (p.tipo === "oro" && !enCinta(p));
  const altoBloque = lineas.reduce(
    (a, l) => a + (l.some(esGrande) ? base * m.grande * 0.96 : l.some(enCinta) ? base * m.cinta * 1.3 : base * 1.12),
    0,
  );
  const maximo = width * (y + (50 * altoBloque) / height > 62.5 ? 0.54 : 0.84);

  return (
    <div
      style={{
        position: "absolute",
        top: `${y}%`,
        transform: "translateY(-50%)",
        left: 0,
        right: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        textAlign: "center",
        color: "#FFFFFF",
        opacity,
      }}
    >
      {lineas.map((linea, i) => {
        const tam = (p: Pieza) => base * (enCinta(p) ? m.cinta : esGrande(p) ? m.grande : p.tipo === "chica" ? m.chica : 1);
        const tieneSerif = linea.some(esGrande);
        const tieneCinta = linea.some(enCinta);
        const estimado = linea.reduce((acc, p, j) => {
          const serif = p.tipo !== "sans";
          return acc + p.texto.length * tam(p) * m.anchoEm[serif ? "serif" : "sans"] + (j ? base * 0.3 : 0) + (enCinta(p) ? tam(p) * 0.3 : 0);
        }, 0);
        const cabe = Math.min(1, maximo / estimado);
        // Una linea sans justo debajo de una serif grande quedaba pegada a sus descendentes.
        const trasSerif = i > 0 && !tieneSerif && lineas[i - 1].some(esGrande);
        return (
          <div
            key={i}
            style={{
              marginTop: trasSerif ? base * 0.22 : 0,
              display: "flex",
              justifyContent: "center",
              alignItems: "baseline",
              whiteSpace: "nowrap",
              lineHeight: tieneSerif ? 0.96 : tieneCinta ? 1.3 : 1.12,
              // La linea con cinta va torcida entera, como la etiqueta pegada de los posts.
              // Con `escalon`, cada linea se corre a la derecha de la anterior (centro del bloque fijo).
              transform: [
                m.escalon && lineas.length > 1 ? `translateX(${(i - (lineas.length - 1) / 2) * m.escalon * base}px)` : "",
                tieneCinta && m.inclinar ? `rotate(${m.inclinar * 0.6}deg)` : "",
              ].join(" ").trim() || undefined,
            }}
          >
            {linea.map((p, j) => {
              const serif = p.tipo !== "sans";
              const cinta = enCinta(p);
              // Dos piezas seguidas en cinta se tocan: la cinta se lee como una sola.
              const pegada = cinta && j > 0 && enCinta(linea[j - 1]);
              const a = entra(ms, p.ms, esGrande(p) ? 380 : serif ? 260 : 220);
              const torcida = serif && !cinta && m.inclinar ? ` rotate(${m.inclinar}deg)` : "";
              return (
                <span
                  key={j}
                  style={{
                    display: "inline-block",
                    whiteSpace: "pre",
                    marginLeft: j && !pegada ? base * 0.3 * cabe : 0,
                    fontFamily: serif ? m.serif : m.sans,
                    fontStyle: serif && m.italica ? "italic" : "normal",
                    fontWeight: serif ? m.pesoSerif : m.pesoSans,
                    fontSize: tam(p) * cabe,
                    letterSpacing: m.espaciado[serif ? "serif" : "sans"],
                    textTransform: m.mayusculas ? "uppercase" : undefined,
                    color: p.tipo === "oro" && !cinta ? acento : "#FFFFFF",
                    ...(cinta ? { background: acento, padding: "0.02em 0.15em 0.06em" } : {}),
                    opacity: a,
                    transform: `translateY(${(1 - a) * base * 0.35}px)${torcida}`,
                    filter: a < 1 ? `blur(${(1 - a) * 6}px)` : undefined,
                    // Opcional: sin ella el blanco se pierde en paredes y ventanas claras (Ray-Ban).
                    // La cinta no la necesita: el fondo ya le da el contraste.
                    textShadow: sombra && !cinta ? m.sombra ?? "0 0.04em 0.2em rgba(0,0,0,0.6), 0 0 0.06em rgba(0,0,0,0.35)" : undefined,
                  }}
                >
                  {p.texto}
                </span>
              );
            })}
          </div>
        );
      })}
    </div>
  );
};

export const SubtitulosEditorial: React.FC<{ paginas: Pagina[]; pos?: { y: number }; oro?: string; sombra?: boolean; marca?: string }> = ({ paginas, pos, oro, sombra, marca }) => {
  useFuentes();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const pagina = paginas.find((p) => ms >= p.desde && ms < p.hasta);
  if (!pagina) return null;
  const sale = interpolate(ms, [pagina.hasta - 160, pagina.hasta], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <BloqueEditorial lineas={pagina.lineas} ms={ms} y={pagina.y ?? pos?.y ?? 63} opacity={sale} oro={oro} sombra={sombra} marca={marca} />;
};
