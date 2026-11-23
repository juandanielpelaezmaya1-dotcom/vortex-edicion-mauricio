"""Musica ORIGINAL melancolica de dejaste-huella-resumen (pedido de Mauricio, 22-nov:
"mas melancolica"; reemplaza a musica-alegre.wav, que se queda en material/ por si se vuelve).

    .venv/Scripts/python -I dejaste-huella-resumen/audio/musica-melancolica.py      (desde la raiz)

La menor a 68 BPM. Piano de fieltro, cuerdas (aditivas con vibrato) y chelo.
  - Gancho en blanco y negro (clips 1-2): solo un bordon grave de cuerdas y notas sueltas de
    piano con mucha sala, debajo de la voz de megafono.
  - La historia (desde el paso a color): arpegio lento de piano, cuerdas y chelo, sobre
    Am(add9) - Fmaj7 - C - G - Am - Fmaj7 - Dm7 - Esus4/E.
  - Desde "estabamos solos" (clip 9) entra una melodia en la mano derecha; desde "es un acto de
    amor" (clip 13) las cuerdas suben una octava. En el apoyo baja a lo minimo y en el logo
    cierra en La menor con la novena arriba.
Niveles horneados (manifest con volumen 1): cama a -10 dB de la referencia (-16 LUFS), -3 dB
mientras alguien habla, sube en el logo. La voz para el ducking se arma con lo que de verdad
suena en cada tramo (gancho-megafono.wav, el audio de la toma o la pista del apoyo).
Deja material/musica-melancolica.wav.
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
DUR = [(c["out_s"] - c.get("in_s", 0)) / c.get("velocidad", 1) for c in M["clips"]]
INI = np.concatenate([[0], np.cumsum(DUR)])
SR = 48000
T = float(INI[-1]) + 0.1
N = int(T * SR)
rng = np.random.default_rng(31)

HISTORIA = float(INI[2])  # el gancho son los clips 1-2
MELODIA_DESDE = float(INI[8])  # clip 9: "estabamos solos"
SUBEN = float(INI[12])  # clip 13: "es un acto de amor"
APOYO = float(INI[-2]) if M["clips"][-2].get("volumen") == 0 else None
LOGO = float(INI[len(DUR) - 1])  # entra el logo (ultimo clip)

BPM = 68.0
PULSO = 60.0 / BPM
COMPAS = 4 * PULSO
T0 = HISTORIA - 3 * COMPAS  # tres compases de gancho; el 4 cae en el paso a color


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
    if x.ndim == 2:
        buf[i : i + len(x)] += x * vol
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i : i + len(x), 0] += x * vol * l * 1.41
    buf[i : i + len(x), 1] += x * vol * r * 1.41


def piano(m, dur=3.0, suave=1.0):
    """Piano de fieltro: ataque blando, armonicos que se apagan rapido, cola larga."""
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 1.6)
         + 0.28 * np.sin(2 * np.pi * 2.002 * f * t) * np.exp(-t / 0.5)
         + 0.08 * np.sin(2 * np.pi * 3.006 * f * t) * np.exp(-t / 0.22))
    return x * np.minimum(t / (0.006 * suave), 1) * np.minimum((dur - t) / 0.1, 1)


def cuerdas(notas, dur, ataque=1.2, brillo=2200):
    """Seccion de cuerdas: sierras suavizadas con vibrato y voces desafinadas, estereo."""
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        for det, lado in ((-0.07, 0), (0.07, 1), (0.0, 0), (0.03, 1)):
            f = hz(m) * 2 ** (det / 12)
            vib = 1 + 0.004 * np.sin(2 * np.pi * (5.0 + rng.uniform(-0.4, 0.4)) * t + rng.uniform(0, 6))
            fase = 2 * np.pi * np.cumsum(f * vib) / SR
            v = sum(np.sin(k * fase) / k for k in range(1, 9))
            x[:, lado] += v * 0.35
    x = sosfilt(butter(2, brillo, btype="low", fs=SR, output="sos"), x, axis=0)
    env = np.minimum(t / ataque, 1) * np.minimum((dur - t) / 1.0, 1)
    return x * env[:, None] / len(notas)


def chelo(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    vib = 1 + 0.003 * np.sin(2 * np.pi * 4.6 * t)
    fase = 2 * np.pi * np.cumsum(f * vib) / SR
    x = sum(np.sin(k * fase) / (k ** 1.3) for k in range(1, 7))
    x = sosfilt(butter(2, 900, btype="low", fs=SR, output="sos"), x)
    return x * np.minimum(t / 0.5, 1) * np.minimum((dur - t) / 0.6, 1)


# (pad de cuerdas, arpegio de piano en negras x2, raiz del chelo)
ACORDES = {
    "Am": ([57, 60, 64, 71], [45, 52, 59, 60, 64, 60, 59, 52], 33),
    "F": ([57, 60, 64, 65], [41, 48, 55, 57, 64, 57, 55, 48], 29),
    "C": ([55, 60, 64, 67], [36, 43, 52, 55, 60, 55, 52, 43], 36),
    "G": ([55, 59, 62, 67], [43, 50, 57, 59, 62, 59, 57, 50], 31),
    "Dm": ([57, 60, 62, 65], [38, 45, 53, 57, 60, 57, 53, 45], 38),
    "E": ([56, 59, 64, 69], [40, 47, 56, 59, 64, 59, 56, 47], 40),  # Esus4 en el pad
}
CICLO = ["Am", "F", "C", "G", "Am", "F", "Dm", "E"]
MELODIA = {  # (corchea, midi) en la mano derecha, sobre el ciclo
    0: [(0, 76), (4, 72), (6, 71)],
    1: [(0, 69), (6, 72)],
    2: [(0, 72), (2, 74), (4, 76)],
    3: [(0, 74), (4, 71)],
    4: [(0, 76), (3, 77), (4, 76), (6, 72)],
    5: [(0, 72), (4, 69)],
    6: [(0, 69), (2, 72), (4, 74)],
    7: [(0, 71), (4, 68)],
}

pads, pianos, graves, mel = (np.zeros((N, 2)) for _ in range(4))
ocho = PULSO / 2

# Gancho: bordon de La (A1 + E2 en cuerdas oscuras) y notas sueltas de piano con mucha sala
poner(pads, cuerdas([33, 40, 45], HISTORIA + 1.5, ataque=2.0, brillo=700), 0.0, vol=1.4)
for k, (cuando, m) in enumerate([(0.0, 69), (1.5, 76), (3.4, 72), (5.0, 71), (6.9, 69), (8.6, 64), (9.8, 72)]):
    poner(pianos, piano(m, 3.5), T0 + cuando * PULSO * 1.0 + 0.4, pan=-0.2 + 0.1 * (k % 4), vol=0.5)

c = 0
while True:
    t_c = HISTORIA + c * COMPAS
    if t_c > T - 0.5:
        break
    final = t_c >= LOGO - 0.3
    en_apoyo = APOYO is not None and APOYO - 0.2 <= t_c < LOGO - 0.3
    nombre = "Am" if final else CICLO[c % 8]
    pad_n, arp, raiz = ACORDES[nombre]
    if nombre == "E":
        pad_n = [57, 59, 64, 69]  # sus4 que resuelve a mitad de compas en el arpegio
    alto = 12 if t_c >= SUBEN - 0.05 and not en_apoyo else 0
    poner(pads, cuerdas([n + alto for n in pad_n], COMPAS + 1.2, brillo=2600 if alto else 2000), t_c - 0.3, vol=0.9)
    poner(graves, chelo(raiz, COMPAS + 0.3), t_c, vol=0.55)
    for k, m in enumerate(arp):
        if en_apoyo and k % 2:
            continue  # en el apoyo, la mitad de las notas
        poner(pianos, piano(m, 2.6), t_c + k * ocho, pan=-0.3 + 0.08 * k, vol=0.30 if k % 4 == 0 else 0.2)
    if t_c >= MELODIA_DESDE - 0.05 and not en_apoyo and not final:
        for paso, m in MELODIA[c % 8]:
            poner(mel, piano(m, 3.0), t_c + paso * ocho, pan=0.25, vol=0.33)
    c += 1

# Cierre en el logo: La menor con la novena arriba
for j, m in enumerate([33, 45, 52, 60, 64, 71]):
    poner(pianos, piano(m, 4.5), LOGO + 0.6 + j * 0.05, pan=-0.3 + 0.12 * j, vol=0.32)

mezcla = pads * 0.6 + pianos + graves * 0.7 + mel
ir_n = int(2.4 * SR)
ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / 0.7)[:, None]
ir = sosfilt(butter(2, 5000, btype="low", fs=SR, output="sos"), ir, axis=0)
ir /= np.sqrt((ir ** 2).sum(axis=0))
humedo = np.stack([fftconvolve((pianos + mel + pads * 0.4)[:, i], ir[:, i])[:N] for i in range(2)], axis=1)
mezcla = mezcla + 0.32 * humedo

os.makedirs(os.path.join(PROY, "cache"), exist_ok=True)
tmp = os.path.join(PROY, "cache", "_musica_pre.wav")
escribir(tmp, mezcla / (np.abs(mezcla).max() + 1e-9) * 0.7)
mezcla = mezcla / (np.abs(mezcla).max() + 1e-9) * 0.7 * 10 ** ((-16 - lufs(tmp)) / 20)

# Curva de nivel (dB sobre -16 LUFS)
t = np.arange(N) / SR
db = np.where(t < HISTORIA, -7.0, -10.0)
db = np.where(t < 0.3, db - 25 * (0.3 - t) / 0.3, db)
sube = np.clip((t - (LOGO + 0.1)) / 0.8, 0, 1)
db = db * (1 - sube) - 2.0 * sube
db -= np.clip((t - (T - 1.6)) / 1.5, 0, 1) * 30

# Ducking: -3 dB mientras alguien habla, con la voz que suena de verdad en cada tramo
vozw = os.path.join(PROY, "cache", "_voz_env.wav")


def env_de(archivo, a, b):
    ff("-ss", f"{a}", "-to", f"{b}", "-i", os.path.join(PROY, archivo), "-vn", "-ac", "1", "-ar", "1000", "-c:a", "pcm_s16le", vozw)
    with wave.open(vozw) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768
    n = int(round((b - a) * 1000))
    return np.pad(x, (0, max(0, n - len(x))))[:n]


v = np.zeros(int(T * 1000) + 1)
for i, cl in enumerate(M["clips"][:-1]):
    ini, d = float(INI[i]), DUR[i]
    if cl.get("volumen") == 0:
        p = next((p for p in M.get("pistas", []) if p["en_s"] - 0.05 <= ini < p["en_s"] + p["out_s"] - p["in_s"]), None)
        if p is None:
            continue
        a = p["in_s"] + (ini - p["en_s"])
        x = env_de(p["archivo"], a, a + d)
    else:
        x = env_de(cl["archivo"], cl.get("in_s", 0), cl["out_s"])
    k = int(round(ini * 1000))
    v[k : k + len(x)] = x[: len(v) - k]
rms = np.sqrt(np.convolve(v ** 2, np.ones(150) / 150, mode="same"))
habla = (20 * np.log10(rms + 1e-9) > -32).astype(float)
habla = np.convolve(habla, np.ones(250) / 250, mode="same")
habla = np.interp(t, np.arange(len(habla)) / 1000, habla, right=0)
db -= 3.0 * habla * (1 - sube)

mezcla *= (10 ** (db / 20))[:, None]
mezcla = np.clip(mezcla, -0.89, 0.89)
salida = os.path.join(PROY, "material", "musica-melancolica.wav")
escribir(salida, mezcla)
for f in (tmp, vozw):
    os.remove(f)
print(f"listo: {salida}  ({T:.2f} s, {BPM:.0f} BPM, historia en {HISTORIA:.2f} s, logo en {LOGO:.2f} s)")
