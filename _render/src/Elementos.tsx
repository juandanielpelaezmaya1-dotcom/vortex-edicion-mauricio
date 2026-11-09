import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/** Punto en % del ancho/alto del cuadro, origen arriba-izquierda. Es exactamente lo que
 *  devuelve el circulo dibujado con el Pencil en la revision del iPad. */
export type Punto = { x: number; y: number };

export type Elemento = {
  icono: string;
  desde_s: number;
  hasta_s: number;
  posicion?: "arriba" | "centro";
  pos?: Punto;
  /** Tamano relativo al de siempre (17 % del ancho). 0,5 = la mitad. */
  escala?: number;
};

// Iconos dibujados a mano en viewBox 24. Trazo, no relleno: sobre video se lee mejor
// y escala a cualquier resolucion sin pesar un byte.
const TRAZOS: Record<string, React.ReactNode> = {
  pin: (
    <>
      <path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z" />
      <circle cx="12" cy="10" r="2.6" />
    </>
  ),
  lupa: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M16 16l4.5 4.5" />
    </>
  ),
  estrella: <path d="M12 3.2l2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z" />,
  alerta: (
    <>
      <path d="M12 3.5 21 20H3l9-16.5Z" />
      <path d="M12 9.5v4.2" />
      <path d="M12 16.6v.1" />
    </>
  ),
  chat: (
    <>
      <path d="M20.5 12c0 4-3.8 7.2-8.5 7.2-1 0-2-.15-2.9-.42L4 20.5l1.5-3.7C4.1 15.5 3.5 13.8 3.5 12c0-4 3.8-7.2 8.5-7.2s8.5 3.2 8.5 7.2Z" />
    </>
  ),
  // "Sube el volumen": un parlante con dos ondas.
  volumen: (
    <>
      <path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z" />
      <path d="M15.5 9a4 4 0 0 1 0 6" />
      <path d="M18 6.5a7.5 7.5 0 0 1 0 11" />
    </>
  ),
  // Los dos del CTA de un reel, con la forma de los botones de Instagram: guardar y enviar.
  guardar: <path d="M6.5 3.5h11v17l-5.5-4.6-5.5 4.6z" />,
  enviar: (
    <>
      <path d="M21 3.5 3 10.2l7.2 3 3 7.3z" />
      <path d="M21 3.5 10.2 13.2" />
    </>
  ),
};

const Icono: React.FC<{ el: Elemento; acento: string }> = ({ el, acento }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const total = Math.max(1, Math.round((el.hasta_s - el.desde_s) * fps));

  const entrada = spring({ frame, fps, config: { damping: 11, stiffness: 190, mass: 0.5 } });
  const salida = interpolate(frame, [total - 7, total], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const escala = 0.55 + 0.45 * entrada;
  const flote = Math.sin((frame / fps) * 2.2) * (height * 0.006); // respira, no se queda muerto
  const lado = width * 0.17 * (el.escala ?? 1);

  const svg = (
    <svg
      width={lado}
      height={lado}
      viewBox="0 0 24 24"
      fill="none"
      stroke={acento}
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{
        opacity: salida,
        transform: `translateY(${flote}px) scale(${escala})`,
        filter: "drop-shadow(0 3px 10px rgba(0,0,0,0.75))",
      }}
    >
      {TRAZOS[el.icono] ?? TRAZOS.pin}
    </svg>
  );

  // pos manda sobre posicion: es el punto exacto senalado en la revision.
  if (el.pos) {
    return (
      <AbsoluteFill>
        <div
          style={{
            position: "absolute",
            left: `${el.pos.x}%`,
            top: `${el.pos.y}%`,
            transform: "translate(-50%, -50%)",
          }}
        >
          {svg}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: el.posicion === "centro" ? "center" : "flex-start",
        alignItems: "center",
        paddingTop: el.posicion === "centro" ? 0 : height * 0.15,
      }}
    >
      {svg}
    </AbsoluteFill>
  );
};

export const Elementos: React.FC<{ elementos: Elemento[]; acento: string }> = ({ elementos, acento }) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {elementos.map((el, i) => (
        <Sequence
          key={i}
          from={Math.round(el.desde_s * fps)}
          durationInFrames={Math.max(1, Math.round((el.hasta_s - el.desde_s) * fps))}
        >
          <Icono el={el} acento={acento} />
        </Sequence>
      ))}
    </>
  );
};
