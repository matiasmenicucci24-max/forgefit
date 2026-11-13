"""
Genera los GIFs de los ejercicios de ForgeFit.

Para cada ejercicio de datos/ejercicios.json baja las 2 fotos (posición inicial
y final) del catálogo público free-exercise-db (licencia Unlicense / dominio
público) y las junta en un GIF animado que se guarda en public/static/gifs/.
También escribe public/static/gifs/index.json (nombre del ejercicio → GIF).

Los GIFs ya vienen generados en el proyecto: este script solo hace falta si
agregás ejercicios nuevos a datos/ejercicios.json. Para correrlo:

    pip install pillow
    python scripts/generar_gifs.py

Para un ejercicio nuevo, agregá su nombre en inglés exacto (como figura en
https://github.com/yuhonas/free-exercise-db) en CATALOGO más abajo.
"""

import io
import json
import os
import re
import sys
import unicodedata
import urllib.request

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_EJERCICIOS = os.path.join(RAIZ, "datos", "ejercicios.json")
CARPETA_SALIDA = os.path.join(RAIZ, "public", "static", "gifs")
URL_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main"

ANCHO = 420            # px; suficiente para el modal y liviano
MS_POR_CUADRO = 750    # velocidad de la animación

# Nombre del ejercicio en ForgeFit → nombre exacto en free-exercise-db
CATALOGO = {
    # Pecho
    "Flexiones de brazos": "Pushups",
    "Press de banca con mancuernas": "Dumbbell Bench Press",
    "Press de banca con barra": "Barbell Bench Press - Medium Grip",
    "Press inclinado con mancuernas": "Incline Dumbbell Press",
    "Aperturas con mancuernas": "Dumbbell Flyes",
    "Cruce de poleas (aperturas)": "Cable Crossover",
    # Espalda
    "Remo con mancuerna": "One-Arm Dumbbell Row",
    "Jalón al pecho (polea)": "Wide-Grip Lat Pulldown",
    "Dominadas asistidas": "Band Assisted Pull-Up",
    "Remo con barra": "Bent Over Barbell Row",
    "Peso muerto": "Barbell Deadlift",
    "Pull-over con mancuerna": "Bent-Arm Dumbbell Pullover",
    # Piernas
    "Sentadilla con peso corporal": "Bodyweight Squat",
    "Prensa de piernas": "Leg Press",
    "Sentadilla con barra": "Barbell Squat",
    "Peso muerto rumano": "Romanian Deadlift",
    "Zancadas con mancuernas": "Dumbbell Lunges",
    "Sentadilla búlgara": "Split Squat with Dumbbells",
    "Extensión de cuádriceps (máquina)": "Leg Extensions",
    "Curl femoral (máquina)": "Lying Leg Curls",
    "Elevación de talones (gemelos)": "Standing Calf Raises",
    # Hombros
    "Press militar con mancuernas": "Dumbbell Shoulder Press",
    "Press militar con barra": "Barbell Shoulder Press",
    "Elevaciones laterales": "Side Lateral Raise",
    "Elevaciones posteriores (deltoides posterior)": "Reverse Flyes",
    "Press Arnold": "Arnold Dumbbell Press",
    # Brazos
    "Curl de bíceps con mancuernas": "Dumbbell Bicep Curl",
    "Curl martillo": "Hammer Curls",
    "Extensión de tríceps en polea": "Triceps Pushdown",
    "Press francés con mancuerna": "Lying Triceps Press",
    "Fondos en banco (tríceps)": "Bench Dips",
    "Press cerrado con barra": "Close-Grip Barbell Bench Press",
    # Core
    "Plancha abdominal": "Plank",
    "Crunch abdominal": "Crunches",
    "Elevación de piernas colgado": "Hanging Leg Raise",
    "Russian twist": "Russian Twist",
    "Rueda abdominal (ab wheel)": "Ab Roller",
    # Cardio
    "Caminata rápida o cinta inclinada": "Walking, Treadmill",
    "Bicicleta o elíptica": "Bicycling, Stationary",
    "HIIT (intervalos de alta intensidad)": "Mountain Climbers",
}


def slug(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def bajar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ForgeFit-gif-builder"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def armar_gif(cuadros: list, destino: str) -> None:
    imgs = []
    for datos in cuadros:
        im = Image.open(io.BytesIO(datos)).convert("RGB")
        alto = round(im.height * ANCHO / im.width)
        imgs.append(im.resize((ANCHO, alto), Image.LANCZOS))
    # Mismo tamaño en todos los cuadros (por si alguna foto viene distinta).
    base = imgs[0].size
    imgs = [im if im.size == base else im.resize(base, Image.LANCZOS) for im in imgs]
    # Una sola paleta para todos los cuadros evita parpadeos de color.
    mosaico = Image.new("RGB", (base[0], base[1] * len(imgs)))
    for i, im in enumerate(imgs):
        mosaico.paste(im, (0, i * base[1]))
    paleta = mosaico.quantize(colors=128, method=Image.MEDIANCUT)
    cuadros_p = [im.quantize(palette=paleta, dither=Image.NONE) for im in imgs]
    cuadros_p[0].save(
        destino, save_all=True, append_images=cuadros_p[1:],
        duration=MS_POR_CUADRO, loop=0, optimize=True, disposal=1,
    )


def main() -> int:
    with open(RUTA_EJERCICIOS, encoding="utf-8") as f:
        ejercicios = [e["nombre"] for lista in json.load(f).values() for e in lista]

    faltan_en_catalogo = [n for n in ejercicios if n not in CATALOGO]
    if faltan_en_catalogo:
        print("Ejercicios sin equivalente en CATALOGO:", *faltan_en_catalogo, sep="\n  - ")
        return 1

    print("Bajando el catálogo free-exercise-db…")
    catalogo = {e["name"]: e for e in json.loads(bajar(f"{URL_BASE}/dist/exercises.json"))}

    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    indice, errores = {}, []
    for nombre in ejercicios:
        en = CATALOGO[nombre]
        try:
            entrada = catalogo[en]
            fotos = [bajar(f"{URL_BASE}/exercises/{ruta}") for ruta in entrada["images"][:2]]
            if len(fotos) < 2:
                raise ValueError("el catálogo trae menos de 2 fotos")
            archivo = f"{slug(nombre)}.gif"
            armar_gif(fotos, os.path.join(CARPETA_SALIDA, archivo))
            indice[nombre] = f"/static/gifs/{archivo}"
            print(f"  OK   {nombre}  ←  {en}")
        except Exception as e:  # noqa: BLE001
            errores.append((nombre, e))
            print(f"  FALLÓ {nombre}: {e}")

    with open(os.path.join(CARPETA_SALIDA, "index.json"), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"\n{len(indice)}/{len(ejercicios)} GIFs generados en {CARPETA_SALIDA}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
