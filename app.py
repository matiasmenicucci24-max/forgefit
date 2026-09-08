"""
app.py
Servidor Flask de ForgeFit. Sirve las páginas y expone la API que consume el frontend.

Nota de rendimiento: los endpoints que generan un resultado (calcular, rutinas, dietas,
hábitos) devuelven la respuesta al instante y guardan en Supabase en un hilo aparte
en segundo plano, para que la app se sienta rápida aunque la conexión a internet
o a Supabase tarde un poco. Los endpoints de lectura (historial, medidas, fotos, racha)
siguen siendo síncronos porque necesitan el dato real antes de responder.
"""
import threading

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

import calculos
import rutinas
import dietas
import habitos
import resumen
import database

load_dotenv()  # carga SUPABASE_URL y SUPABASE_KEY desde el archivo .env

app = Flask(__name__)


def _guardar_en_segundo_plano(func, *args, **kwargs):
    """Corre una función de guardado en un hilo aparte, sin bloquear la respuesta."""
    def _run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"[guardado en segundo plano] error en {func.__name__}: {e}")

    threading.Thread(target=_run, daemon=True).start()


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


# ---------- API: Calculadora ----------

@app.route("/api/calcular", methods=["POST"])
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

    try:
        database.get_client()  # chequeo rápido: solo detecta si faltan credenciales
    except RuntimeError as e:
        return jsonify({**entrada, **resultados, "aviso": str(e)})

    _guardar_en_segundo_plano(database.guardar_calculo, entrada, resultados)
    # Guardamos también los datos básicos del perfil (altura/edad/sexo/nivel de actividad)
    # para no tener que volver a pedirlos la próxima vez que entrés.
    _guardar_en_segundo_plano(database.guardar_perfil, {
        "altura": altura, "edad": edad, "sexo": datos["sexo"],
        "nivel_actividad": datos["nivel_actividad"],
    })

    return jsonify({**entrada, **resultados})


# ---------- API: Rutinas ----------

@app.route("/api/rutinas/generar", methods=["POST"])
def api_generar_rutina():
    datos = request.get_json(force=True)

    objetivo = datos.get("objetivo", "mantener")
    nivel = datos.get("nivel", "principiante")
    dias = int(datos.get("dias_por_semana", 3))

    rutina = rutinas.generar_rutina(objetivo, nivel, dias)

    try:
        database.get_client()
    except RuntimeError as e:
        rutina["aviso"] = str(e)
        return jsonify(rutina)

    _guardar_en_segundo_plano(database.guardar_rutina, rutina)
    return jsonify(rutina)


# ---------- API: Dietas ----------

@app.route("/api/dietas/generar", methods=["POST"])
def api_generar_dieta():
    datos = request.get_json(force=True)

    try:
        calorias_objetivo = float(datos.get("calorias_objetivo"))
    except (TypeError, ValueError):
        return jsonify({"error": "Falta o es inválido calorias_objetivo"}), 400

    variacion = int(datos.get("variacion", 0))
    dieta = dietas.generar_dieta(calorias_objetivo, variacion)

    try:
        database.get_client()
    except RuntimeError as e:
        dieta["aviso"] = str(e)
        return jsonify(dieta)

    _guardar_en_segundo_plano(database.guardar_dieta, dieta)
    return jsonify(dieta)


# ---------- API: Historial ----------

@app.route("/api/historial", methods=["GET"])
def api_historial():
    try:
        registros = database.obtener_historial()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(registros)


@app.route("/api/historial/<int:item_id>", methods=["DELETE"])
def api_borrar_historial(item_id):
    try:
        database.borrar_historial_item(item_id)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify({"ok": True})


# ---------- API: Hábitos ----------

@app.route("/api/habitos/catalogo", methods=["GET"])
def api_habitos_catalogo():
    return jsonify(habitos.obtener_catalogo())


@app.route("/api/habitos/seleccion", methods=["POST"])
def api_habitos_seleccion_post():
    datos = request.get_json(force=True)
    seleccion = datos.get("seleccion", [])

    try:
        database.get_client()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    _guardar_en_segundo_plano(database.guardar_seleccion_habitos, seleccion)
    return jsonify({"ok": True, "seleccion": seleccion})


@app.route("/api/habitos/hoy", methods=["GET"])
def api_habitos_hoy():
    """Única lectura síncrona necesaria: trae el estado inicial al cargar la página.
    A partir de acá, el frontend guarda todo en memoria y ya no vuelve a esperar
    una lectura de la base de datos para reaccionar a un click."""
    fecha = habitos.hoy_iso()
    try:
        completados = database.obtener_completados_del_dia(fecha)
        seleccion = database.obtener_seleccion_habitos()
    except RuntimeError as e:
        estado = habitos.armar_estado_dia([], [])
        estado["seleccion"] = habitos.SELECCION_POR_DEFECTO
        estado["aviso"] = str(e)
        return jsonify(estado)

    estado = habitos.armar_estado_dia(completados, seleccion)
    estado["seleccion"] = seleccion if seleccion else habitos.SELECCION_POR_DEFECTO
    return jsonify(estado)


@app.route("/api/habitos/completados", methods=["POST"])
def api_habitos_completados():
    """Recibe la lista completa de hábitos completados hoy (ya calculada en el
    navegador) y la guarda en segundo plano, sin hacer una lectura previa."""
    datos = request.get_json(force=True)
    completados = datos.get("completados", [])
    seleccion = datos.get("seleccion", [])
    fecha = habitos.hoy_iso()

    estado = habitos.armar_estado_dia(completados, seleccion)

    try:
        database.get_client()
    except RuntimeError as e:
        estado["aviso"] = str(e)
        return jsonify(estado)

    _guardar_en_segundo_plano(database.guardar_completados_del_dia, fecha, completados)
    return jsonify(estado)


@app.route("/api/habitos/racha", methods=["GET"])
def api_habitos_racha():
    try:
        historial_habitos = database.obtener_historial_habitos()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(habitos.calcular_racha(historial_habitos))


# ---------- API: Perfil (para no repetir tus datos básicos cada vez) ----------

@app.route("/api/perfil", methods=["GET"])
def api_perfil_get():
    try:
        perfil = database.obtener_perfil()
    except RuntimeError as e:
        return jsonify({"perfil": None, "aviso": str(e)})
    return jsonify({"perfil": perfil})


# ---------- API: Medidas corporales ----------

@app.route("/api/medidas", methods=["POST"])
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
        guardado = database.guardar_medida(fila)
    except RuntimeError as e:
        return jsonify({**fila, "aviso": str(e)})

    return jsonify(guardado)


@app.route("/api/medidas", methods=["GET"])
def api_obtener_medidas():
    try:
        medidas = database.obtener_medidas()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(medidas)


@app.route("/api/medidas/<int:item_id>", methods=["DELETE"])
def api_borrar_medida(item_id):
    try:
        database.borrar_medida(item_id)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify({"ok": True})


# ---------- API: Fotos de progreso ----------

@app.route("/api/fotos", methods=["POST"])
def api_guardar_foto():
    datos = request.get_json(force=True)
    imagen_base64 = datos.get("imagen_base64")
    nota = datos.get("nota", "")

    if not imagen_base64:
        return jsonify({"error": "Falta la imagen"}), 400

    if len(imagen_base64) > 2_800_000:
        return jsonify({"error": "La imagen es muy pesada, probá con una más chica"}), 400

    try:
        guardado = database.guardar_foto(imagen_base64, nota)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify(guardado)


@app.route("/api/fotos", methods=["GET"])
def api_obtener_fotos():
    try:
        fotos = database.obtener_fotos()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify(fotos)


@app.route("/api/fotos/<int:item_id>", methods=["DELETE"])
def api_borrar_foto(item_id):
    try:
        database.borrar_foto(item_id)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200
    return jsonify({"ok": True})


# ---------- API: Resumen semanal ----------

@app.route("/api/resumen-semanal", methods=["GET"])
def api_resumen_semanal():
    try:
        historial = database.obtener_historial(limite=200)
        rutinas_generadas = database.obtener_rutinas(limite=50)
        habitos_dias = database.obtener_historial_habitos(dias=14)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 200

    return jsonify(resumen.calcular_resumen_semanal(historial, rutinas_generadas, habitos_dias))


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
