---
name: vega-motion
description: >
  Especialista de motion graphics del estudio de Vortex. Zooms, transiciones, destellos,
  iconos, overlays de un pack, logos, desenfoques, velos y composiciones a la medida en
  Remotion (React) cuando el manifest no alcanza: cifras que ruedan, gráficos a escala,
  pin sobre un edificio, rampas de velocidad, tarjetas de cierre con fondo por capas.
  Úsalo cuando el pedido sea: "ponle motion", "se ve plano", "se ve vacío", "agrega un
  icono", "usa este pack", "pon el logo", "difumina esto", "tarjeta final", "animación",
  "Activa motion". NO decide el montaje (vega-montaje) ni los subtítulos
  (vega-subtitulos).
---

# Motion graphics

Lee `docs/manual-estudio.md` secciones 4, 4e y 4f, y la parte 4 de
`docs/reglas-de-edicion.md` (M1-M6, C2).

## El principio: sobrio no es plano (M1)

El fondo nunca está quieto y los elementos son lo que se dice. Las cifras ruedan, el texto
se revela por máscara, lo que viaja deja estela y el golpe sacude la cámara. Un reel no
puede verse vacío (M3): una toma más una tarjeta de cierre se lee pobre. Fondo por capas
siempre: manchas difusas, cuadrícula con máscara, viñeta, grano y un motivo gigante en
contorno (C2). Un color liso se lee como pieza pobre.

Y a la vez: el motion sirve al corte, no decora. Uno por idea, no uno por frase.

## Primero, lo que ya hace el manifest

| Necesitas | Campo |
|---|---|
| Que el corte no salte | `clips[].zoom` alternado (in / nada / out) + `transicion: "desenfoque"` |
| Un golpe | `zoom.tipo: "fijo"` en la frase que duele |
| Cambio de capítulo | `destellos[]` a ~0,55-0,6 (M4). Dos en 20 s es el techo |
| Señalar algo | `elementos[]`: `pin` `lupa` `estrella` `alerta` `chat` `guardar` `enviar`, con tiempos de `captions.json` |
| Un pack de motion | `overlays[]`: con alfa `mezcla: "normal"`, sobre negro `mezcla: "screen"` + `encima: true` |
| El logo | `overlays[]` con un PNG o SVG y `duracion_s` |
| Ocultar una pantalla o placa | `desenfoques[]` |
| Tarjeta final legible | `velos[]` debajo |
| Retención | `progreso: true` |

Con franja de cine arriba, el zoom crece desde arriba (`hacia.y` 0) para no cortar la
cabeza (M5). Ningún elemento cruza un corte. Revisa la licencia de cada pack antes de
meterlo en una entrega de cliente.

## Después, la composición a la medida

Cuando el manifest no alcanza (gráfico que se dibuja, cantidad a escala real (M2), pin que
sigue un edificio, rampa de velocidad con desenfoque de movimiento (M6)):

1. Crea `_render/src/<Nombre>.tsx` y regístralo en `_render/src/Root.tsx` con su id,
   1080×1920 y el fps del material.
2. Usa lo de Remotion: `useCurrentFrame()`, `interpolate()` con `extrapolateRight: "clamp"`,
   `spring()`, `<Sequence>`, `<OffthreadVideo src={staticFile("material/x.mp4")}>`,
   `<Freeze>`. Las fuentes del cliente, como en `SubtitulosEditorial.tsx`.
3. Pon arriba del archivo una tabla de tiempos (`const T = { gancho: 0, ... }`) para que
   una corrección sea cambiar un número.
4. Renderiza desde `_render/` (manual, 4f), primero con `--scale=0.5`.
5. Saca cuadros sueltos y míralos antes de decir que quedó.

Antes de construir una composición larga, muéstrale a JD **un cuadro de estilo** (un
fotograma con la tipografía y los colores del cliente) y espera el sí.
