#!/bin/sh
# Look calido "food" horneado en copias 1080x1920 de las tomas que usa el reel.
# El original queda en la tarjeta Sony (D:/PRIVATE/M4ROOT/CLIP/C20261112_NNNN.MP4): no se toca.
# Uso desde la carpeta del proyecto: sh color/convertir.sh      (salta las que ya existen)
# Cambiar el look = editar LOOK, borrar material/look/*.mov y reconvertir.
SRC=${SRC:-/d/PRIVATE/M4ROOT/CLIP}
TOMAS="5222 5226 5229 5232 5233 5235 5236 5238 5239 5241 5242 5243 5244 5246 5247 5248 5249 5250 5251 5253 5256 5258 5260 5261 5262 5264 5265 5268 5269 5271 5274 5276 5278 5279 5280 5283 5284 5285 5287 5290 5291 5292 5293 5294 5296 5302 5303 5307 5308 5309"
# Contraste medio-alto, dorados y ambar en medios y altas, sombras limpias (casi neutras), viñeta suave.
LOOK="eq=contrast=1.10:saturation=1.12:gamma=0.97,curves=master='0/0 0.12/0.07 0.5/0.5 0.85/0.9 1/1':red='0/0 0.5/0.53 1/1':blue='0/0.01 0.5/0.46 1/0.94',colorbalance=rs=-0.02:bs=0.03:rm=0.06:gm=0.015:bm=-0.06:rh=0.05:gh=0.02:bh=-0.07,vignette=PI/6"
# La mesa de la clienta (5300-5309) llega ~1 diafragma abajo: se levanta antes del look.
CLIENTA="eq=brightness=0.03:gamma=1.22,"
for n in $TOMAS; do echo $n; done | xargs -P 3 -I{} sh -c '
  n={}; o=material/look/$n.mov; [ -f $o ] && exit 0
  pre=""; [ $n -ge 5300 ] && pre="'"$CLIENTA"'"
  ffmpeg -v error -y -i '"$SRC"'/C20261112_$n.MP4 -vf "scale=1080:1920:flags=lanczos,${pre}'"$LOOK"'" \
    -c:v libx264 -preset medium -crf 15 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
    -c:a pcm_s16le -f mov material/look/$n.tmp.mov && mv material/look/$n.tmp.mov $o && echo $n'
