"""Musica ORIGINAL + whooshes + voz en off del recap del Dia de la Escucha a la Gestante.

    .venv/Scripts/python -I madres-lactantes-recap/audio/mezcla.py      (desde la raiz)

Lee cache/cortes.json (lo escribe montaje.py): total, cortes, capitulos y los tramos de voz.
Musica: Fa mayor, 120 BPM (pulso 0,5 s, compas 2 s), feliz y tierna. Progresion F - C - Dm - Bb.
  - 0-4      gancho sin voz: marimba con la melodia, campanita, palmas y bombo. Sube al golpe de 4 s.
  - 4-75     bajo la voz: bombo suave en 1 y 3, palmas en 2 y 4, shaker, bajo, arpegio de marimba y
             colchon. A los 34,5 (premiadas) entran pandereta y la campanita: la fiesta del evento.
  - 75-80    cierre sin voz: vuelve la melodia completa y termina en un acorde de Fa que suena hasta 80.
Efectos: whoosh suave en cada cambio de capitulo (no en todos los cortes: a un corte por segundo
cansaria); un brillo de campanitas en el titulo y en el cierre.
Niveles: cama -25 LUFS bajo la voz, +13 dB sin voz; mezcla a -14 LUFS con la ganancia de la VOZ SOLA.
Deja material/mezcla.wav y material/mezcla-sin-musica.wav.
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
rng = np.random.default_rng(22)
BPM = 120
PULSO = 60 / BPM
COMPAS = 4 * PULSO
OCHO = PULSO / 2
FIESTA = 34.5      # premiadas: entra la pandereta
CIERRE = 75.0      # sin voz
ACORDE_FINAL = 78.0


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
    return sosfilt(butter(orden, fc, btype="low", fs=SR, output="sos"), x)


def hp(x, fc, orden=2):
    return sosfilt(butter(orden, fc, btype="high", fs=SR, output="sos"), x)


def ruido(dur, lo, hi):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= (fr > lo) & (fr < hi)
    x = np.fft.irfft(X, n)
    return x / (np.abs(x).max() + 1e-9)


# --- instrumentos -------------------------------------------------------------------------------
def marimba(m, dur=0.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 40) + 0.12 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 90)
    return x * np.exp(-t / 0.22) * np.minimum(t / 0.0015, 1)


def campanita(m, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6) + 0.2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 12)
    return x * np.exp(-t / 0.55) * np.minimum(t / 0.001, 1)


def bajo(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
    return lp(x, 700) * np.exp(-t / 0.35) * np.minimum(t / 0.004, 1) * np.minimum((dur - t) / 0.02, 1)


def colchon(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        for det, lado in ((-0.12, 0), (0.12, 1), (0.04, 0), (-0.05, 1)):
            f = hz(m) * 2 ** (det / 24)
            x[:, lado] += (np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) + 0.25 * np.sin(4 * np.pi * f * t)) * 0.5
    env = np.minimum(t / 0.5, 1) * np.minimum((dur - t) / 0.4, 1)
    return x * env[:, None] / len(notas)


def bombo(vol=1.0):
    t = np.arange(int(0.35 * SR)) / SR
    f = 50 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.15) * vol


def palma():
    x = ruido(0.2, 900, 8000)
    t = np.arange(len(x)) / SR
    env = np.exp(-t / 0.06) + 0.6 * np.exp(-((t - 0.011) / 0.004) ** 2) + 0.5 * np.exp(-((t - 0.022) / 0.004) ** 2)
    return x * env


def shaker():
    x = ruido(0.08, 5000, 15000)
    t = np.arange(len(x)) / SR
    return x * np.minimum(t / 0.01, 1) * np.exp(-t / 0.025)


def pandereta():
    x = ruido(0.25, 6000, 16000)
    t = np.arange(len(x)) / SR
    jingle = sum(np.sin(2 * np.pi * f * t) for f in (7200, 8900, 10300)) / 3
    return (x * 0.6 + jingle * 0.4) * np.exp(-t / 0.07)


def whoosh(dur=0.5, pico=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    x = ruido(dur, 150, 15000)
    y = np.zeros(n)
    trozo = int(0.02 * SR)
    for i in range(0, n, trozo):
        c = 500 + 8000 * np.interp(p[i], [0, pico, 1], [0, 1, 0.35])
        seg = x[max(0, i - 800) : i + trozo]
        y[i : i + trozo] = lp(hp(seg, c * 0.35), c)[-len(x[i : i + trozo]) :]
    env = np.where(p < pico, (p / pico) ** 2.4, np.exp(-(p - pico) / (1 - pico) * 4))
    y = y * env / (np.abs(y * env).max() + 1e-9)
    pan = np.interp(p, [0, 1], [-0.7, 0.7])
    return np.stack([y * np.cos((pan + 1) * np.pi / 4), y * np.sin((pan + 1) * np.pi / 4)], axis=1) * 1.41


def brillo(en_s, buf, vol=0.25):
    """Cascada de campanitas hacia arriba (el titulo, el cierre)."""
    for j, m in enumerate([77, 81, 84, 89, 93]):
        poner(buf, campanita(m, 1.2), en_s + j * 0.06, pan=-0.5 + 0.25 * j, vol=vol)


# --- la cancion ---------------------------------------------------------------------------------
# F - C - Dm - Bb (raiz grave, acorde)
PROG = [(41, [65, 69, 72]), (36, [64, 67, 72]), (38, [62, 65, 69]), (34, [62, 65, 70])]
# melodia de 16 corcheas por compas (None = silencio), una frase de 4 compases
MEL = [
    [72, None, 69, 72, 74, 72, 69, None],
    [67, None, 69, 72, None, 69, 67, None],
    [69, None, 72, 74, 77, 74, 72, None],
    [70, None, 69, 67, 65, None, 67, None],
]
ARP = [0, 1, 2, 1, 0, 1, 2, 1]
mus = {k: np.zeros((N, 2)) for k in ("ritmo", "bajo", "colchon", "arp", "mel", "fx")}

for c in range(int(np.ceil(T / COMPAS))):
    tc = c * COMPAS
    raiz, acorde = PROG[c % 4]
    final = tc >= ACORDE_FINAL - 0.01
    sin_voz = tc < 4.0 - 0.01 or tc >= CIERRE - 0.01
    fiesta = tc >= FIESTA - 0.6
    if final:
        # acorde final: Fa mayor que suena hasta el ultimo cuadro
        for j, m in enumerate([41, 53, 65, 69, 72, 77]):
            poner(mus["mel"], marimba(m, 2.0), tc + j * 0.03, pan=-0.3 + 0.12 * j, vol=0.5)
        poner(mus["colchon"], colchon([65, 69, 72, 77], T - tc + 0.2), tc, vol=0.9)
        poner(mus["bajo"], bajo(29, 1.9), tc, vol=0.9)
        poner(mus["ritmo"], bombo(), tc)
        brillo(tc + 0.05, mus["fx"], 0.22)
        continue
    poner(mus["colchon"], colchon(acorde, COMPAS + 0.4), tc - 0.1, vol=0.55)
    for p in range(4):
        tp = tc + p * PULSO
        poner(mus["ritmo"], bombo(0.9 if p % 2 == 0 else 0.45), tp)
        if p % 2:
            poner(mus["ritmo"], palma(), tp, pan=0.05, vol=0.35)
    for k in range(8):
        tk = tc + k * OCHO
        poner(mus["ritmo"], shaker(), tk + (0.012 if k % 2 else 0), pan=0.35, vol=0.16 if k % 2 else 0.1)
        if fiesta and k % 2:
            poner(mus["ritmo"], pandereta(), tk, pan=-0.4, vol=0.14)
        # bajo saltarin: raiz, octava
        nota = raiz + (12 if k in (3, 6) else 0)
        if k in (0, 3, 4, 6):
            poner(mus["bajo"], bajo(nota, OCHO * (1.4 if k in (0, 4) else 0.9)), tk, vol=0.8)
        # arpegio de marimba (siempre) y melodia (gancho, cierre y, suave, en la fiesta)
        poner(mus["arp"], marimba(acorde[ARP[k]] + (0 if k % 4 else 12) - 12 + 12, 0.4), tk, pan=0.4 * np.sin(k * 1.3), vol=0.18 if k % 2 == 0 else 0.12)
        m = MEL[c % 4][k]
        if m is not None:
            if sin_voz:
                poner(mus["mel"], marimba(m + 12, 0.7), tk, pan=-0.15, vol=0.42)
                poner(mus["mel"], campanita(m + 24, 0.9), tk, pan=0.2, vol=0.08)
            elif fiesta and k in (0, 4):
                poner(mus["mel"], campanita(m + 12, 1.0), tk, pan=0.25, vol=0.06)

# entrada: un compas de arranque con el filtro abriendose no hace falta: el gancho entra de una
brillo(0.15, mus["fx"], 0.28)
musica = mus["ritmo"] * 0.8 + mus["bajo"] * 0.9 + mus["colchon"] * 0.5 + mus["arp"] + mus["mel"] + mus["fx"]
# el primer bombo no puede sonar cortado: fundido de 10 ms
musica[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
# cola: la ultima nota suena; fundido en los ultimos 1,2 s
cola = np.ones(N)
a = int((T - 1.2) * SR)
cola[a:] = np.linspace(1, 0, N - a) ** 1.5
musica *= cola[:, None]

# --- whooshes en los capitulos (pico en el corte) ------------------------------------------------
efx = np.zeros((N, 2))
for i, c in enumerate(CFG["capitulos"]):
    w = whoosh(0.45 + 0.05 * (i % 2), 0.62)
    if i % 2:
        w = w[:, ::-1]
    poner(efx, w, c - 0.62 * (0.45 + 0.05 * (i % 2)), vol=1.0)


# --- voz ----------------------------------------------------------------------------------------
def leer_tramo(a, b):
    tmp = os.path.join(PROY, "cache", "_voz.raw")
    src = os.path.join(PROY, "material", "C20261122_5748.MP4")
    ff("-ss", f"{a}", "-to", f"{b}", "-i", src, "-vn", "-ac", "1", "-ar", str(SR),
       "-af", "highpass=f=90,afftdn=nf=-30:nr=10,afade=t=in:d=0.05,areverse,afade=t=in:d=0.08,areverse",
       "-f", "f32le", tmp)
    x = np.fromfile(tmp, dtype="<f4")
    os.remove(tmp)
    return x


voz = np.zeros((N, 2))
hay_voz = np.zeros(N)
for a, b, en in CFG["voz"]:
    x = leer_tramo(a, b)
    poner(voz, np.stack([x, x], axis=1), en)
    hay_voz[int(en * SR) : int(en * SR) + len(x)] = 1

# cama: -25 LUFS bajo la voz, +13 dB sin voz (con rampas de 0,3 s para no saltar)
k = int(0.3 * SR)
suave = np.convolve(hay_voz, np.ones(k) / k, mode="same")
cama = 10 ** ((13 * (1 - suave)) / 20)
l_mus = lufs_de(musica[int(4 * SR) : int(CIERRE * SR)])
g_mus = 10 ** ((-25 - l_mus) / 20)
musica = musica * g_mus * cama[:, None]

l_voz = lufs_de(voz[int(4 * SR) : int(CIERRE * SR)])
g = 10 ** ((-14 - l_voz) / 20)
print(f"voz {l_voz:.1f} LUFS, musica {l_mus:.1f} LUFS -> ganancia comun {20*np.log10(g):+.1f} dB")
efx_n = efx / (np.abs(efx).max() + 1e-9) * 0.5 * 10 ** (-3 / 20)


def limitar(x, techo=0.89):
    m = np.abs(x).max()
    return x if m <= techo else np.tanh(x / techo) * techo


escribir(os.path.join(PROY, "material", "mezcla.wav"), limitar((voz + musica + efx_n) * g))
escribir(os.path.join(PROY, "material", "mezcla-sin-musica.wav"), limitar((voz + efx_n) * g))
escribir(os.path.join(PROY, "cache", "musica-sola.wav"), limitar(musica * g))
print("listo")
