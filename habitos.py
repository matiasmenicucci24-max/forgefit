"""
habitos.py
Catálogo de hábitos, selección personalizada del usuario, progreso diario,
cálculo de racha (streak) y logros desbloqueados.
"""
import json
import os
from datetime import date, timedelta

RUTA_HABITOS = os.path.join(os.path.dirname(__file__), "datos", "habitos.json")

with open(RUTA_HABITOS, encoding="utf-8") as f:
    CATALOGO_HABITOS = json.load(f)

# Si el usuario todavía no eligió hábitos propios, arrancamos con estos por defecto.
SELECCION_POR_DEFECTO = ["agua", "entrenar", "dormir", "meditar", "leer", "verduras"]

# Hitos de racha que desbloquean una medalla.
LOGROS = [
    {"dias": 3, "nombre": "Primeros pasos", "descripcion": "3 días seguidos cumpliendo hábitos"},
    {"dias": 7, "nombre": "Una semana fuerte", "descripcion": "7 días seguidos"},
    {"dias": 14, "nombre": "Quincena de hierro", "descripcion": "14 días seguidos"},
    {"dias": 30, "nombre": "Hábito forjado", "descripcion": "30 días seguidos"},
    {"dias": 60, "nombre": "Imparable", "descripcion": "60 días seguidos"},
    {"dias": 100, "nombre": "Leyenda ForgeFit", "descripcion": "100 días seguidos"},
]


def hoy_iso() -> str:
    return date.today().isoformat()


def obtener_catalogo() -> list:
    return CATALOGO_HABITOS


def armar_estado_dia(completados_ids: list, seleccion_ids: list) -> dict:
    """Combina la selección personal del usuario con lo completado hoy."""
    seleccion = seleccion_ids if seleccion_ids else SELECCION_POR_DEFECTO
    completados_set = set(completados_ids or [])

    habitos_del_dia = [
        {**h, "completado": h["id"] in completados_set}
        for h in CATALOGO_HABITOS
        if h["id"] in seleccion
    ]

    total = len(habitos_del_dia)
    hechos = sum(1 for h in habitos_del_dia if h["completado"])
    porcentaje = round((hechos / total) * 100) if total else 0

    return {
        "fecha": hoy_iso(),
        "habitos": habitos_del_dia,
        "completados": hechos,
        "total": total,
        "porcentaje": porcentaje,
    }


def calcular_racha(historial_dias: list) -> dict:
    """
    historial_dias: lista de dicts {"fecha": "YYYY-MM-DD", "completados": [...]}
    Cuenta días consecutivos (terminando hoy o ayer) con al menos 1 hábito cumplido.
    """
    dias_con_progreso = {
        d["fecha"] for d in historial_dias if d.get("completados")
    }

    racha = 0
    cursor = date.today()

    # Si hoy todavía no marcaste nada, la racha se cuenta desde ayer hacia atrás
    # (no la corta solo por no haber marcado nada todavía en el día de hoy).
    if cursor.isoformat() not in dias_con_progreso:
        cursor -= timedelta(days=1)

    while cursor.isoformat() in dias_con_progreso:
        racha += 1
        cursor -= timedelta(days=1)

    logros_desbloqueados = [l for l in LOGROS if racha >= l["dias"]]
    proximo_logro = next((l for l in LOGROS if racha < l["dias"]), None)

    return {
        "racha": racha,
        "logros_desbloqueados": logros_desbloqueados,
        "proximo_logro": proximo_logro,
        "todos_los_logros": LOGROS,
    }
