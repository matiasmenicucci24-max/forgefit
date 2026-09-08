"""
rutinas.py
Arma rutinas de entrenamiento base según objetivo, y permite personalizarlas
según nivel y días disponibles por semana.
"""
import json
import os

RUTA_EJERCICIOS = os.path.join(os.path.dirname(__file__), "datos", "ejercicios.json")

with open(RUTA_EJERCICIOS, encoding="utf-8") as f:
    EJERCICIOS = json.load(f)

# Plantillas base: qué grupos musculares tocar cada día, según objetivo.
PLANTILLAS_BASE = {
    "bajar": {
        "descripcion": "Enfoque en gasto calórico: circuitos de cuerpo completo + cardio.",
        "esquema_dias": [
            ["piernas", "core", "cardio"],
            ["pecho", "espalda", "cardio"],
            ["hombros", "brazos", "cardio"],
        ],
    },
    "mantener": {
        "descripcion": "Rutina equilibrada de cuerpo completo para sostener tu condición actual.",
        "esquema_dias": [
            ["pecho", "espalda"],
            ["piernas", "core"],
            ["hombros", "brazos"],
        ],
    },
    "subir": {
        "descripcion": "Enfoque en fuerza e hipertrofia: más volumen por grupo muscular, menos cardio.",
        "esquema_dias": [
            ["pecho", "brazos"],
            ["espalda", "core"],
            ["piernas"],
            ["hombros", "brazos"],
        ],
    },
}


def _elegir_ejercicios(grupo: str, nivel: str, cantidad: int = 2) -> list:
    """Filtra ejercicios de un grupo muscular hasta el nivel indicado (incluye niveles más fáciles)."""
    orden_niveles = {"principiante": 1, "intermedio": 2, "avanzado": 3}
    tope = orden_niveles.get(nivel, 1)

    candidatos = [
        ej for ej in EJERCICIOS.get(grupo, [])
        if orden_niveles.get(ej["nivel"], 1) <= tope
    ]
    if not candidatos:
        candidatos = EJERCICIOS.get(grupo, [])

    return candidatos[:cantidad]


def generar_rutina(objetivo: str, nivel: str, dias_por_semana: int) -> dict:
    """
    Arma una rutina de `dias_por_semana` días, repitiendo/recortando el esquema base
    de la plantilla del objetivo elegido, y personalizando la dificultad según el nivel.
    """
    plantilla = PLANTILLAS_BASE.get(objetivo, PLANTILLAS_BASE["mantener"])
    esquema = plantilla["esquema_dias"]

    dias_por_semana = max(1, min(dias_por_semana, 6))

    plan_dias = []
    for i in range(dias_por_semana):
        grupos_del_dia = esquema[i % len(esquema)]
        ejercicios_del_dia = []
        for grupo in grupos_del_dia:
            cantidad = 1 if grupo == "cardio" else 2
            for ej in _elegir_ejercicios(grupo, nivel, cantidad):
                ejercicios_del_dia.append({**ej, "grupo": grupo})

        plan_dias.append({
            "dia": i + 1,
            "grupos": grupos_del_dia,
            "ejercicios": ejercicios_del_dia,
        })

    return {
        "objetivo": objetivo,
        "nivel": nivel,
        "dias_por_semana": dias_por_semana,
        "descripcion": plantilla["descripcion"],
        "plan": plan_dias,
    }
