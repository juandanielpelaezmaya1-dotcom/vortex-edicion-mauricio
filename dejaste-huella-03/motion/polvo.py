"""Polvo dorado (bokeh) sobre negro para todo el video de Dejaste Huella 03 (mezcla screen),
y la vineta suave (PNG con alfa). El fondo nunca esta quieto (M1), sin tapar a nadie:
las particulas van sobre todo por los lados y arriba, muy desenfocadas y lentas.

Uso (desde la carpeta del proyecto): ../.venv/Scripts/python -I motion/polvo.py
Deja material/polvo-oro.mp4 (82,9 s) y material/vineta.png.
"""
import subprocess

import numpy as np
from PIL import Image

W, H, FPS, DUR = 540, 960, 60000 / 1001, 82.9
N = int(DUR * FPS)
rng = np.random.default_rng(5)

# Particulas: x sesgado a los lados, deriva hacia arriba, parpadeo lento
P = 46
lado = rng.random(P) < 0.5
x0 = np.where(lado, rng.uniform(-0.05, 0.3, P), rng.uniform(0.7, 1.05, P))
x0[:8] = rng.uniform(0.3, 0.7, 8)  # unas pocas por el centro, arriba
y0 = rng.uniform(0, 1.2, P)
vel = rng.uniform(0.012, 0.035, P)  # alto por segundo
rad = rng.uniform(3, 16, P)
brillo = rng.uniform(0.25, 0.8, P)
fase = rng.uniform(0, 2 * np.pi, P)
frec = rng.uniform(0.2, 0.6, P)
ORO = np.array([1.0, 0.82, 0.48], np.float32)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
    "-s", f"{W}x{H}", "-r", "60000/1001", "-i", "-",
    "-vf", "scale=1080:1920:flags=bicubic,format=rgb24,colorchannelmixer=rr=1:gg=0.82:bb=0.48",
    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
    "-color_primaries", "bt709", "-color_trc", "bt709", "material/polvo-oro.mp4"], stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS
    img = np.zeros((H, W), np.float32)
    ys = ((y0 - vel * t) % 1.2 - 0.1) * H
    xs = (x0 + 0.02 * np.sin(t * 0.3 + fase)) * W
    a = brillo * (0.55 + 0.45 * np.sin(t * frec * 2 * np.pi + fase))
    for k in range(P):
        r = rad[k]
        x1, x2 = int(max(0, xs[k] - 3 * r)), int(min(W, xs[k] + 3 * r))
        y1, y2 = int(max(0, ys[k] - 3 * r)), int(min(H, ys[k] + 3 * r))
        if x1 >= x2 or y1 >= y2:
            continue
        d2 = ((xx[y1:y2, x1:x2] - xs[k]) ** 2 + (yy[y1:y2, x1:x2] - ys[k]) ** 2) / (r * r)
        img[y1:y2, x1:x2] += a[k] * np.exp(-d2 * 1.2)
    ff.stdin.write((np.clip(img, 0, 1) * 255).astype(np.uint8).tobytes())
ff.stdin.close()
ff.wait()

# Vineta: bordes 32 % mas oscuros, el centro intacto
Wv, Hv = 1080, 1920
y, x = np.mgrid[0:Hv, 0:Wv].astype(np.float32)
d = np.sqrt(((x - Wv / 2) / (Wv * 0.62)) ** 2 + ((y - Hv * 0.45) / (Hv * 0.62)) ** 2)
alfa = np.clip((d - 0.55) / 0.6, 0, 1) ** 1.6 * 0.32
img = np.zeros((Hv, Wv, 4), np.uint8)
img[..., 3] = (alfa * 255).astype(np.uint8)
Image.fromarray(img, "RGBA").save("material/vineta.png")
print("listo: material/polvo-oro.mp4, material/vineta.png")
