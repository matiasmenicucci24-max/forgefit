"""
compras.py
Genera una lista de compras agrupada por categoría a partir de un plan de dieta
ya generado (el mismo formato que devuelve dietas.generar_dieta).
"""

NOMBRES_CATEGORIA = {
    "verduleria": "Verdulería",
    "carniceria": "Carnicería",
    "pescaderia": "Pescadería",
    "lacteos_huevos": "Lácteos y huevos",
    "almacen": "Almacén",
}

ORDEN_CATEGORIAS = ["verduleria", "carniceria", "pescaderia", "lacteos_huevos", "almacen"]


def generar_items_desde_dieta(dieta: dict) -> list:
    """
    Toma un plan de dieta (con 'comidas': {tipo: {nombre, porcion_g, categoria?}})
    y arma una lista de items únicos con su categoría, para tildar en la compra.
    """
    items_vistos = {}

    for comida in dieta.get("comidas", {}).values():
        nombre = comida.get("nombre")
        categoria = comida.get("categoria", "almacen")
        if not nombre:
            continue
        if nombre not in items_vistos:
            items_vistos[nombre] = categoria

    items = [
        {"item": nombre, "categoria": categoria}
        for nombre, categoria in items_vistos.items()
    ]
    # Orden estable por categoría para que la lista se vea agrupada
    items.sort(key=lambda i: ORDEN_CATEGORIAS.index(i["categoria"]) if i["categoria"] in ORDEN_CATEGORIAS else 99)
    return items


def agrupar_por_categoria(items: list) -> list:
    """Devuelve [{categoria, nombre_categoria, items: [...]}] para renderizar agrupado."""
    grupos = {}
    for item in items:
        cat = item.get("categoria", "almacen")
        grupos.setdefault(cat, []).append(item)

    resultado = []
    for cat in ORDEN_CATEGORIAS:
        if cat in grupos:
            resultado.append({
                "categoria": cat,
                "nombre_categoria": NOMBRES_CATEGORIA.get(cat, cat),
                "items": grupos[cat],
            })
    # Categorías desconocidas al final, por las dudas
    for cat, items_cat in grupos.items():
        if cat not in ORDEN_CATEGORIAS:
            resultado.append({
                "categoria": cat,
                "nombre_categoria": NOMBRES_CATEGORIA.get(cat, cat.capitalize()),
                "items": items_cat,
            })
    return resultado
