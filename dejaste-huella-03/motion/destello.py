"""Fuga de luz dorada sobre negro (mezcla screen) para las transiciones de Dejaste Huella 03.
Original del estudio: manchas calidas que barren en diagonal, nucleo casi blanco, pico al 35 %.
Uso: .venv/Scripts/python motion/destello.py material/destello-oro.mp4"""
import subprocess, sys
import numpy as np

W, H, FPS, DUR = 270, 480, 59.94, 1.0
N = int(round(FPS * DUR))
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
x /= W; y /= H
ORO = np.array([0.81, 0.62, 0.30], np.float32)    # #CFAA58 aclarado
AMBAR = np.array([0.95, 0.55, 0.20], np.float32)
BLANCO = np.array([1.0, 0.96, 0.88], np.float32)

def mancha(cx, cy, rx, ry):
    return np.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))

out = sys.argv[1]
ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", "60000/1001", "-i", "-", "-vf", "scale=1080:1920:flags=bicubic,gblur=sigma=6",
    "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
    "-color_trc", "bt709", out], stdin=subprocess.PIPE)
for i in range(N):
    p = i / (N - 1)
    env = np.interp(p, [0, 0.35, 1], [0, 1, 0]) ** 1.3          # sube rapido, baja despacio
    s = -0.3 + 1.6 * p                                            # barrido de izquierda a derecha
    a = mancha(s, 0.25 + 0.3 * p, 0.45, 0.9)                     # banda ancha dorada
    b = mancha(s * 0.8 + 0.2, 0.75 - 0.2 * p, 0.3, 0.45)         # segunda, ambar, a destiempo
    c = mancha(s + 0.05, 0.4 + 0.2 * p, 0.16, 0.35)              # nucleo caliente
    rayo = np.exp(-(((x - s) + 0.35 * (y - 0.5)) / 0.05) ** 2) * 0.35  # haz diagonal fino
    img = a[..., None] * ORO * 0.9 + b[..., None] * AMBAR * 0.6 + (c + rayo)[..., None] * BLANCO * 0.8
    img = np.clip(img * env * 1.15, 0, 1)
    ff.stdin.write((img * 255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
