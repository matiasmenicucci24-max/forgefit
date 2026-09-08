"""
database.py
Conexión a Supabase y funciones de guardado/lectura para historial, rutinas y dietas.
Requiere las variables de entorno SUPABASE_URL y SUPABASE_KEY (ver .env.example).
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "Faltan las variables de entorno SUPABASE_URL y/o SUPABASE_KEY. "
                "Revisá tu archivo .env (ver .env.example)."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ---------- Historial de cálculos ----------

def guardar_calculo(datos_entrada: dict, resultados: dict) -> dict:
    fila = {**datos_entrada, **resultados}
    respuesta = get_client().table("historial").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_historial(limite: int = 50) -> list:
    respuesta = (
        get_client()
        .table("historial")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


def borrar_historial_item(item_id: int) -> None:
    get_client().table("historial").delete().eq("id", item_id).execute()


# ---------- Rutinas generadas ----------

def guardar_rutina(rutina: dict) -> dict:
    fila = {
        "objetivo": rutina["objetivo"],
        "nivel": rutina["nivel"],
        "dias_por_semana": rutina["dias_por_semana"],
        "plan": rutina,
    }
    respuesta = get_client().table("rutinas_generadas").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_rutinas(limite: int = 20) -> list:
    respuesta = (
        get_client()
        .table("rutinas_generadas")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


# ---------- Dietas generadas ----------

def guardar_dieta(dieta: dict) -> dict:
    fila = {
        "calorias_objetivo": dieta["calorias_objetivo"],
        "proteinas_g": dieta["totales"]["proteina_g"],
        "carbos_g": dieta["totales"]["carbos_g"],
        "grasas_g": dieta["totales"]["grasas_g"],
        "plan": dieta,
    }
    respuesta = get_client().table("dietas_generadas").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_dietas(limite: int = 20) -> list:
    respuesta = (
        get_client()
        .table("dietas_generadas")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data
