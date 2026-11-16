#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Transforma las capturas de DIA en data/processed/<captura>/productos_dia.json.

Uso: python scripts/2_transformacion.py [ruta/productos_dia.json]
Sin ruta, transforma todas las capturas de data/raw.
"""

import argparse
import json
import re
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UNIT_CONVERSIONS = {
    'kg': ('kg', Decimal('1')),
    'g': ('kg', Decimal('0.001')),
    'mg': ('kg', Decimal('0.000001')),
    'l': ('l', Decimal('1')),
    'dl': ('l', Decimal('0.1')),
    'cl': ('l', Decimal('0.01')),
    'ml': ('l', Decimal('0.001')),
    'km': ('m', Decimal('1000')),
    'm': ('m', Decimal('1')),
    'cm': ('m', Decimal('0.01')),
    'mm': ('m', Decimal('0.001')),
    'unidad': ('unidad', Decimal('1')),
}
CONTENT_PATTERN = re.compile(
    r"(?<![\w.,])(?:(?P<count>\d+)\s*[x×]\s*)?"
    r"(?P<quantity>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>kg|mg|g|ml|cl|dl|litros?|l|unidades?|uds?\.?|km|cm|mm|metros?|m)"
    r"\s*(?:aprox\.?)?\s*$",
    re.IGNORECASE,
)
PACKAGING_PATTERN = re.compile(
    r"\b(botella|botellín|brik|brick|tetrabrik|bote|lata|tarro|"
    r"bandeja|bolsa|saco|caja|estuche|tubo|sobre|tarrina|pack)\b",
    re.IGNORECASE,
)


def extract_content(name: str) -> tuple[int | None, int | float | None, str | None]:
    """Devuelve el número de contenidos y su tamaño individual en kg, l, m o unidad."""
    match = CONTENT_PATTERN.search(name)
    if match is None:
        return None, None, None

    quantity = Decimal(match['quantity'].replace(',', '.'))
    count = int(match['count'] or 1)
    unit = match['unit'].lower().rstrip('.')
    if unit.startswith('ud') or unit.startswith('unidad'):
        unit = 'unidad'
        if quantity != quantity.to_integral_value():
            return None, None, None
        count *= int(quantity)
        quantity = Decimal(1)
    elif unit.startswith('litro'):
        unit = 'l'
    elif unit.startswith('metro'):
        unit = 'm'

    unit, factor = UNIT_CONVERSIONS[unit]
    quantity *= factor
    number = int(quantity) if quantity == quantity.to_integral_value() else float(quantity)
    return count, number, unit


def transform_product(item: dict[str, Any], category: str) -> dict[str, Any]:
    """Selecciona los campos y normaliza identificador, imagen y precio."""
    product_id = item.get('object_id') or item.get('sku_id')
    if product_id is None or not str(product_id).strip():
        raise ValueError('Producto sin object_id ni sku_id.')

    name = (item.get('display_name') or '').strip()
    count, size, unit = extract_content(name)
    packaging = PACKAGING_PATTERN.search(name)
    image = item.get('image')
    price = (item.get('prices') or {}).get('price')

    product = {
        'producto_id': str(product_id),
        'categorias': [category],
        'nombre': name,
        'marca': (item.get('brand') or '').strip() or None,
        'supermercado': 'DIA',
    }
    if packaging:
        product['envase'] = packaging.group().lower()
    product.update({
        'imagen_url': urljoin('https://www.dia.es/', image) if image else None,
        'precio_por_unidad_centimos': int(
            (Decimal(str(price)) * 100 / count).quantize(
                Decimal('1'), rounding=ROUND_HALF_UP
            )
        ) if price is not None and count else None,
        'cantidad_contenidos': count,
        'unidad_contenido': unit,
        'tamano_unidad': size,
    })
    return product


def transform_dataset(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Agrupa por producto y conserva todas sus categorías sin repeticiones.

    Cuando aparece en varias categorías, usa los datos de su primera aparición.
    """
    products = {}
    for category in data['categories']:
        category_name = category.get('name') or category['id']
        for item in category['items']:
            product = transform_product(item, category_name)
            product_id = product['producto_id']
            if product_id not in products:
                products[product_id] = product
            elif category_name not in products[product_id]['categorias']:
                products[product_id]['categorias'].append(category_name)
    return list(products.values())


def transform_file(source: Path) -> Path:
    with source.open(encoding='utf-8') as file:
        products = transform_dataset(json.load(file))

    destination = DATA_DIR / 'processed' / source.parent.name / 'productos_dia.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=destination.parent,
            suffix='.tmp', delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(products, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write('\n')
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    print(f'{len(products)} productos guardados en {destination}')
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', type=Path, help='Captura JSON a transformar')
    args = parser.parse_args()
    sources = [args.source] if args.source else sorted(
        (DATA_DIR / 'raw').glob('*/productos_dia.json')
    )
    if not sources:
        parser.error('No hay capturas productos_dia.json en data/raw.')
    for source in sources:
        transform_file(source)


if __name__ == '__main__':
    main()
