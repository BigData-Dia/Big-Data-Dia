# Análisis de productos y precios del supermercado DIA

Proyecto de recopilación y análisis de información del catálogo online de DIA mediante técnicas de web scraping.

## 1. Fuente de los Datos
* **Entidad:** Supermercados DIA.
* **Web oficial:** [https://www.dia.es/](https://www.dia.es/)
* **Origen:** Catálogo de productos de la tienda online.
* **Método:** Web scraping.
* **Fecha de consulta inicial:** 03/11/2026.

## 2. Registros y Campos
Cada registro representará un producto del catálogo en una fecha determinada. 
Campos previstos: `id_producto`, `nombre`, `marca`, `categoria`, `subcategoria`, `precio`, `precio_unidad`, `unidad_medida`, `descuento` y `fecha_extraccion`.

## 3. Formato y Tamaño
* **Formato:** CSV (alternativamente JSON).
* **Columnas previstas:** 10.
* **Número de registros:** Pendiente de determinar tras el scraping.
* **Tamaño:** Pendiente de determinar. Se intentará recopilar el catálogo completo dentro del ámbito seleccionado.

## 4. Cobertura
* **Ámbito geográfico:** España.
* **Periodo:** Desde la primera extracción.

> **Nota:** Se podrán realizar extracciones periódicas para estudiar la evolución de los precios. El catálogo y los precios pueden variar según el código postal.

## 5. Condiciones de Uso
Los datos proceden de la web oficial de DIA. Está pendiente revisar las condiciones de uso, extracción automatizada, reutilización y redistribución de los datos. No se utilizarán métodos para eludir sistemas de protección o restricciones de acceso.

## 6. Preguntas de Investigación
1. ¿Qué categorías tienen los precios medios más elevados?
2. ¿Qué marcas tienen mayor variedad de productos?
3. ¿Qué categorías tienen más productos en oferta?
4. ¿Cómo evolucionan los precios entre diferentes fechas?
5. ¿Existen diferencias de precio entre la marca DIA y otras marcas?

## 7. Limitaciones Iniciales
La información dependerá de los campos disponibles en la web. Los precios y la disponibilidad pueden variar según el código postal, las promociones y la fecha. Los cambios en la estructura de la web podrían afectar al scraping.

## 8. Motivo de Elección
Se ha elegido este dataset porque permite trabajar con datos reales del sector de la distribución alimentaria. Combina variables categóricas, numéricas y temporales, lo que permitirá practicar:
* Web scraping
* Python
* Limpieza y transformación de datos
* Análisis exploratorio (EDA)
* Almacenamiento y visualización de datos.

---

## Diccionario de Datos (Campos Previstos)

| Campo | Descripción | Tipo de dato |
| :--- | :--- | :--- |
| `id_producto` | Identificador del producto | Texto |
| `nombre` | Nombre completo del producto | Texto |
| `marca` | Marca comercial | Texto |
| `categoria` | Categoría principal | Texto |
| `subcategoria` | Subcategoría | Texto |
| `precio` | Precio de venta en euros | Decimal |
| `precio_unidad` | Precio por kg, litro o unidad | Decimal |
| `unidad_medida` | Unidad de medida | Texto |
| `descuento` | Porcentaje de descuento, si existe | Decimal |
| `fecha_extraccion` | Fecha de recopilación | Fecha |
```eof
