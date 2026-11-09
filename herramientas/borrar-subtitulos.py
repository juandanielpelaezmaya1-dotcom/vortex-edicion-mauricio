"""Borra subtitulos QUEMADOS de un video (texto blanco, centrado, en una franja fija).

Sirve cuando el material llega ya subtitulado (un export con subtitulos quemados) y hay que rehacer los
subtitulos en otra posicion. No es parte del manifest porque no edita: deja un material
limpio en material/ y el manifest parte de ahi. El original no se toca.

    python herramientas/borrar-subtitulos.py <entrada.mp4> <salida.mp4> [--y0 1340 --y1 1476]

Dependencias: opencv-python-headless y numpy (no las trae el estudio: van en un venv).

Como funciona:
1. Mascara por cuadro: lo blanco Y delgado (top-hat) dentro de la franja, creciendo desde
   x=540 porque la palabra va centrada. Una pared blanca no es delgada y no entra.
2. Relleno temporal: cuando la palabra cambia o la camara se mueve, el fondo que tapaba
   queda a la vista en los cuadros de la MISMA toma (los cortes se detectan con scdet).
   Se alinea el vecino —traslacion, afin con ECC (la camara gira o cambia de escala) y, si
   no basta, flujo denso (alguien camina o mueve las manos: cada pixel con su movimiento)—
   y se copia POR ZONAS: solo donde encaja con lo que rodea a la palabra.
3. Lo que no se pudo rellenar asi (algo que se mueve distinto al fondo) va con inpaint.

Todo se hace en YUV, leyendo y escribiendo los planos con ffmpeg: la primera version
pasaba por RGB con OpenCV y la ida y vuelta con matrices distintas oscurecia 2 niveles
y corria el color de TODO el cuadro. Asi, fuera de la franja el video queda igual.
"""
import subprocess, sys, json
import cv2
import numpy as np

args = sys.argv[1:]
def opt(n, d):
    return int(args[args.index(n) + 1]) if n in args else d
ENTRADA, SALIDA = args[0], args[1]
Y0, Y1 = opt("--y0", 1340), opt("--y1", 1476)
Y0, Y1 = Y0 - Y0 % 2, Y1 + Y1 % 2  # pares: el croma va a media resolucion
VENTANA = 24      # cuadros a cada lado donde buscar el fondo (sin salir de la toma)
SECOS = 6         # vecinos seguidos sin aportar nada antes de abandonar ese lado
QUIETO = 6.0      # diferencia media de luma (suavizada) alrededor de la palabra, ya alineado
MARGEN = 120      # margen arriba y abajo de la franja: da contexto a la alineacion y espacio al vecino
K_TOP = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))


def info(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


W, H, FR = info(ENTRADA)
TAM = W * H * 3 // 2
FPS = eval(FR)  # "24000/1001"


def tomas(path):
    """Numero de toma de cada cuadro: el fondo solo se busca dentro de la misma toma."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "scdet=threshold=12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    cortes = sorted(round(float(x) * FPS) for x in
                    [l.split("lavfi.scd.time:")[1].split()[0] for l in err.splitlines() if "lavfi.scd.time:" in l])
    return lambda t: sum(c <= t for c in cortes)
YA, YB = max(0, Y0 - MARGEN), min(H, Y1 + MARGEN)


def cuadros(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"],
                         stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(TAM)
        if len(buf) < TAM:
            break
        yield np.frombuffer(buf, np.uint8).copy()
    p.wait()


def planos(f):
    q = W * H // 4
    return (f[:W * H].reshape(H, W), f[W * H:W * H + q].reshape(H // 2, W // 2),
            f[W * H + q:].reshape(H // 2, W // 2))


def a_croma(m):
    """Mascara de luma -> croma: basta un pixel de los cuatro."""
    return m.reshape(m.shape[0] // 2, 2, m.shape[1] // 2, 2).max(axis=(1, 3))


def mascara(y, u, v):
    w = y.shape[1]
    cx = w // 2
    neutro = (np.abs(u.astype(np.int16) - 128) <= 14) & (np.abs(v.astype(np.int16) - 128) <= 14)
    blanco = (y >= 215) & np.repeat(np.repeat(neutro, 2, 0), 2, 1)
    trazo = (blanco & (cv2.morphologyEx(y, cv2.MORPH_TOPHAT, K_TOP) >= 15)).astype(np.uint8)
    cols = trazo.sum(axis=0) > 2
    if not cols[cx - 60:cx + 60].any():
        return None

    def extremo(paso):
        x, hueco, ult = cx, 0, cx
        while 0 < x < w - 1 and hueco < 34:
            if cols[x]:
                ult, hueco = x, 0
            else:
                hueco += 1
            x += paso
        return ult

    x0, x1 = extremo(-1), extremo(1)
    filas = np.where(trazo[:, x0:x1 + 1].sum(axis=1) > 0)[0]
    if x1 - x0 < 20 or len(filas) == 0:
        return None
    ya, yb = max(0, filas[0] - 6), min(y.shape[0], filas[-1] + 7)
    xa, xb = max(0, x0 - 6), min(w, x1 + 7)
    # Solo lo blanco pegado al trazo: el fondo blanco que cae dentro de la caja (una
    # fachada, una sabana) no se borra, que era lo que dejaba manchas.
    cerca = cv2.dilate(trazo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)
    # Sobre un brillo (el reflejo de una mesa) la letra no es "delgada" y el top-hat no la
    # ve: el blanco PURO de la letra (Y ~235) se toma igual si esta cerca de la palabra.
    puro = (y >= 228) & np.repeat(np.repeat(neutro, 2, 0), 2, 1)
    cerca_ancha = cv2.dilate(trazo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(bool)
    m = np.zeros(y.shape, np.uint8)
    m[ya:yb, xa:xb] = ((blanco & cerca) | (puro & cerca_ancha))[ya:yb, xa:xb]
    return cv2.dilate(m, np.ones((7, 7), np.uint8))


# Pasada 1: solo la franja ancha de cada cuadro (cabe en memoria; el cuadro entero no).
ys, us, vs, mascaras, grises = [], [], [], [], []
for f in cuadros(ENTRADA):
    y, u, v = planos(f)
    yb, ub, vb = y[YA:YB].copy(), u[YA // 2:YB // 2].copy(), v[YA // 2:YB // 2].copy()
    mi = mascara(y[Y0:Y1], u[Y0 // 2:Y1 // 2], v[Y0 // 2:Y1 // 2])
    m = None
    if mi is not None:
        m = np.zeros(yb.shape, np.uint8)
        m[Y0 - YA:Y1 - YA] = mi
    g = yb if m is None else cv2.inpaint(yb, m, 3, cv2.INPAINT_TELEA)  # sin la palabra quieta
    ys.append(yb); us.append(ub); vs.append(vb); mascaras.append(m)
    grises.append(cv2.resize(g, None, fx=0.5, fy=0.5).astype(np.float32))
n = len(ys)
alto, ancho = ys[0].shape


def heredar(orden):
    """Sobre un destello o algo blanco, la palabra deja de verse como trazo pero sigue ahi
    (el subtitulo queda quieto): se hereda la mascara del cuadro vecino mientras lo que cubria
    siga siendo blanco, hasta medio segundo. Sin esto quedaba "enco...nos" en una transicion."""
    previa, edad = None, 0
    for t in orden:
        m = mascaras[t]
        if previa is not None and edad < 12 and (m is None or m.sum() < 0.95 * previa.sum()):
            if (ys[t][previa.astype(bool)] >= 200).mean() > 0.8:
                mascaras[t] = previa if m is None else (m | previa)
                edad += 1
                continue
        previa, edad = m, 0


heredar(range(n))
heredar(range(n - 1, -1, -1))
HANN = cv2.createHanningWindow((grises[0].shape[1], grises[0].shape[0]), cv2.CV_32F)
UNOS = np.ones((alto, ancho), np.uint8)


TOMA = tomas(ENTRADA)
ECC = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 1e-3)
suave = lambda a: cv2.GaussianBlur(a, (5, 5), 0).astype(np.int16)  # tolera medio pixel de desalineacion


def mover(a, M, interp):
    """M: afin 2x3 que lleva coordenadas de t a coordenadas de s (WARP_INVERSE_MAP)."""
    return cv2.warpAffine(a, M, (a.shape[1], a.shape[0]), flags=interp | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def correccion(actual, vecino, zona, sigma):
    """Diferencia de brillo lenta entre el cuadro y el vecino alineado: se mide alrededor de
    la palabra y se extiende hacia adentro (convolucion normalizada). Un reflejo o un cambio
    de luz no se mueve con la superficie; asi se copia el detalle del vecino con el brillo
    del cuadro actual, en vez de rechazarlo y caer al inpaint (que dejaba letras fantasma)."""
    w = zona.astype(np.float32)
    num = cv2.GaussianBlur((actual.astype(np.float32) - vecino.astype(np.float32)) * w, (0, 0), sigma)
    return num / np.maximum(cv2.GaussianBlur(w, (0, 0), sigma), 1e-3)


GX, GY = np.meshgrid(np.arange(ancho, dtype=np.float32), np.arange(alto, dtype=np.float32))
GXc, GYc = np.meshgrid(np.arange(ancho // 2, dtype=np.float32), np.arange(alto // 2, dtype=np.float32))


def de_afin(M):
    """Mapas de remap para una afin dada en coordenadas de media resolucion."""
    xl = (M[0, 0] * (GX / 2) + M[0, 1] * (GY / 2) + M[0, 2]) * 2
    yl = (M[1, 0] * (GX / 2) + M[1, 1] * (GY / 2) + M[1, 2]) * 2
    xc = M[0, 0] * GXc + M[0, 1] * GYc + M[0, 2]
    yc = M[1, 0] * GXc + M[1, 1] * GYc + M[1, 2]
    return (xl, yl), (xc, yc)


def de_flujo(f):
    """Mapas de remap para un flujo denso (media resolucion): cada pixel se mueve por su
    lado. Es lo que salva una toma donde la persona se mueve distinto que el fondo."""
    fx = cv2.resize(f[..., 0], (ancho, alto)) * 2
    fy = cv2.resize(f[..., 1], (ancho, alto)) * 2
    return (GX + fx, GY + fy), (GXc + f[..., 0], GYc + f[..., 1])


def alineaciones(t, s):
    """Formas de traer el cuadro s sobre el t, de la mas barata a la mas cara. El flujo denso
    solo con vecinos cercanos: lejos el movimiento es grande y el flujo ya no es fiable (y es
    lo que mas cuesta: con esto el borrado tarda minutos y no una hora)."""
    (dx, dy), _ = cv2.phaseCorrelate(grises[t], grises[s], HANN)
    for sg in (1, -1):  # camara quieta o paneo
        yield de_afin(np.float32([[1, 0, sg * dx], [0, 1, sg * dy]]))
    try:  # la camara ademas gira o cambia de escala
        _, M = cv2.findTransformECC(grises[t], grises[s], np.float32([[1, 0, dx], [0, 1, dy]]),
                                    cv2.MOTION_AFFINE, ECC, None, 5)
        yield de_afin(M)
    except cv2.error:
        pass
    # alguien camina o mueve las manos: cada pixel con su propio movimiento
    if abs(t - s) <= 8:
        yield de_flujo(cv2.calcOpticalFlowFarneback(grises[t], grises[s], None, 0.5, 3, 21, 2, 5, 1.2, 0))


def traer(plano, mapa, interp=cv2.INTER_LINEAR):
    return cv2.remap(plano, mapa[0], mapa[1], interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


limpias, temporal, espacial = [], 0, 0
for t in range(n):
    m = mascaras[t]
    if m is None:
        limpias.append(None)
        continue
    y, u, v = ys[t].copy(), us[t].copy(), vs[t].copy()
    falta = m.astype(bool)
    falta_c = a_croma(m).astype(bool)
    anillo = cv2.dilate(m, np.ones((41, 41), np.uint8)).astype(bool) & ~falta
    ys_t = suave(y)
    secos = {-1: 0, 1: 0}
    for d in range(1, VENTANA + 1):
        for lado in (-1, 1):
            s = t + lado * d
            if not (0 <= s < n) or not falta.any() or TOMA(s) != TOMA(t) or secos[lado] >= SECOS:
                continue
            antes = int(falta.sum())
            ms = mascaras[s] if mascaras[s] is not None else np.zeros_like(UNOS)
            for mapa, mapa_c in alineaciones(t, s):
                vec = traer(ys[s], mapa)
                libre = traer(UNOS, mapa, cv2.INTER_NEAREST).astype(bool) & \
                    ~traer(ms, mapa, cv2.INTER_NEAREST).astype(bool)
                zona = anillo & libre
                if zona.sum() < 200:
                    continue
                cand = np.clip(vec + correccion(y, vec, zona, 12), 0, 255)
                # Se acepta POR ZONAS, no todo o nada: la diferencia medida alrededor de la
                # palabra se extiende hacia adentro y solo entra donde el vecino encaja.
                dif = np.abs(ys_t - suave(cand)).astype(np.float32)
                conf = correccion(dif, np.zeros_like(dif), zona, 10)
                ok = falta & libre & (conf < QUIETO)
                if not ok.any():
                    continue
                y[ok] = cand[ok]
                falta &= ~ok
                ok_c = falta_c & ~a_croma((~ok).astype(np.uint8)).astype(bool)
                if ok_c.any():
                    zona_c = ~a_croma((~zona).astype(np.uint8)).astype(bool)
                    for plano, suyo in ((u, us[s]), (v, vs[s])):
                        vc = traer(suyo, mapa_c)
                        plano[ok_c] = np.clip(vc + correccion(plano, vc, zona_c, 6), 0, 255)[ok_c]
                    falta_c &= ~ok_c
                if not falta.any():
                    break
            secos[lado] = 0 if falta.sum() < antes else secos[lado] + 1
    total = int(m.astype(bool).sum())
    resto = int(falta.sum())
    temporal += total - resto
    espacial += resto
    if resto:
        y = cv2.inpaint(y, falta.astype(np.uint8), 6, cv2.INPAINT_TELEA)
    if falta_c.any():
        u = cv2.inpaint(u, falta_c.astype(np.uint8), 3, cv2.INPAINT_TELEA)
        v = cv2.inpaint(v, falta_c.astype(np.uint8), 3, cv2.INPAINT_TELEA)
    limpias.append((y[Y0 - YA:Y1 - YA], u[(Y0 - YA) // 2:(Y1 - YA) // 2], v[(Y0 - YA) // 2:(Y1 - YA) // 2]))

# Pasada 2: el cuadro original con solo la franja reemplazada, en YUV y sin convertir color.
enc = subprocess.Popen(
    ["ffmpeg", "-y", "-v", "error",
     "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", FR, "-i", "-",
     "-i", ENTRADA, "-map", "0:v", "-map", "1:a?",
     "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p",
     "-c:a", "copy", "-movflags", "+faststart", SALIDA],
    stdin=subprocess.PIPE)
for t, f in enumerate(cuadros(ENTRADA)):
    if t < n and limpias[t] is not None:
        y, u, v = planos(f)
        y[Y0:Y1], u[Y0 // 2:Y1 // 2], v[Y0 // 2:Y1 // 2] = limpias[t]
    enc.stdin.write(f.tobytes())
enc.stdin.close()
enc.wait()

con = sum(m is not None for m in mascaras)
tot = max(1, temporal + espacial)
print(f"{n} cuadros · {con} con subtitulo · relleno temporal {100 * temporal / tot:.0f}% · inpaint {100 * espacial / tot:.0f}%")
print(SALIDA)
