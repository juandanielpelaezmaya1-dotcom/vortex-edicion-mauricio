"""Musica ORIGINAL + efectos de transicion + voz del Video 04 de tips de Accion Juridica.

    .venv/Scripts/python -I video-04-tips-abogados/audio/mezcla.py      (desde la raiz)

La musica es de suspenso que se resuelve (Re menor, 91,25 BPM: los compases caen en 9,42 s
"son 100 % tuyos" y en 25,2 s, la entrada del logo):
  - 0-7,2 s   pulso grave en corcheas, tic de reloj y un dron: algo importante se va a decir.
  - 7,2-9,4   "no se dividen": el filtro se abre, un riser sube y corta en seco 0,1 s antes.
  - 9,42      golpe grave + entra el ritmo (bombo, palmas suaves) y el arpegio: la revelacion.
  - 22,9-25,2 sin voz (la abogada firmando): la musica sube y llega al golpe del logo.
  - 25,2-     acorde final que se apaga bajo el sonido propio del logo.
Efectos: un whoosh por corte (pico en el corte), con variantes; el del logo es un barrido
inverso. Todo se mezcla con la voz original del video (que ya trae el sonido del logo).
Niveles horneados: cama -25 LUFS bajo la voz, sube sin voz, y la mezcla se lleva a -14 LUFS
con la ganancia que mide la VOZ SOLA (S2: los golpes no entran en la medicion).
Deja material/mezcla.wav (la que usa el manifest) y material/mezcla-sin-musica.wav.
"""
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

AQUI = os.path.dirname(os.path.abspath(__file__))
PROY = os.path.dirname(AQUI)
VIDEO = os.path.join(PROY, "material", "video-04.mp4")
SR = 48000
T = 34.2
N = int(T * SR)
rng = np.random.default_rng(4)

CORTES = [3.28, 5.16, 7.16, 10.96, 13.12, 15.32, 17.28, 19.04, 22.92, 25.2]
REVELA = 9.42      # "Son 100 % tuyos"
FIN_VOZ = 22.92
LOGO = 25.2
BPM = 91.25
PULSO = 60 / BPM
COMPAS = 4 * PULSO


def ff(*args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-2000:])
    return r.stderr


def lufs_de(x):
    tmp = os.path.join(PROY, "cache", "_medir.wav")
    escribir(tmp, x, limpio=True)
    log = ff("-i", tmp, "-af", "ebur128", "-f", "null", "-")
    os.remove(tmp)
    return float([l for l in log.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def escribir(ruta, x, limpio=False):
    x = np.clip(x, -1, 1)
    with wave.open(ruta, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def leer_voz():
    tmp = os.path.join(PROY, "cache", "_voz.raw")
    ff("-i", VIDEO, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", tmp)
    x = np.fromfile(tmp, dtype="<f4").reshape(-1, 2)
    os.remove(tmp)
    out = np.zeros((N, 2))
    out[: min(N, len(x))] = x[:N]
    return out


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


def sierra(f, t):
    x = np.zeros_like(t)
    for k in range(1, 14):
        x += (-1) ** (k + 1) * np.sin(2 * np.pi * k * f * t) / k
    return x * 0.6


def lp(x, fc, orden=2):
    sos = butter(orden, fc, btype="low", fs=SR, output="sos")
    return sosfilt(sos, x)


def hp(x, fc, orden=2):
    sos = butter(orden, fc, btype="high", fs=SR, output="sos")
    return sosfilt(sos, x)


def ruido(dur, lo, hi):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= (fr > lo) & (fr < hi)
    x = np.fft.irfft(X, n)
    return x / (np.abs(x).max() + 1e-9)


# --- instrumentos ---------------------------------------------------------------------------------
def pulso_grave(m, dur, brillo):
    """Nota corta del ostinato: sierra filtrada con envolvente seca (el corazon del suspenso)."""
    t = np.arange(int(dur * SR)) / SR
    x = sierra(hz(m), t) + 0.5 * np.sin(2 * np.pi * hz(m - 12) * t)
    x = lp(x, 300 + 2200 * brillo)
    return x * np.exp(-t / 0.11) * np.minimum(t / 0.003, 1)


def dron(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        for det, lado in ((-0.1, 0), (0.1, 1), (0.03, 0), (-0.04, 1)):
            x[:, lado] += np.sin(2 * np.pi * hz(m) * 2 ** (det / 24) * t + rng.uniform(0, 6)) * 0.5
    env = np.minimum(t / 1.2, 1) * np.minimum((dur - t) / 1.0, 1)
    return x * env[:, None] / len(notas)


def tic(agudo=True):
    t = np.arange(int(0.05 * SR)) / SR
    f = 3200 if agudo else 2200
    return (np.sin(2 * np.pi * f * t) * 0.6 + ruido(0.05, 3000, 9000) * 0.4) * np.exp(-t / 0.008)


def bombo(caida=0.18, f0=46):
    t = np.arange(int(0.45 * SR)) / SR
    f = f0 + 90 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / caida)


def palma():
    x = ruido(0.18, 900, 7000)
    t = np.arange(len(x)) / SR
    env = np.exp(-t / 0.05) + 0.6 * np.exp(-((t - 0.012) / 0.004) ** 2) + 0.5 * np.exp(-((t - 0.024) / 0.004) ** 2)
    return x * env


def pluck(m, dur=0.9):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t + 1.2 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 9))
    return x * np.exp(-t / 0.28) * np.minimum(t / 0.002, 1)


def impacto(dur=2.4):
    """Golpe cinematografico: sub que cae + cuerpo de ruido grave + cola."""
    t = np.arange(int(dur * SR)) / SR
    f = 32 + 70 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    cuerpo = lp(ruido(dur, 40, 3000), 900) * np.exp(-t / 0.12) * 0.7
    cola = lp(ruido(dur, 200, 6000), 2500) * np.exp(-t / 0.9) * 0.12
    return (sub + cuerpo + cola) * np.minimum(t / 0.002, 1)


def riser(dur):
    t = np.arange(int(dur * SR)) / SR
    p = t / dur
    x = ruido(dur, 300, 14000)
    # ruido que se abre + tono que sube
    y = np.zeros_like(x)
    trozo = int(0.05 * SR)
    for i in range(0, len(x), trozo):
        fc = 400 + 9000 * p[i] ** 2
        y[i : i + trozo] = lp(x[i : i + trozo + 2000], fc)[:trozo][: len(y[i : i + trozo])]
    tono = np.sin(2 * np.pi * np.cumsum(180 + 900 * p ** 2) / SR) * 0.25
    return (y * 0.8 + tono) * p ** 2.2


def whoosh(dur=0.55, pico=0.62, lo=500, hi=9000, grave=False):
    """Aire que pasa: ruido con banda que barre, sube hasta el pico y cae rapido. Pico = fraccion."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    x = ruido(dur, 150, 15000)
    y = np.zeros(n)
    trozo = int(0.02 * SR)
    for i in range(0, n, trozo):
        c = lo + (hi - lo) * np.interp(p[i], [0, pico, 1], [0, 1, 0.35])
        seg = x[max(0, i - 800) : i + trozo]
        z = lp(hp(seg, c * 0.35), c)[-len(x[i : i + trozo]) :]
        y[i : i + trozo] = z
    env = np.where(p < pico, (p / pico) ** 2.4, np.exp(-(p - pico) / (1 - pico) * 4))
    y = y * env
    if grave:
        y += np.sin(2 * np.pi * np.cumsum(90 - 40 * p) / SR) * env * 0.5
    y /= np.abs(y).max() + 1e-9
    # estereo que viaja de un lado a otro
    pan = np.interp(p, [0, 1], [-0.7, 0.7])
    return np.stack([y * np.cos((pan + 1) * np.pi / 4), y * np.sin((pan + 1) * np.pi / 4)], axis=1) * 1.41


# --- musica -------------------------------------------------------------------------------------
mus = {k: np.zeros((N, 2)) for k in ("pulso", "dron", "tic", "ritmo", "arp", "fx")}
T0 = REVELA - 4 * COMPAS  # el compas 4 cae en la revelacion
ocho = PULSO / 2
# Dm - Bb - Gm - A, el ostinato recorre la raiz con una nota de paso
PROG = [(50, [62, 65, 69, 74]), (46, [62, 65, 70, 74]), (43, [62, 67, 70, 74]), (45, [61, 64, 69, 73])]
OSTI = [0, 0, 12, 0, 0, 7, 0, 10]
ARP = [0, 1, 2, 3, 2, 1, 2, 3]

c = -1
while True:
    tc = T0 + c * COMPAS
    if tc > T:
        break
    raiz, acorde = PROG[c % 4]
    despues = tc >= REVELA - 0.05
    final = tc >= LOGO - 0.05
    if not final:
        # ostinato grave: se va abriendo hasta la revelacion
        for k in range(8):
            tk = tc + k * ocho
            brillo = float(np.clip((tk - 0) / REVELA, 0, 1)) ** 1.5 * 0.6 + (0.35 if despues else 0)
            poner(mus["pulso"], pulso_grave(raiz + OSTI[k] - 12, ocho * 0.95, brillo), tk, pan=0.15 * np.sin(k), vol=0.55 if k % 2 == 0 else 0.4)
        # tic de reloj: la cuenta atras hasta la revelacion; despues mas suave
        for k in range(8):
            tk = tc + k * ocho
            if tk < REVELA - 0.15 or despues:
                poner(mus["tic"], tic(k % 2 == 0), tk, pan=0.45, vol=(0.22 if k % 2 == 0 else 0.13) * (0.6 if despues else 1))
    if tc + COMPAS > 0 and not final:
        poner(mus["dron"], dron([raiz + 12, *acorde[:3]], COMPAS + 1.0), tc - 0.3, vol=0.5)
    if despues and not final:
        for p in range(4):
            poner(mus["ritmo"], bombo(), tc + p * PULSO, vol=0.7)
            if p % 2:
                poner(mus["ritmo"], palma(), tc + p * PULSO, pan=-0.1, vol=0.22)
        poner(mus["ritmo"], bombo(), tc + 3.5 * PULSO, vol=0.4)
        for k in range(8):
            poner(mus["arp"], pluck(acorde[ARP[k]] + 12), tc + k * ocho, pan=0.4 * np.sin(k * 1.3), vol=0.2 if k % 2 == 0 else 0.13)
    c += 1

# antes de la revelacion: corazon (bombo grave en 1 y "y" del 1) desde el primer corte
for tc in np.arange(T0, REVELA - 0.3, COMPAS):
    if tc >= CORTES[0] - 0.05:
        poner(mus["ritmo"], bombo(0.14, 40), tc, vol=0.55)
        poner(mus["ritmo"], bombo(0.12, 40), tc + 0.75 * PULSO, vol=0.35)

# riser de "no se dividen" que corta en seco justo antes de la revelacion
r = riser(REVELA - 0.1 - 7.3)
poner(mus["fx"], np.stack([r, np.roll(r, 300)], axis=1) * 0.5, 7.3)
poner(mus["fx"], impacto(), REVELA, vol=0.9)
# el silencio de 0,1 s antes del golpe: apaga pulso/tic/dron en ese hueco
hueco = np.ones(N)
a, b = int((REVELA - 0.12) * SR), int(REVELA * SR)
hueco[a:b] = np.linspace(1, 0.05, b - a)

# sin voz (22,9-25,2): riser corto hacia el logo, golpe y acorde final
r2 = riser(LOGO - 0.05 - 23.4)
poner(mus["fx"], np.stack([r2, np.roll(r2, 300)], axis=1) * 0.45, 23.4)
poner(mus["fx"], impacto(3.5), LOGO, vol=0.8)
for j, m in enumerate([38, 50, 57, 62, 65, 69, 74]):
    poner(mus["arp"], pluck(m, 4.0), LOGO + j * 0.025, pan=-0.3 + 0.1 * j, vol=0.22)
poner(mus["dron"], dron([50, 57, 62, 65], 6.5), LOGO - 0.1, vol=0.55)

musica = (mus["pulso"] * 0.9 + mus["dron"] * 0.55 + mus["tic"] + mus["ritmo"] + mus["arp"]) * hueco[:, None] + mus["fx"]

# --- efectos de transicion: un whoosh por corte, pico en el corte ----------------------------------
efx = np.zeros((N, 2))
for i, corte in enumerate(CORTES):
    if corte == LOGO:
        w = whoosh(0.9, 0.85, 300, 7000, grave=True)  # barrido inverso que desemboca en el golpe del logo
        poner(efx, w, corte - 0.85 * 0.9, vol=0.42)
    elif corte in (7.16,):
        w = whoosh(0.6, 0.6, 250, 6000, grave=True)
        poner(efx, w, corte - 0.6 * 0.6, vol=0.42)
    else:
        w = whoosh(0.5 + 0.05 * (i % 3), 0.6, 600 + 200 * (i % 2), 9000)
        if i % 2:
            w = w[:, ::-1]  # alterna el sentido del paso
        poner(efx, w, corte - 0.6 * (0.5 + 0.05 * (i % 3)), vol=0.32)

# --- niveles ------------------------------------------------------------------------------------
voz = leer_voz()
tt = np.arange(N) / SR
# cama: -25 LUFS bajo la voz; sube ~11 dB sin voz (22,9-25,2) y queda presente bajo el logo
# suspenso un poco mas presente antes de la revelacion (+3 dB), cama normal despues, +11 dB sin voz
cama = np.interp(tt, [0, REVELA - 0.15, REVELA + 0.4, FIN_VOZ - 0.05, FIN_VOZ + 0.35, LOGO + 0.6, 30.0, 33.6, T],
                 [1.4, 1.4, 1.0, 1.0, 3.6, 3.6, 2.2, 0.0, 0.0])
musica_sola = musica.copy()
l_mus = lufs_de(musica_sola[: int(FIN_VOZ * SR)])
g_mus = 10 ** ((-25 - l_mus) / 20)
musica = musica * g_mus * cama[:, None]

l_voz = lufs_de(voz[: int(FIN_VOZ * SR)])
g = 10 ** ((-14 - l_voz) / 20)
print(f"voz {l_voz:.1f} LUFS, musica {l_mus:.1f} LUFS -> ganancia comun {20*np.log10(g):+.1f} dB")

efx_n = efx / (np.abs(efx).max() + 1e-9) * 0.5


def limitar(x, techo=0.89):
    m = np.abs(x).max()
    return x if m <= techo else np.tanh(x / techo) * techo


final = limitar((voz + musica + efx_n * 10 ** ((-16 - (-14)) / 20)) * g)
sin_musica = limitar((voz + efx_n * 10 ** ((-16 - (-14)) / 20)) * g)
escribir(os.path.join(PROY, "material", "mezcla.wav"), final)
escribir(os.path.join(PROY, "material", "mezcla-sin-musica.wav"), sin_musica)
escribir(os.path.join(PROY, "cache", "musica-sola.wav"), limitar(musica * g))
print("listo:", os.path.join(PROY, "material", "mezcla.wav"))
