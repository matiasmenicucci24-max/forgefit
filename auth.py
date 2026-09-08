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

    return {
        "ok": True,
        "requiere_confirmacion": False,
        "access_token": respuesta.session.access_token,
        "refresh_token": respuesta.session.refresh_token,
        "user_id": respuesta.user.id,
        "email": respuesta.user.email,
    }


def iniciar_sesion(email: str, password: str) -> dict:
    """Inicia sesión. Devuelve tokens si es exitoso, o un error legible."""
    try:
        client = _client_anonimo()
        respuesta = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        return {"ok": False, "error": _traducir_error(str(e))}

    return {
        "ok": True,
        "access_token": respuesta.session.access_token,
        "refresh_token": respuesta.session.refresh_token,
        "user_id": respuesta.user.id,
        "email": respuesta.user.email,
    }


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
    return f"No se pudo completar la operación: {mensaje}"
