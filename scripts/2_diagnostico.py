#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Diagnóstico de los datos originales de DIA (Tarea 3.2).

Lee las capturas de data/raw/<captura>/productos_dia.json con pandas, sin
modificarlas, y muestra por pantalla las comprobaciones de estructura y calidad.

Uso: python scripts/2_diagnostico.py
Requisitos: Python >= 3.10 y pandas.
"""

import json
import sys
from pathlib import Path

import pandas as pd


RAW_DIR = Path(__file__).resolve().parent.parent / 'data' / 'raw'
ITEM_COLUMNS = ['display_name', 'object_id', 'sku_id', 'brand', 'url', 'image',
                'units_in_stock', 'weight']
PRICE_COLUMNS = ['prices.price', 'prices.price_per_unit', 'prices.measure_unit',
                 'prices.currency', 'prices.strikethrough_price',
                 'prices.discount_percentage', 'prices.is_club_price',
                 'prices.is_promo_price']


def title(text: str) -> None:
    print(f'\n{"=" * 70}\n{text}\n{"=" * 70}')


def load_capture(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (apariciones de productos, resumen de categorías) de una captura."""
    with path.open(encoding='utf-8') as file:
        data = json.load(file)

    items = pd.json_normalize(
        data['categories'], record_path='items',
        meta=['id', 'name', 'complete'], meta_prefix='category_',
    )
    items.insert(0, 'captura', path.parent.name)
    items.insert(1, 'captured_at', pd.to_datetime(data['captured_at']))

    categories = pd.DataFrame(
        [{'captura': path.parent.name, 'category_id': c['id'],
          'category_name': c.get('name'), 'complete': c.get('complete'),
          'items': len(c['items'])} for c in data['categories']]
    )
    categories['archivo_complete'] = data['complete']
    return items, categories


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    pd.set_option('display.width', 200)
    pd.set_option('display.max_columns', 30)
    pd.set_option('display.max_colwidth', 60)

    # 1. Carga ---------------------------------------------------------------
    title('1. CARGA DE LOS DATOS ORIGINALES')
    capture_dirs = sorted(p for p in RAW_DIR.iterdir() if p.is_dir())
    files = []
    for directory in capture_dirs:
        path = directory / 'productos_dia.json'
        if path.exists():
            files.append(path)
            print(f'  {path.relative_to(RAW_DIR.parent.parent)}  ({path.stat().st_size:,} bytes)')
        else:
            print(f'  AVISO: {directory.name}/ no contiene productos_dia.json (carpeta vacía)')

    loaded = [load_capture(path) for path in files]
    df = pd.concat([items for items, _ in loaded], ignore_index=True)
    cats = pd.concat([categories for _, categories in loaded], ignore_index=True)
    captures = list(df['captura'].unique())

    # 2. Estructura ----------------------------------------------------------
    title('2. ESTRUCTURA')
    print(f'Filas (apariciones producto-categoría) y columnas: {df.shape}')
    print(df.groupby('captura').size().rename('filas').to_string())
    print('\nTipos de datos:')
    print(df.dtypes.value_counts().to_string())
    print(df[ITEM_COLUMNS + PRICE_COLUMNS].dtypes.to_string())
    print('\nPrimeros registros (campos principales):')
    print(df[['captura', 'category_name', 'object_id', 'display_name', 'brand',
              'prices.price', 'prices.price_per_unit', 'prices.measure_unit']].head())

    # 3. Calidad -------------------------------------------------------------
    title('3. CALIDAD: VALORES AUSENTES')
    missing = df.isna().sum()
    missing = pd.DataFrame({'ausentes': missing, '%': (missing / len(df) * 100).round(1)})
    print(missing[missing['ausentes'] > 0].sort_values('ausentes', ascending=False).to_string())
    blank_brand = df['brand'].notna() & (df['brand'].str.strip() == '')
    print(f'\nbrand vacía (""): {blank_brand.sum()}')
    print(f'brand con espacios al inicio/fin: {(df["brand"].notna() & (df["brand"] != df["brand"].str.strip())).sum()}')
    print(f'display_name vacío: {(df["display_name"].str.strip() == "").sum()}')

    title('3. CALIDAD: FILAS REPETIDAS')
    # Las columnas con listas (promotions, allergens...) no son hashables: se serializan.
    hashable = df.map(lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False)
                      if isinstance(v, (list, dict)) else v)
    print(f'Filas idénticas en todas las columnas: {hashable.duplicated().sum()}')
    without_category = hashable.drop(columns=['category_id', 'category_name', 'category_complete'])
    print(f'Filas idénticas salvo la categoría (mismo producto, misma captura): '
          f'{without_category.duplicated().sum()}')

    title('3. CALIDAD: CLAVES PROPUESTAS EN LA TAREA 3.1')
    print(f'object_id distinto de sku_id: {(df["object_id"] != df["sku_id"]).sum()}')
    print(f'object_id no numérico: {(~df["object_id"].str.fullmatch(r"\d+")).sum()}')
    rows = []
    for captura, group in df.groupby('captura'):
        rows.append({
            'captura': captura,
            'filas': len(group),
            'object_id únicos': group['object_id'].nunique(),
            'object_id repetidos': group['object_id'].duplicated().sum(),
            '(object_id, categoría) repetidos': group.duplicated(['object_id', 'category_id']).sum(),
        })
    print(pd.DataFrame(rows).to_string(index=False))

    per_product = df.groupby(['captura', 'object_id'])['category_id'].nunique()
    print('\nNúmero de categorías por producto (productos):')
    print(per_product.value_counts().sort_index().to_string())

    print('\nCategorías que más apariciones repetidas aportan:')
    repeated = df[df.duplicated(['captura', 'object_id'], keep=False)]
    print(repeated.groupby('category_name').size().sort_values(ascending=False).head(6).to_string())

    # Un mismo producto en la misma captura, ¿tiene siempre los mismos valores?
    print('\nProductos con valores distintos entre sus apariciones de la misma captura:')
    for column in ['display_name', 'brand', 'prices.price', 'prices.price_per_unit',
                   'units_in_stock', 'url']:
        n = (df.groupby(['captura', 'object_id'])[column].nunique(dropna=False) > 1).sum()
        print(f'  {column}: {n}')

    print('\nClave (object_id, captured_at) para el histórico de precios:')
    unique_obs = df.drop_duplicates(['object_id', 'captured_at'])
    print(f'  observaciones únicas: {len(unique_obs)}')

    # 4. Campos relevantes ---------------------------------------------------
    title('4. CATEGORÍAS Y VALORES CATEGÓRICOS')
    print(f'Categorías distintas: {df["category_id"].nunique()} ids / '
          f'{df["category_name"].nunique()} nombres')
    print('\nCategorías marcadas incompletas:')
    print(cats[~cats['complete']][['captura', 'category_name', 'items']].to_string(index=False))
    print(f'\nArchivo con complete=false: {sorted(cats.loc[~cats["archivo_complete"], "captura"].unique())}')
    for column in ['prices.measure_unit', 'prices.currency', 'headband_promotion',
                   'prices.is_club_price', 'prices.is_promo_price']:
        print(f'\n{column}:')
        print(df[column].value_counts(dropna=False).to_string())
    print(f'\nMarcas distintas: {df["brand"].nunique()} '
          f'(tras strip: {df["brand"].str.strip().nunique()}, '
          f'tras strip+minúsculas: {df["brand"].str.strip().str.lower().nunique()})')

    title('4. RANGOS NUMÉRICOS')
    numeric = ['prices.price', 'prices.price_per_unit', 'prices.strikethrough_price',
               'prices.discount_percentage', 'units_in_stock', 'weight',
               'expiration_days', 'units_in_cart']
    print(df[numeric].describe().T.round(2).to_string())

    products = df.drop_duplicates(['captura', 'object_id'])
    price = products['prices.price']
    ppu = products['prices.price_per_unit']
    strike = products['prices.strikethrough_price']
    disc = products['prices.discount_percentage']
    checks = {
        'price <= 0': (price <= 0).sum(),
        'price_per_unit <= 0': (ppu <= 0).sum(),
        'price > 100 €': (price > 100).sum(),
        'price_per_unit > 500 €': (ppu > 500).sum(),
        'strikethrough_price <= price': (strike.notna() & (strike <= price)).sum(),
        'discount_percentage fuera de 0-100': (disc.notna() & ~disc.between(0, 100)).sum(),
        'descuento declarado vs calculado difiere > 2 pp': (
            disc.notna() & strike.notna()
            & (((1 - price / strike) * 100 - disc).abs() > 2)).sum(),
        'is_promo_price sin strikethrough_price': (
            products['prices.is_promo_price'] & strike.isna()).sum(),
        'units_in_stock == 0': (products['units_in_stock'] == 0).sum(),
        'units_in_stock < 0': (products['units_in_stock'] < 0).sum(),
        'weight == 0': (products['weight'] == 0).sum(),
    }
    print('\nComprobaciones sobre productos únicos por captura:')
    for name, value in checks.items():
        print(f'  {name}: {value}')

    # Coherencia entre price / price_per_unit y la cantidad indicada en el nombre.
    content = products['display_name'].str.extract(
        r'(?:(\d+)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g|l|ml|cl)\b'
        r'(?!.*\d+(?:[.,]\d+)?\s*(?:kg|g|l|ml|cl)\b)',
        flags=2)  # re.IGNORECASE
    factor = content[2].str.lower().map({'kg': 1, 'g': 0.001, 'l': 1, 'ml': 0.001, 'cl': 0.01})
    stated = (content[1].str.replace(',', '.').astype(float) * factor
              * content[0].fillna(1).astype(float))
    implied = price / ppu
    comparable = products['prices.measure_unit'].isin(['KILO', 'LITRO']) & stated.notna()
    ratio = implied / stated
    mismatch = comparable & ~ratio.between(0.8, 1.25)
    print(f'\nKILO/LITRO con cantidad legible en el nombre: {comparable.sum()}')
    print(f'  price/price_per_unit no coincide con el nombre (±20 %): {mismatch.sum()}')
    print(f'  productos distintos: {products.loc[mismatch, "object_id"].nunique()}')
    print(f'  de ellos, desviación de x100 o más: {(mismatch & ((ratio <= 0.01) | (ratio >= 100))).sum()}')
    print(products.loc[mismatch].assign(cantidad_nombre=stated, cantidad_implicita=implied.round(4))
          .sort_values('cantidad_implicita')[['captura', 'object_id', 'display_name', 'prices.price',
                                              'prices.price_per_unit', 'cantidad_nombre',
                                              'cantidad_implicita']].head(10).to_string(index=False))

    print('\nobject_id no numéricos (sufijo):')
    non_numeric = products[~products['object_id'].str.fullmatch(r'\d+')]
    print(non_numeric['object_id'].str.extract(r'(\D+\d*)$')[0].value_counts().to_string())
    print(non_numeric[['object_id', 'display_name']].head(3).to_string(index=False))
    base = non_numeric['object_id'].str.extract(r'^(\d+)')[0]
    print(f'  su id base también existe como producto: {base.isin(products["object_id"]).sum()} '
          f'de {len(non_numeric)}')

    print('\nPrecios más altos (captura más reciente):')
    last = products[products['captura'] == captures[-1]]
    print(last.nlargest(5, 'prices.price')[['object_id', 'display_name', 'prices.price',
                                            'prices.price_per_unit',
                                            'prices.measure_unit']].to_string(index=False))
    print('\nprice_per_unit más altos (captura más reciente):')
    print(last.nlargest(5, 'prices.price_per_unit')[['object_id', 'display_name', 'prices.price',
                                                     'prices.price_per_unit',
                                                     'prices.measure_unit']].to_string(index=False))

    title('4. COBERTURA TEMPORAL')
    print(df.groupby('captura')['captured_at'].agg(['min', 'max', 'nunique']).to_string())
    if len(captures) >= 2:
        first, second = (set(df.loc[df['captura'] == c, 'object_id']) for c in captures[-2:])
        print(f'\nProductos en {captures[-2]}: {len(first)}; en {captures[-1]}: {len(second)}')
        print(f'  comunes: {len(first & second)} | solo en la primera: {len(first - second)} '
              f'| solo en la segunda: {len(second - first)}')
        a = products[products['captura'] == captures[-2]].set_index('object_id')['prices.price']
        b = products[products['captura'] == captures[-1]].set_index('object_id')['prices.price']
        common = a.index.intersection(b.index)
        changed = (a[common] != b[common])
        print(f'  productos comunes con cambio de price: {changed.sum()} '
              f'({changed.mean() * 100:.1f} %)')
        diff = (b[common] - a[common])[changed]
        print(f'  subidas: {(diff > 0).sum()} | bajadas: {(diff < 0).sum()}')

        by_cat = cats.pivot(index='category_name', columns='captura', values='items')
        by_cat['diferencia'] = by_cat[captures[-1]] - by_cat[captures[-2]]
        print('\nCategorías con más variación de apariciones entre capturas:')
        print(by_cat.reindex(by_cat['diferencia'].abs().sort_values(ascending=False).index)
              .head(5).to_string())


if __name__ == '__main__':
    main()
