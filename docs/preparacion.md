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


## 2. Diagnosticar (Tarea 3.2)

Se ha ejecutado el script de diagnóstico (`scripts/fase_3.2_diagnostico.py`) directamente sobre los archivos JSON originales de ambas capturas en `data/raw/` (`20261110T194612.279326Z/` y `20261123T184952.650445Z/`) sin modificarlos.

### 2.1. Resumen de comprobaciones con `pandas`

| Dimensión / Aspecto | Comprobación realizada | Resultado obtenido | Conclusión |
|---|---|---|---|
| **Estructura y volumen** | Filas, columnas y tipos leídos tras aplanar los JSON (`json_normalize`). | `[N]` apariciones totales en `[N]` columnas (`[N]` en 10/11/2026 y `[N]` en 23/11/2026). Precios como `float64` y textos/IDs como `object`. | Estructura consistente entre ambas capturas; cada fila representa una aparición en categoría. |
| **Unicidad y clave candidata** | Duplicados exactos y repeticiones de `object_id + fecha_captura`. | `0` filas 100% idénticas, pero **`[N]` repeticiones** de `object_id` dentro de una misma captura (`[N]` únicos en 10/11 y `[N]` en 23/11). | **Error/comportamiento confirmado:** la clave no es única en el RAW porque un producto aparece en varias categorías; requiere consolidación. |
| **Completitud (ausencias)** | Recuento de nulos en campos clave (`brand`, `prices.price`, `promotions`, `image`). | `brand` ausente en `[N]` registros (`[N]%`); `prices.price` ausente en `[N]` registros. | `brand` nulo es normal en frescos a granel. Si hay precios nulos, deben investigarse o apartarse. |
| **Validez de formatos y marcas** | Variantes en `brand`, unidades en `prices.measure_unit` y columnas constantes (`weight`, `expiration_days`, `units_in_cart`). | `[N]` variantes de escritura en `brand` (espacios/mayúsculas); unidades como `100 ML.` y `100 GR.` mezcladas con `LITRO` y `KILO`; `weight`, `expiration_days` y `units_in_cart` valen siempre `0`. | **Confirmado:** justifica normalizar marcas, escalar unidades a `LITRO`/`KILO` y descartar las columnas constantes a `0`. |
| **Rangos y stock** | Distribución de `prices.price` y registros con `units_in_stock == 0`. | Precios entre `[min] €` y `[max] €` (mediana `[med] €`). Detectados `[N]` registros con `units_in_stock == 0`. | **Caso a investigar:** comprobar si los productos con stock `0` tienen precios válidos antes de incluirlos en comparativas entre fechas. |
| **Cobertura temporal** | Rango de `captured_at` entre capturas. | Desde `2026-11-10T19:46:12Z` hasta `2026-11-23T18:49:52Z` (2 capturas separadas por 13 días). | Cobertura adecuada para analizar variaciones quincenales de precios y promociones. |

### 2.2. Síntesis de problemas confirmados y casos a investigar

* **Problemas confirmados:**
  1. **Colisión de la clave candidata en el RAW (`[N]` repeticiones):** al estar los datos organizados por categoría, un mismo `object_id` aparece repetido hasta `[N]` veces en la misma captura (por ejemplo, en *Frutas* y *Novedades*), confirmando la necesidad de agrupar por `producto_id + fecha_captura` y consolidar `categorias` y `origenes` en listas.
  2. **Inconsistencia en unidades de referencia y marcas:** `prices.measure_unit` combina escalas base (`KILO`, `LITRO`) con fracciones (`100 GR.`, `100 ML.`), y `brand` presenta `[N]` duplicados por diferencias de mayúsculas o espacios. Además, el peso del producto no está en `weight` (siempre `0`), sino incrustado en `display_name`.
* **Casos que necesitan investigación:**
  1. **Artículos con `units_in_stock == 0` (`[N]` apariciones) y sufijos de pack (`[N]` registros):** es necesario verificar en la transformación si los artículos sin stock mantienen actualizado su precio o conservan precios antiguos, así como comprobar qué productos con sufijo de pack (ej. `504P6`) carecen de su producto individual base en la misma captura.