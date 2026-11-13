"""
asistente.py
Chat "Preguntale a ForgeFit": responde dudas de fitness/nutrición usando la API
de Groq (modelos Llama). Requiere la variable de entorno GROQ_API_KEY.

No usa ninguna librería externa: Groq expone una API compatible con OpenAI, así
que alcanza con un POST a /chat/completions con urllib.
"""
import json
import os
import urllib.error
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Se puede cambiar el modelo sin tocar el código: variable GROQ_MODEL en el .env.
MODELO_POR_DEFECTO = "llama-3.3-70b-versatile"
TIMEOUT_SEGUNDOS = 25

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


def _armar_mensajes(pregunta: str, historial_chat: list) -> list:
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turno in (historial_chat or [])[-10:]:  # limitamos contexto a los últimos 10 turnos
        rol = "user" if turno.get("rol") == "usuario" else "assistant"
        contenido = turno.get("texto", "")
        if contenido:
            mensajes.append({"role": rol, "content": contenido})
    mensajes.append({"role": "user", "content": pregunta})
    return mensajes


def _mensaje_de_error_http(codigo: int, cuerpo: str) -> str:
    if codigo in (401, 403):
        return ("Groq rechazó la clave (GROQ_API_KEY). Revisá que esté bien copiada, "
                "sin espacios, y que siga activa en console.groq.com.")
    if codigo == 429:
        return "Se alcanzó el límite de uso de Groq. Esperá un minuto y probá de nuevo."
    if codigo == 404 or (codigo == 400 and "model" in cuerpo.lower()):
        return ("Groq no encontró el modelo configurado. Probá con otro en la variable "
                "GROQ_MODEL (ver los disponibles en console.groq.com/docs/models).")
    return f"Groq respondió con un error ({codigo}). Probá de nuevo en un rato."


def responder(pregunta: str, historial_chat: list) -> dict:
    api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not api_key:
        return {
            "error": (
                "Falta configurar GROQ_API_KEY para usar el asistente. "
                "Podés conseguir una clave gratis en console.groq.com."
            )
        }

    cuerpo = json.dumps({
        "model": (os.environ.get("GROQ_MODEL") or MODELO_POR_DEFECTO).strip(),
        "messages": _armar_mensajes(pregunta, historial_chat),
        "temperature": 0.4,
        "max_tokens": 500,
    }).encode("utf-8")

    req = urllib.request.Request(
        GROQ_URL,
        data=cuerpo,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # Groq está detrás de Cloudflare, que puede bloquear el User-Agent
            # por defecto de urllib: mandamos uno propio.
            "User-Agent": "ForgeFit/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
            datos = json.loads(resp.read().decode("utf-8"))
        texto = (datos["choices"][0]["message"]["content"] or "").strip()
        if not texto:
            return {"error": "El asistente devolvió una respuesta vacía. Probá reformular la pregunta."}
        return {"respuesta": texto}
    except urllib.error.HTTPError as e:
        try:
            detalle = e.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            detalle = ""
        return {"error": _mensaje_de_error_http(e.code, detalle)}
    except (urllib.error.URLError, TimeoutError):
        return {"error": "No se pudo conectar con Groq. Revisá tu conexión y probá de nuevo."}
    except (KeyError, IndexError, ValueError):
        return {"error": "Groq devolvió una respuesta inesperada. Probá de nuevo."}
    except Exception as e:  # noqa: BLE001
        return {"error": f"No se pudo consultar al asistente: {e}"}
