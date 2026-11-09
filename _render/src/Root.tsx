import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { FPS, Reel, ReelProps, duracionTotal } from "./Reel";

// La duracion sale de los clips del manifest (estudio.mjs pasa los props).
const calcular: CalculateMetadataFunction<ReelProps> = ({ props }) => ({
  fps: props.fps ?? FPS,
  durationInFrames: duracionTotal(props.clips ?? [], props.fps ?? FPS),
});

const vacio: ReelProps = { clips: [] };

// Las dos composiciones del estudio. Una pieza con motion a la medida va en su propio
// archivo de src/ y se registra aqui abajo con su id (ver docs/manual-estudio.md, 4f).
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Reel9x16" component={Reel} defaultProps={vacio} calculateMetadata={calcular}
      durationInFrames={FPS} fps={FPS} width={1080} height={1920} />
    <Composition id="Reel16x9" component={Reel} defaultProps={vacio} calculateMetadata={calcular}
      durationInFrames={FPS} fps={FPS} width={1920} height={1080} />
  </>
);
