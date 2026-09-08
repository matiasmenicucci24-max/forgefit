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


# ---------- Hábitos diarios ----------

def obtener_completados_del_dia(fecha_iso: str) -> list:
    respuesta = (
        get_client()
        .table("habitos_dia")
        .select("completados")
        .eq("fecha", fecha_iso)
        .execute()
    )
    if respuesta.data:
        return respuesta.data[0].get("completados") or []
    return []


def guardar_completados_del_dia(fecha_iso: str, completados_ids: list) -> None:
    get_client().table("habitos_dia").upsert(
        {"fecha": fecha_iso, "completados": completados_ids},
        on_conflict="fecha",
    ).execute()


def obtener_historial_habitos(dias: int = 120) -> list:
    """Devuelve los últimos N días de habitos_dia (para calcular la racha)."""
    respuesta = (
        get_client()
        .table("habitos_dia")
        .select("fecha, completados")
        .order("fecha", desc=True)
        .limit(dias)
        .execute()
    )
    return respuesta.data


def obtener_seleccion_habitos() -> list:
    respuesta = get_client().table("habitos_config").select("seleccionados").eq("id", 1).execute()
    if respuesta.data:
        return respuesta.data[0].get("seleccionados") or []
    return []


def guardar_seleccion_habitos(seleccion_ids: list) -> None:
    get_client().table("habitos_config").upsert(
        {"id": 1, "seleccionados": seleccion_ids},
        on_conflict="id",
    ).execute()


# ---------- Perfil (datos básicos recordados) ----------

def obtener_perfil() -> dict | None:
    respuesta = get_client().table("perfil").select("*").eq("id", 1).execute()
    return respuesta.data[0] if respuesta.data else None


def guardar_perfil(datos: dict) -> None:
    fila = {"id": 1, **datos}
    get_client().table("perfil").upsert(fila, on_conflict="id").execute()


# ---------- Medidas corporales ----------

def guardar_medida(datos: dict) -> dict:
    respuesta = get_client().table("medidas").insert(datos).execute()
    return respuesta.data[0] if respuesta.data else datos


def obtener_medidas(limite: int = 60) -> list:
    respuesta = (
        get_client()
        .table("medidas")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


def borrar_medida(item_id: int) -> None:
    get_client().table("medidas").delete().eq("id", item_id).execute()


# ---------- Fotos de progreso ----------

def guardar_foto(imagen_base64: str, nota: str = "") -> dict:
    fila = {"imagen_base64": imagen_base64, "nota": nota}
    respuesta = get_client().table("fotos_progreso").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_fotos(limite: int = 40) -> list:
    respuesta = (
        get_client()
        .table("fotos_progreso")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


def borrar_foto(item_id: int) -> None:
    get_client().table("fotos_progreso").delete().eq("id", item_id).execute()
