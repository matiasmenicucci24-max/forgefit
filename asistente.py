"""
asistente.py
Chat "Preguntale a ForgeFit": responde dudas de fitness/nutrición usando la API
de Claude (Anthropic). Requiere la variable de entorno ANTHROPIC_API_KEY.
"""
import os
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """Sos el asistente de ForgeFit, una app de fitness. Respondés dudas sobre
entrenamiento, nutrición y hábitos saludables de forma breve, clara y en español rioplatense,
con un tono cercano pero directo.

Reglas importantes:
- Basate en evidencia científica de entrenamiento de fuerza y nutrición deportiva (volumen,
  frecuencia, rangos de repeticiones, superávit/déficit calórico, proteína, etc.).
- Nunca reemplazás a un médico, nutricionista o entrenador certificado. Si la pregunta es sobre
  una lesión, dolor persistente, una condición médica, o algo que requiere evaluación individual,
  decilo claramente y sugerí consultar a un profesional en persona.
- No des dosis ni recomendaciones sobre suplementos con riesgo (esteroides, quemadores de grasa
  no regulados, etc.) más allá de información general y de seguridad.
- Respuestas cortas: 2 a 5 oraciones, salvo que la pregunta pida explícitamente más detalle.
- No inventes datos ni cites estudios que no conocés con certeza; si no estás seguro, decilo.
"""


def responder(pregunta: str, historial_chat: list) -> dict:
    if not ANTHROPIC_API_KEY:
        return {
            "error": (
                "Falta configurar ANTHROPIC_API_KEY en tu archivo .env para usar el asistente. "
                "Podés conseguir una clave en console.anthropic.com."
            )
        }

    mensajes = []
    for turno in historial_chat[-10:]:  # limitamos contexto a los últimos 10 turnos
        rol = "user" if turno.get("rol") == "usuario" else "assistant"
        contenido = turno.get("texto", "")
        if contenido:
            mensajes.append({"role": rol, "content": contenido})
    mensajes.append({"role": "user", "content": pregunta})

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        respuesta = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=mensajes,
        )
        texto = "".join(bloque.text for bloque in respuesta.content if bloque.type == "text")
        return {"respuesta": texto}
    except Exception as e:
        return {"error": f"No se pudo consultar al asistente: {e}"}
