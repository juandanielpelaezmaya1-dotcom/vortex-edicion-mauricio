"""Musica ORIGINAL de dejaste-huella-03: ambiental, positiva y con buena energia.

    .venv/Scripts/python -I dejaste-huella-03/audio/musica.py      (desde la raiz)

Do mayor a 100 BPM, C - G/B - Am - F (con novenas): pad calido, arpegio de piano suave,
bajo redondo, y un pulso ligero (bombo suave, rim, shaker) que entra en el primer corte
(20,02 s). La campana con melodia entra en el segundo corte (33,88 s). Cuando termina la
voz (entra el logo con los contactos) sube y cierra en Do.

Los tiempos salen de manifest.json (clip 1 = el video, ultimo clip = logo) y de CORTES.
Niveles horneados (manifest con volumen 1): cama bajo la voz, -3 dB mientras ella habla,
-16 LUFS de referencia y sube en el logo. Deja material/musica-ambiental.wav.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

AQUI = os.path.dirname(os.path.abspath(__file__))
PROY = os.path.dirname(AQUI)
M = json.load(open(os.path.join(PROY, "manifest.json"), encoding="utf-8"))
CLIPS = [(c["archivo"], c.get("in_s", 0), c["out_s"]) for c in M["clips"]]
SR = 48000
T = sum(b - a for _, a, b in CLIPS) + 0.1
N = int(T * SR)
rng = np.random.default_rng(23)

CORTES = [20.02, 33.88, 37.04, 48.56]  # borrador 3: sin la toma repetida ni la cuenta regresiva
BPM = 100.0
PULSO = 60.0 / BPM
COMPAS = 4 * PULSO
GROOVE = CORTES[0]
T0 = GROOVE - 8 * COMPAS  # el compas 8 cae en el primer corte
CAMPANA = CORTES[1]
ULTIMA_PALABRA = sum(b - a for _, a, b in CLIPS[:-1])


def ff(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-2000:])
    return r.stderr


def lufs(ruta):
    log = ff("-i", ruta, "-af", "ebur128", "-f", "null", "-")
    return float([l for l in log.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def escribir(ruta, x):
    x = np.clip(x, -1, 1)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def poner(buf, x, en_s, pan=0.0, vol=1.0):
    i = int(round(en_s * SR))
    if i >= N:
        return
    if i < 0:
        x, i = x[-i:], 0
    x = x[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    if x.ndim == 2:
        buf[i : i + len(x)] += x * vol
        return
    buf[i : i + len(x), 0] += x * vol * l * 1.41
    buf[i : i + len(x), 1] += x * vol * r * 1.41


def pad(notas, dur):
    """Voces apenas desafinadas, ataque y salida lentos: el colchon calido (estereo)."""
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        f = hz(m)
        for det, lado in ((-0.12, 0), (0.12, 1), (0.0, 0), (0.05, 1)):
            fr = f * 2 ** (det / 24)
            fase = rng.uniform(0, 2 * np.pi)
            v = np.sin(2 * np.pi * fr * t + fase) + 0.18 * np.sin(4 * np.pi * fr * t + fase) + 0.06 * np.sin(6 * np.pi * fr * t)
            x[:, lado] += v * 0.5
    env = np.minimum(t / 0.9, 1) * np.minimum((dur - t) / 0.9, 1)
    return x * env[:, None] / len(notas)


def piano(m, dur=1.6):
    """Piano suave (fieltro): fundamental + armonicos que caen rapido."""
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9)
         + 0.35 * np.sin(2 * np.pi * 2.001 * f * t) * np.exp(-t / 0.35)
         + 0.12 * np.sin(2 * np.pi * 3.003 * f * t) * np.exp(-t / 0.18))
    return x * np.minimum(t / 0.004, 1)


def campana(m, dur=2.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t + 0.9 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t * 7))
    x += 0.2 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3)
    return x * np.minimum(t / 0.003, 1) * np.exp(-t / 0.7)


def bajo(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return x * np.minimum(t / 0.01, 1) * np.exp(-t / 0.9) * np.minimum((dur - t) / 0.05, 1)


def bombo():
    t = np.arange(int(0.3 * SR)) / SR
    f = 48 + 70 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def ruido(dur, lo, hi, caida):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= (fr > lo) & (fr < hi)
    x = np.fft.irfft(X, n)
    x /= np.abs(x).max() + 1e-9
    return x * np.exp(-np.arange(n) / SR / caida)


# Acordes: pad (medio), arpegio en corcheas (alto), raiz del bajo
ACORDES = {
    "C": ([60, 64, 67, 71, 74], [72, 76, 79, 74, 84, 79, 76, 74], 36),  # Cmaj9
    "G/B": ([59, 62, 67, 69, 74], [71, 74, 79, 81, 83, 81, 79, 74], 35),
    "Am": ([57, 60, 64, 67, 71], [69, 72, 76, 79, 81, 79, 76, 72], 33),  # Am9
    "F": ([57, 60, 65, 67, 72], [69, 72, 77, 79, 81, 79, 77, 72], 29),  # Fadd9
}
CICLO = ["C", "G/B", "Am", "F"]
MELODIA = [  # (corchea, midi) por compas, sobre el ciclo
    [(0, 88), (3, 86), (4, 84), (6, 79)],
    [(0, 83), (2, 86), (4, 83), (6, 79)],
    [(0, 84), (3, 83), (4, 81), (6, 76)],
    [(0, 81), (2, 84), (4, 86), (6, 88)],
]

pads, arps, graves, ritmo, campanas = (np.zeros((N, 2)) for _ in range(5))
K = bombo()
RIM = ruido(0.08, 1800, 6000, 0.018)
SH = ruido(0.06, 6500, 15000, 0.015)
ocho = PULSO / 2
c = -1  # borrador 4: un compas antes del 0, para que la musica ya suene en el primer cuadro
while True:
    t_c = T0 + c * COMPAS
    if t_c > T - 0.3:
        break
    nombre = CICLO[c % 4]
    final = t_c >= ULTIMA_PALABRA - 0.3
    pad_n, arp_n, raiz = ACORDES[nombre]
    if t_c + COMPAS > 0:
        poner(pads, pad(pad_n, COMPAS + 0.9), t_c - 0.2, vol=0.9)
    if True:  # arpegio desde el inicio (Mauricio: los primeros segundos no se oia musica)
        for k, m in enumerate(arp_n):
            poner(arps, piano(m), t_c + k * ocho, pan=0.35 * np.sin(k), vol=0.32 if k % 2 == 0 else 0.22)
    if t_c >= GROOVE - 0.05:
        for paso, m, d in ((0, raiz, 1.1), (3, raiz, 0.5), (6, raiz + 7, 0.5)):
            poner(graves, bajo(m, d), t_c + paso * ocho, vol=0.6)
        for p in range(4):  # bombo suave en negras, rim en 2 y 4, shaker en semicorcheas
            poner(ritmo, K, t_c + p * PULSO, vol=0.55 if p % 2 == 0 else 0.35)
            if p % 2:
                poner(ritmo, RIM, t_c + p * PULSO, pan=-0.15, vol=0.22)
        for k in range(16):
            poner(ritmo, SH, t_c + k * ocho / 2, pan=0.4, vol=0.1 if k % 2 else 0.16)
    if t_c >= CAMPANA - 0.05 or final:
        for paso, m in MELODIA[c % 4]:
            poner(campanas, campana(m), t_c + paso * ocho, pan=-0.3, vol=0.14)
    c += 1

# Barrido de aire que llega a cada corte: acompana el destello
for corte in CORTES + [ULTIMA_PALABRA]:
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    poner(ritmo, ruido(0.6, 2000, 12000, 10.0) * (t / 0.6) ** 2.5, corte - 0.55, vol=0.12)

# Acorde final de Do sobre el logo
t_fin = ULTIMA_PALABRA + 3.5
for j, m in enumerate([48, 60, 64, 67, 71, 74, 79]):
    poner(arps, piano(m, 3.5), t_fin + j * 0.03, pan=-0.3 + 0.1 * j, vol=0.3)
poner(campanas, campana(84, 3.0), t_fin + 0.2, pan=0.2, vol=0.16)

# El pad lleva un pasabajos que abre de a poco hasta el primer corte (crece la energia)
sos = butter(2, 1800, btype="low", fs=SR, output="sos")
oscuro = np.stack([sosfilt(sos, pads[:, i]) for i in range(2)], axis=1)
tt = np.arange(N) / SR
abre = np.clip(tt / 6.0, 0, 1)[:, None]  # el filtro abre en 6 s, no a los 20
pads = oscuro * (1 - abre) + pads * abre

mezcla = pads * 0.55 + arps + graves * 0.8 + ritmo * 0.85 + campanas
ir_n = int(1.6 * SR)
ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / 0.45)[:, None]
ir /= np.sqrt((ir ** 2).sum(axis=0))
humedo = np.stack([fftconvolve((arps + campanas + pads * 0.3)[:, i], ir[:, i])[:N] for i in range(2)], axis=1)
mezcla = mezcla + 0.25 * humedo

os.makedirs(os.path.join(PROY, "cache"), exist_ok=True)
tmp = os.path.join(PROY, "cache", "_musica_pre.wav")
escribir(tmp, mezcla / (np.abs(mezcla).max() + 1e-9) * 0.7)
mezcla = mezcla / (np.abs(mezcla).max() + 1e-9) * 0.7 * 10 ** ((-16 - lufs(tmp)) / 20)

# Curva de nivel: cama a -9 dB bajo la voz, entrada suave, sube a -1 en el logo, sale al final
db = np.where(tt < GROOVE, -6.0, -9.0)  # antes del ritmo hay menos instrumentos: la cama va 3 dB arriba
db = np.where((tt >= GROOVE - 1.5) & (tt < GROOVE), -6.0 - 3.0 * (tt - (GROOVE - 1.5)) / 1.5, db)
db = np.where(tt < 0.15, db - 20 * (0.15 - tt) / 0.15, db)  # sin clic en el primer cuadro
sube = np.clip((tt - (ULTIMA_PALABRA + 0.15)) / 0.8, 0, 1)
db = db * (1 - sube) - 1.0 * sube
db -= np.clip((tt - (T - 1.5)) / 1.5, 0, 1) * 30

# Ducking: -3 dB mientras ella habla (envolvente del audio de las tomas en la linea de tiempo)
vozw = os.path.join(PROY, "cache", "_voz_env.wav")
trozos = []
for archivo, a, b in CLIPS[:-1]:
    ff("-ss", f"{a}", "-to", f"{b}", "-i", os.path.join(PROY, archivo), "-vn", "-ac", "1", "-ar", "1000",
       "-c:a", "pcm_s16le", vozw)
    with wave.open(vozw) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768
    n = int(round((b - a) * 1000))
    trozos.append(np.pad(x, (0, max(0, n - len(x))))[:n])
v = np.concatenate(trozos)
rms = np.sqrt(np.convolve(v ** 2, np.ones(150) / 150, mode="same"))
habla = (20 * np.log10(rms + 1e-9) > -32).astype(float)
habla = np.convolve(habla, np.ones(250) / 250, mode="same")
habla = np.interp(tt, np.arange(len(habla)) / 1000, habla, right=0)
db -= 3.0 * habla * (1 - sube)

mezcla *= (10 ** (db / 20))[:, None]
mezcla = np.clip(mezcla, -0.89, 0.89)
salida = os.path.join(PROY, "material", "musica-ambiental.wav")
escribir(salida, mezcla)
for f in (tmp, vozw):
    os.remove(f)
print(f"listo: {salida}  ({T:.2f} s, {BPM:.0f} BPM, groove en {GROOVE} s)")
