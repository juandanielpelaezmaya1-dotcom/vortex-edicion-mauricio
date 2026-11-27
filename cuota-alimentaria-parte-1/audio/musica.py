"""Musica ORIGINAL de la serie Cuota alimentaria: cama de tension informativa, sin licencias.

    .venv/Scripts/python -I cuota-alimentaria-parte-1/audio/musica.py      (desde la raiz)

Re menor, 92 BPM, hecha de los mismos instrumentos sinteticos del Video 04 de Accion Juridica
(ostinato grave, dron, tic de reloj, latido) para que la marca suene igual en toda la serie.
  - Parte 1 (el error): ostinato + tic desde el principio, latido desde el gancho, sin ritmo
    lleno: tension que no se resuelve. Riser hacia la pregunta final y golpe en la tarjeta.
  - Parte 2 (la consecuencia): mismo arranque; en "los embargos" entra el ritmo (bombo, palmas,
    arpegio): ahora hay salida. Resuelve en un acorde al final de la voz.
La musica se nivela a -14 LUFS: con `volumen` 0,22 en el manifest queda ~13 dB bajo la voz.
Los tiempos (en el video final) salen de los manifests: correr despues de armar.py.
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SR = 48000
BPM = 92.0
PULSO = 60 / BPM
COMPAS = 4 * PULSO
OCHO = PULSO / 2
rng = np.random.default_rng(7)


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


def lufs(ruta):
    log = ff("-i", ruta, "-af", "ebur128", "-f", "null", "-")
    return float([l for l in log.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


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


def sierra(f, t):
    x = np.zeros_like(t)
    for k in range(1, 14):
        x += (-1) ** (k + 1) * np.sin(2 * np.pi * k * f * t) / k
    return x * 0.6


def pulso_grave(m, dur, brillo):
    t = np.arange(int(dur * SR)) / SR
    x = sierra(hz(m), t) + 0.5 * np.sin(2 * np.pi * hz(m - 12) * t)
    return lp(x, 300 + 2200 * brillo) * np.exp(-t / 0.11) * np.minimum(t / 0.003, 1)


def dron(notas, dur):
    t = np.arange(int(dur * SR)) / SR
    x = np.zeros((len(t), 2))
    for m in notas:
        for det, lado in ((-0.1, 0), (0.1, 1), (0.03, 0), (-0.04, 1)):
            x[:, lado] += np.sin(2 * np.pi * hz(m) * 2 ** (det / 24) * t + rng.uniform(0, 6)) * 0.5
    env = np.minimum(t / 1.2, 1) * np.minimum((dur - t) / 1.0, 1)
    return x * np.clip(env, 0, 1)[:, None] / len(notas)


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
    t = np.arange(int(dur * SR)) / SR
    f = 32 + 70 * np.exp(-t * 9)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    cuerpo = lp(ruido(dur, 40, 3000), 900) * np.exp(-t / 0.12) * 0.7
    return (sub + cuerpo) * np.minimum(t / 0.002, 1)


def riser(dur):
    t = np.arange(int(dur * SR)) / SR
    p = t / dur
    x = ruido(dur, 300, 14000)
    y = np.zeros_like(x)
    trozo = int(0.05 * SR)
    for i in range(0, len(x), trozo):
        y[i : i + trozo] = lp(x[i : i + trozo + 2000], 400 + 9000 * p[i] ** 2)[:trozo][: len(y[i : i + trozo])]
    tono = np.sin(2 * np.pi * np.cumsum(180 + 900 * p ** 2) / SR) * 0.25
    return (y * 0.8 + tono) * p ** 2.2


PROG = [(50, [62, 65, 69, 74]), (46, [62, 65, 70, 74]), (43, [62, 67, 70, 74]), (45, [61, 64, 69, 73])]
OSTI = [0, 0, 12, 0, 0, 7, 0, 10]
ARP = [0, 1, 2, 3, 2, 1, 2, 3]


def duracion_clips(m):
    t = 0.0
    fps = m.get("fps", 30)
    for c in m["clips"]:
        t += round((c["out_s"] - c["in_s"]) / c.get("velocidad", 1) * fps) / fps
    return t


def componer(T, ritmo_desde, fin_voz, tarjeta=None):
    """T: duracion de la musica. ritmo_desde: segundo en que entra el ritmo (None = nunca).
    fin_voz: ultima palabra. tarjeta: segundo de la tarjeta final (riser + golpe) o None."""
    N = int(T * SR)
    buf = {k: np.zeros((N, 2)) for k in ("pulso", "dron", "tic", "ritmo", "arp", "fx")}

    def poner(b, x, en_s, pan=0.0, vol=1.0):
        i = int(round(en_s * SR))
        if i >= N:
            return
        if i < 0:
            x, i = x[-i:], 0
        x = x[: N - i]
        if x.ndim == 2:
            b[i : i + len(x)] += x * vol
            return
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        b[i : i + len(x), 0] += x * vol * l * 1.41
        b[i : i + len(x), 1] += x * vol * r * 1.41

    fin_mus = tarjeta if tarjeta else fin_voz + 0.8
    c = 0
    while c * COMPAS < fin_mus:
        tc = c * COMPAS
        raiz, acorde = PROG[c % 4]
        con_ritmo = ritmo_desde is not None and tc >= ritmo_desde - 0.05
        for k in range(8):
            tk = tc + k * OCHO
            if tk >= fin_mus:
                break
            brillo = min(1.0, 0.25 + 0.6 * tk / fin_mus) * (1.0 if not con_ritmo else 0.8)
            poner(buf["pulso"], pulso_grave(raiz + OSTI[k] - 12, OCHO * 0.95, brillo), tk,
                  pan=0.15 * np.sin(k), vol=0.55 if k % 2 == 0 else 0.4)
            poner(buf["tic"], tic(k % 2 == 0), tk, pan=0.45, vol=(0.2 if k % 2 == 0 else 0.12) * (0.6 if con_ritmo else 1))
        poner(buf["dron"], dron([raiz + 12, *acorde[:3]], COMPAS + 1.0), tc - 0.3, vol=0.5)
        if con_ritmo:
            for p in range(4):
                poner(buf["ritmo"], bombo(), tc + p * PULSO, vol=0.65)
                if p % 2:
                    poner(buf["ritmo"], palma(), tc + p * PULSO, pan=-0.1, vol=0.2)
            for k in range(8):
                poner(buf["arp"], pluck(acorde[ARP[k]] + 12), tc + k * OCHO, pan=0.4 * np.sin(k * 1.3),
                      vol=0.17 if k % 2 == 0 else 0.11)
        elif tc >= 2 * COMPAS:
            # latido: bombo grave en 1 y en el "y" del 1
            poner(buf["ritmo"], bombo(0.14, 40), tc, vol=0.5)
            poner(buf["ritmo"], bombo(0.12, 40), tc + 0.75 * PULSO, vol=0.32)
        c += 1

    if ritmo_desde is not None:
        poner(buf["fx"], impacto(), ritmo_desde, vol=0.5)
    if tarjeta:
        r = riser(3.2)
        poner(buf["fx"], np.stack([r, np.roll(r, 300)], axis=1) * 0.45, tarjeta - 3.2)
        poner(buf["fx"], impacto(3.0), tarjeta, vol=0.8)
        poner(buf["dron"], dron([38, 50, 57, 62, 65], 3.5), tarjeta - 0.1, vol=0.6)
    else:
        # resuelve: acorde de Re menor que se apaga despues de la voz
        for j, m in enumerate([38, 50, 57, 62, 65, 69, 74]):
            poner(buf["arp"], pluck(m, 3.5), fin_mus + j * 0.025, pan=-0.3 + 0.1 * j, vol=0.2)
        poner(buf["dron"], dron([50, 57, 62, 65], 3.8), fin_mus - 0.1, vol=0.55)

    mus = buf["pulso"] * 0.9 + buf["dron"] * 0.55 + buf["tic"] + buf["ritmo"] + buf["arp"] + buf["fx"]
    # entra con fundido corto; la voz del gancho manda
    tt = np.arange(N) / SR
    mus *= np.clip(tt / 0.6, 0, 1)[:, None]
    return mus


def hacer(carpeta, ritmo_id=None, tarjeta=False):
    proy = os.path.join(RAIZ, carpeta)
    m = json.load(open(os.path.join(proy, "manifest.json"), encoding="utf-8"))
    total = duracion_clips(m)
    fps = m.get("fps", 30)
    # fin de la voz = suma de los clips con voz (la cola muda de la Parte 1 no cuenta)
    t, ritmo_desde, fin_voz = 0.0, None, 0.0
    for c in m["clips"]:
        d = round((c["out_s"] - c["in_s"]) / c.get("velocidad", 1) * fps) / fps
        if ritmo_id and ritmo_id in c.get("_dice", "") and ritmo_desde is None:
            ritmo_desde = t
        if c.get("volumen", 1) != 0:
            fin_voz = t + d
        t += d
    T = total + 0.2
    mus = componer(T, ritmo_desde, fin_voz, tarjeta=fin_voz if tarjeta else None)
    tmp = os.path.join(proy, "cache", "_mus.wav")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    escribir(tmp, mus / (np.abs(mus).max() + 1e-9) * 0.8)
    g = 10 ** ((-14 - lufs(tmp)) / 20)
    os.remove(tmp)
    salida = os.path.join(proy, "material", "musica.wav")
    escribir(salida, np.tanh(mus / (np.abs(mus).max() + 1e-9) * 0.8 * g / 0.95) * 0.95)
    print(f"{carpeta}: {T:.1f} s, ritmo desde {ritmo_desde}, fin de voz {fin_voz:.2f} -> {salida}")


hacer("cuota-alimentaria-parte-1", tarjeta=True)
hacer("cuota-alimentaria-parte-2", ritmo_id="El éxito del proceso ejecutivo")
