#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingesta de categorías principales seleccionadas y productos de DIA.

Python >= 3.10
Dependencia: requests

Códigos de salida:
  0 = captura completa según los criterios observables del script
  1 = captura parcial/incompleta (se conservaron los resultados disponibles)
  2 = fallo total (no se pudo obtener/procesar el menú o no se pudo escribir
      el resultado consolidado/manifiesto)

Los originales se guardan como bytes de respuesta HTTP después de que
Requests haya aplicado la descompresión de transporte (gzip/br/deflate).
No son una captura literal de los bytes de red. No se reformatean como JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


MENU_URL = "https://www.dia.es/api/v1/common-aggregator/menu-data"
PRODUCTS_URL_TEMPLATE = (
    "https://www.dia.es/api/v1/plp-back/l1/all/{category_id}/reduced"
)

# Las categorías no se escriben manualmente: se leen del array raíz
# "categories" de la respuesta menu-data. No se recorren sus "children".
USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/157.0.0.0 Safari/537.36"
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp(value: datetime | None = None) -> str:
    value = value or utc_now()
    return value.strftime("%Y%m%dT%H%M%S.%fZ")


def iso_utc(value: datetime | None = None) -> str:
    value = value or utc_now()
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def write_bytes_exclusive(path: Path, content: bytes) -> None:
    """Escribe bytes sin sobrescribir un archivo existente."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def write_json(path: Path, data: Any) -> None:
    """Escribe JSON derivado/manifest en UTF-8 y formato legible."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_json_response(response: requests.Response) -> Any:
    try:
        return response.json()
    except (ValueError, json.JSONDecodeError) as exc:
        preview = response.text[:300].replace("\n", " ")
        raise ValueError(
            f"La respuesta HTTP {response.status_code} no contiene JSON válido. "
            f"Inicio del cuerpo: {preview!r}"
        ) from exc


def fetch_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None,
    timeout: float,
    retries: int,
    pause: float,
    raw_dir: Path,
    raw_stem: str,
    request_log: list[dict[str, Any]],
) -> tuple[Any, bytes, dict[str, Any]]:
    """
    Descarga una respuesta con reintentos finitos.
    Cada cuerpo recibido se conserva individualmente, incluso los HTTP fallidos.
    """
    last_error: Exception | None = None

    for attempt in range(1, retries + 2):
        if pause > 0:
            time.sleep(pause)

        try:
            response = session.get(
                url,
                params=params,
                timeout=timeout,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "es-ES,es;q=0.9",
                    "Referer": "https://www.dia.es/",
                    "Origin": "https://www.dia.es",
                },
            )
            body = response.content
            suffix = "json" if response.headers.get(
                "Content-Type", ""
            ).lower().find("json") >= 0 else "bin"
            raw_path = raw_dir / f"{raw_stem}_attempt_{attempt:02d}.{suffix}"
            write_bytes_exclusive(raw_path, body)

            entry = {
                "requested_url": response.url,
                "status_code": response.status_code,
                "attempt": attempt,
                "raw_file": str(raw_path),
                "body_bytes": len(body),
                "content_type": response.headers.get("Content-Type"),
            }
            request_log.append(entry)

            if response.status_code in (408, 429) or 500 <= response.status_code <= 599:
                last_error = requests.HTTPError(
                    f"HTTP {response.status_code} para {response.url}",
                    response=response,
                )
                if attempt <= retries:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = min(float(retry_after), 60.0) if retry_after else 0.0
                    except ValueError:
                        delay = 0.0
                    if delay > 0:
                        time.sleep(delay)
                    continue

            response.raise_for_status()
            payload = parse_json_response(response)
            return payload, body, entry

        except (requests.RequestException, ValueError, OSError) as exc:
            last_error = exc
            if attempt > retries:
                break
            # No se reintentan errores de escritura: el siguiente intento no
            # arreglaría la falta de permisos o de espacio.
            if isinstance(exc, OSError):
                break

    raise RuntimeError(
        f"No se pudo completar la petición {url}: {last_error}"
    ) from last_error


def extract_categories(menu: Any) -> list[dict[str, str]]:
    if not isinstance(menu, dict):
        raise ValueError("El menú JSON no es un objeto.")
    categories = menu.get("categories")
    if not isinstance(categories, list):
        raise ValueError("El menú no contiene un array 'categories'.")

    result: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, category in enumerate(categories):
        if not isinstance(category, dict):
            raise ValueError(f"categories[{index}] no es un objeto.")
        category_id = category.get("id")
        name = category.get("name")
        if not isinstance(category_id, str) or not category_id.strip():
            raise ValueError(f"categories[{index}] no tiene un id válido.")
        if not isinstance(name, str) or not name.strip():
            name = category_id
        category_id = category_id.strip()
        # El array raíz contiene las categorías principales. No se entra en children.
        if category_id not in seen_ids:
            result.append({"id": category_id, "name": name.strip()})
            seen_ids.add(category_id)
    return result


def find_pagination_objects(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Localiza objetos llamados pagination sin interpretar next_url."""
    found: list[dict[str, Any]] = []

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


def numeric_metadata(pagination_objects: list[dict[str, Any]]) -> dict[str, Any]:
    """Conserva los metadatos de paginación encontrados, sin asumir un esquema."""
    selected: dict[str, Any] = {}
    wanted = {
        "page_number", "current_page", "total_pages", "last_page",
        "per_page", "page_size", "total_items", "total", "has_next",
        "has_more", "next_page",
    }
    for obj in pagination_objects:
        for key in wanted:
            if key in obj and key not in selected:
                value = obj[key]
                if isinstance(value, (str, int, float, bool)) or value is None:
                    selected[key] = value
    return selected


def positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
        return number if number >= 0 else None
    except (TypeError, ValueError):
        return None


def get_expected_page_count(metadata: dict[str, Any]) -> int | None:
    for key in ("total_pages", "last_page"):
        value = positive_int(metadata.get(key))
        if value is not None and value > 0:
            return value
    return None


def get_expected_item_count(metadata: dict[str, Any]) -> int | None:
    for key in ("total_items", "total"):
        value = positive_int(metadata.get(key))
        if value is not None:
            return value
    return None


def ingest_category(
    category: dict[str, str],
    session: requests.Session,
    raw_root: Path,
    timeout: float,
    retries: int,
    pause: float,
    max_pages: int,
    request_log: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, Any]:
    category_id = category["id"]
    category_raw_dir = raw_root / safe_component(category_id)
    category_raw_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "id": category_id,
        "name": category["name"],
        "complete": False,
        "items": [],
        "pages_requested": 0,
        "pages_with_items": 0,
        "item_occurrences": 0,
        "termination": None,
        "pagination_observations": [],
        "warnings": [],
        "errors": [],
        "raw_files": [],
    }

    seen_page_hashes: dict[str, int] = {}
    first_metadata: dict[str, Any] = {}
    terminal_empty_page_seen = False

    for page in range(1, max_pages + 1):
        url = PRODUCTS_URL_TEMPLATE.format(category_id=quote(category_id, safe=""))
        params = {"category_id": category_id, "page": page}
        before = len(request_log)

        try:
            payload, body, request_entry = fetch_json(
                session=session,
                url=url,
                params=params,
                timeout=timeout,
                retries=retries,
                pause=pause,
                raw_dir=category_raw_dir,
                raw_stem=f"page_{page:04d}",
                request_log=request_log,
            )
            result["raw_files"].append(request_entry["raw_file"])
            result["pages_requested"] += 1
        except Exception as exc:
            # Añade a la categoría y continúa con la siguiente; no se puede
            # saltar con seguridad una página fallida dentro de esta categoría.
            message = f"Categoría {category_id}, página {page}: {exc}"
            result["errors"].append(message)
            errors.append(message)
            result["termination"] = "error_de_peticion_o_respuesta"
            break

        if not isinstance(payload, dict):
            message = (
                f"Categoría {category_id}, página {page}: "
                "la raíz de la respuesta no es un objeto JSON."
            )
            result["errors"].append(message)
            errors.append(message)
            result["termination"] = "estructura_json_invalida"
            break

        items = payload.get("items")
        if not isinstance(items, list):
            message = (
                f"Categoría {category_id}, página {page}: "
                "falta el array 'items' o no es una lista."
            )
            result["errors"].append(message)
            errors.append(message)
            result["termination"] = "items_ausente_o_invalido"
            break

        pagination = numeric_metadata(find_pagination_objects(payload))
        result["pagination_observations"].append({
            "requested_page": page,
            "metadata": pagination,
            "items_in_page": len(items),
        })
        if page == 1:
            first_metadata = pagination

        # Huella del contenido de items. No se elimina ni modifica ningún
        # producto; la huella solo detecta respuestas de página repetidas.
        try:
            canonical_items = json.dumps(
                items, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            message = (
                f"Categoría {category_id}, página {page}: "
                f"no se pudo calcular la huella de items: {exc}"
            )
            result["warnings"].append(message)
            canonical_items = body

        page_hash = hashlib.sha256(canonical_items).hexdigest()

        if not items:
            terminal_empty_page_seen = True
            result["termination"] = "pagina_items_vacia_observada"
            expected_pages = get_expected_page_count(pagination)
            if expected_pages is not None and page <= expected_pages:
                result["warnings"].append(
                    f"Metadatos indican total_pages={expected_pages}, "
                    f"pero la página solicitada {page} está vacía."
                )
                result["termination"] = "pagina_vacia_con_metadatos_contradictorios"
            break

        if page_hash in seen_page_hashes:
            previous_page = seen_page_hashes[page_hash]
            message = (
                f"Categoría {category_id}: la página {page} repite el contenido "
                f"de la página {previous_page}; se detiene para evitar un bucle."
            )
            result["warnings"].append(message)
            result["termination"] = "pagina_repetida"
            break

        seen_page_hashes[page_hash] = page
        result["pages_with_items"] += 1
        result["items"].extend(items)
        result["item_occurrences"] += len(items)

        # DIA puede devolver page_number/total_pages incoherentes. Se conservan
        # en pagination_observations, pero no se usan como criterio de parada.
        # El total de productos relevante es el total_items de la raíz.
        if page == 1:
            root_total = positive_int(payload.get("total_items"))
            if root_total is not None:
                result["expected_items_from_first_page"] = root_total
            else:
                fallback_total = get_expected_item_count(pagination)
                if fallback_total is not None:
                    result["expected_items_from_first_page"] = fallback_total

    else:
        result["termination"] = "limite_max_pages_alcanzado"
        result["warnings"].append(
            f"Se alcanzó max_pages={max_pages} sin observar una página vacía."
        )

    # Si la página vacía no pudo obtenerse antes del límite/error, no se
    # considera demostrada la finalización. Los metadatos por sí solos no bastan.
    if not terminal_empty_page_seen:
        result["complete"] = False
    elif result["termination"] == "pagina_items_vacia_observada":
        result["complete"] = True
    else:
        result["complete"] = False

    expected_items = result.get("expected_items_from_first_page")
    if expected_items is not None and expected_items != result["item_occurrences"]:
        result["warnings"].append(
            f"El total_items de la primera página ({expected_items}) no coincide "
            f"con las apariciones descargadas ({result['item_occurrences']}). "
            "No se descartan registros ni se ajusta el resultado."
        )
        # La discrepancia no invalida automáticamente una terminación por
        # página vacía, pero sí deja constancia de la incertidumbre.
        result["complete"] = False

    if result["errors"] or result["warnings"]:
        result["complete"] = False

    # Campos auxiliares no forman parte de la salida consolidada de productos.
    result.pop("expected_items_from_first_page", None)
    return result


def safe_component(value: str) -> str:
    cleaned = "".join(
        char if char.isalnum() or char in ("-", "_") else "_"
        for char in value
    )
    return cleaned or "category"


def create_run_directories(
    raw_base: Path, processed_base: Path
) -> tuple[str, Path, Path]:
    stamp = utc_stamp()
    raw_dir = raw_base / stamp
    processed_dir = processed_base / stamp
    # mkdir sin exist_ok evita sobrescribir una ejecución previa.
    raw_dir.mkdir(parents=True, exist_ok=False)
    processed_dir.mkdir(parents=True, exist_ok=False)
    return stamp, raw_dir, processed_dir


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Descarga secuencial de productos de las categorías principales "
            "de DIA y genera un JSON consolidado."
        )
    )
    parser.add_argument("--raw-dir", default="data/raw", help="Directorio de originales.")
    parser.add_argument(
        "--processed-dir", default="data/processed",
        help="Directorio de resultados consolidados."
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout por petición (s).")
    parser.add_argument("--pause", type=float, default=1.0, help="Pausa antes de cada petición (s).")
    parser.add_argument("--retries", type=int, default=2, help="Reintentos adicionales por petición.")
    parser.add_argument(
        "--max-pages", type=int, default=100,
        help="Máximo de páginas por categoría; alcanzarlo sin página vacía es incompleto."
    )
    parser.add_argument(
        "--menu-url", default=MENU_URL,
        help="URL del menú (útil para pruebas o cambios de endpoint)."
    )
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    if args.timeout <= 0:
        raise ValueError("--timeout debe ser mayor que cero.")
    if args.pause < 0:
        raise ValueError("--pause no puede ser negativo.")
    if args.retries < 0:
        raise ValueError("--retries no puede ser negativo.")
    if args.max_pages < 1:
        raise ValueError("--max-pages debe ser al menos 1.")


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        validate_arguments(args)
        raw_base = Path(args.raw_dir)
        processed_base = Path(args.processed_dir)
        stamp, raw_dir, processed_dir = create_run_directories(
            raw_base, processed_base
        )
    except (ValueError, OSError) as exc:
        print(f"ERROR: no se pudieron preparar los directorios o argumentos: {exc}", file=sys.stderr)
        return 2

    started_at = utc_now()
    manifest: dict[str, Any] = {
        "run_id": stamp,
        "started_at_utc": iso_utc(started_at),
        "finished_at_utc": None,
        "source": "Supermercado DIA API",
        "menu_url": args.menu_url,
        "products_url_template": PRODUCTS_URL_TEMPLATE + "?category_id={CATEGORY_ID}&page={PAGE}",
        "scope": (
            "Todas las categorías principales leídas dinámicamente del array raíz "
            "categories de menu-data; no se consultan children. Para cada categoría "
            "se usa su id tanto en la ruta como en el parámetro category_id."
        ),
        "category_source": "menu-data.categories (array raíz)",
        "category_ids_are_dynamic": True,
        "configuration": {
            "timeout_seconds": args.timeout,
            "pause_seconds": args.pause,
            "retries": args.retries,
            "max_pages_per_category": args.max_pages,
        },
        "http_response_storage": (
            "Se guardan response.content bytes. Requests descomprime automáticamente "
            "la compresión HTTP de transporte habitual; por tanto, no son bytes "
            "literales del cable. No se descarga ningún archivo comprimido como "
            "artefacto independiente."
        ),
        "termination_criteria": (
            "Se solicita page=1,2,... hasta observar items=[]; no se sigue next_url. "
            "Una página vacía después de páginas con productos se considera evidencia "
            "operativa de final. Contradicciones de metadatos, errores, páginas "
            "repetidas o alcanzar max_pages dejan la categoría incompleta."
        ),
        "request_log": [],
        "categories": [],
        "errors": [],
        "complete": False,
        "raw_directory": str(raw_dir),
        "processed_directory": str(processed_dir),
    }

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://www.dia.es/",
        "Origin": "https://www.dia.es",
    })
    menu: Any = None
    categories: list[dict[str, str]] = []
    menu_ok = False

    try:
        # Primero visitamos la página principal para establecer la sesión
        # y obtener las cookies que DIA necesita.
        home_response = session.get(
            "https://www.dia.es/",
            timeout=args.timeout,
        )

        home_body = home_response.content

        home_raw_path = raw_dir / "homepage.html"
        write_bytes_exclusive(home_raw_path, home_body)

        manifest["request_log"].append({
            "requested_url": home_response.url,
            "status_code": home_response.status_code,
            "attempt": 1,
            "raw_file": str(home_raw_path),
            "body_bytes": len(home_body),
            "content_type": home_response.headers.get("Content-Type"),
        })

        home_response.raise_for_status()
        
        menu, menu_body, menu_entry = fetch_json(
            session=session,
            url=args.menu_url,
            params=None,
            timeout=args.timeout,
            retries=args.retries,
            pause=args.pause,
            raw_dir=raw_dir,
            raw_stem="menu-data",
            request_log=manifest["request_log"],
        )
        manifest["menu_raw_file"] = menu_entry["raw_file"]
        categories = extract_categories(menu)
        if not categories:
            raise ValueError("El array raíz 'categories' no contiene categorías válidas.")
        # Guardamos la lista extraída para que quede constancia de qué categorías
        # se leyeron del primer JSON antes de consultar los productos.
        categories_file = raw_dir / "categorias_detectadas.json"
        write_json(categories_file, categories)
        manifest["categories_file"] = str(categories_file)
        menu_ok = True
    except Exception as exc:
        message = f"No se pudo obtener/procesar el menú: {exc}"
        manifest["errors"].append(message)
        print(f"ERROR: {message}", file=sys.stderr)

    consolidated_categories: list[dict[str, Any]] = []

    if menu_ok:
        for index, category in enumerate(categories, start=1):
            print(
                f"[{index}/{len(categories)}] {category['name']} ({category['id']})...",
                flush=True,
            )
            category_result = ingest_category(
                category=category,
                session=session,
                raw_root=raw_dir,
                timeout=args.timeout,
                retries=args.retries,
                pause=args.pause,
                max_pages=args.max_pages,
                request_log=manifest["request_log"],
                errors=manifest["errors"],
            )
            manifest["categories"].append({
                key: value for key, value in category_result.items() if key != "items"
            })
            consolidated_categories.append({
                "id": category_result["id"],
                "name": category_result["name"],
                "complete": category_result["complete"],
                "items": category_result["items"],
            })

    finished_at = utc_now()
    manifest["finished_at_utc"] = iso_utc(finished_at)
    manifest["duration_seconds"] = round(
        (finished_at - started_at).total_seconds(), 3
    )
    manifest["category_count"] = len(categories)
    manifest["categories_processed"] = len(consolidated_categories)
    manifest["pages_requested"] = sum(
        item.get("pages_requested", 0) for item in manifest["categories"]
    )
    manifest["pages_with_items"] = sum(
        item.get("pages_with_items", 0) for item in manifest["categories"]
    )
    manifest["item_occurrences"] = sum(
        len(item["items"]) for item in consolidated_categories
    )
    manifest["categories_complete"] = sum(
        1 for item in manifest["categories"] if item.get("complete")
    )
    manifest["categories_incomplete"] = (
        len(manifest["categories"]) - manifest["categories_complete"]
    )
    manifest["complete"] = (
        menu_ok
        and len(consolidated_categories) == len(categories)
        and all(item["complete"] for item in consolidated_categories)
        and not manifest["errors"]
    )

    output_path = processed_dir / "productos_por_categoria.json"
    manifest_path = raw_dir / "manifest.json"

    try:
        write_json(
            output_path,
            {
                "captured_at": manifest["finished_at_utc"],
                "complete": manifest["complete"],
                "categories": consolidated_categories,
            },
        )
        manifest["consolidated_file"] = str(output_path)
    except (OSError, TypeError, ValueError) as exc:
        manifest["errors"].append(
            f"No se pudo escribir el JSON consolidado: {exc}"
        )
        manifest["complete"] = False

    try:
        write_json(manifest_path, manifest)
    except (OSError, TypeError, ValueError) as exc:
        print(f"ERROR: no se pudo escribir el manifiesto: {exc}", file=sys.stderr)
        session.close()
        return 2

    session.close()

    print("\n========== RESUMEN DE INGESTA ==========")
    print(f"Categorías leídas del menú: {len(categories)}")
    if menu_ok:
        print(f"Listado de categorías:     {raw_dir / 'categorias_detectadas.json'}")
    print(f"Categorías procesadas:     {len(consolidated_categories)}")
    print(f"Categorías completas:      {manifest['categories_complete']}")
    print(f"Categorías incompletas:    {manifest['categories_incomplete']}")
    print(f"Páginas solicitadas:       {manifest['pages_requested']}")
    print(f"Páginas con productos:     {manifest['pages_with_items']}")
    print(f"Apariciones de productos:  {manifest['item_occurrences']}")
    print(f"Errores:                   {len(manifest['errors'])}")
    print(f"JSON consolidado:          {output_path}")
    print(f"Originales y manifiesto:   {raw_dir}")
    print(f"Manifiesto:                {manifest_path}")
    print(f"Captura completa:          {'SÍ' if manifest['complete'] else 'NO'}")

    if not menu_ok:
        return 2
    if not manifest["complete"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
