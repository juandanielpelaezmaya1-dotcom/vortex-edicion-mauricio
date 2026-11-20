"""Musica ORIGINAL de dejaste-huella-resumen: alegre y calida, sin tristeza.

    .venv/Scripts/python -I dejaste-huella-resumen/audio/musica.py      (desde la raiz)

Re mayor a 112 BPM, I-V-vi-IV (D A Bm G): ukelele rasgueado, bajo redondo, bombo y
palmas suaves, shaker, y una campanita con la melodia en los tramos con menos voz.
El compas 5 cae donde termina el gancho (las dos primeras tomas) y empieza la historia:
ahi entra el ritmo completo. Cuando termina la ultima toma con voz (entra el logo) la
musica sube y cierra en un acorde de Re.

Los tiempos salen de manifest.json: si cambian los cortes, basta volver a correrlo.
Los niveles van horneados en el archivo (el manifest la usa con volumen 1): cama a
~-27 LUFS bajo la voz, 3 dB menos mientras alguien habla (envolvente medida sobre el audio
de las tomas tal como quedan en la linea de tiempo) y -16 LUFS al final.
Deja material/musica-alegre.wav (material/ no viaja por git).
"""
import json
import os
import subprocess
import sys

import numpy as np
from scipy.signal import fftconvolve

AQUI = os.path.dirname(os.path.abspath(__file__))
PROY = os.path.dirname(AQUI)
M = json.load(open(os.path.join(PROY, "manifest.json"), encoding="utf-8"))
CLIPS = [(c["archivo"], c.get("in_s", 0), c["out_s"]) for c in M["clips"]]
SR = 48000
T = sum(b - a for _, a, b in CLIPS) + 0.1
N = int(T * SR)
rng = np.random.default_rng(11)

BPM = 112.0
PULSO = 60.0 / BPM
COMPAS = 4 * PULSO
INICIO_HISTORIA = sum(b - a for _, a, b in CLIPS[:2])
T0 = INICIO_HISTORIA - 5 * COMPAS  # el compas 5 cae donde empieza la historia
ULTIMA_PALABRA = sum(b - a for _, a, b in CLIPS[:-1])  # el ultimo clip es el logo


def ff(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-2000:])
    return r.stderr


def lufs(ruta):
    log = ff("-i", ruta, "-af", "ebur128", "-f", "null", "-")
    return float([l for l in log.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def escribir(ruta, x):
    import wave
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
    if i >= N or en_s < 0:
        return
    x = x[: N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i : i + len(x), 0] += x * vol * l * 1.41
    buf[i : i + len(x), 1] += x * vol * r * 1.41


_cache = {}


def ukelele(m, dur=1.1):
    """Cuerda pulsada (Karplus-Strong vectorizado por periodo): brillante y corta."""
    if m in _cache:
        return _cache[m]
    p = int(round(SR / hz(m)))
    n = int(dur * SR)
    y = np.zeros(n + p + 1)
    y[: p + 1] = rng.uniform(-1, 1, p + 1)
    y[: p + 1] -= y[: p + 1].mean()
    k = p + 1
    while k < n + p + 1:
        fin = min(k + p, n + p + 1)
        a = y[k - p : fin - p]
        b = y[k - p - 1 : fin - p - 1]
        y[k:fin] = 0.497 * (a + b)
        k = fin
    x = y[p + 1 : p + 1 + n]
    x *= np.exp(-np.arange(n) / SR / 0.45)
    _cache[m] = x / (np.abs(x).max() + 1e-9)
    return _cache[m]


def campana(m, dur=1.4):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t + 1.2 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t * 9))
    x += 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 4)
    return x * np.minimum(t / 0.003, 1) * np.exp(-t / 0.45)


def bajo(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return x * np.minimum(t / 0.008, 1) * np.exp(-t / 0.5) * np.minimum((dur - t) / 0.03, 1)


def bombo():
    t = np.arange(int(0.35 * SR)) / SR
    f = 52 + 90 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)


def ruido_filtrado(dur, bajo_hz, alto_hz, caida):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= (fr > bajo_hz) & (fr < alto_hz)
    x = np.fft.irfft(X, n)
    x /= np.abs(x).max() + 1e-9
    return x * np.exp(-np.arange(n) / SR / caida)


def palma():
    x = np.zeros(int(0.25 * SR))
    for d in (0.0, 0.011, 0.022):  # tres golpes muy juntos: suena a palmas de varias manos
        r = ruido_filtrado(0.2, 900, 5000, 0.035)
        i = int(d * SR)
        x[i : i + len(r)] += r[: len(x) - i]
    return x / np.abs(x).max()


def shaker():
    return ruido_filtrado(0.07, 6000, 14000, 0.02)


# Acordes (ukelele, voicing alto y abierto) y raiz del bajo
ACORDES = {
    "D": ([62, 66, 69, 74], 38),
    "A": ([61, 64, 69, 73], 45),
    "Bm": ([62, 66, 71, 74], 47),
    "G": ([62, 67, 71, 74], 43),
}
CICLO = ["D", "A", "Bm", "G"]
# Melodia de campana, 4 compases (pulso en corcheas: (inicio en corcheas, midi))
MELODIA = [
    [(0, 78), (2, 81), (3, 83), (4, 81), (6, 78)],
    [(0, 76), (2, 73), (4, 76), (6, 78)],
    [(0, 78), (2, 74), (3, 76), (4, 78), (6, 83)],
    [(0, 79), (2, 78), (4, 76), (6, 74)],
]
RASGUEO = [(0, "b", 1.0), (2, "b", 0.8), (3, "s", 0.55), (5, "s", 0.6), (6, "b", 0.85), (7, "s", 0.5)]

ukes = np.zeros((N, 2))
ritmo = np.zeros((N, 2))
graves = np.zeros((N, 2))
campanas = np.zeros((N, 2))
K, P, S = bombo(), palma(), shaker()

n_compases = int((T - T0) / COMPAS) + 1
for c in range(n_compases):
    t_c = T0 + c * COMPAS
    if t_c > T - 0.5:
        break
    final = t_c >= ULTIMA_PALABRA - 0.3  # el cierre con el logo
    nombre = CICLO[c % 4]
    if final and t_c + COMPAS > T - 0.4:
        nombre = "D"
    notas, raiz = ACORDES[nombre]
    ocho = PULSO / 2
    gancho = c < 5

    # Ukelele: en el gancho solo los golpes largos, luego el rasgueo entero
    for paso, sentido, vel in RASGUEO:
        if gancho and paso not in (0, 3, 6):
            continue
        orden = notas if sentido == "b" else notas[::-1]
        for j, m in enumerate(orden):
            poner(ukes, ukelele(m), t_c + paso * ocho + j * 0.011, pan=-0.25 + 0.15 * j, vol=0.22 * vel)
    if gancho:
        continue

    # Bajo: raiz en 1 y en el "y" del 2, quinta en el 4
    for paso, m, d in ((0, raiz, 0.5), (3, raiz, 0.25), (6, raiz + 7, 0.25)):
        poner(graves, bajo(m, d), t_c + paso * ocho, vol=0.55)
    # Bombo en 1 y 3, palmas en 2 y 4, shaker en corcheas
    for p in (0, 2):
        poner(ritmo, K, t_c + p * PULSO, vol=0.8)
    for p in (1, 3):
        poner(ritmo, P, t_c + p * PULSO, pan=0.1, vol=0.28)
    for k in range(8):
        poner(ritmo, S, t_c + k * ocho, pan=0.35, vol=0.12 if k % 2 else 0.2)
    # Campana: en un ciclo de cada dos, y siempre en el cierre
    if final or (c // 4) % 2 == 1:
        for paso, m in MELODIA[c % 4]:
            poner(campanas, campana(m), t_c + paso * ocho, pan=0.3, vol=0.16)

# Acorde final de Re (con campana arriba) sobre el logo
t_fin = T0 + int((T - 1.2 - T0) / COMPAS) * COMPAS + 2 * PULSO
for j, m in enumerate(ACORDES["D"][0] + [78]):
    poner(ukes, ukelele(m, 1.5), t_fin + j * 0.018, pan=-0.2 + 0.1 * j, vol=0.25)
poner(campanas, campana(86, 1.2), t_fin, pan=0.3, vol=0.18)
poner(graves, bajo(38, 1.2), t_fin, vol=0.6)

mezcla = ukes + ritmo * 0.9 + graves * 0.8 + campanas
# Sala corta y calida (no catedral): IR de ruido con caida de 0,9 s
ir_n = int(0.9 * SR)
ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / 0.25)[:, None]
ir /= np.sqrt((ir**2).sum(axis=0))
humedo = np.stack([fftconvolve((ukes + campanas)[:, i], ir[:, i])[:N] for i in range(2)], axis=1)
mezcla = mezcla + 0.18 * humedo

# Nivel de referencia: toda la pieza a -16 LUFS
os.makedirs(os.path.join(PROY, "cache"), exist_ok=True)
tmp = os.path.join(PROY, "cache", "_musica_pre.wav")
escribir(tmp, mezcla / (np.abs(mezcla).max() + 1e-9) * 0.7)
mezcla = mezcla / (np.abs(mezcla).max() + 1e-9) * 0.7 * 10 ** ((-16 - lufs(tmp)) / 20)

# Curva de nivel en dB: gancho +2,5 (solo ukelele), cama -9, y sube a -1,5 despues de la ultima palabra
t = np.arange(N) / SR
db = np.where(t < INICIO_HISTORIA, 2.5, -9.0)  # el gancho es solo ukelele: necesita mas ganancia
db = np.where(t < 0.6, 2.5 - 30 * (0.6 - t) / 0.6, db)  # entrada suave
sube = np.clip((t - (ULTIMA_PALABRA + 0.15)) / 0.8, 0, 1)
db = db * (1 - sube) - 1.5 * sube

# Ducking: -3 dB mientras alguien habla. La voz se arma con el audio de cada toma del
# manifest, en orden y con su duracion exacta (el logo cuenta como silencio).
import wave
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
ventana = 150  # ms
rms = np.sqrt(np.convolve(v**2, np.ones(ventana) / ventana, mode="same"))
habla = (20 * np.log10(rms + 1e-9) > -32).astype(float)
habla = np.convolve(habla, np.ones(250) / 250, mode="same")  # suaviza ~250 ms
habla = np.interp(t, np.arange(len(habla)) / 1000, habla)
db -= 3.0 * habla * (1 - sube)

mezcla *= (10 ** (db / 20))[:, None]
mezcla = np.clip(mezcla, -0.89, 0.89)
salida = os.path.join(PROY, "material", "musica-alegre.wav")
escribir(salida, mezcla)
for f in (tmp, vozw):
    os.remove(f)
print(f"listo: {salida}  ({T} s, {BPM:.0f} BPM, compas 5 en {INICIO_HISTORIA} s)")
