# Estructura

> Evidencias históricas: capturas del 10 y 16 de noviembre de 2026.

## Registro

Cada registro RAW representa una aparición de un producto en una categoría y captura de DIA.

## Tipo de datos

Los datos son semiestructurados, en formato JSON, contienen objetos anidados como `prices` y presentan campos opcionales como `brand`, que no aparece en todos los registros comprobados.

## Identificador

El campo `object_id` podría identificar cada producto. Es una cadena de texto aunque contenga dígitos.

## Campos relevantes

Las siguientes rutas corresponden a las respuestas originales de la API:

- **`categories[].name`:** Nombre de la categoría a la que pertenece la aparición del producto.

- **`object_id`:** posible identificador del producto. Es texto y puede incluir sufijos de pack, como `P6`.

- **`display_name`:** nombre comercial del producto. Puede incluir información sobre la cantidad, el peso o la presentación.

- **`prices.price_per_unit`:** precio por unidad de medida, útil para comparar productos con distintas presentaciones. Es un valor numérico expresado en la moneda y unidad indicadas en `prices.currency` y `prices.measure_unit`.

- **`prices.measure_unit`:** Unidad de medida a la que se refiere el precio por unidad.

[Volver a recopilación](../recopilacion.md)
