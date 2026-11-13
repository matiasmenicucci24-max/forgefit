"""
rutinas.py
Generador de rutinas basado en evidencia de ciencia del ejercicio:

- Volumen: 10+ series semanales por grupo muscular para hipertrofia
  (Schoenfeld, Ogborn & Krieger, 2017, Journal of Sports Sciences — metaanálisis
  de dosis-respuesta). Volumen tope orientativo ~20 series/músculo/semana para
  evitar fatiga excesiva sin beneficio adicional.
- Frecuencia: no es un factor determinante para la hipertrofia una vez que el
  volumen semanal está igualado (Schoenfeld, Grgic & Krieger, 2019) — por eso el
  split (full body / upper-lower / push-pull-legs) se elige según los días
  disponibles, no según el objetivo.
- Repeticiones y descanso: siguiendo ACSM (2009; actualizado 2026) y revisiones
  recientes sobre descanso entre series — fuerza: 1-6 reps con descansos de
  2-5 min; hipertrofia: 6-12 reps con descansos de 60-120s (los descansos por
  encima de 60s muestran mejores resultados tanto en fuerza como en hipertrofia
  frente a descansos más cortos).
- Déficit calórico ("bajar peso"): la evidencia (Roth et al. 2023; revisiones
  sobre volumen de entrenamiento y preservación de masa magra durante restricción
  calórica) indica que las recomendaciones de volumen que aplican en mantenimiento
  siguen aplicando en déficit moderado — por eso NO se reduce el volumen de fuerza
  al bajar de peso, solo se suma cardio aparte para aumentar el gasto calórico.
"""
import json
import os

RUTA_EJERCICIOS = os.path.join(os.path.dirname(__file__), "datos", "ejercicios.json")

with open(RUTA_EJERCICIOS, encoding="utf-8") as f:
    EJERCICIOS = json.load(f)

ORDEN_NIVELES = {"principiante": 1, "intermedio": 2, "avanzado": 3}

# Series por ejercicio según nivel (ACSM: novatos 1-3 series, avanzados 3-5).
SERIES_POR_NIVEL = {"principiante": 2, "intermedio": 3, "avanzado": 4}

# Rangos de repeticiones según tipo de ejercicio y nivel — más pesado/bajo en
# reps a medida que sube el nivel para los compuestos (progresión hacia trabajo
# de fuerza), manteniendo el rango de hipertrofia clásico en aislamiento.
REPS_POR_TIPO_Y_NIVEL = {
    "compuesto": {"principiante": "8-12", "intermedio": "6-10", "avanzado": "5-8"},
    "aislamiento": {"principiante": "12-15", "intermedio": "10-12", "avanzado": "8-12"},
    "cardio": {"principiante": "20-25 min", "intermedio": "25-35 min", "avanzado": "15-20 min"},
}

DESCANSO_POR_TIPO = {
    "compuesto": "90-120 seg",
    "aislamiento": "60-90 seg",
    "cardio": "—",
}

# Splits basados en evidencia: a mayor frecuencia semanal disponible, se reparte
# el mismo volumen en sesiones más chicas y específicas (no hay ventaja de
# hipertrofia comprobada por sí sola en más frecuencia, pero permite manejar
# mejor la fatiga por sesión — ACSM recomienda no superar ~8 series por músculo
# por sesión).
SPLITS_POR_DIAS = {
    1: [["pecho", "espalda", "piernas", "hombros", "core"]],
    2: [["piernas", "espalda", "core"], ["pecho", "hombros", "brazos"]],
    3: [
        ["pecho", "espalda", "piernas", "core"],
        ["piernas", "hombros", "brazos", "core"],
        ["pecho", "espalda", "piernas"],
    ],
    4: [
        ["pecho", "hombros", "brazos"],
        ["piernas", "core"],
        ["espalda", "hombros", "brazos"],
        ["piernas", "core"],
    ],
    5: [
        ["pecho", "brazos"],
        ["espalda", "brazos"],
        ["piernas", "core"],
        ["hombros", "brazos"],
        ["piernas", "core"],
    ],
    6: [
        ["pecho", "hombros", "brazos"],
        ["espalda", "brazos"],
        ["piernas", "core"],
        ["pecho", "hombros", "brazos"],
        ["espalda", "brazos"],
        ["piernas", "core"],
    ],
}

DESCRIPCIONES_OBJETIVO = {
    "bajar": (
        "El volumen de fuerza se mantiene igual que en mantenimiento — la evidencia "
        "muestra que bajar el entrenamiento de fuerza durante un déficit calórico no "
        "ayuda a preservar músculo, y de hecho puede perjudicarlo. Se suma cardio "
        "aparte para aumentar el gasto calórico sin sacrificar la fuerza."
    ),
    "mantener": (
        "Volumen e intensidad moderados, distribuidos para dar a cada grupo muscular "
        "el estímulo semanal que la evidencia asocia con buenos resultados sin "
        "acumular fatiga innecesaria."
    ),
    "subir": (
        "Mismo volumen base de fuerza que los otros objetivos, con accesorios extra "
        "de aislamiento para maximizar el estímulo de hipertrofia dentro de rangos "
        "de volumen seguros (no más de ~20 series semanales por músculo)."
    ),
}


def _elegir_ejercicios(grupo: str, nivel: str, cantidad: int) -> list:
    """Filtra ejercicios de un grupo muscular hasta el nivel indicado (incluye niveles más fáciles)."""
    tope = ORDEN_NIVELES.get(nivel, 1)
    candidatos = [
        ej for ej in EJERCICIOS.get(grupo, [])
        if ORDEN_NIVELES.get(ej["nivel"], 1) <= tope
    ]
    if not candidatos:
        candidatos = EJERCICIOS.get(grupo, [])
    return candidatos[:cantidad]


def _armar_ejercicio(ejercicio: dict, grupo: str, nivel: str) -> dict:
    tipo = ejercicio.get("tipo", "aislamiento")
    return {
        **ejercicio,
        "grupo": grupo,
        "series": SERIES_POR_NIVEL[nivel],
        "reps": REPS_POR_TIPO_Y_NIVEL[tipo][nivel],
        "descanso": DESCANSO_POR_TIPO[tipo],
    }


def _calcular_volumen_semanal(plan_dias: list) -> dict:
    """Suma las series semanales totales por grupo muscular, para mostrar
    transparencia sobre si el volumen entra en rango de hipertrofia (10+ series)."""
    volumen = {}
    for dia in plan_dias:
        for ej in dia["ejercicios"]:
            if ej["grupo"] == "cardio":
                continue
            volumen[ej["grupo"]] = volumen.get(ej["grupo"], 0) + ej["series"]
    return volumen


def generar_rutina(objetivo: str, nivel: str, dias_por_semana: int) -> dict:
    dias_por_semana = max(1, min(dias_por_semana, 6))
    esquema = SPLITS_POR_DIAS[dias_por_semana]

    plan_dias = []
    for i, grupos_del_dia in enumerate(esquema):
        ejercicios_del_dia = []
        for grupo in grupos_del_dia:
            cantidad = 3 if (grupo == "piernas" and nivel != "principiante") else 2
            for ej in _elegir_ejercicios(grupo, nivel, cantidad):
                ejercicios_del_dia.append(_armar_ejercicio(ej, grupo, nivel))

        # "Bajar peso": se suma cardio aparte al final del día, sin tocar el
        # volumen de fuerza (ver nota científica en el docstring del módulo).
        if objetivo == "bajar":
            cardio = _elegir_ejercicios("cardio", nivel, 1)
            for ej in cardio:
                ejercicios_del_dia.append(_armar_ejercicio(ej, "cardio", nivel))

        # "Subir": un accesorio de aislamiento extra por día para volumen adicional.
        if objetivo == "subir" and grupos_del_dia:
            grupo_extra = grupos_del_dia[0]
            extra = [
                ej for ej in EJERCICIOS.get(grupo_extra, [])
                if ej.get("tipo") == "aislamiento"
                and ORDEN_NIVELES.get(ej["nivel"], 1) <= ORDEN_NIVELES.get(nivel, 1)
            ]
            ya_incluidos = {e["nombre"] for e in ejercicios_del_dia}
            for ej in extra:
                if ej["nombre"] not in ya_incluidos:
                    ejercicios_del_dia.append(_armar_ejercicio(ej, grupo_extra, nivel))
                    break

        plan_dias.append({
            "dia": i + 1,
            "grupos": grupos_del_dia,
            "ejercicios": ejercicios_del_dia,
        })

    volumen_semanal = _calcular_volumen_semanal(plan_dias)

    return {
        "objetivo": objetivo,
        "nivel": nivel,
        "dias_por_semana": dias_por_semana,
        "descripcion": DESCRIPCIONES_OBJETIVO.get(objetivo, DESCRIPCIONES_OBJETIVO["mantener"]),
        "plan": plan_dias,
        "volumen_semanal": volumen_semanal,
        "fuente": (
            "Estructura de volumen y frecuencia basada en Schoenfeld, Ogborn & Krieger "
            "(2017, Journal of Sports Sciences) y Schoenfeld, Grgic & Krieger (2019); "
            "rangos de repeticiones y descanso según ACSM Position Stand (2009/2026)."
        ),
    }
