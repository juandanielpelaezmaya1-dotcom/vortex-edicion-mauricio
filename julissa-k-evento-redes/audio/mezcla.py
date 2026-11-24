"""Musica ORIGINAL + voces del recap del evento de redes de Julissa K.

    .venv/Scripts/python -I julissa-k-evento-redes/audio/mezcla.py      (desde la raiz)

Lee cache/cortes.json (lo escribe montaje.py): total, voces [(archivo, in, out, en)], tramos sin voz
("abiertos": la musica sube), "drops" (silencio de golpe antes de un momento) e "impactos".

La referencia (Awaken Summit) es cinematografica: Re menor, ~100 BPM, un colchon agudo sostenido
(un Fa alto que no se va), sub-bajo pesado, subidas de ruido antes de cada golpe y silencios secos.
Esto es una composicion propia con ese caracter, no la cancion de la referencia:
  - Progresion Dm - Bb - F - C (i - VI - III - VII), un acorde por compas de 2,4 s.
  - Colchon con el Fa5 sostenido todo el video, cuerdas graves, sub en cada compas.
  - Pulso: bombo grave en 1 y 3, toms y palmas con eco en el 3 cuando no hay voz.
  - Piano: motivo de 4 notas (A-F-E-D) solo en los tramos abiertos.
  - Subida de ruido de 2 compases antes de cada impacto; silencio (drop) 0,5 s antes del golpe.
Niveles: cama -26 LUFS bajo la voz, +12 dB en los tramos abiertos; voz a -14 LUFS.
Deja material/mezcla.wav, material/mezcla-sin-musica.wav y cache/musica-sola.wav.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

AQUI = os.path.dirname(os.path.abspath(__file__))
PROY = os.path.dirname(AQUI)
CFG = json.load(open(os.path.join(PROY, "cache", "cortes.json")))
SR = 48000
T = CFG["total"]
N = int(T * SR)
rng = np.random.default_rng(18)
BPM = 100
PULSO = 60 / BPM
COMPAS = 4 * PULSO
OCHO = PULSO / 2


def ff(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-2000:])
    return r.stderr


def escribir(ruta, x):
    x = np.clip(x, -1, 1)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def lufs_de(x):
    tmp = os.path.join(PROY, "cache", "_medir.wav")
    escribir(tmp, x)
    log = ff("-i", tmp, "-af", "ebur128", "-f", "null", "-")
    os.remove(tmp)
    return float([l for l in log.splitlines() if l.strip().startswith("I:")][-1].split()[1])


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


def lp(x, fc, orden=2):
    return sosfilt(butter(orden, fc, btype="low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, orden=2):
    return sosfilt(butter(orden, fc, btype="high", fs=SR, output="sos"), x, axis=0)


def ruido(dur, lo, hi):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= (fr > lo) & (fr < hi)
    x = np.fft.irfft(X, n)
    return x / (np.abs(x).max() + 1e-9)


def eco(x, retardo=PULSO * 0.75, fb=0.38, veces=4):
    """Eco estereo de ping-pong (mono -> estereo)."""
    d = int(retardo * SR)
    y = np.zeros((len(x) + d * veces, 2))
    y[: len(x), 0] += x
    y[: len(x), 1] += x
    for k in range(1, veces + 1):
        lado = k % 2
        y[d * k : d * k + len(x), lado] += x * fb**k
    return y


# --- instrumentos -------------------------------------------------------------------------------
def colchon(notas, dur, brillo=1800):
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        for det, lado in ((-0.1, 0), (0.1, 1), (0.03, 0), (-0.04, 1)):
            f = hz(m) * 2 ** (det / 24)
            ph = rng.uniform(0, 6)
            # sierra suave (pocas armonicas) filtrada: cuerdas sinteticas
            s = sum(np.sin(2 * np.pi * f * h * t + ph * h) / h for h in range(1, 7))
            x[:, lado] += s * 0.4
    x = lp(x, brillo)
    env = np.minimum(t / 0.6, 1) * np.minimum((dur - t) / 0.5, 1)
    return x * env[:, None] / len(notas)


def dron_alto(dur):
    """El Fa5 sostenido de la referencia: seno con vibrato lento y un poco de aire."""
    t = np.arange(int(dur * SR)) / SR
    f = hz(77) * (1 + 0.0025 * np.sin(2 * np.pi * 0.23 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.15 * np.sin(2 * ph) + 0.05 * ruido(dur, 600, 1400)
    env = np.minimum(t / 2.0, 1) * np.minimum((dur - t) / 1.0, 1)
    return x * env


def sub(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.tanh(1.6 * np.sin(2 * np.pi * f * t))
    return lp(x, 220) * np.exp(-t / 0.9) * np.minimum(t / 0.006, 1) * np.minimum((dur - t) / 0.05, 1)


def bombo(vol=1.0):
    t = np.arange(int(0.6 * SR)) / SR
    f = 42 + 120 * np.exp(-t * 30)
    return np.tanh(1.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.28) * vol


def tom(m=45):
    t = np.arange(int(0.5 * SR)) / SR
    f = hz(m) * (1 + 0.6 * np.exp(-t * 25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)


def palma():
    x = ruido(0.25, 900, 7000)
    t = np.arange(len(x)) / SR
    env = np.exp(-t / 0.08) + 0.6 * np.exp(-((t - 0.011) / 0.004) ** 2) + 0.5 * np.exp(-((t - 0.022) / 0.004) ** 2)
    return x * env


def hat():
    x = ruido(0.06, 7000, 16000)
    t = np.arange(len(x)) / SR
    return x * np.exp(-t / 0.018)


def piano(m, dur=2.2):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = sum(np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * (0.9 + 1.4 * h)) / h**1.3 for h in range(1, 8))
    return x * np.minimum(t / 0.003, 1) * np.minimum((dur - t) / 0.08, 1)


def impacto():
    """Golpe cinematografico: bombo grave + sub que cae + ruido de cola."""
    d = 3.0
    t = np.arange(int(d * SR)) / SR
    f = 30 + 70 * np.exp(-t * 6)
    boom = np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.9)
    cola = lp(ruido(d, 80, 5000), 3000) * np.exp(-t / 0.5) * 0.25
    return boom + cola


def subida(dur):
    """Ruido que sube de filtro y volumen hasta el golpe (riser)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    x = ruido(dur, 200, 15000)
    y = np.zeros(n)
    trozo = int(0.02 * SR)
    for i in range(0, n, trozo):
        c = 400 + 9000 * p[i] ** 2
        seg = x[max(0, i - 800) : i + trozo]
        y[i : i + trozo] = lp(hp(seg, c * 0.3), c)[-len(x[i : i + trozo]) :]
    y = y * p**2.2
    tono = np.sin(2 * np.pi * np.cumsum(hz(50) * (1 + 3 * p**2)) / SR) * p**2 * 0.25
    return (y / (np.abs(y).max() + 1e-9)) + tono


# --- la cancion ---------------------------------------------------------------------------------
# Dm - Bb - F - C  (raiz grave, acorde en registro medio)
PROG = [(38, [57, 62, 65]), (34, [58, 62, 65]), (41, [57, 60, 65]), (36, [55, 60, 64])]
MOTIVO = [69, 65, 64, 62]  # A F E D, una nota por pulso en el primer compas de cada par

ABIERTOS = CFG["abiertos"]          # [(a, b)] sin voz: la musica sube y entra el pulso completo
DROPS = CFG["drops"]                # segundos del golpe: silencio 0,5 s antes
IMPACTOS = CFG["impactos"]          # golpes con subida (incluye los drops)


def abierto(t):
    return any(a - 0.05 <= t < b for a, b in ABIERTOS)


def en_drop(t):
    return any(d - 0.5 <= t < d for d in DROPS)


mus = {k: np.zeros((N, 2)) for k in ("ritmo", "bajo", "colchon", "piano", "fx")}
poner(mus["colchon"], np.stack([dron_alto(T + 1)] * 2, axis=1) * np.array([0.9, 1.0]), 0, vol=0.22)

for c in range(int(np.ceil(T / COMPAS)) + 1):
    tc = c * COMPAS
    raiz, acorde = PROG[c % 4]
    poner(mus["colchon"], colchon(acorde + [acorde[0] - 12], COMPAS + 0.5), tc - 0.1, vol=0.55)
    poner(mus["bajo"], sub(raiz - 12 + 12, COMPAS * 0.95), tc, vol=0.9)
    for p in range(4):
        tp = tc + p * PULSO
        if tp >= T or en_drop(tp):
            continue
        ab = abierto(tp)
        if p in (0, 2) and (ab or p == 0):
            poner(mus["ritmo"], bombo(1.0 if p == 0 else 0.75), tp)
        if ab:
            if p == 2:
                poner(mus["ritmo"], eco(palma()), tp, vol=0.35)
            if p == 3 and c % 2:
                poner(mus["ritmo"], tom(43), tp + OCHO, pan=-0.3, vol=0.4)
            for k in range(2):
                poner(mus["ritmo"], hat(), tp + k * OCHO, pan=0.3, vol=0.12 if k else 0.07)
            if c % 2 == 0:
                poner(mus["piano"], eco(piano(MOTIVO[p] + 12)), tp, vol=0.30)
        elif p == 0 and c % 2 == 0:
            # bajo la voz: el motivo solo como una nota de piano grave por compas
            poner(mus["piano"], eco(piano(MOTIVO[0], 2.6), fb=0.3), tp, vol=0.16)

for t in IMPACTOS:
    poner(mus["fx"], np.stack([subida(COMPAS)] * 2, axis=1), t - COMPAS - (0.5 if t in DROPS else 0), vol=0.30)
    poner(mus["fx"], impacto(), t, vol=0.8)

musica = mus["ritmo"] * 0.8 + mus["bajo"] * 0.9 + mus["colchon"] * 0.7 + mus["piano"] + mus["fx"]
# drops: silencio seco (con 20 ms de fundido) 0,5 s antes de cada golpe; el dron sigue debajo bajito
gate = np.ones(N)
for d in DROPS:
    a, b = int((d - 0.5) * SR), int(d * SR)
    f = int(0.02 * SR)
    gate[a:b] = 0.12
    gate[a : a + f] = np.linspace(1, 0.12, f)
musica *= gate[:, None]
musica[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
cola = np.ones(N)
a = int((T - 2.0) * SR)
cola[a:] = np.linspace(1, 0, N - a) ** 1.6
musica *= cola[:, None]


# --- voces (testimonios y Julissa, en sincronia con sus tomas) ------------------------------------
def leer_tramo(arch, a, b):
    tmp = os.path.join(PROY, "cache", "_voz.raw")
    ff("-ss", f"{a}", "-to", f"{b}", "-i", os.path.join(PROY, arch), "-vn", "-ac", "1", "-ar", str(SR),
       "-af", "highpass=f=90,afftdn=nf=-30:nr=8,afade=t=in:d=0.04,areverse,afade=t=in:d=0.08,areverse",
       "-f", "f32le", tmp)
    x = np.fromfile(tmp, dtype="<f4").astype(float)
    os.remove(tmp)
    return x


voz = np.zeros((N, 2))
hay_voz = np.zeros(N)
for arch, a, b, en in CFG["voces"]:
    x = leer_tramo(arch, a, b)
    # cada voz nivelada por separado a -16 LUFS: vienen de micros y salas distintas
    x = x * 10 ** ((-16 - lufs_de(np.stack([x, x], 1))) / 20)
    poner(voz, np.stack([x, x], axis=1), en)
    hay_voz[int(en * SR) : int(en * SR) + len(x)] = 1

k = int(0.35 * SR)
suave = np.convolve(hay_voz, np.ones(k) / k, mode="same")
cama = 10 ** ((12 * (1 - suave)) / 20)
con_voz = hay_voz > 0
l_mus = lufs_de(musica[con_voz]) if con_voz.any() else lufs_de(musica)
musica = musica * 10 ** ((-26 - l_mus) / 20) * cama[:, None]

l_voz = lufs_de(voz[con_voz])
g = 10 ** ((-14 - l_voz) / 20)
print(f"voz {l_voz:.1f} LUFS, musica {l_mus:.1f} LUFS -> ganancia comun {20*np.log10(g):+.1f} dB")


def limitar(x, techo=0.89):
    m = np.abs(x).max()
    return x if m <= techo else np.tanh(x / techo) * techo


escribir(os.path.join(PROY, "material", "mezcla.wav"), limitar((voz + musica) * g))
escribir(os.path.join(PROY, "material", "mezcla-sin-musica.wav"), limitar(voz * g))
escribir(os.path.join(PROY, "cache", "musica-sola.wav"), limitar(musica * g))
print("listo")
