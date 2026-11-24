#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Diagnóstico de los datos originales de DIA (Tarea 3.2).

Python >= 3.10
Dependencia: pandas

Uso:
  python scripts/2_diagnostico.py

Lee todas las capturas de:
data/raw/<fecha_hora>/productos_dia.json

Solo muestra resultados por pantalla: no modifica los originales.
Cada fila del DataFrame es la aparición de un producto en una categoría.
"""

import json
import sys
from pathlib import Path

import pandas as pd


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Columnas que se muestran en los primeros registros
SAMPLE_COLUMNS = [
    "captura", "category_name", "object_id", "display_name", "brand",
    "prices.price", "prices.price_per_unit", "prices.measure_unit",
]

# Columnas numéricas cuyo rango se revisa
NUMERIC_COLUMNS = [
    "prices.price", "prices.price_per_unit", "prices.strikethrough_price",
    "prices.discount_percentage", "units_in_stock", "weight",
    "expiration_days", "units_in_cart",
]

# Columnas categóricas cuyos valores se cuentan
CATEGORICAL_COLUMNS = [
    "prices.measure_unit", "prices.currency", "headband_promotion",
    "prices.is_club_price", "prices.is_promo_price",
]

# Conversión de las unidades del nombre a kg o litros
UNIT_FACTORS = {"kg": 1, "g": 0.001, "l": 1, "ml": 0.001, "cl": 0.01}


# ============================================================
# 2. UTILIDADES
# ============================================================

def title(text: str) -> None:
    print(f"\n{'=' * 70}\n{text}\n{'=' * 70}")


def show(label: str, value: object) -> None:
    print(f"  {label}: {value}")


# ============================================================
# 3. CARGA DE LOS DATOS ORIGINALES
# ============================================================

def load_capture(path: Path) -> tuple[pd.DataFrame, bool]:
    """Aplana una captura: una fila por aparición producto-categoría.

    Devuelve también el indicador complete del archivo.
    """
    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    df = pd.json_normalize(
        data["categories"],
        record_path="items",
        meta=["id", "name", "complete"],
        meta_prefix="category_",
    )
    df.insert(0, "captura", path.parent.name)
    df.insert(1, "captured_at", pd.to_datetime(data["captured_at"]))
    return df, data["complete"]


def load_all() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob("*/productos_dia.json"))
    if not files:
        sys.exit(f"No hay capturas en {RAW_DIR}")

    title("1. CARGA DE LOS DATOS ORIGINALES")
    frames = []
    for path in files:
        df, complete = load_capture(path)
        frames.append(df)
        show(path.relative_to(RAW_DIR.parent.parent),
             f"{path.stat().st_size:,} bytes | complete={complete}")

    return pd.concat(frames, ignore_index=True)


# ============================================================
# 4. ESTRUCTURA
# ============================================================

def check_structure(df: pd.DataFrame) -> None:
    title("2. ESTRUCTURA")
    print(f"Filas y columnas: {df.shape}")
    print(df.groupby("captura").size().rename("filas").to_string())

    print("\nTipos de datos:")
    print(df.dtypes.to_string())

    print("\nPrimeros registros:")
    print(df[SAMPLE_COLUMNS].head().to_string(index=False))


# ============================================================
# 5. CALIDAD: AUSENTES, REPETIDOS Y CLAVES
# ============================================================

def check_missing(df: pd.DataFrame) -> None:
    title("3. CALIDAD: VALORES AUSENTES")
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    print(pd.DataFrame({
        "ausentes": missing,
        "%": (missing / len(df) * 100).round(1),
    }).to_string())

    brand = df["brand"].dropna()
    show("brand vacía", (brand.str.strip() == "").sum())
    show("brand con espacios sobrantes", (brand != brand.str.strip()).sum())
    show("display_name vacío", (df["display_name"].str.strip() == "").sum())


def check_duplicates(df: pd.DataFrame) -> None:
    title("3. CALIDAD: FILAS REPETIDAS")
    # Las listas y diccionarios no se pueden comparar: se pasan a texto.
    hashable = df.map(
        lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False)
        if isinstance(v, (list, dict)) else v
    )
    category_columns = ["category_id", "category_name", "category_complete"]
    show("filas idénticas", hashable.duplicated().sum())
    show("filas idénticas salvo la categoría",
         hashable.drop(columns=category_columns).duplicated().sum())


def check_keys(df: pd.DataFrame) -> None:
    title("3. CALIDAD: CLAVES DE LA TAREA 3.1")
    show("object_id distinto de sku_id", (df["object_id"] != df["sku_id"]).sum())
    show("object_id con sufijo de pack (filas)",
         (~df["object_id"].str.fullmatch(r"\d+")).sum())

    summary = df.groupby("captura").agg(
        filas=("object_id", "size"),
        object_id_unicos=("object_id", "nunique"),
    )
    summary["object_id_repetidos"] = summary["filas"] - summary["object_id_unicos"]
    summary["object_id_categoria_repetidos"] = df.groupby("captura").apply(
        lambda g: g.duplicated(["object_id", "category_id"]).sum()
    )
    print(summary.to_string())

    show("(object_id, captured_at) únicos",
         len(df.drop_duplicates(["object_id", "captured_at"])))

    print("\nCategorías por producto:")
    per_product = df.groupby(["captura", "object_id"])["category_id"].nunique()
    print(per_product.value_counts().sort_index().to_string())

    print("\nProductos con valores distintos entre sus apariciones:")
    for column in ["display_name", "brand", "prices.price",
                   "prices.price_per_unit", "units_in_stock"]:
        varies = df.groupby(["captura", "object_id"])[column].nunique(dropna=False) > 1
        show(column, varies.sum())


# ============================================================
# 6. CAMPOS RELEVANTES: CATEGORÍAS Y RANGOS
# ============================================================

def check_categories(df: pd.DataFrame) -> None:
    title("4. CATEGORÍAS Y VALORES CATEGÓRICOS")
    show("categorías distintas", df["category_name"].nunique())

    print("\nCategorías marcadas incompletas en el JSON:")
    incomplete = df[~df["category_complete"].astype(bool)]
    print(incomplete.groupby(["captura", "category_name"]).size()
          .rename("filas").to_string())

    for column in CATEGORICAL_COLUMNS:
        print(f"\n{column}:")
        print(df[column].value_counts(dropna=False).to_string())

    brand = df["brand"].dropna()
    print()
    show("marcas distintas", brand.nunique())
    show("tras quitar espacios", brand.str.strip().nunique())
    show("tras quitar espacios y pasar a minúsculas",
         brand.str.strip().str.lower().nunique())


def check_ranges(df: pd.DataFrame, products: pd.DataFrame) -> None:
    title("4. RANGOS NUMÉRICOS")
    print(df[NUMERIC_COLUMNS].describe().T.round(2).to_string())

    price = products["prices.price"]
    ppu = products["prices.price_per_unit"]
    strike = products["prices.strikethrough_price"]
    discount = products["prices.discount_percentage"]
    stock = products["units_in_stock"]

    print("\nComprobaciones (productos únicos por captura):")
    show("price <= 0", (price <= 0).sum())
    show("price_per_unit <= 0", (ppu <= 0).sum())
    show("price_per_unit > 500 €", (ppu > 500).sum())
    show("strikethrough_price < price", (strike < price).sum())
    show("discount_percentage fuera de 0-100", (~discount.between(0, 100)).sum())
    show("descuento declarado y calculado difieren > 2 pp",
         (((1 - price / strike) * 100 - discount).abs() > 2).sum())
    show("units_in_stock == 0", (stock == 0).sum())
    show("units_in_stock < 0", (stock < 0).sum())
    show("weight == 0", (products["weight"] == 0).sum())

    print("\nprice_per_unit más altos:")
    print(products.nlargest(5, "prices.price_per_unit")[
        ["captura", "object_id", "display_name", "prices.price",
         "prices.price_per_unit", "prices.measure_unit"]
    ].to_string(index=False))


def check_price_per_unit(products: pd.DataFrame) -> None:
    """Compara la cantidad del nombre con la que implica price / price_per_unit."""
    title("4. COHERENCIA ENTRE NOMBRE Y PRECIO POR UNIDAD")
    content = products["display_name"].str.extract(
        r"(?:(\d+)\s*x\s*)?(\d+(?:[.,]\d+)?)\s*(kg|g|l|ml|cl)\b"
        r"(?!.*\d+(?:[.,]\d+)?\s*(?:kg|g|l|ml|cl)\b)",
        flags=2,  # re.IGNORECASE
    )
    count = content[0].fillna("1").astype(float)
    quantity = content[1].str.replace(",", ".").astype(float)
    factor = content[2].str.lower().map(UNIT_FACTORS)

    stated = count * quantity * factor
    implied = products["prices.price"] / products["prices.price_per_unit"]
    ratio = implied / stated

    comparable = (products["prices.measure_unit"].isin(["KILO", "LITRO"])
                  & stated.notna())
    mismatch = comparable & ~ratio.between(0.8, 1.25)

    show("KILO/LITRO con cantidad en el nombre", comparable.sum())
    show("discrepancias > 20 %", mismatch.sum())
    show("productos distintos", products.loc[mismatch, "object_id"].nunique())
    show("desviación x100 o más",
         (mismatch & ((ratio <= 0.01) | (ratio >= 100))).sum())

    print(products.loc[mismatch]
          .assign(cantidad_nombre=stated, cantidad_implicita=implied.round(4))
          .sort_values("cantidad_implicita")
          [["captura", "object_id", "display_name", "prices.price",
            "prices.price_per_unit", "cantidad_nombre", "cantidad_implicita"]]
          .to_string(index=False))


def check_packs(products: pd.DataFrame) -> None:
    title("4. IDENTIFICADORES CON SUFIJO DE PACK")
    is_pack = ~products["object_id"].str.fullmatch(r"\d+")
    packs = products[is_pack]
    show("productos con sufijo", len(packs))
    print(packs["object_id"].str.extract(r"(P\d+)$")[0]
          .value_counts().rename_axis("sufijo").rename("productos").to_string())

    base_ids = packs["object_id"].str.extract(r"^(\d+)")[0]
    show("con su id base también presente",
         f"{base_ids.isin(products['object_id']).sum()} de {len(packs)}")


# ============================================================
# 7. COBERTURA TEMPORAL
# ============================================================

def check_coverage(products: pd.DataFrame) -> None:
    title("4. COBERTURA TEMPORAL")
    print(products.groupby("captura")["captured_at"]
          .agg(["min", "max", "nunique"]).to_string())

    captures = sorted(products["captura"].unique())
    if len(captures) < 2:
        return

    first, last = (
        products[products["captura"] == c].set_index("object_id")["prices.price"]
        for c in captures[-2:]
    )
    common = first.index.intersection(last.index)
    diff = last[common] - first[common]

    print()
    show("productos comunes", len(common))
    show("solo en la primera", len(first.index.difference(last.index)))
    show("solo en la segunda", len(last.index.difference(first.index)))
    show("comunes con cambio de price",
         f"{(diff != 0).sum()} ({(diff != 0).mean() * 100:.1f} %)")
    show("subidas", (diff > 0).sum())
    show("bajadas", (diff < 0).sum())


# ============================================================
# 8. PROCESO PRINCIPAL
# ============================================================

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_colwidth", 60)

    df = load_all()
    # Un producto por captura para las comprobaciones de valores.
    products = df.drop_duplicates(["captura", "object_id"])

    check_structure(df)
    check_missing(df)
    check_duplicates(df)
    check_keys(df)
    check_categories(df)
    check_ranges(df, products)
    check_price_per_unit(products)
    check_packs(products)
    check_coverage(products)


if __name__ == "__main__":
    main()
