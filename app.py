"""
app.py
Servidor Flask de ForgeFit. Sirve las páginas y expone la API que consume el frontend.

Multiusuario: cada persona tiene su cuenta (Supabase Auth). El token de sesión
se guarda en la cookie de sesión de Flask y se manda a cada función de
database.py, que lo usa para que Supabase aplique Row Level Security y cada
usuario solo pueda ver y modificar sus propios datos.

Nota de rendimiento: los endpoints que generan un resultado (calcular, rutinas,
dietas, hábitos) devuelven la respuesta al instante y guardan en Supabase en un
hilo aparte en segundo plano, para que la app se sienta rápida.
"""
import os
import threading
import time
import functools

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from dotenv import load_dotenv

import calculos
import rutinas
import dietas
import habitos
import resumen
import database
import auth
import asistente
import entrenamiento
import compras

load_dotenv()

# Los archivos estáticos viven en public/static: Vercel sirve todo lo que está
# en public/ directo desde su CDN, y en local Flask los sirve desde la misma
# carpeta, así que funciona igual en los dos lados.
app = Flask(__name__, static_folder="public/static", static_url_path="/static")
EN_VERCEL = bool(os.environ.get("VERCEL"))
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambiar-esta-clave-en-produccion")

RUTAS_PUBLICAS = {"login", "signup", "static", "service_worker"}
MARGEN_REFRESH_SEGUNDOS = 60  # renovamos el token 1 minuto antes de que venza


def manejar_errores_api(func):
    """Envuelve un endpoint /api/ para que NUNCA devuelva la página de error HTML
    de Flask: cualquier excepción (token vencido, error de red con Supabase, etc.)
    se convierte en un JSON prolijo. Sin esto, el frontend intenta hacer
    resp.json() sobre una página HTML de error y la sección queda en blanco
    sin ningún aviso — esta fue la causa de fondo de varios de los bugs reportados."""
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 200
        except Exception as e:
            print(f"[error en /api endpoint '{func.__name__}']: {e}")
            return jsonify({"error": "Hubo un problema al procesar el pedido. Probá de nuevo en un momento."}), 200
    return envoltura


@app.before_request
def requerir_sesion():
    """Protege todas las rutas menos login/signup/static y la API de esas páginas.
    Además, si el access_token está por vencer, lo renueva solo usando el
    refresh_token — antes esto no pasaba y, pasada ~1 hora de sesión, todos los
    pedidos a Supabase empezaban a fallar en silencio."""
    endpoint = request.endpoint or ""
    if endpoint in RUTAS_PUBLICAS or endpoint.startswith("static"):
        return None
    if endpoint in ("api_login", "api_signup"):
        return None
    if "access_token" not in session:
        if request.path.startswith("/api/"):
            return jsonify({"error": "Sesión expirada, iniciá sesión de nuevo."}), 401
        return redirect(url_for("login"))

    expira_en = session.get("expires_at", 0)
    if expira_en and time.time() > expira_en - MARGEN_REFRESH_SEGUNDOS:
        resultado = auth.refrescar_sesion(session.get("refresh_token", ""))
        if resultado.get("ok"):
            session["access_token"] = resultado["access_token"]
            session["refresh_token"] = resultado["refresh_token"]
            session["expires_at"] = time.time() + resultado.get("expires_in", 3600)
        else:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "Tu sesión venció. Iniciá sesión de nuevo."}), 401
            return redirect(url_for("login"))
    return None


def token_actual() -> str:
    return session.get("access_token", "")


def _guardar_en_segundo_plano(func, *args, **kwargs):
    """Corre una función de guardado en un hilo aparte, sin bloquear la respuesta.

    En Vercel (serverless) la función se congela apenas se envía la respuesta,
    así que un hilo en segundo plano puede quedar a medias y perder el guardado.
    Por eso ahí se guarda en el momento, antes de responder."""
    def _run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"[guardado en segundo plano] error en {func.__name__}: {e}")

    if EN_VERCEL:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


# ---------- Autenticación ----------

@app.route("/login")
def login():
    if "access_token" in session:
        return redirect(url_for("home"))
    return render_template("login.html")


@app.route("/signup")
def signup():
    if "access_token" in session:
        return redirect(url_for("home"))
    return render_template("signup.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    datos = request.get_json(force=True)
    email = (datos.get("email") or "").strip()
    password = datos.get("password") or ""

    if not email or not password:
        return jsonify({"ok": False, "error": "Completá email y contraseña."}), 400

    resultado = auth.iniciar_sesion(email, password)
    if not resultado.get("ok"):
        return jsonify(resultado), 200

    session["access_token"] = resultado["access_token"]
    session["refresh_token"] = resultado["refresh_token"]
    session["expires_at"] = time.time() + resultado.get("expires_in", 3600)
    session["user_id"] = resultado["user_id"]
    session["email"] = resultado["email"]
    return jsonify({"ok": True})


@app.route("/api/signup", methods=["POST"])
def api_signup():
    datos = request.get_json(force=True)
    email = (datos.get("email") or "").strip()
    password = datos.get("password") or ""

    if not email or not password:
        return jsonify({"ok": False, "error": "Completá email y contraseña."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "La contraseña debe tener al menos 6 caracteres."}), 400

    resultado = auth.registrarse(email, password)
    if not resultado.get("ok"):
        return jsonify(resultado), 200

    if resultado.get("requiere_confirmacion"):
        return jsonify({
            "ok": True,
            "requiere_confirmacion": True,
            "mensaje": "Te enviamos un email para confirmar tu cuenta. Confirmalo y después iniciá sesión."
        })

    session["access_token"] = resultado["access_token"]
    session["refresh_token"] = resultado["refresh_token"]
    session["expires_at"] = time.time() + resultado.get("expires_in", 3600)
    session["user_id"] = resultado["user_id"]
    session["email"] = resultado["email"]
    return jsonify({"ok": True, "requiere_confirmacion": False})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/sw.js")
def service_worker():
    """Se sirve desde la raíz (no desde /static/) para que el scope del
    service worker cubra toda la app, no solo la carpeta static.
    En Vercel este archivo (public/sw.js) lo entrega directamente la CDN."""
    return send_from_directory(
        os.path.join(app.root_path, "public"), "sw.js", mimetype="application/javascript"
    )


# ---------- Páginas ----------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/rutinas")
def pagina_rutinas():
    return render_template("rutinas.html")


@app.route("/dietas")
def pagina_dietas():
    return render_template("dietas.html")


@app.route("/historial")
def pagina_historial():
    return render_template("historial.html")


@app.route("/habitos")
def pagina_habitos():
    return render_template("habitos.html")


@app.route("/progreso")
def pagina_progreso():
    return render_template("progreso.html")


@app.route("/entrenar")
def pagina_entrenar():
    return render_template("entrenar.html")


@app.route("/compras")
def pagina_compras():
    return render_template("compras.html")


# ---------- API: Calculadora ----------

@app.route("/api/calcular", methods=["POST"])
@manejar_errores_api
def api_calcular():
    datos = request.get_json(force=True)

    campos_requeridos = ["peso", "altura", "edad", "sexo", "nivel_actividad", "objetivo"]
    faltantes = [c for c in campos_requeridos if c not in datos or datos[c] in ("", None)]
    if faltantes:
        return jsonify({"error": f"Faltan campos: {', '.join(faltantes)}"}), 400

    try:
        peso = float(datos["peso"])
        altura = float(datos["altura"])
        edad = int(datos["edad"])
    except (ValueError, TypeError):
        return jsonify({"error": "Peso, altura y edad deben ser números válidos."}), 400

    if peso <= 0 or altura <= 0 or edad <= 0:
        return jsonify({"error": "Peso, altura y edad deben ser mayores a cero."}), 400

    resultados = calculos.calcular_todo(
        peso, altura, edad, datos["sexo"], datos["nivel_actividad"], datos["objetivo"]
    )

    entrada = {
        "peso": peso,
        "altura": altura,
        "edad": edad,
        "sexo": datos["sexo"],
        "nivel_actividad": datos["nivel_actividad"],
        "objetivo": datos["objetivo"],
    }

    token = token_actual()
    try:
        database.get_client(token)
    except RuntimeError as e:
        return jsonify({**entrada, **resultados, "aviso": str(e)})

    _guardar_en_segundo_plano(database.guardar_calculo, token, entrada, resultados)
    _guardar_en_segundo_plano(database.guardar_perfil, token, {
        "altura": altura, "edad": edad, "sexo": datos["sexo"],
        "nivel_actividad": datos["nivel_actividad"],
    })

    return jsonify({**entrada, **resultados})


# ---------- API: Rutinas ----------

@app.route("/api/rutinas/generar", methods=["POST"])
@manejar_errores_api
def api_generar_rutina():
    datos = request.get_json(force=True)

    objetivo = datos.get("objetivo", "mantener")
    nivel = datos.get("nivel", "principiante")
    dias = int(datos.get("dias_por_semana", 3))

    rutina = rutinas.generar_rutina(objetivo, nivel, dias)

    token = token_actual()
    try:
        database.get_client(token)
    except RuntimeError as e:
        rutina["aviso"] = str(e)
        return jsonify(rutina)

    # A diferencia de otros guardados, este se hace sincrónico (no en un hilo
    # en segundo plano): necesitamos el id que devuelve Supabase al instante,
    # para que el botón "Guardar como mi rutina activa" sepa qué rutina activar.
    guardado = database.guardar_rutina(token, rutina)
    rutina["id"] = guardado.get("id")
    rutina["activa"] = False
    return jsonify(rutina)


# ---------- API: Dietas ----------

@app.route("/api/dietas/generar", methods=["POST"])
@manejar_errores_api
def api_generar_dieta():
    datos = request.get_json(force=True)

    try:
        calorias_objetivo = float(datos.get("calorias_objetivo"))
    except (TypeError, ValueError):
        return jsonify({"error": "Falta o es inválido calorias_objetivo"}), 400

    variacion = int(datos.get("variacion", 0))
    dieta = dietas.generar_dieta(calorias_objetivo, variacion)

    token = token_actual()
    try:
        database.get_client(token)
    except RuntimeError as e:
        dieta["aviso"] = str(e)
        return jsonify(dieta)

    _guardar_en_segundo_plano(database.guardar_dieta, token, dieta)
    return jsonify(dieta)


# ---------- API: Historial ----------

@app.route("/api/historial", methods=["GET"])
@manejar_errores_api
def api_historial():
    try:
        registros = database.obtener_historial(token_actual())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(registros)


@app.route("/api/historial/<int:item_id>", methods=["DELETE"])
@manejar_errores_api
def api_borrar_historial(item_id):
    try:
        database.borrar_historial_item(token_actual(), item_id)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify({"ok": True})


# ---------- API: Hábitos ----------

@app.route("/api/habitos/catalogo", methods=["GET"])
@manejar_errores_api
def api_habitos_catalogo():
    return jsonify(habitos.obtener_catalogo())


@app.route("/api/habitos/seleccion", methods=["POST"])
@manejar_errores_api
def api_habitos_seleccion_post():
    datos = request.get_json(force=True)
    seleccion = datos.get("seleccion", [])
    token = token_actual()

    try:
        database.get_client(token)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    _guardar_en_segundo_plano(database.guardar_seleccion_habitos, token, seleccion)
    return jsonify({"ok": True, "seleccion": seleccion})


@app.route("/api/habitos/hoy", methods=["GET"])
@manejar_errores_api
def api_habitos_hoy():
    fecha = habitos.hoy_iso()
    token = token_actual()
    try:
        completados = database.obtener_completados_del_dia(token, fecha)
        seleccion = database.obtener_seleccion_habitos(token)
    except RuntimeError as e:
        estado = habitos.armar_estado_dia([], [])
        estado["seleccion"] = habitos.SELECCION_POR_DEFECTO
        estado["aviso"] = str(e)
        return jsonify(estado)

    estado = habitos.armar_estado_dia(completados, seleccion)
    estado["seleccion"] = seleccion if seleccion else habitos.SELECCION_POR_DEFECTO
    return jsonify(estado)


@app.route("/api/habitos/completados", methods=["POST"])
@manejar_errores_api
def api_habitos_completados():
    datos = request.get_json(force=True)
    completados = datos.get("completados", [])
    seleccion = datos.get("seleccion", [])
    fecha = habitos.hoy_iso()
    token = token_actual()

    estado = habitos.armar_estado_dia(completados, seleccion)

    try:
        database.get_client(token)
    except RuntimeError as e:
        estado["aviso"] = str(e)
        return jsonify(estado)

    _guardar_en_segundo_plano(database.guardar_completados_del_dia, token, fecha, completados)
    return jsonify(estado)


@app.route("/api/habitos/racha", methods=["GET"])
@manejar_errores_api
def api_habitos_racha():
    try:
        historial_habitos = database.obtener_historial_habitos(token_actual())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(habitos.calcular_racha(historial_habitos))


# ---------- API: Perfil ----------

@app.route("/api/perfil", methods=["GET"])
@manejar_errores_api
def api_perfil_get():
    try:
        perfil = database.obtener_perfil(token_actual())
    except RuntimeError as e:
        return jsonify({"perfil": None, "aviso": str(e)})
    return jsonify({"perfil": perfil})


# ---------- API: Medidas corporales ----------

@app.route("/api/medidas", methods=["POST"])
@manejar_errores_api
def api_guardar_medida():
    datos = request.get_json(force=True)

    campos_numericos = ["peso", "cintura", "cadera", "pecho", "brazo", "pierna"]
    fila = {}
    for campo in campos_numericos:
        valor = datos.get(campo)
        if valor not in (None, ""):
            try:
                fila[campo] = float(valor)
            except (ValueError, TypeError):
                return jsonify({"error": f"El campo {campo} debe ser un número"}), 400

    if not fila:
        return jsonify({"error": "Cargá al menos una medida"}), 400

    try:
        guardado = database.guardar_medida(token_actual(), fila)
    except RuntimeError as e:
        return jsonify({**fila, "aviso": str(e)})

    return jsonify(guardado)


@app.route("/api/medidas", methods=["GET"])
@manejar_errores_api
def api_obtener_medidas():
    try:
        medidas = database.obtener_medidas(token_actual())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(medidas)


@app.route("/api/medidas/<int:item_id>", methods=["DELETE"])
@manejar_errores_api
def api_borrar_medida(item_id):
    try:
        database.borrar_medida(token_actual(), item_id)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify({"ok": True})


# ---------- API: Fotos de progreso ----------

@app.route("/api/fotos", methods=["POST"])
@manejar_errores_api
def api_guardar_foto():
    datos = request.get_json(force=True)
    imagen_base64 = datos.get("imagen_base64")
    nota = datos.get("nota", "")

    if not imagen_base64:
        return jsonify({"error": "Falta la imagen"}), 400
    if len(imagen_base64) > 2_800_000:
        return jsonify({"error": "La imagen es muy pesada, probá con una más chica"}), 400

    try:
        guardado = database.guardar_foto(token_actual(), imagen_base64, nota)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify(guardado)


@app.route("/api/fotos", methods=["GET"])
@manejar_errores_api
def api_obtener_fotos():
    try:
        fotos = database.obtener_fotos(token_actual())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(fotos)


@app.route("/api/fotos/<int:item_id>", methods=["DELETE"])
@manejar_errores_api
def api_borrar_foto(item_id):
    try:
        database.borrar_foto(token_actual(), item_id)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify({"ok": True})


# ---------- API: Resumen semanal ----------

@app.route("/api/resumen-semanal", methods=["GET"])
@manejar_errores_api
def api_resumen_semanal():
    token = token_actual()
    try:
        historial = database.obtener_historial(token, limite=200)
        rutinas_generadas = database.obtener_rutinas(token, limite=50)
        habitos_dias = database.obtener_historial_habitos(token, dias=14)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify(resumen.calcular_resumen_semanal(historial, rutinas_generadas, habitos_dias))


# ---------- API: Registro de entrenamientos ----------

@app.route("/api/rutinas/ultima", methods=["GET"])
@manejar_errores_api
def api_rutina_ultima():
    """Devuelve la última rutina generada, para saber qué ejercicios registrar hoy."""
    try:
        rutinas_guardadas = database.obtener_rutinas(token_actual(), limite=1)
    except RuntimeError as e:
        return jsonify({"rutina": None, "aviso": str(e)})

    if not rutinas_guardadas:
        return jsonify({"rutina": None})

    return jsonify({"rutina": rutinas_guardadas[0].get("plan")})


@app.route("/api/rutinas/activa", methods=["GET"])
@manejar_errores_api
def api_rutina_activa():
    """Devuelve la rutina que el usuario marcó como 'activa' — la que usan
    Entrenar y el resto de la app como referencia, sin tener que regenerarla
    cada vez que cambia de sección."""
    fila = database.obtener_rutina_activa(token_actual())
    if not fila:
        return jsonify({"rutina": None})

    plan = fila.get("plan") or {}
    plan["id"] = fila.get("id")
    plan["activa"] = fila.get("activa", False)
    return jsonify({"rutina": plan})


@app.route("/api/rutinas/activar", methods=["POST"])
@manejar_errores_api
def api_activar_rutina():
    """Marca una rutina generada (por su id) como la rutina activa del usuario."""
    datos = request.get_json(force=True)
    rutina_id = datos.get("id")
    if not rutina_id:
        return jsonify({"error": "Falta el id de la rutina a activar"}), 400

    database.marcar_rutina_activa(token_actual(), rutina_id)
    return jsonify({"ok": True})


@app.route("/api/dietas/ultima", methods=["GET"])
@manejar_errores_api
def api_dieta_ultima():
    """Devuelve la última dieta generada, para armar la lista de compras."""
    try:
        dietas_guardadas = database.obtener_dietas(token_actual(), limite=1)
    except RuntimeError as e:
        return jsonify({"dieta": None, "aviso": str(e)})

    if not dietas_guardadas:
        return jsonify({"dieta": None})

    return jsonify({"dieta": dietas_guardadas[0].get("plan")})


@app.route("/api/entrenamiento/registrar-serie", methods=["POST"])
@manejar_errores_api
def api_registrar_serie():
    datos = request.get_json(force=True)

    campos_requeridos = ["ejercicio", "grupo", "serie_numero", "peso", "reps"]
    faltantes = [c for c in campos_requeridos if datos.get(c) in (None, "")]
    if faltantes:
        return jsonify({"error": f"Faltan campos: {', '.join(faltantes)}"}), 400

    try:
        peso = float(datos["peso"])
        reps = int(datos["reps"])
        serie_numero = int(datos["serie_numero"])
    except (ValueError, TypeError):
        return jsonify({"error": "Peso, reps y número de serie deben ser numéricos."}), 400

    if peso <= 0 or reps <= 0:
        return jsonify({"error": "Peso y repeticiones deben ser mayores a cero."}), 400

    token = token_actual()
    try:
        series_previas = database.obtener_series_ejercicio(token, datos["ejercicio"])
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    es_pr = entrenamiento.calcular_es_pr(peso, reps, series_previas)

    fila = {
        "ejercicio": datos["ejercicio"],
        "grupo": datos["grupo"],
        "serie_numero": serie_numero,
        "peso": peso,
        "reps": reps,
        "es_pr": es_pr,
    }

    try:
        guardado = database.guardar_serie(token, fila)
    except RuntimeError as e:
        return jsonify({**fila, "aviso": str(e)})

    return jsonify(guardado)


@app.route("/api/entrenamiento/progresion", methods=["GET"])
@manejar_errores_api
def api_progresion_ejercicio():
    ejercicio = request.args.get("ejercicio", "")
    if not ejercicio:
        return jsonify({"error": "Falta el parámetro ejercicio"}), 400

    try:
        series = database.obtener_series_ejercicio(token_actual(), ejercicio)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify(entrenamiento.calcular_progresion_ejercicio(series))


@app.route("/api/entrenamiento/ejercicios", methods=["GET"])
@manejar_errores_api
def api_ejercicios_registrados():
    try:
        ejercicios = database.obtener_ejercicios_registrados(token_actual())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(ejercicios)


@app.route("/api/entrenamiento/analytics", methods=["GET"])
@manejar_errores_api
def api_analytics_entrenamiento():
    token = token_actual()
    try:
        series = database.obtener_todas_las_series(token, dias=90)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify({
        "volumen_semanal": entrenamiento.calcular_volumen_semanal_real(series),
        "calendario": entrenamiento.calcular_calendario_entrenado(series),
        "total_series_registradas": len(series),
        "volumen_ideal_min": entrenamiento.VOLUMEN_IDEAL_MIN,
        "volumen_ideal_max": entrenamiento.VOLUMEN_IDEAL_MAX,
    })


# ---------- API: Lista de compras ----------

@app.route("/api/compras/generar", methods=["POST"])
@manejar_errores_api
def api_generar_lista_compras():
    datos = request.get_json(force=True)
    dieta = datos.get("dieta")

    if not dieta or "comidas" not in dieta:
        return jsonify({"error": "Falta el plan de dieta para generar la lista"}), 400

    items = compras.generar_items_desde_dieta(dieta)
    token = token_actual()

    try:
        database.reemplazar_lista_compras(token, items)
        guardados = database.obtener_lista_compras(token)
    except RuntimeError as e:
        agrupado = compras.agrupar_por_categoria([{**i, "comprado": False} for i in items])
        return jsonify({"grupos": agrupado, "aviso": str(e)})

    agrupado = compras.agrupar_por_categoria(guardados)
    return jsonify({"grupos": agrupado})


@app.route("/api/compras", methods=["GET"])
@manejar_errores_api
def api_obtener_compras():
    try:
        items = database.obtener_lista_compras(token_actual())
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify({"grupos": compras.agrupar_por_categoria(items)})


@app.route("/api/compras/toggle", methods=["POST"])
@manejar_errores_api
def api_toggle_compra():
    datos = request.get_json(force=True)
    item = datos.get("item")
    comprado = bool(datos.get("comprado"))

    if not item:
        return jsonify({"error": "Falta el item"}), 400

    try:
        database.marcar_item_comprado(token_actual(), item, comprado)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify({"ok": True})


# ---------- API: Asistente ForgeFit (IA) ----------

@app.route("/api/asistente", methods=["POST"])
@manejar_errores_api
def api_asistente():
    datos = request.get_json(force=True)
    pregunta = (datos.get("pregunta") or "").strip()
    historial_chat = datos.get("historial", [])

    if not pregunta:
        return jsonify({"error": "Escribí una pregunta"}), 400

    respuesta = asistente.responder(pregunta, historial_chat)
    return jsonify(respuesta)


if __name__ == "__main__":
    # host="0.0.0.0" permite conectarse desde otros dispositivos de tu misma red
    # (por ejemplo, tu celular) usando la IP local de esta compu en vez de localhost.
    app.run(host="0.0.0.0", debug=True, port=5000, threaded=True)
