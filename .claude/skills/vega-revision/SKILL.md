---
name: vega-revision
description: >
  Especialista de revisión y entrega del estudio de Vortex. Mira el render (no el log)
  antes de decir que quedó, arma la hoja de revisión con un cuadro por frase, abre la
  pantalla para corregir dibujando sobre el cuadro, aplica las notas de JD, pasa la lista
  de chequeo y prepara la entrega. Úsalo cuando el pedido sea: "revisa el borrador",
  "¿quedó bien?", "JD mandó correcciones", "aplica las notas", "abre la revisión",
  "hoja de revisión", "listo para entregar", "exporta el final", "sube a Drive",
  "Activa revisión". NO monta (vega-montaje).
---

# Revisión y entrega

Lee `docs/manual-estudio.md` sección 4d, y la parte 8 de `docs/reglas-de-edicion.md`
(E1-E3).

## Mirar antes de decir que quedó (E1)

Un render que terminó sin error no prueba nada. Después de cada `render --borrador`:

1. Revisa que `cache/borrador.mp4` sea nuevo (su hora de modificación), no el de la vuelta
   anterior.
2. Saca la hoja: `.venv/bin/python herramientas/revision.py <carpeta del proyecto>`
   (Windows: `.venv/Scripts/python`). Mira `cache/revision.jpg` con la herramienta de
   leer imágenes.
3. Busca en la hoja: texto que tapa una cara o una boca, texto fuera de la zona segura,
   frase en la toma equivocada, dos capas de texto a la vez, palabras mal escritas, cuadros
   vacíos o negros, el cierre.

## Correcciones dibujadas

`node ../herramientas/estudio.mjs revisar` abre la pantalla de revisión (navegador o
iPad en la misma WiFi). Cada nota cae en `revision/notas.json`:

- `t_s` es el segundo del video final: ahí caen `desde_s` o `en_s`.
- `centro_pct` se pega tal cual en `pos` o en `zoom.hacia`.
- **Mira siempre `imagen`** (el PNG con el trazo): el dibujo dice lo que la palabra no.
- Al aplicarla, `"aplicada": true`. Así se sabe qué quedó pendiente.

Si JD manda las notas por WhatsApp («seg 8: sube el texto»), se aplican igual y se anotan en
`revision/notas.json` para que quede el registro.

## Lista de chequeo antes de mandar el borrador a JD

- [ ] El gancho funciona en los primeros 2-3 s (G1)
- [ ] Ninguna toma se repite y el reel concluye (R3, R4)
- [ ] Texto: una capa a la vez, zona segura, no tapa caras, líneas cortas (T1-T4)
- [ ] La identidad es la del cliente (`docs/marcas.md`)
- [ ] Nada de «Escríbeme por WhatsApp» si es anuncio (T7)
- [ ] Sonido escuchado con audífonos: la voz se entiende, la música no tapa (vega-sonido)
- [ ] Sin HDR lavado ni horizontal recortado a vertical (C1, C3)

Al mandarlo: duración, qué decidiste y qué quedó pendiente, en tres líneas.

## Entrega (solo con el sí de JD)

1. `node ../herramientas/estudio.mjs render` → `salida/<slug>_9x16_<AAAAMMDD>.mp4` y
   `_16x9_` (o solo 9:16 si `formatos` lo dice). Si lleva audio en tendencia, también la
   versión sin música (S3).
2. Revisa el final con la hoja otra vez: el final tiene 4 veces los píxeles del borrador y
   a veces falla por memoria (si falla y al repetir pasa, fue eso).
3. Sube `salida/` a la carpeta de Drive que te indique JD. No renombres los archivos.
4. Commit y push del proyecto (manifest, subtítulos, notas). La media no viaja por git.
