# Reglas de edición que ya fijó JD

Cada regla salió de una revisión real de JD sobre un video de Vortex. **Si choca con un
tutorial, una referencia o tu criterio, gana este archivo.** Cada una trae el porqué
(el error que la originó) y cómo se aplica aquí.

## 1. Gancho

**G1. Si el protagonista habla en el material, el gancho es su voz en sincronía, sin textos de diseño encima.**
JD rechazó un reel que ignoraba que los clips, con su audio ya grabado, eran el guion. La versión buena abre con 2 s de su voz antes del logo.

**G2. El texto del gancho nunca tapa la cara ni la boca de quien habla: si no cabe abajo, va por encima de la cabeza.**
En un reel de Mi Vieja Burger el gancho tapaba la boca de la niña y otra frase su barbilla. Se arregla con `textos[].pos` o `"y"` por frase.

## 2. Ritmo y cortes

**R1. Ritmo por toma, no velocidad pareja: 2× en tránsito, 1,4-1,6× al llegar a lo que vale mirar.**
Un recorrido de 14 clips de 4 s a la misma velocidad y con fundidos se descartó: demasiados cortes, tomas largas y lentas. Se aplica con `clips[].velocidad`.

**R2. En un montaje al pulso de la música, una o dos tomas de dos pulsos rompen la monotonía.**
Todo el drop a un pulso cansaba; JD: «alarga un poco más estas dos tomitas para que rompan un poquito el ritmo».

**R3. Ninguna toma se repite: los destellos y flashes salen de material que no aparece en otro lado del reel.**
Un reel reciclaba tomas en sus destellos y una toma iba dos veces; JD lo vio.

**R4. El reel concluye: el cierre aterriza la idea, no se queda en el aire ni corta a negro.**
Una tanda de reels terminaba en el aire y con cortes raros. Si la última toma se acaba, sigue en la misma pose en cámara lenta (`velocidad` 0,5) con el texto encima, en vez de cortar a negro.

## 3. Texto en pantalla y subtítulos

**T1. Una sola capa de texto a la vez; un texto escrito va solo donde nadie habla.**
Un gancho escrito encima de los subtítulos: la gente no sabe dónde leer. Vale seguro para Daniel; si el guion de otro cliente pide gancho sobre subtítulos, confírmalo con JD.

**T2. Zona segura: nada sobre el 8 % ni bajo el 78,6 % del alto, 5,5 % de margen a los lados, y del 62 % hacia abajo el lado derecho (desde el 77 % del ancho) es de los botones.**
Subtítulos a todo el ancho y abajo pisaban los botones y la descripción. `render` rechaza `y` fuera de 14-74.

**T3. La altura se elige por toma, no fija: el texto no tapa caras ni lo que protagoniza el plano, va sobre lo más oscuro y no cambia dentro de la misma toma.**
Un subtítulo tapaba la cara de la asesora. Se aplica con `"y"` por frase en `subtitulos.frases`.

**T4. Todo centrado y en trozos cortos, para que la letra no se achique: máximo ~15 caracteres por línea en las frases bajas y ~23 en el resto (8 y 13 en la serif grande).**
El bloque corrido a un lado para esquivar los botones se notaba, y las frases largas salían con letra chica. Partir con ` / `.

**T5. La tipografía grande va con cuentagotas: gancho, marca y golpe emocional, ~1 de cada 4 frases.**
La palabra grande en casi todas las frases; JD: «si se lo hace siempre pierde el sentido». El resto alterna la base sola y la base con la segunda familia chica (`_chica_`).

**T6. Legibilidad sin ensuciar: nunca sombra de fondo detrás del texto.**
Primero mueve la frase a la zona oscura; si no hay, sombra suave solo en las letras (`subtitulos.sombra`, `textos[].sombra`) o un degradado oscuro detrás. La sombra radial ensuciaba la imagen, y un texto dorado sobre pared clara no se leía.

**T7. En un anuncio de Meta no va «Escríbeme por WhatsApp» en pantalla, ni como subtítulo en la toma de cierre: el botón de Meta ya lleva al chat y esa toma va limpia.**
Pasó dos veces. Con `hasta_s` solo, la frase anterior se cierra antes del corte.

## 4. Motion graphics

**M1. Sobrio no es plano.** El fondo nunca está quieto y los elementos son lo que se dice (un embudo con partículas que viajan, un celular real para el chat, un chip de reloj para «fuera de horario»). Las cifras ruedan, el texto se revela por máscara, lo que viaja deja estela y el golpe sacude la cámara.
Una pieza con tipografía animada sobre fondo liso; JD: «demasiado plano». Se arregló sin tocar el copy.

**M2. Una cantidad se dibuja a escala real y el gráfico se estrecha con ella; nada de puntos que no representan nada.**
Un embudo con cuatro columnas iguales de 45 puntos; JD: «no entiendo por qué se representa con esos puntos a las personas». Quedó en 2.148 figuras, una por inscrito.

**M3. Un reel no puede verse vacío: varias tomas, motion y elementos propios de la marca.**
Un clip con tarjeta final; JD: «está horrible… demasiado vacío». Una toma más una tarjeta de cierre se lee pobre.

**M4. Destellos y explosiones de luz, bajos: ~0,55-0,6 de intensidad.**
Un destello a 0,9 que JD pidió bajar a 0,6.

**M5. Con franja de cine arriba, el zoom crece desde arriba para no cortar la cabeza.**
El zoom crecía hacia el 30 % del alto y la franja le cortaba la cabeza al protagonista. `zoom.hacia` con `y` 0.

**M6. «Cómo llegar» con dron: rampa de velocidad en la bajada (lenta, rápida, lenta) con desenfoque de movimiento y un pin pegado al local.**
El manifest no hace ni rampa ni pin: es composición a la medida (manual, 4f).

## 5. Sonido y voz

**S1. La voz del protagonista termina entera; la canción entra ~1 s después de la última palabra.**

**S2. Los efectos de golpe van bajos (~0,4) y la mezcla no se normaliza con ellos adentro.**
Una explosión a volumen 1; JD: «bájale el volumen al efecto final». Normalizada con ella, todo lo demás subía 2,5 dB.

**S3. Con música comercial o audio en tendencia, entrega también la mezcla sin música**, para poner la canción desde la biblioteca de Instagram. Un segundo render sin `musica` en el manifest.

**S4. Sincronía labial con la voz grabada en otro celular: no confíes en el medidor; ajústala a ojo con JD.**
El medidor dio ~0,9 s de desfase y JD eligió −0,284 s a ojo.

## 6. Color y look

**C1. El material del iPhone y de las Ray-Ban es HDR: pásalo a SDR bt709 antes de editar o sale lavado.** Receta en el manual, sección 6.

**C2. Fondo por capas siempre: manchas difusas, cuadrícula con máscara, viñeta, grano y un motivo gigante en contorno que sea del concepto.**
Unas piezas sobre azul navy liso; JD: «hay un fondo muy sólido». Un color liso se lee como pieza pobre.

**C3. Nunca recortes un video horizontal a 9:16 después: queda un tercio de la resolución estirado y se ve blando.**
Reencuadra la fuente o avísale a JD antes de montar. `probe` te da la resolución real antes de decidir.

## 7. Identidad del cliente

**I1. Cada cliente con su identidad: muéstrale a JD un cuadro de estilo (un fotograma con su tipografía y sus colores) antes de montar. Poppins + Playfair es de Dejaste Huella, no un estilo por defecto.**
Un reel salió con los textos de otro cliente; JD: «estás usando lo mismo para todos». Las identidades están en `docs/marcas.md`.

## 8. Revisión y entrega

**E1. Antes de decir que quedó, mira el render, no el log.** La hoja de revisión (`herramientas/revision.py`) da un cuadro por frase y por texto. Y borra el MP4 viejo antes de verificar uno nuevo: una vez se dio por listo un render que no había empezado porque se revisó el archivo anterior.

**E2. Calidad sobre cantidad: de un lote de material salen pocos reels que concluyan, y solo para la marca que toca.**
De 39 reels propuestos con un lote de material, JD lo bajó a 9.

**E3. En pauta, primero los estáticos 4:5 (1080×1350) terminados; el motion va después de que JD los apruebe.**
JD quiere ver la pieza como saldría en el feed, no un storyboard.
