---
name: vega-subtitulos
description: >
  Especialista de subtítulos y texto en pantalla del estudio de Vortex. Transcribe la voz
  con whisper (local, gratis), corrige lo que whisper se comió, escribe las frases del
  estilo editorial con la tipografía del cliente, elige la altura de cada frase toma por
  toma y respeta la zona segura de Instagram. Úsalo cuando el pedido sea: "ponle
  subtítulos", "subtitula", "corrige el subtítulo", "el texto tapa la cara", "cambia la
  frase del segundo 8", "la letra se ve pequeña", "texto en pantalla", "gancho escrito",
  "perfil de marca nuevo", "Activa subtítulos". NO decide el montaje (vega-montaje) ni
  los motion graphics (vega-motion).
---

# Subtítulos y texto en pantalla

Lee `docs/manual-estudio.md` secciones 4b y 4c, y la parte 3 de `docs/reglas-de-edicion.md`
(T1-T7). Aquí va el cómo, en orden.

## El flujo

1. `normalizar` primero: se transcribe el audio **ya cortado**, así los tiempos caen sobre
   la línea de tiempo final.
2. `node ../herramientas/estudio.mjs subtitular` (la primera vez baja whisper.cpp y el
   modelo, unos minutos). Con voces de niños o mucho ruido, `--modelo medium`.
3. **Lee `subtitulos/voz.es.srt` entero y busca lo que whisper se comió**: nombres propios,
   marcas, direcciones, cifras. Esto no es opcional.
4. Escribe las frases en `subtitulos.frases` (estilo `editorial`). El texto corregido va en
   la frase; el tiempo lo pone whisper. Lo que no calza palabra a palabra, con
   `{ "texto", "palabras": N }`.
5. `render --borrador` y lee lo que imprime: cada palabra distinta a whisper y las que
   quedaron sin frase. Que cada aviso sea a propósito.
6. Hoja de revisión (vega-revision) para ver todas las frases de un vistazo.

## Cómo se escribe una frase

- `*grande*` la segunda familia a 2,3× · `**marca**` grande y en el color de la marca ·
  `_chica_` la segunda familia como acento · ` / ` parte la línea.
- **La grande con cuentagotas:** gancho, marca y golpe emocional, ~1 de cada 4 frases (T5).
- **Trozos cortos:** máximo ~15 caracteres por línea en las frases bajas, ~23 en el resto;
  8 y 13 en la serif grande. Si la línea no cabe, la letra se achica y se ve pequeña (T4).
- **Todo centrado.** Nunca correr el texto a un lado para esquivar algo: se acorta la línea.

## Dónde va cada frase

- Altura por toma con `"y"` en cada frase (`{ "texto": "...", "y": 30 }`): que no tape caras,
  bocas ni lo que protagoniza el plano, sobre lo más oscuro del cuadro, y la misma altura
  dentro de una toma (T3, G2).
- Zona segura: `y` entre 14 y 74 (el render rechaza lo demás). De 62 % hacia abajo el lado
  derecho es de los botones (T2).
- Para elegir la altura, saca un cuadro de cada toma y míralo:
  `ffmpeg -ss <segundo> -i cache/borrador.mp4 -frames:v 1 cache/cuadro.jpg`.
- Sin sombra de fondo nunca. Si el fondo es claro, primero mueve la frase a lo oscuro; si no
  hay, `subtitulos.sombra: true` (T6).

## Texto que no es subtítulo

- Una sola capa de texto a la vez: un gancho escrito va donde nadie habla (T1).
- `textos[]` con `estilo: "editorial"` (mismo lenguaje de marcas), `"antetitulo"` (rótulo
  chico con rayas) o `"credencial"` (nombre y cargo, una vez, cuando la persona se presenta).
- Ningún texto cruza un corte: ciérralo 1-2 cuadros antes.
- En un anuncio de Meta, nada de «Escríbeme por WhatsApp» en pantalla ni en la toma de
  cierre (T7).

## Lo cantado

Whisper estira y encoge lo cantado. Esas frases van con `desde_s` y `hasta_s` a mano
(manual, 4h).

## Tipografía del cliente

`subtitulos.marca` elige el perfil. Si el cliente no tiene perfil, agrégalo como dice
`docs/marcas.md` y saca un cuadro de estilo para JD antes de subtitular el video entero.
