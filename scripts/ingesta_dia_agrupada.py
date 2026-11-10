"""Descarga DIA y reúne los productos por categorías en un solo JSON.

Las peticiones se reúnen en memoria. Solo se guardan JSON por categoría.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "https://www.dia.es"
MENU = "/api/v1/common-aggregator/menu-data"
RAIZ = Path(__file__).resolve().parent
ID = re.compile(r"L\d+")


def descargar(ruta, nombre, carpeta, registro):
    url = BASE + ruta
    intento = {"url": url, "archivo": nombre}
    registro.append(intento)
    try:
        time.sleep(1)
        with urlopen(Request(url, headers={"Accept": "application/json",
                                          "User-Agent": "Proyecto-academico-DIA/1.0"}),
                     timeout=20) as respuesta:
            cuerpo = respuesta.read()
            intento.update(http=respuesta.status, url_final=respuesta.url,
                           bytes=len(cuerpo))
        datos = json.loads(cuerpo)
        intento["json_valido"] = True
        return datos
    except Exception as error:
        if isinstance(error, HTTPError):
            intento["http"] = error.code
        intento["error"] = str(error)
        print(f"Error en {nombre}: {error}", flush=True)
        raise


def listas_de_objetos(valor, ruta=()):
    """Enumera las listas candidatas sin asumir nombres de la API."""
    if isinstance(valor, dict):
        for clave, hijo in valor.items():
            yield from listas_de_objetos(hijo, (*ruta, clave))
    elif isinstance(valor, list) and all(isinstance(x, dict) for x in valor):
        yield ".".join(ruta) or "$", len(valor), list(valor[0]) if valor else []


def leer_lista(datos, ruta):
    for clave in ruta.split(".") if ruta != "$" else []:
        datos = datos[clave]
    if not isinstance(datos, list) or not all(isinstance(x, dict) for x in datos):
        raise ValueError(f"{ruta} debe identificar una lista de objetos")
    return datos


def categorias_del_menu(menu):
    """Selecciona una consulta por categoría principal, usando su propio ID."""
    pares = {}
    for principal in menu["categories"]:
        identificador = principal["id"]
        if not isinstance(identificador, str) or not ID.fullmatch(identificador):
            raise ValueError(f"Identificador inesperado: {identificador}")
        pares[(identificador, identificador)] = principal.get("name", identificador)
    if not pares:
        raise ValueError("El menú no contiene categorías")
    return pares


def recoger_categoria(l1, sub, nombre, carpeta, meta, max_paginas):
    resumen = {"l1": l1, "categoria": sub, "nombre": nombre,
               "paginas": 0, "apariciones": 0, "ids_unicos": 0,
               "estado": "incompleta"}
    meta["categorias"].append(resumen)
    grupo = {**resumen, "productos": []}
    meta["_catalogo"].append(grupo)
    ids = set()
    firmas = set()
    esperado = None
    for pagina in range(1, max_paginas + 1):
        ruta = f"/api/v1/plp-back/l1/all/{l1}/reduced?" + urlencode(
            {"category_id": sub, "page": pagina})
        datos = descargar(ruta, f"productos_{l1}_{sub}_p{pagina:03}.json",
                          carpeta, meta["descargas"])
        if datos.get("current_category") != l1:
            raise ValueError("La respuesta corresponde a otra categoría principal")
        actual = datos.get("current_subcategory", {})
        if actual.get("id") != sub:
            raise ValueError("La respuesta corresponde a otra subcategoría")
        nombre_fuente = actual.get("name")
        if not isinstance(nombre_fuente, str) or not nombre_fuente.strip():
            raise ValueError("Falta current_subcategory.name")
        grupo["nombre_fuente"] = nombre_fuente
        productos = leer_lista(datos, "items")
        grupo["productos"].extend(productos)
        total = actual.get("total_items")
        if type(total) is not int or total < 0:
            raise ValueError("Falta un total de subcategoría válido")
        if esperado is None:
            esperado = total
            resumen["total_declarado"] = total
        elif esperado != total:
            raise ValueError("El total de la subcategoría cambió durante la captura")
        nuevos = [producto.get("object_id") for producto in productos]
        if any(not isinstance(x, (str, int)) or isinstance(x, bool) for x in nuevos):
            raise ValueError("Hay productos sin object_id válido")
        nuevos = [str(x) for x in nuevos]
        firma = tuple(sorted(nuevos))
        if productos and firma in firmas:
            raise ValueError("Página repetida")
        firmas.add(firma)
        if len(set(nuevos)) != len(nuevos) or ids.intersection(nuevos):
            raise ValueError("IDs repetidos dentro del listado de la subcategoría")
        ids.update(nuevos)
        meta["_ids"].update(nuevos)
        resumen.update(paginas=pagina, apariciones=resumen["apariciones"] + len(productos),
                       ids_unicos=len(ids))
        grupo.update(resumen)

        if len(ids) == esperado:
            resumen["estado"] = "completa"
            grupo.update(resumen)
            print(f"{nombre_fuente}: {len(ids)} productos reunidos", flush=True)
            return
        if len(ids) > esperado or not productos:
            raise ValueError("El recuento obtenido no coincide con el total declarado")
    raise ValueError("Se alcanzó el límite de páginas sin completar la subcategoría")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-paginas", type=int, default=200)
    parser.add_argument("--limite-categorias", type=int,
                        help="Prueba acotada; deja la captura como parcial")
    args = parser.parse_args()
    if args.max_paginas < 1 or (args.limite_categorias is not None and args.limite_categorias < 1):
        parser.error("Los límites deben ser positivos")
    pares = {}
    inicio = datetime.now(timezone.utc)
    carpeta = RAIZ / "data" / inicio.strftime("%Y-%m-%d_%H%M%S_%fZ")
    carpeta.mkdir(parents=True, exist_ok=False)
    meta = {"inicio_utc": inicio.isoformat(), "estado": "incompleta",
            "alcance": "Solo categorías principales de categories del menú; listado reduced",
            "limites": vars(args), "descargas": [], "categorias": [], "_ids": set(), "_catalogo": []}
    try:
        menu = descargar(MENU, "categorias.json", carpeta, meta["descargas"])
        pares = categorias_del_menu(menu)
        meta["categorias_previstas"] = len(pares)
        seleccion = list(pares.items())
        if args.limite_categorias:
            seleccion = seleccion[:args.limite_categorias]
        for (l1, sub), nombre in seleccion:
            try:
                recoger_categoria(l1, sub, nombre, carpeta, meta, args.max_paginas)
            except (OSError, ValueError, KeyError, TypeError) as error:
                meta["categorias"][-1]["error"] = str(error)
                print(f"Categoría incompleta {sub}: {error}", flush=True)
                if isinstance(error, HTTPError) and error.code in (401, 403, 429):
                    meta["error"] = "Acceso restringido o límite de peticiones; descarga detenida"
                    break
        completas = sum(c["estado"] == "completa" for c in meta["categorias"])
        meta["categorias_completas"] = completas
        if completas == len(pares):
            meta["estado"] = "completa"
    except (OSError, ValueError, KeyError, TypeError) as error:
        meta["error"] = str(error)
    except KeyboardInterrupt:
        meta["error"] = "Interrumpida por el usuario"
    finally:
        grupos = meta.pop("_catalogo")
        for grupo, resumen in zip(grupos, meta["categorias"]):
            grupo.update(resumen)
        # Recuento de los productos efectivamente conservados en el JSON unido.
        ids_conservados = {
            str(producto["object_id"])
            for grupo in grupos for producto in grupo["productos"]
            if isinstance(producto.get("object_id"), (str, int))
            and not isinstance(producto.get("object_id"), bool)
        }
        meta.pop("_ids")
        meta["productos_unicos"] = len(ids_conservados)
        meta["urls_categorias"] = [
            {"categoria": nombre,
             "url_primera_pagina": BASE + f"/api/v1/plp-back/l1/all/{l1}/reduced?" +
                 urlencode({"category_id": sub, "page": 1})}
            for (l1, sub), nombre in pares.items()
        ]
        meta["fin_utc"] = datetime.now(timezone.utc).isoformat()
        meta["archivos_guardados"] = sum(x.get("guardado", False) for x in meta["descargas"])
        meta["apariciones"] = sum(x["apariciones"] for x in meta["categorias"])
        salida = carpeta
        archivos_agrupados = []
        nombres_usados = set()
        for grupo in grupos:
            nombre_fuente = grupo.get("nombre_fuente", grupo["nombre"])
            # Windows prohíbe estos caracteres en los nombres de archivo.
            nombre_archivo = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", nombre_fuente).strip().rstrip(". ")
            nombre_archivo = nombre_archivo or grupo["categoria"]
            if nombre_archivo.casefold() in nombres_usados:
                nombre_archivo += "_" + grupo["categoria"]
            nombres_usados.add(nombre_archivo.casefold())
            destino = salida / (nombre_archivo + ".json")
            contenido = {
                "current_category": grupo["l1"],
                "current_subcategory": {
                    "id": grupo["categoria"],
                    "name": nombre_fuente,
                    "total_items": grupo.get("total_declarado"),
                },
                "estado": grupo["estado"],
                "error": grupo.get("error"),
                "inicio_utc": meta["inicio_utc"],
                "fin_utc": meta["fin_utc"],
                "apariciones_conservadas": len(grupo["productos"]),
                "items": grupo["productos"],
            }
            with destino.open("x", encoding="utf-8") as archivo:
                json.dump(contenido, archivo, ensure_ascii=False, indent=2)
            archivos_agrupados.append(str(destino))
        meta["archivos_agrupados"] = archivos_agrupados
        print(f"Categorías agrupadas en: {salida}", flush=True)
        if meta.get("error"):
            print(f"Incidencia: {meta['error']}", flush=True)
        print(f"Captura {meta['estado']}: {len(archivos_agrupados)} archivos por categoría, "
              f"{meta['productos_unicos']} IDs distintos. Carpeta: {carpeta}", flush=True)
    return 0 if meta["estado"] == "completa" else 1


if __name__ == "__main__":
    raise SystemExit(main())
