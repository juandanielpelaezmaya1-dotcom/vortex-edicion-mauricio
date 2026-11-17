"""Separa el logo de Dejaste Huella en capas para animarlas (Remotion: DejasteHuellaLogo.tsx).

Uso (desde la carpeta del proyecto):  ../.venv/Scripts/python capas.py
Lee material/logo.png y escribe material/capas/*.png + material/capas/capas.json.
Cada capa sale con el color de su tinta y alfa des-mezclado del blanco (bordes suaves).
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

SRC = "material/logo.png"
OUT = "material/capas"
INKS = {"oro": (217, 145, 45), "verde": (21, 115, 101), "oscuro": (10, 60, 60), "salmon": (209, 127, 87)}
W = np.array([255, 255, 255.0])
RAIZ = (628, 876)  # punta baja del corazon: de ahi crece la rama

os.makedirs(OUT, exist_ok=True)
img = np.array(Image.open(SRC).convert("RGB")).astype(float)
H, Wd = img.shape[:2]


def unmix(c):
    d = W - np.array(c, float)
    al = np.clip(((W - img) @ d) / (d @ d), 0, 1)
    res = np.linalg.norm(img - (W - al[..., None] * d), axis=2)
    return al, res


AL, RES = {}, {}
for k, c in INKS.items():
    AL[k], RES[k] = unmix(c)
names = list(INKS)
lab = np.argmin(np.stack([RES[k] for k in names]), axis=0)
alfa_max = np.max(np.stack([AL[k] for k in names]), axis=0)
tinta = (alfa_max > 0.02)

pieces = {}  # nombre -> (mask core bool, ink)


def comps(ink, thr=0.5, region=None):
    m = ((lab == names.index(ink)) & (AL[ink] > thr))
    if region is not None:
        m &= region
    n, cc, st, cen = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    return [(cc == i, st[i], cen[i]) for i in range(1, n) if st[i][4] > 60]


xx = np.arange(Wd)[None, :].repeat(H, 0)
yy = np.arange(H)[:, None].repeat(Wd, 1)
ICONO = xx < 1000
TEXTO = xx >= 1030


def near(st, x, y):
    return st[0] <= x <= st[0] + st[2] and st[1] <= y <= st[1] + st[3]


# --- animales y aros
for m, st, c in comps("oscuro", region=ICONO):
    if st[4] > 50000:
        pieces["perro"] = (m, "oscuro")
    elif near(st, 660, 160):
        pieces["aro_perro"] = (m, "oscuro")
for m, st, c in comps("oro", region=ICONO):
    if st[4] > 50000:
        pieces["gato"] = (m, "oro")
    elif near(st, 840, 370):
        pieces["aro_gato"] = (m, "oro")
    elif near(st, 275, 60) and st[3] < 60:
        pieces["aro_ave"] = (m, "oro")
    elif near(st, 295, 150):
        pieces["ave"] = (m, "oro")
for m, st, c in comps("salmon", region=ICONO):
    if st[4] > 50000:
        # el aro del conejo esta pegado a las orejas: es lo delgado que la apertura borra
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
        grueso = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
        delgado = m & ~grueso
        caja = (xx > 300) & (xx < 490) & (yy > 540) & (yy < 630)
        n, cc, st2, _ = cv2.connectedComponentsWithStats((delgado & caja).astype(np.uint8), 8)
        aro = np.zeros_like(m)
        for i in range(1, n):
            if st2[i][4] > 80:
                aro |= cc == i
        pieces["aro_conejo"] = (aro, "salmon")
        pieces["conejo"] = (m & ~aro, "salmon")

# --- rama: tallos (relleno bajo) y hojas (relleno alto)
tallos = np.zeros((H, Wd), bool)
hojas = []
for m, st, c in comps("verde", thr=0.4, region=ICONO):
    fill = st[4] / float(st[2] * st[3])
    if fill < 0.45 or st[4] > 20000:
        tallos |= m
    else:
        hojas.append(m)

# --- letras: por componente, asignadas por el centro x
cortes_dejaste = [("D", 1240), ("e", 1395), ("j", 1455), ("a", 1605), ("s", 1700), ("t", 1790), ("e2", 9999)]
cortes_huella = [("h", 1190), ("u", 1340), ("e", 1505), ("l", 1550), ("l2", 1600), ("a", 9999)]
letras = {}
txt_core = TEXTO & (alfa_max > 0.35)
n, cc, st, cen = cv2.connectedComponentsWithStats(txt_core.astype(np.uint8), 8)
for i in range(1, n):
    if st[i][4] < 8:
        continue
    cx, cy = cen[i]
    if cy < 520:
        fila, cortes, ink = "dejaste", cortes_dejaste, "oro"
    elif cy < 790:
        fila, cortes, ink = "huella", cortes_huella, "verde"
    else:
        fila, cortes, ink = "lema", None, "verde"
    if cortes:
        nombre = fila + "_" + next(nm for nm, lim in cortes if cx < lim)
    else:
        # palabras del lema por huecos
        nombre = "lema"
    letras.setdefault(nombre, [np.zeros((H, Wd), bool), ink])
    letras[nombre][0] |= cc == i
# lema por palabras
lm = letras.pop("lema")[0]
cols = np.where(lm.any(0))[0]
grupos, ini, prev = [], cols[0], cols[0]
for x in cols[1:]:
    if x - prev > 14:
        grupos.append((ini, prev)); ini = x
    prev = x
grupos.append((ini, prev))
for gi, (a, b) in enumerate(grupos):
    mm = lm.copy(); mm[:, :a] = False; mm[:, b + 1:] = False
    letras[f"lema_{gi}"] = [mm, "verde"]
for k, (m, ink) in letras.items():
    pieces["l_" + k] = (m, ink)
for i, m in enumerate(hojas):
    pieces[f"hoja_{i:02d}"] = (m, "verde")
pieces["tallos"] = (tallos, "verde")

# --- cada pixel con tinta va a la pieza del nucleo mas cercano (bordes suaves)
ids = np.zeros((H, Wd), np.int32)
orden = list(pieces)
for i, k in enumerate(orden, 1):
    ids[pieces[k][0]] = i
dist, lbl = cv2.distanceTransformWithLabels((ids == 0).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
# lbl indexa pixeles semilla; mapeamos a su id
semillas = ids[ids > 0]
mapa = np.zeros(lbl.max() + 1, np.int32)
# orden de etiquetas = orden de escaneo de pixeles cero de (ids==0)
mapa[1:] = semillas
dueno = mapa[lbl]
dueno[(dist > 6) | ~tinta] = 0

capas = []
for i, k in enumerate(orden, 1):
    ink = pieces[k][1]
    m = dueno == i
    if m.sum() < 30:
        continue
    ys, xs = np.where(m)
    x0, x1, y0, y1 = xs.min() - 2, xs.max() + 3, ys.min() - 2, ys.max() + 3
    x0, y0 = max(x0, 0), max(y0, 0)
    a = np.where(m, AL[ink], 0)[y0:y1, x0:x1]
    rgba = np.zeros(a.shape + (4,), np.uint8)
    rgba[..., :3] = INKS[ink]
    rgba[..., 3] = np.round(a * 255)
    Image.fromarray(rgba).save(f"{OUT}/{k}.png")
    capas.append({"id": k, "x": int(x0), "y": int(y0), "w": int(x1 - x0), "h": int(y1 - y0),
                  "cx": float(xs.mean()), "cy": float(ys.mean())})

# --- rama: distancia geodesica desde la raiz sobre la mascara engordada (salta los huecos
# que tapan el perro y el ave). Se guarda en el alfa de un PNG en escala 0-1.
verde_ids = [orden.index(k) + 1 for k in orden if k == "tallos" or k.startswith("hoja_")]
rama = np.isin(dueno, verde_ids)
puente = cv2.dilate(rama.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(bool)
INF = 1e9
D = np.full((H, Wd), INF)
import heapq
ry, rx = RAIZ[1], RAIZ[0]
# arranca en el pixel de rama mas cercano a RAIZ
pys, pxs = np.where(rama)
j = np.argmin((pys - ry) ** 2 + (pxs - rx) ** 2)
ry, rx = pys[j], pxs[j]
D[ry, rx] = 0
pq = [(0.0, ry, rx)]
vec = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
while pq:
    d, y, x = heapq.heappop(pq)
    if d > D[y, x]:
        continue
    for dy, dx, w in vec:
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < Wd and puente[ny, nx]:
            # fuera de la rama real se cobra mas: el camino prefiere seguir el tallo
            nd = d + w * (1.0 if rama[ny, nx] else 1.6)
            if nd < D[ny, nx]:
                D[ny, nx] = nd
                heapq.heappush(pq, (nd, ny, nx))
dmax = D[rama].max()
for c in capas:
    if c["id"] == "tallos" or c["id"].startswith("hoja_"):
        m = np.isin(dueno, [orden.index(c["id"]) + 1])
        c["d0"] = float(D[m].min() / dmax)
        c["d1"] = float(D[m].max() / dmax)
t = next(c for c in capas if c["id"] == "tallos")
dd = np.clip(D / dmax, 0, 1)[t["y"]:t["y"] + t["h"], t["x"]:t["x"] + t["w"]]
g = np.round(dd * 65535).astype(np.uint32)
rgb = np.zeros(dd.shape + (3,), np.uint8)
rgb[..., 0] = g >> 8
rgb[..., 1] = g & 255
Image.fromarray(rgb).save(f"{OUT}/tallos_dist.png")  # R = byte alto, G = byte bajo


def camino(y, x):
    """Baja por la distancia desde (y, x) hasta la raiz: el recorrido de un tallo."""
    pts = [(y, x)]
    while D[y, x] > 0:
        mejor = min(((D[y + dy, x + dx], y + dy, x + dx) for dy, dx, _ in vec
                     if 0 <= y + dy < H and 0 <= x + dx < Wd), key=lambda r: r[0])
        if mejor[0] >= D[y, x]:
            break
        _, y, x = mejor
        pts.append((y, x))
    pts = pts[::-1]
    return [[round(float(D[p] / dmax), 4), int(p[1]), int(p[0])] for p in pts[::6]]


tm = np.isin(dueno, [orden.index("tallos") + 1])
Dt = np.where(tm, D, -1)
fy, fx = np.unravel_index(np.argmax(Dt), D.shape)
medio = np.where(tm & (xx > 540) & (xx < 650) & (yy < 235), D, -1)
my, mx = np.unravel_index(np.argmax(medio), D.shape)
punta = [camino(fy, fx), camino(my, mx)]
for c in capas:
    if c["id"].startswith("hoja_"):
        m = np.isin(dueno, [orden.index(c["id"]) + 1])
        Dm = np.where(m, D, 1e12)
        oy, ox = np.unravel_index(np.argmin(Dm), D.shape)
        c["ox"], c["oy"] = int(ox), int(oy)
json.dump({"ancho": Wd, "alto": H, "capas": capas, "punta": punta}, open(f"{OUT}/capas.json", "w"), indent=1)
print(len(capas), "capas;", [c["id"] for c in capas])
