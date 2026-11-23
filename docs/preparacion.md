# Preparación de los datos

## 1. Objetivo y diseño (Tarea 3.1)

¿Cómo cambian los precios, formatos y promociones de los productos de DIA entre capturas? Se comparan productos comunes y se distingue el precio publicado de las condiciones del Club DIA y de las ofertas por varias unidades.

### Unidad de observación y clave

La salida actual es `data/processed/<captura>/productos_dia.json`: una lista de productos, con una fila por producto dentro de cada captura. La clave candidata es `producto_id` dentro del archivo y `(producto_id, captured_at)` si se combinan capturas. Se conserva el identificador completo, incluidos los sufijos de pack.

Las categorías se almacenan en `categorias`, las ofertas en `promociones` y las referencias RAW en `origenes`. Las tablas separadas `producto_categoria` e `historico_precios` del diseño inicial son posibles ampliaciones; el script actual no las genera.

### Campos obligatorios y tipos

El diseño exige `producto_id`, `nombre`, `captured_at`, `categorias` y `origenes`. La transformación rechaza identificadores ausentes; la validación completa del resto de obligatorios está pendiente. Los campos opcionales desconocidos se representan como `null`. En JSON la fecha se conserva como texto ISO 8601; no se guarda como un tipo fecha nativo.

### Diccionario de la salida actual

| Campos | Tipo y significado |
|---|---|
| `producto_id`, `nombre`, `imagen_url` | Texto; identificador completo, nombre y URL absoluta de imagen. |
| `categorias` | Lista de nombres de categorías sin repeticiones. |
| `cantidad_contenidos`, `tamano_unidad`, `unidad_contenido` | Número de unidades del pack y tamaño individual en kg, l, m o unidad. Un pack 6 x 330 ml se representa como 6, 0.33, l. Se extraen del nombre; nulo si no se reconoce el formato. |
| `precio_por_unidad_centimos` | Entero: precio publicado del pack dividido por cantidad_contenidos, redondeado al céntimo. No equivale al precio por kg/l. |
| `precio_centimos` | Entero: precio publicado del producto o pack completo; puede ser precio Club. |
| `precio_anterior_centimos` | Entero: precio tachado original; no garantiza un precio normal vigente. |
| `precio_referencia_centimos`, `unidad_precio_referencia` | Precio por kg/l/unidad publicado por la fuente y su unidad. |
| `es_promo`, `es_promo_club_dia` | Booleanos: oferta general y oferta Club, respectivamente. Se consultan tanto los indicadores de precio como la lista de promociones. Nulo si no se conoce. |
| `precio_promo_centimos`, `precio_club_centimos` | Enteros: precio publicado cuando la fuente lo marca como precio promocional general o Club. No se calculan precios individuales a partir de 2x1/3x2 u ofertas por lote. |
| `tipo_promo`, `tipo_promo_club` | Texto: 2x1, 3x2, descuento_porcentaje, descuento_unidad, precio_fijo, precio_por_lote u otra. Nulo si hay varios tipos o no se conoce. |
| `descripcion_promo`, `descripcion_promo_club` | Texto original de las condiciones, separado por ámbito. |
| `descuento_porcentaje`, `descuento_porcentaje_club` | Número: porcentaje explícito en la descripción. No supone que se aplique a todo el producto; consultar tipo y condiciones. |
| `promociones` | Lista completa: código, descripción, tipo, solo_club_dia, exclusiva_online, URL, porcentaje, unidad descontada, unidades requeridas/pagadas e importe en céntimos cuando es explícito. Permite conservar varias ofertas simultáneas. |
| `captured_at`, `moneda`, `origenes` | Fecha original de captura, moneda y procedencias de todas las apariciones consolidadas. |
| `marca`, `supermercado`, `envase` | Texto: marca recortada, valor `DIA` y envase reconocido en el nombre. `marca` puede ser nulo; `envase` se omite cuando no se reconoce. |

### Trazabilidad

Cada elemento de `origenes` contiene `archivo`, relativo al proyecto, y `ruta_json`, por ejemplo `/categories/2/items/15`. Los índices empiezan en cero. Al consolidar productos se conservan todas sus apariciones originales.

## 2. Diagnóstico (Tarea 3.2)

El [informe de diagnóstico](diagnostico.md) conserva las cifras del 10 y 16 de noviembre. El código está en [3_diagnostico.py](../scripts/3_diagnostico.py). Una captura nueva exige volver a ejecutar el diagnóstico antes de extender esas conclusiones.

[Recopilación](recopilacion.md) · [Diagnóstico](diagnostico.md) · [Inicio](../README.md)
