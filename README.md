# Análisis de productos y precios de DIA

Dataset del catálogo online de DIA para estudiar precios, categorías, formatos y promociones entre capturas. Los originales y las salidas transformadas se conservan por separado.

## Documentación

- [Recopilación y organización del dataset](docs/recopilacion.md)
- [Preparación, diccionario de campos y ejecución](docs/preparacion.md)
- [Diagnóstico histórico del 10 y 16 de noviembre](docs/diagnostico.md)

## Organización del proyecto

```text
scripts/1_ingesta.py         Obtención de una nueva captura
scripts/2_transformacion.py  Transformación de los originales
scripts/promociones.py       Interpretación de promociones
scripts/3_diagnostico.py     Diagnóstico con pandas
tests/test_promociones.py   Pruebas de promociones
data/raw/<captura>/          Originales JSON
data/processed/<captura>/    Productos transformados en JSON
docs/                       Documentación de las tareas
```

## Dataset actual

Cada registro procesado representa un producto en una captura. `producto_id` identifica el producto dentro del archivo; se combina con `captured_at` al construir un histórico. La salida incluye categorías, nombre, marca, imagen, precios en céntimos, contenido y tamaño de los packs, promociones generales y Club DIA, condiciones originales y procedencias.

El [diccionario de preparación](docs/preparacion.md) define los campos y las diferencias entre precio del pack, precio individual y precio por unidad de referencia. Los valores desconocidos se mantienen como `null`. El formato implementado es JSON; la exportación a Parquet está pendiente.

### Capturas disponibles

Inventario consultado el 23 de noviembre de 2026. Los recuentos RAW corresponden a apariciones producto-categoría; los productos únicos se cuentan por identificador.

| Captura | Apariciones RAW | Productos únicos | `complete` RAW | JSON procesado |
|---|---:|---:|---|---|
| `20261110T194612.279326Z` | 7,233 | 5,755 | `false` | Disponible |
| `20261116T181331.483679Z` | 7,215 | 5,738 | `false` | Disponible |
| `20261123T184952.650445Z` | 7,267 | 5,750 | `false` | Pendiente |

Una captura disponible no implica cobertura completa ni un diagnóstico actualizado. El informe histórico solo cubre las dos capturas que identifica expresamente.

## Ejecución

Python 3.10 o superior. Desde la raíz del proyecto:

```bash
python -m pip install requests pandas
python scripts/3_diagnostico.py
python scripts/2_transformacion.py
```

Para obtener una nueva captura, ejecutar `python scripts/1_ingesta.py`. Este paso consulta DIA; el diagnóstico y la transformación trabajan sobre archivos locales. Las instrucciones de pruebas están en [Preparación](docs/preparacion.md).

## Preguntas de investigación

1. ¿Cómo cambia el precio de los productos comunes entre capturas?
2. ¿Qué categorías y marcas tienen más variedad?
3. ¿Qué promociones generales y del Club DIA aparecen por categoría?
4. ¿Cómo influyen el tamaño del pack y la unidad de referencia en la comparación?

## Cobertura y limitaciones

La fuente es el catálogo online español de DIA. La fecha de observación se conserva en `captured_at`; no representa la fecha de inicio de una promoción. No se ha confirmado un surtido o código postal concreto. La cobertura incompleta, el stock y las condiciones Club limitan las comparaciones. Los identificadores de DIA no permiten equiparar automáticamente productos de otros supermercados.

## Condiciones de uso

Está pendiente revisar las condiciones de extracción, reutilización y redistribución de la fuente. El proyecto conserva los datos originales y documenta las limitaciones observadas.
