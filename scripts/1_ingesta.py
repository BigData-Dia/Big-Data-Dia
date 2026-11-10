
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ingesta de productos de las categorías principales de DIA.

Python >= 3.10
Dependencia: requests

Códigos de salida:
  0 = captura completa
  1 = captura parcial o incompleta
  2 = fallo total

Se genera un único archivo:
data/raw/<fecha_hora>/productos_dia.json
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

MENU_URL = "https://www.dia.es/api/v1/common-aggregator/menu-data"

PRODUCTS_URL = (
    "https://www.dia.es/api/v1/plp-back/l1/all/{category_id}/reduced"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/157.0.0.0 Safari/537.36"
)

# Parámetros fijos de las peticiones
TIMEOUT = 30
PAUSE = 1
RETRIES = 2

# Máximo de páginas por categoría.
# Para probar: 2. Para la extracción completa: 100.
MAX_PAGES = 100

# Carpeta donde se guardarán los datos
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


# ============================================================
# 2. FECHAS Y ARCHIVOS
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_output_directory() -> Path:
    """Crea una carpeta identificada por la fecha y hora."""
    timestamp = utc_now().strftime("%Y%m%dT%H%M%S.%fZ")

    output_dir = RAW_DIR / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)

    return output_dir


def write_json(path: Path, data: Any) -> None:
    """Guarda los datos en un archivo JSON."""
    with path.open("x", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


# ============================================================
# 3. CONEXIÓN HTTP
# ============================================================

def create_session() -> requests.Session:
    """Crea una sesión HTTP reutilizable."""
    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.dia.es/",
        "Origin": "https://www.dia.es",
    })

    return session


def initialize_session(session: requests.Session) -> None:
    """Visita la página principal para establecer la sesión con DIA."""
    last_error = None

    for attempt in range(RETRIES + 1):

        time.sleep(PAUSE)

        try:
            response = session.get(
                "https://www.dia.es/",
                timeout=TIMEOUT,
            )

            if (
                response.status_code in (408, 429)
                or 500 <= response.status_code <= 599
            ):
                if attempt < RETRIES:
                    time.sleep(2 * (attempt + 1))
                    continue

            response.raise_for_status()
            return

        except requests.RequestException as exc:
            last_error = exc

            if attempt == RETRIES:
                break

    raise RuntimeError(
        f"No se pudo establecer la sesión con DIA: {last_error}"
    )


def fetch_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Realiza una petición HTTP con reintentos y devuelve el JSON."""
    last_error = None

    for attempt in range(RETRIES + 1):

        time.sleep(PAUSE)

        try:
            response = session.get(
                url,
                params=params,
                timeout=TIMEOUT,
            )

            if (
                response.status_code in (408, 429)
                or 500 <= response.status_code <= 599
            ):
                if attempt < RETRIES:
                    retry_after = response.headers.get("Retry-After")

                    try:
                        delay = (
                            min(float(retry_after), 60)
                            if retry_after
                            else 2 * (attempt + 1)
                        )
                    except ValueError:
                        delay = 2 * (attempt + 1)

                    time.sleep(delay)
                    continue

            response.raise_for_status()

            return response.json()

        except (requests.RequestException, ValueError) as exc:
            last_error = exc

            if attempt == RETRIES:
                break

    raise RuntimeError(
        f"No se pudo completar la petición {url}: {last_error}"
    )


# ============================================================
# 4. EXTRACCIÓN DE CATEGORÍAS
# ============================================================

def extract_categories(menu: Any) -> list[dict[str, str]]:
    """Obtiene las categorías principales del menú de DIA."""

    if not isinstance(menu, dict):
        raise ValueError("El menú JSON no es un objeto.")

    categories = menu.get("categories")

    if not isinstance(categories, list):
        raise ValueError("El menú no contiene un array 'categories'.")

    result = []
    seen_ids = set()

    for index, category in enumerate(categories):

        if not isinstance(category, dict):
            raise ValueError(
                f"categories[{index}] no es un objeto."
            )

        category_id = category.get("id")
        name = category.get("name")

        if not isinstance(category_id, str) or not category_id.strip():
            raise ValueError(
                f"categories[{index}] no tiene un id válido."
            )

        if not isinstance(name, str) or not name.strip():
            name = category_id

        category_id = category_id.strip()

        if category_id not in seen_ids:

            result.append({
                "id": category_id,
                "name": name.strip(),
            })

            seen_ids.add(category_id)

    return result


# ============================================================
# 5. METADATOS DE PAGINACIÓN
# ============================================================

def find_pagination_objects(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Busca objetos llamados pagination dentro de la respuesta."""

    found = []

    def walk(value: Any) -> None:

        if isinstance(value, dict):

            for key, child in value.items():

                if key == "pagination" and isinstance(child, dict):
                    found.append(child)
                else:
                    walk(child)

        elif isinstance(value, list):

            for child in value:
                walk(child)

    walk(payload)

    return found


def get_expected_item_count(payload: dict[str, Any]) -> int | None:
    """Obtiene el total esperado de productos si está disponible."""

    def valid_count(value: Any) -> int | None:
        if isinstance(value, bool):
            return None

        try:
            number = int(value)
            return number if number >= 0 else None
        except (TypeError, ValueError):
            return None

    # Primero comprobamos el total de la raíz.
    total = valid_count(payload.get("total_items"))

    if total is not None:
        return total

    # Si no existe, comprobamos los metadatos de paginación.
    for pagination in find_pagination_objects(payload):

        for key in ("total_items", "total"):

            total = valid_count(pagination.get(key))

            if total is not None:
                return total

    return None


def get_expected_page_count(payload: dict[str, Any]) -> int | None:
    """Obtiene el número total de páginas si está disponible."""

    for pagination in find_pagination_objects(payload):

        for key in ("total_pages", "last_page"):

            try:
                value = int(pagination.get(key))

                if value > 0:
                    return value

            except (TypeError, ValueError):
                continue

    return None


# ============================================================
# 6. DESCARGA DE PRODUCTOS POR CATEGORÍA
# ============================================================

def ingest_category(
    category: dict[str, str],
    session: requests.Session,
) -> dict[str, Any]:

    category_id = category["id"]

    result = {
        "id": category_id,
        "name": category["name"],
        "complete": False,
        "items": [],
        "pages_requested": 0,
        "pages_with_items": 0,
        "warnings": [],
        "errors": [],
    }

    seen_page_hashes = {}
    expected_items = None
    terminal_empty_page_seen = False

    for page in range(1, MAX_PAGES + 1):

        url = PRODUCTS_URL.format(
            category_id=quote(category_id, safe="")
        )

        params = {
            "category_id": category_id,
            "page": page,
        }

        try:
            payload = fetch_json(
                session=session,
                url=url,
                params=params,
            )

            result["pages_requested"] += 1

        except Exception as exc:

            result["errors"].append(
                f"Página {page}: {exc}"
            )

            break

        if not isinstance(payload, dict):

            result["errors"].append(
                f"Página {page}: la respuesta no es un objeto JSON."
            )

            break

        items = payload.get("items")

        if not isinstance(items, list):

            result["errors"].append(
                f"Página {page}: falta el array 'items'."
            )

            break

        # Obtenemos el total esperado en la primera página.
        if page == 1:
            expected_items = get_expected_item_count(payload)

        # Una página vacía indica que hemos llegado al final.
        if not items:

            terminal_empty_page_seen = True

            expected_pages = get_expected_page_count(payload)

            if expected_pages is not None and page <= expected_pages:

                result["warnings"].append(
                    f"Los metadatos indican {expected_pages} páginas, "
                    f"pero la página {page} está vacía."
                )

            break

        # Detectamos si DIA devuelve una página repetida.
        canonical_items = json.dumps(
            items,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        page_hash = hashlib.sha256(canonical_items).hexdigest()

        if page_hash in seen_page_hashes:

            previous_page = seen_page_hashes[page_hash]

            result["warnings"].append(
                f"La página {page} repite el contenido "
                f"de la página {previous_page}."
            )

            break

        seen_page_hashes[page_hash] = page

        result["pages_with_items"] += 1

        # Se añaden los productos sin modificar sus campos originales.
        result["items"].extend(items)

    else:

        result["warnings"].append(
            f"Se alcanzó el límite de {MAX_PAGES} páginas."
        )

    # Comprobamos si la categoría se ha descargado completamente.
    result["complete"] = (
        terminal_empty_page_seen
        and not result["errors"]
        and not result["warnings"]
    )

    downloaded_items = len(result["items"])

    if (
        expected_items is not None
        and expected_items != downloaded_items
    ):

        result["warnings"].append(
            f"Total esperado: {expected_items}. "
            f"Productos descargados: {downloaded_items}."
        )

        result["complete"] = False

    return result


# ============================================================
# 7. PROCESO PRINCIPAL
# ============================================================

def main() -> int:

    started_at = utc_now()

    try:
        output_dir = create_output_directory()

    except OSError as exc:

        print(
            f"ERROR: no se pudo crear la carpeta de salida: {exc}"
        )

        return 2

    session = create_session()

    try:

        # Establecemos la conexión con DIA.
        initialize_session(session)

        # Obtenemos las categorías principales.
        menu = fetch_json(session, MENU_URL)

        categories = extract_categories(menu)

        if not categories:
            raise ValueError("No se han encontrado categorías.")

    except Exception as exc:

        print(f"ERROR: no se pudo obtener el menú: {exc}")

        session.close()
        return 2

    consolidated_categories = []

    total_pages = 0
    total_pages_with_items = 0
    total_products = 0
    complete_categories = 0
    total_errors = 0

    # Procesamos todas las categorías.
    for index, category in enumerate(categories, start=1):

        print(
            f"\n[{index}/{len(categories)}] "
            f"{category['name']} ({category['id']})...",
            flush=True,
        )

        result = ingest_category(
            category=category,
            session=session,
        )

        total_pages += result["pages_requested"]
        total_pages_with_items += result["pages_with_items"]
        total_products += len(result["items"])
        total_errors += len(result["errors"])

        if result["complete"]:
            complete_categories += 1

        # Conservamos la información de la categoría y sus productos.
        consolidated_categories.append({
            "id": result["id"],
            "name": result["name"],
            "complete": result["complete"],
            "items": result["items"],
        })

        print(
            f"Productos: {len(result['items'])} | "
            f"Páginas: {result['pages_requested']} | "
            f"Completa: {'Sí' if result['complete'] else 'No'}"
        )

        for warning in result["warnings"]:
            print(f"AVISO: {warning}")

        for error in result["errors"]:
            print(f"ERROR: {error}")

    session.close()

    finished_at = utc_now()

    capture_complete = (
        complete_categories == len(categories)
        and total_errors == 0
    )

    # Construimos el JSON final.
    final_data = {
        "captured_at": finished_at.isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
        "complete": capture_complete,
        "categories": consolidated_categories,
    }

    output_path = output_dir / "productos_dia.json"

    try:
        write_json(output_path, final_data)

    except (OSError, TypeError, ValueError) as exc:

        print(f"ERROR: no se pudo guardar el JSON: {exc}")

        return 2

    # Resumen de la ejecución.
    duration = (finished_at - started_at).total_seconds()

    print("\n========== RESUMEN DE INGESTA ==========")
    print(f"Categorías detectadas:    {len(categories)}")
    print(f"Categorías completas:     {complete_categories}")
    print(f"Categorías incompletas:   {len(categories) - complete_categories}")
    print(f"Páginas solicitadas:      {total_pages}")
    print(f"Páginas con productos:    {total_pages_with_items}")
    print(f"Productos obtenidos:      {total_products}")
    print(f"Errores:                  {total_errors}")
    print(f"Duración:                 {duration:.2f} segundos")
    print(f"Archivo generado:         {output_path}")
    print(f"Captura completa:         {'SÍ' if capture_complete else 'NO'}")

    return 0 if capture_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
