# Hoja de revision de un reel ya renderizado: un cuadro por pagina de subtitulos (al final de la pagina,
# con todas sus palabras ya en pantalla) y por texto en pantalla, mas el primero y el ultimo, con el texto
# rotulado debajo.
# Va despues de `render --borrador` (lee cache/props.json y cache/borrador.mp4). Necesita Pillow:
#   python3 -m venv .venv && .venv/bin/pip install pillow          (Windows: .venv/Scripts/pip)
#   .venv/bin/python herramientas/revision.py <carpeta del reel>...  ->  <carpeta>/cache/revision.jpg
import json, math, os, subprocess, sys, tempfile, textwrap
from PIL import Image, ImageDraw, ImageFont


def fuente(tam, *rutas):
    # Arial en Mac o Windows, DejaVu en Linux; si no hay ninguna, la de Pillow.
    for r in rutas:
        try:
            return ImageFont.truetype(r, tam)
        except OSError:
            pass
    return ImageFont.load_default(tam)


FONT = fuente(15, "/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf")
FONTB = fuente(16, "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf")
W, H, PIE, COLS = 270, 480, 58, 5


def texto_pagina(lineas):
    return " / ".join(" ".join(p["texto"] for p in l) for l in lineas)


def hoja(dir):
    props = json.load(open(os.path.join(dir, "cache", "props.json")))
    video = os.path.join(dir, "cache", "borrador.mp4")
    total = sum(c["duracion_s"] for c in props["clips"])
    marcas = [(0.15, "inicio")]
    for i, p in enumerate((props.get("subtitulos") or {}).get("paginas", [])):
        marcas.append((max(p["desde"] / 1000, p["hasta"] / 1000 - 0.3), f"S{i + 1} y={p.get('y', '-')}: {texto_pagina(p['lineas'])}"))
    for i, t in enumerate(props.get("textos", [])):
        marcas.append(((t["desde_s"] + t["hasta_s"]) / 2, f"T{i + 1}: {t['texto']}"))
    marcas.append((max(0, total - 0.2), "final"))
    marcas = sorted((min(t, total - 0.1), r) for t, r in marcas)
    cortes, acc = [], 0
    for c in props["clips"][:-1]:
        acc += c["duracion_s"]
        cortes.append(acc)
    filas = math.ceil(len(marcas) / COLS)
    img = Image.new("RGB", (COLS * (W + 4), filas * (H + PIE + 4)), "white")
    d = ImageDraw.Draw(img)
    with tempfile.TemporaryDirectory() as tmp:
        for i, (t, rot) in enumerate(marcas):
            f = os.path.join(tmp, f"{i}.jpg")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                            "-vf", f"scale={W}:{H}:out_range=full", f], check=True)
            x, y = (i % COLS) * (W + 4), (i // COLS) * (H + PIE + 4)
            img.paste(Image.open(f), (x, y))
            toma = 1 + sum(1 for c in cortes if c <= t)
            d.text((x + 3, y + H + 2), f"{t:.1f}s  toma {toma}", font=FONTB, fill="black")
            for k, linea in enumerate(textwrap.wrap(rot, 34)[:2]):
                d.text((x + 3, y + H + 20 + k * 17), linea, font=FONT, fill="black")
    salida = os.path.join(dir, "cache", "revision.jpg")
    img.save(salida, quality=82)
    print(salida, f"({len(marcas)} cuadros, {total:.1f} s)")


for dir in sys.argv[1:]:
    try:
        hoja(dir)
    except Exception as e:
        print("FALLO", dir, e)
