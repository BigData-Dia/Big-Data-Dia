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

## Ingesta de datos (Tarea 2)

Desde la raíz del repositorio, con Python 3.10 o superior:

```powershell
python -m pip install requests
python scripts/ingest_dia.py
```

Cada ejecución crea un único archivo `data/raw/<fecha-hora-UTC>/captura_dia.json`.
No crea carpetas por categoría ni un directorio `processed`.

- `items`: todos los productos reunidos en una lista, sin limpiar ni eliminar repeticiones entre categorías.
- `request_log`: URL, estado HTTP y cuerpo original de cada respuesta en `body_base64`, incluidos el menú y los intentos fallidos que recibieron respuesta. Se recuperan los bytes con `base64.b64decode(respuesta["body_base64"])`; para JSON, se pueden leer con `json.loads(...)`.
- `categories`, `configuration`, fechas UTC, recuentos y errores: permiten revisar el alcance y repetir la captura.
- `complete`: indica si se completó el alcance según los controles del script; no garantiza cubrir productos fuera de las categorías consultadas.

La API se consulta por categorías principales y páginas, pero todo se conserva en el mismo archivo. Los cuerpos originales son los recibidos después de la descompresión de transporte de Requests. La lista `items` facilita su consulta; las respuestas completas permiten recuperar los originales sin perder campos ni metadatos.

Opciones: `--raw-dir`, `--timeout`, `--pause`, `--retries`, `--max-pages` y `--menu-url`. Las rutas relativas se interpretan desde el directorio de ejecución. El script muestra un resumen y devuelve 0 si la captura es completa, 1 si es incompleta y 2 si falla el menú o la escritura. Cada captura usa una carpeta nueva y no sobrescribe ejecuciones anteriores.
