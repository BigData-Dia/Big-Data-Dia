# Análisis de productos y precios del supermercado DIA

Recopilación y análisis de datos del catálogo online de DIA para estudiar la evolución de los precios, los formatos de los productos y las promociones entre diferentes capturas.

## 1. Fuente

- **Entidad:** Supermercados DIA.
- **Web oficial:** [https://www.dia.es/](https://www.dia.es/)
- **Origen de los datos:** Catálogo de productos de la tienda online de DIA.
- **Método de obtención:** Recopilación automatizada mediante consultas a los servicios utilizados por la tienda online.
- **Fecha de consulta:** 10/11/2026 y 23/11/2026.

Los datos proceden del catálogo online español de DIA. Se conservan los archivos originales obtenidos en cada captura y se generan archivos JSON transformados para facilitar su análisis.

## 2. Registros y campos

Cada registro del dataset procesado representa un producto en una captura determinada. Un mismo producto puede aparecer en varias categorías del catálogo.

Los principales campos utilizados son:

| Campo | Descripción |
|---|---|
| `producto_id` | Identificador del producto utilizado para reconocerlo entre capturas. |
| `nombre` | Nombre comercial del producto. |
| `marca` | Marca comercial del producto, cuando está disponible. |
| `categoria` | Categorías del catálogo en las que aparece el producto. |
| `precio` | Precio publicado del producto o del pack. |
| `precio_unidad` | Precio por unidad de referencia, por ejemplo, por kilogramo o litro, expresado en céntimos. |
| `promociones` | Información sobre las promociones asociadas al producto. |

El diccionario completo de campos, sus tipos y las transformaciones aplicadas se encuentra en [docs/preparacion.md](docs/preparacion.md).

## 3. Formato y tamaño

- **Formato original:** JSON.
- **Formato procesado:** JSON.
- **Tamaño de los archivos:** Pendiente de determinar.
- **Ámbito de recopilación:** Catálogo online de DIA.
- **Conjunto de datos:** Se trabaja con las capturas disponibles, conservando los datos originales y sus correspondientes transformaciones.

### Capturas disponibles

Inventario consultado el 23 de noviembre de 2026.

| Fecha de captura | Apariciones RAW | Productos únicos | JSON procesado |
|---|---:|---:|---|
| 10/11/2026 | 7.233 | 5.755 | Disponible |
| 23/11/2026 | 7.267 | 5.750 | Pendiente |

Las apariciones RAW representan registros producto-categoría. Por tanto, un mismo producto puede aparecer varias veces si pertenece a diferentes categorías.

Las capturas no tienen cobertura completa del catálogo, por lo que los resultados deben interpretarse teniendo en cuenta esta limitación.

## 4. Cobertura

- **Ámbito geográfico:** España.
- **Fuente:** Catálogo online español de DIA.
- **Periodo de observación:** Del 10 y 23 de noviembre de 2026.
- **Fechas de captura disponibles:** 10 y 23 de noviembre de 2026.

Las fechas corresponden a los momentos en los que se recopilaron los datos, no a las fechas de inicio o finalización de las promociones.

No se ha confirmado un código postal o un surtido concreto. Los productos, precios y disponibilidad pueden variar según la ubicación y las condiciones de la tienda online.

## 5. Condiciones de uso

Los datos proceden de la web oficial de DIA. Está pendiente revisar y documentar las condiciones específicas de extracción automatizada, reutilización y redistribución de la información.

No se utilizarán métodos para eludir sistemas de protección o restricciones de acceso.

Hasta confirmar las condiciones aplicables, no se considera verificado que los archivos puedan compartirse o redistribuirse libremente.

## 6. Preguntas de investigación

El proyecto pretende responder a las siguientes preguntas:

1. ¿Cómo cambia el precio de los productos que aparecen en varias capturas?
2. ¿Qué categorías y marcas tienen una mayor variedad de productos?
3. ¿Qué promociones generales y del Club DIA aparecen en las distintas categorías?
4. ¿Qué diferencias existen entre el precio del pack, el precio por unidad y el precio de referencia?
5. ¿Qué productos presentan cambios de precio entre las capturas disponibles?

Estas preguntas permiten estudiar tanto la evolución temporal de los precios como las características del catálogo y sus promociones.

## 7. Limitación inicial

La principal limitación detectada es que las capturas no contienen la totalidad del catálogo. Además, algunos productos pueden aparecer en varias categorías y existen diferencias entre los datos de stock de distintas apariciones.

También se han detectado discrepancias en algunos precios de referencia respecto al contenido indicado en el nombre del producto. Estos casos deben revisarse antes de realizar comparaciones.

Por otra parte, el número de capturas disponibles todavía es reducido, por lo que no permite establecer tendencias de precios a largo plazo.

## 8. Motivo de elección

Se ha elegido este dataset porque permite trabajar con datos reales de un sector cercano a la vida cotidiana: la distribución alimentaria.

Además de estudiar la evolución de los precios, los formatos, las categorías y las promociones de DIA, el proyecto tiene como objetivo facilitar una posible comparación con los datasets de otros grupos de clase, que están recopilando información de otros supermercados.

Este trabajo conjunto permitirá analizar semejanzas y diferencias entre supermercados, por ejemplo, en los precios de productos equivalentes, la variedad de marcas, las categorías disponibles y las estrategias de promoción.

Para ello, será necesario identificar qué campos e información pueden utilizarse de forma común entre los distintos datasets, teniendo en cuenta que cada supermercado puede presentar sus propios formatos, identificadores y condiciones comerciales.

El proyecto permitirá aplicar durante el curso diferentes técnicas de Big Data e inteligencia artificial:

- Recopilación automatizada de datos.
- Python y tratamiento de archivos JSON.
- Limpieza y transformación de datos.
- Análisis exploratorio de datos (EDA).
- Comparación temporal de precios.
- Análisis de categorías, formatos y promociones.
- Integración y comparación de datos procedentes de diferentes supermercados.
- Almacenamiento y visualización de resultados.

---

## 9. Documentación del proyecto

- [Recopilación y organización del dataset](docs/recopilacion.md)
- [Preparación, diccionario de campos y ejecución](docs/preparacion.md)
- [Diagnóstico de los datos](docs/diagnostico.md)

## 10. Organización del proyecto

```text
scripts/
    1_ingesta.py
    2_transformacion.py
    3_diagnostico.py

data/
    raw/          Archivos originales JSON
    processed/    Archivos JSON transformados

docs/
    recopilacion.md
    preparacion.md
```