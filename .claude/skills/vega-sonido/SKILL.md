---
name: vega-sonido
description: >
  Especialista de sonido del estudio de Vortex. Música, efectos, voz aparte de las tomas
  (pistas), niveles en LUFS, limpieza de ruido, sincronía labial y la mezcla sin música
  para audio en tendencia. Úsalo cuando el pedido sea: "ponle música", "la música tapa la
  voz", "bájale al efecto", "la voz se oye baja", "hay ruido", "la canción entra antes",
  "voz en off", "sincroniza la boca", "audio en tendencia", "Activa sonido". NO decide el
  montaje (vega-montaje).
---

# Sonido

Lee `docs/manual-estudio.md` sección 4h, y la parte 5 de `docs/reglas-de-edicion.md`
(S1-S4).

## Niveles de referencia

| Qué | Nivel |
|---|---|
| Voz (pistas) | -16 LUFS, techo -1,5 dBTP. Lo hace `normalizar` en dos pasadas |
| Música bajo voz | `musica.volumen` 0,15-0,25 |
| Música sola | 0,3-0,4 |
| Efecto de golpe | `efectos[].volumen` ~0,4 (S2) |

## Reglas

- **La voz termina entera; la canción entra ~1 s después de la última palabra (S1).**
- **Los efectos no entran a la medición:** si normalizas una mezcla con una explosión
  adentro, todo lo demás baja. Se nivela la voz y el efecto se pone después (S2).
- **Audio en tendencia o música comercial:** entrega también la versión sin `musica` (un
  segundo render), para poner la canción desde la biblioteca de Instagram (S3).
- **Voz aparte** (narración o canto sobre otras tomas): va en `pistas[]` con su `en_s`, y
  las tomas llevan `volumen: 0`.
- **Canción en varios tramos:** misma `ganancia_db` en todos, o el intro y el coro suenan
  igual y el coro pierde su golpe. `limpiar: false` para música y aplausos.
- **Cortes de audio solo en silencios**, nunca a mitad de palabra. `silencedetect` para
  encontrarlos (manual, 4c). `fundido_s` evita el clic.
- **Sincronía labial:** toma y pista del mismo rango del archivo y en el mismo segundo de la
  línea de tiempo. Si la voz se grabó en otro celular, el medidor miente: ajústala a ojo
  con JD, en pasos de un cuadro (S4).

## Música y licencias

El estudio no trae banco de música ni efectos. Usa solo lo que JD o el cliente manden, o
audio con licencia para uso comercial. Si una pieza es de pauta, la canción tiene que
estar licenciada: la biblioteca de Instagram no sirve para anuncios.

## Cómo comprobar

Escucha el borrador entero con audífonos antes de mandarlo. Para medir la sonoridad del
final:

```
ffmpeg -i salida/<archivo>.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12
```

Integrated cerca de -16 LUFS y True peak por debajo de -1 dBTP.
