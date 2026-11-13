"""
entrenamiento.py
Lógica del registro real de entrenamientos: detección de récords personales (PR),
progresión de fuerza por ejercicio, volumen semanal real por grupo muscular
(comparado contra el volumen recomendado por la evidencia) y calendario de días
entrenados.

Fórmula de 1RM estimado: Epley (1RM = peso × (1 + reps/30)), una de las fórmulas
más usadas y validadas para estimar la fuerza máxima a partir de series
submáximas, sin necesidad de probar un levantamiento al fallo real.
"""
from datetime import date, datetime, timedelta

VOLUMEN_IDEAL_MIN = 10  # series semanales por músculo para hipertrofia (Schoenfeld et al. 2017)
VOLUMEN_IDEAL_MAX = 20  # techo orientativo antes de fatiga excesiva


def estimar_1rm(peso: float, reps: int) -> float:
    """Fórmula de Epley. reps=1 devuelve el propio peso levantado."""
    if reps <= 1:
        return round(peso, 1)
    return round(peso * (1 + reps / 30), 1)


def calcular_es_pr(peso_nuevo: float, reps_nuevo: int, series_previas: list) -> bool:
    """Compara el 1RM estimado de la serie nueva contra el mejor 1RM histórico
    del mismo ejercicio. Si no hay series previas, la primera serie no cuenta
    como PR (no hay nada contra qué compararla)."""
    if not series_previas:
        return False
    estimado_nuevo = estimar_1rm(peso_nuevo, reps_nuevo)
    mejor_previo = max(estimar_1rm(s["peso"], s["reps"]) for s in series_previas)
    return estimado_nuevo > mejor_previo


def _inicio_semana_iso(fecha_str: str) -> str:
    """Devuelve el lunes de la semana ISO de una fecha, como string YYYY-MM-DD."""
    f = datetime.fromisoformat(fecha_str.replace("Z", "+00:00")).date()
    lunes = f - timedelta(days=f.weekday())
    return lunes.isoformat()


def calcular_volumen_semanal_real(series: list) -> list:
    """
    Agrupa las series registradas por semana y grupo muscular, contando series
    únicas (no sets duplicados de la misma serie) por semana.
    Devuelve una lista ordenada por semana descendente, cada una con el detalle
    por grupo muscular y una bandera de si llegó al mínimo recomendado.
    """
    semanas = {}
    for s in series:
        semana = _inicio_semana_iso(s["fecha"])
        grupo = s["grupo"]
        semanas.setdefault(semana, {})
        semanas[semana][grupo] = semanas[semana].get(grupo, 0) + 1

    resultado = []
    for semana in sorted(semanas.keys(), reverse=True):
        grupos = semanas[semana]
        detalle = [
            {
                "grupo": grupo,
                "series": cantidad,
                "en_rango_ideal": cantidad >= VOLUMEN_IDEAL_MIN,
            }
            for grupo, cantidad in sorted(grupos.items())
        ]
        resultado.append({"semana_inicio": semana, "grupos": detalle})
    return resultado


def calcular_progresion_ejercicio(series: list) -> list:
    """
    Para un ejercicio puntual: devuelve la mejor marca (1RM estimado) por día
    entrenado, ordenado cronológicamente — ideal para graficar la evolución.
    """
    mejores_por_dia = {}
    for s in series:
        dia = s["fecha"][:10]
        estimado = estimar_1rm(s["peso"], s["reps"])
        if dia not in mejores_por_dia or estimado > mejores_por_dia[dia]:
            mejores_por_dia[dia] = estimado

    return [
        {"fecha": dia, "estimado_1rm": valor}
        for dia, valor in sorted(mejores_por_dia.items())
    ]


def calcular_calendario_entrenado(series: list) -> list:
    """Lista única de fechas (YYYY-MM-DD) en las que se registró al menos una serie."""
    dias = {s["fecha"][:10] for s in series}
    return sorted(dias)


def listar_ejercicios_entrenados(series: list) -> list:
    """Nombres únicos de ejercicios ya registrados, para el selector de progresión."""
    return sorted({s["ejercicio"] for s in series})
