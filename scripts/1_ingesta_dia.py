"""Descarga los productos de cada categoría de DIA en data/raw/<fecha>/<categoria>.json."""
import json
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://www.dia.es"
CABECERAS = {"Accept": "application/json", "User-Agent": "Proyecto-academico-DIA/1.0"}
CARPETA = Path(__file__).resolve().parent.parent / "data" / "raw" / date.today().isoformat()


def obtener_json(ruta):
    time.sleep(1)
    with urlopen(Request(BASE_URL + ruta, headers=CABECERAS), timeout=20) as respuesta:
        return json.load(respuesta)


def descargar_categoria(id_categoria):
    resultado = None
    pagina = 1

    while True:
        consulta = urlencode({"category_id": id_categoria, "page": pagina})
        datos = obtener_json(f"/api/v1/plp-back/l1/all/{id_categoria}/reduced?{consulta}")
        
        if resultado is None:
            resultado = {
                "current_category": datos.get("current_category"),
                "current_subcategory": datos.get("current_subcategory"),
                "items": [],
            }
        
        resultado["items"].extend(datos["items"])
        # Algunas categorías (p. ej. L128) no traen current_subcategory y dan el total en la raíz.
        total = (datos.get("current_subcategory") or datos)["total_items"]

        if not datos["items"] or len(resultado["items"]) >= total:
            return resultado
        
        pagina += 1


def main():
    CARPETA.mkdir(parents=True, exist_ok=True)
    menu = obtener_json("/api/v1/common-aggregator/menu-data")

    for categoria in menu["categories"]:
        resultado = descargar_categoria(categoria["id"])
        nombre = re.sub(r'[<>:"/\\|?*]', "_", categoria["name"]).strip()

        with open(CARPETA / f"{nombre}.json", "w", encoding="utf-8") as archivo:
            json.dump(resultado, archivo, ensure_ascii=False, indent=2)

        print(f"{nombre}: {len(resultado['items'])} productos")


if __name__ == "__main__":
    main()
