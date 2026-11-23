"""Efectos de sonido ORIGINALES de dejaste-huella-resumen (sintetizados, sin licencias).

    .venv/Scripts/python -I dejaste-huella-resumen/audio/efectos.py      (desde la raiz)

Deja en material/sfx/:
  golpe.wav     golpe grave de cine con cola (abre el gancho)
  megafono.wav  clic del megafono y un acople corto (con la primera palabra del gancho)
  subida.wav    subida de aire y brillo que termina en un punto (el gancho pasa a color)
  brillo.wav    racimo de campanitas con cola (el destello del paso a color, y el logo)
  soplo.wav     soplo suave de transicion (cambios de capitulo)
Todos a -6 dBFS de pico; el nivel final lo da `efectos[].volumen` en el manifest (S2: bajos).
`subida.wav` dura 1,6 s y su punto cae en el ultimo cuadro: se pone en `corte - 1.6`.
"""
import os
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(os.path.dirname(AQUI), "material", "sfx")
os.makedirs(DIR, exist_ok=True)
SR = 48000
rng = np.random.default_rng(7)


def escribir(nombre, x):
    x = np.atleast_2d(x.T).T if x.ndim == 1 else x
    if x.ndim == 1 or x.shape[1] == 1:
        x = np.repeat(x.reshape(-1, 1), 2, axis=1)
    x = x / (np.abs(x).max() + 1e-9) * 10 ** (-6 / 20)
    with wave.open(os.path.join(DIR, nombre), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def t(d):
    return np.arange(int(d * SR)) / SR


def filtro(x, tipo, f, orden=2):
    return sosfilt(butter(orden, f, btype=tipo, fs=SR, output="sos"), x, axis=0)


def sala(x, dur=2.5, caida=0.6, mezcla=0.35):
    n = int(dur * SR)
    ir = rng.standard_normal((n, 2)) * np.exp(-np.arange(n) / SR / caida)[:, None]
    ir = filtro(ir, "low", 6000)
    ir /= np.sqrt((ir ** 2).sum(axis=0))
    x2 = np.repeat(x.reshape(-1, 1), 2, axis=1) if x.ndim == 1 else x
    x2 = np.pad(x2, ((0, n), (0, 0)))
    hum = np.stack([fftconvolve(x2[:, i], ir[:, i])[: len(x2)] for i in range(2)], axis=1)
    return x2 * (1 - mezcla) + hum * mezcla


# golpe: barrido grave 70->32 Hz + golpe de ruido filtrado + cola de sala
tt = t(2.2)
f = 32 + 38 * np.exp(-tt * 9)
sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.7)
golpe = filtro(rng.standard_normal(len(tt)), "low", 900) * np.exp(-tt / 0.06) * 0.5
escribir("golpe.wav", sala(np.tanh(1.6 * (sub + golpe)), 2.8, 0.9, 0.3))

# megafono: clic de boton + acople (tono 2,2 kHz que sube y se corta)
tt = t(0.45)
clic = filtro(rng.standard_normal(len(tt)), "band", [1500, 5000]) * np.exp(-tt / 0.004)
acople = np.sin(2 * np.pi * (2150 * tt + 300 * tt ** 2)) * np.minimum(tt / 0.04, 1) * np.clip((0.32 - tt) / 0.06, 0, 1) * 0.35
x = clic + acople
x = np.concatenate([x, np.zeros(int(0.1 * SR))])
y = x.copy()
for d, g in ((0.18, 0.35), (0.36, 0.2)):
    k = int(d * SR)
    y[k:] += x[: len(x) - k] * g
escribir("megafono.wav", y)

# subida: ruido que se abre y sube 1,6 s + armonicos que suben; termina en seco
tt = t(1.6)
p = tt / 1.6
ruido = rng.standard_normal(len(tt))
bloques = []
for i in range(16):  # filtro que se abre por tramos (barrido)
    a, b = int(i * len(tt) / 16), int((i + 1) * len(tt) / 16)
    corte = 400 + 9000 * (i / 15) ** 2
    bloques.append(filtro(ruido, "low", corte)[a:b])
aire = np.concatenate(bloques) * p ** 2.2
tono = sum(np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * p ** 2)) / SR) / (k + 1) for k, f0 in enumerate([220, 330, 440]))
escribir("subida.wav", sala(aire * 0.8 + tono * 0.12 * p ** 3, 0.6, 0.15, 0.25)[: len(tt)])

# brillo: campanitas (FM) en racimo, tonos de La menor add9, con cola larga
tt = t(3.0)
x = np.zeros(len(tt))
for j, m in enumerate([81, 84, 88, 83, 93]):
    f0 = 440 * 2 ** ((m - 69) / 12)
    k = int(j * 0.045 * SR)
    tj = tt[: len(tt) - k]
    x[k:] += np.sin(2 * np.pi * f0 * tj + 0.8 * np.sin(2 * np.pi * f0 * 3.5 * tj) * np.exp(-tj * 6)) * np.exp(-tj / 0.9) * 0.5
escribir("brillo.wav", sala(x, 2.5, 0.8, 0.45))

# soplo: ruido de banda que pasa (sube y baja) con paneo de izquierda a derecha
tt = t(0.9)
env = np.sin(np.pi * tt / 0.9) ** 2
x = filtro(rng.standard_normal(len(tt)), "band", [500, 6000]) * env
pan = tt / 0.9
escribir("soplo.wav", np.stack([x * np.cos(pan * np.pi / 2), x * np.sin(pan * np.pi / 2)], axis=1))
print("listo:", ", ".join(sorted(os.listdir(DIR))))
