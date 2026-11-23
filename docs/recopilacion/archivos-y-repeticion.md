# Archivos y repetición

> Evidencias históricas: capturas del 10 y 16 de noviembre de 2026.

## Ubicación

originales en `data/raw/<fecha-hora-UTC>/productos_dia.json`, con una carpeta independiente por captura para evitar sobrescrituras.

## Formato y tamaño

JSON en UTF-8. La captura del 10/11/2026 ocupa 6.216.349 bytes (6,22 MB) y la del 16/11/2026, 6.189.469 bytes (6,19 MB). JSON permite conservar la estructura de categorías, productos, precios y promociones de la API.

## Almacenamiento

el volumen actual permite conservar y consultar las capturas como archivos, manteniendo los originales separados de los resultados de `data/processed/`. Si crece el histórico y se necesitan consultas frecuentes por producto y fecha, podría convenir una base de datos.

## Repetición

se necesita Python 3.10 o superior y la dependencia `requests`. Desde la raíz del proyecto, ejecutar `python -m pip install requests` y después `python scripts/1_ingesta.py`. La configuración está en las constantes del script: `TIMEOUT = 30` segundos, `PAUSE = 1` segundo, `RETRIES = 2` y `MAX_PAGES = 100` por categoría; `RAW_DIR` establece la carpeta de salida. Cada ejecución obtiene una nueva captura y muestra un resumen con productos, categorías, páginas, errores y archivo generado.

## Ejecución real

la captura finalizada el 16/11/2026 a las 18:21:33 UTC generó `data/raw/20261116T181331.483679Z/productos_dia.json`, con 7.215 registros y 28 de 30 categorías completas. El archivo indica `complete: false`. Estos datos se han comprobado en el JSON; no se conserva la salida de terminal para confirmar las páginas recorridas o los avisos concretos.

[Volver a recopilación](../recopilacion.md)
