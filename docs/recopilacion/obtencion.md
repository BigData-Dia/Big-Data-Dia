# Obtención

> Evidencias históricas: capturas del 10 y 16 de noviembre de 2026.

## Fuente

API interna de la tienda online de [Supermercados DIA](https://www.dia.es/) (`/api/v1/common-aggregator/menu-data` para el menú de categorías y `/api/v1/plp-back/l1/all/{category_id}/reduced` para los productos).

## Fecha y método

web scraping con el script `scripts/1_ingesta.py` (Python + `requests`), recorriendo página a página las 30 categorías principales del menú. Se han realizado dos capturas: 10/11/2026 (19:54 UTC) y 16/11/2026 (18:21 UTC).

## Alcance

captura de todas las categorías principales del catálogo online, conservando los productos sin modificar sus campos originales. Captura del 10/11/2026: 7.233 registros (5.755 productos únicos por `sku_id`). Captura del 16/11/2026: 7.215 registros (5.738 productos únicos). La diferencia entre registros y productos únicos se debe a que un mismo producto puede aparecer en varias categorías (por ejemplo, *Navidad* o *Novedades y recomendados*).

## Comprobación

el script compara los productos descargados con el total indicado por la API, detecta páginas repetidas y marca cada categoría como completa o incompleta. En ambas capturas, 28 de las 30 categorías figuran como completas; *Novedades y recomendados* y *Cabello y belleza* quedan marcadas como incompletas, por lo que el campo `complete` global del archivo es `false`.

[Volver a recopilación](../recopilacion.md)
