# Revisión

> Evidencias históricas: capturas del 10 y 16 de noviembre de 2026.

## Selección de la muestra

la documentación previa declara una revisión de **20 registros** extraídos directamente de `data/raw/` (sin modificar los archivos originales) mediante muestreo aleatorio. No se conserva la semilla ni la lista de posiciones revisadas; esa muestra no es reproducible con la evidencia actual.



## Observaciones y dudas

1. **Repetición de `object_id` entre categorías:** varios productos aparecen simultáneamente en categorías base (como *Frutas* o *Aceites*) y en secciones transversales (*Novedades y recomendados* o *Navidad*), lo que explica que haya más apariciones que productos únicos y obliga a deduplicar en la limpieza.

2. **Campos opcionales y unidades incrustadas en texto:** claves como `brand`, `headband_promotion` o `promotions` (con `only_club_dia`) solo aparecen si el producto tiene marca o promoción activa. Además, el peso o volumen neto viene dentro de `display_name` (ej. *"1 L"*, *"900 g aprox."*) mientras que `weight` figura a `0`.

3. **Precios promocionales y stock a cero:** cuando hay descuento del Club DIA (`is_club_price: true`), `prices.price` muestra ya el precio rebajado (`5,39 €`) y `strikethrough_price` el precio tachado de referencia (`7,69 €`). Asimismo, en productos a granel `price` indica el coste del lote y `price_per_unit` el precio por kilo o litro, y se detectan artículos activos con `units_in_stock: 0`.



## Relación con la Tarea 1

la API consulta bajo sesión anónima sin código postal asignado, mezcla tarifas estándar con descuentos exclusivos de Club DIA en `prices.price` e incluye artículos sin stock (`units_in_stock: 0`). Si en la Tarea 1 se analiza el coste real de una cesta disponible hoy o precios sin tarjeta de fidelización, las conclusiones podrían distorsionarse. *(No se generaliza esta muestra al conjunto del dataset).*

## Diagnóstico completo

Las cifras sobre todas las filas de las capturas del 10 y 16 de noviembre están en el [diagnóstico](../diagnostico.md). Una ausencia de promoción o de marca no demuestra por sí sola que no exista esa información en la realidad.

[Volver a recopilación](../recopilacion.md)
