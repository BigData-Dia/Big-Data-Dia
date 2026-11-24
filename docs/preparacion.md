# Preparación de los datos

## 1. Entender (Tarea 3.1)

**Pregunta:** ¿cómo cambian los precios, formatos y promociones de los productos de DIA entre capturas?

**Datos necesarios:** identificador, nombre, marca y categorías de cada producto; su formato (contenido y envase), precios y promociones, y la fecha de cada captura.

### 1.1. Decisiones

| Concepto | Nuestro proyecto |
|---|---|
| Unidad de observación | Una fila por producto y captura. En el RAW cada registro es la aparición de un producto en una categoría. |
| Clave candidata | `producto_id + fecha_captura`: identifica un producto en una captura concreta.<br>**Limitaciones:** en el RAW `object_id` se repite cuando el producto está en varias categorías, por lo que la clave solo es única tras consolidar. Los packs tienen id propio (`504P6` frente a `504`) y se tratan como productos distintos. |
| Esquema de salida | Tabla `productos_dia` (apartado 1.2). |
| Alcance | **Fuente:** API del catálogo online de DIA.<br>**Periodo:** capturas del 10/11/2026 (`data/raw/20261110T194612.279326Z/`) y del 23/11/2026 (`data/raw/20261123T184952.650445Z/`).<br>**Filtros:** ninguno.<br>**Población:** productos de la tienda online de DIA en España. |
| Trazabilidad | Columna `origenes`: lista con `archivo` (ruta relativa del RAW, incluye la captura) y `ruta_json` (posición del registro, índices desde cero; p. ej. `/categories/2/items/15`). Es una lista porque un producto consolidado procede de varias apariciones. |

### 1.2. Tabla de salida: `productos_dia`

Los campos opcionales quedan nulos cuando el dato no está disponible o no se reconoce.

| Columna | Tipo | Obligatoria | Descripción |
|---|---|---|---|
| `producto_id` | Texto | Sí | Identificador completo, incluidos los sufijos de pack. |
| `fecha_captura` | Fecha y hora (UTC) | Sí | Momento de la captura, tomado de `captured_at` del JSON. |
| `nombre` | Texto | Sí | Nombre comercial. |
| `marca` | Texto | No | Marca limpia y unificada. |
| `categorias` | Lista de textos | Sí | Categorías del producto, sin repeticiones. |
| `cantidad_contenidos` | Entero | No | Unidades del pack. |
| `tamano_unidad` | Decimal | No | Tamaño de cada unidad (p. ej. 0.33 para 330 ml). |
| `unidad_contenido` | Texto | No | kg, l, m o unidad. |
| `envase` | Texto | No | Envase reconocido en el nombre (botella, lata, brik…). |
| `precio_centimos` | Entero | No | Precio publicado del producto o pack; puede ser precio Club. |
| `precio_por_unidad_centimos` | Entero | No | Precio del pack entre sus unidades; no es el precio por kg o litro. |
| `precio_anterior_centimos` | Entero | No | Precio tachado. |
| `precio_referencia_centimos` | Entero | No | Precio por unidad de referencia publicado por DIA. |
| `unidad_precio_referencia` | Texto | No | KILO, LITRO, UNIDAD, LAVADO, DOCENA o METRO. |
| `moneda` | Texto | Sí | Código de moneda (EUR). |
| `es_promo` / `es_promo_club_dia` | Booleano | No | Tiene oferta general / Club DIA. |
| `precio_promo_centimos` / `precio_club_centimos` | Entero | No | Precio marcado como promoción general / Club DIA. |
| `tipo_promo` / `tipo_promo_club` | Texto | No | 2x1, 3x2, descuento_porcentaje, descuento_unidad, precio_fijo, precio_por_lote u otra. |
| `descripcion_promo` / `descripcion_promo_club` | Texto | No | Condiciones originales de la oferta. |
| `descuento_porcentaje` / `descuento_porcentaje_club` | Decimal | No | Porcentaje explícito de la oferta. |
| `promociones` | Lista de objetos | No | Detalle de cada oferta (código, tipo, ámbito, unidades, importe…). |
| `imagen_url` | Texto (URL) | No | URL absoluta de la imagen; ayuda a emparejar productos con otros supermercados. |
| `supermercado` | Texto | Sí | Valor fijo `DIA`, para unir con otros supermercados. |
| `origenes` | Lista de objetos | Sí | Procedencia en el RAW (ver Trazabilidad). |

### 1.3. Transformaciones necesarias

| Transformación | Origen → resultado | Motivo |
|---|---|---|
| Consolidar apariciones | Una fila por categoría → una por producto y captura | Cumplir la unidad de observación y la clave. |
| Añadir fecha y procedencia | `captured_at`, archivo y posición → `fecha_captura`, `origenes` | Comparar capturas y localizar el registro original. |
| Euros a céntimos | `prices.*` → `*_centimos` (enteros) | Evitar errores de redondeo. |
| Limpiar la marca | `brand` → `marca` sin espacios y con mayúsculas unificadas | Que `Dr. Oetker` y `Dr. oetker` sean la misma marca. |
| Normalizar unidades | `100 ML.` → LITRO y `100 GR.` → KILO (precio × 10) | Comparar precios de referencia en la misma unidad. |
| Extraer el formato | `display_name` → contenido, unidad y envase | El contenido solo está en el nombre (`weight` vale 0). |
| Interpretar promociones | `promotions` y flags de `prices` → campos de promoción | Separar ofertas generales y Club DIA. |
| Completar la imagen | `image` relativa → `imagen_url` absoluta | Poder abrirla fuera de la web. |
| Descartar campos vacíos | `weight`, `expiration_days`, `units_in_cart` | Valen 0 en todos los registros. |

## 2. Diagnóstico (Tarea 3.2)

El [informe de diagnóstico](diagnostico.md) conserva las cifras del 10 y 16 de noviembre. El código está en [3_diagnostico.py](../scripts/3_diagnostico.py). Una captura nueva exige volver a ejecutar el diagnóstico antes de extender esas conclusiones.

### Comprobaciones, resultados y conclusiones

Resumen de las cifras obtenidas con pandas y documentadas en el informe de diagnóstico. **Alcance: capturas del 10 y 16 de noviembre de 2026; no incluye la del 23 de noviembre.** Una fila del diagnóstico representa una aparición producto-categoría. La lectura, la inspección de tipos y los primeros registros se realizan sobre los RAW, sin modificarlos.

| Comprobación | Resultado | Conclusión |
|---|---|---|
| Estructura, tipos y muestra | 14.448 filas y 33 columnas: 7.233 filas del 10/11 y 7.215 del 16/11. Identificadores como texto, precios `float64` y fecha de captura UTC. El script muestra los primeros registros con `head()`. | Hay objetos y listas anidados que deben interpretarse antes de construir la salida. |
| Valores ausentes | Marca ausente en 407 filas (2,8 %); sin ausencias en `object_id` ni `display_name`. | La marca requiere admitir valores desconocidos. La ausencia de información opcional no demuestra que no exista en la realidad. |
| Filas repetidas | 0 filas completamente idénticas; 2.919 iguales si se excluye la categoría. | La presencia en varias categorías explica repeticiones de productos; no deben eliminarse categorías sin conservar su relación. |
| Claves del diseño | `object_id` repetido 1.478 veces el 10/11 y 1.477 el 16/11: 5.755 y 5.738 productos únicos. Hay 11.493 pares únicos `(producto_id, captured_at)`; 0 repeticiones de `(producto_id, categoría)` dentro de cada captura. | La clave de salida no es única en el RAW por aparición. Debe consolidarse por producto dentro de cada captura, conservando categorías y procedencias. |
| Categorías, unidades y formatos | 30 categorías, 8 unidades de precio de referencia y solo moneda EUR. Hay 204 marcas con espacios en los extremos. | Los formatos de marca y las unidades necesitan normalización justificada; los precios por distintas unidades no son directamente comparables. |
| Rangos y coherencia de precios | Precio entre 0,15 y 69,00 €, sin ceros ni negativos; descuentos entre 0 y 40 %. Hay 16 discrepancias superiores al 20 % entre contenido del nombre y precio por unidad, correspondientes a 8 productos. | Ajax 1,2 L presenta una incoherencia interna confirmada: 2.241,67 €/L frente a unos 2,24 €/L calculados con 2,69 €/1,2 L. Los otros 7 productos requieren investigación; no se corrigen automáticamente. |
| Consistencia entre apariciones | Nombre, marca y precios coinciden para cada producto y captura; el stock difiere en 35 casos. | Las diferencias de stock necesitan revisión antes de consolidar ese campo. |
| Cobertura y comparación temporal | 2 fechas; 28 de 30 categorías completas en cada captura. Hay 5.705 productos comunes, 50 solo en la primera y 33 solo en la segunda. Cambian de precio 524 productos comunes (282 suben y 242 bajan). | La cobertura es incompleta: no se pueden interpretar las apariciones y desapariciones como altas o bajas reales ni deducir tendencias con dos fechas. |

### Principales problemas y dudas

1. **Incoherencia confirmada:** el precio por litro de Ajax no concuerda con su precio y contenido declarado; el valor real requiere contrastar la fuente. Otros 7 productos con discrepancias necesitan investigación.
2. **Limitación confirmada de la clave RAW:** el identificador se repite por pertenecer a varias categorías. La salida prevista exige consolidar por producto y captura y conservar todas las procedencias.
3. **Cobertura pendiente de aclarar:** dos categorías figuran incompletas en ambas capturas. Las 50 desapariciones y 33 apariciones pueden deberse a diferencias de captura, no necesariamente a cambios reales del catálogo.

[Recopilación](recopilacion.md) · [Diagnóstico](diagnostico.md) · [Inicio](../README.md)
