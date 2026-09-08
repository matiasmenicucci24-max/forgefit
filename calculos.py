"""
calculos.py
Lógica pura de cálculo: IMC, TMB, calorías diarias, macros y agua.
Sin dependencias de Flask ni de la base de datos: funciones testeables por separado.
"""

FACTORES_ACTIVIDAD = {
    "sedentario": 1.2,        # poco o nada de ejercicio
    "ligero": 1.375,          # ejercicio ligero 1-3 días/semana
    "moderado": 1.55,         # ejercicio moderado 3-5 días/semana
    "activo": 1.725,          # ejercicio intenso 6-7 días/semana
    "muy_activo": 1.9,        # ejercicio muy intenso o trabajo físico
}

AJUSTE_OBJETIVO = {
    "bajar": -500,      # déficit ~0.5 kg/semana
    "mantener": 0,
    "subir": 350,       # superávit moderado para ganar masa sin acumular mucha grasa
}


def calcular_imc(peso_kg: float, altura_cm: float) -> dict:
    altura_m = altura_cm / 100
    imc = peso_kg / (altura_m ** 2)

    if imc < 18.5:
        categoria = "Bajo peso"
    elif imc < 25:
        categoria = "Normal"
    elif imc < 30:
        categoria = "Sobrepeso"
    else:
        categoria = "Obesidad"

    return {"imc": round(imc, 1), "categoria": categoria}


def calcular_tmb(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    """Fórmula de Mifflin-St Jeor."""
    base = 10 * peso_kg + 6.25 * altura_cm - 5 * edad
    if sexo == "masculino":
        tmb = base + 5
    else:
        tmb = base - 161
    return round(tmb, 0)


def calcular_calorias_objetivo(tmb: float, nivel_actividad: str, objetivo: str) -> float:
    factor = FACTORES_ACTIVIDAD.get(nivel_actividad, 1.2)
    gasto_total = tmb * factor
    ajuste = AJUSTE_OBJETIVO.get(objetivo, 0)
    return round(gasto_total + ajuste, 0)


def calcular_macros(calorias: float, objetivo: str, peso_kg: float) -> dict:
    """
    Reparto de macros según objetivo, con proteína anclada al peso corporal
    (más precisa que un simple % fijo) y el resto repartido entre carbos y grasas.
    """
    if objetivo == "bajar":
        g_proteina_por_kg = 2.0   # proteína alta para preservar masa muscular en déficit
        pct_grasa = 0.30
    elif objetivo == "subir":
        g_proteina_por_kg = 1.8
        pct_grasa = 0.25
    else:
        g_proteina_por_kg = 1.6
        pct_grasa = 0.28

    proteinas_g = round(peso_kg * g_proteina_por_kg, 0)
    calorias_proteina = proteinas_g * 4

    calorias_grasa = calorias * pct_grasa
    grasas_g = round(calorias_grasa / 9, 0)

    calorias_restantes = calorias - calorias_proteina - calorias_grasa
    carbos_g = round(max(calorias_restantes, 0) / 4, 0)

    return {
        "proteinas_g": proteinas_g,
        "carbos_g": carbos_g,
        "grasas_g": grasas_g,
    }


def calcular_agua(peso_kg: float, nivel_actividad: str) -> float:
    base_litros = peso_kg * 0.035
    if nivel_actividad in ("activo", "muy_activo"):
        base_litros += 0.5
    return round(base_litros, 1)


def calcular_todo(peso_kg, altura_cm, edad, sexo, nivel_actividad, objetivo) -> dict:
    """Corre todos los cálculos juntos y devuelve un dict listo para guardar/responder."""
    imc_info = calcular_imc(peso_kg, altura_cm)
    tmb = calcular_tmb(peso_kg, altura_cm, edad, sexo)
    calorias = calcular_calorias_objetivo(tmb, nivel_actividad, objetivo)
    macros = calcular_macros(calorias, objetivo, peso_kg)
    agua = calcular_agua(peso_kg, nivel_actividad)

    return {
        "imc": imc_info["imc"],
        "categoria_imc": imc_info["categoria"],
        "tmb": tmb,
        "calorias_objetivo": calorias,
        "proteinas_g": macros["proteinas_g"],
        "carbos_g": macros["carbos_g"],
        "grasas_g": macros["grasas_g"],
        "agua_litros": agua,
    }
