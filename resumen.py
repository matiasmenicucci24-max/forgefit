"""
resumen.py
Calcula el resumen semanal a partir de los datos ya guardados
(historial de cálculos, rutinas generadas y hábitos diarios de los últimos 7 días).
No usa un cron: se recalcula cada vez que el usuario entra a la página.
"""
from datetime import date, timedelta


def _dentro_de_los_ultimos_7_dias(fecha_iso: str, hoy: date) -> bool:
    try:
        fecha = date.fromisoformat(fecha_iso[:10])
    except (ValueError, TypeError):
        return False
    return 0 <= (hoy - fecha).days <= 6


def calcular_resumen_semanal(historial: list, rutinas_generadas: list, habitos_dias: list) -> dict:
    hoy = date.today()

    historial_semana = [h for h in historial if _dentro_de_los_ultimos_7_dias(h.get("fecha", ""), hoy)]
    rutinas_semana = [r for r in rutinas_generadas if _dentro_de_los_ultimos_7_dias(r.get("fecha", ""), hoy)]
    habitos_semana = [h for h in habitos_dias if _dentro_de_los_ultimos_7_dias(h.get("fecha", ""), hoy)]

    # Cambio de peso: comparamos el registro más viejo vs el más nuevo de la semana
    cambio_peso = None
    if len(historial_semana) >= 2:
        ordenados = sorted(historial_semana, key=lambda h: h["fecha"])
        cambio_peso = round(ordenados[-1]["peso"] - ordenados[0]["peso"], 1)

    # Promedio de cumplimiento de hábitos en la semana
    porcentajes = []
    for dia in habitos_semana:
        completados = dia.get("completados") or []
        # No sabemos cuántos hábitos tenía seleccionados ese día históricamente,
        # así que usamos la cantidad de completados como proxy simple de actividad.
        porcentajes.append(len(completados))

    promedio_habitos_dia = round(sum(porcentajes) / len(porcentajes), 1) if porcentajes else 0
    dias_con_algun_habito = sum(1 for p in porcentajes if p > 0)

    return {
        "rango": f"{(hoy - timedelta(days=6)).strftime('%d/%m')} — {hoy.strftime('%d/%m')}",
        "rutinas_generadas": len(rutinas_semana),
        "calculos_registrados": len(historial_semana),
        "cambio_peso": cambio_peso,
        "dias_con_habitos": dias_con_algun_habito,
        "promedio_habitos_por_dia": promedio_habitos_dia,
    }
