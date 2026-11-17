# Mide el movimiento de cámara (desplazamiento global por correlación de fase) a 10 fps.
# Uso: python analisis/estabilidad.py material/IMG_x.MOV ...  -> analisis/estabilidad-fina.json
import json, subprocess, sys
import numpy as np
W, H, FPS = 144, 256, 10
def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        yield np.frombuffer(b, np.uint8).astype(np.float32)
win = np.outer(np.hanning(H), np.hanning(W))
def shift(a, b):
    A = np.fft.fft2((a - a.mean()) * win); B = np.fft.fft2((b - b.mean()) * win)
    R = A * np.conj(B); R /= np.abs(R) + 1e-6
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    if y > H // 2: y -= H
    if x > W // 2: x -= W
    return float(np.hypot(x, y))
out = {}
for path in sys.argv[1:]:
    prev = None; s = []
    for f in frames(path):
        f = f.reshape(H, W)
        if prev is not None: s.append(shift(prev, f))
        prev = f
    s = np.array(s)
    # suavizado 1 s
    k = np.ones(FPS) / FPS
    sm = np.convolve(s, k, mode="same") if len(s) >= FPS else s
    quieto = sm < 0.6  # < 0.6 px de 144 por décimo de segundo
    tramos = []; i = 0
    while i < len(quieto):
        if quieto[i]:
            j = i
            while j < len(quieto) and quieto[j]: j += 1
            if (j - i) / FPS >= 2.0: tramos.append([round(i / FPS, 1), round(j / FPS, 1)])
            i = j
        else: i += 1
    out[path] = {"serie": [round(float(x),1) for x in s.reshape(-1)[:len(s)//5*5].reshape(-1,5).mean(1)], "dur": round(len(s) / FPS, 1), "mov_medio": round(float(s.mean()), 2), "quietos": tramos}
    print(path, out[path]["quietos"], flush=True)
json.dump(out, open("analisis/estabilidad-fina.json", "w"), indent=1)
