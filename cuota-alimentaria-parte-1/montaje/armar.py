"""Genera manifest.json de las dos partes de la serie Cuota alimentaria (Accion Juridica).

    python cuota-alimentaria-parte-1/montaje/armar.py     (desde la raiz)

Los cortes salen de montaje/cortes.json: tiempos DTW de whisper + valle de energia (cortes2.py
sobre guion.json) y despues los ajustes a mano de final.py.
Todo va a 1,1x. Este script solo arma el manifest: zooms, viñetas, luces, frases.
"""
import json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
C = json.load(open(os.path.join(RAIZ, "cuota-alimentaria-parte-1", "montaje", "cortes.json"), encoding="utf-8"))
V = 1.1
FPS = 29.97

# Foco de cada abogado en el cuadro vertical (cara)
FOCO = {"79": {"x": 60, "y": 37}, "80": {"x": 48, "y": 40}, "81": {"x": 50, "y": 37}}
# Altura de subtitulos: hombres sobre el traje oscuro, debajo del microfono blanco (a 64 lo pisaba); Marcela sobre la pared oscura, encima
# de la cabeza (su blusa blanca se come el texto blanco)
YSUB = {"79": 73, "80": 74, "81": 20}

VINETA = {
    "80": ("Víctor Rosales", "Abogado · Derecho penal"),
    "79": ("Mauricio Cepeda", "Abogado · Derecho de familia"),
    "81": ("Marcela Gómez", "Abogada · Derecho laboral"),
}

# zoom por tramo: (tipo, intensidad)
ZOOM = {
    "p1": {"a": ("in", 1.12), "b": ("fijo", 1.16), "b2": ("out", 1.1), "c": ("fijo", 1.26),
           "d": ("in", 1.12), "f": ("out", 1.1), "e": ("in", 1.1), "g": ("fijo", 1.16),
           "h2": ("in", 1.08), "i": ("fijo", 1.22), "k": ("fijo", 1.2), "j": ("in", 1.16)},
    "p2": {"a": ("in", 1.12), "a2": ("out", 1.12), "c": ("in", 1.1), "d": ("fijo", 1.18),
           "d2": ("fijo", 1.3), "e": ("out", 1.1), "f": ("in", 1.1), "f2": ("fijo", 1.2),
           "g": ("in", 1.1), "h": ("fijo", 1.16), "h2": ("out", 1.1)},
}
# Donde va la viñeta de cada abogado (id del tramo, segundos dentro del tramo)
# Vacias a proposito: hablan sin pausa y la viñeta chocaba con los subtitulos (T1). Los nombres
# van en el texto del post. Para volver a ponerlas: {"80": ("a2", 0.6), "79": ("c", 0.4), ...}
VIN_EN = {"p1": {}, "p2": {}}
# Fuga de luz (con whoosh) al entrar estos tramos: cambio de capitulo
LUZ = {"p1": ["g", "i"], "p2": ["c", "g"]}

FRASES = {
 "p1": [
  ("a", "No puede existir / *delitos*"),
  ("a", "si previamente / no existió"),
  ("a", "una _fijación_ / de una cuota / alimentaria."),
  ("b", "Las cuotas / alimentarias"),
  ("b", "nacen desde / el momento"),
  ("b", "en que / *se fijan,*"),
  ("b2", "no en el / momento en que"),
  ("b2", "el padre / o madre"),
  ("b2", "o el responsable / de un menor / de edad"),
  ("c", "no ha cumplido / con sus deberes."),
  ("d", "No nace / _únicamente_ / con el vínculo."),
  ("f", "Es muy / importante / que iniciemos"),
  ("f", "con la _fijación_ / de la cuota / alimentaria,"),
  ("f", "porque con esto / *nace* / el derecho"),
  ("f", "para que / posteriormente / se pueda exigir."),
  ("e", "Ya cuando se adquiere / esa responsabilidad"),
  ("e", "y esa obligación / de deber alimentos,"),
  ("e", "realmente surgen / _responsabilidades._"),
  ("g", "¿Qué va a hacer / esta madre?"),
  ("g", "La madre, / lo primero / que va a hacer"),
  ("g", "es un proceso / de _conciliación_"),
  ("g", "para fijar / esta cuota / alimentaria."),
  ("h2", "O podemos / acudir al / Instituto"),
  ("h2", "Colombiano / de Bienestar / Familiar."),
  ("i", "Si ya tenemos / fijada una cuota / alimentaria,"),
  ("i", "la parte / obligada / *no cumple...*"),
  ("k", {"texto": "ahí es donde entramos / a hablar de _embargos_", "palabras": 9}),
  ("j", {"texto": "tenemos una / consecuencia", "palabras": 4}),
  ("j", "ya no solo civil, / sino *penal.*"),
 ],
 "p2": [
  ("a", "El legislador / ha decidido"),
  ("a", "que la falta / de pago"),
  ("a", "o la _inasistencia_ / _alimentaria_"),
  ("a2", "se constituya / en un *delito.*"),
  ("a2", "No solo / se trata de / una deuda"),
  ("a2", "en la materia / civil,"),
  ("a2", "sino que / trascienda / el ámbito"),
  ("a2", "de afectar / por ese / incumplimiento"),
  ("a2", "la *libertad* / de las personas."),
  ("c", "El éxito / del proceso / ejecutivo"),
  ("c", "son los / *embargos*"),
  ("c", "que se pueda / realizar:"),
  ("c", "ya sea / salarios,"),
  ("c", "ya sea bienes / inmuebles,"),
  ("c", "vehículos / automotores,"),
  ("c", "establecimientos / de comercio."),
  ("d", {"texto": "Se permite el embargo / del salario", "palabras": 7}),
  ("d2", {"texto": "y en este caso / es hasta el *50 %.*", "palabras": 8}),
  ("e", "Es importante también / recordar que la ley"),
  ("e", "del _código de infancia_ / _y adolescencia_"),
  ("e", "permite también / el embargo de las"),
  ("e", "_prestaciones sociales._"),
  ("f", "Que los empleadores / también cumplan"),
  ("f", "cuando les llega / una orden."),
  ("f2", "Puede implicar / responsabilidad / disciplinaria,"),
  ("f2", "inclusive para la persona / que _no lo aplique._"),
  ("g", "Hay / circunstancias / en las que"),
  ("g", "*no* / se constituye,"),
  ("g", "como, por / ejemplo,"),
  ("g", "cuando / el deudor / alimentario"),
  ("g", "acredita / que está / _desempleado_"),
  ("g", "y puede / demostrar"),
  ("g", "que está / buscando / un empleo."),
  ("h", "Entonces / los invitamos"),
  ("h", "a nuestros / oyentes"),
  ("h", "a que nos / *consulten*"),
  ("h2", "a través de los canales / de **Acción Jurídica.**"),
 ],
}


def armar(p, carpeta):
    tramos = C[p]
    clips, inicio, t = [], {}, 0.0
    anterior = None
    for s in tramos:
        tipo, k = ZOOM[p][s["id"]]
        clip = {"archivo": f"material/C20261124_57{s['toma']}.MP4", "in_s": s["in_s"], "out_s": s["out_s"],
                "velocidad": V, "zoom": {"tipo": tipo, "hacia": FOCO[s["toma"]], "intensidad": k},
                "_dice": s["texto"]}
        if anterior is not None:
            clip["transicion"] = {"tipo": "desenfoque", "duracion_s": 0.13}
        clips.append(clip)
        inicio[s["id"]] = (round(t, 2), s)
        t += round((s["out_s"] - s["in_s"]) / V * FPS) / FPS
        anterior = s
    fin_voz = round(t, 2)

    frases = []
    for (i, txt) in FRASES[p]:
        f = dict(txt) if isinstance(txt, dict) else {"texto": txt}
        f["y"] = YSUB[inicio[i][1]["toma"]]
        frases.append(f)
    # La ultima frase de cada tramo se cierra en el corte (no cruza a la toma siguiente)
    ids = [i for (i, _) in FRASES[p]]
    orden = [s["id"] for s in tramos]
    for n, (i, _) in enumerate(FRASES[p]):
        ultima = n == len(ids) - 1 or ids[n + 1] != i
        if ultima:
            k = orden.index(i)
            fin = inicio[orden[k + 1]][0] if k + 1 < len(orden) else fin_voz
            frases[n]["hasta_s"] = round(fin - 0.05, 2)

    vinetas = []
    for toma, (i, d) in VIN_EN[p].items():
        a = inicio[i][0] + d
        s = inicio[i][1]
        dur_tramo = (s["out_s"] - s["in_s"]) / V
        h = min(inicio[i][0] + dur_tramo - 0.05, a + 4.2)
        nombre, cargo = VINETA[toma]
        vinetas.append({"nombre": nombre, "cargo": cargo, "desde_s": round(a, 2), "hasta_s": round(h, 2)})

    luces, efectos = [], []
    for n, i in enumerate(LUZ[p]):
        en = inicio[i][0]
        luces.append({"en_s": en, "duracion_s": 0.85, "intensidad": 0.55, "desde": "der" if n % 2 == 0 else "izq"})
        efectos.append({"archivo": "audio/whoosh.wav", "en_s": round(en - 0.25, 2), "volumen": 0.35})

    m = {
        "slug": carpeta,
        "fps": FPS,
        "formatos": ["9x16"],
        "composicion": "Abogados",
        "_nota": "Serie Cuota alimentaria (Accion Juridica, capsula en Ecos de Pasto 24-nov-2026). "
                 "Montaje exploratorio sin guion de JD: lo genera cuota-alimentaria-parte-1/montaje/armar.py. "
                 "Cortes en valles de energia sobre tiempos DTW; todo a 1,1x.",
        "progreso": True,
        "clips": clips,
        "musica": {"archivo": "material/musica.wav", "volumen": 0.22,
                   "_nota": "original, la genera cuota-alimentaria-parte-1/audio/musica.py (correr despues de armar.py)"},
        "efectos": efectos,
        "subtitulos": {"activo": True, "estilo": "editorial", "marca": "accion-juridica", "sombra": True,
                        "pos": {"y": 64}, "frases": frases},
        "cine": {"degradado": 0.6, "vinetas": vinetas, "luces": luces,
                 "cierre": {"archivo": "material/cortinilla-aj.mp4", "in_s": 0, "out_s": 5.4, "volumen": 0.8}},
    }

    if p == "p1":
        # Cola: Mauricio sigue en camara lenta bajo un velo, y la pregunta que abre la Parte 2.
        ult = tramos[-1]
        cola_in = ult["out_s"]
        clips.append({"archivo": "material/C20261124_5779.MP4", "in_s": cola_in, "out_s": round(cola_in + 1.6, 2),
                      "velocidad": 0.5, "volumen": 0,
                      "zoom": {"tipo": "in", "hacia": FOCO["79"], "intensidad": 1.12},
                      "_dice": "(cola sin voz, camara lenta)"})
        cola = round(1.6 / 0.5, 2)
        m["velos"] = [{"desde_s": fin_voz, "hasta_s": round(fin_voz + cola, 2), "opacidad": 0.6, "desenfoque": 14,
                       "color": "#131937"}]
        m["textos"] = [
            {"texto": "CUOTA ALIMENTARIA · PARTE 2", "estilo": "antetitulo", "pos": {"x": 50, "y": 38},
             "desde_s": round(fin_voz + 0.25, 2), "hasta_s": round(fin_voz + cola - 0.1, 2)},
            {"texto": "¿Qué le pasa / a quien *no paga?*", "estilo": "editorial", "sombra": True,
             "pos": {"x": 50, "y": 48}, "desde_s": round(fin_voz + 0.45, 2), "hasta_s": round(fin_voz + cola - 0.1, 2)},
        ]
        m["efectos"].append({"archivo": "audio/whoosh-largo.wav", "en_s": round(fin_voz - 0.2, 2), "volumen": 0.4})
        total = fin_voz + cola
    else:
        total = fin_voz
    m["acento"] = "#7FB6E6"
    os.makedirs(os.path.join(RAIZ, carpeta), exist_ok=True)
    json.dump(m, open(os.path.join(RAIZ, carpeta, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{carpeta}: voz {fin_voz:.1f} s, con cola {total:.1f} s, + cortinilla 5,4 = {total + 5.4:.1f} s")


armar("p1", "cuota-alimentaria-parte-1")
armar("p2", "cuota-alimentaria-parte-2")
