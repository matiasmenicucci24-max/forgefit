"""
dietas.py
Arma un plan de comidas simple (desayuno/almuerzo/merienda/cena) escalando
las porciones de una base de alimentos para acercarse a las calorías objetivo.
"""
import json
import os

RUTA_ALIMENTOS = os.path.join(os.path.dirname(__file__), "datos", "alimentos.json")

with open(RUTA_ALIMENTOS, encoding="utf-8") as f:
    ALIMENTOS = json.load(f)

# Cómo se reparten las calorías totales entre las comidas del día.
REPARTO_COMIDAS = {
    "desayuno": 0.25,
    "almuerzo": 0.35,
    "merienda": 0.15,
    "cena": 0.25,
}


def _armar_comida(tipo: str, kcal_objetivo_comida: float, indice: int) -> dict:
    """Elige una opción de la lista (rotando) y escala su porción para acercarse a las kcal objetivo."""
    opciones = ALIMENTOS.get(tipo, [])
    if not opciones:
        return None

    opcion = opciones[indice % len(opciones)]
    kcal_base_porcion = opcion["kcal_100g"] * (opcion["porcion_g"] / 100)

    factor_escala = kcal_objetivo_comida / kcal_base_porcion if kcal_base_porcion else 1
    factor_escala = max(0.6, min(factor_escala, 1.8))  # evitar porciones absurdas

    porcion_final_g = round(opcion["porcion_g"] * factor_escala)
    escala = porcion_final_g / 100

    return {
        "nombre": opcion["nombre"],
        "porcion_g": porcion_final_g,
        "kcal": round(opcion["kcal_100g"] * escala),
        "proteina_g": round(opcion["proteina_100g"] * escala, 1),
        "carbos_g": round(opcion["carbos_100g"] * escala, 1),
        "grasas_g": round(opcion["grasas_100g"] * escala, 1),
    }


def generar_dieta(calorias_objetivo: float, dia_variacion: int = 0) -> dict:
    """
    Arma un plan de comidas para un día, repartiendo las calorías objetivo
    entre desayuno/almuerzo/merienda/cena. `dia_variacion` permite generar
    variantes distintas rotando las opciones de alimentos.
    """
    plan = {}
    total_kcal = 0
    total_proteina = 0
    total_carbos = 0
    total_grasas = 0

    for i, (tipo, porcentaje) in enumerate(REPARTO_COMIDAS.items()):
        kcal_objetivo_comida = calorias_objetivo * porcentaje
        comida = _armar_comida(tipo, kcal_objetivo_comida, dia_variacion + i)
        if comida:
            plan[tipo] = comida
            total_kcal += comida["kcal"]
            total_proteina += comida["proteina_g"]
            total_carbos += comida["carbos_g"]
            total_grasas += comida["grasas_g"]

    return {
        "calorias_objetivo": calorias_objetivo,
        "comidas": plan,
        "totales": {
            "kcal": round(total_kcal),
            "proteina_g": round(total_proteina, 1),
            "carbos_g": round(total_carbos, 1),
            "grasas_g": round(total_grasas, 1),
        },
    }
