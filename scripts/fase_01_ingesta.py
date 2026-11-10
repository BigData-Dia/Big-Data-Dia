"""Descarga el catálogo de DIA y guarda un JSON por categoría principal."""
import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://www.dia.es"
HEADERS = {"Accept": "application/json", "User-Agent": "Proyecto-academico-DIA/1.0"}
ID = re.compile(r"L\d+")
ERRORES = (OSError, ValueError, KeyError, TypeError)
# Categorías cuyos productos ya aparecen en las demás (duplicados).
EXCLUIDAS = {"novedades y recomendados"}


def get_json(url):
    time.sleep(1)  # cortesía con el servidor
    with urlopen(Request(url, headers=HEADERS), timeout=20) as r:
        return json.load(r)


def recoger(l1, nombre, max_paginas):
    """Descarga todas las páginas de una categoría. Devuelve (contenido, bloqueado)."""
    sub = {"id": l1, "name": nombre, "total_items": None}
    salida = {"current_category": l1, "current_subcategory": sub,
              "estado": "incompleta", "error": None, "items": []}
    ids = set()
    try:
        for pagina in range(1, max_paginas + 1):
            url = f"{BASE}/api/v1/plp-back/l1/all/{l1}/reduced?" + urlencode(
                {"category_id": l1, "page": pagina})
            datos = get_json(url)
            actual = datos.get("current_subcategory") or {}
            if datos.get("current_category") != l1 or actual.get("id") != l1:
                raise ValueError("La respuesta corresponde a otra categoría")
            if not isinstance(actual.get("name"), str) or not actual["name"].strip():
                raise ValueError("Falta current_subcategory.name")
            sub["name"] = actual["name"]

            items = datos.get("items")
            if not isinstance(items, list) or not all(isinstance(x, dict) for x in items):
                raise ValueError("items debe ser una lista de objetos")
            salida["items"].extend(items)

            total = actual.get("total_items")
            if type(total) is not int or total < 0:
                raise ValueError("Falta un total de subcategoría válido")
            if sub["total_items"] not in (None, total):
                raise ValueError("El total cambió durante la captura")
            sub["total_items"] = total

            nuevos = [x.get("object_id") for x in items]
            if any(not isinstance(x, (str, int)) or isinstance(x, bool) for x in nuevos):
                raise ValueError("Hay productos sin object_id válido")
            nuevos = [str(x) for x in nuevos]
            if len(set(nuevos)) != len(nuevos) or ids.intersection(nuevos):
                raise ValueError("IDs repetidos (¿página repetida?)")
            ids.update(nuevos)

            if len(ids) == total:
                salida["estado"] = "completa"
                print(f"{sub['name']}: {len(ids)} productos", flush=True)
                return salida, False
            if len(ids) > total or not items:
                raise ValueError("El recuento no coincide con el total declarado")
        raise ValueError("Se alcanzó el límite de páginas sin completar la categoría")
    except ERRORES as e:
        salida["error"] = str(e)
        print(f"Categoría incompleta {l1}: {e}", flush=True)
        return salida, isinstance(e, HTTPError) and e.code in (401, 403, 429)


def nombre_archivo(nombre, l1, usados):
    # Windows prohíbe estos caracteres en los nombres de archivo.
    limpio = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nombre).strip().rstrip(". ") or l1
    if limpio.casefold() in usados:
        limpio += "_" + l1
    usados.add(limpio.casefold())
    return limpio + ".json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-paginas", type=int, default=200)
    parser.add_argument("--limite-categorias", type=int,
                        help="Prueba acotada; deja la captura como parcial")
    args = parser.parse_args()
    if args.max_paginas < 1 or (args.limite_categorias is not None and args.limite_categorias < 1):
        parser.error("Los límites deben ser positivos")

    inicio = datetime.now(timezone.utc)
    carpeta = Path(__file__).resolve().parent / "data/raw" / inicio.strftime("%Y-%m-%d_%H%M%S_%fZ")
    carpeta.mkdir(parents=True)

    try:
        categorias = {c["id"]: c.get("name", c["id"]) for c in
                      get_json(f"{BASE}/api/v1/common-aggregator/menu-data")["categories"]
                      if c.get("name", "").casefold() not in EXCLUIDAS}
        if not categorias or not all(isinstance(i, str) and ID.fullmatch(i) for i in categorias):
            raise ValueError("Menú vacío o con identificadores inesperados")
    except ERRORES as e:
        print(f"Error leyendo el menú: {e}", flush=True)
        return 1

    completas, productos, usados = 0, set(), set()
    for l1, nombre in list(categorias.items())[:args.limite_categorias]:
        salida, bloqueado = recoger(l1, nombre, args.max_paginas)
        salida.update(inicio_utc=inicio.isoformat(), fin_utc=datetime.now(timezone.utc).isoformat(),
                      apariciones_conservadas=len(salida["items"]))
        destino = carpeta / nombre_archivo(salida["current_subcategory"]["name"], l1, usados)
        destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
        completas += salida["estado"] == "completa"
        productos.update(str(p["object_id"]) for p in salida["items"] if "object_id" in p)
        if bloqueado:
            print("Acceso restringido o límite de peticiones; descarga detenida", flush=True)
            break

    ok = completas == len(categorias)
    print(f"Captura {'completa' if ok else 'incompleta'}: {completas}/{len(categorias)} categorías, "
          f"{len(productos)} IDs distintos. Carpeta: {carpeta}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())