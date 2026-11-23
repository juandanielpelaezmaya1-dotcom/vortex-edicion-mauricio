"""Voz del gancho en blanco y negro como por megafono, con eco (pedido de Mauricio, 22-nov).

    .venv/Scripts/python -I dejaste-huella-resumen/audio/megafono.py      (desde la raiz)

Toma el audio de las dos tomas del gancho (clips 1 y 2 del manifest, de material/gancho-gris.mp4)
en el orden y con la duracion que tienen en la linea de tiempo, y le aplica:
banda de megafono (450-3400 Hz, realce en 1,8 kHz), saturacion suave (tanh), compresion y un eco
de tres rebotes (180/360/540 ms). La cola del eco se apaga 0,5 s despues de la ultima palabra
del gancho, para no pisar la primera pregunta de la entrevista.
Deja material/gancho-megafono.wav. En el manifest: los clips 1-2 con volumen 0 y este archivo
como pista en 0 (limpiar false; se nivela como voz).
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PROY = os.path.dirname(AQUI)
M = json.load(open(os.path.join(PROY, "manifest.json"), encoding="utf-8"))
G = [c for c in M["clips"][:2]]
assert all(c["archivo"].endswith("gancho-gris.mp4") for c in G), "los clips 1-2 ya no son el gancho"
FIN = sum(c["out_s"] - c["in_s"] for c in G)
COLA = 0.5

src = os.path.join(PROY, "material", "gancho-gris.mp4")
partes = ";".join(f"[0:a]atrim={c['in_s']}:{c['out_s']},asetpts=PTS-STARTPTS[a{i}]" for i, c in enumerate(G))
megafono = ",".join([
    "highpass=f=450:poles=2", "highpass=f=450:poles=2",
    "lowpass=f=3400:poles=2", "lowpass=f=3400:poles=2",
    "equalizer=f=1800:t=q:w=1.2:g=7",
    "acompressor=threshold=0.08:ratio=6:attack=5:release=80:makeup=2",
    "volume=9dB", "asoftclip=type=tanh", "volume=-7dB",
    f"apad=pad_dur={COLA + 0.2}",
    "aecho=0.85:0.75:180|360|540:0.38|0.22|0.12",
    f"atrim=0:{FIN + COLA}",
    f"afade=t=out:st={FIN}:d={COLA}",
    "afade=t=in:st=0:d=0.02",
])
filtro = f"{partes};{''.join(f'[a{i}]' for i in range(len(G)))}concat=n={len(G)}:v=0:a=1,{megafono}[out]"
out = os.path.join(PROY, "material", "gancho-megafono.wav")
r = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", src, "-filter_complex", filtro, "-map", "[out]",
                    "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", out], capture_output=True, text=True)
if r.returncode:
    sys.exit(r.stderr[-1500:])
print(f"listo: {out}  ({FIN + COLA:.2f} s, el gancho dura {FIN:.2f} s)")
