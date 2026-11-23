# Preparación de los datos

## 1. Objetivo y diseño (Tarea 3.1)

¿Cómo cambian los precios, formatos y promociones de los productos de DIA entre capturas? Se comparan productos comunes y se distingue el precio publicado de las condiciones del Club DIA y de las ofertas por varias unidades.

### Unidad de observación y clave

La salida actual es `data/processed/<captura>/productos_dia.json`: una lista de productos, con una fila por producto dentro de cada captura. La clave candidata es `producto_id` dentro del archivo y `(producto_id, captured_at)` si se combinan capturas. Se conserva el identificador completo, incluidos los sufijos de pack.

Las categorías se almacenan en `categorias`, las ofertas en `promociones` y las referencias RAW en `origenes`. Las tablas separadas `producto_categoria` e `historico_precios` del diseño inicial son posibles ampliaciones; el script actual no las genera.

### Campos obligatorios y tipos

El diseño exige `producto_id`, `nombre`, `captured_at`, `categorias` y `origenes`. La transformación rechaza identificadores ausentes; la validación completa del resto de obligatorios está pendiente. Los campos opcionales desconocidos se representan como `null`. En JSON la fecha se conserva como texto ISO 8601; no se guarda como un tipo fecha nativo.

### Diccionario de la salida actual

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `producto_id` | Texto | Sí | Identificador completo, incluidos los sufijos de pack. |
| `nombre` | Texto | Sí | Nombre comercial del producto. |
| `imagen_url` | Texto (URL) | No | URL absoluta de la imagen. |
| `categorias` | Lista de textos | Sí | Nombres de categorías sin repeticiones. |
| `cantidad_contenidos` | Entero | No | Número de unidades del pack; nulo si no se reconoce. |
| `tamano_unidad` | Decimal | No | Tamaño individual en la unidad indicada; por ejemplo, 0.33 para 330 ml expresados en litros. |
| `unidad_contenido` | Texto | No | Unidad del tamaño individual: kg, l, m o unidad. |
| `precio_por_unidad_centimos` | Entero | No | Precio publicado del pack dividido por la cantidad de contenidos, redondeado al céntimo; no equivale al precio por kg/l. |
| `precio_centimos` | Entero | No | Precio publicado del producto o pack completo; puede ser precio Club. |
| `precio_anterior_centimos` | Entero | No | Precio tachado original; no garantiza un precio normal vigente. |
| `precio_referencia_centimos` | Entero | No | Precio por unidad de referencia publicado, expresado en céntimos. |
| `unidad_precio_referencia` | Texto | No | Unidad del precio de referencia: KILO, LITRO u otra indicada por DIA. |
| `es_promo` | Booleano | No | Indica una oferta general; nulo si no se conoce. |
| `es_promo_club_dia` | Booleano | No | Indica una oferta Club DIA; nulo si no se conoce. |
| `precio_promo_centimos` | Entero | No | Precio marcado como promocional general; no se calcula a partir de ofertas por varias unidades. |
| `precio_club_centimos` | Entero | No | Precio marcado como Club DIA; no se calcula a partir de ofertas por varias unidades. |
| `tipo_promo` | Texto | No | Tipo de oferta general: 2x1, 3x2, descuento_porcentaje, descuento_unidad, precio_fijo, precio_por_lote u otra. Nulo si no hay un único tipo conocido. |
| `tipo_promo_club` | Texto | No | Tipo de oferta Club DIA, con las mismas categorías que la oferta general. |
| `descripcion_promo` | Texto | No | Condiciones originales de las ofertas generales. |
| `descripcion_promo_club` | Texto | No | Condiciones originales de las ofertas Club DIA. |
| `descuento_porcentaje` | Decimal | No | Porcentaje explícito de la oferta general; consultar las condiciones para saber a qué unidad se aplica. |
| `descuento_porcentaje_club` | Decimal | No | Porcentaje explícito de la oferta Club DIA; consultar las condiciones de aplicación. |
| `promociones` | Lista de objetos | No | Ofertas con código, descripción, tipo, ámbito Club/online, URL, porcentaje, unidad descontada, unidades requeridas/pagadas e importe cuando se conocen. Lista vacía si no se incluyen ofertas. |
| `captured_at` | Texto (fecha y hora ISO 8601 UTC) | Sí | Instante original de la captura. |
| `moneda` | Texto | No | Código de moneda del precio publicado. |
| `origenes` | Lista de objetos | Sí | Apariciones originales; cada objeto exige `archivo` y `ruta_json`, ambos de tipo texto. |
| `marca` | Texto | No | Marca con los espacios de los extremos eliminados; puede ser nula. |
| `supermercado` | Texto | No | Valor fijo DIA. |
| `envase` | Texto | No | Envase reconocido en el nombre; se omite cuando no se reconoce. |

### Trazabilidad

Cada elemento de `origenes` contiene `archivo`, relativo al proyecto, y `ruta_json`, por ejemplo `/categories/2/items/15`. Los índices empiezan en cero. Al consolidar productos se conservan todas sus apariciones originales.

## 2. Diagnóstico (Tarea 3.2)

El [informe de diagnóstico](diagnostico.md) conserva las cifras del 10 y 16 de noviembre. El código está en [3_diagnostico.py](../scripts/3_diagnostico.py). Una captura nueva exige volver a ejecutar el diagnóstico antes de extender esas conclusiones.

[Recopilación](recopilacion.md) · [Diagnóstico](diagnostico.md) · [Inicio](../README.md)
