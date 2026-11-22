"""Copia derivada de la toma de «y yo tomé la decisión» (full.mp4, 240,7-249,66 s) sin el click
seco que trae el original a los 243,142 s (52,86 s del resumen): un golpe que llega a saturar
antes de la voz. Se baja a ras del ruido de la sala con rampas de 2 ms; el resto queda igual.
El original no se toca. Salida: material/toma-decision.mp4 (el clip 11 usa in 0,5 / out 7,96).
"""
import os, subprocess, wave
import numpy as np

PROY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(PROY, "material", "full.mp4")
DESDE, HASTA = 240.7, 249.66
SALIDA = os.path.join(PROY, "material", "toma-decision.mp4")
TMP = os.path.join(PROY, "cache", "_toma_audio.wav")
SR = 48000
CLICK = (2.4405, 2.462)  # segundos dentro de la copia: el golpe y su caida
RAMPA = 0.002

def ff(*a):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", *a], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])

ff("-ss", str(DESDE), "-to", str(HASTA), "-i", FUENTE, "-vn", "-ar", str(SR), "-c:a", "pcm_s16le", TMP)
with wave.open(TMP) as w:
    ch = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, ch).astype(float)

t = np.arange(len(x)) / SR
a, b = CLICK
g = np.ones(len(x))
baja = 0.06
dentro = (t >= a) & (t <= b)
g[dentro] = baja
for c0, c1, s in ((a - RAMPA, a, 1), (b, b + RAMPA * 4, -1)):
    m = (t >= c0) & (t < c1)
    u = (t[m] - c0) / (c1 - c0)
    k = 0.5 + 0.5 * np.cos(np.pi * u) if s == 1 else 0.5 - 0.5 * np.cos(np.pi * u)
    g[m] = baja + (1 - baja) * k
y = np.clip(x * g[:, None], -32768, 32767).astype("<i2")
print("pico antes/despues en el click:", np.abs(x[dentro]).max() / 32768, np.abs(y[dentro]).max() / 32768)
with wave.open(TMP, "wb") as w:
    w.setnchannels(ch); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())

ff("-ss", str(DESDE), "-to", str(HASTA), "-i", FUENTE, "-i", TMP, "-map", "0:v", "-map", "1:a",
   "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p",
   "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
   "-c:a", "aac", "-b:a", "256k", SALIDA)
os.remove(TMP)
print("listo:", SALIDA)
