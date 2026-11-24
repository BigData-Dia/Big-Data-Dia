# Preparación de los datos

## 1. Entender (Tarea 3.1.)

Antes de modificar los datos, definimos la pregunta de investigación, el significado de los registros y la estructura que queremos obtener. Así podemos determinar qué información necesitamos y qué condiciones deben cumplir los datos preparados.

### 1.1. Conceptos que debemos definir

| Concepto | Qué significa en nuestro proyecto |
|---|---|
| Unidad de observación | Un producto del catálogo de DIA en una captura determinada. |
| Clave candidata | Combinación de campos que permite identificar de forma única un producto dentro de una captura. |
| Esquema de salida | Campos, tipos de datos, unidades y campos obligatorios de los productos preparados. |
| Alcance | Catálogo online de DIA recopilado en distintas fechas, incluyendo sus categorías, productos, precios y promociones. |
| Trazabilidad | Forma de localizar el archivo y la posición del registro original del que procede cada producto preparado. |

### 1.2. Nuestros datos originales

Hemos recopilado información del catálogo online de Supermercados DIA mediante su API y guardado las capturas originales en `data/raw/`.

Los datos están organizados en formato JSON. Cada captura contiene distintas categorías y, dentro de ellas, los productos correspondientes.

| Elemento | Descripción |
|---|---|
| Fuente | API del catálogo online de Supermercados DIA. |
| Formato | JSON. |
| Estructura | Categorías que contienen listas de productos (`items`). |
| Identificador original | `object_id`. |
| Nombre original | `display_name`. |
| Información de precios | Precios publicados, precios anteriores y precios de referencia. |
| Información de promociones | Ofertas generales, promociones Club DIA y condiciones de las ofertas por varias unidades. |
| Fechas de recopilación | 10, 16 y 23 de noviembre de 2026. |
| Ubicación | `data/raw/`. |

Cada producto puede aparecer asociado a una o varias categorías. Por este motivo, un mismo identificador puede repetirse en los datos originales.

Las capturas corresponden a momentos diferentes. Esto nos permitirá comparar los productos que aparecen en varias fechas y estudiar los cambios de precios, formatos y promociones.

### 1.3. Diseñamos el resultado esperado

| Decisión | Nuestro proyecto |
|---|---|
| Pregunta | ¿Cómo cambian los precios, formatos y promociones de los productos de DIA entre capturas? |
| Objetivo | Comparar productos comunes entre distintas fechas y estudiar las diferencias en sus precios y promociones. |
| Unidad de observación | Una fila por producto y captura. |
| Clave candidata | `producto_id + fecha_captura`. |
| Tabla de salida | `productos_dia`. |
| Campos principales | Identificador, nombre, marca, categorías, formato, precios y promociones. |
| Procedencia | Archivo RAW original y ruta del registro dentro del JSON. |

La clave candidata `producto_id + fecha_captura` permite identificar un producto en una captura concreta, siempre que cada producto se consolide en una única fila por captura.

El identificador del producto se conservará completo, incluidos los sufijos correspondientes a los formatos o packs.

Como un producto puede aparecer en varias categorías, estas se conservarán en una lista sin repeticiones. También se mantendrán todas sus referencias de origen.

**Nota sobre la fecha de captura:** `fecha_captura` es un dato necesario para comparar las recopilaciones. No se considera un campo original proporcionado por DIA. Se incorporará a partir de la información de la propia captura o de su registro de recopilación, y se conservará en los datos preparados.

### 1.4. Definimos las columnas de salida

La tabla principal `productos_dia` contendrá una fila por producto y captura.

| Columna | Tipo | Obligatoria | Descripción |
|---|---|---|---|
| `producto_id` | Texto | Sí | Identificador completo del producto, incluidos los sufijos de pack. |
| `nombre` | Texto | Sí | Nombre comercial del producto. |
| `imagen_url` | Texto (URL) | No | Dirección de la imagen del producto. |
| `categorias` | Lista de textos | Sí | Categorías a las que pertenece el producto, sin repeticiones. |
| `cantidad_contenidos` | Entero | No | Número de unidades que contiene el pack; nulo si no se reconoce. |
| `tamano_unidad` | Decimal | No | Tamaño de cada unidad, expresado en la unidad correspondiente. |
| `unidad_contenido` | Texto | No | Unidad del contenido: kg, l, m o unidad. |
| `precio_por_unidad_centimos` | Entero | No | Precio publicado del pack dividido entre el número de contenidos, redondeado al céntimo. No equivale al precio por kg o litro. |
| `precio_centimos` | Entero | No | Precio publicado del producto o pack completo; puede corresponder al precio Club. |
| `precio_anterior_centimos` | Entero | No | Precio tachado original; no garantiza que sea el precio habitual vigente. |
| `precio_referencia_centimos` | Entero | No | Precio por unidad de referencia publicado por DIA, expresado en céntimos. |
| `unidad_precio_referencia` | Texto | No | Unidad del precio de referencia: KILO, LITRO u otra indicada por DIA. |
| `es_promo` | Booleano | No | Indica si el producto tiene una oferta general; nulo si no se conoce. |
| `es_promo_club_dia` | Booleano | No | Indica si el producto tiene una oferta Club DIA; nulo si no se conoce. |
| `precio_promo_centimos` | Entero | No | Precio marcado como promocional general. No se calcula a partir de ofertas por varias unidades. |
| `precio_club_centimos` | Entero | No | Precio marcado como Club DIA. No se calcula a partir de ofertas por varias unidades. |
| `tipo_promo` | Texto | No | Tipo de oferta general: 2x1, 3x2, descuento_porcentaje, descuento_unidad, precio_fijo, precio_por_lote u otra. |
| `tipo_promo_club` | Texto | No | Tipo de oferta Club DIA, con las mismas categorías que la oferta general. |
| `descripcion_promo` | Texto | No | Condiciones originales de las ofertas generales. |
| `descripcion_promo_club` | Texto | No | Condiciones originales de las ofertas Club DIA. |
| `descuento_porcentaje` | Decimal | No | Porcentaje explícito de descuento de la oferta general. |
| `descuento_porcentaje_club` | Decimal | No | Porcentaje explícito de descuento de la oferta Club DIA. |
| `promociones` | Lista de objetos | No | Información detallada de las ofertas: código, descripción, tipo, ámbito, URL, porcentaje, unidades e importes cuando se conocen. |
| `fecha_captura` | Fecha y hora | Sí | Momento en que se recopiló el catálogo. Se incorpora a partir de la información de la captura, no es un campo original de DIA. |
| `moneda` | Texto | No | Código de la moneda del precio publicado. |
| `origenes` | Lista de objetos | Sí | Referencias a las apariciones originales del producto. Cada objeto contiene el archivo y la ruta JSON. |
| `marca` | Texto | No | Marca del producto, eliminando los espacios sobrantes de los extremos. |
| `supermercado` | Texto | No | Supermercado al que pertenece el catálogo. En este proyecto, DIA. |
| `envase` | Texto | No | Tipo de envase reconocido en el nombre del producto; se omite si no se reconoce. |

Los campos opcionales podrán contener valores nulos cuando la información no esté disponible o no pueda reconocerse. Esto no significa necesariamente que el producto carezca de esa característica.

Las categorías, promociones y procedencias se mantienen como listas de datos relacionados para evitar multiplicar las filas de productos.

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
