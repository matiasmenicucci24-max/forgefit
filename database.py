"""
database.py
Conexión a Supabase y funciones de guardado/lectura.

Multiusuario: cada función recibe un `token` (el access_token de sesión del
usuario logueado). Ese token se adjunta a cada pedido a Supabase para que
Postgres sepa quién es auth.uid() y las políticas de Row Level Security
filtren automáticamente los datos de cada usuario — nadie puede ver ni tocar
los datos de otra persona, ni aunque conozca la URL o la anon key.
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_client(token: str | None = None) -> Client:
    """Crea un cliente nuevo por pedido (no se cachea: cada usuario tiene su
    propio token, así que cachear un cliente global mezclaría sesiones)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Faltan las variables de entorno SUPABASE_URL y/o SUPABASE_KEY. "
            "Revisá tu archivo .env (ver .env.example)."
        )
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if token:
        client.postgrest.auth(token)
    return client


# ---------- Historial de cálculos ----------

def guardar_calculo(token: str, datos_entrada: dict, resultados: dict) -> dict:
    fila = {**datos_entrada, **resultados}
    respuesta = get_client(token).table("historial").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_historial(token: str, limite: int = 50) -> list:
    respuesta = (
        get_client(token)
        .table("historial")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


def borrar_historial_item(token: str, item_id: int) -> None:
    get_client(token).table("historial").delete().eq("id", item_id).execute()


# ---------- Rutinas generadas ----------

def guardar_rutina(token: str, rutina: dict) -> dict:
    fila = {
        "objetivo": rutina["objetivo"],
        "nivel": rutina["nivel"],
        "dias_por_semana": rutina["dias_por_semana"],
        "plan": rutina,
    }
    respuesta = get_client(token).table("rutinas_generadas").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_rutinas(token: str, limite: int = 20) -> list:
    respuesta = (
        get_client(token)
        .table("rutinas_generadas")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


# ---------- Dietas generadas ----------

def guardar_dieta(token: str, dieta: dict) -> dict:
    fila = {
        "calorias_objetivo": dieta["calorias_objetivo"],
        "proteinas_g": dieta["totales"]["proteina_g"],
        "carbos_g": dieta["totales"]["carbos_g"],
        "grasas_g": dieta["totales"]["grasas_g"],
        "plan": dieta,
    }
    respuesta = get_client(token).table("dietas_generadas").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_dietas(token: str, limite: int = 20) -> list:
    respuesta = (
        get_client(token)
        .table("dietas_generadas")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


# ---------- Hábitos diarios ----------

def obtener_completados_del_dia(token: str, fecha_iso: str) -> list:
    respuesta = (
        get_client(token)
        .table("habitos_dia")
        .select("completados")
        .eq("fecha", fecha_iso)
        .execute()
    )
    if respuesta.data:
        return respuesta.data[0].get("completados") or []
    return []


def guardar_completados_del_dia(token: str, fecha_iso: str, completados_ids: list) -> None:
    get_client(token).table("habitos_dia").upsert(
        {"fecha": fecha_iso, "completados": completados_ids},
        on_conflict="user_id,fecha",
    ).execute()


def obtener_historial_habitos(token: str, dias: int = 120) -> list:
    respuesta = (
        get_client(token)
        .table("habitos_dia")
        .select("fecha, completados")
        .order("fecha", desc=True)
        .limit(dias)
        .execute()
    )
    return respuesta.data


def obtener_seleccion_habitos(token: str) -> list:
    respuesta = get_client(token).table("habitos_config").select("seleccionados").execute()
    if respuesta.data:
        return respuesta.data[0].get("seleccionados") or []
    return []


def guardar_seleccion_habitos(token: str, seleccion_ids: list) -> None:
    get_client(token).table("habitos_config").upsert(
        {"seleccionados": seleccion_ids},
        on_conflict="user_id",
    ).execute()


# ---------- Perfil (datos básicos recordados) ----------

def obtener_perfil(token: str) -> dict | None:
    respuesta = get_client(token).table("perfil").select("*").execute()
    return respuesta.data[0] if respuesta.data else None


def guardar_perfil(token: str, datos: dict) -> None:
    get_client(token).table("perfil").upsert(datos, on_conflict="user_id").execute()


# ---------- Medidas corporales ----------

def guardar_medida(token: str, datos: dict) -> dict:
    respuesta = get_client(token).table("medidas").insert(datos).execute()
    return respuesta.data[0] if respuesta.data else datos


def obtener_medidas(token: str, limite: int = 60) -> list:
    respuesta = (
        get_client(token)
        .table("medidas")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


def borrar_medida(token: str, item_id: int) -> None:
    get_client(token).table("medidas").delete().eq("id", item_id).execute()


# ---------- Fotos de progreso ----------

def guardar_foto(token: str, imagen_base64: str, nota: str = "") -> dict:
    fila = {"imagen_base64": imagen_base64, "nota": nota}
    respuesta = get_client(token).table("fotos_progreso").insert(fila).execute()
    return respuesta.data[0] if respuesta.data else fila


def obtener_fotos(token: str, limite: int = 40) -> list:
    respuesta = (
        get_client(token)
        .table("fotos_progreso")
        .select("*")
        .order("fecha", desc=True)
        .limit(limite)
        .execute()
    )
    return respuesta.data


def borrar_foto(token: str, item_id: int) -> None:
    get_client(token).table("fotos_progreso").delete().eq("id", item_id).execute()
