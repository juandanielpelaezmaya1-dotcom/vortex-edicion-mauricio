"""Musica ORIGINAL (afro-house organico) + diseno sonoro ASMR del reel de empanadas.

    .venv/Scripts/python -I empanadas-proceso/audio/mezcla.py      (desde la raiz)

Lee cache/cortes.json (lo escribe montaje.py): cada toma con su segundo en la linea de tiempo, su
seccion y sus etiquetas de efecto. Todo va sobre la misma grilla: 119,88 BPM, un pulso = 15 cuadros.

Musica (composicion propia, La menor): bombo a negras, palma en 2 y 4, hat abierto a contratiempo,
shaker en semicorcheas con swing, congas sincopadas, bajo sub que rueda y acordes cortos con eco
(Am9 - Fmaj9 - Dm9 - Em7). Marimba con el motivo en emplatado. Por seccion:
  gancho     sin pulso: el aceite manda; subida corta y golpe seco en el corte a "masa"
  masa       bombo + shaker + congas + bajo (el hat entra en la segunda mitad)
  relleno/armado  groove completo con palma y acordes
  aceite     break: la musica se cierra a 380 Hz y queda el bombo; el chisporroteo al frente
  escurrido/emplatado  vuelve todo, con marimba
  clienta    se apaga de golpe en el mordisco (crunch solo) y cierra con el acorde final
Efectos: sintetizados (whoosh, golpe de masa, chisporroteo, crunch, cuchara, rodillo, llama) mas el
sonido real de cada toma, limpio y bajo, como cama de foley. La musica hace ducking con el bus de
efectos (baja hasta 9 dB en el aceite y el crunch).
Deja material/mezcla.wav (-14 LUFS, pico -1 dBTP), cache/musica-sola.wav y cache/sfx-solo.wav.
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
N = int(T * SR) + 1
P = CFG["pulso"]
C = 4 * P
S16 = P / 4
rng = np.random.default_rng(26)
CORTES = CFG["cortes"]
SEC = CFG["secciones"]


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
    escribir(tmp, x / max(1, np.abs(x).max()))
    log = ff("-i", tmp, "-af", "ebur128", "-f", "null", "-")
    os.remove(tmp)
    v = float([l for l in log.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    return v + 20 * np.log10(max(1, np.abs(x).max()))


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def poner(buf, x, en_s, pan=0.0, vol=1.0):
    i = int(round(en_s * SR))
    if i >= len(buf) or vol == 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    x = x[: len(buf) - i]
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


def bp(x, lo, hi, orden=2):
    return sosfilt(butter(orden, [lo, hi], btype="band", fs=SR, output="sos"), x, axis=0)


def ruido(dur, lo=20, hi=20000):
    n = max(1, int(dur * SR))
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= (fr > lo) & (fr < hi)
    x = np.fft.irfft(X, n)
    return x / (np.abs(x).max() + 1e-9)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)


def eco(x, retardo=P * 0.75, fb=0.35, veces=4):
    d = int(retardo * SR)
    y = np.zeros((len(x) + d * veces, 2))
    y[: len(x)] += x[:, None] if x.ndim == 1 else x
    for k in range(1, veces + 1):
        y[d * k : d * k + len(x), k % 2] += (x if x.ndim == 1 else x[:, 0]) * fb**k
    return y


# ================================ instrumentos ===================================================
def bombo(vol=1.0):
    t = np.arange(int(0.45 * SR)) / SR
    f = 48 + 140 * np.exp(-t * 38)
    x = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.22)
    click = ruido(0.01, 2000, 9000) * np.exp(-np.arange(int(0.01 * SR)) / SR / 0.002) * 0.25
    x[: len(click)] += click
    return x * vol


def palma():
    x = ruido(0.3, 900, 8000)
    t = np.arange(len(x)) / SR
    env = np.exp(-t / 0.09) + 0.7 * np.exp(-((t - 0.010) / 0.003) ** 2) + 0.6 * np.exp(-((t - 0.021) / 0.003) ** 2)
    return x * env * 0.8


def hat(abierto=False):
    d = 0.22 if abierto else 0.05
    x = ruido(d, 7000, 17000)
    return x * np.exp(-np.arange(len(x)) / SR / (0.07 if abierto else 0.014))


def shaker():
    x = ruido(0.08, 4000, 14000)
    t = np.arange(len(x)) / SR
    return x * np.minimum(t / 0.012, 1) * np.exp(-t / 0.025)


def conga(m, slap=False):
    t = np.arange(int(0.4 * SR)) / SR
    f = hz(m) * (1 + 0.18 * np.exp(-t * 40))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.07 if slap else 0.16))
    x += 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * np.exp(-t / 0.05)
    if slap:
        x[: int(0.03 * SR)] += ruido(0.03, 1500, 7000) * np.exp(-np.arange(int(0.03 * SR)) / SR / 0.006) * 0.8
    return x


def sub_nota(m, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(4 * np.pi * hz(m) * t)
    return np.tanh(1.3 * x) * np.minimum(t / 0.005, 1) * np.minimum((dur - t) / 0.02, 1) * np.exp(-t / 0.5)


def acorde_corto(notas, dur=0.32):
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros(len(t))
    for m in notas:
        for det in (-0.08, 0.08):
            f = hz(m) * 2 ** (det / 12)
            x += sum(np.sin(2 * np.pi * f * h * t) / h**1.4 for h in range(1, 6))
    x = lp(x, 2600)
    return x * env_ad(len(t), 0.004, 0.12) / len(notas)


def colchon(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        for det, lado in ((-0.1, 0), (0.1, 1)):
            f = hz(m) * 2 ** (det / 24)
            x[:, lado] += sum(np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6)) / h for h in range(1, 5))
    x = lp(x, 1500)
    return x * (np.minimum(t / 0.8, 1) * np.minimum((dur - t) / 1.2, 1))[:, None] / len(notas)


def marimba(m, dur=0.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.25) + 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.05)
    return x * np.minimum(t / 0.002, 1)


# ================================ efectos (ASMR) =================================================
def whoosh(dur=0.45, fuerte=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = ruido(dur, 150, 12000)
    y = np.zeros(n)
    trozo = int(0.01 * SR)
    for i in range(0, n, trozo):
        p = i / n
        c = 300 + 5000 * np.sin(np.pi * p) ** 2
        seg = x[max(0, i - 600) : i + trozo]
        y[i : i + trozo] = bp(seg, c * 0.5, min(c * 1.8, 20000))[-len(x[i : i + trozo]):]
    env = np.sin(np.pi * t / dur) ** 2
    y = y * env / (np.abs(y * env).max() + 1e-9)
    st = np.stack([y * np.linspace(1.2, 0.6, n), y * np.linspace(0.6, 1.2, n)], 1)
    return st * fuerte


def golpe_masa():
    """Golpe sordo de masa contra la mesa: thump grave + palmada humeda."""
    t = np.arange(int(0.35 * SR)) / SR
    f = 70 + 60 * np.exp(-t * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08)
    x[: int(0.06 * SR)] += lp(ruido(0.06, 200, 4000), 2500) * np.exp(-np.arange(int(0.06 * SR)) / SR / 0.012) * 0.7
    return x


def amasar(dur):
    """Masa pegajosa: pellizcos humedos irregulares."""
    n = int(dur * SR)
    y = np.zeros(n)
    k = 0.0
    while k < dur - 0.1:
        g = lp(ruido(0.09, 150, 3500), 1800) * env_ad(int(0.09 * SR), 0.01, 0.025)
        i = int(k * SR)
        y[i : i + len(g)] += g[: n - i] * rng.uniform(0.4, 1)
        k += rng.uniform(0.07, 0.17)
    return y


def chisporroteo(dur, intensidad=1.0):
    """El "shhhh" del aceite: siseo agudo + crepitar de burbujas que revientan."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    base = hp(ruido(dur, 1500, 16000), 2500) * (0.35 + 0.1 * np.sin(2 * np.pi * 3.1 * t))
    pops = np.zeros(n)
    for _ in range(int(dur * 140 * intensidad)):
        i = rng.integers(0, max(1, n - 400))
        L = rng.integers(40, 300)
        r = ruido((L + 0.5) / SR, 2000, 14000)[:L]
        pops[i : i + len(r)] += r * np.exp(-np.arange(len(r)) / (L / 4)) * rng.uniform(0.2, 1)
    x = base + 0.6 * pops
    env = np.minimum(t / 0.05, 1) * np.minimum((dur - t) / 0.25, 1)
    return np.stack([x * env, np.roll(x, 37) * env], 1) * intensidad


def caida_aceite():
    """Empanada que entra al aceite: golpe liquido + rafaga de siseo que estalla."""
    d = 1.6
    t = np.arange(int(d * SR)) / SR
    plop = lp(ruido(0.12, 100, 2000), 900) * env_ad(int(0.12 * SR), 0.003, 0.03)
    x = chisporroteo(d, 1.6)
    x *= (0.25 + 1.6 * np.exp(-t / 0.45))[:, None]
    x[: len(plop)] += plop[:, None] * 0.8
    return x


def crunch():
    """Mordisco crocante: rafaga de chasquidos secos + cola de migas."""
    d = 0.7
    n = int(d * SR)
    y = np.zeros(n)
    k = 0.0
    while k < 0.32:
        L = int(rng.uniform(0.004, 0.02) * SR)
        g = bp(ruido((L + 0.5) / SR + 0.01, 800, 9000), rng.uniform(900, 2500), rng.uniform(4000, 9000))[:L]
        g *= np.exp(-np.arange(L) / (L / 3))
        i = int(k * SR)
        y[i : i + L] += g * rng.uniform(0.5, 1) * (1.2 - k * 2)
        k += rng.uniform(0.006, 0.03)
    y += lp(ruido(d, 200, 3000), 1500) * env_ad(n, 0.005, 0.06) * 0.5   # cuerpo
    y += hp(ruido(d, 3000, 12000), 3000) * np.exp(-np.arange(n) / SR / 0.25) * 0.12  # migas
    return y / (np.abs(y).max() + 1e-9)


def cuchara():
    x = bp(ruido(0.35, 300, 6000), 500, 3000) * env_ad(int(0.35 * SR), 0.03, 0.1)
    t = np.arange(int(0.08 * SR)) / SR
    tin = np.sin(2 * np.pi * 2350 * t) * np.exp(-t / 0.02) * 0.25   # el metal toca el plato
    x[: len(tin)] += tin
    return x


def rodillo(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = lp(ruido(dur, 80, 2500), 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * t) ** 2)
    return x * np.minimum(t / 0.08, 1) * np.minimum((dur - t) / 0.1, 1)


def harina(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(ruido(dur, 1000, 12000), 2000, 9000) * np.minimum(t / 0.1, 1) * np.minimum((dur - t) / 0.2, 1)
    return x * 0.6


def llama():
    d = 0.9
    t = np.arange(int(d * SR)) / SR
    x = lp(ruido(d, 40, 1500), 600) * np.minimum(t / 0.03, 1) * np.exp(-t / 0.5)
    x[: int(0.05 * SR)] += ruido(0.05, 3000, 12000) * np.exp(-np.arange(int(0.05 * SR)) / SR / 0.01) * 0.5
    return x


def hervor(dur):
    n = int(dur * SR)
    y = lp(ruido(dur, 60, 2000), 700) * 0.4
    for _ in range(int(dur * 25)):
        i = rng.integers(0, n - 2000)
        L = rng.integers(300, 1500)
        f = rng.uniform(300, 900)
        tt = np.arange(L) / SR
        y[i : i + L] += np.sin(2 * np.pi * f * (1 + 2 * tt / (L / SR)) * tt) * np.exp(-tt / (L / SR / 3)) * 0.4
    return y


def agua(dur):
    return bp(ruido(dur, 300, 8000), 600, 5000) * np.minimum(np.arange(int(dur * SR)) / SR / 0.05, 1) * 0.6


def limon():
    x = lp(ruido(0.3, 200, 5000), 2500) * env_ad(int(0.3 * SR), 0.02, 0.08)
    gotas = np.zeros_like(x)
    for k in (0.12, 0.19, 0.24):
        L = int(0.02 * SR)
        tt = np.arange(L) / SR
        gotas[int(k * SR) : int(k * SR) + L] += np.sin(2 * np.pi * 1400 * (1 + 8 * tt) * tt) * np.exp(-tt / 0.005)
    return x + 0.5 * gotas


def plato():
    t = np.arange(int(0.4 * SR)) / SR
    x = (np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.05) + lp(ruido(0.4, 100, 3000), 1200) * np.exp(-t / 0.03)) * 0.8
    return x


def subida(dur):
    n = int(dur * SR)
    p = np.arange(n) / n
    x = ruido(dur, 200, 15000)
    y = np.zeros(n)
    trozo = int(0.02 * SR)
    for i in range(0, n, trozo):
        c = 400 + 9000 * p[i] ** 2
        seg = x[max(0, i - 800) : i + trozo]
        y[i : i + trozo] = lp(hp(seg, c * 0.3), c)[-len(x[i : i + trozo]):]
    return y * p**2.2 / (np.abs(y).max() + 1e-9)


def impacto():
    d = 1.8
    t = np.arange(int(d * SR)) / SR
    f = 32 + 80 * np.exp(-t * 9)
    return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.55) + lp(ruido(d, 80, 5000), 3000) * np.exp(-t / 0.3) * 0.2


# ================================ musica ========================================================
# Am9 - Fmaj9 - Dm9 - Em7, un acorde por compas; raiz del bajo y voces del acorde
PROG = [(33, [60, 64, 67, 71]), (29, [57, 60, 64, 67]), (26, [57, 60, 65, 64]), (28, [55, 59, 62, 67])]
MOTIVO = [76, 74, 72, 69, 72, 74, 76, 79]   # marimba, corcheas del compas impar
CONGA = [(0, 62, False), (3, 62, True), (6, 57, False), (7, 57, False), (10, 62, True), (12, 57, False), (14, 62, False)]
BAJO = [(0, 0, 3), (3, 0, 1), (6, 12, 2), (10, 0, 2), (14, 7, 2)]   # (semicorchea, intervalo, largo en 16avos)


def seccion(t):
    for s, (a, b) in SEC.items():
        if a - 1e-6 <= t < b - 1e-6:
            return s
    return "clienta"


t_inicio = SEC["masa"][0]            # la musica arranca en el corte a la masa
t_break = SEC["aceite"]              # break filtrado
corte_crunch = [c for c in CORTES if "crunch" in c["sfx"]][0]
# el mordisco: segundo del archivo en que muerde -> linea de tiempo (lo afina MORDISCO_S)
MORDISCO_S = float(os.environ.get("MORDISCO_S", "16.95"))
t_crunch = corte_crunch["en_s"] + (MORDISCO_S - corte_crunch["in_s"]) / corte_crunch["vel"]

mus = {k: np.zeros((N, 2)) for k in ("bombo", "perc", "bajo", "acordes", "colchon", "marimba", "fx")}
n_comp = int(np.ceil((T - t_inicio) / C)) + 1
for c in range(n_comp):
    tc = t_inicio + c * C
    if tc >= T:
        break
    s = seccion(tc + 0.01)
    raiz, notas = PROG[c % 4]
    full = s in ("relleno", "armado", "escurrido", "emplatado")
    en_break = s == "aceite"
    final = s == "clienta"
    poner(mus["colchon"], colchon(notas, C + 1.2), tc - 0.1, vol=0.35 if not full else 0.25)
    for q in range(16):
        tq = tc + q * S16 + (S16 * 0.12 if q % 2 else 0)   # swing leve
        if tq >= T or (final and tq >= t_crunch - 0.25):
            continue
        sq = seccion(tq + 0.001)
        if q % 4 == 0:
            poner(mus["bombo"], bombo(1.0), tq)
        if en_break:
            continue
        if q in (4, 12) and (full or sq == "clienta" or (sq == "masa" and c >= 2)):
            poner(mus["perc"], eco(palma(), fb=0.2, veces=2), tq, vol=0.45)
        if q % 4 == 2 and (full or (sq == "masa" and c >= 3) or sq == "clienta"):
            poner(mus["perc"], hat(True), tq, pan=0.25, vol=0.22)
        poner(mus["perc"], shaker(), tq, pan=-0.35, vol=(0.16 if q % 4 == 2 else 0.09))
        for (pq, m, sl) in CONGA:
            if pq == q:
                poner(mus["perc"], conga(m, sl), tq, pan=0.4 if m > 60 else -0.2, vol=0.38)
        for (bq, iv, largo) in BAJO:
            if bq == q:
                poner(mus["bajo"], sub_nota(raiz + 12 + iv, largo * S16 * 0.95), tq, vol=0.85)
        if full and q in (2, 6, 11, 14):
            poner(mus["acordes"], eco(acorde_corto(notas), fb=0.3), tq, vol=0.42)
        if s in ("escurrido", "emplatado") and q % 2 == 0 and c % 2 == 1:
            poner(mus["marimba"], eco(marimba(MOTIVO[q // 2]), fb=0.25, veces=2), tq, vol=0.3)

# break del aceite: todo lo que no es bombo pasa por un pasabajos que se cierra y se abre
musica = mus["perc"] * 0.9 + mus["bajo"] * 0.9 + mus["acordes"] + mus["colchon"] * 0.6 + mus["marimba"]
a, b = int(t_break[0] * SR), int(t_break[1] * SR)
cerrado = lp(musica[a:b], 380, 4)
xf = int(0.25 * SR)
w = np.ones(b - a)
w[:xf] = np.linspace(0, 1, xf)
w[-xf:] = np.linspace(1, 0, xf)
musica[a:b] = musica[a:b] * (1 - w[:, None]) + cerrado * w[:, None]
musica += mus["bombo"]

# gancho: sin pulso, subida corta al corte de la masa + golpe en el corte
poner(mus["fx"], np.stack([subida(1.4)] * 2, 1), t_inicio - 1.4, vol=0.30)
poner(mus["fx"], np.stack([impacto()] * 2, 1), t_inicio, vol=0.55)
# subida antes de volver del break, impacto al escurrido
poner(mus["fx"], np.stack([subida(2 * P * 2)] * 2, 1), t_break[1] - 4 * P, vol=0.22)
poner(mus["fx"], np.stack([impacto()] * 2, 1), t_break[1], vol=0.4)
# cierre: el acorde final suena despues del mordisco y se queda
poner(mus["fx"], colchon([57, 60, 64, 71, 76], T - t_crunch + 0.5), t_crunch + 0.25, vol=0.9)
poner(mus["fx"], eco(marimba(81, 1.2), fb=0.35), t_crunch + 0.35, vol=0.35)
musica += mus["fx"]
# silencio seco 0,25 s antes del mordisco
g = np.ones(N)
i0, i1 = int((t_crunch - 0.25) * SR), int(t_crunch * SR) + int(0.2 * SR)
g[i0:i1] = 0.05
f = int(0.02 * SR)
g[i0 : i0 + f] = np.linspace(1, 0.05, f)
musica *= g[:, None]
cola = np.ones(N)
k = int((T - 1.6) * SR)
cola[k:] = np.linspace(1, 0, N - k) ** 1.5
musica *= cola[:, None]


# ================================ efectos por toma ===============================================
sfx = np.zeros((N, 2))
foley = np.zeros((N, 2))


def sonido_real(c):
    """El sonido de la toma, limpio: misma ventana del archivo, a velocidad normal."""
    tmp = os.path.join(PROY, "cache", "_toma.raw")
    dur = c["dur"]
    ff("-ss", f"{c['in_s']}", "-t", f"{dur}", "-i", os.path.join(PROY, c["archivo"]), "-vn", "-ac", "1",
       "-ar", str(SR), "-af", "highpass=f=120,afftdn=nf=-35:nr=6", "-f", "f32le", tmp)
    x = np.fromfile(tmp, dtype="<f4").astype(float)
    os.remove(tmp)
    if len(x) < 100:
        return np.zeros(int(dur * SR))
    fl = int(0.02 * SR)
    x[:fl] *= np.linspace(0, 1, fl)
    x[-fl:] *= np.linspace(1, 0, fl)
    return x


for k, c in enumerate(CORTES):
    t0, dur = c["en_s"], c["dur"]
    # whoosh en cada cambio de seccion (fuerte) y cada dos cortes dentro de la seccion (suave)
    if k > 0 and (c["cambio"] or k % 2 == 0):
        fuerte = 1.0 if c["cambio"] else 0.45
        poner(sfx, whoosh(0.42 if c["cambio"] else 0.3, fuerte), t0 - (0.3 if c["cambio"] else 0.2), vol=0.32)
    real = sonido_real(c)
    tags = [e.partition("@") for e in c["sfx"]]
    sizzle_real = any(e[0] in ("aceite", "fritura", "escurrir") for e in tags)
    poner(foley, real, t0, vol=0.9 if sizzle_real else 0.45)
    for e, _, off in tags:
        if off:   # "golpe@0.35": el efecto cae en ese segundo de la toma (linea de tiempo)
            t0 = c["en_s"] + float(off) - 0.12
        else:
            t0 = c["en_s"]
        if e == "aceite":
            poner(sfx, caida_aceite() if c["toma"] == "5283" else chisporroteo(dur + 0.2, 1.2), t0 + 0.05, vol=0.5)
        elif e == "fritura":
            poner(sfx, chisporroteo(dur + 0.2, 1.4 if c["seccion"] == "gancho" else 1.0), t0, vol=0.5 if c["seccion"] == "gancho" else 0.42)
        elif e == "escurrir":
            poner(sfx, chisporroteo(dur, 0.45), t0, vol=0.3)
            poner(sfx, plato(), t0 + 0.1, vol=0.35)
        elif e == "golpe":
            poner(sfx, golpe_masa(), t0 + 0.12, vol=0.7)
        elif e == "amasar":
            poner(sfx, amasar(dur), t0, vol=0.35)
        elif e == "harina":
            poner(sfx, harina(dur), t0, pan=0.1, vol=0.35)
        elif e == "agua":
            poner(sfx, agua(dur), t0, vol=0.3)
        elif e == "hervor":
            poner(sfx, hervor(dur), t0, vol=0.45)
        elif e == "llama":
            poner(sfx, llama(), t0 + 0.1, vol=0.7)
        elif e == "cuchara":
            poner(sfx, cuchara(), t0 + 0.15, vol=0.5)
        elif e == "rodillo":
            poner(sfx, rodillo(dur), t0, vol=0.4)
        elif e == "limon":
            poner(sfx, limon(), t0 + 0.2, vol=0.5)
        elif e == "plato":
            poner(sfx, plato(), t0 + 0.15, vol=0.4)
        elif e == "crunch":
            poner(sfx, crunch(), t_crunch, vol=0.9)

# foley nivelado: el sonido real va como cama, nunca encima de los efectos
lf = lufs_de(foley)
foley *= 10 ** ((-30 - lf) / 20) if lf > -70 else 0
efectos = sfx + foley

# ducking: la musica baja con la envolvente del bus de efectos (hasta -7 dB)
envf = np.abs(efectos).max(axis=1)
kk = int(0.12 * SR)
envf = np.convolve(envf, np.ones(kk) / kk, mode="same")
envf = envf / (np.percentile(envf, 99.5) + 1e-9)
duck = 10 ** (-9 * np.clip(envf, 0, 1) / 20)
# y un bombeo leve con el bombo (sidechain de afro-house)
pump = np.ones(N)
for c in range(n_comp * 4):
    tb = t_inicio + c * P
    i = int(tb * SR)
    L = int(0.18 * SR)
    if i < N:
        pump[i : i + L] = np.minimum(pump[i : i + L], 1 - 0.18 * np.exp(-np.arange(len(pump[i : i + L])) / SR / 0.06))
bombos = mus["bombo"] * cola[:, None] * g[:, None]
musica = (musica - bombos) * (duck * pump)[:, None] + bombos * duck[:, None]

# niveles: musica -17 LUFS, efectos encima; mezcla final a -14 LUFS, pico -1 dBTP
lm = lufs_de(musica)
musica *= 10 ** ((-17 - lm) / 20)
le = lufs_de(efectos)
efectos *= 10 ** ((-14 - le) / 20)
mezcla = musica + efectos
lt = lufs_de(mezcla)
gan = 10 ** ((-14 - lt) / 20)
print(f"musica {lm:.1f}, efectos {le:.1f}, mezcla {lt:.1f} LUFS -> {20 * np.log10(gan):+.1f} dB; mordisco en {t_crunch:.2f} s")


def limitar(x, techo=0.89):
    m = np.abs(x).max()
    return x if m <= techo else np.tanh(x / techo) * techo


escribir(os.path.join(PROY, "material", "mezcla.wav"), limitar(mezcla * gan))
escribir(os.path.join(PROY, "cache", "musica-sola.wav"), limitar(musica * gan))
escribir(os.path.join(PROY, "cache", "sfx-solo.wav"), limitar(efectos * gan))
print("listo")
