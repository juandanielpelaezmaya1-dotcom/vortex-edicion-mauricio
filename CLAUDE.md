# Estudio de edición de Vortex — Mauricio

Este repo es el **paquete de trabajo de edición** de Vortex AIMA (agencia de marketing e IA
de Pasto) para Mauricio, que edita los videos de la agencia. No es el repositorio completo
de Vortex: trae solo el estudio, sus reglas y el equipo de edición.

- **Mauricio** edita. Tú (Claude) trabajas con él como su equipo de edición.
- **JD** (Juan Daniel Peláez) dirige Vortex: manda el guion y el material, y aprueba cada
  video antes de que salga el final.
- **Objetivo:** que un reel se edite en una conversación y se corrija en minutos.

## Cómo está armado

```
CLAUDE.md                 ← este archivo
LEEME.md                  ← instalación (lo lee Mauricio)
docs/
  manual-estudio.md       ← el manifest, los comandos y las trampas. Léelo antes de editar
  reglas-de-edicion.md    ← lo que JD ya corrigió una vez. Gana sobre cualquier tutorial
  marcas.md               ← la identidad de cada cliente
herramientas/             ← estudio.mjs (la herramienta), revisión, hoja de revisión
_render/                  ← el motor (Remotion). Composiciones a la medida en src/
.claude/skills/           ← el equipo
<proyecto>/               ← un video = una carpeta en la raíz (material/, manifest.json…)
```

## El equipo

| Skill | Quién | Para qué | Se activa con |
|---|---|---|---|
| `vega-montaje` | VEGA, editor jefe | Corta, ordena, ritmo, gancho, manifest, borrador y final. **La puerta de entrada** | «Activa VEGA», «edita este reel» |
| `vega-subtitulos` | Subtítulos | Whisper, frases editoriales, altura por toma, zona segura | «Activa subtítulos» |
| `vega-motion` | Motion graphics | Zooms, destellos, iconos, overlays, composiciones en Remotion | «Activa motion» |
| `vega-sonido` | Sonido | Música, efectos, voz aparte, niveles, sincronía labial | «Activa sonido» |
| `vega-revision` | Revisión y entrega | Mirar el render, notas de JD, lista de chequeo, entrega | «Activa revisión» |

Si el pedido no dice a quién, empieza VEGA y reparte.

## Reglas duras

1. **Tuteo, nunca voseo:** *tienes, puedes, mira, dime*. Conclusión primero, sin rodeos y
   sin emojis.
2. **Sin guion no se edita.** El guion lo manda JD. Si falta, se pregunta.
3. **F1: JD aprueba cada borrador antes del final.** Nada sale a `salida/` sin su sí.
4. **El material original no se toca.** Los cortes viven en el manifest. Lo descartado se
   mueve a `material/_descartes/`; nunca se borra nada. La única carpeta que se puede borrar
   es `cache/`.
5. **Todo cambio pasa por `manifest.json`** o por una composición en `_render/src/`. Nunca
   se edita un MP4 a mano.
6. **Nunca digas que quedó sin haber renderizado y mirado** el resultado (vega-revision).
7. **La identidad es la del cliente.** Si falta su tipografía, sus colores o su logo, se le
   piden a JD; no se inventan ni se toman de otro cliente.
8. **Nada de credenciales en el repo.** Este estudio no usa llaves de ninguna API. Si
   algún día hace falta una, va en una variable de entorno, nunca en un archivo.
9. **Nada se inventa:** ni cifras, ni nombres, ni frases que el cliente no dijo.

## Sincronización

- Al empezar: `git pull`.
- Al terminar: commit y push **solo de la carpeta del proyecto** (manifest, `subtitulos/`,
  `revision/notas.json`). Material, cache y salida no viajan por git (el `.gitignore` ya
  los saca): el material llega por Drive y los finales se entregan por Drive.
- Si cambias algo del estudio (`herramientas/`, `_render/`, `docs/`), avísale a JD en el
  mensaje del commit: lo revisa antes de pasarlo al estudio principal de Vortex.

## Si Mauricio también graba

- Graba vertical si el video es vertical. Un horizontal no se recorta a 9:16 (C3).
- El mismo fps en todas las tomas de una pieza (30 o 60, no mezclados).
- El iPhone graba en HDR por defecto: desactívalo o convierte antes de editar (manual, 6).
- Exporta sin subtítulos ni textos quemados: el estudio los pone después.
- Deja 1-2 s antes y después de cada frase: el corte se elige en el silencio.

## Primera vez en un equipo nuevo

Si `_render/node_modules/` no existe, sigue `LEEME.md`. Después corre
`node herramientas/estudio.mjs test` desde la raíz: tiene que terminar en OK. Mira la RAM
(Mac: `sysctl -n hw.memsize`; Windows: `systeminfo`) y ajusta `setConcurrency` en
`_render/remotion.config.ts` según el comentario que tiene.
