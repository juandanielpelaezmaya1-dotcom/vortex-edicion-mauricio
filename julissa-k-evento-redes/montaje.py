"""Montaje del recap del 4.o encuentro empresarial Nexus Narino (charla de Julissa Katerin, 18-nov-2026).

    .venv/Scripts/python -I julissa-k-evento-redes/montaje.py        (desde la raiz)

Escribe manifest.json y cache/cortes.json (que lee audio/mezcla.py). Si cambias una toma o un
tiempo, cambialo AQUI y vuelve a correr los dos scripts; no edites el manifest a mano.

Estructura tomada de la referencia (recap del Awaken Summit): frase fuerte desde la tarima como
gancho -> golpe y montaje con musica -> la anfitriona da la bienvenida a camara -> charla y
testimonios -> otro montaje sin voz -> mas charla y testimonios -> cierre que aterriza la idea.
Pulso 100 BPM (0,6 s): los montajes sin voz cortan al pulso; la musica (audio/mezcla.py) va
sobre la misma grilla. Las voces son el sonido real de cada toma, en sincronia: los tramos
verificados con whisper small palabra por palabra.
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
M = "material/C20261118_{}.MP4"
PULSO = 0.6
COMPAS = 4 * PULSO

# Bloques en orden. Un bloque de VOZ: (clave, archivo, in_s, out_s, [tomas]); las tomas son
#   ("sync", dur)            -> la misma toma de quien habla, en sincronia con su voz
#   (archivo, in_s, dur)     -> toma de apoyo encima de la voz (la voz sigue)
# Un bloque SIN VOZ: ("abierto", [(archivo, in_s, dur)], golpe) -> montaje al pulso con la musica arriba.
BLOQUES = [
    # --- gancho: Julissa en la tarima. "Si no tenemos claro el proposito, esta empresa esta sin alma"
    ("voz", "5622", 19.80, 25.95, [("sync", 3.3), ("5626", 3.0, None)]),
    # --- golpe + montaje del evento (2 compases)
    ("abierto", [("5601", 5.5, 1.2), ("5616", 2.0, 0.6), ("5624", 1.5, 0.6), ("5621", 0.5, 1.2),
                 ("5617", 1.5, 0.6), ("5606", 3.0, 0.6)], True),
    # --- bienvenida a camara: "Hola, muy buenas noches ... cuarto encuentro empresarial Nexus Narino,
    #     un espacio para que crezcamos en comunidad"
    ("voz", "5595", 0.00, 10.05, [("sync", 4.6), ("5602", 1.5, 1.5), ("5613", 3.4, 1.4), ("sync", None)]),
    # --- Julissa expone: "Cuando nosotros nos congregamos con un proposito que es crecer en conjunto,
    #     surgen muchisimas ... ideas, proyectos, alianzas, incluso amistades"
    ("voz", "5615", 7.35, 19.95, [("sync", 3.65), ("5620", 3.0, 2.0), ("sync", 3.5), ("5608", 3.0, 0.8),
                                  ("5618", 4.0, 0.8), ("sync", None)]),
    # --- Karen: "Estos encuentros ya hacen falta y uno necesita la conexion"
    ("voz", "5600", 17.25, 20.35, [("sync", None)]),
    # --- Carito: "Me voy muy feliz con muchos tips, con muchas ideas, con todos mis bombillos encendidos"
    ("voz", "5599", 18.70, 24.50, [("sync", None)]),
    # --- montaje de la exposicion (3 compases, una toma larga que rompe el pulso: R2)
    ("abierto", [("5623", 0.5, 1.2), ("5609", 4.0, 0.6), ("5612", 4.0, 0.6), ("5629", 6.0, 2.4),
                 ("5630", 3.0, 1.2), ("5627", 21.0, 1.2)], True),
    # --- Julissa: "Hay muchas maneras de competir sin competir por precio"
    ("voz", "5628", 17.15, 23.60, [("sync", None)]),
    # --- Julissa: "Ponerte en la postura de cliente. Tu como cliente, que quieres ver"
    ("voz", "5631", 1.00, 7.10, [("sync", None)]),
    # --- diseñadora: "Como empresarios a nosotros nos ha costado mucho sacar nuestra marca, y es algo
    #     que queremos como un hijo"
    ("voz", "5607", 68.90, 76.25, [("sync", 3.5), ("5605", 9.0, 1.4), ("sync", None)]),
    # --- Leo: "El encuentro supero mis expectativas, me nutrio demasiado en conocimiento"
    ("voz", "5635", 20.50, 25.00, [("sync", None)]),
    # --- Monica: "No es solamente la parte de dinero sino la parte de educacion, que es la mas importante"
    ("voz", "5637", 96.40, 101.10, [("sync", None)]),
    # --- cierre: "Todos unidos a un proposito, que es crecer en comunidad desde el ganar-ganar"
    ("voz", "5636", 10.70, 15.60, [("sync", None)]),
    # --- Julissa sonrie a camara en camara lenta mientras la musica cierra (R4)
    ("final", "5594", 4.8, 3.6, 0.7),
]
HUECO = 0.15   # respiro entre dos voces seguidas
D = "desenfoque"

clips, voces, abiertos, impactos, drops, tomas = [], [], [], [], [], []
t = 0.0
zooms = ["in", None, "out"]
zi = 0


def poner(arch, ins, dur, trans=D, vel=1.0):
    global t, zi
    z = zooms[zi % 3]
    zi += 1
    c = {"archivo": M.format(arch), "in_s": round(ins, 3), "out_s": round(ins + dur * vel, 3), "volumen": 0}
    if vel != 1.0:
        c["velocidad"] = vel
    if z:
        c["zoom"] = {"tipo": z, "intensidad": 1.08}
    if trans and t > 0:
        c["transicion"] = {"tipo": "escala", "duracion_s": 0.25} if trans == "escala" else {"tipo": "desenfoque", "duracion_s": 0.13}
    clips.append(c)
    tomas.append([M.format(arch), round(ins, 3), round(t, 3), round(dur, 3)])
    t = round(t + dur, 3)


previo = None
for b in BLOQUES:
    if b[0] == "voz":
        _, arch, a, z, plano = b
        if previo == "voz":
            # el respiro va en la toma anterior: se alarga sin cambiar su inicio
            clips[-1]["out_s"] = round(clips[-1]["out_s"] + HUECO, 3)
            tomas[-1][3] = round(tomas[-1][3] + HUECO, 3)
            t = round(t + HUECO, 3)
        en = t
        largo = round(z - a, 3)
        voces.append([M.format(arch), a, z, en])
        usado = sum(p[-1] if p[0] == "sync" else p[2] for p in plano if (p[-1] if p[0] == "sync" else p[2]) is not None)
        for k, p in enumerate(plano):
            dur = p[1] if p[0] == "sync" else p[2]
            if dur is None:
                dur = round(largo - usado, 3)
            trans = "escala" if (k == 0 and previo == "abierto") else D
            if p[0] == "sync":
                poner(arch, a + (t - en), dur, trans)
            else:
                poner(p[0], p[1], dur, trans)
        previo = "voz"
    elif b[0] == "abierto":
        _, plano, golpe = b
        a0 = t
        if golpe:
            impactos.append(t)
            drops.append(t)
        for k, (arch, ins, dur) in enumerate(plano):
            poner(arch, ins, dur, "escala" if k == 0 else D)
        abiertos.append([a0, t])
        previo = "abierto"
    else:  # final
        _, arch, ins, dur, vel = b
        a0 = t
        poner(arch, ins, dur, "disolver", vel)
        clips[-1]["transicion"] = {"tipo": "disolver", "duracion_s": 0.4}
        impactos.append(round(a0, 3))
        abiertos.append([a0, t + 1])

TOTAL = t
assert TOTAL <= 90, TOTAL
vistos = [c["archivo"] for c in clips]
apoyo = [x for x in vistos if vistos.count(x) > 1 and x not in [v[0] for v in voces]]
assert not apoyo, f"toma de apoyo repetida (R3): {apoyo}"

manifest = {
    "slug": "julissa-k-evento-redes",
    "fps": 29.97,
    "formatos": ["9x16"],
    "_nota": "Generado por montaje.py (no editar a mano). Audio: audio/mezcla.py -> material/mezcla.wav (voces de las tomas + musica original). Sin musica: material/mezcla-sin-musica.wav",
    "clips": clips,
    "pistas": [{"archivo": "material/mezcla.wav", "in_s": 0, "out_s": TOTAL, "en_s": 0, "volumen": 1,
                "limpiar": False, "ganancia_db": 0, "fundido_s": [0.01, 0.01]}],
    "destellos": [{"en_s": i, "duracion_s": 0.3, "color": "#FFF1E6", "intensidad": 0.55} for i in impactos[:2]],
    "progreso": False,
}
with open(os.path.join(AQUI, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
os.makedirs(os.path.join(AQUI, "cache"), exist_ok=True)
with open(os.path.join(AQUI, "cache", "cortes.json"), "w") as f:
    json.dump({"total": TOTAL, "voces": voces, "abiertos": abiertos, "drops": drops, "impactos": impactos,
               "tomas": tomas}, f)
print(f"{len(clips)} tomas, {TOTAL} s")
for v in voces:
    print(f"  voz {v[0][-8:-4]} {v[1]:6.2f}-{v[2]:6.2f} en {v[3]:6.2f}")
print(f"  abiertos {abiertos}\n  impactos {impactos}")
