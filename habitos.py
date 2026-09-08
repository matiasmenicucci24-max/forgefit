"""
habitos.py
Lógica de la lista de hábitos y el cálculo de progreso diario.
"""
import json
import os
from datetime import date

RUTA_HABITOS = os.path.join(os.path.dirname(__file__), "datos", "habitos.json")

with open(RUTA_HABITOS, encoding="utf-8") as f:
    HABITOS = json.load(f)


def obtener_lista_habitos() -> list:
    return HABITOS


def hoy_iso() -> str:
    return date.today().isoformat()


def armar_estado_dia(completados_ids: list) -> dict:
    """Combina la lista fija de hábitos con cuáles están completados hoy."""
    completados_set = set(completados_ids or [])

    habitos_con_estado = [
        {**h, "completado": h["id"] in completados_set}
        for h in HABITOS
    ]

    total = len(HABITOS)
    hechos = len(completados_set)
    porcentaje = round((hechos / total) * 100) if total else 0

    return {
        "fecha": hoy_iso(),
        "habitos": habitos_con_estado,
        "completados": hechos,
        "total": total,
        "porcentaje": porcentaje,
    }
