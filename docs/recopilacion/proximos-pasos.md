# Próximos pasos

> Evidencias históricas: capturas del 10 y 16 de noviembre de 2026.

Compararemos los productos de DIA con otros supermercados mediante los campos comunes `producto_id`, `imagen_url`, `precio_centimos`, `unidad_contenido`, `categorias` y `nombre`. Adaptaremos los nombres de los campos, convertiremos el precio a céntimos e intentaremos completar `unidad_contenido` a partir del nombre. Queda pendiente acordar cómo reconocer productos equivalentes entre supermercados. Proponemos una captura semanal completa y una carga incremental del histórico, incorporando productos nuevos y modificaciones de precio u otros campos. Reconoceremos cada producto de DIA por `producto_id`, obtenido de `object_id`, y detectaremos novedades o cambios comparando sus valores con la captura anterior. No hemos identificado un campo de actualización del producto; utilizaremos `captured_at` como fecha de observación del cambio. Antes de comparar capturas, revisaremos su cobertura, ya que las actuales son incompletas.

## Estado de la preparación

La transformación actual y su diccionario están en [Preparación](../preparacion.md). La comparación entre supermercados es una propuesta: los identificadores internos de DIA no identifican automáticamente productos equivalentes de otras cadenas.

[Volver a recopilación](../recopilacion.md)
