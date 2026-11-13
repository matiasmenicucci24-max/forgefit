"""
auth.py
Registro, login y logout usando Supabase Auth (email + contraseña).
Supabase se encarga de guardar y hashear las contraseñas de forma segura;
esta app nunca ve ni guarda una contraseña en texto plano.
"""
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def _client_anonimo():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            "Faltan las variables de entorno SUPABASE_URL y/o SUPABASE_KEY. "
            "Revisá tu archivo .env (ver .env.example)."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _datos_sesion(respuesta, requiere_confirmacion: bool = False) -> dict:
    return {
        "ok": True,
        "requiere_confirmacion": requiere_confirmacion,
        "access_token": respuesta.session.access_token,
        "refresh_token": respuesta.session.refresh_token,
        "expires_in": respuesta.session.expires_in,
        "user_id": respuesta.user.id,
        "email": respuesta.user.email,
    }


def registrarse(email: str, password: str) -> dict:
    """Crea una cuenta nueva. Devuelve {'ok': True} o {'ok': False, 'error': str}."""
    try:
        client = _client_anonimo()
        respuesta = client.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        return {"ok": False, "error": _traducir_error(str(e))}

    if respuesta.session is None:
        # Supabase puede requerir confirmación de email según la configuración del proyecto.
        return {"ok": True, "requiere_confirmacion": True}

    return _datos_sesion(respuesta, requiere_confirmacion=False)


def iniciar_sesion(email: str, password: str) -> dict:
    """Inicia sesión. Devuelve tokens si es exitoso, o un error legible."""
    try:
        client = _client_anonimo()
        respuesta = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        return {"ok": False, "error": _traducir_error(str(e))}

    return _datos_sesion(respuesta)


def refrescar_sesion(refresh_token: str) -> dict:
    """Pide un access_token nuevo usando el refresh_token, sin pedir contraseña de nuevo.
    Se usa automáticamente cuando el token de sesión está por vencer (antes.py)."""
    if not refresh_token:
        return {"ok": False, "error": "No hay refresh_token disponible."}
    try:
        client = _client_anonimo()
        respuesta = client.auth.refresh_session(refresh_token)
    except Exception as e:
        return {"ok": False, "error": _traducir_error(str(e))}

    return _datos_sesion(respuesta)


def _traducir_error(mensaje: str) -> str:
    mensaje_lower = mensaje.lower()
    if "invalid login credentials" in mensaje_lower:
        return "Email o contraseña incorrectos."
    if "user already registered" in mensaje_lower:
        return "Ya existe una cuenta con ese email. Iniciá sesión en vez de registrarte."
    if "password should be at least" in mensaje_lower:
        return "La contraseña debe tener al menos 6 caracteres."
    if "unable to validate email" in mensaje_lower or "invalid email" in mensaje_lower:
        return "El email no es válido."
    if "refresh_token_not_found" in mensaje_lower or "invalid refresh token" in mensaje_lower:
        return "Tu sesión venció. Iniciá sesión de nuevo."
    return f"No se pudo completar la operación: {mensaje}"
