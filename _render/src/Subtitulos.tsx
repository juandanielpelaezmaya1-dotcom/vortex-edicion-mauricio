import React, { useMemo } from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { createTikTokStyleCaptions, Caption } from "@remotion/captions";

/**
 * Subtitulos palabra por palabra.
 * Whisper da el tiempo de CADA palabra; aca se agrupan en paginas de 2-4 y la palabra
 * que suena se pinta con el acento y da un saltito. Eso es lo "dopaminico": el ojo
 * siempre tiene algo que seguir sin que la pantalla se llene de basura.
 */
/**
 * Whisper no devuelve palabras: devuelve sub-palabras ("client" + "es", " P" + "ela" + "es").
 * Sin unirlas, el resaltado parte palabras por la mitad y se lee "losPRIMERos".
 * Una palabra nueva empieza donde el token trae espacio delante.
 */
const unirPalabras = (captions: Caption[]): Caption[] =>
  captions.reduce<Caption[]>((acc, c) => {
    const previa = acc[acc.length - 1];
    if (previa && !c.text.startsWith(" ")) {
      previa.text += c.text;
      previa.endMs = c.endMs;
      return acc;
    }
    acc.push({ ...c });
    return acc;
  }, []);

export const Subtitulos: React.FC<{
  captions: Caption[];
  acento: string;
  fontFamily: string;
  /** Altura del CENTRO de la banda, en % del alto. Sin ella, la safe zone de siempre. */
  pos?: { y: number };
}> = ({ captions, acento, fontFamily, pos }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const ms = (frame / fps) * 1000;

  const { pages } = useMemo(
    () => createTikTokStyleCaptions({ captions: unirPalabras(captions), combineTokensWithinMilliseconds: 900 }),
    [captions],
  );

  const pagina = pages.find((p) => ms >= p.startMs && ms < p.startMs + p.durationMs);
  if (!pagina) return null;

  return (
    <div
      style={{
        position: "absolute",
        ...(pos
          ? { top: `${pos.y}%`, transform: "translateY(-50%)" }
          : { bottom: height * 0.18 }), // safe zone: por encima de la UI de reels
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        padding: "0 7%",
      }}
    >
      <div
        style={{
          fontFamily,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          // El espacio va como GAP, no como caracter: el scale del rebote no ocupa
          // layout, y una palabra crecida se comia el espacio de la de al lado.
          gap: "0 0.34em",
          fontWeight: 800,
          fontSize: width * 0.058,
          textAlign: "center",
          lineHeight: 1.18,
          letterSpacing: "-0.02em",
          color: "#FFFFFF",
          textShadow: "0 0 10px rgba(0,0,0,0.9), 0 3px 6px rgba(0,0,0,0.85)",
        }}
      >
        {pagina.tokens.map((tok, i) => {
          const activa = ms >= tok.fromMs && ms < tok.toMs;
          // El saltito arranca en el frame en que entra la palabra, no en el de la pagina.
          const salto = activa
            ? spring({
                frame: frame - Math.round((tok.fromMs / 1000) * fps),
                fps,
                config: { damping: 12, stiffness: 220, mass: 0.4 },
              })
            : 1;
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                color: activa ? acento : "#FFFFFF",
                // Salto discreto a proposito: el scale no ocupa layout, y con 1.14 una
                // palabra larga se comia el gap y se pegaba a la anterior. El color hace
                // el trabajo; el salto solo acompana.
                transform: `scale(${activa ? 1.07 - 0.07 * salto : 1})`,
              }}
            >
              {tok.text.trim()}
            </span>
          );
        })}
      </div>
    </div>
  );
};
