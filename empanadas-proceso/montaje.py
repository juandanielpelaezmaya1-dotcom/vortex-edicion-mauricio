"""Montaje del reel "El arte de la empanada" (B-roll gastronomico, sin voz).

    .venv/Scripts/python -I empanadas-proceso/montaje.py        (desde la raiz)

Escribe manifest.json y cache/cortes.json (que lee audio/mezcla.py). Si cambias una toma o un
tiempo, cambialo AQUI y vuelve a correr los dos scripts; no edites el manifest a mano.

Material: tarjeta Sony C20261112_5221..5309 (vertical 2160x3840; 5221-5248 a 29,97 y 5249-5309 a
59,94). Las tomas usadas van con el look horneado en material/look/NNNN.mov (color/convertir.sh).

Estructura (brief del 2026-11-26): gancho con el final (cae al aceite / sale dorada) ->
masa -> relleno -> armado -> aceite -> escurrido -> emplatado -> la clienta prueba.
Todo corta al pulso: 119,88 BPM = 15 cuadros a 29,97 (0,5005 s), asi cada corte cae en un cuadro.
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
FPS = 29.97
PULSO = 15 / FPS
M = "material/look/{}.mov"

# (toma, in_s, pulsos, velocidad, seccion, [sfx])
#   sfx: etiquetas que audio/mezcla.py convierte en efectos en el corte de esa toma:
#   llama, hervor, harina, agua, golpe, amasar, cuchara, rodillo, limon, aceite, fritura, escurrir,
#   plato, crunch.  (whoosh va solo en los cambios de seccion y cada dos cortes)
TOMAS = [
    # --- GANCHO: el final primero (2 s, camara lenta real a 60p)
    ("5284", 1.30, 4, 0.5, "gancho", ["fritura"]),       # la espumadera las saca doradas, escurriendo aceite
    # --- MASA
    ("5222", 0.80, 2, 1.0, "masa", ["llama@0.5"]),       # se enciende el fogon
    ("5226", 1.00, 2, 1.0, "masa", ["hervor"]),          # el agua hierve
    ("5229", 3.50, 2, 1.0, "masa", ["harina"]),          # cae la harina
    ("5232", 8.90, 2, 1.0, "masa", ["harina"]),          # la sal
    ("5235", 2.50, 2, 1.0, "masa", ["agua"]),            # el agua caliente sobre la harina
    ("5236", 4.00, 2, 2.0, "masa", ["amasar"]),          # mezcla en el platon, rapido
    ("5238", 2.20, 2, 1.5, "masa", ["golpe@0.13"]),      # la masa cae a la mesa
    ("5243", 0.50, 2, 2.0, "masa", ["amasar"]),          # amasa, rapido
    ("5241", 0.00, 1, 1.0, "masa", ["golpe@0.35"]),      # la bola cae
    ("5268", 2.50, 2, 1.0, "masa", ["amasar"]),          # la masa de maiz sale del plastico
    ("5271", 2.00, 2, 1.0, "masa", ["limon@0.2"]),       # limon sobre la masa
    ("5274", 0.50, 2, 1.5, "masa", ["golpe@0.4"]),       # amasa la amarilla
    # --- RELLENO
    ("5244", 5.00, 2, 1.0, "relleno", ["plato@0.4"]),    # el guiso llega a la mesa
    ("5256", 9.00, 2, 1.0, "relleno", ["cuchara@0.3"]),  # cucharada de relleno
    # --- ARMADO
    ("5246", 2.50, 4, 1.0, "armado", ["harina@0.4"]),    # nube de harina sobre la mesa (dos pulsos mas: R2)
    ("5249", 4.50, 2, 1.5, "armado", ["rodillo"]),       # el rodillo
    ("5253", 9.50, 2, 1.5, "armado", ["rodillo"]),       # levanta el disco abierto
    ("5248", 1.00, 2, 1.0, "armado", ["cuchara@0.2"]),   # el relleno sobre el disco
    ("5250", 14.0, 2, 1.0, "armado", ["golpe@0.2"]),     # el molde corta la empanada
    ("5276", 14.3, 2, 1.0, "armado", ["amasar"]),        # la de maiz se cierra con el plastico
    ("5287", 5.00, 4, 1.0, "armado", ["amasar"]),        # el repulgue (dos pulsos mas: R2)
    ("5251", 1.50, 2, 1.0, "armado", []),                # listas
    # --- ACEITE
    ("5283", 1.80, 3, 1.0, "aceite", ["aceite@0.5"]),    # cae al aceite y estalla
    ("5258", 0.00, 2, 1.0, "aceite", ["aceite"]),        # bajan en la espumadera
    ("5262", 8.50, 3, 0.5, "aceite", ["fritura"]),       # fritura de cerca, lenta
    ("5278", 1.00, 2, 1.0, "aceite", ["fritura"]),       # las de maiz en la paila
    ("5285", 2.00, 2, 1.0, "aceite", ["fritura"]),       # sale la de maiz en la espumadera
    # --- ESCURRIDO
    ("5264", 9.80, 2, 1.0, "escurrido", ["escurrir"]),   # al colador
    ("5265", 0.50, 4, 0.5, "escurrido", ["escurrir"]),   # doradas en el colador, lenta
    # --- EMPLATADO
    ("5290", 2.20, 2, 1.0, "emplatado", ["plato@0.5"]),  # al plato de barro
    ("5294", 12.5, 2, 1.0, "emplatado", ["limon@0.3"]),  # el limon
    ("5292", 0.20, 2, 1.0, "emplatado", []),             # el plato servido
    # --- CLIENTA (cierre)
    ("5307", 3.00, 2, 1.0, "clienta", []),               # la abre
    ("5308", 6.00, 3, 1.0, "clienta", ["cuchara@0.6"]),  # aji encima
    ("5309", 16.2, 9, 1.0, "clienta", ["crunch"]),       # muerde, mastica y levanta la mirada (R4)
]

clips, cortes = [], []
t = 0.0
zooms = [("in", 1.06), None, ("out", 1.06)]
seccion_previa = None
for k, (toma, ins, pulsos, vel, sec, sfx) in enumerate(TOMAS):
    dur = pulsos * PULSO
    c = {"archivo": M.format(toma), "in_s": round(ins, 3), "out_s": round(ins + dur * vel, 3), "volumen": 0}
    if vel != 1.0:
        c["velocidad"] = vel
    z = zooms[k % 3]
    if z:
        c["zoom"] = {"tipo": z[0], "intensidad": z[1]}
    if k > 0:
        if sec != seccion_previa:
            c["transicion"] = {"tipo": "escala", "duracion_s": 0.2}
        elif k % 2 == 0:
            c["transicion"] = {"tipo": "desenfoque", "duracion_s": 0.1}
    clips.append(c)
    cortes.append({"toma": toma, "archivo": M.format(toma), "in_s": c["in_s"], "vel": vel, "en_s": round(t, 4),
                   "dur": round(dur, 4), "seccion": sec, "sfx": sfx, "cambio": sec != seccion_previa})
    seccion_previa = sec
    t += dur

TOTAL = round(t, 4)
assert 30 <= TOTAL <= 50, TOTAL
vistos = [c["archivo"] for c in clips]
assert len(set(vistos)) == len(vistos), "toma repetida (R3)"

secciones = {}
for c in cortes:
    secciones.setdefault(c["seccion"], [c["en_s"], 0])[1] = round(c["en_s"] + c["dur"], 4)

manifest = {
    "slug": "empanadas-proceso",
    "fps": FPS,
    "formatos": ["9x16"],
    "_nota": "Generado por montaje.py (no editar a mano). Imagen: material/look (color/convertir.sh). "
             "Audio: audio/mezcla.py -> material/mezcla.wav (musica original + efectos).",
    "clips": clips,
    "pistas": [{"archivo": "material/mezcla.wav", "in_s": 0, "out_s": TOTAL, "en_s": 0, "volumen": 1,
                "limpiar": False, "ganancia_db": 0, "fundido_s": [0.01, 0.01]}],
    "destellos": [{"en_s": round(secciones["masa"][0], 3), "duracion_s": 0.25, "color": "#FFE2B8", "intensidad": 0.55}],
    "progreso": False,
}
with open(os.path.join(AQUI, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
os.makedirs(os.path.join(AQUI, "cache"), exist_ok=True)
with open(os.path.join(AQUI, "cache", "cortes.json"), "w") as f:
    json.dump({"total": TOTAL, "pulso": PULSO, "fps": FPS, "cortes": cortes, "secciones": secciones}, f, indent=1)
print(f"{len(clips)} tomas, {TOTAL:.2f} s, {TOTAL / PULSO:.0f} pulsos")
for s, (a, b) in secciones.items():
    print(f"  {s:10s} {a:6.2f} - {b:6.2f}")
