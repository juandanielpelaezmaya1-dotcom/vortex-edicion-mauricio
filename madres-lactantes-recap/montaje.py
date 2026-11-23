"""Montaje del recap del Dia de la Escucha a la Gestante (Secretaria de Salud de Pasto, 22-nov-2026).

    .venv/Scripts/python -I madres-lactantes-recap/montaje.py        (desde la raiz)

Escribe manifest.json y cache/cortes.json (que lee audio/mezcla.py). Si cambias una toma o un
tiempo, cambialo AQUI y vuelve a correr los dos scripts; no edites el manifest a mano.

Pulso: 120 BPM (0,5 s). Todos los cortes caen en el pulso; la musica (audio/mezcla.py) se
compone sobre la misma grilla. Las tomas van en el orden en que paso el evento.
Voz en off: testimonio C20261122_5748 (Angelica Sanchez), en tres tramos limpios (verificados
con whisper): sin el saludo, sin "teniendo en cuenta que con los bebes..." y sin "etcetera".
"""
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
M = "material/C20261122_{}.MP4"

# Voz: (in_s, out_s, en_s) del archivo 5748
VOZ = [
    (2.82, 19.62, 4.0),    # Angelica Sanchez ... celebrando el dia de la escucha a la gestante. Hemos convocado mas de 150 gestantes, las hemos dividido en dos grupos,
    (23.88, 37.06, 21.2),  # ya cerca de 60 gestantes ... el plan de parto humanizado,
    (37.70, 78.22, 34.7),  # Ademas han salido premiadas ... animacion para sus bebes.
]

# (toma, in_s, duracion en la linea de tiempo, zoom, transicion de entrada)
# zoom: "in" / "out" / None alterna para que el corte no salte.
D = "desenfoque"
TOMAS = [
    # --- gancho, solo musica: los bebes del evento + titulo (0-4)
    ("5675", 0.5, 1.0, "in", None),
    ("5683", 1.5, 1.0, "out", "escala"),
    ("5686", 2.0, 1.0, "in", D),
    ("5697", 1.5, 1.0, "out", D),
    # --- Angelica se presenta (sincronia labial: mismo rango que la voz)
    ("5748", 2.82, 5.5, "in", "escala"),
    # --- "estamos hoy aqui ... celebrando el dia de la escucha a la gestante"
    ("5674", 10.0, 1.5, "out", "deslizar-izq"),
    ("5699", 1.0, 1.5, "in", D),
    ("5677", 2.0, 1.5, None, D),
    ("5676", 1.5, 1.5, "out", D),
    # --- "hemos convocado mas de 150 gestantes, las hemos dividido en dos grupos"
    ("5680", 0.3, 1.5, "in", D),
    ("5730", 1.0, 1.5, "out", D),
    ("5693", 1.5, 1.0, "in", D),
    ("5692", 2.0, 1.5, None, D),
    # --- "cerca de 60 gestantes en este primer grupo, fortaleciendo los temas importantes..."
    ("5700", 1.5, 1.5, "in", "deslizar-der"),
    ("5687", 4.0, 1.5, "out", D),
    ("5688", 1.2, 1.0, "in", D),
    ("5689", 1.5, 1.5, None, D),
    ("5694", 1.0, 1.0, "out", D),
    ("5698", 2.0, 1.5, "in", D),
    ("5704", 2.0, 1.5, "out", D),
    ("5705", 1.5, 1.0, "in", D),
    ("5707", 4.5, 1.5, None, D),
    ("5712", 3.0, 1.5, "out", D),
    # --- "ademas han salido premiadas, se han llevado detalle"
    ("5713", 2.0, 1.0, "in", "escala"),
    ("5718", 0.3, 1.0, "out", D),
    ("5722", 2.5, 1.0, "in", D),
    ("5723", 2.0, 1.0, "out", D),
    ("5724", 3.0, 1.0, "in", D),
    ("5726", 0.3, 1.0, "out", D),
    ("5729", 5.0, 1.0, "in", D),
    # --- "una feria de servicios ... comite materno perinatal, IPS, CPS, Banco de Leche Humana"
    ("5731", 1.0, 1.5, "out", "deslizar-izq"),
    ("5732", 2.0, 1.0, "in", D),
    ("5733", 1.0, 1.5, "out", D),
    ("5734", 4.0, 1.0, "in", D),
    ("5735", 2.0, 1.5, None, D),
    ("5737", 1.0, 1.5, "out", D),
    ("5738", 2.0, 1.0, "in", D),
    # --- "la Secretaria de las Mujeres y la Academia ... universidades"
    ("5739", 1.0, 1.5, "out", D),
    ("5740", 2.5, 1.5, "in", D),
    ("5741", 6.0, 1.5, None, D),
    ("5743", 3.0, 1.5, "out", D),
    # --- "ellas estan ofreciendo informacion ... para que se vayan totalmente educadas"
    ("5742", 2.0, 1.5, "in", "deslizar-der"),
    ("5745", 1.0, 1.5, "out", D),
    ("5747", 1.0, 1.5, "in", D),
    ("5744", 0.5, 1.5, "out", D),
    ("5746", 2.0, 2.0, "in", D),
    # --- "finalmente la Secretaria de Cultura ... animacion para sus bebes"
    ("5714", 1.0, 1.5, "out", "escala"),
    ("5717", 1.0, 1.5, "in", D),
    ("5727", 1.0, 1.5, None, D),
    ("5728", 3.0, 1.5, "out", D),
    ("5719", 2.0, 1.5, "in", D),
    ("5709", 0.5, 1.5, "out", D),
    ("5720", 2.0, 1.5, "in", D),
    # --- cierre: las mamas con sus bebes, en grupo (75-80)
    ("5736", 8.0, 5.0, "out", "disolver"),
]

ZOOM = {"in": {"tipo": "in", "intensidad": 1.1}, "out": {"tipo": "out", "intensidad": 1.1}}


def transicion(t):
    if t is None:
        return None
    if t.startswith("deslizar"):
        return {"tipo": "deslizar", "desde": t.split("-")[1], "duracion_s": 0.28}
    if t == "escala":
        return {"tipo": "escala", "duracion_s": 0.25}
    if t == "disolver":
        return {"tipo": "disolver", "duracion_s": 0.4}
    return {"tipo": "desenfoque", "duracion_s": 0.15}


clips, cortes, capitulos = [], [], []
t = 0.0
for toma, i, dur, z, tr in TOMAS:
    c = {"archivo": M.format(toma), "in_s": i, "out_s": round(i + dur, 3), "volumen": 0}
    if z:
        c["zoom"] = ZOOM[z]
    if tr:
        c["transicion"] = transicion(tr)
    clips.append(c)
    if t > 0:
        cortes.append(round(t, 3))
        if tr and tr != D:
            capitulos.append(round(t, 3))
    t += dur
TOTAL = round(t, 3)
assert TOTAL <= 90, TOTAL
assert len({x[0] for x in TOMAS}) == len(TOMAS), "una toma repetida (R3)"

manifest = {
    "slug": "madres-lactantes-recap",
    "fps": 29.97,
    "formatos": ["9x16"],
    "_nota": "Generado por montaje.py (no editar a mano). Audio: audio/mezcla.py -> material/mezcla.wav (voz 5748 + musica original 120 BPM + whooshes). Motion: _render/src/GestanteMotion.tsx -> material/mg/*.webm",
    "clips": clips,
    "pistas": [{"archivo": "material/mezcla.wav", "in_s": 0, "out_s": TOTAL, "en_s": 0, "volumen": 1,
                "limpiar": False, "ganancia_db": 0, "fundido_s": [0.01, 0.01]}],
    "destellos": [{"en_s": c, "duracion_s": 0.3, "color": "#FFF1DC", "intensidad": 0.55} for c in (34.5, 64.5)],
    "overlays": [
        {"archivo": "material/mg/titulo.webm", "en_s": 0.15, "encima": True},
        {"archivo": "material/mg/credencial.webm", "en_s": 4.45, "encima": True},
        {"archivo": "material/mg/cierre.webm", "en_s": 75.4, "encima": True},
    ],
    "progreso": False,
}
with open(os.path.join(AQUI, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
os.makedirs(os.path.join(AQUI, "cache"), exist_ok=True)
with open(os.path.join(AQUI, "cache", "cortes.json"), "w") as f:
    json.dump({"total": TOTAL, "cortes": cortes, "capitulos": capitulos, "voz": VOZ}, f)
print(f"{len(clips)} tomas, {TOTAL} s; capitulos en {capitulos}")
