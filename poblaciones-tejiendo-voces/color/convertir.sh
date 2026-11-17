#!/bin/sh
# HDR (HLG) del iPhone -> SDR bt709 con look cinematic. Deja el original intacto.
# Uso desde la carpeta del proyecto: sh color/convertir.sh
TM="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
CINE="eq=contrast=1.12:brightness=0.01:saturation=0.82,curves=master='0/0.04 0.2/0.15 0.5/0.49 0.8/0.84 1/0.95',colorbalance=rs=-0.10:gs=-0.02:bs=0.12:rm=0.03:gm=0:bm=-0.04:rh=0.10:gh=0.03:bh=-0.10,vignette=PI/5"
ls material/*.MOV | xargs -P 3 -I{} sh -c 'b=$(basename {} .MOV); [ -f material/cine/$b.mp4 ] || ffmpeg -v error -y -i {} -vf "'"$TM,$CINE"'" -c:v libx264 -preset fast -crf 16 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a aac -b:a 192k material/cine/$b.tmp.mp4 && mv material/cine/$b.tmp.mp4 material/cine/$b.mp4 && echo $b'
