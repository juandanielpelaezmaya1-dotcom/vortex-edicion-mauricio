# Manual del estudio de edición

Aquí se **edita** el material grabado hasta convertirlo en el video que se publica. El
video no se arrastra en una línea de tiempo: se **describe** en un archivo
(`manifest.json`) y la herramienta lo arma. Cambiar un texto o el orden de dos clips es
editar una línea y volver a renderizar.

> El guion llega hecho (lo manda JD). Aquí solo se corta, monta y exporta.

## 1. Contexto

- **Qué es:** el estudio de edición de Vortex. Entra material grabado y sale un MP4 listo
  para Instagram, TikTok o YouTube.
- **Quién:** tú, con el equipo de skills de `.claude/skills/` (ver `CLAUDE.md`).
- **Objetivo:** que un reel se edite en una conversación y se re-edite en minutos.

## 2. Stack

| Pieza | Dónde | Rol |
|---|---|---|
| Remotion 4.0.512 | `_render/` | Motor de composición: pone clips, textos y música en la línea de tiempo |
| ffmpeg / ffprobe | instalados en el sistema | Inventario del material y cortes (los clips cortados se guardan en `cache/`) |
| `herramientas/estudio.mjs` | raíz del repo | La herramienta principal. Node sin dependencias |
| whisper.cpp | `_assets/modelos/` (se baja solo la primera vez) | Transcribe la voz para los subtítulos. Local y gratis |
| `herramientas/revision.py` | raíz del repo | Hoja de revisión: un cuadro por frase y por texto (ver 4d). Python + Pillow |
| `herramientas/borrar-subtitulos.py` | raíz del repo | Borra subtítulos **quemados** (ver 4g). Python + OpenCV. Plan B, no es parte del flujo normal |
| Proyectos | `<slug>/` en la raíz | Un proyecto = un video |

**Anatomía de un proyecto:**

```
mvb-reel-la-mango/
├── material/        ← lo grabado, tal cual salió de la cámara. Nunca se toca
├── manifest.json    ← EL video descrito: qué clip, qué pedazo, qué texto, qué música
├── subtitulos/      ← lo que transcribió whisper (captions.json + .srt)
├── revision/        ← las correcciones (notas.json)
├── cache/           ← clips ya cortados + borradores. Regenerable, se puede borrar
└── salida/          ← los MP4 finales que se entregan
```

Por git viajan `manifest.json`, `subtitulos/` y `revision/notas.json`. El material, el
cache y la salida no (pesan): el material llega y la salida se entrega por Drive.

## 3. Los comandos

Se corren **desde la carpeta del proyecto**:

| Comando | Qué hace | Cuándo |
|---|---|---|
| `node ../herramientas/estudio.mjs probe` | Tabla del material: duración, resolución, fps, si trae audio | Apenas llega material nuevo |
| `node ../herramientas/estudio.mjs normalizar` | Corta cada clip según el manifest y lo deja en `cache/` | Después de escribir o cambiar cortes en el manifest |
| `node ../herramientas/estudio.mjs subtitular` | Transcribe la voz **ya cortada** y deja `subtitulos/captions.json` + `.srt`. `--modelo medium` para voces difíciles (niños, ruido) | Después de `normalizar`, si el video lleva subtítulos |
| `node ../herramientas/estudio.mjs render --borrador` | Un solo MP4 9:16 a media resolución, rápido, en `cache/borrador.mp4` | Para revisar el montaje |
| `node ../herramientas/estudio.mjs render --borrador --hd` | El mismo borrador a resolución completa (~4× más lento) | Cuando se va a juzgar **calidad de imagen**, no solo montaje: a media resolución todo se ve blando |
| `node ../herramientas/estudio.mjs revisar` | Abre el borrador en un iPad o un navegador para corregirlo dibujando sobre el cuadro (ver 4d) | Después del borrador |
| `node ../herramientas/estudio.mjs render` | Los dos finales (9:16 y 16:9) a `salida/` | Solo cuando JD aprobó el borrador |

`node herramientas/estudio.mjs test` (desde la raíz del repo) verifica el motor entero
con material sintético en `_prueba/`. Si algo del estudio se rompe, ese es el primer
comando a correr.

## 4. El manifest — el contrato

```json
{
  "slug": "mvb-reel-la-mango",
  "clips": [
    { "archivo": "material/IMG_0231.MOV", "in_s": 2.0, "out_s": 5.5 },
    { "archivo": "material/IMG_0232.MOV", "in_s": 0,   "out_s": 3.2 }
  ],
  "musica": { "archivo": "material/track.mp3", "volumen": 0.25 },
  "textos": [
    { "texto": "Tu ropa habla antes que tú", "desde_s": 0, "hasta_s": 2.8, "posicion": "abajo" }
  ]
}
```

| Campo | Obligatorio | Qué es |
|---|---|---|
| `slug` | no | Nombre de los archivos de salida. Por defecto, el de la carpeta |
| `fps` | no | El del material (`23.976` si la cámara graba así). Por defecto 30. Pasar 24 a 30 duplica un cuadro de cada cuatro y los paneos dan tirones |
| `clips[].archivo` | **sí** | Ruta **relativa a la carpeta del proyecto** |
| `clips[].in_s` / `out_s` | no / no | Segundo donde entra y sale el corte. Sin ellos, el clip entero |
| `musica.archivo` | no | Baja sola 1,5 s antes del final. `volumen` 0-1 (defecto 0.25) |
| `textos[]` | no | `posicion`: `arriba` · `centro` · `abajo` (defecto). Entra y sale con fundido |
| `subtitulos` | no | `{ "activo": true, "acento": "#7cb9f2" }`. Exige haber corrido `subtitular` |
| `subtitulos.estilo` | no | `"editorial"`: frases escritas por el editor en `subtitulos.frases`, dos familias (ver 4b). Sin él, palabra por palabra con acento |
| `subtitulos.frases[].desde_s` / `hasta_s` | no | Tiempo a mano, sin whisper: para lo cantado (ver 4h). No consume palabras de whisper. **`hasta_s` solo** (sin `desde_s`) deja el tiempo de whisper pero cierra la frase ahí: para que no se meta en la toma siguiente |
| `subtitulos.pos` | no | `{ "y": 70 }` — altura del centro de la banda, en % del alto. Sin ella, 18 % desde abajo. Solo `y`: la banda va de lado a lado y siempre centrada |
| `subtitulos.marca` | no | La tipografía del cliente para el estilo `editorial` (ver 4b): `"mi-vieja-burger"`. Sin ella, Dejaste Huella (Poppins + Playfair). Los perfiles viven en `MARCAS` de `_render/src/SubtitulosEditorial.tsx` |
| `subtitulos.sombra` | no | `true` le pone a los subtítulos editoriales una sombra suave en las letras. Sin ella (el defecto) el blanco se pierde en paredes y ventanas claras |
| `efectos[]` | no | `{ "archivo": ..., "en_s": 3.2, "volumen": 0.6 }`. Un efecto por corte, si hace falta |
| `elementos[]` | no | `{ "icono": "pin", "desde_s": 1.4, "hasta_s": 2.8 }`. Iconos: `pin` `lupa` `estrella` `alerta` `chat` `guardar` `enviar` (los dos del CTA, con la forma de los botones de Instagram) |
| `clips[].zoom` | no | `{ "tipo": "in", "hacia": {"x":30,"y":25}, "intensidad": 1.15 }`. `hacia` es la zona que crece; sin ella, el centro. `tipo`: `in` · `out` · **`fijo`** (punch-in: entra ya acercado y no se mueve) |
| `clips[].transicion` | no | Cómo ENTRA el clip: `{ "tipo": "desenfoque", "duracion_s": 0.13 }`. Tipos: `disolver` `desenfoque` `deslizar` (con `desde`: izq/der/arriba/abajo) `escala` |
| `textos[].animacion` | no | `fundido` (defecto) · `subir` · `resorte` |
| `textos[].estilo` | no | `credencial` lo pinta como rótulo de TV (caja, barra de acento, a la izquierda). Con `"Nombre \| Cargo"` parte en dos líneas |
| `progreso` | no | `true` pinta una barra fina de avance arriba. En un reel es retención |
| `overlays[]` | no | Motion graphics encima del video (ver 4f): `{ "archivo": "material/mg/anillo.webm", "en_s": 1.4, "mezcla": "screen", "pos": {...}, "escala": 0.6, "opacidad": 0.9, "encima": true }`. La duración se mide del archivo. **Una imagen (PNG, SVG) también entra**: así va el logo del cliente, y como no tiene duración, lleva `duracion_s` |
| `textos[].pos` / `elementos[].pos` | no | `{ "x": 28, "y": 34 }` en % del cuadro. Manda sobre `posicion`: es el punto exacto señalado en la revisión |
| `destellos[]` | no | `{ "en_s": 3.2, "duracion_s": 0.25, "color": "white", "intensidad": 0.55 }`. Flash de cámara: sube de golpe, baja despacio. Va bajo, ~0,55-0,6: a 0,85 sobre imagen cálida y oscura pega como error de cámara |
| `clips[].velocidad` | no | `0.5` cámara lenta (con material a 60 fps usa cuadros reales), `2` al doble. La toma dura `(out_s-in_s)/velocidad` en la línea de tiempo. Rango 0,25-4 |
| `clips[].volumen` | no | `0` silencia la toma. Va con `pistas`: cuando la voz va aparte, el sonido de las tomas estorba |
| `pistas[]` | no | Voz aparte de las tomas (ver 4h): `{ "archivo": "material/x.MOV", "in_s": 34.4, "out_s": 48.2, "en_s": 21.3, "volumen": 1 }`. Se corta, se limpia y se nivela en `normalizar` |
| `textos[].estilo: "editorial"` | no | Título en el lenguaje de los subtítulos editoriales (mismas marcas `*grande*` `**acento**` `_chica_` ` / `), palabras escalonadas. Altura con `pos.y` |
| `textos[].sombra` | no | `true` con `estilo: "editorial"`: la misma sombra suave de `subtitulos.sombra` |
| `textos[].estilo: "antetitulo"` | no | Rótulo chico en mayúsculas espaciadas y en el acento, con una raya que se dibuja a cada lado. Altura con `pos.y` |
| `desenfoques[]` | no | `{ "desde_s": 3, "hasta_s": 7.5, "x": 30, "y": 55, "w": 45, "h": 25, "fuerza": 24 }`: difumina ese rectángulo (esquina superior izquierda + tamaño, en % del cuadro 9:16) en ese tramo. Para una pantalla con datos, una placa, un teléfono pintado. No sigue al objeto: en un POV que se mueve, rectángulo generoso o varios tramos cortos |
| `velos[]` | no | `{ "desde_s": 40, "hasta_s": 46, "opacidad": 0.55, "desenfoque": 14, "color": "#1E5A48" }`. Oscurece y desenfoca el video debajo de una tarjeta final |
| `color` | no | `{ "contraste": 1.06, "saturacion": 1.12, "brillo": 1.02 }`. Corrección global, para material nublado y plano |
| `acento` | no | Color de la marca del video: iconos, barra de progreso, antetítulos y `**acento**`. Sin él, el azul de Vortex y el dorado de los subtítulos |
| `formatos` | no | `["9x16"]` para un reel sin versión horizontal. Por defecto los dos |

Los tiempos de `textos` corren sobre el **video final**, no sobre el clip original.

## 4b. Subtítulos (whisper local, gratis)

Se transcribe **el audio de los clips ya cortados**, no el material original: así el
tiempo de cada palabra cae sobre la línea de tiempo final y no hay que recalcular nada
si se cambia el orden.

1. `normalizar` → 2. `subtitular` → 3. **leer `subtitulos/voz.es.srt` y corregir** →
4. `render`.

El paso 3 no es opcional: whisper acierta casi todo pero se come los nombres propios
(escribió "Daniel Pelaes"). Si se corrige el SRT hay que corregir **el mismo texto en
`captions.json`**, que es el que consume Remotion.

El estilo por defecto es palabra por palabra: la que suena se pinta con el acento de
Vortex (`#7cb9f2`) y da un saltito. El resto es texto blanco con sombra.

**Estilo `editorial`.** Las frases las escribe el editor en el manifest y `render` las
cuadra en orden con las palabras de whisper: el **texto** sale de la frase (ahí se
corrige "Pazto" sin tocar `captions.json`) y el **tiempo**, de whisper. `render` lista
cada palabra que no coincide y las de whisper que quedaron sin frase, para revisar que
sea a propósito.

```json
"subtitulos": { "activo": true, "estilo": "editorial", "pos": { "y": 63 }, "frases": [
  "cuando su mascota / *fallece*",
  { "texto": "**Dejaste Huella**", "palabras": 3 },
  { "texto": "*Carrera 41B* / Nº 17A-182 · El Dorado", "palabras": 7 }
] }
```

- `*palabra*` va en la segunda familia a 2,3× (puede abarcar varias palabras) ·
  `**palabra**` además en el color de la marca · `_palabra_` la segunda familia **chica**,
  apenas menor que la base, como acento · ` / ` parte la línea · el resto va en la base.
- `{ "texto", "palabras": N }` cuando el texto no calza palabra a palabra con whisper
  (una marca que whisper parte en tres, una dirección): cubre N palabras y entra entera.
- **Variedad, no fórmula:** la grande solo de vez en cuando, en el gancho, la marca y los
  golpes emocionales (~1 de cada 4 frases). El resto alterna frases solo en la base y
  frases con la chica de acento. Si todo es grande, nada pesa.
- **Trozos cortos, letra grande:** una línea que no cabe se achica sola, y eso es lo que
  se ve "pequeño". La frase se parte en más porciones y en más líneas hasta que cada línea
  entre a tamaño completo: **máximo ~15 caracteres** por línea en las frases bajas (las que
  llegan a los botones) y ~23 en el resto; en la serif grande, 8 y 13.
- Cada palabra entra cuando se dice (fundido, sube y se enfoca), sin rebote. **Sin sombra
  de fondo**: ensucia la imagen. Sobre fondos muy claros el blanco cuesta: revisar esas tomas.
- **Posición por toma, no fija:** `{ "texto": "...", "y": 30 }` en cada frase. Se elige
  mirando el cuadro: que no tape caras ni lo que protagoniza el plano (la mascota, una
  placa, el letrero), sin alejarse de más, y sobre lo más oscuro que haya. Dentro de una
  misma toma, la misma altura. `pos.y` (63) solo es el valor por defecto.
- **Zona segura de Instagram:** nada por encima del 8 % ni por debajo del 78,6 % del alto,
  márgenes de 5,5 % a los lados, y del 62 % hacia abajo el lado derecho (desde el 77 % del
  ancho) es de los botones. `render` rechaza `y` fuera de 14-74.
- **Todo centrado: el texto NUNCA se corre a los lados.** Cuando el bloque llega a la zona
  de los botones se acota el ancho al 54 % centrado; lo que se ajusta es el largo de las
  líneas, no la posición. La variación de altura sí se mantiene.
- Las fuentes van dentro del render (`_render/src/fuentes/`, OFL y Apache): no dependen
  del computador.

**Perfil de marca por cliente (`subtitulos.marca`).** El lenguaje es el mismo para todos
(base sans, la segunda familia chica o grande, `**…**` para la marca); cada cliente cambia
familias, escala y cómo se pinta el acento. Los perfiles están en `MARCAS` de
`_render/src/SubtitulosEditorial.tsx`; agregar un cliente es una entrada más y sus fuentes
en `_render/src/fuentes/` (con su licencia al lado). Las identidades de cada cliente están
en `docs/marcas.md`.

| Perfil | Base | `_chica_` | `*grande*` | `**marca**` |
|---|---|---|---|---|
| (sin `marca`) Dejaste Huella | Poppins SemiBold, 6 % del ancho | Playfair itálica 1,06× | Playfair itálica 2,3× | Playfair grande en dorado |
| `mi-vieja-burger` | Fjalla One MAYÚSCULAS, 7,6 % | Permanent Marker 1×, torcida -4° | Marker 1,65×, torcida | Marker blanca sobre **cinta** `#F24405`, la línea torcida |

Con Mi Vieja Burger va `sombra: true` (el mural es naranja y la madera clara) y su sello
como overlay arriba a la izquierda (`pos` 12/11,6, `escala` 0,13). Fjalla es angosta y la
Marker ancha: en las frases bajas caben ~16 caracteres de Fjalla, y una palabra de marca
larga en cinta ("MI VIEJA BURGER") solo cabe entera si la frase va por encima del 62 % del alto.

## 4c. Iconos y cortes precisos

**Los cortes salen de `silencedetect`, no de whisper.** Whisper da los tiempos de las
palabras pero se desborda en los bordes (llegó a decir que la voz terminaba en el
segundo 6,3 de un clip de 4,36). Para decidir dónde entra y sale un clip:

```
ffmpeg -i clip.mov -af "silencedetect=noise=-35dB:d=0.12" -f null -
```

`in_s` = primer `silence_end` − 0,08 · `out_s` = último `silence_start` + 0,20. El
margen de atrás es más grande a propósito: cortar justo en la última sílaba suena
guillotinado.

**Los iconos son SVG dibujados en `Elementos.tsx`**, no archivos. Entran con un rebote,
respiran mientras están y se van con fundido, en el acento de la marca. Se colocan con
los tiempos reales de `subtitulos/captions.json`, nunca a ojo. Regla: **uno por idea,
no uno por frase** — cinco en 21 segundos es el techo antes de que estorben.

## 4d. Revisión: dibujar sobre el cuadro

Las correcciones no se describen por chat: se **señalan** sobre el cuadro. Quien revisa
dibuja dónde y escribe qué; Claude lo traduce a manifest y vuelve a renderizar.

```
render --borrador  →  revisar  →  dibujar en el iPad o el navegador  →  aplicar  →  render --borrador
```

1. Desde la carpeta del proyecto: `node ../herramientas/estudio.mjs revisar`
2. Imprime una URL tipo `http://192.168.x.x:7777`. Se abre en el navegador del mismo
   computador o en un iPad **conectado a la misma WiFi**. La pantalla está pensada para el
   iPad en horizontal: visor al centro, tintas a la izquierda, la corrección a la derecha
   y la línea de tiempo abajo.
3. Pausa el cuadro, dibuja el círculo o la flecha, escribe la nota y guarda.
4. Cada corrección cae en `revision/notas.json` + `revision/nota-NN.png` (el cuadro con
   el trazo encima).

**Si JD revisa desde lejos** (no está en tu WiFi): le mandas `cache/borrador.mp4` y te
responde con el segundo y la nota. Esas notas las pasas tal cual a Claude.

**Lo que trae cada corrección:**

| Campo | Para qué sirve |
|---|---|
| `t_s` | El segundo exacto del video final donde se pausó. Ahí caen `desde_s`/`en_s` |
| `texto` | Qué hay que corregir |
| `centro_pct` | El centro de lo dibujado, en %. **Se pega tal cual** en `pos` o en `zoom.hacia` |
| `caja_pct` | El área encerrada. Sirve para calibrar cuánto zoom hace falta |
| `trazos[]` | Los puntos, en %, por si hace falta leer la forma |
| `imagen` | El PNG anotado. **Míralo siempre**: la palabra sola no dice lo que el dibujo sí |

**Al aplicar una corrección, marcarla `"aplicada": true` en `notas.json`.** Es el único
registro de qué se atendió y qué quedó pendiente.

Reglas de la pantalla: el dedo no dibuja, solo el lápiz (y el mouse en el computador), así
el dedo sirve para mover el video; mover el tiempo limpia el lienzo (un trazo pertenece a
un cuadro); el primer trazo fija el segundo de la corrección y pausa el video.

**Hoja de revisión.** Antes de mandar un borrador, mira el render, no el log:

```
.venv/bin/python herramientas/revision.py <carpeta del proyecto>     (Windows: .venv/Scripts/python)
```

Deja `cache/revision.jpg`: un cuadro por página de subtítulos y por texto, con el texto
rotulado debajo. Ahí se ve de un vistazo si algo tapa una cara, se sale de la zona segura
o quedó en una toma equivocada.

## 4e. Animación: qué usar y cuándo

El material de una entrevista suele ser **el mismo encuadre en todas las tomas**. Sin
nada, cada corte se lee como salto (*jump cut*). El trabajo de la animación acá no es
decorar: es que un corte parezca una decisión.

| Recurso | Para qué sirve de verdad |
|---|---|
| **Zoom alternado** entre tomas | Lo primero que hay que hacer. Si dos tomas seguidas llevan el mismo movimiento, el corte sigue saltando. Alternar in / nada / out |
| **`zoom.tipo: "fijo"`** (punch-in) | El golpe. Entra ya acercado, sin animar. Va en la frase que duele, no en cualquier lado |
| **`transicion: "desenfoque"`** | El mejor disimulo para un jump cut: 4 cuadros de desenfoque y el ojo no alcanza a comparar los dos encuadres |
| **Destellos** | Solo en cambios de capítulo del guion (problema → solución). Dos en 20 s es el techo |
| **`estilo: "credencial"`** | La presentación del que habla. Una vez, cuando dice su nombre |
| **`progreso`** | Retención: se ve cuánto falta |

**Regla dura: la transición NO solapa clips.** Es una animación del clip que entra, no
un fundido entre dos. Un solape de verdad acortaría el video y **desincronizaría los
subtítulos y los iconos**, cuyos tiempos corren sobre la línea de tiempo final.

**Los iconos y textos no deben cruzar un corte.** Un elemento que sobrevive al corte
ancla el ojo justo donde la imagen salta y hace el jump cut más visible. Cerrarlos
1-2 cuadros antes.

## 4f. Motion graphics de un pack, y composiciones a la medida

Un pack comprado se puede usar tal cual. Lo que decide si sirve es **el formato**, y solo
hay dos familias:

| Familia | Qué es | Cómo se usa |
|---|---|---|
| **Con canal alfa** | WebM VP9 con alfa · MOV ProRes 4444 · MOV HEVC con alfa | `mezcla: "normal"` (por defecto). Se ve tal cual, con su transparencia |
| **Rodado sobre negro** | Fugas de luz, partículas, glitch, destellos | `mezcla: "screen"` — el negro desaparece y solo queda la luz |

**Lo que NO se puede usar:** proyectos de After Effects (`.aep`), plantillas de Premiere
(`.mogrt`) ni nada que exija abrir Adobe. Eso hay que **exportarlo antes** a una de las
dos familias de arriba.

**Colocación:** sin `pos` el overlay cubre el cuadro; con `pos` se coloca en ese punto a
`escala` del ancho. Va **debajo de textos y subtítulos** salvo `encima: true`. Los de luz
(`screen`) suelen querer `encima: true`.

**Ojo con la RAM.** Cada overlay es un video más decodificándose en paralelo. Dos o tres
solapados a la vez es el techo sensato; si un render empieza a morir por *timeout*, el
primer sospechoso es esto.

**Ojo con la licencia.** Un pack para uso personal no cubre un video facturado a un
cliente. Antes de meter un gráfico en una entrega, mirar su licencia.

**Composición a la medida.** Cuando la pieza pide algo que el manifest no hace (una rampa
de velocidad, un pin pegado a un edificio, un gráfico que se dibuja, una tarjeta de cierre
con motion propio), se escribe una composición de Remotion en `_render/src/<Nombre>.tsx`,
se registra en `_render/src/Root.tsx` con su id y se renderiza desde `_render/`:

```
node node_modules/@remotion/cli/remotion-cli.js render src/index.ts <Id> ../<proyecto>/cache/borrador.mp4 --public-dir=../<proyecto>
```

Con `--public-dir` apuntando al proyecto, `staticFile("material/x.mp4")` carga su material.
Agrega `--scale=0.5` para un borrador rápido. Si el render es largo y se pega por memoria,
se renderiza por partes con `--frames=0-449`, `--frames=450-899`… y se unen con el
`concat` de ffmpeg.

## 4g. Material que llega con subtítulos quemados

**Lo ideal es pedir el export sin subtítulos antes de empezar.** Se ahorran horas y el
material llega con más calidad (sin una generación de compresión). Esto es el plan B:

```
python3 -m venv .venv && .venv/bin/pip install opencv-python-headless numpy
.venv/bin/python herramientas/borrar-subtitulos.py material/x-original.mp4 material/x-limpio.mp4
```

Detecta el texto blanco y delgado centrado en la franja `--y0/--y1` (por defecto
1340-1476) y rellena con el fondo real de otros cuadros **de la misma toma**. Lo que no
encuentra así va con inpaint, que es lo que se nota (manchas y letras fantasma sobre texto
impreso). Tarda ~35 min por reel de 39 s. **Revisar siempre las tomas con texto impreso o
brillos** cuadro a cuadro antes de entregar. El original queda en `material/` y el
manifest parte del limpio.

## 4h. Voz aparte de las tomas (`pistas`)

Para cuando alguien canta o narra y la imagen tiene que ir a otra parte (tomas de apoyo sobre
una voz, un canto que empieza antes de que se vea a quien canta). La voz sale del archivo que
sea y se coloca en `en_s` de la línea de tiempo; las tomas llevan `"volumen": 0`.

- `normalizar` corta cada pista, le quita graves y ruido de fondo y la **nivela en dos
  pasadas**: mide la sonoridad y aplica una ganancia fija hacia -16 LUFS con un limitador a
  -1,5 dBTP. Con ganancia fija la dinámica queda como se grabó.
  - `"limpiar": false` se salta la limpieza (música, aplauso) pero **se nivela igual**: una
    canción masterizada llega ~10 dB por encima de una voz de campo.
  - `nivel_lufs` cambia el objetivo (-16).
  - `ganancia_db` fija se salta la medición: los tramos de **una misma canción** llevan la
    misma, o el intro suave y el coro quedan igual de fuertes y el coro pierde su golpe.
  - `fundido_s` (0,06) evita el clic del corte; con `[entrada, salida]` cada borde lleva el suyo.
- **Música que se apaga para que alguien cante:** la canción va en `pistas` en dos tramos (hasta
  el momento de la voz, y desde el punto de la canción que convenga), no en `musica`, que suena
  pareja todo el video.
- **Sincronía labial:** si la persona que canta está en pantalla, su toma y su pista tienen que
  ser el **mismo rango del archivo** y empezar en el **mismo segundo** de la línea de tiempo.
- **Lo cantado no se subtitula con whisper:** estira y encoge las palabras (le dio 22 s a un
  verso de 7). Las frases van con `desde_s`/`hasta_s` a mano. Si todas las frases llevan
  tiempo, `render` no pide `captions.json`.
- Cortar la pista solo en silencios: entre coplas o entre versos, nunca a mitad de palabra.

## 5. Reglas del estudio

1. **El material original no se toca.** Los cortes viven en el manifest; `material/`
   queda tal como llegó. Lo descartado se mueve a `material/_descartes/`, no se borra.
2. **Todo cambio pasa por el manifest** (o por la composición a la medida). Nada de editar
   el MP4 a mano: si el video no se puede reproducir desde el manifest, no es reproducible.
3. **Borrador antes de final, siempre.** El final se exporta cuando JD dijo que sí.
4. **`cache/` es la única carpeta que se puede borrar** — se reconstruye sola.
5. **Nombres de salida:** `<slug>_9x16_<AAAAMMDD>.mp4` y `<slug>_16x9_<AAAAMMDD>.mp4`.
   Los pone la herramienta; no renombrarlos a mano. Si la pieza tiene ID (`A1_`, `O3_`,
   `V2_`), el ID va al principio del `slug`.

## 6. Trampas ya pagadas (no volver a descubrirlas)

- **Concurrencia fija en `_render/remotion.config.ts`. Manda la RAM, no los cores.**
  Remotion la calcula por cores, abre 6 Chrome a 1080×1920 y con 8 GB se queda sin
  memoria: el render muere con *"Timeout exceeded rendering the component at frame N"*.
  Con 8 GB, 2; con 16 GB, 4; con 32 GB, 6.
- **Si el render final falla y al repetirlo pasa, fue memoria.** El final tiene 4 veces
  los píxeles del borrador: cierra Chrome y otras apps pesadas antes de exportar, o baja la
  concurrencia a 1.
- **Las rutas del manifest son relativas al proyecto** porque el render se lanza con
  `--public-dir=<carpeta del proyecto>`. Una ruta absoluta no carga.
- **El material de cámara a veces viene marcado horizontal y es vertical.** Graba 3840x2160
  y mete `rotation=-90` en los metadatos: la imagen real es 2160x3840. ffmpeg la aplica sola
  al decodificar, pero `ffprobe` reporta el ancho y alto crudos. `probe` ya lo corrige; si
  se lee ffprobe a mano, mirar `side_data_list[].rotation`.
- **El iPhone y las gafas Ray-Ban graban en HDR** (HLG, bt2020). Sin pasarlo a SDR bt709
  antes de editar, sale lavado. `probe` no lo dice; esto sí (HDR si sale `arib-std-b67` o
  `smpte2084`): `ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 material/IMG_1.MOV`
  `estudio.mjs` no lo convierte solo: conviértelo a un archivo nuevo y deja el original.
  - Mac: `avconvert --preset PresetHighestQuality --source material/IMG_1.MOV --output material/IMG_1-sdr.mov`
  - Windows (el ffmpeg de winget trae `zscale`):
    `ffmpeg -i material/IMG_1.MOV -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p" -c:v libx264 -crf 16 -c:a copy material/IMG_1-sdr.mp4`
- **Whisper no devuelve palabras, devuelve sub-palabras.** `unirPalabras()` en
  `Subtitulos.tsx` los une antes de paginar. No pintar los tokens directo.
- **Con audio de ambiente, los tiempos de whisper mienten hasta 2 s.** Por eso `subtitular`
  usa los tiempos DTW (`t_dtw`) y los **adelanta 200 ms**: sin el adelanto, la palabra
  aparece cuando ya se dijo.
- **El demuxer `concat` de ffmpeg resuelve las rutas contra la carpeta del archivo de
  lista**, no contra el proyecto. La lista lleva rutas absolutas.
- **Safari en iOS exige `Range` para mover el tiempo del video.** Por eso `revisar.mjs`
  responde 206 por partes, y el self-check lo verifica.
- **Un texto con `pos` cerca del borde se apila en una columna angosta.** El ancho se
  acota solo al espacio que queda hasta el borde (`2 × min(x, 100−x)`). Si te señalan una
  esquina y el texto es largo, muévelo hacia adentro y avisa — no lo dejes apilado.
- **En Windows, el `.cmd` de `node_modules/.bin` exige shell** y con shell los argumentos
  no se escapan. Por eso la herramienta llama al CLI por su entry `.js` con el mismo Node.
  No volver al `.bin`.
- **Un corte a medio cuadro hace temblar la toma.** Un `in_s` como `0.05` en material a
  30 fps cae entre dos cuadros y la toma se ve a 20 fps con tirones. `normalizar` redondea
  `in_s` al cuadro real (el cache viejo no se rehace solo: si una toma tiembla, bórrala de
  `cache/`).
- **Un export de CapCut esconde cortes que el detector no ve.** Dos planos casi iguales se
  pegan sin que salte. Antes de usar un tramo largo de un video ya editado, mirarlo cuadro
  a cuadro.
- **Calidad: se perdía en cuatro sitios a la vez, ya corregidos.** El normalizado va a
  crf 16 *medium*; Remotion captura cada cuadro en JPEG al 95; la salida va en `bt709`
  rango TV (si no, cada reproductor la pinta distinto); y `fps` en el manifest respeta el
  material. Con eso el borrador `--hd` queda a 1-2 niveles de 255 del original.

## 7. Cadencia

- **F1 (hoy)** — JD aprueba el borrador antes de cualquier export final.
- **F2** — propones cortes y textos desde el guion; JD revisa el borrador.
- **F3** — autonomía en lo no crítico: inventario del material, primer armado, versiones
  de prueba.
- **F4** — la tanda semanal se edita sola y JD revisa la tanda completa.

## 8. Qué NO tiene el estudio (y cuándo agregarlo)

| Falta | Se agrega cuando |
|---|---|
| Banco de efectos de sonido y música | JD decida licencia. El manifest ya los acepta (`efectos`, `musica`); faltan los archivos |
| Conversión HDR automática en `normalizar` | Llegue material HDR seguido |
| Lottie (`.json` de After Effects) | Un pack lo traiga y valga la pena: exige instalar `@remotion/lottie` |
| B-roll generado con IA | JD lo pida y con control de presupuesto |

Ninguna se construyó por adelantado: cada una es media hora el día que haga falta.
