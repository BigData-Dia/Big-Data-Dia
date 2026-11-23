# Preparación de los datos

## Diseño de las tablas (Tarea 3.1)

**Pregunta.** ¿Cuántos productos de DIA subieron, bajaron o mantuvieron su precio de venta entre las capturas del 10 y del 16 de noviembre de 2026? Para responderla hacen falta el identificador del producto (`object_id`), la fecha y hora de captura (`captured_at`), el precio de venta (`prices.price`) y su moneda (`prices.currency`). Se compararán los productos presentes en ambas capturas. El nombre permitirá identificar los productos en los resultados y la categoría se conservará como relación aparte.

| Tabla | Qué representa cada fila | Clave candidata y qué identifica |
|---|---|---|
| `productos` | Un producto observado en alguna captura. | `producto_id` identifica un artículo del catálogo. Se conserva el identificador completo, incluidos los sufijos de pack. |
| `producto_categoria` | Una pertenencia a una categoría observada al menos una vez en las capturas. | `(producto_id, categoria_id)` identifica la relación entre un producto y una categoría, aunque aparezca en varias capturas. |
| `historico_precios` | El precio de venta de un producto en un instante de captura. | `(producto_id, captured_at)` identifica una observación de precio. Si dos apariciones con esa clave discrepan en precio o moneda, se registrará el conflicto antes de consolidarlas. |

| Tabla | Columna | Tipo | Obligatoria | Descripción |
|---|---|---|---|---|
| `productos` | `producto_id` | Texto | Sí | Identificador original `object_id`. |
| `productos` | `nombre` | Texto | Sí | Nombre comercial (`display_name`) de la aparición más reciente con nombre. |
| `producto_categoria` | `producto_id` | Texto | Sí | Referencia al producto. |
| `producto_categoria` | `categoria_id` | Texto | Sí | Identificador de la categoría (`categories[].id`). |
| `historico_precios` | `producto_id` | Texto | Sí | Referencia al producto. |
| `historico_precios` | `captured_at` | Fecha y hora UTC | Sí | Instante de la captura indicado en el JSON. |
| `historico_precios` | `precio_eur` | Decimal con dos decimales | Sí | Precio de venta del artículo en euros. |
| `historico_precios` | `moneda` | Texto | Sí | Código de moneda del precio original. Para esta comparación se exige `EUR`. |
| Todas | `origenes` | Lista de objetos | Sí | Referencias a las apariciones originales que respaldan la fila. Cada objeto contiene `archivo` (texto) y `ruta_json` (texto), ambos obligatorios. |

**Trazabilidad.** Antes de aplanar el JSON se guardará la ruta del archivo relativa al repositorio (`data/raw/<captura>/productos_dia.json`) y la posición del elemento dentro de él (`/categories/2/items/15`, con índices desde cero). Esa posición identifica el registro original. Al agrupar apariciones se conservarán sus referencias en `origenes`.

**Transformaciones previstas.** Aplanar las listas de productos de cada categoría, conservar los identificadores como texto, recortar espacios del nombre y convertir `captured_at` a fecha y hora UTC. Leer `prices.price` como decimal, validar `EUR` y conservar el importe sin dividirlo por 100 porque el archivo ya lo expresa en euros. Separar productos, pertenencias y precios, y consolidar las apariciones por sus claves. Para responder la pregunta, emparejar los precios por `producto_id` entre ambas capturas y clasificar el signo de la diferencia.

[Diagnóstico de los datos originales (Tarea 3.2)](diagnostico.md)
