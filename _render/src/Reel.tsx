import React from "react";
import { Caption } from "@remotion/captions";
import { Subtitulos } from "./Subtitulos";
import { SubtitulosEditorial, Pagina, Pieza, BloqueEditorial, useFuentes } from "./SubtitulosEditorial";
import { Elementos, Elemento, Punto } from "./Elementos";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  Sequence,
  Series,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const FPS = 30;

/**
 * Acercamiento sobre un clip. `hacia` es la zona que se senala en la revision: la imagen
 * crece desde ahi, no desde el centro. `tipo: "fijo"` NO anima: entra ya acercado y se
 * queda — es el punch-in de reels, el recurso que hace que un corte se lea como decision.
 */
export type Zoom = { tipo?: "in" | "out" | "fijo"; hacia?: Punto; intensidad?: number };

/**
 * Como ENTRA un clip. Es una animacion del clip entrante, no un solape entre dos: la
 * linea de tiempo no se mueve ni un cuadro, que es lo que mantiene los subtitulos y los
 * iconos donde estan. Un solape de verdad acortaria el video y desincronizaria todo.
 */
export type Transicion = {
  tipo?: "disolver" | "desenfoque" | "deslizar" | "escala";
  duracion_s?: number;
  desde?: "izq" | "der" | "arriba" | "abajo";
};

/** `volumen` 0 silencia la toma: cuando la voz va aparte (`pistas`), el sonido de las tomas estorba. */
export type Clip = { src: string; duracion_s: number; zoom?: Zoom; transicion?: Transicion; volumen?: number };

/** Correccion de color global (1 = sin cambio). Para material nublado y plano. */
export type Color = { contraste?: number; saturacion?: number; brillo?: number };

export type Texto = {
  texto: string;
  desde_s: number;
  hasta_s: number;
  posicion?: "arriba" | "centro" | "abajo";
  pos?: Punto;
  /** Como entra. Por defecto `fundido`, que es como se comportaba siempre. */
  animacion?: "fundido" | "subir" | "resorte";
  /** `credencial` lo pinta como rotulo de TV: caja, barra de acento y alineado a la
   *  izquierda. Con "|" en el texto, lo de antes es el nombre y lo de despues el cargo.
   *  `editorial` usa el lenguaje de los subtitulos editoriales (Poppins + Playfair, las
   *  mismas marcas) con las palabras escalonadas: gancho, titulos, CTA.
   *  `antetitulo`: mayusculas chicas espaciadas en el acento, con una raya que se dibuja. */
  estilo?: "credencial" | "editorial" | "antetitulo";
  /** Lo arma estudio.mjs para `editorial` a partir de `texto`. */
  lineas?: Pieza[][];
  /** `editorial` con sombra suave en las letras, como `subtitulos.sombra`. */
  sombra?: boolean;
};

export type Efecto = { src: string; en_s: number; volumen?: number };

/**
 * Motion graphic encima del video. Dos familias, y la diferencia importa:
 *  - Con canal alfa (WebM VP9 alfa, ProRes 4444): `mezcla: "normal"`, se ve tal cual.
 *  - Rodado sobre NEGRO (fugas de luz, particulas, glitch): `mezcla: "screen"`, que
 *    hace que el negro desaparezca y solo quede la luz.
 * Sin `pos` cubre el cuadro entero; con `pos` se coloca en ese punto a `escala` del ancho.
 * Va debajo de textos y subtitulos salvo `encima: true`, para que el texto no se tape.
 * Una imagen (PNG, SVG) va igual: es el logo del cliente encima de todo el video.
 */
export type Overlay = {
  src: string;
  en_s: number;
  duracion_s: number;
  mezcla?: "normal" | "screen" | "lighten" | "overlay" | "soft-light";
  pos?: Punto;
  escala?: number;
  opacidad?: number;
  encima?: boolean;
};
export type Destello = { en_s: number; color?: string; duracion_s?: number; intensidad?: number };

/** Voz aparte de las tomas (ya cortada y nivelada en cache/), en su segundo de la linea de tiempo. */
export type Pista = { src: string; en_s: number; duracion_s: number; volumen?: number };

/** Difumina un rectangulo del cuadro en un tramo (una pantalla con datos, una placa). `x`,`y`
 *  = esquina superior izquierda y `w`,`h` = tamano, todo en % del cuadro 9:16. No sigue al objeto:
 *  en un POV que se mueve, el rectangulo tiene que ser generoso. */
export type Desenfoque = { desde_s: number; hasta_s: number; x: number; y: number; w: number; h: number; fuerza?: number };

/** Oscurece y desenfoca el video en un tramo: el fondo de una tarjeta final o de un titulo. */
export type Velo = { desde_s: number; hasta_s: number; opacidad?: number; desenfoque?: number; color?: string };

export type ReelProps = {
  /** El del material; sin el, FPS. */
  fps?: number;
  clips: Clip[];
  musica?: { src: string; volumen?: number };
  textos?: Texto[];
  efectos?: Efecto[];
  elementos?: Elemento[];
  destellos?: Destello[];
  overlays?: Overlay[];
  /** Barra fina de avance arriba. En un reel es retencion: se ve cuanto falta. */
  progreso?: boolean;
  /** Palabra por palabra (`captions`) o, con estilo "editorial", paginas ya armadas. */
  subtitulos?: { captions?: Caption[]; paginas?: Pagina[]; acento?: string; pos?: { y: number }; sombra?: boolean; marca?: string };
  pistas?: Pista[];
  velos?: Velo[];
  desenfoques?: Desenfoque[];
  color?: Color;
  /** Color de la marca: iconos, barra de progreso, antetitulos y las piezas `**oro**`. */
  acento?: string;
};

/** Frames por clip, redondeados uno a uno: la suma debe cuadrar con la duracion total. */
export const framesDeClips = (clips: Clip[], fps: number) =>
  clips.map((c) => Math.max(1, Math.round(c.duracion_s * fps)));

export const duracionTotal = (clips: Clip[], fps: number) =>
  Math.max(1, framesDeClips(clips, fps).reduce((a, b) => a + b, 0));

const ALINEACION = { arriba: "flex-start", centro: "center", abajo: "flex-end" } as const;
const FUENTE = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif";
const ACENTO = "#7cb9f2";

const suave = (frame: number, hasta: number) =>
  interpolate(frame, [0, hasta], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

/** El clip con su acercamiento y su entrada. El zoom va en el video y la transicion en
 *  el contenedor: separados no se pelean por el mismo `transform`. */
const ClipVideo: React.FC<{ clip: Clip; frames: number; color?: Color }> = ({ clip, frames, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const z = clip.zoom;
  const fuerza = Math.max(1, z?.intensidad ?? 1.15);
  const escala = !z
    ? 1
    : z.tipo === "fijo"
      ? fuerza
      : interpolate(frame, [0, frames], z.tipo === "out" ? [fuerza, 1] : [1, fuerza], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
  const foco = z?.hacia ?? { x: 50, y: 50 };

  const tr = clip.transicion;
  const dur = Math.max(1, Math.round((tr?.duracion_s ?? 0.13) * fps));
  const p = tr ? suave(frame, dur) : 1;
  const fuera = 1 - p;

  const entrada: React.CSSProperties = !tr
    ? {}
    : tr.tipo === "deslizar"
      ? {
          transform: `translate(${
            tr.desde === "izq" ? -fuera * 100 : tr.desde === "der" ? fuera * 100 : 0
          }%, ${tr.desde === "arriba" ? -fuera * 100 : tr.desde === "abajo" ? fuera * 100 : 0}%)`,
        }
      : tr.tipo === "escala"
        ? { opacity: Math.min(1, p * 1.8), transform: `scale(${1 + fuera * 0.09})` }
        : tr.tipo === "desenfoque"
          ? { opacity: Math.min(1, p * 1.6), filter: `blur(${fuera * 16}px)` }
          : { opacity: p };

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "black" }}>
      <AbsoluteFill style={entrada}>
        <OffthreadVideo
          src={staticFile(clip.src)}
          volume={clip.volumen ?? 1}
          muted={clip.volumen === 0}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${escala})`,
            transformOrigin: `${foco.x}% ${foco.y}%`,
            ...(color
              ? { filter: `contrast(${color.contraste ?? 1}) saturate(${color.saturacion ?? 1}) brightness(${color.brillo ?? 1})` }
              : {}),
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const TextoEnPantalla: React.FC<{ t: Texto; acento: string }> = ({ t, acento }) => {
  const frame = useCurrentFrame();
  const { fps, height } = useVideoConfig();
  const total = Math.max(1, Math.round((t.hasta_s - t.desde_s) * fps));
  const fade = Math.min(8, Math.floor(total / 3));
  const salida = interpolate(frame, [total - fade, total], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (t.estilo === "editorial" && t.lineas) {
    return <TituloEditorial lineas={t.lineas} y={t.pos?.y ?? 50} opacity={salida} acento={acento} sombra={t.sombra} />;
  }
  if (t.estilo === "antetitulo") {
    return <Antetitulo texto={t.texto} y={t.pos?.y ?? 20} opacity={salida} acento={acento} />;
  }

  // La entrada cambia con `animacion`; la salida siempre se funde.
  const anim = t.animacion ?? "fundido";
  const brinco = spring({ frame, fps, config: { damping: 12, stiffness: 200, mass: 0.5 } });
  const p = anim === "resorte" ? brinco : suave(frame, fade || 1);
  const opacity = Math.min(anim === "fundido" ? p : Math.min(1, p * 2), salida);
  const mueve =
    anim === "subir" ? `translateY(${(1 - p) * height * 0.035}px)` :
    anim === "resorte" ? `scale(${0.86 + 0.14 * p})` : "";

  const credencial = t.estilo === "credencial";
  const [nombre, cargo] = t.texto.split("|").map((s) => s.trim());

  const estilo: React.CSSProperties = {
    opacity,
    transform: mueve,
    // Con `pos` el ancho ya lo acota el contenedor: un 84% encima se desborda y
    // descentra el texto en vez de acotarlo.
    maxWidth: t.pos ? "100%" : "84%",
    textAlign: credencial ? "left" : "center",
    color: "white",
    fontFamily: FUENTE,
    fontWeight: 800,
    fontSize: height * 0.045,
    lineHeight: 1.15,
    letterSpacing: "-0.02em",
    textShadow: credencial ? "none" : "0 2px 12px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.8)",
    ...(credencial
      ? {
          background: "rgba(6, 8, 53, 0.74)",
          borderLeft: `${height * 0.005}px solid ${ACENTO}`,
          padding: `${height * 0.016}px ${height * 0.022}px`,
          borderRadius: height * 0.006,
          backdropFilter: "blur(6px)",
        }
      : {}),
  };

  const cuerpo = credencial ? (
    <div style={estilo}>
      <div>{nombre}</div>
      {cargo ? (
        <div style={{ fontSize: height * 0.026, fontWeight: 600, color: ACENTO, letterSpacing: "0.01em", marginTop: height * 0.004 }}>
          {cargo}
        </div>
      ) : null}
    </div>
  ) : (
    <div style={estilo}>{t.texto}</div>
  );

  // pos manda sobre posicion: es el punto exacto senalado en la revision. El ancho se
  // acota al espacio que queda hasta el borde mas cercano: si no, un punto senalado
  // cerca de una esquina saca la mitad del texto fuera del cuadro.
  if (t.pos) {
    // Ancho EXPLICITO, no shrink-to-fit: un absoluto con `left: 50%` y sin ancho solo
    // puede usar la mitad derecha del cuadro, y partia en dos lineas textos que cabian
    // de sobra. El ancho se acota al espacio hasta el borde mas cercano para que un
    // punto senalado en una esquina no saque el texto fuera.
    const ancho = Math.max(20, Math.min(84, 2 * Math.min(t.pos.x, 100 - t.pos.x)));
    return (
      <AbsoluteFill>
        <div
          style={{
            width: `${ancho}%`,
            display: "flex",
            justifyContent: "center",
            position: "absolute",
            left: `${t.pos.x}%`,
            top: `${t.pos.y}%`,
            transform: "translate(-50%, -50%)",
          }}
        >
          {cuerpo}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: ALINEACION[t.posicion ?? "abajo"],
        alignItems: credencial ? "flex-start" : "center",
        padding: `${height * 0.09}px ${height * 0.045}px`,
      }}
    >
      {cuerpo}
    </AbsoluteFill>
  );
};

/** El bloque de los subtitulos editoriales con su propio reloj: las palabras entran escalonadas
 *  desde que empieza el texto. Es un componente aparte porque carga las fuentes (hook). */
const TituloEditorial: React.FC<{ lineas: Pieza[][]; y: number; opacity: number; acento: string; sombra?: boolean }> = ({ lineas, y, opacity, acento, sombra }) => {
  useFuentes();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return <BloqueEditorial lineas={lineas} ms={(frame / fps) * 1000} y={y} opacity={opacity} oro={acento} sombra={sombra} />;
};

/** Rotulo chico como los del informe ("EL TERRITORIO"): una raya que se dibuja y el texto que
 *  se destapa detras de ella, de izquierda a derecha. */
const Antetitulo: React.FC<{ texto: string; y: number; opacity: number; acento: string }> = ({ texto, y, opacity, acento }) => {
  useFuentes();
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const raya = suave(frame, Math.round(0.35 * fps));
  const destapa = interpolate(frame, [0.15 * fps, 0.75 * fps], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <div
      style={{
        position: "absolute",
        top: `${y}%`,
        left: 0,
        right: 0,
        transform: "translateY(-50%)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: width * 0.022,
        opacity,
      }}
    >
      <div style={{ width: width * 0.07 * raya, height: Math.max(2, width * 0.0028), background: acento, boxShadow: "0 1px 8px rgba(0,0,0,0.45)" }} />
      <div
        style={{
          fontFamily: '"Poppins", sans-serif',
          fontWeight: 600,
          fontSize: width * 0.03,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: acento,
          whiteSpace: "nowrap",
          clipPath: `inset(0 ${100 - destapa}% 0 0)`,
          // Letra chica y de color sobre cielo o ventana se pierde: una sombra suave, como la de
          // los iconos. Los subtitulos no la llevan (se la quito un cliente); este rotulo si.
          textShadow: "0 1px 10px rgba(0,0,0,0.55)",
        }}
      >
        {texto}
      </div>
      <div style={{ width: width * 0.07 * raya, height: Math.max(2, width * 0.0028), background: acento, boxShadow: "0 1px 8px rgba(0,0,0,0.45)" }} />
    </div>
  );
};

/** Entra en medio segundo y sale en un tercio: sin corte brusco al empezar ni al terminar. */
const UnVelo: React.FC<{ v: Velo; total: number }> = ({ v, total }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [0, 0.5 * fps, total - 0.33 * fps, total], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const hex = Math.round((v.opacidad ?? 0.5) * p * 255).toString(16).padStart(2, "0");
  return (
    <AbsoluteFill
      style={{
        backgroundColor: `${v.color ?? "#000000"}${hex}`,
        backdropFilter: `blur(${(v.desenfoque ?? 0) * p}px)`,
      }}
    />
  );
};

/** Sube de golpe y baja despacio: asi lee como flash de camara y no como parpadeo. */
const UnDestello: React.FC<{ d: Destello; total: number }> = ({ d, total }) => {
  const frame = useCurrentFrame();
  const pico = Math.max(1, Math.round(total * 0.18));
  const opacity = interpolate(frame, [0, pico, total], [0, d.intensidad ?? 0.85, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ backgroundColor: d.color ?? "white", opacity }} />;
};

const UnOverlay: React.FC<{ o: Overlay }> = ({ o }) => {
  const { width } = useVideoConfig();
  // `transparent` es lo que hace que Remotion respete el canal alfa del WebM. En un
  // overlay de mezcla screen no hace falta: el negro lo quita la mezcla.
  const ajuste: React.CSSProperties = { width: "100%", height: "100%", objectFit: o.pos ? "contain" : "cover" };
  const video = /\.(png|svg|jpe?g|webp)$/i.test(o.src) ? (
    <Img src={staticFile(o.src)} style={ajuste} />
  ) : (
    <OffthreadVideo src={staticFile(o.src)} transparent={(o.mezcla ?? "normal") === "normal"} style={ajuste} />
  );
  const capa: React.CSSProperties = {
    mixBlendMode: o.mezcla ?? "normal",
    opacity: o.opacidad ?? 1,
  };
  if (!o.pos) return <AbsoluteFill style={capa}>{video}</AbsoluteFill>;
  const lado = width * (o.escala ?? 0.5);
  return (
    <AbsoluteFill style={capa}>
      <div
        style={{
          position: "absolute",
          left: `${o.pos.x}%`,
          top: `${o.pos.y}%`,
          width: lado,
          height: lado,
          transform: "translate(-50%, -50%)",
        }}
      >
        {video}
      </div>
    </AbsoluteFill>
  );
};

const Overlays: React.FC<{ overlays: Overlay[] }> = ({ overlays }) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {overlays.map((o, i) => (
        <Sequence
          key={`ov${i}`}
          from={Math.round(o.en_s * fps)}
          durationInFrames={Math.max(1, Math.round(o.duracion_s * fps))}
        >
          <UnOverlay o={o} />
        </Sequence>
      ))}
    </>
  );
};

const Progreso: React.FC<{ acento: string }> = ({ acento }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start" }}>
      <div style={{ height: height * 0.004, background: "rgba(255,255,255,0.18)" }}>
        <div
          style={{
            height: "100%",
            width: `${(frame / Math.max(1, durationInFrames - 1)) * 100}%`,
            background: acento,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const Reel: React.FC<ReelProps> = ({
  clips, musica, textos, efectos, elementos, destellos, overlays, progreso, subtitulos, pistas, velos, desenfoques, color, acento: marca,
}) => {
  const detras = (overlays ?? []).filter((o) => !o.encima);
  const delante = (overlays ?? []).filter((o) => o.encima);
  const { fps, durationInFrames } = useVideoConfig();
  const duraciones = framesDeClips(clips, fps);
  const acento = marca ?? subtitulos?.acento ?? ACENTO;

  if (clips.length === 0) {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: "#101014",
          color: "#8a8a95",
          justifyContent: "center",
          alignItems: "center",
          fontFamily: "system-ui, sans-serif",
          fontSize: 32,
        }}
      >
        Sin clips: pasa props desde el manifest.
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Series>
        {clips.map((clip, i) => (
          <Series.Sequence key={i} durationInFrames={duraciones[i]}>
            <ClipVideo clip={clip} frames={duraciones[i]} color={color} />
          </Series.Sequence>
        ))}
      </Series>

      {detras.length ? <Overlays overlays={detras} /> : null}

      {(desenfoques ?? []).map((d, i) => (
        <Sequence key={`d${i}`} from={Math.round(d.desde_s * fps)} durationInFrames={Math.max(1, Math.round((d.hasta_s - d.desde_s) * fps))}>
          <div
            style={{
              position: "absolute", left: `${d.x}%`, top: `${d.y}%`, width: `${d.w}%`, height: `${d.h}%`,
              backdropFilter: `blur(${d.fuerza ?? 24}px)`, WebkitBackdropFilter: `blur(${d.fuerza ?? 24}px)`, borderRadius: 16,
            }}
          />
        </Sequence>
      ))}

      {(velos ?? []).map((v, i) => {
        const total = Math.max(1, Math.round((v.hasta_s - v.desde_s) * fps));
        return (
          <Sequence key={`v${i}`} from={Math.round(v.desde_s * fps)} durationInFrames={total}>
            <UnVelo v={v} total={total} />
          </Sequence>
        );
      })}

      {(textos ?? []).map((t, i) => (
        <Sequence
          key={i}
          from={Math.round(t.desde_s * fps)}
          durationInFrames={Math.max(1, Math.round((t.hasta_s - t.desde_s) * fps))}
        >
          <TextoEnPantalla t={t} acento={acento} />
        </Sequence>
      ))}

      {elementos?.length ? <Elementos elementos={elementos} acento={acento} /> : null}

      {subtitulos?.paginas?.length ? (
        <SubtitulosEditorial paginas={subtitulos.paginas} pos={subtitulos.pos} oro={marca} sombra={subtitulos.sombra} marca={subtitulos.marca} />
      ) : subtitulos?.captions?.length ? (
        <Subtitulos
          captions={subtitulos.captions}
          acento={acento}
          fontFamily={FUENTE}
          pos={subtitulos.pos}
        />
      ) : null}

      {(destellos ?? []).map((d, i) => {
        const total = Math.max(2, Math.round((d.duracion_s ?? 0.25) * fps));
        return (
          <Sequence key={`d${i}`} from={Math.round(d.en_s * fps)} durationInFrames={total}>
            <UnDestello d={d} total={total} />
          </Sequence>
        );
      })}

      {delante.length ? <Overlays overlays={delante} /> : null}

      {progreso ? <Progreso acento={acento} /> : null}

      {(efectos ?? []).map((e, i) => (
        <Sequence key={`fx${i}`} from={Math.round(e.en_s * fps)}>
          <Audio src={staticFile(e.src)} volume={e.volumen ?? 0.6} />
        </Sequence>
      ))}

      {(pistas ?? []).map((p, i) => (
        <Sequence
          key={`p${i}`}
          from={Math.round(p.en_s * fps)}
          durationInFrames={Math.max(1, Math.round(p.duracion_s * fps))}
        >
          <Audio src={staticFile(p.src)} volume={p.volumen ?? 1} />
        </Sequence>
      ))}

      {musica ? (
        <Audio
          src={staticFile(musica.src)}
          volume={(f) =>
            interpolate(
              f,
              [durationInFrames - 1.5 * fps, durationInFrames],
              [musica.volumen ?? 0.25, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            )
          }
        />
      ) : null}
    </AbsoluteFill>
  );
};
