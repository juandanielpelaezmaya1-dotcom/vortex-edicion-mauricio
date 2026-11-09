# Identidad de cada marca

Antes de montar la pieza de un cliente, mira su fila. Si el cliente no está aquí o le
falta algo (logo, colores exactos, tipografía), **pídeselo a JD**: no se improvisa ni se
copia el estilo de otro cliente.

| Marca | Texto en pantalla | Colores | Lo que no se toca |
|---|---|---|---|
| **Vortex** (la agencia) | Montserrat (títulos) + Inter (texto) | Royal `#305aa3`, Sky `#7cb9f2`, Navy `#060835`, Slate `#5c6972`, Fog `#d4d5d5` | El verde de WhatsApp `#25d366` solo en lo que abre un chat. Fondo por capas, nunca navy liso |
| **Dejaste Huella** | Poppins SemiBold + Playfair Display itálica (perfil por defecto de `subtitulos`) | Dorado `#CFAA58` | Sin sombra, todo centrado |
| **Mi Vieja Burger** | Fjalla One en mayúsculas + Permanent Marker, cinta naranja (`"marca": "mi-vieja-burger"`) | Naranja `#F24405` | Con sombra; su sello arriba a la izquierda todo el video; sin precio en pantalla |
| **MT** | Archivo Black, Permanent Marker, IBM Plex Mono | Amarillo `#ffe10a` sobre negro `#0e0d0b` | «La calle de noche». Todavía no es perfil de `MARCAS`: si te toca, se agrega |
| **Daniel Peláez** (marca personal de JD) | Poppins blanca sola, sin variación tipográfica | — | POV crudo y orgánico |
| **U. Mariana** | Sin manual | Azul `#244BC5`, cian `#00B6ED`, logo `#0050A0` (medidos) | Registro formal si lo ve la directiva |

## Agregar un perfil de subtítulos

1. Pon las fuentes del cliente en `_render/src/fuentes/` con su licencia al lado (solo
   fuentes libres: OFL, Apache; si la marca usa una comercial, pregúntale a JD).
2. Agrega una entrada a `MARCAS` en `_render/src/SubtitulosEditorial.tsx`, copiando la de
   `mi-vieja-burger` y cambiando familias, escala y acento. Importa la fuente arriba del
   archivo y cárgala en `useFuentes()` (un `new FontFace` más), o el render usa la de respaldo.
3. Úsala con `"subtitulos": { "marca": "<nombre>" }` y saca un cuadro de estilo para JD
   antes de montar el video entero.
