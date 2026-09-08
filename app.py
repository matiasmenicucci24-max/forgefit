"""
app.py
Servidor Flask de ForgeFit. Sirve las páginas y expone la API que consume el frontend.
"""
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

import calculos
import rutinas
import dietas
import habitos
import database

load_dotenv()  # carga SUPABASE_URL y SUPABASE_KEY desde el archivo .env

app = Flask(__name__)


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
        guardado = database.guardar_calculo(entrada, resultados)
    except RuntimeError as e:
        # Si Supabase no está configurado todavía, devolvemos el cálculo igual
        return jsonify({**resultados, "aviso": str(e)})

    return jsonify(guardado)


# ---------- API: Rutinas ----------

@app.route("/api/rutinas/generar", methods=["POST"])
def api_generar_rutina():
    datos = request.get_json(force=True)

    objetivo = datos.get("objetivo", "mantener")
    nivel = datos.get("nivel", "principiante")
    dias = int(datos.get("dias_por_semana", 3))

    rutina = rutinas.generar_rutina(objetivo, nivel, dias)

    try:
        database.guardar_rutina(rutina)
    except RuntimeError as e:
        rutina["aviso"] = str(e)

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
        database.guardar_dieta(dieta)
    except RuntimeError as e:
        dieta["aviso"] = str(e)

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


@app.route("/api/habitos/hoy", methods=["GET"])
def api_habitos_hoy():
    fecha = habitos.hoy_iso()
    try:
        completados = database.obtener_completados_del_dia(fecha)
    except RuntimeError as e:
        estado = habitos.armar_estado_dia([])
        estado["aviso"] = str(e)
        return jsonify(estado)

    return jsonify(habitos.armar_estado_dia(completados))


@app.route("/api/habitos/toggle", methods=["POST"])
def api_habitos_toggle():
    datos = request.get_json(force=True)
    habito_id = datos.get("habito_id")
    if not habito_id:
        return jsonify({"error": "Falta habito_id"}), 400

    fecha = habitos.hoy_iso()

    try:
        completados = database.obtener_completados_del_dia(fecha)
        if habito_id in completados:
            completados.remove(habito_id)
        else:
            completados.append(habito_id)
        database.guardar_completados_del_dia(fecha, completados)
    except RuntimeError as e:
        estado = habitos.armar_estado_dia([])
        estado["aviso"] = str(e)
        return jsonify(estado)

    return jsonify(habitos.armar_estado_dia(completados))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
